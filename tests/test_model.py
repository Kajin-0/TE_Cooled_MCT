from dataclasses import replace
import pytest
from tecooledmct.model import Scenario, gas_conductivity, solve, calibration_check, stage_transport
from tecooledmct.experiments import compare_gases, sweep, monte_carlo, simulate_transient


def test_datasheet_anchor_not_validation():
    c=calibration_check()
    assert abs(c['delta_t0_k']-113)<2
    assert abs(c['qmax_deltat0_w']-.5)<.015
    assert abs(c['R_ac_nominal_ohm']-2.89)<1e-9


def test_three_stage_thermal_balance():
    p=solve(Scenario())
    assert p['stage_k'][2]<p['stage_k'][1]<p['stage_k'][0]<p['hot_k']
    assert p['energy_balance_max_w']<1e-6
    for stage in p['stage_transport']:
        assert stage['qh_w']-stage['qc_w']==pytest.approx(p['current_a']*stage['voltage_v'])


def test_gas_ranking():
    args=Scenario()
    assert gas_conductivity(replace(args,gas='Kr'))<gas_conductivity(replace(args,gas='Ar'))<gas_conductivity(replace(args,gas='N2'))
    temps={r['gas']:r['detector_k'] for r in compare_gases(args)}
    assert temps['Kr']<temps['Ar']<temps['N2']


def test_parasitic_loads_and_hot_sink():
    s=Scenario()
    base=solve(s)['detector_k']
    assert solve(replace(s,detector_bias_v=1.))['detector_k']>base
    assert solve(replace(s,aperture_area_mm2=40))['detector_k']>base
    assert solve(replace(s,hot_to_ambient_k_per_w=6))['detector_k']>base
    assert solve(replace(s,gas_pressure_pa=0))['detector_k']<base


def test_mixture_and_inputs():
    s=Scenario(gas='mixture',gas_mole_fractions=(.5,.5,0.))
    assert gas_conductivity(s)>0
    with pytest.raises(ValueError):solve(replace(s,gas_mole_fractions=(.5,.3,.3)))
    with pytest.raises(ValueError):solve(replace(s,current_a=2))
    with pytest.raises(ValueError):solve(replace(s,gas='Kr',gas_mole_fractions=(-.1,.1,1.)))


def test_sweeps_uncertainty_and_transient():
    s=Scenario()
    assert len(sweep(s,'current_a',[.3,.5,.7]))==3
    mc=monte_carlo(s,8,seed=7)
    assert mc['n_converged']==8 and mc['p95_k']>mc['p05_k']
    tr=simulate_transient(s,25,20)
    assert tr['detector_k'][-1]<s.ambient_k
    assert len(tr['time_s'])==20
