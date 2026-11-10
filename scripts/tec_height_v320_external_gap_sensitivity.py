"""Fixed archived state: sensitivity of existing external 3-mm gas proxy only."""
from pathlib import Path
import json
from tecooledmct.integrated_reference import Scenario,gas_transport
from tecooledmct.height_coupling_v320 import read
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_coupling_20261110';b=read(R/'data/v3_11_rev3_backfill_source_20261109/Kr100_I040/result.json');n=b['source_full_temperature_nodes_K'];T=[n[x] for x in ('stage0_cold','stage1_cold','stage2_cold','die')];A=b['source_exposed_effective_surface_area_m2'];cfg=Scenario(gas='Kr',cavity_pressure_pa=100.,accommodation=.8);rows=[]
for gap in (.0015,.003,.006):
 q=[]
 for area,t in zip(A,T):
  k,j,_=gas_transport(cfg,(300+t)/2);q.append(float(k*area/(gap+2*j)*(300-t)))
 rows.append({'external_gap_m':gap,'total_gas_W':sum(q),'gas_by_surface_W':q})
o={'status':'FIXED ARCHIVED TEMPERATURES ONLY; not a coupled uncertainty interval','gaps':rows,'note':'External reservoir proxy only; not interstage gas and not a measured physical cavity.'}
p=D/'external_gap_fixed_field_sensitivity.json';assert not p.exists();p.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o))
