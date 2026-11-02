"""Independent vertical-fit counterexample and selected matching requirements."""
import json,math
from pathlib import Path
import pytest
from tecooledmct.tec_assembly_v3_fit import NOMINAL,ERRORS,fixed_tab_fits,matching_plan,sweep
from tecooledmct.tec_assembly_v3 import design
from tecooledmct.tec_assembly_v3_audit import tolerances
@pytest.mark.parametrize('error',[.018,-.018,.036,-.036])
def test_original_fixed_tab_still_fails(error):assert not fixed_tab_fits(error)
def test_original_counterexample_independent():
    assert .025-.018==pytest.approx(.007)
    assert .007<.015
@pytest.mark.parametrize('delta',[.018,-.018,.036,-.036])
def test_measured_land_matching_accepts_actual_offset(delta):
    m=list(NOMINAL);m[1]+=delta
    p=matching_plan(m);assert p['foot_mating_planes_mm'][1]-m[1]==pytest.approx(.020)
    assert p['finished_joint_interval_mm']==pytest.approx([.015,.025])
def test_all_registered_corner_and_heel_envelopes():
    r=sweep(design());assert r['true_land_corners']==128 and r['gap_error_corners']==16
    assert r['full_measured_enclosure_stroke_reserve_mm']==pytest.approx(.018)
    assert r['minimum_straight_mm']>=.65
    assert len(r['heel_envelopes'])==4
@pytest.mark.parametrize('fault',['land','stroke','profile','force','nonfinite','missing'])
def test_no_silent_forcefit_or_tolerance_relaxation(fault):
    m=list(NOMINAL);kw={}
    if fault=='land':m[0]+=.142
    elif fault=='stroke':m[1]+=.018;kw['stroke']=.010
    elif fault=='profile':kw['errors']={**ERRORS,'relative_profile_parallelism':.003}
    elif fault=='force':kw['clamp_force_N']=.011
    elif fault=='nonfinite':m[0]=math.nan
    elif fault=='missing':m.pop()
    with pytest.raises(ValueError):matching_plan(m,**kw)
def test_outer_finish_uncertainty_not_omitted():
    r=next(q for q in tolerances() if q['check']=='metallized_TEC_height')
    assert [r['lower_bound'],r['upper_bound']]==pytest.approx([3.664,3.944])
def test_nominal_source_and_step_unchanged():
    root=Path(__file__).resolve().parents[1];b=root/'data/synthetic_v3_assembly_20261102'
    assert json.loads((b/'source_final/design.json').read_text())==json.loads(json.dumps(design()))
    import hashlib
    assert hashlib.sha256((b/'cad_02/synthetic_v3_mm.step').read_bytes()).hexdigest()=='5e46c10fb75713a9dffbc97c44a2b94ca23bee14a93df7f4c0c7c915eb761a73'


@pytest.mark.parametrize('stroke',[float('nan'),float('inf'),0,-.3,.301])
def test_nonfinite_or_unregistered_tool_limits_reject(stroke):
    with pytest.raises(ValueError):matching_plan(NOMINAL,stroke=stroke)
