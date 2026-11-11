"""Conservative planar open-column geometry; mm. Not a molecular ray solver."""
import math
from .nominal_gas_p1_v325 import clip,centroid_area

def overlap(a,b,tol=1e-12):
 return a[0]<b[2]-tol and a[2]>b[0]+tol and a[1]<b[3]-tol and a[3]>b[1]+tol

def open_rectangles(bounds,blocks,tol=1e-10):
 """Disjoint rectangular subset of bounds outside every closed blocker bbox."""
 if len(bounds)!=4 or not all(math.isfinite(float(x)) for x in bounds) or bounds[0]>=bounds[2] or bounds[1]>=bounds[3]:raise ValueError('invalid bounds')
 valid=[]
 for b in blocks:
  if len(b)!=4 or not all(math.isfinite(float(x)) for x in b) or b[0]>b[2] or b[1]>b[3]:raise ValueError('invalid blocker')
  q=(max(bounds[0],b[0]),max(bounds[1],b[1]),min(bounds[2],b[2]),min(bounds[3],b[3]))
  if q[0]<q[2] and q[1]<q[3]:valid.append(q)
 xs=sorted({bounds[0],bounds[2]}|{v for b in valid for v in (b[0],b[2])});ys=sorted({bounds[1],bounds[3]}|{v for b in valid for v in (b[1],b[3])});out=[]
 for x,X in zip(xs,xs[1:]):
  for y,Y in zip(ys,ys[1:]):
   q=(x,y,X,Y)
   if X-x>tol and Y-y>tol and not any(overlap(q,b,tol) for b in valid):out.append(q)
 return out

def rectangle_poly(r):return [(r[0],r[1]),(r[2],r[1]),(r[2],r[3]),(r[0],r[3])]
def intersection(*polys):
 if not polys:return (0.,None,[])
 p=polys[0]
 for q in polys[1:]:p=clip(p,q)
 a,c=centroid_area(p)
 return a,c,p

def die_window_exchange(window_K,die_K,area_mm2,gap_m,pressure_Pa,alpha):
 """Gas heat from window to die; equal, opposite reservoir load returned."""
 from .nominal_gas_v324 import flux
 v=flux(window_K,die_K,area_mm2,gap_m,pressure_Pa,alpha);q=v['Q_hot_to_cold_W']
 if window_K<=0 or die_K<=0 or q*(window_K-die_K)<-1e-18:raise ValueError('nonpassive exchange')
 return {'die_load_W':q,'window_load_W':-q,'conductance_W_K':v['G_W_K']}
