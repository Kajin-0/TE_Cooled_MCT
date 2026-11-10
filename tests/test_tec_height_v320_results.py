"""Saved independent audits, actual field identity and matched power; no new solves."""
from pathlib import Path
import hashlib,json
import numpy as np
import pytest
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_coupling_20261110'
def test_two_matched_cases_have_independent_energy_and_saved_fields():
 s=json.loads((D/'summary.json').read_text());assert s['full_system_solves']==s['independent_audits']==2
 assert s['candidate_minus_nominal_die_K']==pytest.approx(-3.705321165257402,abs=1e-9)
 for row in s['cases']:
  p=D/row['case'];r=json.loads((p/'result.json').read_text());a=json.loads((p/'independent_audit.json').read_text());g=json.loads((p/'gas_crosscheck.json').read_text())
  port=json.loads((p/'ports_crosscheck.json').read_text())
  digest=hashlib.sha256((p/'result.json').read_bytes()).hexdigest();assert digest==a['result_sha256']==g['source_result_sha256']==port['source_result_sha256']
  assert port['status'].startswith('PASS') and max(x['max_foil_node_energy_error_W'] for x in port['copper'])<1e-12
  assert a['status'].startswith('PASS') and g['status'].startswith('PASS')
  assert r['operating_current_A']*r['terminal_voltage_V']==pytest.approx(.5956680349614825,abs=1e-8)
  assert max(abs(v) for v in a['stage_boundary_residual_W'])<1e-7 and abs(a['global_energy_residual_W'])<1e-7
  assert len(r['source_individual_leg_flux_and_electric_results'])==88
  assert all(180<=x['leg_min_K']<=x['leg_max_K']<=390 for x in r['source_individual_leg_flux_and_electric_results'])
  with np.load(p/'ceramic_fields.npz',allow_pickle=False) as f:
   for j in range(4):
    k=f'ceramic{j}';assert f[k+'_xyz_mm'].shape==(len(f[k+'_temperature_K']),3)
 assert 'unqualified' in s['status'].lower()
