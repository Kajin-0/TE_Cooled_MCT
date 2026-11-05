#!/usr/bin/env python3
"""R3.14 read-only Au bond-8 P1/P2 comparison on original native straight TET4 geometry.
Quadratic Lagrange P2 is a solution basis ONLY; all 13540 boundary facets stay planar TRI3.
Independent non-affine manufactured Poisson forcing, exact boundary Dirichlet/Neumann,
high-order quadrature, independently measured relative H1 gradient error.
"""
from pathlib import Path
import hashlib,json,math,resource,time,scipy
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spilu,gmres,LinearOperator
P=Path('/input');O=Path('/out')
t0=time.monotonic()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
meta=json.loads((P/'source_metadata.json').read_text())
ele=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
node=np.loadtxt(P/'R38_430_domains.1.node',dtype=np.float64,skiprows=1)
face=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
REGION=420
tet_global=ele[ele[:,5]==REGION,1:5]
gnodes=np.unique(tet_global)
xyz=node[gnodes-1,1:4]
tets=np.searchsorted(gnodes,tet_global)
nvert=len(xyz);nt=len(tets)
assert (nvert,nt)==(6884,25905)
tags=[int(k) for k,v in meta['faces'].items() if REGION in v['owner_volume_ids']]
sf=face[np.isin(face[:,4],tags)]
sface=np.searchsorted(gnodes,sf[:,1:4])
assert len(sface)==13540 and np.all(gnodes[sface]==sf[:,1:4])
dirface=2399
dtri=sface[sf[:,4]==dirface]
assert len(dtri)==6048
EDGE_PAIRS=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
FACE_EDGE_PAIRS=((0,1),(0,2),(1,2))
block=[]
for a,b in EDGE_PAIRS:
 block.append(np.sort(tets[:,[a,b]],axis=1))
all_edges=np.concatenate(block)
edges,inv=np.unique(all_edges,axis=0,return_inverse=True)
edge_tags=inv.reshape((6,nt)).T+nvert
local10=np.column_stack((tets,edge_tags)).astype(np.int32)
ndofs=nvert+len(edges)
# For surface edge dof lookup, lexicographic structured row key
etype=np.dtype([('a','<i4'),('b','<i4')])
def keys2(e):return np.ascontiguousarray(e,np.int32).view(etype).reshape(-1)
edgekeys=keys2(edges)
assert np.array_equal(np.unique(edges,axis=0),edges)
def boundary_elem6(f):
 f_edges=np.concatenate([np.sort(f[:,[a,b]],axis=1) for a,b in FACE_EDGE_PAIRS])
 idx=np.searchsorted(edgekeys,keys2(f_edges))
 assert np.all(idx<len(edges)) and np.all(edgekeys[idx]==keys2(f_edges))
 return np.column_stack((f,idx.reshape(3,len(f)).T+nvert))
sface6=boundary_elem6(sface)
dfix6=boundary_elem6(dtri)
fix1=np.unique(dtri)
fix2=np.unique(dfix6)
assert len(fix1)==3072
assert len(fix2)>len(fix1)
# Exact boundary triangle incidence and outward normal
faces=((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3))
adj={}
for c in tets:
 for a,b,c_,o in faces:
  v=(int(c[a]),int(c[b]),int(c[c_]))
  key=tuple(sorted(v))
  if key in adj:adj[key]=None
  else:adj[key]=(v,int(c[o]))
surface_map={k:v for k,v in adj.items() if v is not None}
assert len(surface_map)==13540
assert set(surface_map)=={tuple(sorted(x)) for x in sface}
surface_dirs=np.array([x for x in sf[:,4]!=dirface])
# Degree-4 tetrahedral quadrature, normalized weights sum 1
Q4=[([.25]*4,-.07893333333333333)]
for k in range(4):
 a=[.07142857142857142]*4;a[k]=.7857142857142857
 Q4.append((a,.04573333333333333))
import itertools
for combo in itertools.combinations(range(4),2):
 a=[.1005964238332008]*4
 for k in combo:a[k]=.3994035761667992
 Q4.append((a,.14933333333333335))
QL=np.array([x for x,w in Q4])
QW=np.array([w for x,w in Q4])
assert len(QL)==11 and abs(QW.sum()-1)<1e-12
# Degree 5 Dunavant seven-point face rule
QF=[([1/3]*3,.225)]
for val,rest,wt in [(0.059715871789770,0.470142064105115,0.132394152788506),
                     (0.797426985353087,0.101286507323456,0.125939180544827)]:
 for k in range(3):
  bary=[rest]*3;bary[k]=val
  QF.append((bary,wt))
FL=np.array([a for a,w in QF]);FW=np.array([w for a,w in QF])
assert abs(FW.sum()-1)<1e-12
# Independent degree-5/6 Duffy quadrature for H1 error
gx,gw=np.polynomial.legendre.leggauss(4);gx=(gx+1)/2;gw=gw/2
HL=[];HW=[]
for i,u in enumerate(gx):
 for j,v in enumerate(gx):
  for k,w in enumerate(gx):
   HL.append([(1-u)*(1-v)*(1-w),u,(1-u)*v,(1-u)*(1-v)*w])
   HW.append(float(6*(1-u)**2*(1-v)*gw[i]*gw[j]*gw[k]))
HL=np.array(HL);HW=np.array(HW)
assert abs(HW.sum()-1)<1e-13
origin=xyz.mean(axis=0)
scale=np.maximum(np.ptp(xyz,axis=0),.05)
inv_sq=1/scale**2
ymin=float(xyz[:,1].min())
wave_k=float(math.pi/max(np.ptp(xyz,axis=0)[1],.05))
beta=.25
def ue(p,nonlinear):
 d=(p-origin)/scale
 res=np.sum(d*d,axis=-1)
 if nonlinear:res+=beta*np.sin(wave_k*(p[...,1]-ymin))
 return res
def ge(p,nonlinear):
 res=2*(p-origin)*inv_sq
 if nonlinear:res[...,1]+=beta*wave_k*np.cos(wave_k*(p[...,1]-ymin))
 return res
def ff(p,nonlinear):
 val=-2*float(inv_sq.sum())
 if nonlinear:return val+beta*wave_k**2*np.sin(wave_k*(p[...,1]-ymin))
 return val+np.zeros(p.shape[:-1])
refgrad=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
def basis(lam,gradlam,order):
 if order==1:return lam,gradlam
 vs=lam*(2*lam-1)
 gs=(4*lam-1)[...,None]*gradlam
 ev=np.stack([4*lam[...,a]*lam[...,b] for a,b in EDGE_PAIRS],axis=-1)
 eg=np.stack([4*(lam[...,a,None]*gradlam[...,b,:]+lam[...,b,None]*gradlam[...,a,:]) for a,b in EDGE_PAIRS],axis=-2)
 return np.concatenate((vs,ev),axis=-1),np.concatenate((gs,eg),axis=-2)
def surface_basis(l,order):
 if order==1:return l
 vals=[l[:,i]*(2*l[:,i]-1) for i in range(3)]
 vals.extend([4*l[:,a]*l[:,b] for a,b in FACE_EDGE_PAIRS])
 return np.stack(vals,axis=1)
def prepare_surface_sources(order,nonlinear):
 nd=nvert if order==1 else ndofs
 rhs=np.zeros(nd)
 for i in range(0,len(sface),500):
  ids=sface[i:i+500]
  attr=sf[i:i+500,4]
  outward=np.empty((len(ids),3))
  for j,tri in enumerate(ids):
   key=tuple(sorted(map(int,tri)))
   oriented,opp=surface_map[key]
   p0,p1,p2=xyz[list(oriented)]
   narea=.5*np.cross(p1-p0,p2-p0)
   if np.dot(narea,xyz[opp]-p0)>0:narea=-narea
   outward[j]=narea
  mask=attr!=dirface
  if not np.any(mask):continue
  ids=ids[mask];normal_area=outward[mask]
  verts=xyz[ids]
  surface_nodes=(ids if order==1 else sface6[i:i+500][mask])
  B=surface_basis(FL,order)
  accum=np.zeros((len(ids),3 if order==1 else 6))
  for j in range(len(FL)):
   x=np.einsum('a,bac->bc',FL[j],verts)
   flux=np.einsum('bi,bi->b',ge(x,nonlinear),normal_area)
   accum+=FW[j]*flux[:,None]*B[j]
  np.add.at(rhs,surface_nodes.ravel(),accum.ravel())
 return rhs
def solve_case(order,nonlinear):
 nd=nvert if order==1 else ndofs
 fix=fix1 if order==1 else fix2
 free=np.setdiff1d(np.arange(nd,dtype=np.int32),fix)
 tstart=time.monotonic()
 rhs=prepare_surface_sources(order,nonlinear)
 # Volume stiffness and source, in manageable fixed 300-element blocks
 rows=[];cols=[];data=[]
 B=4 if order==1 else 10
 for lo in range(0,nt,300):
  hi=min(lo+300,nt)
  verts=xyz[tets[lo:hi]]
  J=np.stack((verts[:,1]-verts[:,0],verts[:,2]-verts[:,0],verts[:,3]-verts[:,0]),axis=2)
  det=np.linalg.det(J)
  assert np.all(det>0)
  vol=det/6
  inv=np.linalg.inv(J)
  gl=np.einsum('tji,aj->tai',inv,refgrad)
  loc=np.zeros((hi-lo,B,B))
  loads=np.zeros((hi-lo,B))
  for lam,w in zip(QL,QW):
   ll=np.broadcast_to(lam,(hi-lo,4))
   N,g=basis(ll,gl,order)
   loc+=w*vol[:,None,None]*np.einsum('tai,tbi->tab',g,g)
   pts=np.einsum('a,bac->bc',lam,verts)
   loads+=w*vol[:,None]*ff(pts,nonlinear)[:,None]*N
  index=tets[lo:hi] if order==1 else local10[lo:hi]
  rows.append(np.broadcast_to(index[:,:,None],loc.shape).ravel().copy())
  cols.append(np.broadcast_to(index[:,None,:],loc.shape).ravel().copy())
  data.append(loc.ravel())
  np.add.at(rhs,index.ravel(),loads.ravel())
 K=coo_matrix((np.concatenate(data),(np.concatenate(rows),np.concatenate(cols))),shape=(nd,nd)).tocsr()
 del rows,cols,data
 K.sum_duplicates()
 A=K[free,:][:,free].tocsr()
 # edge node physical coordinates = midpoint; exact Dirichlet trace at edge DOFs
 if order==1:dofpts=xyz
 else:dofpts=np.vstack((xyz,(xyz[edges[:,0]]+xyz[edges[:,1]])*.5))
 b=rhs[free]-K[free,:][:,fix]@ue(dofpts[fix],nonlinear)
 counter=[0]
 def cb(_):counter[0]+=1
 tsolve=time.monotonic()
 try:
  ilu=spilu(A.tocsc(),drop_tol=1e-5,fill_factor=16)
  M=LinearOperator(A.shape,matvec=ilu.solve,dtype=np.float64)
  uh,info=gmres(A,b,M=M,restart=60,maxiter=45,rtol=1e-9,atol=0,callback=cb,callback_type='pr_norm')
  res=float(np.linalg.norm(A@uh-b)/np.linalg.norm(b))
  nnz=int(ilu.L.nnz+ilu.U.nnz)
 except Exception as ex:
  return {'status':'PRECONDITIONER_FAIL','error':str(ex)[:320]}
 report={'status':'PASS' if info==0 and res<1e-8 else 'SOLVER_STOP',
 'order':order,'manufactured':'nonpolynomial sinusoidal+quadratic' if nonlinear else 'exact quadratic',
 'tets':nt,'mesh_geometry_order':1,'dofs_total':nd,'fixed_dofs':len(fix),
 'free_dofs':len(free),'matrix_NNZ':int(A.nnz),'ILU_factor_NNZ':nnz,
 'ILU_GMRES_info':int(info),'ILU_GMRES_iterations':counter[0],
 'true_relative_residual':res,'factor_and_solver_seconds':round(time.monotonic()-tsolve,3),
 'assembly_plus_solver_seconds':round(time.monotonic()-tstart,3)}
 print('R314_SOLVE',json.dumps(report),flush=True)
 if report['status']!='PASS':return report
 coeff=ue(dofpts,nonlinear)
 coeff[free]=uh
 # independent 64-point Duffy rule H1 error; stage in moderate 180-tet batches
 numer=0.0;denom=0.0
 for lo in range(0,nt,180):
  hi=min(lo+180,nt)
  p=xyz[tets[lo:hi]]
  J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
  vv=np.linalg.det(J)/6
  inv=np.linalg.inv(J)
  gl=np.einsum('tji,aj->tai',inv,refgrad)
  coeffloc=coeff[(tets if order==1 else local10)[lo:hi]]
  for l,w in zip(HL,HW):
   basis_l=np.broadcast_to(l,(hi-lo,4))
   N,g=basis(basis_l,gl,order)
   approx=np.einsum('bi,bij->bj',coeffloc,g)
   xx=np.einsum('a,bac->bc',l,p)
   target=ge(xx,nonlinear)
   numer+=float(np.sum(vv*w*np.sum((approx-target)**2,axis=1)))
   denom+=float(np.sum(vv*w*np.sum(target**2,axis=1)))
 report['exact_solution_H1_seminorm_norm']=math.sqrt(denom)
 report['H1_seminorm_absolute']=math.sqrt(numer)
 report['H1_seminorm_relative']=math.sqrt(numer/denom)
 report['elapsed_seconds_including_H1']=round(time.monotonic()-tstart,3)
 print('R314_H1',order,nonlinear,report['H1_seminorm_relative'],'sec',report['elapsed_seconds_including_H1'],flush=True)
 return report
# Minimal exact P2 interpolation consistency checks, including surface trace.
rng=np.random.default_rng(314)
l=rng.dirichlet(np.ones(4),size=200)
dummy=np.broadcast_to(refgrad,(len(l),4,3))
for order in (1,2):
 n,g=basis(l,dummy,order)
 assert np.max(np.abs(n.sum(axis=1)-1))<2e-14
 assert np.max(np.abs(g.sum(axis=1)))<2e-14
# For a quadratic polynomial in XYZ, P2 interpolation gradient must be EXACT.
for _ in range(3):
 x=rng.normal(size=(4,3))
 j=np.stack((x[1]-x[0],x[2]-x[0],x[3]-x[0]),axis=1)
 if abs(np.linalg.det(j))<.001:continue
 gg=np.einsum('ji,aj->ai',np.linalg.inv(j),refgrad)
 xx=np.vstack((x,np.array([(x[a]+x[b])/2 for a,b in EDGE_PAIRS])))
 qv=ue(xx,False)
 ll=rng.dirichlet(np.ones(4),size=20)
 nn,grad=basis(ll,np.broadcast_to(gg,(len(ll),4,3)),2)
 xq=ll@x
 err=np.max(np.abs(np.einsum('i,qij->qj',qv,grad)-ge(xq,False)))
 assert err<4e-10,err
print('R314_BASIS_PREFLIGHT','nodes',nvert,'edges',len(edges),'P2_DOFS',ndofs,'boundary_TRI3',len(sf),'Dirichlet_vertex',len(fix1),'Dirichlet_P2',len(fix2),flush=True)
O.mkdir(exist_ok=True)
runs=[]
# One exact polynomial P2 test and a fair non-polynomial P1 / P2 comparison.
for order,nonlin in ((2,False),(1,True),(2,True)):
 if time.monotonic()-t0>215:break
 r=solve_case(order,nonlin)
 runs.append(r)
 (O/f'order{order}_nonlin{int(nonlin)}.json').write_text(json.dumps(r,indent=2)+'\n')
 if r['status']!='PASS':break
status='PASS P2 EXACT POLYNOMIAL AND NONPOLYNOMIAL H1 COMPARISON' if len(runs)==3 and all(x['status']=='PASS' for x in runs) else 'PARTIAL/STOP P2 COMPARISON'
report={'status':status,
 'region':'detector_bond8','native_volume_id':REGION,'source_mesh':'R3.9 25905 original linear tetrahedra',
 'source_ownership_faces':13540,'source_Dirichlet_face':dirface,
 'source_mesh_coordinates_unchanged':True,'all_native_TRI3_geometry_unchanged':True,
 'P2_basis':'10-node quadratic Lagrange using four existing vertices and six unique edge-midpoint DOFs; geometry still linear/planar',
 'volume_quadrature':'Keast 11-point degree-4 normalized','boundary_quadrature':'Dunavant 7-point degree-5 normalized',
 'H1_error_quadrature':'independent degree-4 Gauss Duffy product (64 points/tet)',
 'analytic_quadratic_origin_mm':list(map(float,origin)),
 'analytic_quadratic_scale_mm':list(map(float,scale)),
 'analytic_nonlinear':'u_quad + 0.25 sin(k(y-y_min)), k=pi/max(y_range,0.05mm)',
 'runs':runs,'full_device_PDE':'NOT RUN','global_convergence':'NOT DEMONSTRATED',
 'source_sha256':{x.name:sha(x) for x in (P/'R39_430_domains.1.ele',P/'R38_430_domains.1.node',P/'R38_430_domains.1.face')},
 'seconds':round(time.monotonic()-t0,2),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
(O/'P1_P2_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print('R314_RESULT',json.dumps({'status':status,'seconds':report['seconds'],'peak_RSS_MiB':report['peak_RSS_MiB'],
 'outcomes':[{'order':x['order'],'nonlinearity':x['manufactured'],'status':x['status'],'H1':x.get('H1_seminorm_relative')} for x in runs]},indent=2),flush=True)
