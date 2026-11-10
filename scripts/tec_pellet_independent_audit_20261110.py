#!/usr/bin/env python3
"""Independent saved-output arithmetic; no transport solver or material model call."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/tec_pellet_screen_20261110'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(case_id):
 reg=read(DATA/'registration.json');base=read(ROOT/reg['baseline_case']/'result.json');p=DATA/'cases'/case_id/'result.json';d=read(p)
 assert d['status']=='ACCEPTED FROZEN-PAD TRANSPORT ONLY' and not d['source_CAD_rebuilt'] and not d['detector_or_top_temperature_solved']
 original=base['source_individual_leg_flux_and_electric_results'];errors=[];stages=[]
 for mode in ('fixed_current','matched_power'):
  x=d[mode];I=x['current_A'];assert len(x['legs'])==88
  assert x['source_die_K_FIXED']==base['calculated_detector_temperature_K'] and x['source_top_ceramic_K_FIXED']==base['source_full_temperature_nodes_K']['stage2_cold']
  assert [z['source_leg_ID'] for z in x['legs']]==[z['source_leg_ID'] for z in original]
  for row,src in zip(x['legs'],original):
   assert (row['Th_K'],row['Tc_K'],row['material'])==(src['Th_K'],src['Tc_K'],src['material'])
   errors.append(row['Qh_W']-row['Qc_W']-I*row['V_V'])
  for i,s in enumerate(x['stage_budgets']):
   ls=[z for z in x['legs'] if z['stage']==i];assert len(ls)==[58,22,8][i]
   for key,target in [('Qh_W','qh_W'),('Qc_W','qc_W'),('V_V','V'),('joule_W','joule_W')]:assert abs(math.fsum(z[key] for z in ls)-s[target])<1e-11
   stages.append(s['qh_W']-s['qc_W']-I*s['V'])
  R=base['source_tec_power_leads']['total_R_ohm']+base['source_total_solder_and_contact_series_resistance_ohm']+base['Cu_form_tab_electrical_R_ohm']
  V=math.fsum(z['V_V'] for z in x['legs'])+I*R;assert abs(x['terminal_V']-V)<1e-11 and abs(x['electrical_power_W']-I*V)<1e-11
 assert max(map(abs,errors))<reg['leg_energy_gate_W'] and max(map(abs,stages))<reg['stage_energy_gate_W']
 assert abs(d['matched_power']['electrical_power_W']-reg['matched_power_reference_W'])<reg['root_power_abs_tolerance_W']
 out=dict(status='PASS independent frozen-boundary leg/stage/electrical conservation; full-system NOT SOLVED',case=case_id,result_sha256=sha(p),max_leg_energy_error_W=max(map(abs,errors)),max_stage_energy_error_W=max(map(abs,stages)),source_legs=88,states=2,global_package_energy='NOT MEASURED; frozen boundary cannot represent a coupled package',new_geometry='NOT BUILT')
 (p.parent/'independent_audit.json').write_text(json.dumps(out,indent=2)+'\n');return out
if __name__=='__main__':
 import sys
 print(json.dumps(audit(sys.argv[1])))
