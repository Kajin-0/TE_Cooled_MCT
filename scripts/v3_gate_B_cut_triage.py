#!/usr/bin/env python3
"""R3 original Gate B read-only signed current-cut triage, no PDE or field mutation."""
from pathlib import Path
import json,hashlib,collections
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'data/v3_interconnect_et_20261102/B/coarse_field/result.json'
fine=ROOT/'data/v3_interconnect_et_20261102/B/fine_field/result.json'
gate=ROOT/'data/v3_interconnect_et_20261102/B/gate_B.json'
source=ROOT/'data/v3_interconnect_et_20261102/registration.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads(old.read_text());b=json.loads(fine.read_text());g=json.loads(gate.read_text())
assert g['status']=='FAIL/STOP'
assert abs(b['worst_cut_relative_error']-g['worst_fine_cut_relative_error'])<1e-14
assert len(a['cuts'])==len(b['cuts'])==16
def key(row):
 if 'pair' in row:return ' → '.join(map(str,row['pair']))
 if 'terminal' in row:return 'terminal_'+str(row['terminal'])
 if 'interior' in row:return 'interior_'+str(row['interior'])
 raise ValueError('Unrecognized registered Gate B cut')
c={key(v):v for v in a['cuts']}
f={key(v):v for v in b['cuts']}
assert c.keys()==f.keys() and len(f)==16
ledger=[]
for key_,v in f.items():
 previous=c[key_]
 e0=float(previous['gate_error']);e1=float(v['gate_error'])
 raw=float(v.get('raw_relative_error',e1))
 nat=float(v.get('natural_relative_error',0.0))
 if 'pair' in v:assert abs(e1-max(raw,nat))<1e-9
 ledger.append({
  'cut':key_, 'coarse_error':e0, 'fine_error':e1,
  'fine_to_coarse_error_ratio':e1/e0 if e0 else None,
  'fine_gate_factor':e1/.001,
  'coarse_pass':e0<=.001,'fine_pass':e1<=.001,
  'error_decreased':e1<e0,
  'error_increased':e1>e0,
  'fine_raw_a_A':v.get('raw_a_A'), 'fine_raw_b_A':v.get('raw_b_A'),
  'fine_contact_or_natural_A':v.get('natural_A'),
  'fine_natural_relative_error':nat,
  'fine_raw_relative_error':raw,
  'fine_area_m2':v.get('area_m2')})
ledger.sort(key=lambda v:v['fine_error'],reverse=True)
fail=[x for x in ledger if not x['fine_pass']]
assert len(fail)>=1
assert abs(max(x['fine_error'] for x in ledger)-g['worst_fine_cut_relative_error'])<1e-14
assert b['tets']==28691 and a['tets']==10819
assert g['acceptance']['cuts_0p1pct'] is False
r={
 'status':'FAIL original Gate B; preserved coarse/fine current-cut triage; NO PDE',
 'test_scope':'Original V3 net88/lead9 internal coupon, not TEC full external pin1->pin9 circuit',
 'coarse_tetrahedra':a['tets'],'fine_tetrahedra':b['tets'],
 'fine_cut_count':len(ledger),
 'fine_raw_cut_failed_count':len(fail),
 'coarse_raw_cut_failed_count':sum(not x['coarse_pass'] for x in ledger),
 'fine_cut_pass_count':sum(x['fine_pass'] for x in ledger),
 'cut_error_improved_with_refinement_count':sum(x['error_decreased'] for x in ledger),
 'cut_error_worsened_with_refinement_count':sum(x['error_increased'] for x in ledger),
 'declared_original_max_current_cut_relative_error':.001,
 'fine_worst_error':g['worst_fine_cut_relative_error'],
 'worst_cut':ledger[0]['cut'],
 'worst_error_multiplier':ledger[0]['fine_gate_factor'],
 'ranked_cut_ledger':ledger,
 'fine_min_potential_V':b['minimum_voltage'],
 'fine_potential_boundedness':'FAIL',
 'original_gate_B':g['status'],
 'discrete_IV_loss_rel':b['loss_relative_error'],
 'resistance_refinement_rel':g['R_relative_refinement'],
 'contact_reaction_equals_raw_bulk_flux':'NOT ESTABLISHED',
 'numerical_cause_identified':'NO; interpolation, geometric resolution and constitutive assumptions remain confounded',
 'physical_contact_property_release':'NOT RUN',
 'source_field_mesh_unchanged':True,
 'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (old,fine,gate,source)},
 'recommended_next_gate':'Only after read-only field/cut attribution, preregister one flux-resolving method on frozen original coupon preserving its failure and 0.1% raw cut threshold; do not retrofit P2 manufactured result.'
}
out=ROOT/'data/v3_physical_blocker_closure_20261106/attempt01/gate_B_cut_triage.json'
assert not out.exists()
out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ('status','fine_cut_count','fine_raw_cut_failed_count',
     'fine_cut_pass_count','cut_error_improved_with_refinement_count',
     'cut_error_worsened_with_refinement_count','worst_cut','worst_error_multiplier')},indent=2))
for row in ledger[:7]:
 print(row['cut'], 'coarse=',round(100*row['coarse_error'],3),'fine=',round(100*row['fine_error'],3),
       'improved=',row['error_decreased'])
