"""Independent geometry, passive reciprocity, work and source-domain controls."""
import numpy as np
import pytest
from tecooledmct.nonlocal_solid_network import (inputs,build,laplacian,condense,coupled,
                                             finite_die_readout)
from tecooledmct.solid_model_diagnostic import linear_control
from tecooledmct.integrated_reference import geometry
from tecooledmct.nonlocal_solid_network import ROOT,sha,read
from tecooledmct.nonlocal_solid_review import assess


@pytest.fixture(scope='module')
def operator():
    m,_=inputs();return build(m,160e-6)


def test_layered_bar_independent_series_solution():
    # Two half-cell end distances plus their exact two-material face resistance.
    area=2.;k1,k2=3.,7.;length1,length2=.4,.8
    g0=k1*area/(length1/2);g1=area/(length1/(2*k1)+length2/(2*k2));g2=k2*area/(length2/2)
    L=laplacian(2,2,[0],[1],[g1],[0,1],[0,1],[g0,g2]);_,_,H,K=condense(L,2)
    expected=area/(length1/k1+length2/k2)
    assert K==pytest.approx(expected*np.array([[1,-1],[-1,1]]),rel=1e-12)
    assert H.sum(1)==pytest.approx(np.ones(2),abs=1e-12)


def test_unit_temperature_passivity_reciprocity_and_sign(operator):
    K=operator['K'];H=operator['H']
    assert K==pytest.approx(K.T,abs=1e-14)
    assert K.sum(1)==pytest.approx(np.zeros(4),abs=1e-12)
    assert np.linalg.eigvalsh(K).min()>-1e-12
    assert np.min(H)>-1e-12 and np.max(H)<1+1e-12
    for i in range(4):
        t=np.eye(4)[i];q=K@t
        assert q[i]>0 and abs(q.sum())<1e-12
        assert np.max(q[np.arange(4)!=i])<1e-12
        assert K@(-t)==pytest.approx(-q,abs=1e-14)
    assert -K[0,2]>0 # genuinely nonlocal hot-to-second-intermediate coupling


def test_joule_condensation_conserves_electrical_work(operator):
    generated=operator['source_per_A2'].sum()+operator['port_source_per_A2'].sum()
    assert generated==pytest.approx(sum(operator['Cu_R_ohm']),abs=1e-10)
    assert operator['joule_port_per_A2'].sum()==pytest.approx(generated,abs=1e-10)
    assert min(operator['joule_port_per_A2'])>=0


def test_off_recovers_unchanged_original_model_and_side_leg(operator):
    a=coupled(operator,on=False);b=linear_control(geometry(),300.1148977882757)
    assert a['temperatures_k'][:5]==pytest.approx(b['temperatures_k'],abs=2e-6)
    assert a['module_voltage_v']==pytest.approx(b['voltage_v'],abs=2e-8)
    assert abs(a['global_energy_residual_w'])<1e-12


def test_uniform_zero_current_control(operator):
    a=coupled(operator,current=0.,load=0.)
    assert a['temperatures_k']==pytest.approx([300.1148977882757]*6,abs=1e-12)
    assert a['module_voltage_v']==pytest.approx(0.,abs=1e-12)
    assert a['bath_out_w']==pytest.approx(0.,abs=1e-12)


@pytest.mark.parametrize('kwargs',[{'current':-.1},{'current':1.1},{'load':-.001},
                                  {'hot':float('nan')},{'hot':170.},{'hot':391.}])
def test_bad_coupled_inputs_reject(operator,kwargs):
    with pytest.raises(ValueError):coupled(operator,**kwargs)


def test_finite_die_zero_heat_and_nonconstant_source_law():
    assert finite_die_readout(260.,0.,1e-6,.0002)['mean_k']==pytest.approx(260.,abs=1e-12)
    result=finite_die_readout(260.,.002,1e-6,.0002)
    assert 260.<result['mean_k']<result['top_k']<261.
    with pytest.raises(ValueError):finite_die_readout(400.,.002,1e-6,.0002)


def test_disconnected_or_nonpositive_network_fails():
    with pytest.raises(ValueError):laplacian(2,1,[0],[1],[-1.],[0],[0],[1.])
    with pytest.raises(ValueError):laplacian(2,1,[],[],[],[0],[0],[1.])


def test_side_contact_stage_work_and_coupled_heat_balance(operator):
    a=coupled(operator)
    for st in a['stage_budget']:
        assert st['qh_w']-st['qc_w']==pytest.approx(.1*st['voltage_v']+st['side_contact_in_w'],abs=1e-12)
    assert a['stage_budget'][2]['qc_w']==pytest.approx(.002,abs=1e-12)
    assert a['stage_budget'][2]['side_contact_in_w']>0
    assert a['bath_out_w']==pytest.approx(.002+.1*a['module_voltage_v'],abs=1e-12)
    assert sum(a['network_into_ports_w'])==pytest.approx(sum(a['route_Joule_w']),abs=1e-12)
    assert max(abs(np.array(a['free_node_residuals_w'])))<1e-12
    q=a['network_into_ports_w'];st=a['stage_budget']
    assert st[0]['qc_w']==pytest.approx(st[1]['qh_w']+q[1],abs=1e-12)
    assert st[1]['qc_w']==pytest.approx(st[2]['qh_w']+q[2],abs=1e-12)


def test_archived_geometry_coefficients_and_registration_are_still_target_blind(operator):
    folder=ROOT/'data/nonlocal_solid_network_20261031';frozen=read(folder/'frozen_operators.json')
    for group in ('source_sha256',):
        for name,h in frozen[group].items():assert sha(ROOT/name)==h
    for name,h in frozen['geometry_audit']['input_sha256'].items():assert sha(ROOT/name)==h
    for name,h in frozen['operator_sha256'].items():assert sha(folder/name)==h
    assert frozen['registration']==(ROOT/'docs/NONLOCAL_PORT_NETWORK_20261031.md').read_text().split('## Results')[0]
    saved=read(folder/'operator_160um.json')
    assert operator['K']==pytest.approx(np.array(saved['K_W_K']),abs=1e-12)
    assert operator['Cu_R_ohm']==pytest.approx(saved['Cu_R_ohm'],abs=1e-12)


def test_saved_predictions_conserve_and_keep_failures_visible():
    folder=ROOT/'data/nonlocal_solid_network_20261031';d=read(folder/'diagnostic.json')
    for name,h in read(folder/'checksums.json')['artifact_sha256'].items():assert sha(folder/name)==h
    for name,h in d['reference']['input_sha256'].items():assert sha(ROOT/name)==h
    for row in d['levels']:
        assert abs(row['global_energy_residual_w'])<1e-9
        assert row['max_internal_heat_residual_w']<1e-9
        assert max(abs(np.array(row['free_node_residuals_w'])))<1e-9
        for st in row['stage_budget']:assert abs(st['energy_residual_including_side_w'])<1e-9
    for row in d['path_comparison']:assert row['area_m2']>0
    review=read(folder/'all_port_review.json')
    for name,h in review['input_sha256'].items():assert sha(folder/name)==h
    for name,h in review['source_sha256'].items():assert sha(ROOT/name)==h
    for key,value in assess(d).items():assert review[key]==value
    assert review['registered_sensitivity_exceeded'] # P174 side-port sensitivity must not disappear
    assert not review['physical_mean_to_contact_closure_qualified'] and not review['new_mesh_release']
    assert not d['identifiability']['causal_attribution_complete'] and not d['Rev3_modified']


def test_quiet_cold_and_sharp_screen_cannot_hide_sensitive_side_port():
    r={'levels':[{'temperatures_k':[300,280,270,260], 'network_into_ports_w':[-1,.3,.6,.1]},
                 {'temperatures_k':[300,280,270,260], 'network_into_ports_w':[-1,.3,.6,.2]}],
       'discretization':{'path_changes':[{'coarse_fine_relative_power_change':.01}]}}
    a=assess(r)
    assert not a['sharp_cut_screen_exceeded'] and a['all_port_screen_exceeded']
    assert a['registered_sensitivity_exceeded']


def test_same_cut_signed_uniform_heat_and_real_zero_gaps(operator):
    from tecooledmct.nonlocal_solid_study import cuts,planes
    m,_=inputs();z=planes(m);delta=-operator['center'][:,2] # +z conduction
    positive=cuts(operator,delta,z);negative=cuts(operator,-delta,z)
    for a,b in zip(positive,negative):
        for bid in a['bodies']:
            assert a['bodies'][bid]['up_w']>0
            assert a['bodies'][bid]['up_w']==pytest.approx(-b['bodies'][bid]['up_w'],abs=1e-14)
    assert positive[2]['bodies']=={} # no invented path through third-stage void


def test_uniform_temperature_local_joule_analytical_superposition(operator):
    # At zero port temperature difference, total heat leaving equals Cu I²R;
    # internal nodes solve L_ii*u=j independently of the stage equations.
    n=operator['nodes'];u=operator['u_per_A2'];source=operator['source_per_A2']
    assert operator['L'][:n,:n]@u==pytest.approx(source,abs=1e-11)
    q=-operator['B'].T@u+operator['port_source_per_A2']
    assert sum(q)==pytest.approx(sum(operator['Cu_R_ohm']),abs=1e-10)
