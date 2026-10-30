"""Independent signed bath trace and full passive nodal-support identity."""
import argparse,gzip,json,shutil
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
PLAN=ROOT/'data/bath_spatial/diagnostic_plan.json'
OLD=ROOT/'fem/results/cold20_completion_20261030'
NEW=ROOT/'fem/results/cold_bath_rev3_20261030'
CASES=[('fine647657',ROOT/'fem/results/cold_interface_convergence_20261030/device/cold20um_FAILED/mesh',OLD/'cases/loaded20_refined_replay'),
       ('previous675496',OLD/'bath_mesh',OLD/'cases/bath_coupled'),
       ('normal744713',NEW/'meshes/bath2',NEW/'cases/bath2'),('normal821458',NEW/'meshes/bath3',NEW/'cases/bath3')]

def read(p):return json.loads(p.read_text())
def gradients(p,c,u):
    e=p[c[:,1:]]-p[c[:,:1]];v=np.cross(e[:,1],e[:,2]);det=np.einsum('ij,ij->i',e[:,0],v)
    if np.any(abs(det)<1e-30):raise ValueError('Degenerate tetrahedron')
    du=u[c[:,1:]]-u[c[:,:1]]
    g=(du[:,0,None]*v+du[:,1,None]*np.cross(e[:,2],e[:,0])+du[:,2,None]*np.cross(e[:,0],e[:,1]))/det[:,None]
    return abs(det)/6,g

def outer_edges(p,bath,plan,pins):
    edges=np.sort(np.concatenate([bath[:,[0,1]],bath[:,[1,2]],bath[:,[2,0]]]),axis=1)
    edges,count=np.unique(edges,axis=0,return_counts=True);edges=edges[count==1];xy=p[edges,:2].mean(1)
    mount=np.min(abs(np.linalg.norm(xy[:,None,:]-np.array([[x,0] for x in plan['hole_centers_x_m']])[None,:,:],axis=2)-plan['hole_radius_m']),axis=1)<1e-4
    seal=np.min(np.linalg.norm(xy[:,None,:]-pins[None,:,:],axis=2),axis=1)<plan['glass_outer_radius_m']+1e-4
    return p[edges[~(mount|seal)],:2]

def distance_segments(xy,segments):
    result=np.full(len(xy),np.inf);a=segments[:,0];e=segments[:,1]-a;den=np.sum(e*e,1)
    for first in range(0,len(xy),256):
        d=xy[first:first+256,None,:]-a;u=np.clip(np.einsum('pki,ki->pk',d,e)/den,0,1)
        result[first:first+256]=np.linalg.norm(d-u[:,:,None]*e,axis=2).min(1)
    return result

def partitions(xyz,manifest,segments,plan):
    xy=xyz[:,:2];r=np.linalg.norm(xy,axis=1);by={x['id']:x for x in manifest['bodies']};pins=np.array([by[i]['center_xy_m'] for i in range(401,410)])
    radial=np.digitize(r,plan['radial_edges_m'][1:-1]);angle=np.floor((np.arctan2(xy[:,1],xy[:,0])%(2*np.pi))/(2*np.pi/plan['angular_sectors'])).astype(int)
    quadrant=(xy[:,0]>=0).astype(int)+2*(xy[:,1]>=0).astype(int);physical=np.full(len(xy),'remaining_Kovar',dtype=object)
    physical[abs(xy[:,0])>.00875]='ear_lobes';physical[distance_segments(xy,segments)<plan['outer_rim_width_m']]='outer_rim'
    physical[(abs(xy[:,0])<=.0032)&(abs(xy[:,1])<=.0032)]='hot_footprint'
    for bid in (190,191):
        for x,y,z,dx,dy,dz in by[bid]['boxes_m']:
            physical[(xy[:,0]>=x)&(xy[:,0]<=x+dx)&(xy[:,1]>=y)&(xy[:,1]<=y+dy)]='projected_hot_routes'
    holes=np.array([[x,0] for x in plan['hole_centers_x_m']]);dh=np.linalg.norm(xy[:,None,:]-holes[None,:,:],axis=2)-plan['hole_radius_m']
    for i in range(2):physical[dh[:,i]<plan['hole_band_width_m']]='mount_hole_'+str(i+1)
    dg=np.linalg.norm(xy[:,None,:]-pins[None,:,:],axis=2);nearest=dg.argmin(1)
    near=dg.min(1)<plan['glass_outer_radius_m']+plan['glass_band_width_m']
    for i in range(9):physical[near&(nearest==i)]='glass_annulus_'+str(i+1)
    return {'physical':physical.astype(str),'radial':radial.astype(str),'quadrant':quadrant.astype(str),'angular':angle.astype(str)}

def signed(power):
    pos=float(power[power>=0].sum());neg=float(power[power<0].sum());absolute=pos-neg
    return {'net_W':pos+neg,'positive_W':pos,'negative_W':neg,'absolute_W':absolute,'cancellation_fraction':float(1-abs(pos+neg)/absolute) if absolute else 0.}

def geometry_flux(p,c,b,f,tags,T,phi,quality,manifest):
    """All identity terms are actual P1 diagnostics, never recovered bath flux."""
    bath=f[tags==101];nodes=np.unique(bath);indicator=np.zeros(len(p));indicator[nodes]=1
    support=np.flatnonzero(np.any(indicator[c]>0,axis=1));lc=c[support];vol,gt=gradients(p,lc,T);_,gv=gradients(p,lc,phi);_,gw=gradients(p,lc,indicator)
    by={x['id']:x for x in manifest['bodies']};materials=np.array([by[int(x)]['material'] for x in b[support]])
    if not set(materials)<=set(['Kovar','Glass','Pin']):raise ValueError('Unexpected material in bath nodal support')
    k=np.array([{'Kovar':17.3,'Glass':1.,'Pin':17.3}[x] for x in materials]);q=-k[:,None]*gt;work=1e-12*np.sum(gv*gv,axis=1)
    faces=np.concatenate([np.delete(lc,j,axis=1) for j in range(4)]);owner=np.tile(np.arange(len(lc)),4);xyz=p[faces];center=xyz.mean(1)
    av=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2
    av[np.einsum('ij,ij->i',av,center-p[lc[owner]].mean(1))<0]*=-1
    keys,ix,count=np.unique(np.sort(faces,axis=1),axis=0,return_inverse=True,return_counts=True)
    if count.max()>2:raise ValueError('Nonmanifold support')
    trace=indicator[faces].mean(1);power=np.einsum('ij,ij->i',q[owner],av);weighted=power*trace
    declared={tuple(sorted(row)):int(tag) for row,tag in zip(f,tags)};bathset={tuple(sorted(row)) for row in bath}
    isbath=np.zeros(len(faces),bool);other=np.zeros(len(faces),bool)
    for j in np.flatnonzero((count[ix]==1)&(trace>0)):
        key=tuple(keys[ix[j]])
        if key not in declared or declared[key]>=1000:raise ValueError('Incomplete nodal support or hidden exterior face')
        if key in bathset:isbath[j]=True
        else:other[j]=True
    ib=np.flatnonzero(isbath)
    if len(ib)!=len(bath) or not np.all(b[support[owner[ib]]]==300):raise ValueError('Bath has wrong owners or duplicate triangles')
    avb=av[ib];area=np.linalg.norm(avb,axis=1)
    if abs(avb[:,:2]).max()>1e-18 or np.any(avb[:,2]>=0) or abs(center[ib,2]).max()>1e-12:raise ValueError('Wrong bath normal/plane')
    tri=faces[ib];ids=owner[ib];ci=lc[ids];apex=np.array([row[~np.isin(row,face)][0] for row,face in zip(ci,tri)])
    height=3*vol[ids]/area;offset=p[apex,:2]-center[ib,:2];edge=np.max(np.linalg.norm(p[tri][:,:,None]-p[tri][:,None,:],axis=3),axis=(1,2))
    internal=count[ix]==2;volume_terms=np.einsum('ij,ij->i',q,gw)*vol;work_w=float(vol@(work*indicator[lc].mean(1)))
    identity={'raw_bath_W':float(power[ib].sum()),'other_exterior_weighted_W':float(weighted[other].sum()),
       'internal_weighted_jumps_W':float(weighted[internal].sum()),'passive_work_W':work_w,
       'independent_reaction_W':float(volume_terms.sum()+work_w),
       'support_tets':len(lc),'support_materials':sorted(set(materials)),
       'material_volume_terms_W':{x:float(volume_terms[materials==x].sum()) for x in sorted(set(materials))}}
    identity['closure_error_W']=identity['independent_reaction_W']-sum(identity[x] for x in ['raw_bath_W','other_exterior_weighted_W','internal_weighted_jumps_W','passive_work_W'])
    if abs(identity['closure_error_W'])>1e-10:raise ValueError('Discrete signed identity does not close')
    # Unique support-face sums retain both internal owners before grouping.
    jump=np.bincount(ix,weights=weighted,minlength=len(keys));kind=np.full(len(keys),'internal',dtype=object)
    for j in np.flatnonzero(other):kind[ix[j]]='other_exterior_'+materials[owner[j]]
    for j in ib:kind[ix[j]]='bath'
    face_data={'faces':tri,'xyz_m':p[tri],'centroids_m':center[ib],'areas_m2':area,'outward_area_vectors_m2':avb,
        'power_W':power[ib],'density_W_m2':power[ib]/area,'owners':support[ids],'normal_height_m':height,
        'tangential_face_max_edge_m':edge,'apex_offset_xy_m':offset,'owner_T_span_K':np.ptp(T[ci],axis=1),
        'bath_T_span_K':np.ptp(T[tri],axis=1),'owner_SICN':quality[support[ids]],'owner_gradient_K_m':gt[ids]}
    return face_data,identity,{'centroids_m':p[keys].mean(1),'weighted_power_W':jump,'kind':kind.astype(str),'areas_m2':np.linalg.norm(np.cross(p[keys[:,1]]-p[keys[:,0]],p[keys[:,2]]-p[keys[:,0]]),axis=1)/2}

def audit(label,mesh,case,out):
    import meshio
    from reports.field_geometry import node_map,cell_map
    if out.exists():raise ValueError('New spatial audit label required')
    out.mkdir(parents=True);d=np.load(mesh/'mesh.npz');p,c,b,f,tags,quality=[d[k] for k in ['points','cells','bodies','faces','boundaries','quality']]
    m=read(mesh/'manifest.json');e=read(case/'execution.json');r=read(case/'metrics.json');plan=read(PLAN)
    if sha(mesh/'mesh.npz')!=e['mesh_sha256']:raise ValueError('Mesh/execution mismatch')
    zipped=case/(e['field_source']+'.gz');raw=out/'actual_fields.vtu'
    with gzip.open(zipped,'rb') as src,raw.open('wb') as dst:shutil.copyfileobj(src,dst)
    if sha(raw)!=e['vtu_sha256']:raise ValueError('Archived native field mismatch')
    field=meshio.read(raw);index,distance=node_map(p,field.points);cell_map(c,np.argsort(index)[field.cells_dict['tetra']])
    T=field.point_data['temperature'].ravel()[index];phi=field.point_data['potential'].ravel()[index]
    data,identity,jumps=geometry_flux(p,c,b,f,tags,T,phi,quality,m)
    if abs(identity['raw_bath_W']-r['hot_out_raw_gradient_w'])>5e-10 or abs(identity['independent_reaction_W']-r['hot_out_reaction_w'])>1e-9:raise ValueError('Independent trace or passive reaction differs')
    pins=np.array([x['center_xy_m'] for x in m['bodies'] if x['kind']=='glass']);segments=outer_edges(p,f[tags==101],plan,pins)
    groups=partitions(data['centroids_m'],m,segments,plan);jgroups=partitions(jumps['centroids_m'],m,segments,plan);rows=[];jrows=[]
    for family,labels in groups.items():
        data['partition_'+family]=labels
        for name in sorted(set(labels)):
            sel=labels==name;rows.append({'family':family,'region':name,'triangles':int(sel.sum()),'area_m2':float(data['areas_m2'][sel].sum()),**signed(data['power_W'][sel])})
    for name in sorted(set(jgroups['physical'])):
        for kind in sorted(set(jumps['kind'])):
            sel=(jgroups['physical']==name)&(jumps['kind']==kind)
            jrows.append({'region':name,'kind':kind,**signed(jumps['weighted_power_W'][sel])})
    np.savez_compressed(out/'bath_faces.npz',**data);np.savez_compressed(out/'support_faces.npz',**jumps)
    source={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(PLAN.relative_to(ROOT)):sha(PLAN)}
    quant=lambda x:np.quantile(x,[0,.25,.5,.75,1]).tolist()
    result={'case':label,'new_solver_run':False,'mesh_sha256':e['mesh_sha256'],'field_sha256':e['vtu_sha256'],'source_sha256':source,
       'mesh_nodes':len(p),'tetrahedra':len(c),'bath_area_m2':float(data['areas_m2'].sum()),'bath_owner_body':300,
       'known_external_W':r['external_total_power_w'],'raw_relative_error':float(identity['raw_bath_W']/r['external_total_power_w']-1),
       'raw_signed_powers':signed(data['power_W']),'identity':identity,'partitions':rows,'weighted_support_partitions':jrows,
       'normal_height_um_quantiles':quant(data['normal_height_m']*1e6),'tangential_face_edge_um_quantiles':quant(data['tangential_face_max_edge_m']*1e6),
       'apex_offset_over_normal_quantiles':quant(np.linalg.norm(data['apex_offset_xy_m'],axis=1)/data['normal_height_m']),
       'bath_nodal_T_span_max_K':float(data['bath_T_span_K'].max()),'node_bijection_max_m':distance,
       'local_physical_error_known':False,'qualified_recovery':False,'boundary_scope':'Kovar underside300K only; exposed glass/pin surfaces adiabatic TEST boundary, not OEM environment'}
    write(out/'audit.json',result);print(label,'raw',result['raw_relative_error'],'signed',result['raw_signed_powers'],'identity',identity,flush=True);return result

def run(out):
    if out.exists():raise ValueError('New study output required')
    out.mkdir(parents=True);results=[audit(label,mesh,case,out/label) for label,mesh,case in CASES]
    write(out/'summary.json',{'cases':results,'plan_sha256':sha(PLAN),'new_solver_run':False,'approved_report_changed':False})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.out.resolve())
