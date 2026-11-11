"""Convex P1 surface overlap and conservative gas exchange, coordinates in mm."""
import math
import numpy as np
from .nominal_gas_v324 import flux
EPS=1e-12

def signed_area(poly):
 if len(poly)<3:return 0.
 origin=poly[0];p=[(z[0]-origin[0],z[1]-origin[1]) for z in poly]
 return .5*sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))
def ccw(poly):
 p=[tuple(map(float,z)) for z in poly];return p if signed_area(p)>=0 else p[::-1]
def clip(subject,clipper):
 """Sutherland–Hodgman intersection with a convex, CCW clip polygon."""
 out=ccw(subject);c=ccw(clipper)
 for a,b in zip(c,c[1:]+c[:1]):
  if not out:break
  old=out;out=[]
  def side(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
  previous=old[-1];sp=side(previous)
  for current in old:
   sc=side(current);inp=sp>=-EPS;inc=sc>=-EPS
   if inp!=inc:
    den=sp-sc
    if abs(den)>1e-30:
     t=sp/den;out.append((previous[0]+t*(current[0]-previous[0]),previous[1]+t*(current[1]-previous[1])))
   if inc:out.append(current)
   previous,sp=current,sc
 return out

def centroid_area(poly):
 if len(poly)<3:return 0.,(0.,0.)
 # Translate first to avoid catastrophic cancellation for tiny cells at mm-scale coordinates.
 ox,oy=poly[0];p=[(z[0]-ox,z[1]-oy) for z in poly]
 cross=[a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])];A=sum(cross)/2
 if abs(A)<1e-14:return 0.,(0.,0.)
 cx=sum((a[0]+b[0])*c for a,b,c in zip(p,p[1:]+p[:1],cross))/(6*A);cy=sum((a[1]+b[1])*c for a,b,c in zip(p,p[1:]+p[:1],cross))/(6*A)
 return abs(A),(ox+cx,oy+cy)

def weights(tri,xy):
 a,b,c=np.asarray(tri,float);M=np.column_stack((b-a,c-a));u,v=np.linalg.solve(M,np.asarray(xy)-a);w=np.array([1-u-v,u,v]);
 if min(w)<-2e-8 or max(w)>1+2e-8:raise ValueError(('point outside triangle',w,xy))
 return w

def exchange(pairs,node_temperatures,p=100.,alpha=.8):
 """Each overlap uses a common centroid: P1 integrals exact, nonlinear flux midpoint quadrature."""
 loads={};details=[];by_stage=np.zeros(3);entropy=0.
 for x in pairs:
  hot=x['hot'];cold=x['cold'];Th=sum(node_temperatures[n]*w for n,w in zip(hot['node_ids'],hot['weights']));Tc=sum(node_temperatures[n]*w for n,w in zip(cold['node_ids'],cold['weights']));q=flux(Th,Tc,x['area_mm2'],x['gap_m'],p,alpha)['Q_hot_to_cold_W']
  for side,sign in ((hot,-1),(cold,1)):
   for node,w in zip(side['node_ids'],side['weights']):loads[node]=loads.get(node,0.)+sign*q*w
  by_stage[x['stage']]+=q;entropy+=q*(1/Tc-1/Th);details.append(float(q))
 if abs(sum(loads.values()))>1e-12 or entropy < -1e-14:raise ValueError('gas conservation/passivity failure')
 return {'node_load_W':loads,'pair_heat_hot_to_cold_W':details,'stage_heat_hot_to_cold_W':by_stage.tolist(),'global_heat_W':float(sum(loads.values())),'entropy_generation_W_K':float(entropy)}
