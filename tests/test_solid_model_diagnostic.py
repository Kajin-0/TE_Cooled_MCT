"""Analytic independent controls, signed common-surface accounting and evidence."""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pytest

from tecooledmct.solid_model_diagnostic import ROOT,linear_control,weak_channels
from tecooledmct.integrated_reference import geometry,coefficients,Scenario
from tecooledmct.fem_g1 import tetra_geometry


def test_passive_series_resistance_and_uniform_zero_control():
    g=geometry();q=.002;hot=300.
    zero=linear_control(g,hot,0.,0.)
    assert zero['temperatures_k']==pytest.approx([hot]*5,abs=1e-10)
    assert zero['voltage_v']==pytest.approx(0.,abs=1e-12)
    cs=coefficients(Scenario(current_a=0),g)
    expected=np.r_[hot,hot+q*np.cumsum([1/c['k_w_k'] for c in cs])]
    expected=np.r_[expected,expected[-1]+q*g['die_attach_thickness_over_area_m_inverse']]
    result=linear_control(g,hot,0.,q)
    assert result['temperatures_k']==pytest.approx(expected,abs=1e-10)
    # Open-circuit voltage is Seebeck voltage, not forcibly zero under finite load.
    assert result['voltage_v']<0


def test_hot_control_is_affine_without_fitted_temperature_response():
    g=geometry();a=linear_control(g,300.);b=linear_control(g,300.1)
    assert np.subtract(b['temperatures_k'],a['temperatures_k'])==pytest.approx(
        np.array(a['d_temperatures_d_hot'])*.1,abs=1e-10)
    assert 0<a['d_temperatures_d_hot'][-1]<1
    assert max(abs(np.array(a['residuals_first_four_w_last_k'])))<1e-12
    assert all(abs(s['energy_residual_w'])<1e-12 for s in a['stages'])


@pytest.mark.parametrize('kwargs',[{'hot':float('nan')},{'hot':-1.},
    {'current':-.1},{'current':1.1},{'load':-.001},{'load':float('inf')}])
def test_invalid_controls_reject(kwargs):
    with pytest.raises(ValueError):linear_control(geometry(),**kwargs)


@pytest.mark.parametrize('flux',[-2.,0.,2.])
def test_common_indicator_exact_uniform_flux_and_sign(flux):
    points=np.array([[x,y,z] for z in (0.,1.) for y in (0.,1.) for x in (0.,1.)])
    cells=[]
    for axes in itertools.permutations(range(3)):
        cells.append([0,1<<axes[0],(1<<axes[0])+(1<<axes[1]),7])
    cells=np.array(cells);vol,grad=tetra_geometry(points,cells)
    bodies=np.array([1,1,1,2,2,2]);q=np.tile([0,0,flux],(6,1))
    result=weak_channels(points,cells,bodies,vol,grad,q,np.zeros(6),.4,-flux,0.)
    assert vol.sum()==pytest.approx(1.)
    assert result['total_down_w']==pytest.approx(-flux,abs=1e-14)
    assert sum(result['body_down_w'].values())==pytest.approx(-flux,abs=1e-14)
    assert abs(result['balance_residual_w'])<1e-14


def test_saved_audit_is_traceable_and_does_not_claim_causal_or_mesh_release():
    path=ROOT/'data/solid_model_diagnostic_20261031/diagnostic.json'
    d=json.loads(path.read_text());f=d['field_accounting']
    for section in ('source_sha256','input_sha256'):
        for name,h in d[section].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
    for name,h in d['legacy_review']['input_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
    note=(ROOT/'docs/MATCHED_SOLID_MODEL_DIAGNOSTIC_20261031.md').read_text()
    assert note.split('## Results')[0]==d['registration']
    assert not d['new_numerical_release'] and not d['causal_temperature_attribution_complete']
    assert not d['legacy_review']['new_OpenFOAM_execution']
    assert d['residuals']['hot_boundary_effect_die_k']<.1
    assert d['residuals']['remaining_cold_ceramic_residual_k']>7.6
    assert sum(f['voltage_decomposition_v'].values())==pytest.approx(d['FEM_summary']['voltage_v'],abs=1e-12)
    for cut in f['same_indicator_midleg_channels']:
        assert sum(cut['body_down_w'].values())==pytest.approx(cut['total_down_w'],abs=1e-12)
        assert abs(cut['balance_residual_w'])<1e-6
    for name,case in d['controls'].items():
        c=case['original'];assert c['heat_paths_w']['Cu_total_joule_w']==0
        assert c['terminal_voltage_v']==c['module_voltage_v']
        assert c['heat_paths_w']['external_into_nodes_w']==[0.]*4
    assert max(abs(np.array(f['node_residuals_at_archived_means_w'])))>.03
