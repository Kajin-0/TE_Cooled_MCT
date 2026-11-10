"""Conservative source-envelope clearances; no OCC interference certification."""
from pathlib import Path
import json,math,hashlib,itertools
from tecooledmct.tec_assembly_v3 import samples
R=Path(__file__).resolve().parents[1];P=R/'data/tec_height_060_cad_20261110';SRC=P/'source_candidate/design.json'
def audit(d):
 by={b['name']:b for b in d['bodies']};excluded={'VIGO_reference_header','cap_shell','cap_roof','window'}
 # Wire bounds originate from 2 um centerline sampling; conservative 5 um extra is retained for all bodies.
 rings=[]
 for b in d['bodies']:
  if b['name'] in excluded:continue
  q=b['bbox_mm'];r=max(math.hypot(x,y) for x in (q[0],q[3]) for y in (q[1],q[4]));rings.append((r+.005,b['name']))
 radial,name=max(rings);shell=by['cap_shell']['inner_radius'];assert shell-radial>0
 high=max((b['bbox_mm'][5]+.005,b['name']) for b in d['bodies'] if b['name'] not in excluded)
 roof=by['cap_roof']['base'][2];assert roof-high[0]>0
 # Distance from each wire centerline to each unrelated pin bounding box,
 # minus wire radius and half of sampling step. Box contains whole pin.
 rows=[]
 for wname,pin in [('TEC_lead1',1),('TEC_lead9',9),('lead1_insulation',1),('lead9_insulation',9),('detector_bond7',7),('detector_bond8',8)]:
  w=by[wname];ss=samples(w['parts'],.025)
  for n in range(1,10):
   if n==pin:continue
   q=by[f'pin{n}']['bbox_mm'];dist=min(math.sqrt(sum(max(q[i]-p[i],0,p[i]-q[i+3])**2 for i in range(3))) for p,t in ss)
   gap=dist-w['radius']-.0125;rows.append({'wire':wname,'unrelated_pin':n,'lower_bound_mm':gap})
 assert all(x['lower_bound_mm']>0 for x in rows)
 stages=[]
 for j in range(3):
  ll=[by[f'leg{l["index"]}_{l["polarity"]}']['boxes_mm'][0] for l in d['legs'] if l['stage']==j];gaps=[]
  for a,b in itertools.combinations(ll,2):
   gaps.append(math.hypot(max(a[0]-b[0]-b[3],b[0]-a[0]-a[3],0),max(a[1]-b[1]-b[4],b[1]-a[1]-a[4],0)))
  stages.append(min(gaps))
 assert all(abs(x-.18)<1e-8 for x in stages)
 return {'status':'PASS bounded radial/axial enclosure, unrelated pin-wire envelope and same-stage pellet spacing; no all-pair curved collision audit',
  'radial_shell_clearance_lower_bound_mm':shell-radial,'limiting_radial_bbox':name,'roof_clearance_lower_bound_mm':roof-high[0],'limiting_top_bbox':high[1],
  'unrelated_pin_wire_pair_count':len(rows),'min_unrelated_pin_wire_clearance_lower_bound_mm':min(r['lower_bound_mm'] for r in rows),
  'unrelated_pin_wire_pairs':rows,'min_interleg_gap_per_stage_mm':stages,
  'method':'full solids inside conservative bounding envelopes; centerline-to-pin-AABB bound uses 25um sampling minus 12.5um and wire radius; 5um outer bbox allowance; does not certify other body interactions'}
def main():
 d=json.loads(SRC.read_text());r=audit(d);r['design_sha256']=hashlib.sha256(SRC.read_bytes()).hexdigest();(P/'clearance_audit.json').write_text(json.dumps(r,indent=2)+'\n');print({k:v for k,v in r.items() if k!='unrelated_pin_wire_pairs'})
if __name__=='__main__':main()
