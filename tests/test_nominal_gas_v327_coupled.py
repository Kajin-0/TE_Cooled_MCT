from pathlib import Path
import hashlib,json
import numpy as np
import pytest
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_visibility_v327_20261111';C=D/'coupled_attempt01'
def test_one_saved_coupled_original_and_independent_balances():
 r=json.loads((C/'result.json').read_text());a=json.loads((C/'independent_audit.json').read_text());p=json.loads((C/'ports_crosscheck.json').read_text());n=json.loads((D/'node_label_audit.json').read_text());h=hashlib.sha256((C/'result.json').read_bytes()).hexdigest();assert a['source_result_sha256']==p['source_result_sha256']==n['source_result_sha256']==h
 assert r['variant']=='nominal' and len(r['source_individual_leg_flux_and_electric_results'])==88 and r['outer_iterations']==14
 assert a['die_window_gas_W']==pytest.approx(.00011283289006326198,abs=1e-13) and a['die_window_pair_balance_W']==0
 assert all(x==0 for x in r['cavity_gas_heat_into_three_ceramics_and_die_W'][:3]);assert abs(a['max_stage_residual_W'])<1e-8 and abs(a['global_residual_W'])<1e-8 and abs(a['power_residual_W'])<1e-8
 assert r['max_last_spatial_temperature_update_K']<1e-6 and r['Cu_form_tab_electrothermal_result']['net_details']['88']['contact_electrical_R_ohm'][1]==0
 assert r['source_full_temperature_nodes_K']['carrier']==a['top_K'] and a['top_K']!=r['source_full_temperature_nodes_K']['stage2_cold']
 f=np.load(C/'ceramic_fields.npz');assert abs(sum(float(f[f'ceramic{i}_gas_nodal_load_W'].sum()) for i in range(4)))<1e-12
