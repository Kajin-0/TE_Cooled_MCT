import copy
import json
import numpy as np
import pytest

from tecooledmct import corrected_exchange as ce
from tecooledmct import exchange_geometry as eg
from tecooledmct.fem_g3b_exchange import radiation_matrix,SIGMA
from tecooledmct.integrated_reference import Scenario,solve


@pytest.fixture(scope='module')
def operator():return ce.build(1024)


def test_source_native_faces_and_proxy_scope(operator):
    native=operator['specification']['native_audit']
    assert sum(native['native_cap_tet_counts'].values())==8143
    assert native['all_audited_exterior_faces_have_one_owner']
    assert len(native['native_top_faces'])==5
    assert 'proxy' in operator['scope']
    assert operator['ray_audit']['unclosed_rays']==0
    assert operator['ray_audit']['raw_row_closure_error']==0
    assert operator['ray_audit']['balancing']['visibility_zeros_preserved']


def test_actual_ray_occlusion_top_planes_and_box_sides(operator):
    spec=operator['specification']
    # A vertical ray above the die hits the die, and below the roof hits the
    # candidate window; lower coplanar upward tops cannot see other tops.
    start=np.array([[0.,0.,.008],[0.,0.,.006]])
    direction=np.array([[0.,0.,-1.],[0.,0.,1.]])
    hit,length=eg.first_hit(start,direction,spec)
    assert hit.tolist()==[8,13]
    assert np.all(length>0)
    f=np.asarray(operator['raw_view_factors'])
    assert np.array_equal(f[np.ix_([0,2,4,6,8],[0,2,4,6,8])],np.zeros((5,5)))
    assert all(f[i,i]==0 for i in range(14) if i!=11)


def test_reciprocity_closure_isothermal_and_signed_heat(operator):
    f=np.asarray(operator['view_factors']);a=np.array([s['area_m2'] for s in operator['surfaces']])
    assert np.max(abs(f.sum(axis=1)-1))<2e-10
    assert np.max(abs(a[:,None]*f-(a[:,None]*f).T))<1e-16
    zero=ce.evaluate(operator,[300.]*8)
    assert np.max(np.abs(zero['radiation_nodes_w']))<1e-12
    assert np.max(np.abs(zero['gas_nodes_w']))<1e-12
    t=[300.,270.,240.,220.,221.,300.,300.,300.]
    r=ce.evaluate(operator,t)
    assert r['radiation_nodes_w'][4]>0 and r['gas_nodes_w'][4]>0
    assert r['max_conservation_residual_w']<1e-10
    vacuum=ce.evaluate(operator,t,pressure_pa=0.)
    assert vacuum['gas_nodes_w']==[0.]*8
    dark=ce.evaluate(operator,t,pressure_pa=0.,cap_emissivity=0.,window_emissivity=0.,body_emissivity=0.)
    assert dark['radiation_nodes_w']==[0.]*8
    low=ce.evaluate(operator,t,pressure_pa=1e-3)
    twice=ce.evaluate(operator,t,pressure_pa=2e-3)
    assert np.asarray(twice['gas_nodes_w'])==pytest.approx(2*np.asarray(low['gas_nodes_w']),rel=1e-3,abs=1e-10)


def test_independent_two_plate_gray_analytic_limit():
    a=np.array([1e-4,1e-4]);f=np.array([[0.,1.],[1.,0.]])
    power=-(radiation_matrix(a,f,[.2,.8])@np.array([300.,250.])**4)
    exact=SIGMA*a[0]*(300**4-250**4)/(1/.2+1/.8-1)
    assert power[1]==pytest.approx(exact,rel=1e-12)
    assert power[0]==pytest.approx(-exact,rel=1e-12)


@pytest.mark.parametrize('changes',[{'pressure_pa':-1.},{'accommodation':0.},
    {'gas':'unknown'},{'cap_emissivity':np.nan},{'body_emissivity':1.1},{'gas_scale':-1.}])
def test_invalid_scenarios_rejected(operator,changes):
    with pytest.raises(ValueError):ce.evaluate(operator,[300.]*8,**changes)


def test_payload_corruption_and_source_hash_guards(operator,tmp_path,monkeypatch):
    path=tmp_path/'op.json';path.write_text(json.dumps(operator))
    assert ce.load(path)['payload_sha256']==operator['payload_sha256']
    bad=copy.deepcopy(operator);bad['view_factors'][0][0]=.1;path.write_text(json.dumps(bad))
    with pytest.raises(ValueError,match='checksum'):ce.load(path)
    source=json.loads(eg.LEDGER.read_text());source['fixture_sha256']['cap_window_only.msh']='0'*64
    ledger=tmp_path/'sources.json';ledger.write_text(json.dumps(source))
    monkeypatch.setattr(eg,'LEDGER',ledger)
    with pytest.raises(ValueError,match='hash'):eg.verify_sources()


def test_integrated_operator_conserves_hot_cold_and_reservoir_paths(operator):
    r=solve(Scenario(material_model='zhang2025_nonlinear'),exchange=operator)
    p=r['heat_paths_w']
    assert abs(r['global_energy_residual_w'])<1e-8
    assert p['enclosure_conservation_residual_w']<1e-10
    assert r['enclosure_operator']['payload_sha256']==operator['payload_sha256']
    net=sum(p['gas_w'])+sum(p['radiation_w'])+p['enclosure_into_hot_w']+sum(p['enclosure_reservoir_into_w'])
    assert abs(net)<1e-10


def test_gas_extension_and_input_bounds(operator):
    low=ce.evaluate(operator,[185.]*8)
    assert low['gas_sub200_assumption_used']
    for t in ([np.nan]*8,[-1.]*8,[170.]*8,[410.]*8):
        with pytest.raises(ValueError):ce.evaluate(operator,t)


def test_independent_high_pressure_fourier_network_limit(operator):
    r=ce.evaluate(operator,[300.]*8,pressure_pa=1e14)
    a=np.array([s['area_m2'] for s in operator['surfaces']])
    w=a[:,None]*np.array(operator['view_factors']);distance=np.array(operator['chord_distance_m'])
    expected=np.divide(.0095*w,distance,out=np.zeros_like(w),where=w>0)
    np.fill_diagonal(expected,0.)
    assert np.array(r['gas_conductance_w_k'])==pytest.approx(expected,rel=1e-8,abs=1e-14)
