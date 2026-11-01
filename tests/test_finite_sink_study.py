"""Independent finite-sink controls, immutable baseline and genuine target calls."""
from copy import deepcopy
from dataclasses import replace
import numpy as np
import pytest

from tecooledmct.finite_sink_study import (ROOT,NOTE,design,scenario,wire_coefficients,constant_exact,
    zero_current_exact,audit,falling_brackets,nondominated,SINKS,CURRENTS)
from tecooledmct.integrated_reference import geometry
from tecooledmct.tec_material_plausibility import read,sha

DATA=ROOT/'data/finite_sink_20261101'


def test_registration_fixed_scenarios_no_geometry_or_fitted_triple():
    reg=read(DATA/'registration.json');plan=design()
    assert reg['design']==plan and len(plan['grid'])==288 and plan['maximum_top_level_calls']==361
    assert reg['protocol']==NOTE.read_text().split('## Results')[0]
    assert len({c['id'] for family in ('grid','constant','branch','target_slots') for c in plan[family]})==361
    for p,h in reg['input_sha256'].items():assert sha(ROOT/p)==h
    assert reg['producer_sha256']==sha(ROOT/'tecooledmct/finite_sink_study.py')
    assert reg['producer_sha256']==sha(DATA/'producer.py.source')
    assert [s['couples'] for s in geometry()['stages']]==[28,12,4]
    for c in plan['grid']:
        s=scenario(c);assert s.ambient_k==300 and s.detector_bias_w==.002 and s.detector_absorbed_w==0
        assert s.cavity_pressure_pa==s.cap_emissivity==s.window_thermal_emissivity==0


@pytest.mark.parametrize('R',[0.,.5,10.])
@pytest.mark.parametrize('Q',[0.,.002])
def test_two_independent_zero_current_resistance_limits(R,Q):
    g=geometry();s=replace(scenario(design()['constant'][0]),heat_sink_k_w=R,detector_bias_w=Q)
    a=constant_exact(s,g);b=zero_current_exact(s,g)
    assert a['temperatures_K'][0]==pytest.approx(b['hot_K'],abs=1e-9)
    assert a['temperatures_K'][4]==pytest.approx(b['die_K'],abs=1e-9)
    assert a['sink_W']==pytest.approx(b['sink_W'],abs=1e-11)
    assert max(abs(a['linear_residual']))<1e-11
    if Q==0:assert np.max(abs(a['temperatures_K']-300))<1e-9


def test_recorded_controls_and_baselines_are_unaltered():
    assert all(r['passed'] for r in read(DATA/'controls.json'))
    a=read(DATA/'analysis.json');assert len(a['baseline_replays'])==33
    for r in a['baseline_replays']:
        assert r['previous_status']==r['new_status']
        if r['new_status']=='ACCEPTED':assert r['die_error_K']<1e-6 and r['voltage_error_V']<1e-7
    for r in read(DATA/'branch_checks.json'):
        assert r['temperature_difference_K']<1e-5 and r['V_difference']<1e-7 and r['P_difference_W']<1e-8
        assert r['stage_heat_difference_W']<1e-8 and r['sink_difference_W']<1e-8


def test_independent_energy_paths_source_coverage_and_reject_details():
    g=geometry();cases=read(DATA/'cases.json')
    assert len(cases)==361
    for r in cases.values():
        if r['status']=='ACCEPTED':
            a=audit(scenario(r['case']),g,r['result'])
            assert abs(a['sink_W']-(a['terminal_W']+a['Qdie_W']+a['Au_into_die_W']+a['Cu_into_hot_W']-.5*a['Cu_joule_W']))<1e-8
            assert abs(a['net_total_ambient_rejection_W']-a['terminal_W']-.002)<1e-8
            assert 180<=a['leg_min_K']<=a['leg_max_K']<=390
            if r['case']['family']=='grid':assert a['assumed_continuation']==(a['leg_max_K']>300)
            if r['case']['current_A']==0:assert a['die_COP'] is None
        elif r['status']=='REJECTED':assert r['diagnostics'] and not r['diagnostics']['candidate_is_accepted']
        else:assert r['status']=='NOT RUN' and r['reason']
    sample=deepcopy(next(r for r in cases.values() if r['case']['family']=='grid' and r['status']=='ACCEPTED'))
    sample['result']['heat_paths_w']['Cu_conduction_into_hot_w']=float('nan')
    with pytest.raises(AssertionError):audit(scenario(sample['case']),g,sample['result'])


def test_target_is_real_bounded_cold_side_not_interpolated_or_gap_bridged():
    a=read(DATA/'analysis.json');cases=read(DATA/'cases.json')
    for R,cross in a['target_crossings'].items():
        assert len(cross['attempts'])<=10
        if cross['status']=='PASS':
            r=cases[cross['cold_side_case']]
            assert r['status']=='ACCEPTED' and 0<=200-r['audit']['Tdie_K']<=.005
            left,right=[cases[k] for k in cross['registered_falling_grid_brackets'][0]]
            for k in cross['attempts']:
                mid=cases[k];assert mid['case']['current_A']==.5*(left['case']['current_A']+right['case']['current_A'])
                assert mid['status']=='ACCEPTED'
                if mid['audit']['Tdie_K']>200:left=mid
                else:right=mid
    def row(i,T,status='ACCEPTED'):
        return {'case':{'id':str(i)},'status':status,'audit':{'Tdie_K':T,'terminal_W':float(i)}}
    x=[row(1,210),row(2,199,'REJECTED'),row(3,190)]
    assert falling_brackets(x)==[]
    assert falling_brackets([x[0],x[2]])==[('1','3')]
    assert nondominated([row(1,200),row(2,199),row(3,199)])==['1','2']


def test_invalid_source_and_scaling_controls_do_not_become_observations():
    assert len(read(DATA/'input_controls.json'))==6
    for c in read(DATA/'input_controls.json'):assert c['rejected']
    controls=read(DATA/'analysis.json')['sink_load_scaling_controls']
    assert len(controls)==24 and max(r['sink_load_W'] for r in controls)==3
    for r in controls:assert r['hot_rise_K']==r['sink_K_W']*r['sink_load_W']
