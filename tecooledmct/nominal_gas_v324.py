"""Original-cavity bare-face column subset and conservative two-port gas law.

Solid bounding boxes over-exclude gas. Non-colliding columns are geometric
subsets, not validated 3D transport channels or bounds on physical heat flow.
"""
import math
from .integrated_reference import Scenario,gas_transport
TOL=1e-9

def cut(a,b):
 x,y=max(a[0],b[0]),max(a[1],b[1]);u,v=min(a[2],b[2]),min(a[3],b[3]);return (x,y,u,v) if u-x>TOL and v-y>TOL else None

def columns(design,stage):
 if stage not in (0,1,2):raise ValueError('stage')
 bodies=design['bodies'];by={b['name']:b for b in bodies};lo=by[f'ceramic{stage}']['boxes_mm'][0];hi=by[f'ceramic{stage+1}']['boxes_mm'][0];z0=lo[2]+lo[5];z1=hi[2];assert z1>z0
 face=(hi[0],hi[1],hi[0]+hi[3],hi[1]+hi[4]);ex=[];annulus=[]
 for b in bodies:
  if b['name'] in (f'ceramic{stage}',f'ceramic{stage+1}'):continue
  if b['shape']=='annulus' and b['name']=='cap_shell':
   maxr=max(math.hypot(x-b['base'][0],y-b['base'][1]) for x in (face[0],face[2]) for y in (face[1],face[3]));assert maxr<b['inner_radius'];annulus.append(b['name']);continue
  boxes=b.get('boxes_mm') if b['shape']=='boxes' else None
  if boxes is None:
   q=b['bbox_mm'];boxes=[[q[0],q[1],q[2],q[3]-q[0],q[4]-q[1],q[5]-q[2]]]
  for q in boxes:
   if q[2]+q[5]<=z0+TOL or q[2]>=z1-TOL:continue
   c=cut(face,(q[0],q[1],q[0]+q[3],q[1]+q[4]))
   if c:ex.append((b['name'],c))
 xs=sorted({face[0],face[2]}|{x for _,q in ex for x in (q[0],q[2])});ys=sorted({face[1],face[3]}|{x for _,q in ex for x in (q[1],q[3])});cells=[]
 for x,X in zip(xs,xs[1:]):
  if X-x<=TOL:continue
  for y,Y in zip(ys,ys[1:]):
   if Y-y<=TOL:continue
   a,b=(x+X)/2,(y+Y)/2
   if not any(q[0]<a<q[2] and q[1]<b<q[3] for _,q in ex):cells.append([x,y,X,Y])
 area=math.fsum((r[2]-r[0])*(r[3]-r[1]) for r in cells);total=(face[2]-face[0])*(face[3]-face[1]);assert 0<area<=total
 return {'stage':stage,'z0_mm':z0,'z1_mm':z1,'gap_m':(z1-z0)*1e-3,'domain_xy_mm':list(face),'unobstructed_column_area_mm2':area,'excluded_projection_area_mm2':total-area,'cells_xy_mm':cells,'blocker_names':sorted({n for n,_ in ex}),'cap_annulus_certified_outside':annulus,'method':'axis-aligned source-solid boxes and conservative curved-body bounding boxes; unblocked vertical prisms; no transport bound'}

def flux(Th,Tc,area_mm2,gap_m,p,accommodation):
 if not all(math.isfinite(z) for z in (Th,Tc,area_mm2,gap_m,p,accommodation)) or area_mm2<0 or gap_m<=0 or p<0 or not 0<accommodation<=1:raise ValueError('invalid gas state')
 if p==0 or area_mm2==0:return {'G_W_K':0.,'Q_hot_to_cold_W':0.}
 k,jump,below=gas_transport(Scenario(gas='Kr',cavity_pressure_pa=p,accommodation=accommodation),.5*(Th+Tc));g=k*area_mm2*1e-6/(gap_m+2*jump)
 return {'G_W_K':g,'Q_hot_to_cold_W':g*(Th-Tc),'k_W_mK':k,'temperature_jump_m':jump,'below_source_assumption':below}

def stage_loads(y,patches,p,accommodation):
 """Return four equal-and-opposite stage loads; source-temperature callback is caller's duty."""
 out=[0.]*4;details=[]
 for j,a in enumerate(patches):
  v=flux(y[j][0],y[j][1],a['unobstructed_column_area_mm2'],a['gap_m'],p,accommodation);q=v['Q_hot_to_cold_W'];out[j]-=q;out[j+1]+=q;details.append(v)
 assert abs(sum(out))<1e-15
 return out,details

def nominal_residual_adjustment(old_internal,old_external,new_internal):
 """Adapt V3.20 gas residual terms: subset only, other gas surfaces adiabatic.

Returns changes to the four original stage/die energy residuals and bath heat;
not an equilibrium solution, and radiation is intentionally unchanged.
"""
 if len(old_internal)!=3 or len(new_internal)!=3 or len(old_external)!=4:raise ValueError('expected three interstage and four exterior terms')
 if not all(math.isfinite(float(v)) for a in (old_internal,old_external,new_internal) for v in a):raise ValueError('nonfinite heat')
 d=[old_internal[i]-new_internal[i] for i in range(3)]
 return {'stage_die_residual_delta_W':[old_external[0]+d[0]-d[1],old_external[1]+d[1]-d[2],old_external[2]+d[2],old_external[3]],'bath_rejection_delta_W':d[0],'omitted_external_gas_W':sum(old_external)}
