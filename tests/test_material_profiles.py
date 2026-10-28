import json
import numpy as np
import pytest
from tecooledmct.material_profiles import Curve,load_profile,synthetic_profile,DATA

def test_source_units_signs_and_reciprocal_resistivity():
    p=load_profile()
    assert p.interval==(200,300)
    for kind in ('P','N'):
        v=p.properties(kind,np.array([200,260,300]))
        assert np.all(v['sigma']*v['rho']==pytest.approx(1))
        assert np.all(v['k']>0)
        assert np.all(np.sign(v['S'])==(1 if kind=='P' else -1))
    # Independent source-figure anchors catch an inverted negative axis.
    assert p.properties('N',300)['S']==pytest.approx(-190e-6,abs=5e-6)
    assert abs(p.properties('N',300)['S'])>abs(p.properties('N',200)['S'])
    assert p.properties('P',300)['k']==pytest.approx(1.10,abs=.01)
    assert p.metadata['oem_grade_matched'] is False

@pytest.mark.parametrize('temperature',[199.999,300.001,float('nan')])
def test_no_silent_extrapolation(temperature):
    with pytest.raises(ValueError):load_profile().properties('P',temperature)

def test_linear_interpolation_derivative_and_units():
    c=Curve((200,250,300),(1e-4,2e-4,2.5e-4),'V/K')
    assert c.evaluate(225)==pytest.approx(1.5e-4)
    assert c.slope(225)==pytest.approx(2e-6)
    assert c.slope(300)==pytest.approx(1e-6)
    with pytest.raises(ValueError):Curve((200,300),(1,2),'mV/K')
    with pytest.raises(ValueError):Curve((300,200),(1,2),'V/K')

def test_incomplete_and_synthetic_are_not_grade_qualified():
    r=json.loads((DATA/'source_registry.json').read_text())
    assert not r['sources'][0]['complete_triple_profile']
    assert not r['sources'][1]['complete_triple_profile']
    assert synthetic_profile().metadata['status'].startswith('SYNTHETIC')
