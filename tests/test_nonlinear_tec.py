from dataclasses import replace
import numpy as np
import pytest

from tecooledmct import nonlinear_tec as nt
from tecooledmct.integrated_reference import Scenario,geometry,solve,OperatingPointFailure
from tecooledmct.graded_tec_checks import POINTS
from tecooledmct import graded_tec
from tecooledmct.oem_phase_a import bounded_leg


@pytest.mark.parametrize('polarity,j',[('P',-8e5),('N',8e5),('P',0.),('N',-8e5)])
def test_banded_solver_against_constant_analytic_profile(monkeypatch,polarity,j):
    s=160e-6 if polarity=='P' else -170e-6;rho=8e-6;k=1.5
    def law(pol,t,scales):
        return {key:np.full_like(t,value) for key,value in
                dict(S=s,rho=rho,k=k,S_prime=0.,rho_prime=0.,k_prime=0.).items()}
    monkeypatch.setattr(nt,'properties',law)
    r=nt.leg(polarity,300.,270.,j,.001,intervals=32)
    z=np.linspace(0.,.001,33)
    exact=300+(270-300)*z/.001+rho*j*j/(2*k)*z*(.001-z)
    assert np.max(np.abs(r['temperatures_k']-exact))<1e-8
    assert r['electric_integral_v']==pytest.approx(j*rho*.001+s*(270-300),abs=1e-12)
    assert r['max_balance_residual_w_m2']<1e-4


@pytest.mark.parametrize('idx,hot,cold,current',POINTS)
def test_direct_solver_matches_independent_same_grid_bvp(idx,hot,cold,current):
    g=geometry()['stages'][idx];tr=nt.Transport();r=tr.stage(g,hot,cold,current)
    a=g['leg_area_m2'];n=g['couples'];p=graded_tec.source()
    refs={pol:bounded_leg(p,pol,hot,cold,current/a*(1 if pol=='N' else -1),g['leg_length_m'],intervals=32)
          for pol in ('P','N')}
    qc=-n*a*sum(v['q_cold_w_m2'] for v in refs.values())
    voltage=n*(refs['N']['electric_integral_v']-refs['P']['electric_integral_v'])
    assert r['qc_w']==pytest.approx(qc,abs=2e-9)
    assert r['voltage_v']==pytest.approx(voltage,abs=2e-8)
    assert abs(r['energy_residual_w'])<1e-9
    assert r['affine_T_axial_approximation'] is False
    assert tr.stage(g,hot,cold,current)==r and tr.hits==1
    tr.stage(g,hot,cold+1e-5,current)
    assert tr.calls==2,'Cache keys must not round temperatures'


def test_stage_zero_negative_controls_and_rejections():
    g=geometry()['stages'][0];tr=nt.Transport()
    r=tr.stage(g,250.,250.,0.)
    assert max(abs(r[k]) for k in ('qc_w','qh_w','voltage_v'))<1e-12
    reverse=tr.stage(g,280.,260.,-.2)
    assert abs(reverse['qh_w']-reverse['qc_w']+.2*reverse['voltage_v'])<1e-9
    for hot in (179.99,390.01,np.nan):
        with pytest.raises(ValueError):tr.stage(g,hot,250.,.1)
    with pytest.raises(nt.LegFailure) as e:
        nt.leg('N',260.,240.,4e6,.00107,max_iterations=1)
    assert e.value.diagnostics['temperatures_k']


def test_new_model_is_opt_in_and_preserves_package_failure_diagnostics():
    old=solve(Scenario());new=solve(Scenario(material_model='zhang2025_nonlinear'))
    assert old['material_model']=='g1_constant'
    assert new['MCT_die_k']==pytest.approx(231.191779,abs=1e-5)
    assert new['transport_computation']['exact_cache_hits']>0
    assert abs(new['global_energy_residual_w'])<1e-8
    with pytest.raises(OperatingPointFailure) as e:
        solve(Scenario(current_a=.7,material_model='zhang2025_nonlinear'))
    assert e.value.diagnostics['candidate_is_accepted'] is False
    assert e.value.diagnostics['physical_domain']['measured_PN_interval_k']==[40,300]
    zero=solve(Scenario(current_a=0.,material_model='zhang2025_nonlinear'))
    assert abs(zero['global_energy_residual_w'])<1e-8
    assert zero['MCT_die_k']>300


def test_assumed_continuation_consistency_not_measured_validation():
    from tecooledmct.nonlinear_tec_study import ActiveProfile
    r=nt.leg('N',330.,260.,8e5,.00107)
    reference=bounded_leg(ActiveProfile(),'N',330.,260.,8e5,.00107,intervals=32)
    assert r['assumed_high_T_continuation_used']
    assert r['electric_integral_v']==pytest.approx(reference['electric_integral_v'],abs=2e-8)


@pytest.mark.parametrize('hot,cold,current',[(260.,240.,.7),(230.,210.,.9)])
def test_high_current_accuracy_against_refined_independent_bvp(hot,cold,current):
    g=geometry()['stages'][0];a=g['leg_area_m2'];n=g['couples']
    r=nt.Transport(32).stage(g,hot,cold,current)
    reference={pol:bounded_leg(graded_tec.source(),pol,hot,cold,
        current/a*(1 if pol=='N' else -1),g['leg_length_m'],intervals=64) for pol in ('P','N')}
    qc=-n*a*sum(v['q_cold_w_m2'] for v in reference.values())
    voltage=n*(reference['N']['electric_integral_v']-reference['P']['electric_integral_v'])
    assert abs(r['qc_w']-qc)/abs(qc)<1e-4
    assert abs(r['voltage_v']-voltage)/abs(voltage)<1e-4


def test_package_leg_grid_convergence_at_high_current():
    coarse=solve(Scenario(current_a=.9,material_model='zhang2025_nonlinear'),transport_intervals=32)
    fine=solve(Scenario(current_a=.9,material_model='zhang2025_nonlinear'),transport_intervals=64)
    assert abs(coarse['MCT_die_k']-fine['MCT_die_k'])<.002
    assert abs(coarse['terminal_voltage_v']-fine['terminal_voltage_v'])<.0003


def test_internal_joule_overshoot_marks_assumed_law_even_with_cool_boundaries():
    r=nt.Transport().stage(geometry()['stages'][0],295.,285.,.7)
    assert r['leg_temperature_extrema_k'][1]>300.
    assert r['high_T_assumption_applied'] is True
