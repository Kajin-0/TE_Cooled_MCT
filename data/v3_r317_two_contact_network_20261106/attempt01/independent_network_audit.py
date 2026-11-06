#!/usr/bin/env python3
"""R3.17 independent readback of two native CAD contact faces and 216pt H1.
Reads saved field coefficients; no assembly or PDE solve. All source CAD and
mesh are read-only. Independently rebuilds P2 edge identities and normals.
"""
from pathlib import Path
from collections import defaultdict
import json,hashlib,math,time
import numpy as np
P=Path('/input');R=Path('/result');START=time.monotonic()
summary=json.loads((R/'network_summary.json').read_text())
m=json.loads((P/'source_metadata.json').read_text())
node=np.loadtxt(P/'R38_430_domains.1.node',skiprows=1)
ele=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
fac=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
REG=(408,410,420);CONTACT=((408,410,2336),(410,420,2349))
K={408:2.,410:1.,420:10.};GC={2336:4.,2349:5.}
selection=ele[np.isin(ele[:,5],REG)]
orig=selection[:,1:5]
owner=selection[:,5]
coded=np.unique(owner[:,None]*1000000+orig)
tet=np.searchsorted(coded,owner[:,None]*1000000+orig)
pos=node[coded%1000000-1,1:4]
T=len(tet);NV=len(pos)
edgepairs=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
pairarray=np.concatenate([np.sort(tet[:,[i,j]],axis=1) for i,j in edgepairs])
edges,inv=np.unique(pairarray,axis=0,return_inverse=True)
t10=np.column_stack((tet,inv.reshape(6,T).T+NV))
assert (T,NV,NV+len(edges))==(26290,7055,47334)
REF=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
incidence=defaultdict(list)
for i,t in enumerate(orig):
 for a,b,c,o in ((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3)):
  k=tuple(sorted(int(t[x]) for x in (a,b,c)))
  incidence[k].append((i,int(owner[i]),int(tet[i,o])))
z1=m['faces']['2336']['center_mm'][2]
z2=m['faces']['2349']['center_mm'][2]
YRANGE=float(np.ptp(pos[:,1]));YMIN=float(np.min(pos[:,1]))
W=math.pi/max(YRANGE,.05)
BETA=.15;A=.025;QX=1.8;QY=2.5
def flux_var(p):return 1+QX*(p[...,0]+.35)+QY*p[...,1]
def s(p,r):
 z=p[...,2]
 if r==408:return (z-z1)/2.-1/4.
 if r==410:return z-z1
 return (z-z2)/10.+(z2-z1)+1/5.
def analytic_gradient(p,r,nl):
 g=np.empty_like(p)
 ss=s(p,r)
 g[...,0]=2*A*(p[...,0]+.35)+QX*ss
 g[...,1]=2*A*p[...,1]+QY*ss
 if nl:g[...,1]+=BETA*W*np.cos(W*(p[...,1]-YMIN))
 g[...,2]=flux_var(p)/K[r]
 return g
def interp(i,point,coefficient,order):
 p=pos[tet[i]]
 mat=np.column_stack((p[1]-p[0],p[2]-p[0],p[3]-p[0]))
 gradl=REF@np.linalg.inv(mat)
 b=np.linalg.solve(mat,point-p[0])
 l=np.r_[1-b.sum(),b]
 if order==1:
  shape=l;g=gradl;idx=tet[i]
 else:
  shape=np.r_[l*(2*l-1),[4*l[a]*l[b] for a,b in edgepairs]]
  g=np.vstack(((4*l-1)[:,None]*gradl,
      [4*(l[a]*gradl[b]+l[b]*gradl[a]) for a,b in edgepairs]))
  idx=t10[i]
 return float(coefficient[idx]@shape), coefficient[idx]@g
qx,gw=np.polynomial.legendre.leggauss(6);qx=(qx+1)/2;gw=gw/2
lambdas=[];weights=[]
for i,u in enumerate(qx):
 for j,v in enumerate(qx):
  for k,w in enumerate(qx):
   lambdas.append([(1-u)*(1-v)*(1-w),u,(1-u)*v,(1-u)*(1-v)*w])
   weights.append(6*(1-u)**2*(1-v)*gw[i]*gw[j]*gw[k])
lambdas=np.array(lambdas);weights=np.array(weights)
assert abs(weights.sum()-1)<1e-12
result=[]
for nonlinear in (False,True):
 for order in (1,2):
  file=R/f'P{order}_nonlin{int(nonlinear)}_field.npz'
  coeff=np.load(file)['field']
  assert len(coeff)==(NV if order==1 else NV+len(edges))
  reference=next(x for x in summary['results'] if x['order']==order and x['nonlinear']==nonlinear)
  contacts={}
  for ra,rb,tag in CONTACT:
   face=fac[fac[:,4]==tag]
   jumps=[];flux=[];robin=[];aa=[];expected_q=[]
   for f in face:
    key=tuple(sorted(int(x) for x in f[1:4]))
    entries=incidence[key]
    assert {x[1] for x in entries}=={ra,rb} and len(entries)==2
    p=node[f[1:4]-1,1:4]
    centroid=p.mean(axis=0)
    area=.5*np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))
    surface={}
    for ti,r,opp in entries:
     u,gr=interp(ti,centroid,coeff,order)
     n=np.array([0.,0.,1.]) if r==ra else np.array([0.,0.,-1.])
     normalflux=K[r]*float(np.dot(gr,n))
     surface[r]=(u,normalflux)
    delta=surface[ra][0]-surface[rb][0]
    jumps.append(delta)
    flux.append(surface[ra][1]+surface[rb][1])
    robin.append(surface[ra][1]+GC[tag]*delta)
    aa.append(area)
    expected_q.append(flux_var(centroid))
   aa=np.asarray(aa);jumps=np.asarray(jumps);flux=np.asarray(flux)
   robin=np.asarray(robin);expected_q=np.asarray(expected_q)
   wrms=lambda arr:float(np.sqrt(np.dot(aa,arr*arr)/aa.sum()))
   qRMS=wrms(expected_q)
   c={'tag':tag,'owner_pair':[ra,rb],'triangles':len(face),
      'interface_area_mm2':float(aa.sum()),
      'varying_analytic_q_range':[float(expected_q.min()),float(expected_q.max())],
      'independent_RMS_Robin_rel':wrms(robin)/qRMS,
      'independent_RMS_flux_balance_rel':wrms(flux)/qRMS,
      'independent_RMS_jump_error_rel':wrms(jumps+expected_q/GC[tag])/qRMS,
      'independent_signed_imbalance_integral':float(np.dot(aa,flux))}
   prev=reference['contacts'][str(tag)]
   for old,new in (('Robin_RMS_rel','independent_RMS_Robin_rel'),
                   ('flux_balance_RMS_rel','independent_RMS_flux_balance_rel'),
                   ('contact_jump_RMS_err_relative_to_q','independent_RMS_jump_error_rel')):
    assert abs(prev[old]-c[new])/max(abs(prev[old]),1e-30)<2e-5,(order,nonlinear,tag,old)
   contacts[str(tag)]=c
  # 216-point independent H1, no reuse of primary 4point rule.
  numerator=0.;denominator=0.
  idxs=tet if order==1 else t10
  for lo in range(0,T,135):
   hi=min(T,lo+135)
   p=pos[tet[lo:hi]]
   J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
   dv=np.linalg.det(J)
   assert np.all(dv>0)
   vol=dv/6
   gradL=np.einsum('tji,aj->tai',np.linalg.inv(J),REF)
   cv=coeff[idxs[lo:hi]]
   mats=owner[lo:hi]
   for l,w in zip(lambdas,weights):
    xx=np.einsum('a,tai->ti',l,p)
    if order==1:gr=gradL
    else:
     vert=(4*l-1)[None,:,None]*gradL
     ge=np.stack([4*(l[a]*gradL[:,b,:]+l[b]*gradL[:,a,:]) for a,b in edgepairs],axis=1)
     gr=np.concatenate((vert,ge),axis=1)
    approx=np.einsum('ti,tij->tj',cv,gr)
    expected=np.empty_like(xx)
    ss=np.select([mats==408,mats==410,mats==420],
        [(xx[:,2]-z1)/2-.25,xx[:,2]-z1,(xx[:,2]-z2)/10+(z2-z1)+.2])
    expected[:,0]=2*A*(xx[:,0]+.35)+QX*ss
    expected[:,1]=2*A*xx[:,1]+QY*ss
    if nonlinear:expected[:,1]+=BETA*W*np.cos(W*(xx[:,1]-YMIN))
    expected[:,2]=flux_var(xx)/np.select([mats==408,mats==410,mats==420],[K[408],K[410],K[420]])
    numerator+=float(np.dot(vol,w*np.einsum('ti,ti->t',approx-expected,approx-expected)))
    denominator+=float(np.dot(vol,w*np.einsum('ti,ti->t',expected,expected)))
  h1=math.sqrt(numerator/denominator)
  rec={'order':order,'nonlinear':nonlinear,'H1_relative_216pt':h1,
       'H1_relative_4pt_primary':reference['H1_relative_4pt'],
       'H1_relative_quadrature_discrepancy':h1/reference['H1_relative_4pt']-1,
       'contacts':contacts,
       'saved_solution_sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
  if not nonlinear:
   assert abs(rec['H1_relative_quadrature_discrepancy'])<.0001
  result.append(rec)
  print('R317_INDEPENDENT',json.dumps({'order':order,'nonlinear':nonlinear,'H1_216':h1,
    'H1_4':reference['H1_relative_4pt'],'contact2336':contacts['2336']['independent_RMS_Robin_rel'],
    'contact2349':contacts['2349']['independent_RMS_Robin_rel']}),flush=True)
assert len(result)==4
assert result[3]['H1_relative_216pt']<result[2]['H1_relative_216pt']/50
assert all(c['independent_RMS_Robin_rel']<1e-5 and c['independent_RMS_flux_balance_rel']<1e-5 for c in result[3]['contacts'].values())
receipt={'status':'PASS independent 216-point two-contact native face and nonpolynomial H1 audit',
    'cases':result,'source_mesh_unchanged':True,'full_physical_PDE':'NOT RUN',
    'elapsed_seconds':round(time.monotonic()-START,2)}
(R/'independent_network_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('R317_INDEPENDENT_PASS',receipt['elapsed_seconds'],flush=True)
