"""Source-only admissibility gate for the registered seven-port plate fixture.

No reference temperatures, mesh generation, PDE solve, or new thermal closure.
Failure is a scientific stop, not permission to add boundary conditions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np

from .fem_g1 import tetra_geometry

ROOT=Path(__file__).resolve().parents[1]
GEOM=ROOT/'fem/results/geometry_complete_checkpoint_20261030'
SIF=ROOT/'fem/results/corrected_coupled_thermal_20261030/cases/cu_off/case.sif'
NOTE=ROOT/'docs/PASSIVE_PLATE_PORT_AUDIT_20261031.md'
PORTS=('stage1_hot','stage1_cold','stage2_hot','stage2_cold','stage3_hot','stage3_cold','P174_side')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def write(p,obj):
    def native(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        raise TypeError(type(x).__name__)
    Path(p).write_text(json.dumps(obj,indent=2,default=native,allow_nan=False)+'\n')


def selection(manifest):
    by={b['id']:b for b in manifest['bodies']}
    selected={b['id'] for b in by.values() if b['kind']=='ceramic' or
              (b['kind'] in ('bridge','terminal') and b['material']=='Cu' and b.get('stage') in (0,1,2))}
    selected.update(range(184,193))
    if any(by[i]['material'] not in ('Cu','Alumina') for i in selected):raise ValueError('Non-passive material selected')
    return by,selected


def port_for(pair,by,selected,xyz):
    """Native patch ownership and actual leg endpoint, not all-Cu body channels."""
    outside=[b for b in pair if b not in selected]
    if len(outside)!=1:raise ValueError('Not a fixture cut interface')
    other=outside[0]
    if tuple(sorted(pair))==(174,192):return 6
    leg=by[other]
    if leg['kind']!='leg':return None
    z0=leg['boxes_m'][0][2];z1=z0+leg['boxes_m'][0][5]
    if np.max(abs(xyz[:,:,2]-z0))<1e-12:side=0
    elif np.max(abs(xyz[:,:,2]-z1))<1e-12:side=1
    else:raise ValueError('Unexpected non-end P/N contact')
    return 2*leg['stage']+side


def encoded(faces,node_count):
    f=np.sort(faces,axis=1).astype(np.int64)
    if node_count**3>=2**63:raise ValueError('Face encoding range exceeded')
    return (f[:,0]*node_count+f[:,1])*node_count+f[:,2]


def trace_collisions(points,faces,labels,port_count=7):
    """Disjoint face ownership can still give incompatible shared-edge traces."""
    nodes=[];edges=[]
    for port in range(port_count):
        f=faces[labels==port];nodes.append(np.unique(f))
        edges.append(np.unique(np.sort(f[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1),axis=0))
    records=[];edge_sets=[]
    dtype=np.dtype([('a',np.int64),('b',np.int64)])
    for i in range(port_count):
        for j in range(i+1,port_count):
            common_nodes=np.intersect1d(nodes[i],nodes[j])
            if not len(common_nodes):continue
            a=np.ascontiguousarray(edges[i],dtype=np.int64).view(dtype).ravel()
            b=np.ascontiguousarray(edges[j],dtype=np.int64).view(dtype).ravel()
            common=np.intersect1d(a,b).view(np.int64).reshape(-1,2)
            length=float(np.linalg.norm(points[common[:,1]]-points[common[:,0]],axis=1).sum()) if len(common) else 0.
            records.append({'ports':[PORTS[i],PORTS[j]],'shared_native_nodes':len(common_nodes),
                'shared_edges':len(common),'shared_edge_length_m':length,
                'independent_unit_values_compatible':length<1e-12,
                'witness_coordinates_m':points[common_nodes].tolist()})
            if len(common):edge_sets.append(common)
    return records,np.vstack(edge_sets) if edge_sets else np.empty((0,2),np.int64)


def decision(unmapped,collisions):
    reasons=[]
    if unmapped:reasons.append('Unregistered physical cut interfaces')
    if any(x['shared_edge_length_m']>=1e-12 for x in collisions):
        reasons.append('Independent constant-temperature ports meet on a positive-length native edge')
    return {'seven_port_admissible':not reasons,'stop_reasons':reasons,
        'operator_built':False,'passive_unit_solves_executed':0,'fixture_discretizations':0,
        'reference_temperature_fields_read':False,'extra_boundary_conditions_added':False}


def wedge_energy(k,length,angle,delta,inner,outer):
    """Analytic homogeneous wedge Dirichlet integral, W K, not a device fit.

    T=T0+delta*theta/angle gives integral k|grad T|² dV.
    Different constants on meeting faces cause logarithmic cutoff dependence.
    """
    if not np.isfinite([k,length,angle,delta,inner,outer]).all() or min(k,length,angle,inner)<=0 or outer<=inner:
        raise ValueError('Invalid analytic wedge')
    return k*length*delta**2/angle*np.log(outer/inner)


def audit():
    start=time.monotonic();ledger=read(GEOM/'checksums.json')['artifact_sha256']
    for name in ('manifest.json','mesh.npz'):
        if sha(GEOM/name)!=ledger[name]:raise ValueError('Source geometry identity changed')
    sif_ledger=read(SIF.parents[2]/'checksums.json')['artifact_sha256']
    if sha(SIF)!=sif_ledger['cases/cu_off/case.sif']:raise ValueError('Source SIF identity changed')
    manifest=read(GEOM/'manifest.json');by,selected=selection(manifest)
    names=sorted({b['material'] for b in by.values()});sif=SIF.read_text();materials={}
    for name in ('Cu','Alumina'):
        block=re.search(r'^Material '+str(names.index(name)+1)+r'\n(.*?)^End',sif,re.M|re.S).group(1)
        k=float(re.search(r'Heat Conductivity = Real ([^\n]+)',block).group(1))
        if not np.isfinite(k) or k<=0:raise ValueError('Nonpositive/nonfinite k')
        materials[name]={'k_w_mk':k,'constant':True}
    d=np.load(GEOM/'mesh.npz');p,c,bodies=(d[k] for k in ('points','cells','bodies'))
    volumes,_=tetra_geometry(p,c);body_rows=[]
    for bid in sorted(selected):
        actual=float(volumes[bodies==bid].sum());expected=by[bid]['expected_volume_m3']
        if actual<=0 or not np.isclose(actual,expected,rtol=1e-8,atol=1e-20):raise ValueError('Native volume/coverage mismatch')
        body_rows.append({'body':bid,'kind':by[bid]['kind'],'material':by[bid]['material'],'volume_m3':actual})
    # All native tetrahedron faces establish independent two-sided ownership.
    facets=c[:,[[1,2,3],[0,3,2],[0,1,3],[0,2,1]]].reshape(-1,3)
    codes=encoded(facets,len(p));order=np.argsort(codes);codes=codes[order];owner=np.repeat(bodies,4)[order]
    port_faces=[];port_labels=[];missing_faces=[];missing_labels=[];unmapped=[];patches=[];internal_count=0
    native_contact_faces=0;seen=set();old_side_faces=[];old_side_labels=[]
    for row in manifest['contacts']:
        pair=row['bodies']
        if not any(b in selected for b in pair):continue
        f=d['faces'][d['boundaries']==row['boundary_id']];xyz=p[f];key=encoded(f,len(p))
        if len(np.unique(key))!=len(f) or any(int(k) in seen for k in key):raise ValueError('Duplicate native contact face')
        seen.update(map(int,key));left=np.searchsorted(codes,key,side='left');right=np.searchsorted(codes,key,side='right')
        if np.any(right-left!=2):raise ValueError('Contact lacks two native tetrahedron owners')
        actual=np.sort(np.column_stack([owner[left],owner[left+1]]),axis=1)
        if not np.array_equal(actual,np.tile(sorted(pair),(len(f),1))):raise ValueError('Native face body ownership differs')
        a=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
        area=float(a.sum())
        if np.any(a<=0) or not np.isclose(area,row['area_m2'],rtol=1e-8,atol=1e-18):raise ValueError('Native contact area mismatch')
        native_contact_faces+=len(f)
        if tuple(pair) in ((183,192),(174,192)):
            old_side_faces.append(f);old_side_labels.extend([4 if pair[0]==183 else 6]*len(f))
        if all(b in selected for b in pair):internal_count+=1;continue
        port=port_for(pair,by,selected,xyz)
        rec={'bodies':pair,'boundary_id':row['boundary_id'],'area_m2':area,'triangles':len(f),
             'port':PORTS[port] if port is not None else None}
        patches.append(rec)
        if port is None:
            other=next(b for b in pair if b not in selected);rec={**rec,'excluded_kind':by[other]['kind']}
            missing_faces.append(f);missing_labels.extend([len(unmapped)]*len(f));unmapped.append(rec)
        else:port_faces.append(f);port_labels.extend([port]*len(f))
    pf=np.vstack(port_faces);labels=np.array(port_labels);collisions,conflict_edges=trace_collisions(p,pf,labels)
    old_side_collisions,_=trace_collisions(p,np.vstack(old_side_faces),np.array(old_side_labels))
    port_rows=[]
    for port,name in enumerate(PORTS):
        rows=[r for r in patches if r['port']==name]
        if not rows:raise ValueError('An empty registered port cannot be solved')
        port_rows.append({'port':name,'footprint_patches':len(rows),'area_m2':sum(r['area_m2'] for r in rows),
                          'native_nodes':len(np.unique(pf[labels==port])),'triangles':int(np.sum(labels==port))})
    # Patch-constant grouping has disjoint support: rank = occupied groups.
    rank=len(port_rows);patch_count=sum(r['footprint_patches'] for r in port_rows)
    result={'scope':'Native geometry/material and seven-port boundary admissibility ONLY; no new thermal solution',
        'selection':body_rows,'source_materials':materials,'native_tetrahedra_read':len(c),
        'audited_internal_contact_pairs':internal_count,'audited_contact_triangles':native_contact_faces,
        'two_sided_face_ownership_verified':True,'native_body_and_contact_geometry_verified':True,
        'ports':port_rows,'cut_patches':patches,'unmapped_physical_interfaces':unmapped,
        'trace_collisions':collisions,'previous_isothermal_side_closure_native_edge':old_side_collisions,
        'grouping':{'independent_patch_constants':patch_count,'scalar_rank':rank,
            'unrepresented_zero_group_mean_patch_modes':patch_count-rank,'arbitrary_nonisothermal_traces_representable':False},
        'decision':decision(unmapped,collisions),
        'comparisons':{'old_vs_finite_plate_flux_w':None,'spreading_attributed_excess_gap_flux_w':None,
            'archived_plate_volume_to_face_temperature_differences_k':None,'side_port_reaction_w':None,
            'meaning':'NOT IDENTIFIABLE / NOT RUN after admissibility stop; null is not zero'},
        'operator_checks':{'reciprocity':'NOT RUN','conservation':'NOT RUN','entropy':'NOT RUN',
            'reason':'No admissible seven-port operator or boundary basis was assembled'},
        'resource_registration':{'max_spacing_um':80,'max_active_cells':60000,'max_edges':200000,
            'max_build_plus_seven_solve_seconds':180,'cpus':4,'memory_gib':8},
        'source_only_audit_seconds':time.monotonic()-start,
        'new_numerical_release':False,'Rev3_modified':False,'next_science_priority':'Independent native interleg gas conduction; no more solid fits/grids/fixtures'}
    if result['decision']['seven_port_admissible']:
        raise RuntimeError('Audit unexpectedly admissible; stop for review rather than run an unimplemented operator')
    mf=np.vstack(missing_faces) if missing_faces else np.empty((0,3),int)
    keep=np.unique(np.r_[pf.ravel(),mf.ravel()]);remap=np.full(len(p),-1,int);remap[keep]=np.arange(len(keep))
    arrays={'points_m':p[keep],'native_node_ids':keep,'port_faces':remap[pf],'port_index':labels,
        'unmapped_faces':remap[mf],'unmapped_index':np.array(missing_labels),'conflict_edges':remap[conflict_edges]}
    return result,arrays,manifest


def figures(result,a,manifest,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection,Line3DCollection
    palette=plt.get_cmap('tab10').colors;plt.rcParams.update({'font.size':9,'savefig.dpi':210})
    fig=plt.figure(figsize=(12,5.5));ax=fig.add_subplot(121,projection='3d');p=a['points_m']*1e3
    for i,name in enumerate(PORTS):
        tris=p[a['port_faces'][a['port_index']==i]]
        ax.add_collection3d(Poly3DCollection(tris,facecolor=palette[i],edgecolor='none',alpha=.85))
    for b in manifest['bodies']:
        if b['kind']!='ceramic':continue
        x,y,z,dx,dy,dz=np.array(b['boxes_m'][0])*1e3
        for zz in (z,z+dz):ax.plot([x,x+dx,x+dx,x,x],[y,y,y+dy,y+dy,y],[zz]*5,color='#808080',lw=.6)
        ax.text(x+dx,y+dy,z,str(b['id']),size=8)
    for j in range(len(result['unmapped_physical_interfaces'])):
        tris=p[a['unmapped_faces'][a['unmapped_index']==j]]
        ax.add_collection3d(Poly3DCollection(tris,facecolor='#cf3f35',edgecolor='none',alpha=.20))
    ax.set(xlim=(-3.4,3.4),ylim=(-3.4,3.4),zlim=(1.4,5.5),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',
           title='Actual native footprint/cut triangles\nFour ceramic outlines; red = unmapped cuts')
    ax.set_box_aspect((1,1,.85));ax.view_init(23,-53)
    ax=fig.add_subplot(122,projection='3d')
    for i in (4,6):
        f=a['port_faces'][a['port_index']==i];tri=p[f]
        if i==4:
            mask=(tri.mean(1)[:,0]<-.60)&(tri.mean(1)[:,0]>-1.1)&(tri.mean(1)[:,1]>.05)&(tri.mean(1)[:,1]<.5)
            tri=tri[mask]
        ax.add_collection3d(Poly3DCollection(tri,facecolor=palette[i],edgecolor='#666666',linewidth=.4,alpha=.5))
    ax.add_collection3d(Line3DCollection(p[a['conflict_edges']],colors='#d62728',linewidths=3))
    ax.set(xlim=(-1.07,-.59),ylim=(.03,.52),zlim=(4.40,4.50),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',
           title='P174: actual shared native edge\nStage-3 hot footprint versus side patch')
    ax.set_box_aspect((1,1,.6));ax.view_init(25,-55)
    length=sum(x['shared_edge_length_m'] for x in result['trace_collisions'])*1e3
    fig.text(.52,.05,f'Red shared edge: {length:.6g} mm. Independent 0/1 basis\nvalues prescribe a discontinuous temperature trace here.',size=9)
    fig.text(.03,.012,'Source geometry only; no thermal field, fixture mesh or passive PDE solve. The P/N solids are excluded.',size=8)
    fig.subplots_adjust(left=.01,right=.98,bottom=.13,top=.90,wspace=.15)
    fig.savefig(out/'native_port_geometry.png');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8));names=[r['port'] for r in result['ports']]+['Unmapped: hot/presolder','Unmapped: cold/attach']
    areas=[r['area_m2']*1e6 for r in result['ports']]+[r['area_m2']*1e6 for r in result['unmapped_physical_interfaces']]
    y=np.arange(len(names));ax.barh(y,areas,color=[*palette[:7],'#cf3f35','#cf3f35'])
    ax.set(yticks=y,yticklabels=names,xscale='log',xlabel='Native cut-interface area (mm², logarithmic scale)',
           title='Seven registered groups do not cover all physical cut interfaces')
    for i,v in enumerate(areas):ax.text(v*1.08,i,f'{v:.6g}',va='center',fontsize=8)
    ax.set_xlim(.008,90);ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
    fig.text(.03,.015,'Areas establish boundary coverage, not heat-flow shares. Seven scalar groups also omit 170 independent patch-constant modes.',size=8)
    fig.tight_layout(rect=(0,.05,1,1));fig.savefig(out/'native_port_coverage.png');plt.close(fig)


def run(out):
    out=Path(out)
    if out.exists():raise ValueError('Use an absent output directory; preserve evidence')
    registration=NOTE.read_text().split('## Results')[0]
    result,arrays,manifest=audit();out.mkdir(parents=True)
    sources=('tecooledmct/passive_plate_audit.py','tecooledmct/fem_g1.py')
    result['registration']=registration
    result['source_sha256']={name:sha(ROOT/name) for name in sources}
    result['input_sha256']={str(p.relative_to(ROOT)):sha(p) for p in (GEOM/'manifest.json',GEOM/'mesh.npz',SIF)}
    write(out/'boundary_audit.json',result);np.savez_compressed(out/'native_boundary_geometry.npz',**arrays)
    figures(result,arrays,manifest,out)
    write(out/'checksums.json',{'artifact_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    result=run(args.out);print(json.dumps({'decision':result['decision'],'unmapped':result['unmapped_physical_interfaces'],
        'trace_collisions':result['trace_collisions'],'grouping':result['grouping']},indent=2))


if __name__=='__main__':main()
