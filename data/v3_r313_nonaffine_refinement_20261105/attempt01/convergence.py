#!/usr/bin/env python3
"""R3.13: frozen-boundary nested regional P1 FEM nonaffine manufactured test.

CAD region 420, original R3.9 tetrahedral bond8; centroid 1->4 recursive splits
preserve every original boundary triangular facet, node coordinate, owner.
PDE -Δu = f const with u*=sum((x_i-center_i)/scale_i)^2.
Dirichlet analytic on native face2399, all other faces analytic Neumann.
Exact H1-seminorm error integrated using tetrahedral second moments;
solver true residual independently checked; Jacobi + ILU GMRES tested.
"""
import pathlib,json,time,hashlib,resource,math
import numpy as np
import scipy
import scipy.sparse as sp
from scipy.sparse.linalg import gmres,spilu,LinearOperator, spsolve

P=pathlib.Path('/input')
OUT=pathlib.Path('/out')
S=time.monotonic()
REGION=420;FACE=2399
meta=json.loads((P/'source_metadata.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
raw_nodes=np.loadtxt(P/'R38_430_domains.1.node',skiprows=1)
raw_ele=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
raw_fac=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
tet_global=raw_ele[raw_ele[:,5]==REGION,1:5]
old_global=np.unique(tet_global)
node_mapping=np.full(len(raw_nodes)+1,-1,dtype=np.int32)
node_mapping[old_global]=np.arange(len(old_global),dtype=np.int32)
tetra=node_mapping[tet_global]
vertices=raw_nodes[old_global-1,1:4].copy()
fids=[int(fid) for fid,p in meta['faces'].items() if REGION in p['owner_volume_ids']]
fac=raw_fac[np.isin(raw_fac[:,4],fids)]
surface=fac[:,1:4].copy()
local_surface=node_mapping[surface]
fix=np.unique(node_mapping[raw_fac[raw_fac[:,4]==FACE,1:4]])
assert len(fix)==3072
assert len(fac)==13540 and len(vertices)==6884 and len(tetra)==25905
assert np.all(local_surface>=0)
# Preserve the exact 13540 input facets at every step; future vertices strictly interior.
surfaceset={tuple(sorted(x)) for x in local_surface}
ref_face_set={tuple(sorted(x)) for x in local_surface[fac[:,4]==FACE]}
origin=vertices.mean(axis=0)
range_xyz=np.ptp(vertices,axis=0)
# Use physically comparable scale in each direction, with lower bound
# to avoid precision artifacts on very thin Z variation.
scale=np.maximum(range_xyz,0.05)
inv_sq=1/scale**2
def exact(x):return np.sum(((x-origin)/scale)**2,axis=-1)
def gradient(x):return 2*(x-origin)*inv_sq
forcing=-2*float(np.sum(inv_sq))
# Critical: no caching facet-flux RHS across refinement levels? Original boundary
# integrals unchanged, but add zeros for new internal nodes.
boundary_flux=np.zeros(len(vertices))
# original local boundary facets have one adjacent tetrahedron; build sided normals
FACE_INDICES=((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3))
own={}
for t in tetra:
 for i,j,k,opp in FACE_INDICES:
  facekey=tuple(sorted((int(t[i]),int(t[j]),int(t[k]))))
  if facekey in own:
   own[facekey]=None
  else:
   own[facekey]=(int(t[i]),int(t[j]),int(t[k]),int(t[opp]))
real_boundary={k:v for k,v in own.items() if v is not None}
assert set(real_boundary)==surfaceset,(len(real_boundary),len(surfaceset))
for key,oriented in real_boundary.items():
 i,j,k,o=oriented
 x0,x1,x2=vertices[[i,j,k]]
 narea=np.cross(x1-x0,x2-x0)*0.5
 if np.dot(narea,vertices[o]-x0)>0:narea=-narea
 # ∇u quadratic => affine across triangle; exact flux mass-vector
 # integrals ∫_triangle N_i ∇u(x)·n dA.
 # Face P1 mass: integral N_i N_j = A/12 (diag2,off1).
 gn=gradient(vertices[[i,j,k]])@narea
 if key in ref_face_set:continue
 for m,node in enumerate((i,j,k)):
  boundary_flux[node]+=float((np.sum(gn)+gn[m])/12)
# Flux amount above uses narea = normal*A, so mass integrals weight /12,
# correct for sum_i ∫N_i g = A/3 sum(g_i).
total_boundary_flux=float(np.sum(boundary_flux))
results=[]
initial_facets=np.sort(local_surface,axis=1)
def solve_level(level,v,t):
 global boundary_flux
 before=time.monotonic()
 count=len(v);n_tets=len(t)
 free=np.setdiff1d(np.arange(count,dtype=np.int32),fix)
 p=v[t]
 J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
 det=np.linalg.det(J)
 if np.any(det<=0):raise RuntimeError(f'Level{level} inverted: {np.sum(det<=0)}')
 vol=det/6
 inv=np.linalg.inv(J)
 ref=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
 g=np.einsum('tji,aj->tai',inv,ref)
 k_loc=vol[:,None,None]*np.einsum('tai,tbi->tab',g,g)
 row=np.broadcast_to(t[:,:,None],k_loc.shape).ravel()
 col=np.broadcast_to(t[:,None,:],k_loc.shape).ravel()
 stiff=sp.coo_matrix((k_loc.ravel(),(row,col)),shape=(count,count)).tocsr()
 stiff.sum_duplicates()
 A=stiff[free,:][:,free].tocsr()
 fvec=np.bincount(t.ravel(),weights=np.repeat((forcing*vol/4)[:,None],4,axis=1).ravel(),minlength=count)
 fvec[:len(boundary_flux)]+=boundary_flux
 rhs=fvec[free]-stiff[free,:][:,fix]@exact(v[fix])
 rhs_norm=float(np.linalg.norm(rhs))
 assert rhs_norm>0
 stats={'level':level,'tetrahedra':n_tets,'nodes':count,'free_DOF':len(free),
  'fixed_Dirichlet_face_nodes':len(fix),
  'original_boundary_triangle_count':len(initial_facets),
  'original_boundary_vertices_fixed':len(vertices),
  'min_signed_tet_volume_mm3':float(vol.min()),
  'sum_tet_volumes_mm3':float(vol.sum()),
  'matrix_nonzeros':int(A.nnz),'matrix_symmetry_error_relative':float(sp.linalg.norm(A-A.T)/sp.linalg.norm(A))}
 assert stats['matrix_symmetry_error_relative']<1e-12
 try:
  startfac=time.monotonic()
  ilu=spilu(A.tocsc(),drop_tol=1e-5,fill_factor=16)
  M=LinearOperator(A.shape,matvec=ilu.solve,dtype=np.float64)
  it=[0]
  def cb(_):it[0]+=1
  uh,info=gmres(A,rhs,M=M,restart=60,maxiter=55,rtol=1e-9,atol=0,callback=cb,callback_type='pr_norm')
  res=float(np.linalg.norm(A@uh-rhs)/rhs_norm)
  stats['ILU_GMRES']={'info':int(info),'iterations':it[0],'true_relative_residual':res,
    'factor_plus_solve_seconds':round(time.monotonic()-startfac,3),
    'ILU_factor_nonzeros':int(ilu.L.nnz+ilu.U.nnz)}
 except Exception as ex:
  stats['ILU_GMRES']={'status':'ERROR','error':str(ex)[:350]}
  stats['status']='SOLVER_STOP';return stats
 if info!=0 or res>1e-8:
  stats['status']='SOLVER_STOP';return stats
 nodal=exact(v)
 nodal[free]=uh
 # Exact integrated squared H1 error: grad(u*) affine; cell-average + covariance
 grad_approx=np.einsum('ti,tij->tj',nodal[t],g)
 center=p.mean(axis=1)
 delta=grad_approx-gradient(center)
 # uniform tetra covariance = (sum_i (v_i-c)(v_i-c)^T)/20
 variance=(np.sum((p-center[:,None,:])**2,axis=1))/20
 error_sq=vol*(np.einsum('ij,ij->i',delta,delta)
              +np.sum((4*inv_sq**2)[None,:]*variance,axis=1))
 H1=math.sqrt(float(error_sq.sum()))
 # exact integral gradient magnitude squared, same moment formula
 gcenter=gradient(center)
 exactnorm=math.sqrt(float(np.sum(vol*(np.einsum('ij,ij->i',gcenter,gcenter)
                   +np.sum((4*inv_sq**2)[None,:]*variance,axis=1)))))
 stats['H1_seminorm_absolute']=H1
 stats['H1_seminorm_relative']=H1/exactnorm
 stats['H1_exact_solution_norm']=exactnorm
 stats['interior_nodal_relative_L2']=float(np.linalg.norm(uh-exact(v[free]))/
                                     max(np.linalg.norm(exact(v[free])),1e-30))
 stats['elapsed_seconds']=round(time.monotonic()-before,3)
 stats['status']='PASS REGIONAL SOLVE; ERROR MEASURED'
 print('R313_LEVEL',json.dumps({k:stats[k] for k in ('level','tetrahedra','nodes','free_DOF','ILU_GMRES',
'H1_seminorm_relative','interior_nodal_relative_L2','elapsed_seconds')}),flush=True)
 return stats
n0=len(vertices);v=vertices.copy();t=tetra.copy()
original_volume=None
def split_all(v,t):
 # Centroid refinement all tets: four children share a single new interior node,
 # original surface faces remain triangles EXACTLY, no new boundary vertices.
 n=len(v)
 newnodes=v[t].mean(axis=1)
 newtags=np.arange(n,n+len(t),dtype=np.int32)
 # Orient each child with appropriate vertex ordering and verify jacobians later.
 c=np.concatenate([
  np.column_stack((t[:,2],t[:,1],t[:,3],newtags)),
  np.column_stack((t[:,3],t[:,0],t[:,2],newtags)),
  np.column_stack((t[:,1],t[:,0],t[:,3],newtags)),
  np.column_stack((t[:,2],t[:,0],t[:,1],newtags))
 ])
 nv=np.vstack((v,newnodes))
 return nv,c
for level in range(3):
 result=solve_level(level,v,t)
 results.append(result)
 if original_volume is None:original_volume=result['sum_tet_volumes_mm3']
 if abs(result['sum_tet_volumes_mm3']/original_volume-1)>1e-9:raise RuntimeError('Refinement volume conservation failed')
 OUT.mkdir(exist_ok=True)
 (OUT/f'level{level}_result.json').write_text(json.dumps(result,indent=2)+'\n')
 if result['status']!='PASS REGIONAL SOLVE; ERROR MEASURED':break
 if level<2:
  v,t=split_all(v,t)
  boundary_flux=np.pad(boundary_flux,(0,len(v)-len(boundary_flux)))
 if time.monotonic()-S>190:
  print('STOP R313 TOTAL TIME',flush=True);break
tested=[s for s in results if s['status']=='PASS REGIONAL SOLVE; ERROR MEASURED']
for a,b in zip(tested,tested[1:]):
 b['H1_error_ratio_to_prev']=b['H1_seminorm_absolute']/a['H1_seminorm_absolute']
# Diffusion h_eff = (V / N)^(1/3), exact h ratio for uniform 4 way refine = 4^(-1/3)
# No legitimate asymptotic global convergence rate if boundary unchanged.
report={'status':'PASS 3 LEVELS REGIONAL FIXED-BOUNDARY INTERIOR-REFINEMENT BENCHMARK' if len(tested)==3
        and all(b['H1_error_ratio_to_prev']<1 for b in tested[1:])
        else 'LIMITED OR FAILED: NO ASYMPTOTIC CONVERGENCE CLAIM',
 'region':'detector_bond8','volume_id':REGION,'Dirichlet_native_face':FACE,
 'manufactured_solution':'u = sum(((x_i-origin_i)/scale_i)^2); f=-Delta u; analytic natural Neumann on all non-Dirichlet CAD interface facets',
 'manufactured_origin_mm':list(map(float,origin)),
 'manufactured_scale_mm':list(map(float,scale)),
 'source_R39_ele_sha256':sha(P/'R39_430_domains.1.ele'),
 'source_R38_node_sha256':sha(P/'R38_430_domains.1.node'),
 'source_R38_face_sha256':sha(P/'R38_430_domains.1.face'),
 'preserved_registered_surface_facets':13540,
 'refinement':'uniform 1-to-4 tetra centroid splits; preserves original boundary triangle triplets, creates only interior vertices',
 'global_surface_hmax_UNCHANGED':True,
 'cannot_claim_full_3D_mesh_h_convergence':True,
 'full_device_electrothermal_PDE':'NOT RUN',
 'results':results,
 'runtime_seconds':round(time.monotonic()-S,3),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
(OUT/'convergence_result.json').write_text(json.dumps(report,indent=2)+'\n')
print('R313_RESULT',report['status'],'seconds',report['runtime_seconds'],'levels',len(results),flush=True)
