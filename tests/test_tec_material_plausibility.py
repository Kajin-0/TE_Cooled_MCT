"""Engineering-hypothesis transport and condition-matching gates, no new FEM."""
from copy import deepcopy
import hashlib
import json

import numpy as np
import pytest

from tecooledmct import tec_material_plausibility as m
from tecooledmct import graded_tec,nonlinear_tec
from tecooledmct.integrated_reference import geometry,solve

BASE=m.ROOT/'data/tec_material_plausibility_20261101'


@pytest.mark.parametrize('hyp',m.HYPOTHESES)
@pytest.mark.parametrize('polarity',['P','N'])
def test_scaled_active_law_reciprocal_thomson_and_source_boundary_semantics(hyp,polarity):
    scales=m.HYPOTHESES[hyp];t=np.array([180.,200.,280.,300.-1e-6,300.,300.+1e-6,390.])
    p=m.material_properties(polarity,t,scales);native=nonlinear_tec.properties(polarity,t,scales)
    assert p['sigma']*p['rho']==pytest.approx(np.ones(len(t)),abs=2e-16)
    assert p['thomson_v_k']==pytest.approx(t*native['S_prime'],abs=1e-18)
    for k in ('S','rho','k'):assert p[k]==pytest.approx(native[k],rel=1e-14)
    left=graded_tec.source().curves[polarity]['S'].slope(300.)*scales[0]
    assert p['S_prime'][4]==pytest.approx(left)
    assert p['S_prime'][5]==p['S_prime'][6]==pytest.approx(.25*left)
    assert np.all(p['rho']>0) and np.all(p['k']>0)
    assert np.all(p['S']*(1 if polarity=='P' else -1)>0)


@pytest.mark.parametrize('temp',[39.9,390.1,float('nan')])
def test_hypothesis_property_domain_rejects_without_clamping(temp):
    with pytest.raises(ValueError):m.material_properties('N',temp,(1.,1.,1.))


@pytest.mark.parametrize('hyp',m.HYPOTHESES)
def test_constant_law_nonlinear_stage_matches_independent_analytic_energy(monkeypatch,hyp):
    scales=m.HYPOTHESES[hyp]
    def constant(pol,t,sc):
        S=(160e-6 if pol=='P' else -170e-6)*sc[0];rho=(1/1.4e5 if pol=='P' else 1/1.655e5)*sc[1];k=1.5*sc[2]
        return {name:np.full_like(t,v) for name,v in {'S':S,'rho':rho,'k':k,'S_prime':0.,'rho_prime':0.,'k_prime':0.}.items()}
    monkeypatch.setattr(nonlinear_tec,'properties',constant)
    g=geometry()['stages'][0];n,A,L=g['couples'],g['leg_area_m2'],g['leg_length_m'];I=.2;hot=290.;cold=260.
    a=n*330e-6*scales[0];R=n*L/A*(1/1.4e5+1/1.655e5)*scales[1];K=n*A/L*3*scales[2]
    for current in (I,0.,-I):
        r=nonlinear_tec.Transport().stage(g,hot,cold,current,alpha_scale=scales[0],rho_scale=scales[1],k_scale=scales[2])
        assert r['qc_w']==pytest.approx(a*current*cold-.5*current**2*R-K*(hot-cold),abs=1e-10)
        assert r['voltage_v']==pytest.approx(current*R+a*(hot-cold),abs=1e-11)
        assert abs(r['qh_w']-r['qc_w']-current*r['voltage_v'])<1e-9


def test_engineering_ZT_factors_are_not_claimed_measured_grades():
    c=m.characterization();n=np.array(c['hypotheses']['nominal']['equal_area_couple_ZT'])
    for h,factor in [('lower',.5625),('higher',1.890625)]:
        assert np.array(c['hypotheses'][h]['equal_area_couple_ZT'])/n==pytest.approx(np.full(len(n),factor))
    assert c['source']['commercial_grade_matched'] is False
    assert c['source']['source_id'].endswith('v2r1')


def test_registered_scenarios_are_fixed_no_fit_and_no_gas_radiation():
    o=m.read(m.ROOT/'data/g2c/oem2019_curves_v1.json');cases=m.registered_cases(o)
    assert len(cases)==181 and len({c['id'] for c in cases})==181
    for c in cases:
        s=m.scenario(c);s.validate()
        assert s.cavity_pressure_pa==s.cap_emissivity==s.window_thermal_emissivity==s.heat_sink_k_w==0
    assert sum(c['group']=='OEM_literal' for c in cases)==60
    assert sum(c['group']=='core' for c in cases)==66
    assert sum(c['group']=='G1_control' for c in cases)==11


def test_wire_off_removes_electrical_paths_and_attach_leaves_module_observables_invariant():
    g=deepcopy(geometry());g['wires']=[]
    c=m.case('test','nominal',.2,.1,300.15);r1=solve(m.scenario(c),g)
    c2=dict(c,attach_k_W_mK=.5);r2=solve(m.scenario(c2),g)
    assert r1['terminal_voltage_v']==r1['module_voltage_v']
    assert r1['MCT_die_k']!=pytest.approx(r2['MCT_die_k'],abs=.1)
    assert r1['temperatures_k']['cold_ceramic']==pytest.approx(r2['temperatures_k']['cold_ceramic'],abs=1e-6)
    assert r1['module_voltage_v']==pytest.approx(r2['module_voltage_v'],abs=1e-7)
    assert r1['stage_budget'][2]['qc_w']==pytest.approx(.1,abs=1e-8)


def test_saved_results_count_conserve_domains_preserve_rejects_and_freeze_baselines():
    reg=m.read(BASE/'registration.json');results=m.read(BASE/'cases.json');summary=m.read(BASE/'summary.json')
    assert reg['registration']==m.NOTE.read_text().split('## Results')[0]
    assert reg['study_code_sha256']==m.sha(m.__file__)
    for p,h in reg['input_sha256'].items():assert m.sha(m.ROOT/p)==h
    assert len(results)==len(reg['cases'])==summary['cases']==181
    assert sum(summary[k] for k in ('accepted','rejected','not_run'))==181
    for c in reg['cases']:
        r=results[c['id']]
        if r['status']=='ACCEPTED':
            out=r['result'];s=r['summary']
            assert out['material_model']==c['material_model']
            assert abs(out['temperatures_k']['hot_ceramic']-c['hot_K'])<1e-7
            assert abs(out['global_energy_residual_w'])<1e-8
            assert out['max_node_balance_residual_w']<1e-8
            for stage in out['stage_budget']:assert abs(stage['qh_w']-stage['qc_w']-c['current_A']*stage['voltage_v'])<1e-9
            assert 180<=s['local_leg_min_K']<=s['local_leg_max_K']<=390
            assert s['Qc_cold_W']==out['stage_budget'][2]['qc_w']
            assert not s['material_grade_identified']
        elif r['status']=='REJECTED':
            assert r['reason'] and not r['diagnostics']['candidate_is_accepted']
            assert 'last_candidate_temperatures_k' in r['diagnostics']
            assert 'optimizer' in r['diagnostics'] and 'physical_domain' in r['diagnostics']
    tr=m.read(BASE/'transport_verification.json')
    assert tr['passed'] and len(tr['rows'])==6
    assert max(r['Qc_absolute_error_W'] for r in tr['rows'])<3e-8


def test_OEM_comparison_uses_actual_conditions_not_package_or_fresh_holdout():
    d=m.read(BASE/'oem_comparison.json');assert d['attach_invariance_passed']
    assert d['Qmax']==d['DeltaTmax']=='NOT RUN'
    assert d['historical_G2d_residual_current_validation'] is False
    for r in d['rows']:
        assert not r['fresh_blind_holdout'] and not r['measured_grade_match']
        if r['panel']!='300K_vacuum':assert r['status']=='NOT COMPARABLE'
        if r['status'].startswith('CONDITIONAL'):
            assert r['literal_hot_K']==300.15 and r['assumed_continuation_used']
            assert r['strict_measured_source_comparison'].startswith('NOT COMPARABLE')
            assert r['absolute_difference']==pytest.approx(abs(r['model_value']-r['source_value']))
            assert r['absolute_relative_difference']==pytest.approx(abs(r['model_value']/r['source_value']-1))


def test_target_claims_require_real_admitted_points_and_figure_artifacts_are_traceable():
    summary=m.read(BASE/'summary.json');cases=m.read(BASE/'cases.json');reg=m.read(BASE/'registration.json')
    for key,target in summary['targets'].items():
        for case_id in target['target_hit_case_ids']:
            r=cases[case_id];c=next(c for c in reg['cases'] if c['id']==case_id)
            assert r['status']=='ACCEPTED' and r['summary']['Tdie_K']<=200
            assert c['hot_K']==300 and c['die_load_W']==.002 and c['group']=='core'
        for case_id in target['strict_measured_domain_target_ids']:
            assert cases[case_id]['summary']['local_leg_max_K']<=300
    assert summary['targets']['nominal_wires_ON']['target_demonstrated_in_registered_reduced_assumptions']
    assert not summary['targets']['lower_wires_ON']['target_demonstrated_in_registered_reduced_assumptions']
    f=m.read(BASE/'figure_provenance.json')
    assert f['source_sha256']==m.sha(m.ROOT/'tecooledmct/tec_material_plausibility_figures.py')
    for name,digest in f['input_sha256'].items():assert m.sha(m.ROOT/name)==digest
    for name,digest in f['figures'].items():assert m.sha(BASE/name)==digest
    for name,digest in m.read(BASE/'checksums.json')['artifact_sha256'].items():assert m.sha(BASE/name)==digest
