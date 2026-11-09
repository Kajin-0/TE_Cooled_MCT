"""Focused independent material/circuit checks for the provisional V3.4 copper multiport."""
from pathlib import Path
import json,hashlib
import numpy as np
from scripts.v3_4_source_copper_multiport import (
 evaluate,SPEC,PORTS,STAGES,DESIGN,FACES,TABS,THERMAL_CONTACT_R_AREA_M2K_W)

def plate_temps(a=303.,b=265.,c=235.):
    t=[a,b,c]
    return {k:t[i] for s in SPEC.values() for k,i in zip(s['faces'],s['stage'])}

def test_source_faces_and_thermally_distinct_ports():
    assert len(SPEC)==3
    assert set(SPEC)=={58,80,88}
    assert [tuple(SPEC[x]['faces']) for x in (58,80,88)]==[(38,75),(79,105),(36,74,104)]
    assert len(SPEC[88]['segments_m'])==2
    for s in SPEC.values():
        assert abs(s['cross_section_m2']-9e-9)<1e-20
        assert all(x>0 for x in s['segments_m'])
        assert all(abs(x-6e-8)<1e-18 for x in s['contact_area_m2'])
        assert len(s['segments_m'])==len(s['faces'])-1
        assert 0 < s['contact_centre_span_m'] < s['source_centerline_total_length_m']

def test_isothermal_joule_and_zero_current():
    for T in (230.,270.,300.):
        z=plate_temps(T,T,T)
        q0=evaluate(0.,z)
        assert q0['total_electrical_power_W']==0
        assert max(abs(v) for v in q0['heat_into_face_W'].values())<1e-13
        q=evaluate(.4,z)
        assert abs(sum(q['heat_into_ceramic_by_stage_W'])-q['total_electrical_power_W'])<1e-12
        assert q['total_electrical_power_W']>0
        assert all(q['heat_into_face_W'][t]>0 for t in q['heat_into_face_W'])
        assert abs(q['total_electrical_power_W']-.4*.4*q['total_electrical_R_ohm'])<1e-13

def test_heat_flows_hot_to_cold_and_voltage_positive():
    q=evaluate(.4,plate_temps())
    assert q['heat_into_ceramic_by_stage_W'][0]<0
    assert q['heat_into_ceramic_by_stage_W'][2]>0
    assert q['total_electrical_R_ohm']>0
    for n,z in q['net_details'].items():
        assert abs(sum(z['face_heat_into_ceramic_W'])-z['electric_Joule_W'])<1e-12
        assert z['electric_voltage_V']>0
        assert min(z['foil_node_temperature_K'])>180

def test_zero_current_reciprocal_three_port_and_heat_balance():
    original=plate_temps(300,265,235)
    a=evaluate(0.,original)
    # Net 88 is a true three-foot network: adjusting the center contact
    # changes all three external heat fluxes, not just a two-wire terminal.
    varied=dict(original)
    varied[74]=285.
    b=evaluate(0.,varied)
    aa=a['net_details']['88']['face_heat_into_ceramic_W']
    bb=b['net_details']['88']['face_heat_into_ceramic_W']
    assert max(abs(x-y) for x,y in zip(aa,bb))>1e-3
    for res in (a,b):
        assert abs(sum(res['heat_into_face_W'].values()))<1e-12
        for z in res['net_details'].values():
            assert abs(sum(z['face_heat_into_ceramic_W']))<1e-12

def test_contact_thermal_resistance_changes_bypass():
    T=plate_temps(303,266,236)
    q0=evaluate(0.,T,thermal_area_resistance=0.)
    q1=evaluate(0.,T,thermal_area_resistance=1e-6)
    q2=evaluate(0.,T,thermal_area_resistance=1e-5)
    # High thermal contact resistance reduces the net heat delivered to
    # the upper ceramic under a fixed imposed stage temperature profile.
    assert q0['heat_into_ceramic_by_stage_W'][2]>q1['heat_into_ceramic_by_stage_W'][2]
    assert q1['heat_into_ceramic_by_stage_W'][2]>q2['heat_into_ceramic_by_stage_W'][2]

def test_original_v33_result_is_immutable():
    p=Path(__file__).resolve().parents[1]/'data/v3_3_cavity_package_feedback_20261108/attempt02/result.json'
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='a7679d0c69b1d53f9fc7b289eb8596af4bac856fa3f3d9ade83b263f998bbd58'
