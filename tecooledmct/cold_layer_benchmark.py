"""Independent manufactured3D mixed-boundary heat benchmark for cold interfaces."""
import argparse,json,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import ROOT,sha,write
from .flux_presolder_coupon import extrude
from .fem_g2a import mesh_adjacency
from .fem_g1_run import execute
from .cold_interface_audit import face_flux,affine

PLAN=ROOT/'data/cold_convergence/plan.json';L=.001;K={1:30.,2:1.,3:1.1};Z=np.array([0.,.00022,.00025,.00045]);P=.002;Q=P/L**2


def exact(x,source=False):
    z=x[:,2];value=np.full(len(x),300.)
    value+=Q*np.minimum(z,Z[1])/K[1]
    value+=Q*np.clip(z-Z[1],0,Z[2]-Z[1])/K[2]
    u=np.maximum(z-Z[2],0);value+=Q*u/K[3]
    if source:value-=Q/(Z[3]-Z[2])*u*u/(2*K[3])
    return value+.04*(x[:,0]**2-x[:,1]**2)/L**2+.03*x[:,0]*x[:,1]/L**2


def geometry(n,nz):
    xy=np.array([(x,y) for y in np.linspace(-L/2,L/2,n+1) for x in np.linspace(-L/2,L/2,n+1)])
    tri=[]
    for j in range(n):
        for i in range(n):
            a=j*(n+1)+i;tri.extend([(a,a+1,a+n+2),(a,a+n+2,a+n+1)])
    z=[];layers=[]
    for i,count in enumerate(nz):z.extend(np.linspace(Z[i],Z[i+1],count+1)[:-1]);layers.extend([i+1]*count)
    z.append(Z[-1]);return extrude(xy,np.array(tri),z,layers)


def case(out,level,source=False):
    import meshio
    plan=json.loads(PLAN.read_text())['benchmark'];n=plan['xy_intervals'][level];nz=plan['z_intervals_by_layer'][level]
    p,c,b=geometry(n,nz);adj=mesh_adjacency(c);faces=[];tags=[]
    for face,owners in adj.items():
        xyz=p[list(face)]
        if len(owners)==1:
            tag=1 if np.all(abs(xyz[:,2])<1e-12) else 2 if np.all(abs(xyz[:,2]-Z[-1])<1e-12) else 10+int(b[owners[0]])
        elif b[owners[0]]!=b[owners[1]]:tag=100+int(min(b[owners]))
        else:continue
        faces.append(face);tags.append(tag)
    f=np.array(faces);tags=np.array(tags);out.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(out/'mesh.npz',points=p,cells=c,bodies=b,faces=f,tags=tags)
    meshio.write(out/'case.msh',meshio.Mesh(p,[('triangle',f),('tetra',c)],cell_data={'gmsh:physical':[tags,b],'gmsh:geometrical':[tags,b]}),file_format='gmsh22',binary=False)
    execute(['ElmerGrid','14','2','case.msh','-out','elmer'],out,'grid',timeout=120)
    common='0.04*(tx(0)^2-tx(1)^2)/1.0e-6+0.03*tx(0)*tx(1)/1.0e-6'
    profiles={1:'300+2000*tx(2)/30',2:'300+2000*0.00022/30+2000*(tx(2)-0.00022)',
              3:'300+2000*0.00022/30+2000*0.00003+2000*(tx(2)-0.00025)/1.1'+('-1.0e7*(tx(2)-0.00025)^2/(2*1.1)' if source else '')}
    text=f'''Header
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
End
Boundary Condition 1
 Target Boundaries(1) = 1
 Temperature = Variable Coordinate 1,Coordinate 2,Coordinate 3
  Real MATC "300+{common}"
End
Boundary Condition 2
 Target Boundaries(1) = 2
 Heat Flux = Real {0 if source else Q}
End
'''
    for bid,k in K.items():
        text+=f'''Body {bid}
 Equation = 1
 Material = {bid}
 Body Force = {bid}
End
Material {bid}
 Heat Conductivity = Real {k}
 Density = Real 1
 Heat Capacity = Real 1
End
Body Force {bid}
 Heat Source = Real {1e7 if source and bid==3 else 0}
End
Boundary Condition {bid+2}
 Target Boundaries(1) = {10+bid}
 Temperature = Variable Coordinate 1,Coordinate 2,Coordinate 3
  Real MATC "{profiles[bid]}+{common}"
End
'''
    (out/'case.sif').write_text(text);hashes={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(PLAN.relative_to(ROOT)):sha(PLAN),
         'tecooledmct/cold_interface_audit.py':sha(ROOT/'tecooledmct/cold_interface_audit.py')}
    status,_=execute(['ElmerSolver','case.sif'],out,'solver',timeout=180)
    raw=next(out.rglob('fields*.vtu'));field=meshio.read(raw);dist,ix=cKDTree(field.points).query(p)
    if dist.max()>1e-12:raise ValueError('Benchmark field mapping')
    t=field.point_data['temperature'].ravel()[ix];kn=np.broadcast_to(np.array([K[int(v)] for v in b])[:,None],(len(c),4));rows=[]
    for tag in (101,102):
        r,arrays=face_flux(p,c,b,f[tags==tag],t,kn);np.savez_compressed(out/f'interface_{tag}.npz',**arrays);rows.append(r)
    vol,gt=affine(p,c,t);q=-kn[:,0,None]*gt;source_e=np.where(b==3,1e7 if source else 0.,0.)
    reaction=np.zeros(len(p))
    # Independent stiffness gradient through coordinate differences.
    inv=np.linalg.inv(p[c[:,1:]]-p[c[:,:1]]);g=np.concatenate([-inv.sum(2)[:,None,:],np.swapaxes(inv,1,2)],axis=1)
    local=vol[:,None]*(kn[:,0,None]*np.einsum('eij,ej->ei',g,gt)-source_e[:,None]/4);np.add.at(reaction,c.ravel(),local.ravel())
    top=f[tags==2];xyz=p[top];area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
    np.add.at(reaction,top.ravel(),-np.repeat(area*(0 if source else Q)/3,3))
    fixed=np.unique(f[np.isin(tags,[1,11,12,13])]);free=np.ones(len(p),bool);free[fixed]=False
    # Exact volume mean: transverse harmonic mean is zero on the centred square.
    mean_exact=300+Q*Z[1]/30+Q*(Z[2]-Z[1])+Q*(Z[3]-Z[2])/(2*K[3])
    if source:mean_exact-=Q*(Z[3]-Z[2])/(6*K[3])
    mct=b==3;mean=float(vol[mct]@t[c[mct]].mean(1)/vol[mct].sum());errors=[max(abs(np.array(v['raw_outward_w'])/np.array([-P,P])-1)) for v in rows]
    bound=.05 if source else .01
    checks={'interface_integrated_bound':max(errors)<bound,'interface_jump_5percent':max(abs(v['mismatch']) for v in rows)<.05,
            'MCT_mean_0p2mK':abs(mean-mean_exact)<.0002,'free_weak_residual_10nW':float(abs(reaction[free]).sum())<1e-8,
            'actual_source_volume':abs(float(vol@source_e)-(P if source else 0))<1e-12}
    result={'kind':'distributed_MCT_source' if source else 'constant_flux','level':level,'nodes':len(p),'tets':len(c),
       'interfaces':rows,'interface_relative_errors':errors,'MCT_mean_k':mean,'analytic_MCT_mean_k':mean_exact,'MCT_mean_error_k':mean-mean_exact,
       'max_nodal_error_k':float(abs(t-exact(p,source)).max()),'volume_source_w':float(vol@source_e),'free_residual_L1_w':float(abs(reaction[free]).sum()),
       'checks':{k:bool(v) for k,v in checks.items()},'finest_targets_passed':bool(all(checks.values())),
       'source_sha256':hashes,'mesh_sha256':sha(out/'mesh.npz'),'sif_sha256':sha(out/'case.sif'),'vtu_sha256':sha(raw),'field_source':str(raw.relative_to(out)),
       'solver_status':status,'reference':'independent analytic T(z)+harmonic transverse; no FE reaction defines reference flux',
       'h_m':float((vol.sum()/len(c))**(1/3))}
    if any(sha(ROOT/n)!=v for n,v in hashes.items()):raise ValueError('Benchmark source changed while executing')
    write(out/'verification.json',result);print(result['kind'],level,'raw errors',errors,'jump',[v['mismatch'] for v in rows],'mean error',result['MCT_mean_error_k'],'checks',checks,flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[]
    for source in (False,True):
        for level in range(3):rows.append(case(a.out/('source' if source else 'flux')/str(level),level,source))
    write(a.out/'summary.json',{'cases':rows,'qualified':all(v['finest_targets_passed'] for v in rows if v['level']==2),'plan_sha256':sha(PLAN)})
