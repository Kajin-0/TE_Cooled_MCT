"""Insert source-field subset into V3.20 residual bookkeeping without solving."""
from pathlib import Path
import hashlib,json
from tecooledmct.nominal_gas_v324 import nominal_residual_adjustment
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_coupler_20261110';oldp=R/'data/tec_height_coupling_20261110/nominal/result.json';old=json.loads(oldp.read_text());new=json.loads((D/'source_field_subset_exchange.json').read_text());q=new['summary']['0.8']['link_W'];a=nominal_residual_adjustment(old['internal_interstage_gas_heat_hot_to_cold_W'],old['cavity_gas_heat_into_three_ceramics_and_die_W'],q)
a.update(status='NOT EQUILIBRIUM: changed gas terms applied to archived original residual; all other gas faces adiabatic, no new solve',new_interstage_W=q,old_interstage_W=old['internal_interstage_gas_heat_hot_to_cold_W'],old_external_gas_W=old['cavity_gas_heat_into_three_ceramics_and_die_W'],source_result_sha256=hashlib.sha256(oldp.read_bytes()).hexdigest(),full_system_solves=0)
p=D/'source_residual_adapter.json';assert not p.exists();p.write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a,indent=2))
