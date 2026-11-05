#!/usr/bin/env python3
"""R3.12 independent manufactured mixed Dirichlet-Neumann affine Laplace test.
Assemble P1 stiffness and boundary-normal surface flux from each true TetGen
region-boundary triangle, not from assembled K @ exact. No physical coefficients.
"""
from pathlib import Path
from collections import defaultdict
import json,hashlib,time,resource,sys
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve,spilu,gmres,LinearOperator

P=Path('/input');O=Path('/out');t0=time.monotonic()
reference_meta=json.loads((P/'source_metadata.json').read_text())
fac=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
ele_file={'R39':'R39_430_domains.1.ele','R311':'R311_430_domains.1.ele'}
node_file='R38_430_domains.1.node'
node=np.loadtxt(P/node_file,skiprows=1);xyz0=node[:,1:4]
out={}
id_region=420
dir_face=2399
face_tags=[int(x) for x,data in reference_meta['faces'].items() if id_region in data['owner_volume_ids']]
source_face=fac[np.isin(fac[:,4],face_tags)]
source_keys={tuple(sorted(map(int,triangle))) for triangle in source_face[:,1:4]}
fixed_native_nodes=set(map(int,fac[fac[:,4]==dir_face,1:4].ravel()))
grad_u=np.array([1.0,2.0,-0.3])
def ssha(p):
 h=hashlib.sha256()
 with p.open('rb') as fh:
  for b in iter(lambda:fh.read(4<<20),b''):h.update(b)
 return h.hexdigest()
for rev,filename in ele_file.items():
 tic=time.monotonic()
 e=np.loadtxt(P/filename,dtype=np.int32,skiprows=1)
 tetra_orig=e[e[:,5]==id_region,1:5]
 nodes=np.unique(tetra_orig);index={int(v):i for i,v in enumerate(nodes)}
 tets=np.searchsorted(nodes,tetra_orig)
 n=len(nodes);xyz=xyz0[nodes-1]
 fix=np.array(sorted(index[i] for i in fixed_native_nodes),dtype=np.int32)
 free=np.setdiff1d(np.arange(n,dtype=np.int32),fix)
 assert (n,len(fix),len(free))==(6884,3072,3812) if rev=='R39' else len(free)==3812
 vertices=xyz[tets]
 J=np.stack((vertices[:,1]-vertices[:,0],vertices[:,2]-vertices[:,0],vertices[:,3]-vertices[:,0]),axis=2)
 det=np.linalg.det(J);assert np.all(det>0)
 volume=det/6
 inv=np.linalg.inv(J)
 refgrad=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
 grads=np.einsum('tji,aj->tai',inv,refgrad)
 loc=volume[:,None,None]*np.einsum('tai,tbi->tab',grads,grads)
 rows=np.broadcast_to(tets[:,:,None],loc.shape).ravel()
 cols=np.broadcast_to(tets[:,None,:],loc.shape).ravel()
 K=sparse.coo_matrix((loc.ravel(),(rows,cols)),shape=(n,n)).tocsr()
 A=K[free,:][:,free].tocsr()
 # Native tetrahedral region boundary, direct facet incidence from local tets.
 # Each key's value is a single oriented facet and its opposite vertex.
 skin={}
 faces=((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3))
 for i,t in enumerate(tetra_orig):
  for ai,bi,ci,oi in faces:
   tri=(int(t[ai]),int(t[bi]),int(t[ci]))
   key=tuple(sorted(tri))
   if key in skin: skin[key]=None
   else: skin[key]=(tri,int(t[oi]))
 boundary={k:v for k,v in skin.items() if v is not None}
 assert set(boundary)==source_keys,(len(boundary),len(source_keys),len(set(boundary)^source_keys))
 # Integrate exact outward normal flux ∂u/∂n across TRI3:
 # g dA = grad(u)·(0.5 cross(p1-p0,p2-p0)), and
 # ∫_face g N_i dA = (g A)/3 each vertex.
 flux=np.zeros(n)
 for (key,(tri,opp)) in boundary.items():
  p0,p1,p2=(xyz0[j-1] for j in tri)
  op=xyz0[opp-1]
  outward_area_vector=np.cross(p1-p0,p2-p0)*0.5
  if np.dot(outward_area_vector,op-p0)>0:
   outward_area_vector=-outward_area_vector
  amount=float(np.dot(outward_area_vector,grad_u))/3
  for v in tri: flux[index[v]]+=amount
 exact=xyz@grad_u
 b=flux[free]-K[free,:][:,fix]@exact[fix]
 rr_exact=float(np.linalg.norm(A@exact[free]-b)/max(np.linalg.norm(b),1e-30))
 net_flux=float(np.sum(flux))
 sol_dir=spsolve(A,b)
 dir_res=float(np.linalg.norm(A@sol_dir-b)/np.linalg.norm(b))
 dir_err=float(np.linalg.norm(sol_dir-exact[free])/max(np.linalg.norm(exact[free]),1e-30))
 ilu=spilu(A.tocsc(),drop_tol=1e-5,fill_factor=16)
 pre=LinearOperator(A.shape,matvec=ilu.solve,dtype=float)
 it=[0]
 def cb(_):it[0]+=1
 sol,info=gmres(A,b,M=pre,restart=60,maxiter=50,rtol=1e-8,atol=0,
                callback=cb,callback_type='pr_norm')
 gm_res=float(np.linalg.norm(A@sol-b)/np.linalg.norm(b))
 gm_err=float(np.linalg.norm(sol-exact[free])/max(np.linalg.norm(exact[free]),1e-30))
 out[rev]={
  'region_nodes':n,'tetrahedra':len(tetra_orig),'native_boundary_triangles':len(boundary),
  'fixed_face':dir_face,'free_nodes':len(free),
  'affine_analytic_harmonic':list(map(float,grad_u)),'integrated_total_neumann_flux':net_flux,
  'analytic_exact_discrete_residual':rr_exact,
  'direct_true_relative_residual':dir_res,'direct_solution_relative_error_vs_affine':dir_err,
  'ILU_GMRES_info':int(info),'ILU_GMRES_iterations':it[0],
  'ILU_GMRES_true_relative_residual':gm_res,
  'ILU_GMRES_solution_relative_error_vs_affine':gm_err,
  'wall_seconds':round(time.monotonic()-tic,3)}
 print('R312_MANUFACTURED',rev,json.dumps(out[rev]),flush=True)
 assert info==0 and gm_res<1e-8
 assert rr_exact<1e-7 and dir_err<1e-6 and gm_err<1e-6
assert len(out)==2
result={'status':'PASS MIXED BOUNDARY MANUFACTURED AFFINE HARMONIC TEST ON GOLD BOND 8',
 'formulation':'Unit scalar Laplace Δu=0; Dirichlet u=x+2y−0.3z on face 2399; analytic natural Neumann flux on all remaining native CAD faces; P1 tetrahedral FE',
 'not_physical_transport':True,'not_mesh_refinement_or_convergence':True,
 'source_R38_nodes_sha256':ssha(P/node_file),
 'source_R39_elements_sha256':ssha(P/ele_file['R39']),
 'source_R311_elements_sha256':ssha(P/ele_file['R311']),
 'results':out,'total_wall_seconds':round(time.monotonic()-t0,3),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2)}
(O/'manufactured_mixed_bc.json').write_text(json.dumps(result,indent=2)+'\n')
print('R312_MANUFACTURED_RESULT',result['status'],flush=True)
