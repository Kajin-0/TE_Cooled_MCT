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
    assert r['grid_best']['nominal_krypton']['unqualified_optimum_if_failures']
    assert all(r['cases'][key]['status']=='FAILED CLOSED' for key in
               r['grid_best']['nominal_krypton']['failed_case_labels'])
    assert (tmp_path/'analog'/'summary.json').exists()


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
