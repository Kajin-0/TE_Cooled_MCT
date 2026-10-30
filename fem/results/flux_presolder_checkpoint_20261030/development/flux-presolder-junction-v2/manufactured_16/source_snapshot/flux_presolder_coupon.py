"""Bounded genuine 3D Elmer conduction coupons; never full-device predictions."""
import argparse, itertools, json, shutil
from pathlib import Path
import numpy as np
from .g2d_data import ROOT, sha, dump
from .flux_presolder_common import affine_geometry, outward_vectors, guard
from .fem_g1_run import execute
from reports.field_geometry import node_map


def extrude(points2, triangles, z, layer_body):
    """Conformal prism-to-tet split, fixed global edge diagonals across neighbors."""
    n=len(points2);triangles=np.sort(triangles,axis=1)
    p=np.vstack([np.column_stack([points2,np.full(n,h)]) for h in z]);cells=[];bodies=[]
    for i,body in enumerate(layer_body):
        a,b,c=(triangles[:,j]+i*n for j in range(3));A,B,C=a+n,b+n,c+n
        cells.extend([np.column_stack(v) for v in [(a,b,c,C),(a,b,B,C),(a,A,B,C)]])
        bodies.extend([np.broadcast_to(body,len(triangles))]*3)
    c=np.vstack(cells);b=np.concatenate(bodies).astype(int)
    sign=np.linalg.det(p[c[:,1:]]-p[c[:,:1]])
    if np.any(abs(sign)<1e-30):raise ValueError('Degenerate extrusion')
    neg=sign<0;c[neg,0],c[neg,1]=c[neg,1].copy(),c[neg,0].copy()
    return p,c,b


def skin(cells):
    faces=np.concatenate([np.delete(cells,i,axis=1) for i in range(4)])
    keys=np.sort(faces,axis=1);_,first,count=np.unique(keys,axis=0,return_index=True,return_counts=True)
    if np.max(count)>2:raise ValueError('Nonmanifold coupon')
    use=first[count==1];return faces[use],np.tile(np.arange(len(cells)),4)[use]


def solve(out,p,c,b,k,source,top=310.,bottom=300.,metadata=None):
    import meshio
    if len(p)>100000 or len(c)>300000:raise ValueError('Bounded coupon resource cap')
    out.mkdir(parents=True,exist_ok=False)
    sources=[ROOT/'tecooledmct'/('flux_presolder_'+n+'.py') for n in ('common','coupon')]
    hashes={str(x.relative_to(ROOT)):sha(x) for x in sources}
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for path in sources:shutil.copy2(path,snapshot/path.name)
    f,owner=skin(c);centres=p[f].mean(1);tags=np.full(len(f),3)
    tags[np.all(abs(p[f,2]-p[:,2].min())<1e-12,axis=1)]=1
    tags[np.all(abs(p[f,2]-p[:,2].max())<1e-12,axis=1)]=2
    np.savez_compressed(out/'mesh.npz',points=p,cells=c,bodies=b,faces=f,tags=tags)
    meshio.write(out/'coupon.msh',meshio.Mesh(p,[('triangle',f),('tetra',c)],cell_data={'gmsh:physical':[tags,b],'gmsh:geometrical':[tags,b]}),file_format='gmsh22',binary=False)
    execute(['ElmerGrid','14','2','coupon.msh','-out','elmer'],out,'grid',timeout=120)
    text=f'''Check Keywords Warn
Header
 Mesh DB "{(out/'elmer').resolve()}" "."
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
 Linear System Solver = Direct
 Linear System Direct Method = UMFPACK
 Nonlinear System Max Iterations = 1
 Nonlinear System Convergence Tolerance = 1e-12
End
Initial Condition 1
 Temperature = Real 305
End
Boundary Condition 1
 Target Boundaries(1) = 1
 Temperature = Real {bottom:.17g}
End
Boundary Condition 2
 Target Boundaries(1) = 2
 Temperature = Real {top:.17g}
End
'''
    for bid,value in k.items():
        text+=f'''Body {bid}
 Equation = 1
 Material = {bid}
 Body Force = {bid}
 Initial Condition = 1
End
Material {bid}
 Heat Conductivity = Real {value:.17g}
 Density = Real 1
 Heat Capacity = Real 1
End
Body Force {bid}
 Heat Source = Real {source.get(bid,0):.17g}
End
'''
    (out/'case.sif').write_text(text);status,_=execute(['ElmerSolver','case.sif'],out,'solver',timeout=120)
    if any(sha(ROOT/name)!=digest for name,digest in hashes.items()):raise ValueError('Runtime source changed')
    field_path=sorted(out.rglob('fields*.vtu'))[-1];field=meshio.read(field_path);ix,distance=node_map(p,field.points)
    t=np.asarray(next(v for name,v in field.point_data.items() if name.lower()=='temperature')).ravel()[ix]
    vol,g=affine_geometry(p,c);gt=np.einsum('ei,eij->ej',t[c],g);kc=np.array([k[int(v)] for v in b]);sc=np.array([source.get(int(v),0.) for v in b]);q=-kc[:,None]*gt
    av=outward_vectors(p,c,f,owner);flux=np.einsum('ij,ij->i',q[owner],av);rt=np.zeros(len(p));local=vol[:,None]*(kc[:,None]*np.einsum('eij,ej->ei',g,gt)-sc[:,None]/4);np.add.at(rt,c.ravel(),local.ravel())
    bath=np.unique(f[tags==1]);hot=np.unique(f[tags==2]);free=np.ones(len(p),bool);free[np.r_[bath,hot]]=False
    if not np.isfinite(t).all():raise ValueError('Nonfinite actual temperature')
    result={'nodes':len(p),'tetrahedra':len(c),'temperature_min_k':float(t.min()),'temperature_max_k':float(t.max()),'bottom_raw_out_w':float(flux[tags==1].sum()),'top_raw_out_w':float(flux[tags==2].sum()),'bottom_reaction_out_w':float(-rt[bath].sum()),'top_reaction_out_w':float(-rt[hot].sum()),'volume_source_w':float(vol@sc),'free_residual_l1_w':float(abs(rt[free]).sum()),'solver_status':status,'solver_executed':True,'source_sha256':hashes,'sif_sha256':sha(out/'case.sif'),'vtu_sha256':sha(field_path),'field_source':str(field_path.relative_to(out)),'mesh_sha256':sha(out/'mesh.npz'),'node_mapping_max_m':distance,'metadata':metadata or {}}
    result['reaction_energy_error_w']=result['bottom_reaction_out_w']+result['top_reaction_out_w']-result['volume_source_w']
    dump(out/'execution.json',result)
    return result,t,vol,flux,tags


def circle_mesh():
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.NumThreads',1);gmsh.option.setNumber('General.Terminal',0)
        occ=gmsh.model.occ;radii=[.0013,.00055,.00022]
        disks=[(2,occ.addDisk(0,0,0,r,r)) for r in radii]
        occ.fragment(disks[:1],disks[1:]);occ.synchronize()
        gmsh.option.setNumber('Mesh.MeshSizeMin',.00025);gmsh.option.setNumber('Mesh.MeshSizeMax',.00025);gmsh.option.setNumber('Mesh.MinimumCirclePoints',64);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',64);gmsh.option.setNumber('Mesh.RandomSeed',20261030)
        gmsh.model.mesh.generate(2);ids,xyz,_=gmsh.model.mesh.getNodes();points=np.array(xyz).reshape(-1,3)[:,:2];lookup={int(v):i for i,v in enumerate(ids)}
        types,_,nodes=gmsh.model.mesh.getElements(2);tri=np.concatenate([np.array([lookup[int(v)] for v in nn]).reshape(-1,3) for typ,nn in zip(types,nodes) if typ==2])
        r=np.linalg.norm(points[tri].mean(1),axis=1);body=np.where(r<.00022,3,np.where(r<.00055,2,1))
        return points,tri,body
    finally:gmsh.finalize()


def junction(out):
    out.mkdir(parents=True,exist_ok=False);p2,tri,body=circle_mesh();L=.0011;k={1:17.3,2:1.,3:17.3};areas=np.abs(np.cross(p2[tri[:,1]]-p2[tri[:,0]],p2[tri[:,2]]-p2[tri[:,0]]))/2
    conductance=sum(float(areas[body==bid].sum())*kk/L for bid,kk in k.items());rows=[]
    for label,n,delta,amplitude in [('linear',8,10.,0.),('reverse',8,-10.,0.)]+[(f'manufactured_{n}',n,10.,5.) for n in (8,16,32,64)]:
        p,c,b=extrude(p2,tri,np.linspace(0,L,n+1),[body]*n)
        source={bid:2*kk*amplitude/L**2 for bid,kk in k.items()}
        result,t,_,_,_=solve(out/label,p,c,b,k,source,top=300+delta,metadata={'type':'3D coaxial Kovar/glass/pin junction benchmark','axial_layers':n,'quadratic_amplitude_k':amplitude,'manufactured_solution':'300 + delta*z/L + amplitude*z/L*(1-z/L)','lateral_interfaces':'vertical, continuous T and zero normal interface flux; NOT the full-device protruding pin corner'})
        z=p[:,2]/L;exact=300+delta*z+amplitude*z*(1-z);want=conductance*(delta+amplitude)
        result.update(expected_bottom_out_w=want,raw_relative_error=(result['bottom_raw_out_w']-want)/abs(want),max_temperature_error_k=float(abs(t-exact).max()),expected_raw_relative_error_uniform_axial=-amplitude/(n*abs(delta+amplitude)),conductance_on_actual_polygon_w_k=conductance)
        # A separate temperature-only, one-sided quadratic derivative. It is
        # exact for this aligned quadratic manufactured family, not an RT0
        # equilibration and not a qualified arbitrary-device boundary flux.
        plane=t.reshape(n+1,len(p2));derivative=(-3*plane[0]+4*plane[1]-plane[2])/(2*L/n)
        recovered=float(sum(areas[body==bid]@derivative[tri[body==bid]].mean(1)*kk for bid,kk in k.items()))
        result.update(recovered_bottom_out_w=recovered,recovered_relative_error=(recovered-want)/abs(want),recovery_scope='temperature-only one-sided quadratic axial derivative on aligned extrusion; independent of weak reactions, not general conservative RT0 recovery')
        result['passed']=bool(abs(result['reaction_energy_error_w'])<1e-8 and result['free_residual_l1_w']<1e-7 and (abs(result['raw_relative_error'])<1e-7 if amplitude==0 else True))
        dump(out/label/'verification.json',result);rows.append(result)
        print('junction',label,'raw error',result['raw_relative_error'],flush=True)
    errors=[abs(r['raw_relative_error']) for r in rows[2:]]
    passed=all(r['passed'] for r in rows) and all(a>b for a,b in zip(errors,errors[1:])) and errors[-1]<.01
    passed=passed and max(abs(r['recovered_relative_error']) for r in rows)<1e-6
    summary={'passed':passed,'genuine_solver_executions':len(rows),'raw_gate_unchanged':.01,'recovered_flux_implemented':'aligned-benchmark quadratic axial derivative only; full device recovery NOT qualified','full_device_qualified':False,'cases':rows,'geometry_error_separate':{'actual_area_m2':float(areas.sum()),'analytic_area_m2':float(np.pi*.0013**2),'relative':float(areas.sum()/(np.pi*.0013**2)-1)}}
    dump(out/'summary.json',summary)
    if not passed:raise ValueError('Junction verification failed; retain evidence')
    return summary


def layers(thickness, conductivity, contacts=(0.,0.), equal=False):
    if not 20e-6<=thickness<=100e-6 or not 10<=conductivity<=80 or any(v<0 or v>1e-5 for v in contacts):raise ValueError('Outside declared hypothesis bounds')
    result=[('Kovar',.0011,17.3,4)]
    if contacts[0]:result.append(('contact_film_1',2e-6,2e-6/contacts[0],1))
    result.append(('unidentified_metallic_presolder',thickness,conductivity,2))
    if contacts[1]:result.append(('contact_film_2',2e-6,2e-6/contacts[1],1))
    result.append(('Alumina',.00022,30.,4))
    if equal:result=[(name,t,17.3,n) for name,t,_,n in result]
    return result


def presolder(out):
    out.mkdir(parents=True,exist_ok=False);x=np.linspace(0,.001,6);p2=np.array(list(itertools.product(x,x)));tri=[]
    for i in range(5):
        for j in range(5):
            a=i*6+j;b=a+6;tri.extend([[a,b,b+1],[a,b+1,a+1]])
    tri=np.array(tri);rows=[]
    scenarios=[('metal_25um',25e-6,35.,(0.,0.),False),('metal_50um',50e-6,35.,(0.,0.),False),('metal_100um',100e-6,35.,(0.,0.),False),('AuSn_proxy_50um',50e-6,57.,(0.,0.),False),('contact_50um',50e-6,35.,(2e-6,3e-6),False),('equal_material',50e-6,35.,(0.,0.),True)]
    for label,thickness,ks,contacts,equal in scenarios:
        stack=layers(thickness,ks,contacts,equal);z=[0.];bodies=[]
        for bid,(_,h,_,n) in enumerate(stack,1):
            z.extend(np.linspace(z[-1],z[-1]+h,n+1)[1:]);bodies.extend([bid]*n)
        p,c,b=extrude(p2,tri,np.array(z),bodies);k={i:row[2] for i,row in enumerate(stack,1)}
        result,t,_,_,_=solve(out/label,p,c,b,k,{},metadata={'type':'isolated full-wetted 3D Kovar/presolder/alumina thermal coupon','layers':[{'name':name,'thickness_m':h,'k_w_mk':kk,'cells_through_thickness':n} for name,h,kk,n in stack],'electrical':'HeatSolve only, no electrical PDE or TEC conductor; alumina separates metal regions in prospective stack; no shorting claim for unrun full device','contact_representation':'finite 2um resistance films k=film_t/Rdoubleprime; continuous T, not zero-thickness jump condition','material_law':'frozen sourced/proxy reference values over assumed numerical300..310K interval, not measured k(T)','contact_Rdoubleprime_m2K_W':contacts})
        resistance=sum(h/kk for _,h,kk,_ in stack)/1e-6;expected=10/resistance;planes=[]
        cumulative=0.
        for name,h,kk,_ in stack:
            start=300+expected*cumulative/1e-6;cumulative+=h/kk;end=300+expected*cumulative/1e-6
            zz=sum(v[1] for v in stack[:len(planes)+1]);nodes=np.flatnonzero(abs(p[:,2]-zz)<1e-12)
            planes.append({'layer':name,'analytic_drop_k':end-start,'actual_top_plane_mean_k':float(t[nodes].mean()),'analytic_top_plane_k':end})
        result.update(analytic_R_K_W=resistance,expected_out_w=expected,raw_relative_error=(result['bottom_raw_out_w']-expected)/expected,interface_planes=planes)
        result['passed']=bool(abs(result['raw_relative_error'])<1e-7 and abs(result['reaction_energy_error_w'])<1e-8 and max(abs(v['actual_top_plane_mean_k']-v['analytic_top_plane_k']) for v in planes)<1e-6 and t.min()>299.999999 and t.max()<310.000001)
        dump(out/label/'verification.json',result);rows.append(result);print('presolder',label,'R K/W',resistance,'raw error',result['raw_relative_error'],flush=True)
    summary={'passed':all(r['passed'] for r in rows),'genuine_solver_executions':len(rows),'full_stack_presolder_solved':False,'alloy_identified':False,'cases':rows,'wetted_area_m2':1e-6,'void_geometry_solved':False,'temperature_dependent_transport_qualified':False}
    dump(out/'summary.json',summary)
    if not summary['passed']:raise ValueError('Presolder coupon verification failed')
    return summary


def main(out,kind):
    guard()
    if kind=='junction':junction(out)
    else:presolder(out)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['junction','presolder']);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();main(args.out.resolve(),args.kind)
