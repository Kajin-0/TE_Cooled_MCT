#!/usr/bin/env python3
"""R3.15 independent replay-coefficient audit:
reconstruct shared native CAD face 2349; compute per-side normal flux at 3
surface quadrature points; verify common P1/P2 trace and H1 gradient error
from saved coefficients with independent 216-point Duffy tetra quadrature.
No solver assembly or source mesh edits.
"""
from pathlib import Path
import json,math,hashlib,time,resource,itertools
import numpy as np
P=Path('/input');R=Path('/replay');O=Path('/out')
start=time.monotonic()
m=json.loads((P/'source_metadata.json').read_text())
node=np.loadtxt(P/'R38_430_domains.1.node',skiprows=1)
el=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
face=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
selection=el[np.isin(el[:,5],[410,420])]
tglobal=selection[:,1:5]
regions=selection[:,5]
original=np.unique(tglobal)
vertices=node[original-1,1:4]
tet=np.searchsorted(original,tglobal)
n=len(original); nt=len(tet)
native_iface=face[face[:,4]==2349,1:4]
assert (nt,n,len(native_iface))==(26053,6908,48)
iface=np.searchsorted(original,native_iface)
z0=float(m['faces']['2349']['center_mm'][2])
assert abs(z0-5.7849)<1e-12
ks={410:1.,420:10.}
c=.025;d=.05;q=1.;xc=-.35;yc=0.
def grad_exact(p,r):
 out=np.empty_like(p)
 out[...,0]=2*c*(p[...,0]-xc)
 out[...,1]=2*c*(p[...,1]-yc)
 out[...,2]=2*d*(p[...,2]-z0)+q/ks[r]
 return out
edges6=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
allpairs=np.concatenate([np.sort(tet[:,[i,j]],axis=1) for i,j in edges6])
edges,inverse=np.unique(allpairs,axis=0,return_inverse=True)
tet10=np.column_stack((tet,inverse.reshape(6,nt).T+n))
assert len(edges)==39753,(len(edges))
REF=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
def interpolate_at_face(tindex,pos,coeff,order):
 conn=tet[tindex]
 p=vertices[conn]
 J=np.column_stack((p[1]-p[0],p[2]-p[0],p[3]-p[0]))
 bary=np.r_[1.,0.,0.,0.]
 r=np.linalg.solve(J,pos-p[0])
 bary[1:]=r;bary[0]=1-r.sum()
 gl=REF@np.linalg.inv(J)
 if order==1:
  grad=coeff[conn]@gl
  value=coeff[conn]@bary
 else:
  vv=bary*(2*bary-1)
  gv=(4*bary-1)[:,None]*gl
  ev=np.asarray([4*bary[i]*bary[j] for i,j in edges6])
  ge=np.asarray([4*(bary[i]*gl[j]+bary[j]*gl[i]) for i,j in edges6])
  coef=coeff[tet10[tindex]]
  grad=coef[:4]@gv+coef[4:]@ge
  value=coef[:4]@vv+coef[4:]@ev
 return float(value),grad
# Real two-sided tetrahedral ownership independent of the primary solver.
incidence={}
for ti,t in enumerate(tet):
 for a,b,c_,opp in ((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3)):
  tri=(int(t[a]),int(t[b]),int(t[c_]))
  key=tuple(sorted(tri))
  incidence.setdefault(key,[]).append((ti,tri,int(t[opp]),int(regions[ti])))
assert all(len(incidence[tuple(sorted(t))])==2 for t in iface)
# normalized high-order H1 integration, independent of the primary 4-point tetra rule
abscissa,weights=np.polynomial.legendre.leggauss(6)
abscissa=(abscissa+1)/2;weights=weights/2
bary=[];wts=[]
for i,u in enumerate(abscissa):
 for j,v in enumerate(abscissa):
  for k,w in enumerate(abscissa):
   bary.append([(1-u)*(1-v)*(1-w),u,(1-u)*v,(1-u)*(1-v)*w])
   wts.append(6*(1-u)**2*(1-v)*weights[i]*weights[j]*weights[k])
bary=np.asarray(bary);wts=np.asarray(wts)
assert abs(sum(wts)-1)<2e-13
cases=[]
for order in (1,2):
 cf=np.load(R/f'P{order}_coefficients.npz')['coefficients']
 assert len(cf)==n if order==1 else len(cf)==n+len(edges)
 errors=[];areas=[];trace_errors=[];normal_flux_side={}
 for k,row in enumerate(iface):
  key=tuple(sorted(row.tolist()))
  points=vertices[row]
  area=float(np.linalg.norm(np.cross(points[1]-points[0],points[2]-points[0]))/2)
  # Three barycentric points exact integration of linear P2 face flux.
  testpts=[points.mean(axis=0)]
  for side,neighbors in enumerate(((0,1),(1,2),(0,2))):
   testpts.append((points[neighbors[0]]+points[neighbors[1]])/2)
  jumpper=[];traceper=[]
  for pt in testpts:
   flux=[];values=[]
   for ti,tri,op,reg in incidence[key]:
    val,gr=interpolate_at_face(ti,pt,cf,order)
    p0,p1,p2=vertices[list(tri)]
    nr=.5*np.cross(p1-p0,p2-p0)
    if np.dot(nr,vertices[op]-p0)>0:nr=-nr
    flux.append(float(ks[reg]*np.dot(gr,nr)/area))
    values.append(val)
   jumpper.append(flux[0]+flux[1])
   traceper.append(values[0]-values[1])
  errors.append(float(np.mean(jumpper)))
  trace_errors.extend(traceper)
  areas.append(area)
 errors=np.asarray(errors);areas=np.asarray(areas)
 rms=float(np.sqrt(np.dot(areas,errors*errors)/areas.sum())/q)
 trace=float(max(abs(v) for v in trace_errors))
 # volume H1 from independent Duffy 216 rule; batch no solver dependency
 square=0.;reference=0.
 connectivity=tet if order==1 else tet10
 for lo in range(0,nt,120):
  hi=min(lo+120,nt)
  p=vertices[tet[lo:hi]]
  J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
  determinant=np.linalg.det(J)
  assert np.all(determinant>0)
  vol=determinant/6
  gl=np.einsum('tji,aj->tai',np.linalg.inv(J),REF)
  material=regions[lo:hi]
  cc=cf[connectivity[lo:hi]]
  for lam,wt in zip(bary,wts):
   loc=np.einsum('a,tai->ti',lam,p)
   if order==1:gs=gl
   else:
    gv=np.stack([(4*lam[i]-1)*gl[:,i,:] for i in range(4)],axis=1)
    ge=np.stack([4*(lam[i]*gl[:,j,:]+lam[j]*gl[:,i,:]) for i,j in edges6],axis=1)
    gs=np.concatenate((gv,ge),axis=1)
   gn=np.einsum('ti,tij->tj',cc,gs)
   target=np.empty_like(loc)
   target[:,0]=2*.025*(loc[:,0]+.35)
   target[:,1]=2*.025*loc[:,1]
   target[:,2]=2*.05*(loc[:,2]-z0)+1/np.where(material==410,1.,10.)
   square+=float(np.dot(vol,wt*np.sum((gn-target)**2,axis=1)))
   reference+=float(np.dot(vol,wt*np.sum(target*target,axis=1)))
 relative=math.sqrt(square/reference)
 case={'order':order,'source_solution_sha256':hashlib.sha256((R/f'P{order}_coefficients.npz').read_bytes()).hexdigest(),
       'shared_cad_face_TRI3':len(iface),'shared_trace_max_abs_difference':trace,
       'independent_interface_flux_jump_RMS_relative':rms,
       'independent_interface_flux_jump_integral':float(np.dot(areas,errors)),
       'independent_H1_gradient_relative':relative,
       'shared_interface_area_mm2':float(areas.sum())}
 cases.append(case)
 print('R315_INDEPENDENT_CASE',json.dumps(case),flush=True)
original=json.loads((O/'two_material_comparison.json').read_text())
for item in cases:
 expected=next(k for k in original['P1_P2_runs'] if k['order']==item['order'])
 assert abs(item['independent_H1_gradient_relative']/expected['H1_relative_error']-1)<1e-5
 assert item['independent_interface_flux_jump_RMS_relative']<1
 assert item['shared_trace_max_abs_difference']<2e-9
 assert abs(item['shared_interface_area_mm2']/original['saved_mesh_interface_area_mm2']-1)<1e-12
assert cases[1]['independent_interface_flux_jump_RMS_relative']<1e-7
assert cases[1]['independent_H1_gradient_relative']<1e-7
result={'status':'PASS independent reconstructed shared CAD face 2349 flux and H1 integration on saved P1/P2 two-material solutions',
        'source':'Native immutable 410/420 shared tetra geometry and saved regional field coefficient arrays',
        'interfaces':{'tag':2349,'regions':[410,420],'triangles':48,'synthetic_k_ratio':10.},
        'separate_216pt_Duffy_H1':True,
        'P2_global_single_trace':True,
        'not_physical_material_model':True,
        'cases':cases,'elapsed_seconds':round(time.monotonic()-start,2),
        'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
(O/'independent_interface_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('R315_INDEPENDENT_FINAL',result['status'],flush=True)
