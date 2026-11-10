"""One-shot source-CAD P2 coupon error gates and preservation checks (no PDE)."""
from pathlib import Path
import json,hashlib,math
ROOT=Path(__file__).resolve().parents[1]
O=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109'
R=ROOT/'reports/current'

def load(p):return json.loads(p.read_text())
def test_original_source_and_registration_sha():
    reg=load(O/'preregistration.json')
    for k,h in reg['accepted_source_sha256'].items():assert hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==h
    for k,h in reg['frozen_candidate_mesh_sha256'].items():assert hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==h
    assert hashlib.sha256((ROOT/'scripts/v3_14_native_net88_p2_h035.py').read_bytes()).hexdigest()==reg['candidate_producer_sha256']
    assert reg['n_attempts']==1 and reg['mesh_h_mm']==.035

def test_new_p2_stop_is_not_mislabelled_pass():
    d=load(O/'attempt01/P2_candidate_h035_result.json')
    assert d['status'].startswith('STOP') and d['original_P1_Gate_B'].startswith('FAIL/STOP')
    assert d['P2_raw_cuts_failing_count']==11 and len(d['P2_cuts'])==16
    assert d['P2_raw_cut_max_relative_error']>d['current_gate_limit']==.001
    assert d['P2_minimum_voltage_V']<-d['voltage_bound_tolerance_V']
    assert d['P2_IV_minus_losses_relative']<d['power_gate_limit']==.005
    assert d['solver']['true_reduced_relative_residual']<1e-8
    assert d['P2_geometry_linear_TET4_unchanged'] is False

def test_independent_field_readback_source_match():
    d=load(O/'attempt01/independent_readback.json')
    assert d['status'].startswith('PASS independently reconstructed')
    assert d['contact_triangles']==2178 and d['material_interfaces']==11
    assert d['max_reconstruction_disagreement_rel']<2e-11
    assert d['original_gate_B']=='FAIL/STOP'
    src={'P2_saved_field':'attempt01/P2_candidate_h035_field.npz','P2_result':'attempt01/P2_candidate_h035_result.json','fine_mesh':'fine35/mesh.npz','fine_registry':'fine35/registry.json'}
    for k,n in src.items():assert hashlib.sha256((O/n).read_bytes()).hexdigest()==d['source_file_SHA256'][k]

def test_comparison_all_sixteen_and_untuned_current_gate():
    d=load(O/'refinement_comparison.json')
    assert d['result'].startswith('FAIL/STOP')
    assert d['original_failing_cuts']==d['new_failing_cuts']==11
    assert d['strictly_improved_cut_count']==9 and d['strictly_worsened_cut_count']==7
    assert math.isclose(d['new_worst_cut_error_pct'],7.019320630430186,rel_tol=1e-10)
    assert math.isclose(d['original_worst_cut_error_pct'],8.0993023932639,rel_tol=1e-10)
    assert d['current_cut_acceptance_pct']==.1
    assert d['new_worst_over_limit_factor']>70
    assert d['new_thermal_FEM_solves']==d['new_spatial_Joule_FEM_solves']==0
    assert len(d['cutwise_results'])==16
    for name,h in d['input_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
    for name,h in d['figure_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h

def test_reader_first_report_and_prior_archives_preserved():
    s=(R/'reader_first_report.tex').read_text()
    assert s.count('\\input{v314_p2_resolution_section.tex}')==1
    assert s.count('\\appendix')==1
    assert (R/'TEC_TO_Reader_First_Assessment_20261109_V314.pdf').is_file()
    assert (R/'TEC_TO_Reader_First_Assessment_20261109_V313.pdf').is_file()
    assert 'Gate B remains' in (R/'v314_p2_resolution_section.tex').read_text()
