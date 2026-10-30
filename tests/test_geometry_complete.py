"""Prove hot-return routing and reject an open circuit or interstage bypass."""
import copy
import json
import numpy as np
import pytest
from tecooledmct.geometry_complete import manifest,wire_routes,REGISTRY
from tecooledmct.fem_g2b_connected import orthogonal_audit,mm_box


def test_full_reference_path_has_88_legs_and_two_module_hot_terminals():
    m=manifest();by={b['id']:b for b in m['bodies']}
    assert len(m['conductor_path'])==183
    assert len(set(m['conductor_path']))==183
    assert sum(by[i]['kind']=='leg' for i in m['conductor_path'])==88
    assert sum(b['kind']=='ceramic' for b in m['bodies'])==4
    assert m['terminals']==[190,191]
    z=m['hot_z_m']+.00022+.000065
    for plane in m['terminal_planes'].values():
        assert plane['axis']==2 and plane['coordinate_m']==pytest.approx(z)
    assert by[183]['boxes_m'][0][2]>z+.002
    assert by[4]['boxes_m'][0][2]+by[4]['boxes_m'][0][5]-m['hot_z_m']==pytest.approx(.0038)


def test_missing_return_or_added_interstage_bypass_is_rejected():
    base=json.loads(REGISTRY.read_text())['stack']
    for bypass in (False,True):
        m=copy.deepcopy(base);ret=next(b for b in m['bodies'] if b['id']==191)
        if bypass:ret['boxes_m'][-1]=mm_box(-2.75,-1.025,-.3,.325,2.6025,2.6425)
        else:ret['boxes_m'].pop()
        with pytest.raises(ValueError):orthogonal_audit(m)


def test_reduced_wires_have_correct_pin_roles_positive_clearance_and_physical_lengths():
    m=manifest();r=wire_routes(m);wires=r['wires']
    assert [v['pin'] for v in wires if v['material']=='Cu']==[1,9]
    assert [v['pin'] for v in wires if v['material']=='Au']==[7,8]
    assert r['hybrid_TEC_graph']['nodes']==187
    assert r['hybrid_TEC_graph']['edges']==186
    assert r['no_TEC_current_path_to_signal_pins']
    for row in wires:
        p=np.array(row['polyline_m']);L=np.linalg.norm(np.diff(p,axis=0),axis=1).sum()
        assert row['length_m']==pytest.approx(L)
        assert row['length_m']>=np.linalg.norm(p[-1]-p[0])
        assert row['certified_other_solid_clearance_lower_bound_m']>0
        assert row['R_ohm']>0 and row['G_W_K']>0
        if row['material']=='Cu':assert p[-1,2]==pytest.approx(m['hot_z_m']+.000285)
    assert r['minimum_wire_pair_clearance_lower_bound_m']>0


def test_raised_hot_pad_cannot_be_mislabeled_as_hot_endpoint():
    m=manifest();body=next(b for b in m['bodies'] if b['id']==191)
    body['boxes_m'][0][2]+=.001
    with pytest.raises(ValueError):wire_routes(m)
