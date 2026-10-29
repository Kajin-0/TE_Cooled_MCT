"""G2d split discipline, physical balances, source guards and identifiability."""
import ast
import json
from pathlib import Path
import numpy as np
import pytest
from tecooledmct.g2d_data import DATA,ROOT,points,residual,preserve
from tecooledmct.g2d_network import baseline,constant,local_leg
from tecooledmct.g2d_analysis import jacobian,predict
from tecooledmct.g2d_fem import constant_profile
from tecooledmct.material_profiles import load_profile,DATA as MATERIAL_DATA


def test_split_is_preserved_and_conditions_are_explicit():
    original=json.loads((ROOT/'data/g2c/oem2019_curves_v1.json').read_text())['points']
    all_ids=[]
    for split,currents in [('calibration_reserved',{.2,.6,1.}),('validation_holdout',{.1,.4,.8})]:
        raw=json.loads((DATA/(split+'.json')).read_text())['points'];all_ids += [r['id'] for r in raw]
        assert {r['current_a'] for r in raw}==currents
        assert all(r['split']==split for r in raw)
        selected=points(split)
        assert all(r['hot_k']==300 and r['ambient']=='vacuum' and r['unit'] in ('K','V') for r in selected)
        assert {r['id'] for r in selected}=={r['id'] for r in original if r['split']==split and r['hot_k']==300 and r['ambient']=='vacuum'}
    assert len(all_ids)==len(set(all_ids))==len(original)


def test_freeze_precedes_holdout_and_fit_uses_calibration_only_weights():
    # Guard the runner's data flow, including accidental holdout-derived weights.
    source=(ROOT/'tecooledmct/g2d_analysis.py').read_text();ast.parse(source)
    assert source.index("dump(out/'frozen_fit.json',frozen)") < source.index("hold=points('validation_holdout')")
    assert "bounds=np.array([r['value_reading_bound'] for r in cal])" in source
    assert "predict(cal,p,counts)-obs" in source


@pytest.mark.parametrize('current,load',[(0,0),(.1,0),(.2,.1),(.6,.2),(1.,.41),(-.1,.002)])
def test_constant_network_conserves_each_stage_and_external_bath(current,load):
    p={**baseline(),'bath_r':2.,'q_extra_w':.003,'re_area':2e-10,'rth_area':2e-6}
    r=constant(current,load,parameters=p)
    assert r['max_stage_energy_error_w']<1e-10
    assert abs(r['global_energy_error_w'])<1e-10
    assert r['max_cascade_residual_w']<1e-10
    assert r['plate_temperatures_k'][0]-300==pytest.approx(2*r['stages'][0]['qh_w'],abs=1e-10)
    assert r['stages'][-1]['qc_w']==pytest.approx(load+.003,abs=1e-10)


def test_topology_and_hypothesis_bounds_are_not_continuous_fit_variables():
    for counts in ((28.,12.,4.),(28,12,5),(-1,40,5)):
        with pytest.raises(ValueError):constant(.1,0,counts=counts)
    with pytest.raises(ValueError):constant(.1,0,parameters={**baseline(),'rho_scale':-1})


def test_distinct_parameters_have_exact_geometry_material_degeneracy():
    rows=points('calibration_reserved');p=baseline();c=1.1
    q={**p,'leg_aspect':c,'rho_scale':1/c,'k_scale':c}
    assert np.max(np.abs(predict(rows,p,(28,12,4))-predict(rows,q,(28,12,4))))<1e-8
    # Finite-difference rank alone can overstate a weak direction; exact null above
    # is the structural evidence, tested independently of rank threshold.
    a=jacobian(rows,p);b=jacobian(rows,p,step=5e-4)
    assert a['rank']==b['rank']==8 and a['condition_number'] is None
    assert a['singular_values'][-1]/a['singular_values'][0]<1e-7


def test_residuals_refuse_mismatched_temperature_load_and_environment():
    row=points('validation_holdout')[0];p={k:row[k] for k in ('current_a','load_w','hot_k','ambient')};p[row['field']]=row['value']
    r=residual(row,p);assert r['signed_residual']==0 and not r['device_accuracy_proven']
    for key,value in [('hot_k',295),('load_w',.123),('ambient','dry_N2'),('current_a',.3)]:
        with pytest.raises(ValueError):residual(row,{**p,key:value})


def test_local_bvp_reproduces_independent_constant_law_and_fails_closed():
    profile=constant_profile();j=2e5;length=.001;hot,cold=295.,280.
    for polarity in ('P','N'):
        r=local_leg(profile,polarity,hot,cold,j,length);p=profile.properties(polarity,hot)
        # Integral E = J*rho*L + S*(Tc-Th), independent of internal Joule T(x).
        expected=j*p['rho']*length+p['S']*(cold-hot)
        assert r['electric_integral_v']==pytest.approx(expected,rel=1e-8)
        assert abs(r['energy_error_w_m2'])<1e-5
    sourced=load_profile(MATERIAL_DATA/'zhang2025_he_40_300_v2.json')
    with pytest.raises(ValueError):local_leg(sourced,'P',300.01,290.,j,length)


def test_prior_sources_and_all_accepted_evidence_are_unchanged():
    assert preserve()['g2c_unchanged']
