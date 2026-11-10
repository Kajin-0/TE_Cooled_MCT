"""V3.13 source identity, physical network and preserved stop gates."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/v3_13_native_foil_port_readiness_20261109/port_readiness.json'

def get():return json.loads(P.read_text())

def test_original_source_hash_and_3d_gates_unchanged():
    q=get()
    for f,h in q['source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
    g=q['3D_electrical_gates']
    assert g['P1_original_gate']=='FAIL/STOP' and g['P2_raw_cuts_failed']==11
    assert g['P2_raw_current_cut_relative']>g['cut_release_threshold_relative']
    assert g['P2_voltage_min_V']< -g['P2_voltage_bound_tolerance_V']
    assert g['thermal_C_gate'].startswith('NOT RUN') and g['Joule_coupled_D_gate'].startswith('NOT RUN')

def test_3port_matrix_null_energy_symmetry():
    q=get();G=q['thermal_G_positive_heat_into_foil_W_K'];assert len(G)==3 and all(len(row)==3 for row in G)
    assert max(abs(G[i][j]-G[j][i]) for i in range(3) for j in range(3))<1e-12
    assert max(abs(sum(row)) for row in G)<1e-12
    assert max(abs(sum(G[i][j] for i in range(3))) for j in range(3))<1e-12
    # All principal minors of a real symmetric 3x3 PSD matrix are nonnegative.
    assert all(G[i][i]>0 for i in range(3))
    assert all(G[i][i]*G[j][j]-G[i][j]**2>-1e-12 for i in range(3) for j in range(i+1,3))
    assert min(q['thermal_G_eigenvalues_W_K'])>=-1e-12
    T=q['foil_ports_temperature_K'];qh=q['heat_into_ceramic_at_I040_W'];qj=q['Joule_port_allocation_current_reduced_W']
    assert max(abs(qh[i]+sum(G[i][j]*T[j] for j in range(3))-qj[i]) for i in range(3))<1e-11
    assert abs(sum(qh)-sum(qj))<1e-11

def test_deadend_thermal_contact_remains_and_electrical_error_prospective_only():
    q=get();x=q['electrical_dead_end_midfoot']
    assert x['CAD_foot']=='tab_joint5' and x['source_alloy']=='SnBi57_43'
    assert x['P2_expected_current_fraction']==0
    assert math.isclose(x['middle_contact_series_R_mistaken_if_assumed_through_current_ohm'],1e-11/6e-8,rel_tol=1e-12)
    assert math.isclose(x['middle_contact_Joule_overcount_if_no_branch_current_at_0p4A_W'],.4**2*1e-11/6e-8,rel_tol=1e-12)
    assert q['foil_ports_CAD_tags']==[36,74,104]
    assert q['new_FEM_solves']==0
