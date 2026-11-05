#!/usr/bin/env python3
"""R3.11 mixed boundary P1 scalar Poisson benchmark, bond8 native-largest face Dirichlet, remaining natural Neumann."""
import json,time,hashlib,resource
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import cg,eigsh,spsolve
from scipy.sparse.csgraph import connected_components
import warnings
R=Path('/input')
OUT=Path('/out')
t0=time.monotonic()
meta=json.loads((R/'source_metadata.json').read_text())
source=R/'R39_430_domains.1.ele'
ele=np.loadtxt(source,dtype=np.int32,skiprows=1)
fac=np.loadtxt(R/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
selected=ele[ele[:,5]==420,1:5]
assert 20000<len(selected)<30000
faces_owned=[int(k) for k,v in meta['faces'].items() if 420 in v['owner_volume_ids']]
native_faces=fac[np.isin(fac[:,4],faces_owned)]
counts=np.bincount(native_faces[:,4],minlength=2441)
tag=int(np.argmax(counts))
fixed_nodes=np.unique(native_faces[native_faces[:,4]==tag,1:4])
gnodes=np.unique(selected)
assert np.all(np.isin(fixed_nodes,gnodes))
maptags=np.full(156766,-1,dtype=np.int32);maptags[gnodes]=np.arange(len(gnodes))
localtet=maptags[selected]
fix=maptags[fixed_nodes]
free=np.setdiff1d(np.arange(len(gnodes)),fix)
assert len(fix)>30 and len(free)>100
results={}
for key,path in [('R39',R/'R38_430_domains.1.node'),('R310',R/'R310_430_domains.1.node')]:
 node=np.loadtxt(path,skiprows=1)
 xyz=node[gnodes-1,1:4]
 t=xyz[localtet]
 J=np.stack((t[:,1]-t[:,0],t[:,2]-t[:,0],t[:,3]-t[:,0]),axis=2)
 det=np.linalg.det(J);assert np.all(det>0)
 volume=det/6
 inv=np.linalg.inv(J)
 ref=np.array([[-1,-1,-1],[1,0,0],[0,1,0],[0,0,1]])
 grad=np.einsum('tji,aj->tai',inv,ref)
 loc=volume[:,None,None]*np.einsum('tai,tbi->tab',grad,grad)
 rr=np.broadcast_to(localtet[:,:,None],loc.shape).ravel()
 cc=np.broadcast_to(localtet[:,None,:],loc.shape).ravel()
 K=sp.coo_matrix((loc.ravel(),(rr,cc)),shape=(len(gnodes),len(gnodes))).tocsr()
 A=K[free,:][:,free].tocsr()
 f=np.bincount(localtet.ravel(),weights=np.repeat(volume[:,None]/4,4,axis=1).ravel(),minlength=len(gnodes))[free]
 diagonal=A.diagonal()
 assert np.all(diagonal>0)
 pre=sp.diags(1/diagonal)
 it=[0]
 def count(_):it[0]+=1
 u,info=cg(A,f,M=pre,rtol=1e-8,atol=0,maxiter=2500,callback=count)
 residual=float(np.linalg.norm(A@u-f)/np.linalg.norm(f))
 nc,labels=connected_components(A, directed=False)
 comp=np.bincount(labels)
 row_sum=np.asarray(A.sum(axis=1)).ravel()
 # compare graph component sums: a positive row sum indicates Dirichlet anchoring
 component_anchor=[float(np.sum(row_sum[labels==i])) for i in range(nc)]
 with warnings.catch_warnings(record=True) as caught:
  warnings.simplefilter('always')
  direct=spsolve(A,f)
 direct_res=float(np.linalg.norm(A@direct-f)/np.linalg.norm(f)) if np.all(np.isfinite(direct)) else float('inf')
 print('STRUCTURAL',key,'connected_components',nc,'sizes',comp.tolist()[:12],
       'component_anchor',component_anchor[:12],
       'diag_min',float(diagonal.min()),'diag_max',float(diagonal.max()),
       'row_sum_minmax',[float(row_sum.min()),float(row_sum.max())],
       'direct_res',direct_res,'warnings',[str(x.message) for x in caught][:3],flush=True)
 out={'tetrahedra':len(selected),'nodes':len(gnodes),'fixed_native_face':tag,'fixed_face_TRI3_count':int(counts[tag]),
  'Dirichlet_nodes':len(fix),'free_degrees_of_freedom':len(free),'nonpositive_cells':int(np.count_nonzero(det<=0)),
  'Jacobi_preconditioned_CG_iterations_rtol_1e_8':it[0],'CG_info':int(info),
  'relative_equation_residual':residual,'solution_L2':float(np.linalg.norm(u)),
  'source_total_integral_mm3':float(volume.sum()),
  'sparse_Kff_nonzeros':int(A.nnz), 'connected_components':int(nc),
  'component_sizes':comp.tolist(), 'component_anchor':component_anchor,
  'direct_relative_residual':direct_res,'direct_warnings':[str(x.message) for x in caught]}
 results[key]=out
 print('MIXED_BC',key,'DOF',len(free),'ITER',it[0],'info',info,'res',residual,'runtime',round(time.monotonic()-t0,2),flush=True)
report={'status':'PASS MIXED_BC REGIONAL SCALAR POISSON BENCHMARK' if all(v['CG_info']==0 and v['relative_equation_residual']<1e-7 for v in results.values()) else 'FAIL REGIONAL SOLVE',
 'test':'unit scalar P1 FE, f=1, Dirichlet u=0 on native CAD face with largest TRI3 count; homogeneous natural Neumann elsewhere; Jacobi PCG',
 'regions':['detector_bond8'],'R39_R310':results,'physical_model':'NO, deliberately abstract unit scalar diffusion',
 'full_package_solver':'NOT RUN','mesh_convergence':'NOT TESTED','time_s':round(time.monotonic()-t0,2),
 'RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2)}
(OUT/'mixed_bc_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
print('FINAL',report['status'],flush=True)
