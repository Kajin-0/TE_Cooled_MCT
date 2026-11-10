"""Meaningful analytical and archived-evidence controls; no whole-package solve."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import pytest
from tecooledmct import nonlinear_tec,graded_tec
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/tec_pellet_screen_20261110'
def read(p):return json.loads(p.read_text())

@pytest.mark.parametrize('polarity,S,J',[('P',200e-6,-2.5e6),('N',-180e-6,2.5e6)])
def test_uniform_material_peltier_fourier_joule_and_voltage(monkeypatch,polarity,S,J):
    rho=1e-5;k=1.4;length=.0005;hot=300.;cold=250.
    def constant(_pol,t,_scales):
        return {key:np.full_like(t,val,dtype=float) for key,val in [('S',S),('rho',rho),('k',k),('S_prime',0.),('rho_prime',0.),('k_prime',0.)]}
    monkeypatch.setattr(nonlinear_tec,'properties',constant)
    d=nonlinear_tec.leg(polarity,hot,cold,J,length)
    expected_hot=S*hot*J+k*(hot-cold)/length-.5*rho*J*J*length
    expected_cold=S*cold*J+k*(hot-cold)/length+.5*rho*J*J*length
    expected_v=J*rho*length+S*(cold-hot)
    assert d['q_hot_w_m2']==pytest.approx(expected_hot,abs=1e-6)
    assert d['q_cold_w_m2']==pytest.approx(expected_cold,abs=1e-6)
    assert d['electric_integral_v']==pytest.approx(expected_v,abs=1e-12)
    assert d['joule_w_m2']==pytest.approx(J*J*rho*length,abs=1e-6)
    assert expected_cold-expected_hot==pytest.approx(J*expected_v,abs=1e-8)

@pytest.mark.parametrize('polarity',['P','N'])
def test_actual_law_scaling_and_one_sided_knot(polarity):
    a=graded_tec.props(polarity,np.array([299.999,300.,300.001,390.]))
    assert np.all(a['rho']>0) and np.all(a['k']>0)
    assert np.allclose(a['sigma'],1/a['rho'],rtol=1e-14)
    curve=graded_tec.source().curves[polarity]['S'];left=curve.slope(300.)
    assert a['thomson_v_k'][1]==pytest.approx(300*left,rel=1e-12)
    assert a['thomson_v_k'][2]==pytest.approx(300.001*.25*left,rel=1e-12)
    assert a['thomson_v_k'][3]==pytest.approx(390*.25*left,rel=1e-12)
    with pytest.raises(ValueError):graded_tec.props(polarity,390.01)
    # Equal A/L at unchanged I, with both A and L doubled, is the same
    # dimensionless nonlinear field and terminal heat/power.
    A=.4e-3*.4e-3;I=.4;L=.5e-3;sgn=1 if polarity=='N' else -1
    q1=nonlinear_tec.leg(polarity,300.,250.,sgn*I/A,L)
    q2=nonlinear_tec.leg(polarity,300.,250.,sgn*I/(2*A),2*L)
    assert np.allclose(q1['temperatures_k'],q2['temperatures_k'],atol=1e-9)
    assert q1['electric_integral_v']==pytest.approx(q2['electric_integral_v'],abs=1e-12)
    assert A*q1['q_cold_w_m2']==pytest.approx(2*A*q2['q_cold_w_m2'],abs=1e-11)

def test_registered_results_independent_audits_and_matched_power():
    reg=read(DATA/'registration.json');seal=read(DATA/'source_seal.json');summary=read(DATA/'summary.json')
    assert hashlib.sha256((DATA/'registration.json').read_bytes()).hexdigest()==seal['registration_sha256']
    for name,digest in {**reg['source_sha256'],**seal['sources_sha256']}.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    assert len(reg['geometry_cases'])==summary['accepted_case_count']==summary['independently_audited_count']==5
    assert summary['full_system_solves']==0 and summary['physical_geometry_variants_qualified']==0
    for z in reg['geometry_cases']:
        p=DATA/'cases'/z['id'];r=read(p/'result.json');a=read(p/'independent_audit.json')
        assert a['status'].startswith('PASS') and a['result_sha256']==hashlib.sha256((p/'result.json').read_bytes()).hexdigest()
        assert abs(r['matched_power']['electrical_power_W']-reg['matched_power_reference_W'])<1e-6
        assert not r['source_CAD_rebuilt'] and not r['detector_or_top_temperature_solved']
        assert .25<=r['matched_power']['current_A']<=.55 and max(z['max_leg_K'] if 'max_leg_K' in z else 0 for z in [r['matched_power']])<=390
    assert read(DATA/'cases/baseline/result.json')['baseline_replay_max_abs_difference']<1e-10
