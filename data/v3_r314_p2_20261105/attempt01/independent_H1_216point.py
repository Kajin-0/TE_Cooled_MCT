#!/usr/bin/env python3
"""R3.14 independent H1 gradient-error auditor.
Replays saved P1/P2 coefficient vectors and performs independent 6x6x6 Duffy
integration on identical native straight TET4 geometry. Read-only source.
"""
import pathlib,json,hashlib,time,resource,math
import numpy as np
D=pathlib.Path('/input');R=pathlib.Path('/replay');O=pathlib.Path('/out')
T=time.monotonic()
original=json.loads((O/'P1_P2_comparison.json').read_text())
nodes=np.loadtxt(D/'R38_430_domains.1.node',skiprows=1)
data=np.loadtxt(D/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
g_tets=data[data[:,5]==420,1:5]
g_nodes=np.unique(g_tets)
xyz=nodes[g_nodes-1,1:4]
tet=np.searchsorted(g_nodes,g_tets)
m=len(tet);n=len(xyz)
pairs=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
edge_array=np.concatenate([np.sort(tet[:,[a,b]],axis=1) for a,b in pairs])
edge_ids,inv=np.unique(edge_array,axis=0,return_inverse=True)
t10=np.column_stack((tet,inv.reshape(6,m).T+n))
assert (n,m,len(edge_ids))==(6884,25905,39558)
origin=np.asarray(original['analytic_quadratic_origin_mm'])
scale=np.asarray(original['analytic_quadratic_scale_mm'])
inv2=1/(scale*scale)
ymin=float(xyz[:,1].min())
wave=float(np.pi/max(np.ptp(xyz,axis=0)[1],.05))
def grad_sol(p,nonlinear):
 r=2*(p-origin)*inv2
 if nonlinear:r[:,1]+=.25*wave*np.cos(wave*(p[:,1]-ymin))
 return r
x,w=np.polynomial.legendre.leggauss(6);x=(x+1)/2;w=w/2
bary=[];weights=[]
for i,u in enumerate(x):
 for j,v in enumerate(x):
  for k,q in enumerate(x):
   bary.append([(1-u)*(1-v)*(1-q),u,(1-u)*v,(1-u)*(1-v)*q])
   weights.append(6*(1-u)**2*(1-v)*w[i]*w[j]*w[k])
bary=np.asarray(bary);weights=np.asarray(weights)
assert abs(weights.sum()-1)<1e-12
REF=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
def file_hash(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for part in iter(lambda:f.read(4<<20),b''):h.update(part)
 return h.hexdigest()
runs=[]
for order,nonlin in ((2,False),(1,True),(2,True)):
 coeff_file=R/f'order{order}_nonlin{int(nonlin)}_solution.npz'
 coeff=np.load(coeff_file)['coeff']
 e=tet if order==1 else t10
 assert len(coeff)==(n if order==1 else n+len(edge_ids))
 numerator=0.;denominator=0.
 tic=time.monotonic()
 for lo in range(0,m,180):
  hi=min(lo+180,m)
  pos=xyz[tet[lo:hi]]
  J=np.stack((pos[:,1]-pos[:,0],pos[:,2]-pos[:,0],pos[:,3]-pos[:,0]),axis=2)
  determinant=np.linalg.det(J)
  assert np.all(determinant>0)
  volume=determinant/6
  gr=np.einsum('tji,aj->tai',np.linalg.inv(J),REF)
  nodal=coeff[e[lo:hi]]
  for L,weight in zip(bary,weights):
   v_pos=np.einsum('a,tai->ti',L,pos)
   if order==1:
    grads=gr
   else:
    gv=np.stack([(4*L[a]-1)*gr[:,a,:] for a in range(4)],axis=1)
    ge=np.stack([4*(L[a]*gr[:,b,:]+L[b]*gr[:,a,:]) for a,b in pairs],axis=1)
    grads=np.concatenate((gv,ge),axis=1)
   approx=np.einsum('ti,tij->tj',nodal,grads)
   exact=grad_sol(v_pos,nonlin)
   numerator+=float(np.dot(volume,weight*np.sum((approx-exact)**2,axis=1)))
   denominator+=float(np.dot(volume,weight*np.sum(exact*exact,axis=1)))
 value=math.sqrt(numerator/denominator)
 known=next(r['H1_seminorm_relative'] for r in original['runs'] if r['order']==order and ('sinusoidal' in r['manufactured'])==nonlin)
 absdiff=abs(value-known)
 reldiff=absdiff/known
 item={'order':order,'nonpolynomial':nonlin,'quadrature':'independent 216-point 6x6x6 Duffy Gauss-Legendre',
       'replay_solution_sha256':file_hash(coeff_file),
       'independent_H1_relative':value,'original_64point_H1_relative':known,
       'relative_error_between_quadratures':reldiff,
       'seconds':round(time.monotonic()-tic,2)}
 runs.append(item)
 print('INDEPENDENT_R314_H1',json.dumps(item),flush=True)
 assert reldiff<1e-3,(order,nonlin,reldiff)
delta=next(r['independent_H1_relative'] for r in runs if r['order']==1)/next(r['independent_H1_relative'] for r in runs if r['order']==2 and r['nonpolynomial'])
report={'status':'PASS independently re-evaluated P1/P2 gradient H1 errors on 216-point tetra Duffy integration',
 'source_R39_sha256':file_hash(D/'R39_430_domains.1.ele'),
 'source_R38_node_sha256':file_hash(D/'R38_430_domains.1.node'),
 'source_nodes_modified':False,'boundary_geometry_modified':False,
 'tetrahedra':m,'unique_P2_global_edges':len(edge_ids),
 'quadrature_integral_total':float(weights.sum()),
 'independent_P1_P2_nonlinear_error_ratio':delta,
 'runs':runs,'total_seconds':round(time.monotonic()-T,2),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
(O/'independent_H1_216point.json').write_text(json.dumps(report,indent=2)+'\n')
print('R314_INDEPENDENT_H1_PASS',delta,flush=True)
