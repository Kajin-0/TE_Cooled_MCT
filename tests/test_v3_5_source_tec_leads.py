"""V3.5 source-local two-power-lead finite-route physical regression tests."""
from pathlib import Path
import json,hashlib
from scripts.v3_5_supply_lead_boundary import LEADS,MODELS,evaluate
ROOT=Path(__file__).resolve().parents[1]
V34=ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json'
def test_actual_pin_contacts():
    assert {v['pin']:v['ceramic_face_tag'] for v in LEADS.values()}=={1:8,9:36}
    assert len(LEADS)==2
    assert abs(LEADS['TEC_lead1']['source_internal_length_m']-0.0034510622711917908)<1e-14
    assert abs(LEADS['TEC_lead9']['source_internal_length_m']-0.004964886971715783)<1e-14
    assert all(abs(z['source_radius_m']-1e-4)<1e-15 for z in LEADS.values())
def test_isothermal_wire_energy_conservation():
    for alloy in MODELS:
        for current in (0.,.1,.4,1.):
            z=evaluate({8:300.,36:300.},alloy,current_A=current)
            assert abs(z['conduction_into_ceramic_W'])<1e-13
            assert abs(z['total_pad_heat_W']-.5*z['joule_W'])<1e-12
            assert abs(z['joule_W']-current**2*z['total_R_ohm'])<1e-12
            assert abs(sum(z['face_heats_W'].values())-z['total_pad_heat_W'])<1e-12
def test_hot_and_cold_lead_signs():
    # As measured in V3.4's saved native ceramic FEM surfaces.
    T={8:303.94314462845284,36:298.39062138990175}
    a=evaluate(T,'copper')
    assert a['per_lead']['TEC_lead1']['conduction_into_tec_W']<0
    assert a['per_lead']['TEC_lead9']['conduction_into_tec_W']>0
    assert abs(a['total_R_ohm']-0.004607673334498167)<1e-12
    assert abs(a['conduction_into_ceramic_W']+0.01028477700044805)<1e-12
def test_material_electric_loss_ordering():
    T={8:300.,36:300.}
    q=[evaluate(T,v)['joule_W'] for v in ('copper','nickel_proxy','fecral_screen')]
    assert 0<q[0]<q[1]<q[2]
    assert q[2]>0.05
def test_internal_length_vs_external_factory_excess():
    T={8:310.,36:290.}
    l=[evaluate(T,'copper',v) for v in (.5,1.,2.)]
    assert abs(l[2]['total_R_ohm']-2*l[1]['total_R_ohm'])<1e-13
    assert abs(l[0]['total_R_ohm']-.5*l[1]['total_R_ohm'])<1e-13
    assert abs(l[2]['per_lead']['TEC_lead1']['thermal_G_W_K']-.5*l[1]['per_lead']['TEC_lead1']['thermal_G_W_K'])<1e-13
    assert all('NOT INSIDE' in v['factory_supplied_extra_length'] for v in LEADS.values())
def test_v34_frozen_archive():
    assert hashlib.sha256(V34.read_bytes()).hexdigest()=='2aa84432098907c3ac37d276fa3b430652ac77ce53a5fbac1174828b9e5d63bb'
if __name__=='__main__':
    for name,value in sorted(globals().items()):
        if name.startswith('test_') and callable(value):
            value();print(name,'PASS')
