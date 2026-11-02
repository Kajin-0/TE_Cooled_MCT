"""Independent source contacts, SI gates and adversarial synthetic-design controls."""
import copy,json,hashlib
from pathlib import Path
import pytest
from tecooledmct.tec_assembly_v3 import design,fillet,LAYERS,OUTER
from tecooledmct.tec_assembly_v3_audit import audit,tolerances,signature_ok,interval_clearance
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/synthetic_v3_assembly_20261102'
@pytest.fixture(scope='module')
def d():return design()
def test_frozen_baseline_and_stage_identity(d):
    old=json.loads((ROOT/'data/tec_candidate_29114_v2_20261102/source_final/design.json').read_text())
    assert d['legs']==old['legs']
    assert sum(t for _,t in LAYERS)==pytest.approx(.015)
    assert sum(t for _,t in OUTER)==pytest.approx(.002)
    assert all(b['volume_mm3']>0 for b in d['bodies'])
def test_actual_source_graph_and_independent_intervals(d):
    a=audit(d)
    assert (a['P_N_contacts'],a['net_count'],a['metal_components'])==(176,89,98)
    assert all(x['status']=='PASS' for x in tolerances())
@pytest.mark.parametrize('missing',['tab_joint0','formed_tab58','hot_mount_In52Sn48','TEC_lead1','detector_bond7','net2_plane0.500_Cu'])
def test_missing_physical_path_is_rejected(d,missing):
    q=copy.deepcopy(d);q['bodies']=[b for b in q['bodies'] if b['name']!=missing]
    with pytest.raises((ValueError,KeyError)):audit(q)
@pytest.mark.parametrize('fault',['pin_swap','wrong_detector','polarity','foot','metal_short','misregister'])
def test_wrong_identity_or_geometry_rejected(d,fault):
    q=copy.deepcopy(d)
    if fault=='pin_swap':
        for b in q['bodies']:
            if b['name']=='pin1':b['group']='PIN9'
            elif b['name']=='pin9':b['group']='PIN1'
    elif fault=='wrong_detector':q['detector']='photovoltaic'
    elif fault=='polarity':q['legs'][0]['polarity']='P'
    elif fault=='foot':q['feet'].pop()
    elif fault=='metal_short':
        b=next(v for v in q['bodies'] if v['name']=='net2_plane0.500_Cu');b['group']=4
    elif fault=='misregister':
        b=next(v for v in q['bodies'] if v['name']=='leg0_N');b['boxes_mm'][0][0]+=.06
        b['bbox_mm'][0]+=.06;b['bbox_mm'][3]+=.06
    with pytest.raises((ValueError,KeyError)):audit(q)
def test_tight_process_metallurgy_is_explicit(d):
    assert [x[0] for x in d['layer_stack']]==['Ti','TiW','Cu','Ni','Au']
    assert all(b['material']=='SnBi57_43' for b in d['bodies'] if b['name'].startswith('tab_joint'))
    assert len(d['feet'])==7
@pytest.mark.parametrize('scale',[1e-3,1e3])
def test_unit_error_rejected(scale):
    expected=1e-9;volume=expected*scale**3
    assert not signature_ok(volume,[.02*scale]*3+[.021*scale]*3,expected,[.02]*3+[.021]*3)
    assert scale**3==pytest.approx(1e-9 if scale<1 else 1e9)
def test_impossible_bend_rejected():
    with pytest.raises(ValueError):fillet([[0,0],[.01,0],[.01,1]],.075)
def test_no_simulation_in_new_cad_sources():
    for name in ('tec_assembly_v3.py','tec_assembly_v3_audit.py','tec_assembly_v3_step_audit.py'):
        t=(ROOT/'tecooledmct'/name).read_text()
        assert 'mesh.generate(' not in t and 'ElmerSolver' not in t


def test_unqualified_metallurgy_cannot_pass(d):
    q=copy.deepcopy(d);q["layer_stack"]=[("Au",.015)]
    with pytest.raises(ValueError,match="metallurgy"):audit(q)

@pytest.mark.parametrize("nom,losses,req",[(.05,[.015,.02,.02],.01),(.08,[.03,.03],.05),(.075,[.015,.02],.05)])
def test_worst_case_fail_not_nominal_pass(nom,losses,req):
    with pytest.raises(ValueError):interval_clearance(nom,losses,req)


def test_collision_enclosure_never_excludes_an_overlap(d):
    from tecooledmct.tec_assembly_v3_step_audit import certified_separation
    wire=next(b for b in d['bodies'] if b['name']=='TEC_lead1')
    p=wire['points'][0];box=dict(shape='boxes',bbox_mm=[p[0]-.01,p[1]-.01,p[2],p[0]+.01,p[1]+.01,p[2]+.01])
    assert certified_separation(wire,box) is None
    box['bbox_mm']=[20,20,20,21,21,21]
    assert certified_separation(wire,box)
    shell=next(b for b in d['bodies'] if b['name']=='cap_shell')
    assert certified_separation(shell,dict(shape='boxes',bbox_mm=[-3,-3,2,3,3,3]))
    assert certified_separation(shell,dict(shape='boxes',bbox_mm=[7.2,0,2,7.3,.1,3])) is None


def test_actual_terminal_mapping_cannot_be_relabelled(d):
    q=copy.deepcopy(d);q['legs'][0]['hot_node']=2
    with pytest.raises(ValueError,match='quotient|ownership'):audit(q)


def test_bridge_alloy_element_order_is_not_reversed():
    j=json.loads((BASE/'material_definitions.json').read_text())['SnBi57_43']
    assert j['resolves_to']=='Bi57Sn43'
    assert j['Bi_mass_fraction']==.57 and j['Sn_mass_fraction']==.43
    assert 'NOT57Sn/43Bi' in j['warning']
