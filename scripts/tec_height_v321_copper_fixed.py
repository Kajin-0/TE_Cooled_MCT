"""Fixed V3.20 face temperatures: Cu thermal-contact-R scenario, no device solve."""
from pathlib import Path
import json,hashlib
from tecooledmct.height_coupling_v320 import ORIGINAL,CANDIDATE,read,copper_specs,copper_eval
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_robustness_20261110';reg=read(D/'copper_fixed_registration.json')
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==reg['producer_sha256'];rows=[]
for case,path in [('nominal',ORIGINAL),('custom_060',CANDIDATE)]:
 p=R/'data/tec_height_coupling_20261110'/case/'result.json';r=read(p);assert hashlib.sha256(p.read_bytes()).hexdigest()==reg['source_sha256'][case]
 spec=copper_specs(read(path));t={}
 for z in r['Cu_form_tab_electrothermal_result']['net_details'].values():
  for k,v in zip(z['face_tags'],z['plate_temperature_K']):
   if k in t:assert abs(t[k]-v)<1e-10
   t[k]=v
 for rr in reg['thermal_contact_Rarea_m2K_W']:
  x=copper_eval(spec,r['operating_current_A'],t,thermal_Rarea=rr)
  rows.append({'case':case,'thermal_contact_Rarea_m2K_W':rr,'stage_heat_W':x['heat_into_ceramic_by_stage_W'],'terminal_joule_W':x['total_electrical_power_W'],'sum_energy_residual_W':sum(x['heat_into_ceramic_by_stage_W'])-x['total_electrical_power_W']})
  assert abs(rows[-1]['sum_energy_residual_W'])<1e-11
out={'status':'FIXED FACE TEMPERATURE Cu multiport sensitivity only; NOT coupled device temperatures or uncertainty interval','cases':rows}
p=D/'copper_fixed_sensitivity.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
