"""Independent invariants, geometric limits and saved nonlinear diagnostics."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest

from tecooledmct.tec_identifiability import (ROOT,design,invariant_factors,native_geometry_audit,
    rectangle_union_area,scenario_geometry,independent_controls,NULL)
from tecooledmct.integrated_reference import geometry
from tecooledmct.tec_material_plausibility import read,sha

DATA=ROOT/'data/tec_identifiability_20261101'


def assert_registered_design(frozen,reconstructed):
    reconstructed=deepcopy(reconstructed)
    assert len(frozen['cases'])==len(reconstructed['cases'])==269
    for old,new in zip(frozen['cases'],reconstructed['cases']):
        if old['uses']!=['jacobian']:continue
        # NumPy exp(.0025) differs by one binary64 ULP across the pinned and
        # CI environments. Only FD factor reconstruction permits that one ULP;
        # IDs, grouping, steps, operating conditions and all other cases stay exact.
        for name in ('a','r','k','s'):
            if old[name]==1.:continue
            assert abs(old[name]-new[name])<=np.spacing(old[name])
            new[name]=old[name]  # In-memory comparison only, never archived data.
    assert reconstructed==frozen


def test_registration_comparison_allows_one_exp_ulp_but_rejects_changed_design():
    frozen=read(DATA/'registration.json')['design'];other=deepcopy(frozen)
    point=next(c for c in other['cases'] if c['uses']==['jacobian'] and c['a']>1)
    point['a']=np.nextafter(point['a'],np.inf)
    assert_registered_design(frozen,other)
    point['a']=np.nextafter(point['a'],np.inf)
    with pytest.raises(AssertionError):assert_registered_design(frozen,other)
    other=deepcopy(frozen);other['cases'][0]['current_A']+=1e-12
    with pytest.raises(AssertionError):assert_registered_design(frozen,other)
    other=deepcopy(frozen);other['cases'][0]['counts']=[26,12,6]
    with pytest.raises(AssertionError):assert_registered_design(frozen,other)


@pytest.mark.parametrize('name',['a','l','r','k','s'])
@pytest.mark.parametrize('bad',[0.,-1.,np.nan])
def test_nonfinite_or_nonpassive_factors_reject(name,bad):
    with pytest.raises(ValueError):invariant_factors(**{name:bad})


def test_independent_invariant_algebra_and_seebeck_distinction():
    base=invariant_factors(a=1.3,l=.9,r=.8,k=1.1,s=.94)
    gauge=invariant_factors(a=1.3*1.7,l=.9,r=.8*1.7,k=1.1/1.7,s=.94)
    for key in ('R','K','RK','ZT'):assert gauge[key]==pytest.approx(base[key],rel=1e-14)
    assert invariant_factors(a=1.7)['RK']==1
    assert invariant_factors(a=1.7)['ZT']==1
    assert invariant_factors(r=.6,k=1.73,s=.89)['ZT']<.8
    assert invariant_factors(a=1.7)['intrinsic_PF']==1


def test_analytic_geometry_and_reverse_current_controls():
    assert independent_controls(geometry())['passed']
    # Independent union-area analytic controls with overlapping rectangles.
    assert rectangle_union_area([(0,0,2,1),(1,0,3,1)])==3
    assert rectangle_union_area([(0,0,2,2),(1,1,3,3)])==7
    assert rectangle_union_area([])==0


def test_native_coverage_and_scenario_copy_do_not_claim_new_cad():
    base=geometry();before=deepcopy(base);c=design()['cases'][0];c=dict(c,a=1.7,l=1.)
    _,g=scenario_geometry(c,base)
    assert base==before and g['stages'][0]['leg_area_m2']==pytest.approx(base['stages'][0]['leg_area_m2']*1.7)
    assert native_geometry_audit()['admissible_on_frozen_native_pads']
    grow=native_geometry_audit(1.7,1.)
    assert grow['native_full_Cu_footprint_failures']==176
    assert grow['minimum_footprint_coverage']==pytest.approx(1/1.7)
    assert grow['minimum_interleg_gap_m']>0 and not grow['admissible_on_frozen_native_pads']
    shorten=native_geometry_audit(1.,1/1.7)
    assert not shorten['axial_mating_preserved'] and not shorten['within_candidate_height_tolerance']


def test_registered_scenarios_frozen_and_no_fitted_triple_added():
    reg=read(DATA/'registration.json')
    assert_registered_design(reg['design'],design())
    assert reg['study_code_sha256']==sha(DATA/'executed_study.py.source')
    assert reg['protocol']==(ROOT/'docs/TEC_GEOMETRY_MATERIAL_IDENTIFIABILITY_20261101.md').read_text().split('## Results')[0]
    for c in reg['design']['cases']:
        assert (c['s'],c['r'],c['k']) not in ((.89,.60,1.73),(.892,.603,1.731))
    for p,h in reg['input_sha256'].items():assert sha(ROOT/p)==h
    recovery=read(DATA/'analysis_recovery.json')
    assert recovery['cases_sha256_before']==recovery['cases_sha256_after']==sha(DATA/'cases.json')


def test_saved_nonlinear_budgets_nulls_and_unstable_raw_rank_are_honest():
    a=read(DATA/'analysis.json');cases=read(DATA/'cases.json')
    assert a['coverage']=={'accepted':260,'rejected':9,'not_run':0,'measured_domain':71,'assumed_continuation':189}
    assert sum(p['status']=='PASS' for p in a['pairs'])==35
    assert not any(p['status']=='FAIL' for p in a['pairs'])
    for p in a['pairs']:
        if p['status']=='PASS':assert p['max_temperature_difference_K']<1e-6 and p['voltage_difference_V']<1e-7
    for r in cases.values():
        if r['status']=='ACCEPTED':
            x=r['result'];assert abs(x['global_energy_residual_w'])<1e-8
            assert x['max_node_balance_residual_w']<1e-8
            assert all(abs(s['energy_residual_w'])<1e-9 for s in x['stage_budget'])
        else:assert r['diagnostics'] and not r['diagnostics']['candidate_is_accepted']
    for hot,obj in a['jacobians'].items():
        assert obj['finite_difference_stability_passed']
        for step,b in obj['steps'].items():
            matrix=np.array(b['chain_rule_constrained']['matrix'])
            assert np.linalg.norm(matrix@NULL)<1e-12
            assert b['chain_rule_constrained']['rank_relative_1e_5']==3
            assert all(r==2 for r in b['single_condition_ranks'])
    primary=a['jacobians']['300.15']['steps']
    assert primary['0.005']['raw']['rank_relative_1e_5']==4  # Retain finite-difference artifact.
    assert primary['0.0025']['raw']['rank_relative_1e_5']==3


def test_external_contacts_and_unmatched_source_controls():
    a=read(DATA/'analysis.json')
    assert a['higher_Thot_panel']['status']=='NOT COMPARABLE'
    assert any('no exact digitized' in r['status'] for r in a['oem_rows'])
    for r in a['external_contact_limits']:
        assert r['extra_hot_reservoir_rejection_W']==pytest.approx(r['extra_work_W'])
        assert r['extra_hot_reservoir_rejection_W']>=0 and r['thermal_contact_entropy_W_K']>=0
    rows=[r for r in a['oem_rows'] if r['factor']==1.7 and r['I']==.2 and r['Q']==0 and r['status']=='CONDITIONAL']
    assert len(rows)==2 and all(r['difference']>0 for r in rows)  # Overcool and overvolt, not agreement.
    assert all(r['assumed_continuation'] for r in rows)
    assert max(r['Tc_error_K'] for r in a['baseline_replays'])<1e-6
