import numpy as np
import pytest
from tecooledmct.material_profiles import DATA,load_profile


def test_additive_low_temperature_source_profile_preserves_v1():
    old=load_profile();p=load_profile(DATA/'zhang2025_he_40_300_v2.json')
    assert old.interval==(200,300) and p.interval==(40,300)
    for polarity in ('P','N'):
        assert len(p.curves[polarity]['rho'].temperature_k)==14
        for key in ('S','k','rho','sigma'):
            assert np.all(p.properties(polarity,np.array([200,260,300]))[key]==old.properties(polarity,np.array([200,260,300]))[key])
        assert p.properties(polarity,190)['k']>0

@pytest.mark.parametrize('temperature',[39.9,300.1])
def test_low_temperature_extension_does_not_extrapolate(temperature):
    with pytest.raises(ValueError):load_profile(DATA/'zhang2025_he_40_300_v2.json').properties('N',temperature)
