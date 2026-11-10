"""Conservative gas-port building blocks; no inferred physical face mapping.

Patch rectangles are local to a named physical face and in mm.  A gas link
may use each area only once, across all links.  Caller must independently map
both ports and justify the physical gap before using the operator in a model.
"""
import math
from .integrated_reference import Scenario,gas_transport

def _area(r):
 if len(r)!=4 or not all(math.isfinite(v) for v in r) or r[2]<=r[0] or r[3]<=r[1]:raise ValueError('invalid patch rectangle')
 return (r[2]-r[0])*(r[3]-r[1])
def _overlap(a,b):
 return max(0.,min(a[2],b[2])-max(a[0],b[0]))*max(0.,min(a[3],b[3])-max(a[1],b[1]))
def allocate(face_bounds,links):
 """Reject out-of-face, unequal endpoint areas, repeated patches, or self-links."""
 used={}
 for j,link in enumerate(links):
  if link['a']['port']==link['b']['port']:raise ValueError('self-link')
  aa=[]
  for endpoint in (link['a'],link['b']):
   name=endpoint['face'];patch=endpoint['rect'];A=_area(patch);bound=face_bounds[name]
   if abs(_overlap(patch,bound)-A)>1e-12:raise ValueError('patch outside owned face')
   for other in used.setdefault(name,[]):
    if _overlap(patch,other)>1e-12:raise ValueError('overlapping gas ownership')
   used[name].append(patch);aa.append(A)
  if not math.isclose(*aa,rel_tol=1e-12,abs_tol=1e-12):raise ValueError('pair footprint area mismatch')
  if not math.isfinite(link['gap_m']) or link['gap_m']<=0:raise ValueError('invalid gas gap')
 return used

def exchange(face_bounds,links,temps,pressure_pa):
 if not math.isfinite(pressure_pa) or not 0<=pressure_pa<=101325:raise ValueError('invalid pressure')
 allocate(face_bounds,links);out={k:0. for k in temps};details=[]
 for link in links:
  a,b=link['a']['port'],link['b']['port'];ta,tb=temps[a],temps[b]
  if not all(math.isfinite(x) and 180<=x<=390 for x in (ta,tb)):raise ValueError('temperature outside selected range')
  if pressure_pa==0:g=0.
  else:
   cfg=Scenario(gas='Kr',cavity_pressure_pa=pressure_pa,accommodation=.8)
   k,jump,_=gas_transport(cfg,(ta+tb)/2);g=k*_area(link['a']['rect'])*1e-6/(link['gap_m']+2*jump)
  q=g*(ta-tb);out[a]-=q;out[b]+=q;details.append({'conductance_W_K':g,'a_to_b_W':q})
 return {'heat_into_ports_W':out,'links':details}
