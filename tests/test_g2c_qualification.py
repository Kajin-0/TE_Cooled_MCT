import json
import pytest
from tecooledmct.g2c_qualification import Contact,holdout_compare
from tecooledmct.material_profiles import DATA

def test_contact_dimensions_and_zero_limit_are_explicit():
    p=Contact(1e-9,1e-5,10e-6).layer_parameters(.4e-3**2)
    assert p['electrical_resistance_ohm']==pytest.approx(.00625)
    assert p['layer_sigma_s_m']==pytest.approx(1e4)
    assert p['layer_k_w_mk']==pytest.approx(1)
    assert Contact().layer_parameters(1)['layer_sigma_s_m'] is None
    with pytest.raises(ValueError):Contact(-1,0)

def test_oem_split_and_environment_not_silently_mixed():
    d=json.loads((DATA/'oem2019_curves_v1.json').read_text())
    assert len(d['panels'])==4 and d['curve_status']=='DIGITIZED'
    assert d['panels'][0]['qmax_w']==.51
    assert all(r['value_reading_bound']>0 and r['current_reading_bound_a']>0 for r in d['points'])
    prediction={'current_a':.1,'load_w':0,'delta_t_k':38.9,'voltage_v':.57,'origin':'test fixture, not FEM evidence'}
    r=holdout_compare([prediction])
    assert len(r['comparisons'])==2 and not r['device_validation_passed'] and r['calibration_points_used']==0
    assert not holdout_compare([{**prediction,'load_w':.002}])['comparisons']
    assert not holdout_compare([{**prediction,'hot_k':295}])['comparisons']
    with pytest.raises(ValueError):holdout_compare([{**prediction,'ambient':'dry_N2','hot_k':323}])


def test_family_objective_is_not_a_likelihood_or_identification():
    from tecooledmct.g2c_qualification import family_objective
    r=family_objective([])
    assert r['observations']==0 and r['score_sum_squared_reading_bound_residual']==0
    assert not r['statistical_likelihood'] and not r['fit_performed']
    assert not r['full_family_coverage_established']
