"""Independent checks of analog-grade thermoelectric energy identities."""
from dataclasses import replace
import json
import numpy as np
import pytest
from tecooledmct import graded_tec
from tecooledmct.integrated_reference import (
    Scenario, coefficients, geometry, solve, stage_thermoelectric, run,
)
from tecooledmct.material_profiles import synthetic_profile


@pytest.mark.parametrize('current,hot,cold',[(0.,300.,250.),(.1,300.,250.),(.4,280.,220.),(.2,250.,250.)])
def test_constant_transport_exact_reduction(monkeypatch,current,hot,cold):
    monkeypatch.setattr(graded_tec,'source',lambda:synthetic_profile(False))
    g=geometry()
    s=Scenario(current_a=current)
    for geom,c in zip(g['stages'],coefficients(s,g)):
        variable=graded_tec.stage(geom,hot,cold,current)
        constant=stage_thermoelectric(c,hot,cold,current)
        for name in ('qc_w','qh_w','voltage_v','conduction_w','joule_w'):
            assert variable[name]==pytest.approx(constant[name],rel=1e-11,abs=1e-13),name
        assert abs(variable['energy_residual_w'])<1e-12


def test_real_analog_source_and_explicit_high_temp_extension():
    evidence=graded_tec.source_evidence()
    assert evidence['measured_K']==[40,300]
    assert evidence['analog_model_K']==[180,390]
    assert evidence['commercial_grade_matched'] is False
    assert len(evidence['file_sha256'])==64
    for pol in ('P','N'):
        from_source=graded_tec.source().properties(pol,260.)
        from_model=graded_tec.props(pol,260.)
        for key in ('S','k','rho'):
            assert float(from_model[key])==pytest.approx(float(from_source[key]),rel=1e-14)
        val300=graded_tec.props(pol,300.)
        val320=graded_tec.props(pol,320.)
        assert float(val320['k'])>0 and float(val320['rho'])>0
        assert float(val320['S'])!=pytest.approx(float(val300['S']),abs=1e-12)
    for temp in (179.99,390.01):
        with pytest.raises(ValueError):
            graded_tec.props('P',temp)


@pytest.mark.parametrize('current', [0.,.05,.15,.3])
def test_graded_stage_energy_equality(current):
    g=geometry()
    for geom in g['stages']:
        r=graded_tec.stage(geom,305.,225.,current)
        assert r['qh_w']-r['qc_w']==pytest.approx(current*r['voltage_v'],abs=1e-12)
        assert abs(r['energy_residual_w'])<1e-12
        assert r['high_T_assumption_applied'] is True
        assert r['mean_effective_resistance_ohm']>0
        assert r['mean_effective_k_w_k']>0


def test_analog_is_not_hidden_default_and_integrates_packages():
    legacy=solve(Scenario(current_a=.15))
    analog=solve(Scenario(current_a=.15,material_model='zhang2025_analog'))
    assert legacy['material_model']=='g1_constant'
    assert legacy['MCT_die_k']==pytest.approx(243.2800473061375,abs=1e-7)
    assert analog['material_model']=='zhang2025_analog'
    assert abs(analog['global_energy_residual_w'])<1e-8
    assert analog['MCT_die_k']!=pytest.approx(legacy['MCT_die_k'],abs=1.)
    assert analog['transport_source']['commercial_grade_matched'] is False
    assert all('transport_domain_K' in x for x in analog['stage_budget'])


def test_graded_run_preserves_failed_current_cases(tmp_path):
    r=run(tmp_path/'analog',material_model='zhang2025_analog')
    assert r['material_model']=='zhang2025_analog'
    assert r['temperature_dependent_tec']
    assert all(h['material_model']=='zhang2025_analog' for h in r['hypotheses'].values())
    assert len(r['cases'])==63
    bad=[v for v in r['cases'].values() if v.get('status')=='FAILED CLOSED']
    assert bad, 'Do not silently clamp high-current solutions into domain'
    for rejected in bad:
        d=rejected['diagnostics']
        assert d['candidate_is_accepted'] is False
        assert len(d['last_candidate_temperatures_k'])==5
        assert len(d['node_balance_residuals_w'])==4
        assert d['max_optimizer_scaled_residual']>1e-8
        assert d['optimizer']['message'] and isinstance(d['optimizer']['status'],int)
        assert d['physical_domain']['candidate_within_model_domain'] is True
    assert r['grid_best']['nominal_krypton']['unqualified_optimum_if_failures']
    assert all(r['cases'][key]['status']=='FAILED CLOSED' for key in
               r['grid_best']['nominal_krypton']['failed_case_labels'])
    assert (tmp_path/'analog'/'summary.json').exists()
    from pathlib import Path
    original=json.loads((Path(__file__).resolve().parents[1]/'data/integrated_graded_20261030/summary.json').read_text())
    for label,case in original['cases'].items():
        updated=r['cases'][label]
        assert case.get('status')==updated.get('status')
        if 'status' not in case:
            assert updated['MCT_die_k']==pytest.approx(case['MCT_die_k'],abs=1e-9)
            assert updated['terminal_voltage_v']==pytest.approx(case['terminal_voltage_v'],abs=1e-11)
            for old,new in zip(case['stage_budget'],updated['stage_budget']):
                for key in ('qc_w','qh_w','voltage_v'):
                    assert new[key]==pytest.approx(old[key],abs=1e-11)


@pytest.mark.parametrize('bad',[
    {'material_model':'invalid'}, {'current_a':1.1}, {'pn_thermal_conductivity_scale':0},
])
def test_analog_bad_inputs_fail_closed(bad):
    with pytest.raises(ValueError):
        solve(replace(Scenario(material_model='zhang2025_analog'),**bad))

def test_breakpoint_split_quadrature_is_order_independent():
    geom=geometry()['stages'][0]
    two=graded_tec.stage(geom,303.,225.,.15,gauss_n=2)
    eight=graded_tec.stage(geom,303.,225.,.15,gauss_n=8)
    for key in ('qc_w','qh_w','voltage_v','conduction_w','joule_w'):
        assert two[key]==pytest.approx(eight[key],abs=2e-12)

def test_affine_analog_against_independent_bounded_1d_leg_bvp():
    # Material-matched BVP comparison: checks the affine-temperature
    # simplification, NOT OEM/device agreement. All T inside 40..300K source.
    from tecooledmct.oem_phase_a import bounded_leg
    g=geometry()['stages'][0]
    hot,cold,current=295.,250.,.1
    approximate=graded_tec.stage(g,hot,cold,current)
    j=current/g['leg_area_m2']; length=g['leg_length_m']
    profile=graded_tec.source()
    n=bounded_leg(profile,'N',hot,cold,j,length,intervals=32)
    p=bounded_leg(profile,'P',hot,cold,-j,length,intervals=32)
    n_couple=g['couples'];area=g['leg_area_m2']
    full_qc=-n_couple*area*(n['q_cold_w_m2']+p['q_cold_w_m2'])
    full_v=n_couple*(n['electric_integral_v']-p['electric_integral_v'])
    assert abs(approximate['qc_w']-full_qc)<.0005
    assert abs(approximate['voltage_v']-full_v)<.001


@pytest.mark.parametrize('polarity',['P','N'])
@pytest.mark.parametrize('temperature',[299.9999,300.,300.0001,390.])
def test_active_property_law_reciprocal_and_one_sided_derivative(polarity,temperature):
    p=graded_tec.props(polarity,temperature)
    curve=graded_tec.source().curves[polarity]['S']
    factor=1. if temperature<=300 else .25
    assert p['sigma']==1/p['rho']
    assert p['thomson_v_k']==temperature*factor*curve.slope(min(temperature,300.))
    # At 300 use measured left limit; at 390 continuation left limit.
    step=-1e-5 if temperature in (300.,390.) else 1e-5
    finite_difference=(graded_tec.props(polarity,temperature+step)['S']-p['S'])/step
    assert p['thomson_v_k']==pytest.approx(temperature*finite_difference,rel=2e-7,abs=1e-12)


def test_vector_property_derivatives_and_strict_guards():
    for pol in ('P','N'):
        temperatures=np.array([180.,280.,299.999,300.,300.001,390.])
        result=graded_tec.props(pol,temperatures)
        assert np.array_equal(result['sigma'],1/result['rho'])
        assert all(result['S']*(1 if pol=='P' else -1)>0)
        for i,temp in enumerate(temperatures):
            assert result['thomson_v_k'][i]==graded_tec.props(pol,temp)['thomson_v_k']
    for temp in (np.nan,np.inf,-np.inf,np.nextafter(180.,0.),np.nextafter(390.,np.inf)):
        with pytest.raises(ValueError):
            graded_tec.props('P',temp)


def test_prior_accepted_stage_values_unchanged():
    result=solve(Scenario(material_model='zhang2025_analog'))
    from pathlib import Path
    old=json.loads((Path(__file__).resolve().parents[1]/'data/integrated_graded_20261030/summary.json').read_text())
    original=old['cases']['nominal_krypton_I0.15']
    assert result['MCT_die_k']==pytest.approx(original['MCT_die_k'],abs=1e-10)
    assert result['terminal_voltage_v']==pytest.approx(original['terminal_voltage_v'],abs=1e-12)


def test_representative_nonlinear_bvp_checks():
    from tecooledmct.graded_tec_checks import compare
    report=compare()
    assert len(report['rows'])==6
    assert report['assumed_300_390K_continuation_validated'] is False
    for row in report['rows']:
        for level in row['bvp_levels']:
            assert 40<level['temperature_min_k']<=level['temperature_max_k']<300
            assert level['max_leg_balance_residual_w']<1e-6
            assert level['max_leg_energy_error_w']<1e-6
        for error in row['errors'].values():
            assert np.isfinite(error['relative_error_abs'])
            assert error['absolute_error']>=0
    # A practical comparison check at the original low-current point.
    assert report['rows'][0]['errors']['qc_w']['absolute_error']<.0005
