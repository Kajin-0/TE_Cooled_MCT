#!/usr/bin/env python3
"""Independent R3.16 split-trace face2349 contact-law and 216-pt H1 checks.
Reads saved coefficient arrays; does NOT solve a PDE or import primary FEM.
"""
from pathlib import Path
from collections import defaultdict
import json,math,time,hashlib
import numpy as np
P=Path('/input');R=Path('/result');tstart=time.monotonic()
m=json.loads((P/'source_metadata.json').read_text())
nodes=np.loadtxt(P/'R38_430_domains.1.node',skiprows=1)
cells=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
faces=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
selected=cells[np.isin(cells[:,5],[410,420])]
original=selected[:,1:5]
regions=selected[:,5]
enc=regions[:,None]*1000000+original
uniq=np.unique(enc)
tet=np.searchsorted(uniq,enc)
xyz=nodes[uniq%1000000-1,1:4]
n=len(xyz);nt=len(tet)
assert n==6957 and nt==26053
E=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
arr=np.concatenate([np.sort(tet[:,[a,b]],axis=1) for a,b in E])
edges,index=np.unique(arr,axis=0,return_inverse=True)
t10=np.column_stack((tet,index.reshape(6,nt).T+n))
assert n+len(edges)==46806
iface=faces[faces[:,4]==2349]
assert len(iface)==48
junc=defaultdict(list)
for ti,v in enumerate(original):
 for a,b,c,o in ((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3)):
  tri=tuple(sorted((int(v[a]),int(v[b]),int(v[c]))))
  junc[tri].append((ti,int(regions[ti]),int(tet[ti,o])))
assert all(len(junc[tuple(sorted(f[1:4]))])==2 and {x[1] for x in junc[tuple(sorted(f[1:4]))]}=={410,420} for f in iface)
REF=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
A=.025;B=.05;Q=1.;beta=.25;z0=5.7849
G=5.;K={410:1.,420:10.}
freq=math.pi/max(float(np.ptp(xyz[:,1])),.05)
ymin=float(np.min(xyz[:,1]))
def ge(x,r,nonlinear):
 v=np.empty_like(x)
 v[...,0]=2*A*(x[...,0]+.35)
 v[...,1]=2*A*x[...,1]
 if nonlinear:v[...,1]+=beta*freq*np.cos(freq*(x[...,1]-ymin))
 v[...,2]=2*B*(x[...,2]-z0)+Q/K[r]
 return v
def evaluate(ti,coeff,order,point):
 p=xyz[tet[ti]]
 J=np.column_stack((p[1]-p[0],p[2]-p[0],p[3]-p[0]))
 inv=np.linalg.inv(J)
 abc=inv@(point-p[0])
 bary=np.r_[1-abc.sum(),abc]
 gr=REF@inv
 if order==1:
  N=bary
  g=gr
  row=tet[ti]
 else:
  N=np.r_[bary*(2*bary-1),[4*bary[a]*bary[b] for a,b in E]]
  g=np.vstack(((4*bary-1)[:,None]*gr,np.array([4*(bary[a]*gr[b]+bary[b]*gr[a]) for a,b in E])))
  row=t10[ti]
 return float(coeff[row]@N),coeff[row]@g
# independent degree4 Gauss Duffy 64 points for P1, degree6 216 points for P2
x,w=np.polynomial.legendre.leggauss(6);x=(x+1)/2;w=w/2
lambda_samples=[];weights=[]
for i,u in enumerate(x):
 for j,v in enumerate(x):
  for k,q in enumerate(x):
   lambda_samples.append([(1-u)*(1-v)*(1-q),u,(1-u)*v,(1-u)*(1-v)*q])
   weights.append(6*(1-u)**2*(1-v)*w[i]*w[j]*w[k])
lambda_samples=np.array(lambda_samples);weights=np.array(weights)
assert abs(np.sum(weights)-1)<1e-13
records=[]
for nl in (False,True):
 for order in (1,2):
  label=f'P{order}_nonlinear{int(nl)}'
  f=R/(label+'_coefficients.npz')
  assert f.exists()
  coeff=np.load(f)['coefficient']
  assert len(coeff)==(6957 if order==1 else 46806)
  jumps=[];robin=[];bal=[];areas=[]
  for face in iface:
   key=tuple(sorted(int(v) for v in face[1:4]))
   p0,p1,p2=nodes[face[1:4]-1,1:4]
   a=.5*np.linalg.norm(np.cross(p1-p0,p2-p0))
   pt=(p0+p1+p2)/3
   sides={}
   for ti,r,op in junc[key]:
    val,gradient=evaluate(ti,coeff,order,pt)
    nvec=np.array([0.,0.,1.]) if r==410 else np.array([0.,0.,-1.])
    flux=K[r]*float(np.dot(gradient,nvec))
    sides[r]=(val,flux)
   jump=sides[410][0]-sides[420][0]
   jumps.append(jump)
   robin.append(sides[410][1]+G*jump)
   bal.append(sides[410][1]+sides[420][1])
   areas.append(a)
  jumps=np.asarray(jumps);robin=np.asarray(robin);bal=np.asarray(bal);areas=np.asarray(areas)
  def norm2(v):return float(np.sqrt(np.dot(areas,v*v)/areas.sum()))
  # 216 pt independent gradient volume integration (not original 4 pt)
  numerator=0.;denominator=0.
  for lo in range(0,nt,120):
   hi=min(nt,lo+120)
   p=xyz[tet[lo:hi]]
   J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
   vol=np.linalg.det(J)/6
   assert np.all(vol>0)
   gr=np.einsum('tji,aj->tai',np.linalg.inv(J),REF)
   localcoeff=coeff[(tet if order==1 else t10)[lo:hi]]
   rr=regions[lo:hi]
   for l,weight in zip(lambda_samples,weights):
    point=np.einsum('a,tai->ti',l,p)
    if order==1:gshape=gr
    else:
     vgr=(4*l-1)[None,:,None]*gr
     egr=np.stack([4*(l[a]*gr[:,b,:]+l[b]*gr[:,a,:]) for a,b in E],axis=1)
     gshape=np.concatenate((vgr,egr),axis=1)
    gnum=np.einsum('ti,tij->tj',localcoeff,gshape)
    exact=np.empty_like(point)
    exact[:,0]=2*A*(point[:,0]+.35)
    exact[:,1]=2*A*point[:,1]
    if nl:exact[:,1]+=beta*freq*np.cos(freq*(point[:,1]-ymin))
    exact[:,2]=2*B*(point[:,2]-z0)+Q/np.where(rr==410,K[410],K[420])
    numerator+=float(np.dot(vol,weight*np.sum((gnum-exact)**2,axis=1)))
    denominator+=float(np.dot(vol,weight*np.sum(exact*exact,axis=1)))
  report={
   'case':label,'order':order,'nonpolynomial':nl,
   'independent_mean_interface_jump':float(np.dot(areas,jumps)/areas.sum()),
   'independent_jump_RMS_abs_error':norm2(jumps+Q/G),
   'independent_robin_RMS_rel':norm2(robin)/Q,
   'independent_normal_flux_conservation_RMS_rel':norm2(bal)/Q,
   'independent_relative_H1':math.sqrt(numerator/denominator),
   'interface_triangles':len(iface),'interface_area_mm2':float(areas.sum()),
   'saved_solution_SHA256':hashlib.sha256(f.read_bytes()).hexdigest()}
  print('R316_INDEPENDENT',json.dumps(report),flush=True)
  records.append(report)
  main=json.loads((R/(label+'_result.json')).read_text())
  for k,k0 in [('independent_robin_RMS_rel','contact_Robin_condition_RMS_rel'),
               ('independent_normal_flux_conservation_RMS_rel','flux_balance_RMS_rel'),
               ('independent_relative_H1','H1_relative_error')]:
   ratio=abs(report[k]-main[k0])/max(abs(main[k0]),1e-30)
   if nl and order==2 and k=='independent_relative_H1':
    # High-degree sinusoidal H1 integrand is NOT degree-2; 216-point
    # independent quadrature supersedes original 4-point estimate.
    report['primary_quadrature_H1_relative_error']=main[k0]
    report['primary_quadrature_relative_disagreement']=ratio
    assert 0.05<ratio<0.5,('unexpected quadrature discrepancy',ratio)
   else:
    assert ratio<1e-5,(label,k,ratio)
  assert abs(report['independent_mean_interface_jump']+Q/G)<3e-7
assert records[1]['independent_robin_RMS_rel']<1e-6
assert records[3]['independent_robin_RMS_rel']<1e-6
assert records[3]['independent_normal_flux_conservation_RMS_rel']<1e-6
assert records[3]['independent_relative_H1']<records[2]['independent_relative_H1']/100
result={'status':'PASS independent 216pt H1 and real two-side interface face2349 Robin/flux and potential-jump audits',
 'source':'R3.9 registered CAD410/420 and R3.16 saved split P1/P2 coefficient arrays',
 'contact_geometry_modified':False,
 'mathematical_contact_G':G,'manufactured_jump':-Q/G,
 'cases':records,'total_seconds':round(time.monotonic()-tstart,2)}
(R/'independent_contact_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('R316_INDEPENDENT_FINAL',result['status'],flush=True)
