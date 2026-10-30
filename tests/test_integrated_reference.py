"""Checks of the corrected-reference 5-node exploratory package model."""
from dataclasses import replace
import json
import numpy as np
import pytest

from tecooledmct.integrated_reference import (
    Scenario, GEOMETRY, coefficients, gas_transport, geometry,
    heat_paths, radiative_load, scenarios, solve, stage_thermoelectric,
)


def test_corrected_geometry_only_and_source_audit():
    g=geometry()
    assert g['source_archive'].endswith('geometry_complete_checkpoint_20261030')
    assert sum(s['couples'] for s in g['stages'])==44
    assert [s['couples'] for s in g['stages']]==[28,12,4]
    assert len(g['wires'])==4
    assert {w['pin'] for w in g['wires']}=={1,7,8,9}
    assert g['die_area_m2']==pytest.approx(1e-6)
    assert g['die_attach_thickness_over_area_m_inverse']==pytest.approx(30.)
    assert len(g['source_sha256'])==2
    assert all(len(x)==64 for x in g['source_sha256'].values())


@pytest.mark.parametrize('current', [0., .05, .1, .2])
def test_thermoelectric_stage_analytic_work_identity(current):
    c=coefficients(Scenario(),geometry())
    for item in c:
        x=stage_thermoelectric(item,300.,250.,current)
        assert x['qh_w']-x['qc_w']==pytest.approx(current*x['voltage_v'],abs=5e-16)
        assert x['conduction_w']==pytest.approx(item['k_w_k']*50)
        assert x['joule_w']==pytest.approx(current**2*item['r_ohm'])


def test_passive_null_state_has_no_reservoir_heat_leak_or_voltage():
    s=replace(Scenario(),current_a=0.,detector_bias_w=0.,detector_absorbed_w=0.,
              cavity_pressure_pa=0.,cap_emissivity=0.,window_thermal_emissivity=0.)
    r=solve(s)
    assert all(abs(v-300.)<1e-7 for v in r['temperatures_k'].values())
    assert abs(r['terminal_voltage_v'])<1e-10
    assert abs(r['bath_rejected_power_w'])<1e-9
    assert abs(r['global_energy_residual_w'])<1e-10


@pytest.mark.parametrize('scenario', list(scenarios()))
def test_all_scenarios_conserve_energy_and_temperature_domain(scenario):
    s=scenarios()[scenario]
    for current in (.0,.1,.15,.25):
        r=solve(replace(s,current_a=current))
        assert 180.<min(r['temperatures_k'].values())<390.
        assert max(r['temperatures_k'].values())<390.
        assert r['max_node_balance_residual_w']<1e-8
        assert abs(r['global_energy_residual_w'])<1e-8
        assert all(abs(st['energy_residual_w'])<1e-9 for st in r['stage_budget'])
        assert r['terminal_electrical_power_w']==pytest.approx(r['current_a']*r['terminal_voltage_v'])
        assert r['heat_paths_w']['die_internal_heating_w']==pytest.approx(s.detector_bias_w+s.detector_absorbed_w)
        assert r['qualification'].startswith('exploratory')


def test_vacuum_zero_gas_and_reciprocal_radiation_sign():
    s=replace(Scenario(),cavity_pressure_pa=0.)
    g=geometry()
    temperatures=(300.,270.,250.,230.,230.)
    q=heat_paths(s,g,temperatures)
    assert q['gas_w'].tolist()==[0.]*4
    assert all(v>0 for v in q['radiation_w'])
    assert radiative_load(300,240,1e-6,.2,.5,.5)==pytest.approx(
        -radiative_load(240,300,1e-6,.5,.2,.5))
    assert radiative_load(300,240,1e-6,0,.5,.5)==0.


def test_gas_sub200_extension_is_explicit_and_pressure_zero_guard():
    s=Scenario()
    k200,_,flag=gas_transport(s,200.)
    assert not flag
    k190,_,flag=gas_transport(s,190.)
    assert flag and k190==pytest.approx(k200*(190/200)**.75)
    with pytest.raises(ValueError):
        gas_transport(s,179.9)
    zero=replace(s,cavity_pressure_pa=0.)
    assert np.array_equal(heat_paths(zero,geometry(),(300.,270.,250.,230.,220.))['gas_w'],np.zeros(4))


def test_package_sensitivity_and_hot_sink_direction():
    low,nominal,high=(solve(scenarios()[name]) for name in scenarios())
    assert low['MCT_die_k']<nominal['MCT_die_k']<high['MCT_die_k']
    assert low['bath_rejected_power_w']<high['bath_rejected_power_w']
    fixed=Scenario()
    r1=solve(replace(fixed,heat_sink_k_w=0.))
    r2=solve(replace(fixed,heat_sink_k_w=5.))
    assert r1['temperatures_k']['hot_ceramic']==pytest.approx(300.,abs=1e-8)
    assert r2['temperatures_k']['hot_ceramic']>300.
    assert r2['MCT_die_k']>r1['MCT_die_k']


@pytest.mark.parametrize('changes',[
    {'gas':'Xe'},{'ambient_k':100.},{'current_a':-1.},
    {'gas_gap_m':0.},{'cavity_pressure_pa':-1.},
    {'heat_sink_k_w':-1.},{'cap_emissivity':1.1},
    {'pn_seebeck_scale':0.},{'pn_resistivity_scale':-1.},
    {'accommodation':0.},{'stage_bypass_w_k':(-1,0,0)},
])
def test_invalid_assumptions_fail_closed(changes):
    with pytest.raises(ValueError):
        solve(replace(Scenario(),**changes))

def test_immutable_geometry_hash_refuses_modified_archive(monkeypatch,tmp_path):
    import tecooledmct.integrated_reference as ir
    import shutil
    for name in ('manifest.json','wire_routes.json','checksums.json'):
        shutil.copy2(GEOMETRY/name,tmp_path/name)
    with (tmp_path/'manifest.json').open('ab') as f:
        f.write(b'\\n')
    monkeypatch.setattr(ir,'GEOMETRY',tmp_path)
    with pytest.raises(ValueError,match='hash mismatch'):
        ir.geometry()


def test_reproducible_current_grid_and_best_label(tmp_path):
    from tecooledmct.integrated_reference import run
    report=run(tmp_path/'new')
    assert len(report['cases'])==63
    assert len(report['summary_rows'])==63
    assert all('status' not in x for x in report['cases'].values())
    for scenario in scenarios():
        best=report['grid_best'][scenario]
        assert .4<best['current_a']<.9
        assert best['detector_k']==min(
            row['detector_k'] for row in report['summary_rows']
            if row['scenario']==scenario)
    for name in ('summary.json','sweep.csv','sensitivity.csv'):
        assert (tmp_path/'new'/name).is_file()
