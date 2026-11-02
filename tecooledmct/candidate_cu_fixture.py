"""Bounded native-Cu3D electrical fixture; staged gates, no production TEC solve."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import signal,time
import numpy as np
from scipy.sparse.csgraph import connected_components

from .candidate_cu_fem import assemble,solve_dirichlet,gradient,plane_current,analytic_controls
from .tec_material_plausibility import ROOT,read,write,sha
from .native_gas_audit import step_units

SOURCE=ROOT/'data/tec_candidate_29114_20261101'
SIGMA=1/1.72e-8
KCU=400.


def native_geometry(gmsh):
    occ=gmsh.model.occ
    gmsh.option.setString('Geometry.OCCTargetUnit','M')
    path=SOURCE/'geometry/candidate_mm.step'
    if step_units(path.read_text())['metres_per_coordinate_unit']!=.001:raise ValueError('Invalid source units')
    tags=occ.importShapes(str(path));occ.synchronize();vols=[t for dim,t in tags if dim==3]
    old=read(SOURCE/'geometry/cad_writer.json')['records'];d=read(SOURCE/'geometry/design.json')
    if len(vols)!=361:raise ValueError('Source solid count')
    boxes=np.array([occ.getBoundingBox(3,t) for t in vols]);masses=np.array([occ.getMass(3,t) for t in vols])
    names={};available=set(range(len(vols)))
    for r in old:
        mask=np.all(abs(boxes-r['bbox_m'])<=2.1e-7,axis=1)&np.isclose(masses,r['volume_m3'],rtol=1e-7,atol=1e-20)
        matches=[i for i in np.flatnonzero(mask) if i in available]
        if len(matches)!=1:raise ValueError('Ambiguous SI source signature: '+r['name'])
        i=matches[0];available.remove(i);names[r['name']]=vols[i]
    meta={b['name']:b for b in d['bodies']};keep={n for n,b in meta.items() if b['kind'] in ('Cu','SnSb','Al2O3')}
    keep.update(('Cu_tail_node0','Cu_tail_node88'))
    occ.remove([(3,t) for n,t in names.items() if n not in keep],recursive=True)
    cu={j:names[f'Cu_node{j}'] for j in range(89)}
    for j in (0,88):
        fused=occ.fuse([(3,cu[j])],[(3,names[f'Cu_tail_node{j}'])])[0]
        if len(fused)!=1:raise ValueError('Lead continuity/fuse failed')
        cu[j]=fused[0][1]
    tools=[(n,names[n]) for n in keep if n in meta and meta[n]['kind']!='Cu'];tools.sort()
    _,mapping=occ.fragment([(3,cu[j]) for j in range(89)],[(3,t) for n,t in tools]);occ.synchronize()
    owner={};native_cu={};toolmeta={}
    for j,tags in enumerate(mapping[:89]):
        vs=[t for dim,t in tags if dim==3]
        if len(vs)!=1 or vs[0] in owner:raise ValueError('Split/overlapped conductor after imprint')
        owner[vs[0]]=j;native_cu[j]=vs[0]
        expected=next(r['volume_m3'] for r in old if r['name']==f'Cu_node{j}')
        if j in (0,88):expected+=next(r['volume_m3'] for r in old if r['name']==f'Cu_tail_node{j}')
        if not np.isclose(occ.getMass(3,vs[0]),expected,rtol=1e-7,atol=1e-20):raise ValueError('Imprint changed Cu volume')
    for (name,_),tags in zip(tools,mapping[89:]):
        vs=[t for dim,t in tags if dim==3]
        if len(vs)!=1:raise ValueError('Imprint split source contact tool')
        toolmeta[vs[0]]=meta[name]
    faces=[];legmeta={l['index']:l for l in d['legs']}
    for dim,f in gmsh.model.getEntities(2):
        up,_=gmsh.model.getAdjacencies(2,f);cus=[int(v) for v in up if int(v) in owner]
        if not cus:continue
        if len(cus)!=1:raise ValueError('Cu short/ambiguous face ownership')
        j=owner[cus[0]];ep=-1;tp=-1;contact=None
        others=[toolmeta[int(v)] for v in up if int(v) in toolmeta]
        if len(others)>1:raise ValueError('Ambiguous Cu material-contact face')
        if others:
            b=others[0];contact=b['name']
            if b['kind']=='SnSb':
                leg=b['leg'];side=0 if leg==j-1 else 1 if leg==j else -1
                if side<0 or b['node']!=j:raise ValueError('Invalid chain contact map')
                ep=2*j+side;tp=legmeta[leg]['stage']+(b['face']=='cold')
            else:tp=int(b['name'].replace('ceramic',''))
        bbox=occ.getBoundingBox(2,f)
        if j in (0,88) and abs(bbox[1]+.005)<2.1e-7 and abs(bbox[4]+.005)<2.1e-7:
            if not np.isclose(occ.getMass(2,f),np.pi*1e-8,rtol=1e-7):raise ValueError('Invalid true tail terminal')
            ep=0 if j==0 else 177;tp=4;contact='external_tail_end'
        faces.append(dict(tag=f,cu_node=j,electrical_port=ep,thermal_port=int(tp),contact_source=contact,area_m2=occ.getMass(2,f)))
    for p in range(178):
        area=sum(f['area_m2'] for f in faces if f['electrical_port']==p)
        expected=np.pi*1e-8 if p in (0,177) else .16e-6
        if not np.isclose(area,expected,rtol=1e-7,atol=1e-18):raise ValueError('Missing/ambiguous full electrical port: '+str(p))
    occ.remove([(3,t) for t in toolmeta],recursive=True);occ.synchronize()
    remaining={t for dim,t in gmsh.model.getEntities(3)}
    if remaining!=set(native_cu.values()):raise ValueError('Unexpected fixture volume coverage')
    return native_cu,faces,{j:occ.getMass(3,t) for j,t in native_cu.items()}


def extract(gmsh,cu,faces):
    tags,coordinates,_=gmsh.model.mesh.getNodes();tags=np.asarray(tags,int);points=np.array(coordinates).reshape(-1,3)
    index=np.full(int(tags.max())+1,-1,int);index[tags]=np.arange(len(tags))
    tets=[];body=[]
    for j,v in cu.items():
        types,_,nodes=gmsh.model.mesh.getElements(3,v)
        for kind,n in zip(types,nodes):
            if kind!=4:raise ValueError('Non-P1 tetrahedron')
            cells=index[np.asarray(n,int).reshape(-1,4)];tets.extend(cells);body.extend([j]*len(cells))
    tets=np.array(tets,int);body=np.array(body,int)
    if len(tets)>250000:raise ValueError('Hard250k tetrahedron cap exceeded')
    used=np.unique(tets);remap=np.full(len(points),-1,int);remap[used]=np.arange(len(used));points=points[used];tets=remap[tets]
    tri=[];ep=[];tp=[];tb=[];ft=[]
    for f in faces:
        types,_,nodes=gmsh.model.mesh.getElements(2,f['tag']);count=0
        for kind,n in zip(types,nodes):
            if kind!=2:raise ValueError('Nonlinear/nontriangular boundary')
            x=remap[index[np.asarray(n,int).reshape(-1,3)]]
            if np.any(x<0):raise ValueError('Boundary outside Cu tet mesh')
            tri.extend(x);count+=len(x)
        if count==0:raise ValueError('Missing native boundary face mesh')
        ep.extend([f['electrical_port']]*count);tp.extend([f['thermal_port']]*count)
        tb.extend([f['cu_node']]*count);ft.extend([f['tag']]*count)
    tri=np.array(tri,int);ep=np.array(ep,int);tp=np.array(tp,int);tb=np.array(tb,int);ft=np.array(ft,int)
    allfaces=np.sort(tets[:,np.array([[1,2,3],[0,2,3],[0,1,3],[0,1,2]])],axis=2).reshape(-1,3)
    dtype=np.dtype([(str(i),np.int64) for i in range(3)])
    key=np.ascontiguousarray(allfaces).view(dtype).ravel();order=np.argsort(key)
    query=np.ascontiguousarray(np.sort(tri,axis=1)).view(dtype).ravel()
    left=np.searchsorted(key[order],query);right=np.searchsorted(key[order],query,side='right')
    if np.any(right-left!=1):raise ValueError('Boundary triangle does not have exactly one Cu tet')
    parent=order[left]//4
    if np.any(body[parent]!=tb):raise ValueError('Native face/tet owner disagreement')
    xyz=points[tri];vectors=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2
    toward=points[tets[parent]].mean(axis=1)-xyz[:,0];vectors[np.einsum('ij,ij->i',toward,vectors)>0]*=-1
    areas=np.linalg.norm(vectors,axis=1)
    for f in faces:
        mesharea=areas[ft==f['tag']].sum()
        if abs(mesharea/f['area_m2']-1)>.01:raise ValueError('Native boundary area error>1%')
    return dict(points=points,tets=tets,body=body,tri=tri,electrical_port=ep,thermal_port=tp,tri_body=tb,
                face_tag=ft,parent=parent,area_vectors=vectors)


def port_nodes(mesh,key,count):
    groups=[np.unique(mesh['tri'][mesh[key]==j]) for j in range(count)]
    for i,a in enumerate(groups):
        for b in groups[i+1:]:
            if np.intersect1d(a,b).size:raise ValueError('Incompatible shared-node Dirichlet trace')
    return groups


def electrical(mesh,cad_volumes):
    p,t,b=mesh['points'],mesh['tets'],mesh['body'];K,vol,g,det=assemble(p,t,SIGMA)
    if np.any(det<=0):raise ValueError('Nonpositive native tetrahedron orientation')
    for j in range(89):
        if abs(vol[b==j].sum()/cad_volumes[j]-1)>.01:raise ValueError('Cu body volume mesh error>1%')
    components,labels=connected_components(K,directed=False)
    if components!=89:raise ValueError('Cu mesh component count')
    node_body=np.full(len(p),-1,int)
    for j in range(89):
        nodes=np.unique(t[b==j]);node_body[nodes]=j
        if len(np.unique(labels[nodes]))!=1:raise ValueError('Disconnected Cu conductor')
    groups=port_nodes(mesh,'electrical_port',178);mask=np.zeros(len(p),bool);values=np.zeros((len(p),3))
    for j,nodes in enumerate(groups):
        if not len(nodes):raise ValueError('Empty electrical terminal')
        mask[nodes]=True;values[nodes]=[1,0,-1] if j%2==0 else [0,1,0]
    u,reaction=solve_dirichlet(K,mask,values)
    currents=np.array([reaction[n].sum(axis=0) for n in groups]).reshape(89,2,3)
    G=currents[:,0,0];R=1/G
    grad=gradient(u[:,0],t,g);energy=np.bincount(b,weights=SIGMA*vol*np.sum(grad*grad,axis=1),minlength=89)
    free_l1=np.array([abs(reaction[(node_body==j)&~mask,0]).sum() for j in range(89)])
    errors=dict(free_relative_L1=float(max(free_l1/G)),terminal_closure=float(max(abs(currents[:,:,0].sum(axis=1))/G)),
        work_energy_relative=float(max(abs(energy/G-1))),reciprocity_relative=float(max(abs(currents[:,1,1]/G-1))),
        reverse_relative=float(max(abs(currents[:,0,2]/G+1))),swap_field_error=float(abs(u[:,0]+u[:,1]-1).max()),
        reverse_field_error=float(abs(u[:,0]+u[:,2]).max()))
    if np.any(G<=0) or max(errors.values())>1e-8:raise ValueError('Electrical residual/work/reciprocity gate')
    voltage=u[:,0]/G[node_body];J=-SIGMA*grad/G[b,None];heat=SIGMA*vol*np.sum((grad/G[b,None])**2,axis=1)
    raw=-np.einsum('ij,ij->i',J[mesh['parent']],mesh['area_vectors']) # positive inward
    raw_ports=np.array([raw[mesh['electrical_port']==j].sum() for j in range(178)]).reshape(89,2)
    d=read(SOURCE/'geometry/design.json');legs=d['legs'];cuts=[]
    # Frozen path_boxes uses square0.1x0.1mm vertical pillars; only horizontal
    # ribbons have0.1x0.03mm sections. Do not reuse the old uniform-area estimate.
    special={0:(0,0.,-1,.1e-3*.03e-3),58:(2,.0012,1,.1e-3*.1e-3),80:(2,.0024,1,.1e-3*.1e-3),88:(2,.002,-1,.1e-3*.1e-3)}
    for j in range(89):
        if j in special:axis,z,sign,area_expected=special[j]
        else:
            a=np.array(legs[j-1]['center_mm']);c=np.array(legs[j]['center_mm']);axis=int(np.argmax(abs(c-a)))
            z=float((a[axis]+c[axis])*.0005);sign=float(np.sign(c[axis]-a[axis]));area_expected=.44e-3*.03e-3
        sel=b==j;current,area=plane_current(p,t[sel],J[sel],axis,z);current*=sign
        cuts.append(dict(cu_node=j,axis=axis,position_m=z,current_A=current,area_m2=area,error=abs(current-1)))
        if not np.isclose(area,area_expected,rtol=1e-7,atol=1e-20):raise ValueError('Interior section area/ownership error')
    result=dict(R_ohm=R,total_R_ohm=float(R.sum()),tetrahedra=len(t),nodes=len(p),components=components,
        numerical_errors=errors,cuts=cuts,max_raw_cut_error=max(c['error'] for c in cuts),
        raw_terminal_inward_A=raw_ports,raw_terminal_closure_A=raw_ports.sum(axis=1),
        max_J_A_m2=float(np.linalg.norm(J,axis=1).max()),Joule_total_W_at1A=float(heat.sum()),
        electrical_gate_without_comparator=bool(max(c['error'] for c in cuts)<.02))
    fields=dict(voltage_1A=voltage,current_density_1A=J,Joule_tet_W_1A=heat,volume=vol)
    return result,fields,K,g,vol


def thermal(mesh,fields):
    p,t=mesh['points'],mesh['tets'];K,_,_,_=assemble(p,t,KCU)
    groups=port_nodes(mesh,'thermal_port',5);boundary=np.zeros(len(p),bool);value=np.zeros((len(p),5))
    for j,n in enumerate(groups):boundary[n]=True;value[n,j]=1
    phi,reactions=solve_dirichlet(K,boundary,value)
    L=np.array([reactions[n].sum(axis=0) for n in groups])
    F=np.bincount(t.ravel(),weights=np.repeat(fields['Joule_tet_W_1A']/4,4),minlength=len(p))
    theta,r=solve_dirichlet(K,boundary,np.zeros(len(p)),F);theta=theta[:,0];r=r[:,0]
    allocation=phi.T@F;actual=np.array([-r[n].sum() for n in groups]);total=F.sum()
    err=dict(reciprocity=float(abs(L-L.T).max()/max(abs(L).max(),1e-30)),row_closure=float(abs(L.sum(axis=1)).max()/max(abs(L).max(),1e-30)),
        allocation_relative=float(abs(allocation-actual).max()/total),Joule_closure_relative=float(abs(allocation.sum()/total-1)),
        partition_of_unity=float(abs(phi.sum(axis=1)-1).max()))
    if max(err.values())>1e-8 or min(allocation)<-1e-10 or np.linalg.eigvalsh((L+L.T)/2).min()<-1e-10 or phi.min()<-1e-8:
        raise ValueError('Thermal response/partition gate')
    return dict(status='PASS under registered constant-Cu/perfect-contact/isothermal-ceramic closure',L_W_K=L,
        Joule_destinations_W_at1A=allocation,thermal_errors=err,all_ports300K_max_Cu_K=float(300+theta.max()),
        ideal_materials_and_contacts=True,physical_heat_partition_measured=False),dict(thermal_basis=phi,Joule_temperature_rise_K_1A=theta)


def run(out):
    out=Path(out)
    if out.exists():raise ValueError('Absent fixture output required')
    out.mkdir(parents=True);start=time.monotonic()
    def timeout(*_):raise TimeoutError('Registered fixture/phase wallclock cap')
    old=signal.signal(signal.SIGALRM,timeout)
    def phase(seconds):signal.setitimer(signal.ITIMER_REAL,min(seconds,max(.001,600-(time.monotonic()-start))))
    import gmsh
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4);gmsh.logger.start()
    results=[]
    try:
        phase(30);write(out/'analytic_controls.json',analytic_controls())
        phase(120);cu,faces,cad=native_geometry(gmsh);write(out/'native_faces.json',faces);write(out/'CAD_volumes.json',cad)
        for level,h in [('coarse',60e-6),('fine',40e-6)]:
            phase(150);gmsh.model.mesh.clear()
            for key,val in {'Mesh.MeshSizeMin':h*.25,'Mesh.MeshSizeMax':h,'Mesh.MeshSizeFromPoints':0,
                'Mesh.MeshSizeFromCurvature':0,'Mesh.MeshSizeExtendFromBoundary':0,'Mesh.MinimumCirclePoints':32,
                'Mesh.Algorithm3D':1,'Mesh.ElementOrder':1,'Mesh.Binary':1}.items():gmsh.option.setNumber(key,val)
            gmsh.model.mesh.generate(3);m=extract(gmsh,cu,faces)
            phase(90);r,f,_,_,_=electrical(m,cad);r['level']=level;r['h_m']=h;results.append(r)
            np.savez_compressed(out/(level+'_fields.npz'),**m,**f)
            gmsh.write(str(out/(level+'.msh')));write(out/(level+'.json'),r)
            if level=='fine':fine_mesh,fine_fields=m,f
        delta=np.array(results[1]['R_ohm'])/np.array(results[0]['R_ohm'])-1
        electrical_PASS=bool(results[1]['electrical_gate_without_comparator'] and max(abs(delta))<.02 and abs(results[1]['total_R_ohm']/results[0]['total_R_ohm']-1)<.02)
        result=dict(stage_A_electrical='PASS' if electrical_PASS else 'FAIL',R_ohm=results[1]['total_R_ohm'],
            max_component_R_change=float(max(abs(delta))),total_R_relative_change=results[1]['total_R_ohm']/results[0]['total_R_ohm']-1,
            fine_max_raw_cut_error=results[1]['max_raw_cut_error'],seconds=time.monotonic()-start,
            stage_B='NOT RUN: A gate pending',stage_C='NOT RUN: B gate pending')
        if electrical_PASS:
            phase(90);therm,tf=thermal(fine_mesh,fine_fields);write(out/'thermal.json',therm)
            np.savez_compressed(out/'thermal_fields.npz',**tf)
            result['stage_A_thermal']='PASS under declared ideal closure';result['stage_B']='AUTHORIZED after independent operator checks; NOT RUN yet'
        else:
            result['stage_A_thermal']='NOT RUN: electrical gate failed';result['stage_B']='NOT RUN: electrical gate failed'
            result['Joule_destination_bounds_W_at1A']=[0.,result['R_ohm']]
        result['seconds']=time.monotonic()-start;write(out/'result.json',result);print(result)
    except Exception as error:
        write(out/'STOP.json',dict(observed_UTC=datetime.now(timezone.utc).isoformat(),reason=str(error),seconds=time.monotonic()-start,
            stage_B='NOT RUN',stage_C='NOT RUN',completed_levels=[r['level'] for r in results]));raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0.);signal.signal(signal.SIGALRM,old)
        write(out/'gmsh_log.json',gmsh.logger.get());gmsh.finalize()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);run(parser.parse_args().out)
