"""Independent fan-integral and source visibility/port audit for saved die/window link."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_visibility_v327_20261111';M=Path('/var/tmp/mct_r3_header_3d_20261107')
def fan_area_centroid(p):
 base=np.array(p[0]);A=0.;mom=np.zeros(2)
 for i in range(1,len(p)-1):
  b=np.array(p[i]);c=np.array(p[i+1]);v=b-base;w=c-base;area=abs(v[0]*w[1]-v[1]*w[0])/2;A+=area;mom+=area*(base+b+c)/3
 return A,mom/A

def main():
 v=json.loads((D/'die_window_visibility.json').read_text());r=json.loads((R/'data/nominal_gas_coupler_20261110/source_bare_column_subset.json').read_text());design=json.loads((R/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text());by={b['name']:b for b in design['bodies']};z0=by['p_HgCdTe_photoconductor']['bbox_mm'][5];z1=by['window']['bbox_mm'][2];assert v['gap_mm']==z1-z0
 # Existing ceramic columns terminate at lower ceramic3 face; new path begins above die.
 assert max(x['z1_mm'] for x in r['patches']) < z0
 fs={};needed={}
 for p in v['patches']:
  for key in ('die','window'):needed[p[key]['triangle_id']]=p[key]['face_tag']
 with (M/'R38_430_domains.1.face').open() as f:
  next(f)
  for row in f:
   x=row.split()
   if len(x)==5 and int(x[0]) in needed:
    idx=int(x[0]);assert idx not in fs and int(x[4])==needed[idx];fs[idx]=tuple(map(int,x[1:4]))
 ids={j for t in fs.values() for j in t};nodes={}
 with (M/'R38_430_domains.1.node').open() as f:
  next(f)
  for row in f:
   x=row.split()
   if len(x)>=4 and x[0].isdigit() and int(x[0]) in ids:nodes[int(x[0])]=np.array(list(map(float,x[1:4])))
 blockers=[]
 for b in design['bodies']:
  if b['name'] in ('p_HgCdTe_photoconductor','window','cap_shell'):continue
  q=b['bbox_mm']
  if q[5]<=z0+1e-9 or q[2]>=z1-1e-9:continue
  blockers.append((b['name'],q))
 cap=by['cap_shell'];assert cap['inner_radius']>math.sqrt(.5)
 total=0.;max_a=0.;max_w=0.;max_centroid=0.
 for x in v['patches']:
  poly=x['polygon_xy_mm'];a,c=fan_area_centroid(poly);total+=a;max_a=max(max_a,abs(a-x['area_mm2']));max_centroid=max(max_centroid,float(np.max(abs(c-np.array(x['centroid_xy_mm'])))))
  q=np.asarray(poly);pb=(min(q[:,0]),min(q[:,1]),max(q[:,0]),max(q[:,1]));assert all(not (pb[0]<b[3]-1e-11 and pb[2]>b[0]+1e-11 and pb[1]<b[4]-1e-11 and pb[3]>b[1]+1e-11) for _,b in blockers)
  for key in ('die','window'):
   side=x[key];ns=fs[side['triangle_id']];assert list(ns)==side['node_ids'];xyz=np.array([nodes[n][:2] for n in ns]);w=np.array(side['p1_weights']);assert abs(sum(w)-1)<1e-12 and min(w)>-2e-8;max_w=max(max_w,float(np.max(abs(w@xyz-c))))
   # Every output polygon vertex lies in the original triangle, independently of centroid.
   A=np.vstack((xyz.T,np.ones(3)))
   for vtx in q:
    bary=np.linalg.solve(A,np.r_[vtx,1]);assert min(bary)>-2e-8
 assert abs(total-v['paired_area_mm2'])<1e-9 and max_a<1e-12 and max_w<1e-10 and max_centroid<1e-10
 g=v['screened_frozen_source_state']['Kr_alpha_results']['0.8'];hot=v['screened_frozen_source_state']['window_K_assumed'];cold=v['screened_frozen_source_state']['die_K'];q=g['k_W_mK']*total*1e-6*(hot-cold)/(v['gap_mm']*1e-3+2*g['temperature_jump_m']);assert abs(q-g['Q_hot_to_cold_W'])<1e-15
 out={'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS independent polygon fan/P1, all-solid bbox and vertical separation readback; gas remains conditional','patches':len(v['patches']),'total_area_mm2':total,'max_area_error_mm2':max_a,'max_centroid_error_mm':max_centroid,'max_p1_position_error_mm':max_w,'max_old_column_top_z_mm':max(x['z1_mm'] for x in r['patches']),'new_column_bottom_z_mm':z0,'all_solid_blockers_checked':len(blockers),'frozen_window_die_heat_W':q,'pair_global_W':q-q,'source_visibility_sha256':hashlib.sha256((D/'die_window_visibility.json').read_bytes()).hexdigest()};(D/'independent_readback.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
