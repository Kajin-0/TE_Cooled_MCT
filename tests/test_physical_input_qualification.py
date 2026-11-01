"""Independent controls for local target derivatives and evidence qualification."""
from copy import deepcopy
import numpy as np
import pytest

from tecooledmct.physical_input_qualification import (
    ROOT, OLD, NOTE, FACTORS, STEPS, TOL, scenario, balance, implicit, partial,
    stable, valid_bracket, target, read, sha)
from tecooledmct.integrated_reference import geometry

DATA=ROOT/'data/physical_input_qualification_20261101'


def test_independent_implicit_chain_rule_and_units():
    # Exact analytic target for T=300-400I+20p, P=2I^2+3p.
    # At p=1, T=200 gives I=.3; no TEC solver or numerical derivative involved.
    r=implicit(20.,3.,-400.,1.2,3.18)
    assert r['current_A_per_log_factor']==pytest.approx(.05)
    assert r['power_W_per_log_factor']==pytest.approx(3.06)
    eps=1e-5
    exact=lambda p:2*((100+20*p)/400)**2+3*p
    assert r['power_W_per_log_factor']==pytest.approx((exact(1+eps)-exact(1-eps))/(2*eps),rel=1e-9)
    for TI,P in ((0,1),(1,1),(-1,0),(float('nan'),1)):
        with pytest.raises(ValueError):implicit(1,1,TI,1,P)


@pytest.mark.parametrize('f',FACTORS)
def test_fixed_conditions_and_registered_factor_guards(f):
    s=scenario(.29,f,1.01)
    assert s.heat_sink_k_w==2 and s.ambient_k==300 and s.detector_bias_w==.002
    assert s.cavity_pressure_pa==s.cap_emissivity==s.window_thermal_emissivity==0
    assert s.material_model=='zhang2025_nonlinear' and s.detector_absorbed_w==0
    assert getattr(s,f)==1.01
    for x in (0.,1.02,float('nan')):
        with pytest.raises(ValueError):scenario(.29,f,x)
    with pytest.raises(ValueError):scenario(.24,f)
    with pytest.raises(ValueError):scenario(.29,'cu_wire_conductance_scale')


def row(i,T,status='ACCEPTED'):
    return {'case':{'id':str(i),'current_A':i},'status':status,'audit':{'Tdie_K':T}}


def test_target_requires_real_admitted_bracket_no_gap_or_nonmonotone_bridge():
    lo,hi=row(.28,201),row(.3,199)
    assert valid_bracket(lo,hi)
    assert not valid_bracket(hi,lo)
    assert not valid_bracket(lo,row(.3,199,'REJECTED'))
    calls=[]
    def rejected(c):calls.append(c);return dict(case=c,status='REJECTED')
    r=target(lo,hi,[{'id':'m'}],rejected)
    assert r['status']=='STOP' and len(calls)==1 and calls[0]['current_A']==pytest.approx(.29)
    def nonmonotone(c):return dict(case=c,status='ACCEPTED',audit={'Tdie_K':202})
    assert target(lo,hi,[{'id':'m'}],nonmonotone)['status']=='STOP'
    assert target(lo,row(.3,199,'REJECTED'),[],rejected)['attempts']==[]
    assert target(lo,hi,[],rejected)['status']=='STOP'


def test_step_stability_uses_actual_central_partials():
    for h in STEPS:
        p=partial({'Tdie_K':200-3*h,'terminal_W':1+2*h},
                  {'Tdie_K':200+3*h,'terminal_W':1-2*h},h)
        assert p['Tdie_K']==pytest.approx(3.)
        assert p['terminal_W']==pytest.approx(-2.)
    assert stable(p,p)
    assert not stable(p,{'Tdie_K':4.,'terminal_W':-2.})


def test_independent_audit_detects_missing_au_multiplier_and_wrong_work():
    ref=read(OLD/'cases.json')['target_R2_step8'];g=geometry()
    s=scenario(ref['case']['current_A']);r=deepcopy(ref['result'])
    a=balance(s,g,r)
    assert abs(a['net_ambient_rejection_W']-a['terminal_W']-.002)<1e-8
    with pytest.raises(AssertionError):balance(scenario(s.current_a,'au_wire_conductance_scale',1.01),g,r)
    r['terminal_electrical_power_w']+=1e-5
    with pytest.raises(AssertionError):balance(s,g,r)


def test_frozen_registration_and_every_actual_result():
    reg=read(DATA/'registration.json')
    assert reg['protocol']==NOTE.read_text().split('## Results')[0]
    assert reg['producer_sha256']==sha(DATA/'producer.py.source')==sha(ROOT/'tecooledmct/physical_input_qualification.py')
    assert reg['maximum_calls']==150 and reg['fractional_steps']==list(STEPS)
    assert reg['factors']==list(FACTORS)
    for p,h in reg['input_sha256'].items():assert sha(ROOT/p)==h
    cases=read(DATA/'cases.json');e=read(DATA/'execution.json');g=geometry()
    assert len(cases)==e['recorded_calls']<=150 and e['seconds']<=600
    for r in cases.values():
        c=r['case']
        if r['status']=='ACCEPTED':
            a=balance(scenario(c['current_A'],c.get('factor'),c.get('multiplier',1)),g,r['result'])
            # Python 3.12+ sums floats with compensation; CI Python 3.11 sums
            # serially. Reconstructed work can differ by one ULP, not physics.
            for key,value in r['audit'].items():
                if isinstance(value,bool):assert a[key]==value
                else:np.testing.assert_allclose(a[key],value,rtol=0,atol=5e-15)
            assert a['assumed_continuation']
        elif r['status']=='REJECTED':assert r['diagnostics'] and not r['diagnostics']['candidate_is_accepted']
        else:assert r['status']=='NOT RUN' and r['reason']
    for r in read(DATA/'targets.json').values():
        assert r['status']=='PASS'  # Intended complete scope; a STOP must be reported and retained.
        cold=cases[r['cold_side_case']]
        assert 0<=200-cold['audit']['Tdie_K']<=TOL
        a,b=[cases.get(k,read(OLD/'cases.json').get(k)) for k in r['initial_bracket']]
        assert valid_bracket(a,b)
        for k in r['attempts']:
            mid=cases[k];assert mid['case']['current_A']==.5*(a['case']['current_A']+b['case']['current_A'])
            if mid['audit']['Tdie_K']>200:a=mid
            else:b=mid
        assert r['final_bracket']==[a['case']['id'],b['case']['id']]


def test_constant_property_geometry_gauge_and_its_tangent_are_independent():
    # Arbitrary SI material values, not calibrated to a target or manufacturer.
    n,L,A=28,1.07e-3,.16e-6
    def endpoints(g,r,k):
        R=n*L/(A*g)*(7e-6+9e-6)*r
        K=n*A*g/L*(1.3+1.5)*k
        alpha=n*(180e-6+160e-6)
        I,Th,Tc=.3,301.,240.
        qc=alpha*I*Tc-.5*I*I*R-K*(Th-Tc)
        V=I*R+alpha*(Th-Tc)
        return np.array([R,K,qc,V,alpha*I*Th+.5*I*I*R-K*(Th-Tc)])
    base=endpoints(1,1,1)
    assert base[4]-base[2]==pytest.approx(.3*base[3])
    for c in (.7,1.01,1.7):np.testing.assert_allclose(endpoints(c,c,1/c),base,atol=1e-14)
    h=1e-5
    dg=(endpoints(1+h,1,1)-endpoints(1-h,1,1))/(2*h)
    dk=(endpoints(1,1,1+h)-endpoints(1,1,1-h))/(2*h)
    dr=(endpoints(1,1+h,1)-endpoints(1,1-h,1))/(2*h)
    np.testing.assert_allclose(dg,dk-dr,rtol=1e-8,atol=1e-9)


def test_source_domains_and_actual_target_comparison_are_not_physical_validation():
    a=read(DATA/'evidence_analysis.json')
    assert a['all_actual_target_chain_rules_pass'] and a['physical_validation'] is False
    assert a['native_gas_nonlocal_contact_matched_target_sensitivity']=='NOT RUN'
    for r in a['sensitivities']:
        assert r['chain_rule_agrees'] and r['signal_resolution']=='RESOLVED'
        assert r['actual_power_derivative_error_W_per_log_factor']<=r['actual_derivative_tolerance_W_per_log_factor']
        assert 0<r['conditional_fractional_measurement_TARGET']<=.01
    p=read(ROOT/'data/g2c/zhang2025_he_40_300_v2.json')
    s={r['id']:r for r in read(DATA/'source_audit.json')}
    assert s['Zhang2025']['sha256']==p['original_pdf_sha256']
    assert p['id']=='zhang2025_he_digitized_40_300_v2r1' and p['valid_temperature_k']==[40,300]
    assert all(not v['network_retrieval_this_milestone'] for v in s.values())
    reg=read(ROOT/'fem/results/geometry_rebaseline_20261030/registry_snapshot.json')
    assert s['VIGO2024']['sha256']==reg['sources']['vigo']['sha256']
    assert s['TEC2019']['sha256']==reg['sources']['tec']['sha256']
    assert s['Huber2019']['sha256']==read(ROOT/'data/g3b/source_review.json')['gas_conductivity']['retrieved_pdf_sha256']
    ledger=read(DATA/'checksums.json')
    for p,h in ledger['artifact_sha256'].items():assert sha(DATA/p)==h
    assert sha(ROOT/ledger['projection_source_path'])==ledger['projection_sha256']


def test_solver_free_projection_reproduces_values_and_same_environment_plot(tmp_path,monkeypatch):
    import shutil
    from tecooledmct import physical_input_evidence as p
    for f in ('cases.json','targets.json','derivatives.json','controls.json'):
        shutil.copyfile(DATA/f,tmp_path/f)
    # CI need not have the untracked copyrighted source PDFs; their inspected
    # identities were cross-checked against versioned source registries above.
    monkeypatch.setattr(p,'sources',lambda:read(DATA/'source_audit.json'))
    p.project(tmp_path)
    assert read(tmp_path/'evidence_analysis.json')==read(DATA/'evidence_analysis.json')
    first=sha(tmp_path/'conditional_sensitivity.png')
    p.project(tmp_path)
    assert sha(tmp_path/'conditional_sensitivity.png')==first
