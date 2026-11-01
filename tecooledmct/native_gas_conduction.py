"""Single native-void conduction-only control, with independent P1 flux audit.

The mesh, Elmer solve and audit are separate bounded steps. No device temperature
is predicted: every wall temperature is a registered analytic Dirichlet control.
"""
import argparse
from collections import defaultdict
import os
from pathlib import Path
import subprocess
import threading
import time

import numpy as np

from .native_gas_audit import ROOT, PACKAGE, read, write, sha, regime
from .flux_presolder_common import affine_geometry, boundary_owners, outward_vectors

K_GAS = .0259
GAS_BODY = 8000
BOUNDARY_OFFSET = 20000


def profile(points, top):
    """Common stack trace; endpoints are not silently clipped."""
    points = np.asarray(points)
    u = (points[...,2]-.0015)/(top-.0015)
    if not np.isfinite(u).all() or np.any(u < -1e-10) or np.any(u > 1+1e-10):
        raise ValueError('Stack wall lies outside registered temperature control')
    return 300.-50.*u*u*(3.-2.*u)


def reservoir(body):
    return body == 300 or 401 <= body <= 409 or 501 <= body <= 509 or 7301 <= body <= 7303


def residual_and_flux(points, cells, temperature, faces):
    """Independent affine-basis residual and raw one-sided boundary gradient."""
    volume, basis = affine_geometry(points,cells)
    gradient = np.einsum('ei,eij->ej',temperature[cells]-300.,basis)
    local = K_GAS*volume[:,None]*np.einsum('eij,ej->ei',basis,gradient)
    residual = np.zeros(len(points));np.add.at(residual,cells.ravel(),local.ravel())
    owners = boundary_owners(cells,faces)
    vectors = outward_vectors(points,cells,faces,owners)
    raw = -K_GAS*np.einsum('ij,ij->i',gradient[owners],vectors)
    return residual,raw,gradient,owners,vectors,volume


def analytic_controls():
    """Six-tet 1 mm cube: affine slab flux, uniform zero, passive work."""
    points = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],
                       [0,0,1],[1,0,1],[1,1,1],[0,1,1]],float)*.001
    cells = np.array([[0,1,2,6],[0,2,3,6],[0,3,7,6],
                      [0,7,4,6],[0,4,5,6],[0,5,1,6]])
    boundary = defaultdict(list)
    for i,c in enumerate(cells):
        for omit in range(4):boundary[tuple(sorted(np.delete(c,omit)))].append(i)
    faces=np.array([f for f,v in boundary.items() if len(v)==1])
    T=300.-50.*points[:,2]/.001
    r,q,g,_,vectors,v=residual_and_flux(points,cells,T,faces)
    bottom=np.all(points[faces,2]==0,axis=1);top=np.all(points[faces,2]==.001,axis=1)
    exact=K_GAS*.001**2*50/.001
    uniform=residual_and_flux(points,cells,np.full(8,300.),faces)
    error=max(abs(q[top].sum()/exact-1),abs(q[bottom].sum()/exact+1))
    zero=max(abs(uniform[0]).max(),abs(uniform[1]).max())
    work=float((T-300.)@r);dissipation=float(K_GAS*np.sum(v*np.sum(g*g,axis=1)))
    if error>1e-12 or zero>1e-15 or not np.isclose(work,dissipation,rtol=1e-12) or work<=0:
        raise ValueError('Independent analytic/passive operator controls failed')
    return {'slab_exact_Q_w':exact,'slab_raw_relative_error':error,
            'uniform_max_W':zero,'work_W_K':work,'dissipation_W_K':dissipation,'passed':True}


def mesh(out, geometry):
    out,geometry=Path(out).resolve(),Path(geometry).resolve();start=time.monotonic()
    if out.exists():raise ValueError('One mesh only; output must be absent')
    out.mkdir(parents=True)
    status={'stage':'geometry read','mesh_attempts':0,'PDE_solves':0,'qualified':False}
    def save(**kw):
        status.update(kw);status['elapsed_seconds']=time.monotonic()-start;write(out/'mesh_status.json',status)
    save()
    import gmsh
    gmsh.initialize();gmsh.option.setNumber('General.NumThreads',4);gmsh.option.setNumber('General.Terminal',1)
    timer=None
    try:
        geom=read(geometry/'geometry.json');faces=read(geometry/'gas_faces.json')
        if not geom['qualified'] or sha(geometry/'gas_only.brep')!=geom['BREP_sha256']:
            raise ValueError('Geometry not qualified or changed')
        entities=gmsh.model.occ.importShapes(str(geometry/'gas_only.brep'),highestDimOnly=True)
        gmsh.model.occ.synchronize()
        if len(entities)!=1 or entities[0][0]!=3:raise ValueError('Gas-only BREP has extra/missing solids')
        gas=entities[0][1];occ=gmsh.model.occ
        if not np.isclose(occ.getMass(3,gas),geom['volume_m3'],rtol=1e-8) or np.max(abs(np.array(occ.getBoundingBox(3,gas))-geom['bbox_m']))>1e-10:
            raise ValueError('SI BREP round trip failed')
        owned={};used=set()
        for _,tag in gmsh.model.getEntities(2):
            area=occ.getMass(2,tag);box=np.array(occ.getBoundingBox(2,tag));center=np.array(occ.getCenterOfMass(2,tag))
            candidates=[f for f in faces if np.isclose(area,f['area_m2'],rtol=1e-8,atol=1e-18)
                        and np.max(abs(box-f['bbox_m']))<1e-10 and np.linalg.norm(center-f['centroid_m'])<1e-10]
            if len(candidates)!=1 or candidates[0]['tag'] in used:raise ValueError('Ambiguous BREP boundary source ownership')
            f=candidates[0];used.add(f['tag']);owned[tag]=f['body']
        if len(owned)!=len(faces):raise ValueError('Incomplete BREP face coverage')
        gmsh.model.addPhysicalGroup(3,[gas],GAS_BODY,'native_internal_gas')
        for body in sorted(set(owned.values())):
            gmsh.model.addPhysicalGroup(2,[f for f,b in owned.items() if b==body],BOUNDARY_OFFSET+body,'gas_solid_'+str(body))
        m=read(PACKAGE/'manifest.json')
        stack_top=max(box[2]+box[5] for b in m['bodies'] if 'boxes_m' in b for box in b['boxes_m'])
        controls={'wall_temperature':'reservoir 300 K; stack 300-50*u^2*(3-2*u), u=(z-.0015)/(stack_top-.0015)',
                  'stack_top_m':stack_top,'z0_m':.0015,'k_w_mk':K_GAS,'pressure_pa':101325.,
                  'regime':regime(.00015,.00815,101325.),'controls':analytic_controls(),
                  'scope':'One-way prescribed analytic walls, constant-k N2 conduction-only limiting baseline; buoyancy deliberately suppressed',
                  'geometry_sha256':sha(geometry/'geometry.json'),'BREP_sha256':sha(geometry/'gas_only.brep'),
                  'source_sha256':sha(__file__),'mesh_attempts_authorized':1,'mesh_sizes_m':{'core':.00018,'outer':.0006,'min':.00003},
                  'tet_target':300000,'tet_hard_stop':500000,'mesh_timeout_seconds':180,'PDE_timeout_seconds':120}
        write(out/'controls.json',controls)
        gmsh.option.setNumber('Mesh.MeshSizeMin',.00003);gmsh.option.setNumber('Mesh.MeshSizeMax',.0006)
        gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',16);gmsh.option.setNumber('Mesh.ElementOrder',1)
        gmsh.option.setNumber('Mesh.RandomSeed',20261101);gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
        box=gmsh.model.mesh.field.add('Box');gmsh.model.mesh.field.setNumber(box,'VIn',.00018);gmsh.model.mesh.field.setNumber(box,'VOut',.0006)
        for key,value in {'XMin':-.0034,'XMax':.0034,'YMin':-.0034,'YMax':.0034,'ZMin':.0015,'ZMax':.0057}.items():
            gmsh.model.mesh.field.setNumber(box,key,value)
        gmsh.model.mesh.field.setAsBackgroundMesh(box)
        save(stage='one registered mesh',mesh_attempts=1)
        timer=threading.Timer(180,lambda:os._exit(124));timer.daemon=True;timer.start()
        gmsh.model.mesh.generate(3)
        timer.cancel()
        tags,xyz,_=gmsh.model.mesh.getNodes();order=np.argsort(tags);tags=np.array(tags)[order];points=np.array(xyz).reshape(-1,3)[order]
        kinds,_,arrays=gmsh.model.mesh.getElements(3,gas)
        if list(kinds)!=[4]:raise ValueError('Only linear tetrahedra allowed')
        cells=np.searchsorted(tags,arrays[0]).reshape(-1,4)
        save(stage='mesh gates',tetrahedra=len(cells),nodes=len(points))
        if len(cells)>500000:raise ValueError('Registered 500k tetrahedron hard cap exceeded; no solve')
        determinants=np.linalg.det(points[cells[:,1:]]-points[cells[:,:1]])
        if np.min(determinants)<=0:raise ValueError('Nonpositive gas tetrahedron')
        triangles=[];bodies=[];native_faces=[]
        for face,body in owned.items():
            kinds,_,arrays=gmsh.model.mesh.getElements(2,face)
            if list(kinds)!=[2]:raise ValueError('Missing/unsupported gas interface mesh')
            f=np.searchsorted(tags,arrays[0]).reshape(-1,3);triangles.append(f);bodies.extend([body]*len(f));native_faces.extend([face]*len(f))
        triangles=np.concatenate(triangles);bodies=np.array(bodies);native_faces=np.array(native_faces)
        gmsh.write(str(out/'gas.msh'))
        np.savez_compressed(out/'mesh.npz',points=points,cells=cells,faces=triangles,solid_bodies=bodies,native_faces=native_faces)
        # Reconstruct ALL tetrahedral boundary faces independently, including
        # surfaces a missing physical group would otherwise silently omit.
        all_faces=np.sort(np.concatenate([np.delete(cells,i,axis=1) for i in range(4)]),axis=1)
        unique,count=np.unique(all_faces,axis=0,return_counts=True)
        if count.max()>2:raise ValueError('Nonmanifold tetrahedral mesh')
        exposed=unique[count==1];given=np.sort(triangles,axis=1)
        key=lambda a: a[np.lexsort(a.T[::-1])]
        if not np.array_equal(key(exposed),key(given)):raise ValueError('Missing/duplicate gas boundary triangles')
        volume=determinants.sum()/6
        write(out/'mesh_audit.json',{'nodes':len(points),'tetrahedra':len(cells),'boundary_triangles':len(triangles),
              'CAD_faces':len(owned),'gas_volume_m3':volume,'CAD_volume_m3':geom['volume_m3'],
              'volume_relative_tessellation_error':volume/geom['volume_m3']-1,'minimum_signed_tet_m3':determinants.min()/6,
              'all_boundary_faces_owned_once':True,'all_elements_positive':True,'target_300k_passed':len(cells)<=300000,
              'hard_500k_passed':True,'mesh_sha256':sha(out/'mesh.npz'),'gmsh_version':gmsh.__version__})
        save(qualified=True,stage='COMPLETE')
        return True
    except Exception as exc:
        save(stage='STOP',reason=str(exc));print('Phase C mesh STOP:',exc);return False
    finally:
        if timer:timer.cancel()
        gmsh.finalize()


def execute(command,folder,name,seconds):
    path=Path(folder)/(name+'.log');start=time.monotonic()
    with path.open('w') as f:
        try:
            result=subprocess.run(command,cwd=folder,stdout=f,stderr=subprocess.STDOUT,timeout=seconds)
            status={'returncode':result.returncode,'timeout':False}
        except subprocess.TimeoutExpired:status={'returncode':None,'timeout':True}
    status['elapsed_seconds']=time.monotonic()-start;write(Path(folder)/(name+'_status.json'),status)
    if status['returncode']!=0:raise ValueError(name+' failed or exceeded registered deadline')


def solve(out):
    out=Path(out).resolve()
    if not read(out/'mesh_status.json')['qualified']:raise ValueError('No qualified gas mesh')
    if (out/'case.sif').exists():raise ValueError('One PDE only; never overwrite')
    controls=read(out/'controls.json');m=np.load(out/'mesh.npz');bodies=sorted(set(m['solid_bodies'].tolist()))
    execute(['ElmerGrid','14','2','gas.msh','-out','elmer'],out,'grid',60)
    top=controls['stack_top_m'];u=f'((tx-0.0015)/{top-.0015:.17g})'
    text=f'''Header
 Mesh DB "{out/'elmer'}" "."
End
Simulation
 Coordinate System = Cartesian 3D
 Simulation Type = Steady State
 Steady State Max Iterations = 1
 Post File = "fields.vtu"
End
Equation 1
 Active Solvers(1) = 1
End
Solver 1
 Equation = "Heat Equation"
 Variable = Temperature
 Procedure = "HeatSolve" "HeatSolver"
 Linear System Solver = Iterative
 Linear System Iterative Method = BiCGStab
 Linear System Preconditioning = ILU1
 Linear System Convergence Tolerance = 1.0e-12
 Linear System Max Iterations = 2000
 Nonlinear System Max Iterations = 1
End
Body 1
 Target Bodies(1) = {GAS_BODY}
 Equation = 1
 Material = 1
End
Material 1
 Heat Conductivity = Real {K_GAS}
 Density = Real 1
 Heat Capacity = Real 1
End
'''
    for i,body in enumerate(bodies,1):
        law='Real 300' if reservoir(body) else f'Variable Coordinate 3\n  Real MATC "300-50*{u}^2*(3-2*{u})"'
        text+=f'Boundary Condition {i}\n Target Boundaries(1) = {BOUNDARY_OFFSET+body}\n Temperature = {law}\nEnd\n'
    (out/'case.sif').write_text(text)
    write(out/'PDE_registration.json',{'PDE_solves':1,'k_w_mk':K_GAS,'controls_sha256':sha(out/'controls.json'),
         'mesh_sha256':sha(out/'mesh.npz'),'SIF_sha256':sha(out/'case.sif'),'solver_timeout_seconds':120})
    execute(['ElmerSolver','case.sif'],out,'solver',120)


def audit(out):
    import meshio
    from reports.field_geometry import node_map,cell_map
    out=Path(out).resolve();controls=read(out/'controls.json');m=np.load(out/'mesh.npz')
    points,cells,faces,bodies=[m[k] for k in ('points','cells','faces','solid_bodies')]
    fieldpath=next(out.rglob('fields*.vtu'));field=meshio.read(fieldpath)
    ix,distance=node_map(points,field.points);cell_map(cells,np.argsort(ix)[field.cells_dict['tetra']])
    T=field.point_data['temperature'].ravel()[ix]
    r,raw,gradient,owner,vectors,volume=residual_and_flux(points,cells,T,faces)
    area=np.linalg.norm(vectors,axis=1);fixed=np.unique(faces);free=np.ones(len(points),bool);free[fixed]=False
    expected=np.full(len(points),np.nan)
    conflict=0.
    for body in np.unique(bodies):
        nodes=np.unique(faces[bodies==body]);values=np.full(len(nodes),300.) if reservoir(body) else profile(points[nodes],controls['stack_top_m'])
        seen=np.isfinite(expected[nodes])
        if seen.any():conflict=max(conflict,float(abs(expected[nodes][seen]-values[seen]).max()))
        expected[nodes]=values
    if conflict>1e-8:raise ValueError('Incompatible registered wall temperatures at shared boundary nodes')
    raw_relative=abs(raw.sum())/max(raw[raw>0].sum(),-raw[raw<0].sum())
    nodal_area=np.zeros(len(points));np.add.at(nodal_area,faces.ravel(),np.repeat(area/3,3))
    allocated=-r[faces]*(area[:,None]/3)/nodal_area[faces]
    reaction_face=allocated.sum(1)
    budget=[]
    manifest={b['id']:b for b in read(PACKAGE/'manifest.json')['bodies']}
    for body in sorted(set(bodies)):
        selected=bodies==body;b=manifest.get(int(body),{'name':{7301:'cap_shell',7302:'cap_roof',7303:'window'}[int(body)]} if body>=7301 else {})
        budget.append({'body':int(body),'name':b['name'],'kind':b.get('kind','enclosure'),'stage_zero_based':b.get('stage'),
                       'area_m2':area[selected].sum(),'raw_out_of_gas_W':raw[selected].sum(),
                       'allocated_reaction_into_solid_W':reaction_face[selected].sum()})
    dissipation=K_GAS*np.sum(volume*np.sum(gradient*gradient,axis=1));work=(T-300.)@r
    entropy=K_GAS*np.sum(volume*np.sum(gradient*gradient,axis=1)/T[cells].mean(1)**2)
    metrics={'scope':controls['scope'],'new_device_temperature':None,'gas':'N2','pressure_pa':101325.,'k_w_mk':K_GAS,
       'nodes':len(points),'tetrahedra':len(cells),'temperature_min_K':T.min(),'temperature_max_K':T.max(),
       'boundary_trace_max_error_K':float(abs(T[fixed]-expected[fixed]).max()),'trace_conflict_K':conflict,
       'free_max_residual_W':float(abs(r[free]).max()) if free.any() else 0.,'free_L1_residual_W':float(abs(r[free]).sum()),
       'global_reaction_sum_W':r.sum(),'allocated_global_into_solid_W':reaction_face.sum(),
       'raw_outward_sum_W':raw.sum(),'raw_global_relative_mismatch':raw_relative,
       'raw_positive_W':raw[raw>0].sum(),'raw_negative_W':raw[raw<0].sum(),
       'work_W_K':work,'dissipation_W_K':dissipation,'entropy_production_W_K':entropy,
       'field_sha256':sha(fieldpath),'field_path':str(fieldpath.relative_to(out)),
       'node_map_max_distance_m':distance,'surface_allocation':'Nodal reactions split by incident boundary-triangle area at shared nodes; not raw face gradient',
       'bodies':budget,'regime':controls['regime'],'analytic_controls':controls['controls']}
    gates={'bounded_250_300_K':bool(T.min()>=250-1e-6 and T.max()<=300+1e-6),
           'boundary_trace_1e_6_K':bool(metrics['boundary_trace_max_error_K']<1e-6),
           'free_reaction_max_1nW':bool(metrics['free_max_residual_W']<1e-9),
           'free_reaction_L1_1nW':bool(metrics['free_L1_residual_W']<1e-9),
           'global_reaction_1nW':bool(abs(r.sum())<1e-9 and abs(reaction_face.sum())<1e-9),
           'raw_global_1percent':bool(raw_relative<.01),
           'passive_work_identity':bool(work>0 and np.isclose(work,dissipation,rtol=1e-9)),
           'positive_entropy':bool(entropy>0)}
    metrics.update(gates=gates,registered_numerical_gates_passed=all(gates.values()),physical_device_validation=False)
    np.savez_compressed(out/'audited_field.npz',temperature_K=T,gradient_K_m=gradient,
                        raw_face_power_W=raw,allocated_face_power_W=reaction_face,face_owner_tet=owner,area_vectors_m2=vectors)
    write(out/'result.json',metrics)
    print('Standalone gas control gates:',gates)
    return metrics


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['mesh','solve','audit']);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry',type=Path)
    args=p.parse_args()
    if args.stage=='mesh':mesh(args.out,args.geometry)
    elif args.stage=='solve':solve(args.out)
    else:audit(args.out)
