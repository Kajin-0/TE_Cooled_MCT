"""Source bounds, heat-path scaling, independent wire physics and preservation."""
import math
import numpy as np
import pytest
from tecooledmct.fem_g3a_data import registry,preserve,wire_conductance
from tecooledmct.fem_g3a_physics import material_properties


def test_actual_mct_anchors_are_local_bounded_and_separate_from_tec_constants():
    k,sigma,s=material_properties('MCT',np.array([90.,148.,298.,400.]))
    assert k==pytest.approx([2.41,1.61,.973,.790])
    assert np.all(s==0) and np.all(sigma==1e-12)
    assert material_properties('MCT',223.)[0]==pytest.approx((1.61+.973)/2)
    for t in (89.999,400.001,float('nan')):
        with pytest.raises(ValueError):material_properties('MCT',t)
    assert registry()['mct']['source_relative_uncertainty_ranges']['k']==[.07,.14]


def test_thermal_layer_resistance_scaling_and_electrical_isolation():
    for name in ('Mount','Attach'):
        a=material_properties(name,300.)
        b=material_properties(name,300.,attach_scale=.5,mount_scale=.5)
        assert float(b[0])==pytest.approx(float(a[0])/2)
        assert float(b[1])==1e-12 and float(b[2])==0
    assert float(material_properties('Kovar',300.,sigma=1e-14)[1])==1e-14
    assert float(material_properties('Au',300.)[0])==315


def test_two_wire_power_is_conservative_and_has_correct_geometry_scaling():
    g=wire_conductance();single=315*math.pi*(25e-6/2)**2/.007
    assert g==pytest.approx(2*single)
    assert wire_conductance(diameter=50e-6)==pytest.approx(4*g)
    assert wire_conductance(length=.014)==pytest.approx(g/2)
    # A hot/cold swap reverses heat, and the two endpoint powers cancel.
    for warm,cold in [(300.,260.),(260.,300.)]:
        q=g*(warm-cold);assert -q+q==0
        assert q*(warm-cold)>=0
    assert wire_conductance(number=0)==0
    for count in (-1,1.5):
        with pytest.raises(ValueError):wire_conductance(number=count)


def test_simulation_scope_and_all_prior_source_evidence_are_intact():
    p=registry();assert p['feedthroughs']['actually_meshed_pin_count']==2
    assert p['feedthroughs']['illustrated_pin_count']==9
    assert 'cap/window' in p['missing'] and 'carrier transport' in p['missing']
    assert preserve()['g2d_unchanged']
