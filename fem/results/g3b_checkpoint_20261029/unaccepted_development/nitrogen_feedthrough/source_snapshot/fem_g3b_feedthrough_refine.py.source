"""Conformal glass/pin/header junction refinement; unchanged TEC and cavity.

The source steady field may fail ONLY the direct-bath discretization gate. It is
used strictly as a P1-prolongated initial guess, never as accepted performance.
"""
import argparse,itertools,json,shutil
from pathlib import Path
import numpy as np
from scipy.sparse import hstack,csr_matrix,load_npz,save_npz
from scipy.spatial import cKDTree
from .g2d_data import ROOT,sha,dump
from .fem_g3b_data import preserve
from .fem_g1 import tetra_geometry
from .fem_g2a import mesh_adjacency
from .fem_g2b_connectivity import connectivity
from .fem_g2c_mesh import verify_elmer_tetra_mapping
from .fem_g1_run import execute
from .fem_g2b_physics import execute_solver
from .fem_g3b_physics import write_case
from .fem_g3b_post import postprocess

PAIRS=list(itertools.combinations(range(4),2))


from .fem_g3b_bath_refine import bisect_edges,prolong


def build(parent,mesh,operator,rounds=2):
    import gmsh,meshio
    preserve()
    if not 1<=rounds<=3:raise ValueError('One to three bounded bisection rounds required')
    if mesh.exists() or operator.exists():raise ValueError('Keep existing meshes; choose new labels')
    old=np.load(parent/'mesh.npz');p,c,b,f,bt=[old[k] for k in ('points','cells','bodies','faces','boundaries')];pi=old['patch_index'];solver=old['solver_boundaries'];m=json.loads((parent/'manifest.json').read_text());a=json.loads((parent/'audit.json').read_text());pins=np.array(m['package_registry']['feedthroughs']['centers_xy_m']);original_nodes=len(p);midpoints=[];counts=[]
    for iteration in range(rounds):
        adj=mesh_adjacency(c)
        if iteration==0:
            center=p[c].mean(axis=1);distance=np.min(np.linalg.norm(center[:,None,:2]-pins,axis=2),axis=1);ids=np.flatnonzero((distance<.0007)&(np.abs(center[:,2]-m['header_bottom_m'])<.00015))
        else:
            bath=f[bt==101];cent=p[bath].mean(axis=1);near=np.min(np.linalg.norm(cent[:,None,:2]-pins,axis=2),axis=1)<.0013;ids=np.array([adj[tuple(sorted(t))][0] for t in bath[near]])
        edges={tuple(sorted((int(row[i]),int(row[j])))) for row in c[ids] for i,j in PAIRS}

        skin_edges={tuple(sorted((int(row[i]),int(row[j])))) for row in f[pi>=0] for i,j in ((0,1),(1,2),(2,0))}
        if edges & skin_edges:raise ValueError('Refinement would alter a cavity facet')
        before=len(f);p,c,b,f,bt,mid=bisect_edges(p,c,b,f,bt,edges);midpoints.extend(mid.tolist());pi=np.r_[pi,np.full(len(f)-before,-1)];solver=bt.copy();solver[pi>=0]=20000+pi[pi>=0]
        counts.append({'round':iteration+1,'selected_cells':len(np.unique(ids)),'selected_edges':len(edges),'nodes':len(p),'tetrahedra':len(c)})
        if len(p)>300000:raise ValueError('Declared 300000-node resource cap exceeded')
    if not np.array_equal(f[pi>=0],old['faces'][old['patch_index']>=0]):raise ValueError('Cavity changed')
    if not np.array_equal(c[b<=m['original_TEC_domains']],old['cells'][old['bodies']<=m['original_TEC_domains']]):raise ValueError('TEC discretization changed')
    vol,_=tetra_geometry(p,c);oldvol,_=tetra_geometry(old['points'],old['cells']);adj=mesh_adjacency(c);contacts={}
    for face,ids in adj.items():
        if len(ids)>2:raise ValueError('Nonmanifold refined mesh')
        if len(ids)==2 and b[ids[0]]!=b[ids[1]]:
            pair=tuple(sorted((int(b[ids[0]]),int(b[ids[1]]))));x=p[list(face)];contacts[pair]=contacts.get(pair,0)+np.linalg.norm(np.cross(x[1]-x[0],x[2]-x[0]))/2
    expected={tuple(x['bodies']):x for x in m['contacts']}
    if set(contacts)!=set(expected):raise ValueError('Refined contact topology changed')
    volumes={}
    for body in m['bodies']:
        vv=float(vol[b==body['id']].sum());base=float(oldvol[old['bodies']==body['id']].sum())
        if not np.isclose(vv,base,rtol=1e-12,atol=1e-22):raise ValueError('Refinement changed body volume')
        volumes[body['name']]=vv
    for face,tag in zip(f,bt):
        if len(adj[tuple(sorted(face))])!=(2 if tag>=1001 else 1):raise ValueError('Refined face tags nonconformal')
    for pair,area in contacts.items():
        if not np.isclose(area,expected[pair]['area_m2'],rtol=.01 if expected[pair].get('curved') else 1e-7,atol=1e-20):raise ValueError('Contact area gate')
    conductor={x['id'] for x in m['bodies'][:m['original_TEC_domains']] if x['material']!='Alumina'};proof=connectivity(c,b,conductor)
    if not proof['passed']:raise ValueError('Refined face connectivity failed')
    mesh.mkdir(parents=True);operator.mkdir(parents=True);np.savez_compressed(mesh/'mesh.npz',points=p,cells=c,bodies=b,faces=f,boundaries=bt);np.savez_compressed(operator/'mesh.npz',points=p,cells=c,bodies=b,faces=f,boundaries=bt,solver_boundaries=solver,patch_index=pi);np.savez_compressed(operator/'prolongation.npz',original_nodes=original_nodes,midpoint_edges=np.array(midpoints,dtype=int));dump(mesh/'manifest.json',m);dump(operator/'manifest.json',m)
    for target,tags in ((mesh,bt),(operator,solver)):
        meshio.write(target/'connected.msh',meshio.Mesh(p,[('triangle',f),('tetra',c)],cell_data={'gmsh:physical':[tags,b],'gmsh:geometrical':[tags,b]}),file_format='gmsh22',binary=False);execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],target,'grid')
    gmsh.initialize();gmsh.logger.start()
    try:
        gmsh.open(str(mesh/'connected.msh'));types,ids,_=gmsh.model.mesh.getElements(3);quality=np.concatenate([gmsh.model.mesh.getElementQualities(ix,'minSICN') for typ,ix in zip(types,ids) if typ==4]);minimum=float(quality.min())
    finally:
        (mesh/'gmsh.log').write_text('\n'.join(gmsh.logger.get()));gmsh.logger.stop();gmsh.finalize()
    if minimum<=0:raise ValueError('Nonpositive refined quality')
    geometry={'passed':True,'nodes':len(p),'tetrahedra':len(c),'domains':len(m['bodies']),'min_sicn':minimum,'graph':json.loads((parent.parent/'mesh_h1/audit.json').read_text())['graph'],'connectivity':proof,'volumes_m3':volumes,'actual_contact_areas_m2':{f'{x}:{y}':float(v) for (x,y),v in contacts.items()},'package_chordal_volume_area_tolerance':.01,'TEC_box_tolerance':1e-7,'elmer_mapping':verify_elmer_tetra_mapping(mesh),'mesh_npz_sha256':sha(mesh/'mesh.npz'),'method':'first complete-edge-star round on all material cells within0.7mm radius of each feedthrough and0.15mm of header bottom; optional following bath neighborhoods radius1.3mm; chordal geometry, TEC and cavity preserved','rounds':counts,'source_operator':str(parent),'source_operator_mesh_sha256':sha(parent/'mesh.npz'),'source_sha256':{str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))}}
    dump(mesh/'audit.json',geometry)
    for name in ('patches.json','operators.npz'):shutil.copy2(parent/name,operator/name)
    weights=load_npz(parent/'weights.npz');save_npz(operator/'weights.npz',hstack([weights,csr_matrix((weights.shape[0],len(p)-original_nodes))],format='csr'))
    er=np.loadtxt(operator/'elmer/mesh.nodes');dist,ix=cKDTree(er[:,2:5]).query(p);ids=er[ix,0].astype(int);expected_faces={tuple(sorted(ids[t])):int(tag) for t,tag in zip(f,solver)};actual={}
    for line in (operator/'elmer/mesh.boundary').read_text().splitlines():
        v=list(map(int,line.split()));actual[tuple(sorted(v[5:]))]=v[1]
    if dist.max()>1e-12 or actual!=expected_faces:raise ValueError('Actual refined boundary mapping failed')
    a.update(source_mesh_sha256=sha(mesh/'mesh.npz'),mesh_sha256=sha(operator/'mesh.npz'),elmer_mapping=verify_elmer_tetra_mapping(operator),actual_boundary_mapping_verified=True,source_sha256={**a['source_sha256'],str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},inherited_ray_execution={'parent':str(parent),'operators_npz_sha256':sha(parent/'operators.npz'),'new_rays_traced':0,'cavity_triangles_and_patch_weights_unchanged':True},bulk_refinement=counts);dump(operator/'audit.json',a);print(json.dumps(geometry,indent=2),flush=True)


def run(operator,case,source):
    import meshio
    preserve();r=json.loads((source/'metrics.json').read_text());ex=json.loads((source/'execution.json').read_text())
    if ex['solver_status']['exit_code'] or ex['solver_status']['nonlinear_last_relative_change']>=1e-9 or not all(v for k,v in r['checks'].items() if k!='direct_bath_1pct'):raise ValueError('Initial source must be genuine converged physics with only the bath-gradient gate possibly failed')
    field=source/r['field_source']
    if sha(field)!=ex['vtu_sha256'] or sha(source/'case.sif')!=ex['sif_sha256']:raise ValueError('Changed genuine source field/SIF')
    if case.exists():raise ValueError('Keep previous execution')
    names=('data','reference','exchange','physics','bath_refine','feedthrough_refine');sources=[ROOT/'tecooledmct'/f'fem_g3b_{n}.py' for n in names];hashes={str(p.relative_to(ROOT)):sha(p) for p in sources};case.mkdir(parents=True);snap=case/'source_snapshot';snap.mkdir()
    for p in sources:(snap/(p.name+'.source')).write_bytes(p.read_bytes())
    write_case(operator,case,gas='N2',pressure=100.);parent=Path(r['operator_path']);old=np.load(parent/'mesh.npz');f=meshio.read(field);dist,ix=cKDTree(f.points).query(old['points']);ff={k.lower():v.ravel()[ix] for k,v in f.point_data.items()};values=prolong(np.column_stack([ff['temperature'],ff['potential']]),np.load(operator/'prolongation.npz')['midpoint_edges']);d=np.load(operator/'mesh.npz');er=np.loadtxt(operator/'elmer/mesh.nodes');dd,ix=cKDTree(er[:,2:5]).query(d['points']);ordered=np.empty_like(values);ordered[er[ix,0].astype(int)-1]=values
    if dist.max()>1e-12 or dd.max()>1e-12 or len(values)!=len(d['points']):raise ValueError('P1 warm-start mapping failed')
    np.savetxt(case/'InitialFields.dat',ordered,fmt='%.17e',header=str(len(ordered)),comments='');lib=case/'initial_library';lib.mkdir();shutil.copy2(source/'initial_library/Initial.F90',lib/'Initial.F90');execute(['elmerf90','-ffree-line-length-none','-o','G3bInitial','Initial.F90'],lib,'compile');sif=(case/'case.sif').read_text();a=sif.index('Initial Condition 1\n');z=sif.index('\nEnd',a);sif=sif[:a]+f'Initial Condition 1\n Temperature = Variable Coordinate 1\n  Real Procedure "{(lib/"G3bInitial").resolve()}" "InitialT"\n Potential = Variable Coordinate 1\n  Real Procedure "{(lib/"G3bInitial").resolve()}" "InitialPhi"'+sif[z:];(case/'case.sif').write_text(sif);meta=json.loads((case/'case.json').read_text());meta['initial_actual_state']={'source':str(source),'source_accepted':bool(r['passed']),'source_failure_scope':'direct bath-gradient discretization only; never accepted performance','source_vtu_sha256':sha(field),'initial_field_sha256':sha(case/'InitialFields.dat'),'method':'exact conformal P1 edge-midpoint prolongation of actual T/phi as initial guess; final fields both solved'};dump(case/'case.json',meta)
    status=execute_solver(case,timeout=1800)
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Source changed during actual PDE')
    dump(case/'execution.json',{'source_sha256':hashes,'solver_status':status,'operator_path':str(operator),'mesh_sha256':sha(operator/'mesh.npz'),'sif_sha256':sha(case/'case.sif'),'vtu_sha256':sha(sorted(case.glob('fields*.vtu'))[-1])});result=postprocess(operator,case);result['solver_status']=status;dump(case/'metrics.json',result)
    if not result['passed']:raise ValueError('Bath-refined acceptance failed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--rounds',type=int,default=1);p.add_argument('--parent',type=Path,default=ROOT/'outputs/fem-g3b/operator_h1');p.add_argument('--mesh',type=Path,default=ROOT/'outputs/fem-g3b/mesh_feedthrough');p.add_argument('--operator',type=Path,default=ROOT/'outputs/fem-g3b/operator_feedthrough');p.add_argument('--case',type=Path,default=ROOT/'outputs/fem-g3b/nitrogen_feedthrough');p.add_argument('--source',type=Path,default=ROOT/'outputs/fem-g3b/nitrogen_fine_verified');a=p.parse_args()
    if a.build:build(a.parent.resolve(),a.mesh.resolve(),a.operator.resolve(),a.rounds)
    else:run(a.operator.resolve(),a.case.resolve(),a.source.resolve())
