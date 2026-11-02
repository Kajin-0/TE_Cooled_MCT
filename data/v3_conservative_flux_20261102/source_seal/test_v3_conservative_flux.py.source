"""Saved experiment and fail-closed guards; no new physical run in regression."""
import hashlib,json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/v3_conservative_flux_20261102'

def test_prospectively_sealed_source_inputs_and_original_fields():
    r=json.loads((BASE/'registration.json').read_text())
    for p,h in r['sealed_files'].items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p

def test_original_failed_gate_is_not_reclassified_by_recovery():
    r=json.loads((BASE/'original_reproduction.json').read_text())
    assert r['old_gate_unchanged']['status']=='FAIL/STOP'
    assert abs(r['R_relative_refinement']-.00315802858265)<1e-10
    assert r['fine_minimum_V']<-1e-8
    assert r['fine_total_volume_relative_error']<-.016

def test_normal_continuity_is_not_the_registered_accuracy_gate():
    r=json.loads((BASE/'registration.json').read_text())
    assert r['uniform_flux_relative_limit']==1e-7
    assert r['harmonic_flux_L2_limit']==.05
    assert r['required_harmonic_error_reduction']==1.5
    assert r['thermal_C']=='NOT AUTHORIZED' and r['coupled_D']=='NOT AUTHORIZED'

def test_all_saved_control_claims_are_numeric_not_conservation_only():
    records=json.loads((BASE/'controls/cases.json').read_text())
    for row in records:
        assert set(row['methods'])=={'P1_raw','mixed','recovered'}
        assert all('relative_flux_L2_error' in q for q in row['methods'].values())
    gate=json.loads((BASE/'controls/gate.json').read_text())
    if gate['status']!='PASS':
        assert not (BASE/'geometry/L1_field').exists()

def test_no_downstream_thermal_or_new_material_fit_outputs():
    assert not any((BASE/name).exists() for name in ('C','D','thermal','fit'))
