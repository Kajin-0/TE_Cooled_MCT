"""Prospective bounded 1D screening: independent analytic and source-domain checks.

Do not alter/reinterpret historical G2d material, FEM or publication gates.
"""
import numpy as np
import pytest

from tecooledmct.material_profiles import (
    DATA as PROFILE_DATA, load_profile, synthetic_profile,
)
from tecooledmct.oem_phase_a import bounded_leg, bounded_cascade
from tecooledmct.g2d_network import local_leg


@pytest.mark.parametrize('polarity,j', [('P',2e5), ('N',-2e5)])
def test_bounded_leg_matches_constant_property_analytic_solution(polarity,j):
    profile=synthetic_profile(varying=False)
    hot,cold,length=300.,280.,.001
    p=profile.properties(polarity,hot)
    result=bounded_leg(profile,polarity,hot,cold,j,length,intervals=24)
    z=np.linspace(0,length,25)
    a=j*j*p['rho']/(2*p['k'])
    expected=hot+((cold-hot)/length+a*length)*z-a*z*z
    assert np.max(np.abs(np.asarray(result['temperatures_k'])-expected))<.002
    exact_voltage=j*p['rho']*length+p['S']*(cold-hot)
    assert result['electric_integral_v']==pytest.approx(exact_voltage,abs=2e-7)
    assert abs(result['energy_error_w_m2'])<2e-3
    assert result['max_balance_residual_w_m2']<2e-3


def test_no_material_evaluation_outside_coverage_even_at_300k():
    profile=load_profile(PROFILE_DATA/'zhang2025_he_40_300_v2.json')
    assert profile.interval==(40,300)
    result=bounded_leg(profile,'N',300.,275.,5e5,.00107,intervals=16)
    assert result['max_k']<=300
    assert result['min_k']>=40
    for kw in ({'hot':300.0000001}, {'cold':39.9}, {'length':-1.}):
        args=dict(profile=profile,polarity='N',hot=300.,cold=275.,current_density=5e5,length=.00107,intervals=16)
        args.update(kw)
        with pytest.raises(ValueError):
            bounded_leg(**args)
    with pytest.raises(ValueError):
        bounded_leg(profile,'N',300.,275.,5e5,.00107,intervals=7)


@pytest.mark.parametrize('polarity,j', [('P',-2e5), ('N',2e5)])
def test_bounded_leg_agrees_with_existing_independent_bvp(polarity,j):
    profile=load_profile(PROFILE_DATA/'zhang2025_he_40_300_v2.json')
    original=local_leg(profile,polarity,295.,280.,j,.00107)
    coarse=bounded_leg(profile,polarity,295.,280.,j,.00107,intervals=16)
    fine=bounded_leg(profile,polarity,295.,280.,j,.00107,intervals=32)
    assert abs(fine['q_hot_w_m2']-original['q_hot_w_m2'])<15.
    assert abs(fine['q_cold_w_m2']-original['q_cold_w_m2'])<15.
    assert abs(fine['electric_integral_v']-original['electric_integral_v'])<5e-5
    assert abs(fine['q_hot_w_m2']-original['q_hot_w_m2']) <= abs(coarse['q_hot_w_m2']-original['q_hot_w_m2'])+2.
    assert abs(fine['energy_error_w_m2'])<2e-3


def test_bounded_cascade_returns_verified_screening_not_validation():
    profile=load_profile(PROFILE_DATA/'zhang2025_he_40_300_v2.json')
    r=bounded_cascade(profile,.05,0.,300.,intervals=16)
    assert r['method'].startswith('bounded source-backed')
    assert not r['grade_matched']
    assert r['min_leg_temperature_k']>=40 and r['max_leg_temperature_k']<=300.
    assert r['max_cascade_residual_w']<1e-6
    assert r['max_stage_energy_error_w']<1e-6
    assert r['delta_t_k']>0 and r['voltage_v']>0
