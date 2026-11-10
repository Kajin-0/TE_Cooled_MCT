"""Registered scenario and conservation controls; no new coupled solves."""
from pathlib import Path
import hashlib,json
import pytest
from scripts.tec_height_v321_runner import SCENARIOS,transformed,source_hash
R=Path(__file__).resolve().parents[1]
def test_three_single_parameter_scenarios_are_paired():
 assert SCENARIOS=={'interstage_off':{'interstage_factor':0.,'outer_gap_m':.003,'extra_sink_K_W':0.},'outer_gap_1p5mm':{'interstage_factor':1.,'outer_gap_m':.0015,'extra_sink_K_W':0.},'sink_plus5':{'interstage_factor':1.,'outer_gap_m':.003,'extra_sink_K_W':5.}}
 for v in SCENARIOS.values():assert sum((v['interstage_factor']!=1.,v['outer_gap_m']!=.003,v['extra_sink_K_W']!=0.))==1

def test_derived_source_is_deterministic_and_controls_actual_solver():
 s=transformed();compile(s,'scenario-derived','exec');assert hashlib.sha256(s.encode()).hexdigest()==source_hash()
 assert "CONFIG['interstage_factor']*np.array" in s and "CONFIG['outer_gap_m']+2*jump" in s and "+CONFIG['extra_sink_K_W']" in s
 assert "gas_W=previous['internal_interstage_gas_heat_hot_to_cold_W']" in s
 assert 'for iteration in range(1,reg[\'outer_steps_cap\']+1)' in s and "'matched_power'" in s

def test_warm_start_archives_conserve_and_are_distinct_from_new_cases():
 for v in ('nominal','custom_060'):
  p=R/'data/tec_height_coupling_20261110'/v/'result.json';d=json.loads(p.read_text());a=json.loads((p.parent/'independent_audit.json').read_text())
  assert a['status'].startswith('PASS') and hashlib.sha256(p.read_bytes()).hexdigest()==a['result_sha256']
  assert d['electrical_power_W']==pytest.approx(.5956680349614825,abs=1e-8)
  assert max(abs(x['total_flux_mismatch_W']) for x in d['original_native_source_ceramic_pad_flux_by_face'])<5e-8
