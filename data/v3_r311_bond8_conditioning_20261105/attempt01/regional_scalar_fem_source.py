#!/usr/bin/env python3
"""R3.11 independent scalar Laplace/Poisson P1-FEM benchmark in two gold detector bonds.
All physical boundary nodes fixed Dirichlet; NOT a physical electrical/thermal model.
"""
from pathlib import Path
import json,hashlib,time,resource
import numpy as np
from scipy.sparse import coo_matrix,csr_matrix
from scipy.sparse.linalg import cg,spsolve
ROOT=Path('/bench')
OUT=Path('/out')
t0=time.monotonic()
basepath=Path('/r38/R38_430_domains.1.node')
newpath=Path('/r310/R310_430_domains.1.node')
elepath=Path('/r39/R39_430_domains.1.ele')
facpath=Path('/r38/R38_430_domains.1.face')
assert all(p.is_file() for p in (basepath,newpath,elepath,facpath))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for blk in iter(lambda:f.read(4<<20),b''):h.update(blk)
 return h.hexdigest()
node0=np.loadtxt(basepath,skiprows=1)
node1=np.loadtxt(newpath,skiprows=1)
ele=np.loadtxt(elepath,dtype=np.int32,skiprows=1)
fac=np.loadtxt(facpath,dtype=np.int32,skiprows=1)
assert len(node0)==len(node1)==156765 and len(ele)==1010119
assert np.array_equal(node0[:156599],node1[:156599])
boundary=set(map(int,fac[:,1:4].ravel()))
assert len(boundary)==156599
tet=ele[:,1:5]
region=ele[:,5]
out={}
for name,region_id in [('detector_bond7',418),('detector_bond8',420)]:
 globaltet=tet[region==region_id]
 global_nodes=np.unique(globaltet)
 localindex=np.full(len(node0)+1,-1,dtype=np.int32)
 localindex[global_nodes]=np.arange(len(global_nodes))
 localtet=localindex[globaltet]
 free_idx=np.array([i for i,k in enumerate(global_nodes) if int(k) not in boundary],dtype=np.int32)
 fixed_idx=np.array([i for i,k in enumerate(global_nodes) if int(k) in boundary],dtype=np.int32)
 assert len(free_idx)>0
 variants={}
 for var,node in [('R39',node0),('R310',node1)]:
  coords=node[global_nodes-1,1:4]
  xyz=coords[localtet]
  # Tetra map J columns p1-p0, p2-p0, p3-p0
  J=np.stack((xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0],xyz[:,3]-xyz[:,0]),axis=2)
  det=np.linalg.det(J)
  assert np.all(det>0),(name,var,'nonpositive tets')
  volumes=det/6
  invJ=np.linalg.inv(J)
  # For x = p0 + J*(r,s,t), grad N_i = inv(J).T @ gradref N_i.
  gradref=np.array([[-1,-1,-1],[1,0,0],[0,1,0],[0,0,1]],float)
  gradients=np.einsum('tji,aj->tai',invJ,gradref)
  # Better independently validate gradN dot affine position identity:
  gsum=gradients.sum(axis=1)
  assert np.max(np.abs(gsum))<1e-5
  k_local=volumes[:,None,None]*np.einsum('tai,tbi->tab',gradients,gradients)
  rows=np.broadcast_to(localtet[:,:,None],(len(localtet),4,4)).ravel()
  cols=np.broadcast_to(localtet[:,None,:],(len(localtet),4,4)).ravel()
  K=coo_matrix((k_local.ravel(),(rows,cols)),shape=(len(global_nodes),len(global_nodes))).tocsr()
  K.sum_duplicates()
  Kff=K[free_idx,:][:,free_idx].toarray()
  Kfb=K[free_idx,:][:,fixed_idx].toarray()
  symmetry=float(np.max(np.abs(Kff-Kff.T))/max(np.max(np.abs(Kff)),1e-20))
  lambdas=np.linalg.eigvalsh(Kff)
  cond=float(lambdas[-1]/lambdas[0])
  D=np.sqrt(np.diag(Kff))
  cond_scaled=float(np.linalg.cond(Kff/D[:,None]/D[None,:]))
  assert lambdas[0]>0 and symmetry<1e-10
  # Manufactured affine harmonic u, exact P1 representation. Dirichlet at all surface/interface nodes.
  exact=coords[:,0]+2*coords[:,1]-.3*coords[:,2]
  b=-Kfb@exact[fixed_idx]
  solved=np.linalg.solve(Kff,b)
  err_inf=float(np.max(np.abs(solved-exact[free_idx])))
  err_rel=float(np.linalg.norm(solved-exact[free_idx])/max(np.linalg.norm(exact[free_idx]),1e-30))
  residual=float(np.linalg.norm(Kff@solved-b)/max(np.linalg.norm(b),1e-30))
  # Unit volumetric source: consistent load vector, F_i += volume/4.
  f_local=np.repeat(volumes[:,None]/4,4,axis=1)
  f=np.bincount(localtet.ravel(),weights=f_local.ravel(),minlength=len(global_nodes))
  rhs=f[free_idx]
  uf=np.linalg.solve(Kff,rhs)
  solres=float(np.linalg.norm(Kff@uf-rhs)/np.linalg.norm(rhs))
  iter_counter=[0]
  def count(_):iter_counter[0]+=1
  ucg,info=cg(csr_matrix(Kff),rhs,rtol=1e-10,atol=0,maxiter=3000,callback=count)
  cgerror=float(np.linalg.norm(ucg-uf)/np.linalg.norm(uf))
  assert info==0
  qsum=np.sum(volumes)
  variants[var]={
   'nodes':len(global_nodes),'tetrahedra':len(localtet),'free_interior_DOF':len(free_idx),
   'locked_surface_nodes':len(fixed_idx),'volume_mm3':float(qsum),
   'Kff_diagonal_positive':bool(np.all(np.diag(Kff)>0)),
   'Kff_relative_symmetry_error':symmetry,
   'lambda_min':float(lambdas[0]),'lambda_max':float(lambdas[-1]),
   'spectral_condition_number_unscaled':cond,'spectral_condition_number_jacobi_scaled':cond_scaled,
   'manufactured_harmonic_Linf_error':err_inf,'manufactured_harmonic_relative_L2_error':err_rel,
   'manufactured_harmonic_algebraic_residual':residual,
   'poisson_unit_source_direct_solution_L2':float(np.linalg.norm(uf)),
   'poisson_unit_source_direct_relative_residual':solres,
   'poisson_unit_source_CG_iterations_rtol_1e_10':iter_counter[0],
   'poisson_unit_source_CG_info':int(info),'CG_to_direct_relative_solution_error':cgerror}
  print('BENCHMARK',name,var,'free',len(free_idx),'cond',cond,'Jacobi',cond_scaled,'CG',iter_counter[0],'affine_err',err_inf,flush=True)
 out[name]=variants
report={'status':'PASS SMALL REGIONAL P1 LAPLACE/POISSON BENCHMARK; GLOBAL FEM UNQUALIFIED',
 'problem':'unit scalar diffusion, k=1, P1 tetrahedron nodal FE; all boundary nodes locked Dirichlet',
 'manufactured_solution':'u=x+2y-0.3z, f=0, prescribed on every region boundary/interface vertex',
 'forced_solution':'homogeneous zero Dirichlet, source f=1; compare direct and CG residual',
 'caveat':'All-boundary Dirichlet is a solver benchmark, not real detector-bond electrical/heat boundary physics',
 'source_R39_element_sha256':sha(elepath),
 'source_R38_original_node_sha256':sha(basepath),
 'source_R310_relocated_node_sha256':sha(newpath),
 'results':out,
 'PDE_for_full_device':'NOT RUN',
 'global_mesh_conditioning':'NOT ASSESSED',
 'seconds':round(time.monotonic()-t0,2),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
OUT.mkdir(exist_ok=True)
(OUT/'regional_scalar_fem_benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
print('BENCHMARK_FINAL',json.dumps({'status':report['status'],'seconds':report['seconds'],'regions':list(out)},indent=2),flush=True)
