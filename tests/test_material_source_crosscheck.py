"""Independent source-figure anchors, not identities of the interpolation code."""
import pytest
from tecooledmct.material_profiles import DATA,load_profile


def test_thermopower_and_resistivity_agree_with_published_power_factor_panel():
    p=load_profile(DATA/'zhang2025_he_40_300_v2.json')
    # Original paper Fig. 2c red N-HE-1 / Fig. 3c red P-HE at 300 K:
    # approximately 48 / 38 microW cm^-1 K^-2, i.e. .0048 / .0038 W m^-1 K^-2.
    # Bounds reflect plot reading, not experimental/device confidence intervals.
    for polarity,reference in (('N',.0048),('P',.0038)):
        v=p.properties(polarity,300)
        assert v['S']**2/v['rho']==pytest.approx(reference,abs=.0003)
    assert p.properties('N',40)['S']==pytest.approx(-40e-6,abs=6e-6)
