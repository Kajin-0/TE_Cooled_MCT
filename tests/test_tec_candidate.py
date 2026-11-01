"""Separate-candidate geometry, conservation, calibration provenance and FAIL gates."""
from copy import deepcopy
import hashlib,json
import numpy as np
import pytest

from tecooledmct.tec_candidate_geometry import design,audit,union_volume,path_boxes,reader,ID
from tecooledmct.tec_candidate_study import DATA,ROOT,geometry,scenario,metrics,CALIBRATION
from tecooledmct.tec_material_plausibility import read,sha
from tecooledmct.physical_input_qualification import balance
from tecooledmct.native_gas_audit import step_units
from tecooledmct import graded_tec


def test_independent_rectilinear_union_and_invalid_path():
    assert union_volume([[0,0,0,1,1,1],[.5,0,0,1,1,1]])==pytest.approx(1.5)
    assert union_volume([[0,0,0,1,1,1],[1,0,0,1,1,1]])==pytest.approx(2.)
    with pytest.raises(ValueError):path_boxes([[0,0,0],[1,1,0]])


def test_exact_source_constrained_geometry_contacts_and_solder_areas():
    d=read(DATA/'geometry/design.json');expected=json.loads(json.dumps(design()))
    assert {k:v for k,v in d.items() if k!='bodies'}=={k:v for k,v in expected.items() if k!='bodies'}
    for actual,calculated in zip(d['bodies'],expected['bodies']):
        assert {k:v for k,v in actual.items() if k!='volume_mm3'}=={k:v for k,v in calculated.items() if k!='volume_mm3'}
        assert actual['volume_mm3']==pytest.approx(calculated['volume_mm3'],rel=1e-12,abs=1e-13)
    assert d['id']==ID
    a=audit(d)
    assert a['legs']==88 and a['contact_count']==176 and a['solid_count']==361
    assert a['minimum_pattern_pullback_mm']>=.1 and a['minimum_unrelated_Cu_gap_mm']>=.139999
    legs=[b for b in d['bodies'] if b['kind'] in ('P','N')]
    assert len(legs)==88
    assert all(np.allclose(b['boxes_mm'][0][3:],[.4,.4,.5],atol=1e-14) for b in legs)
    assert sum(b['volume_mm3'] for b in legs)==pytest.approx(7.04)
    # Independent per-leg box interface check, without using the nominal contact list.
    for b in legs:
        j=b['chain_index'];x,y,z,w,h,L=b['boxes_mm'][0]
        for face,plane in [('hot',z),('cold',z+L)]:
            s=next(q for q in d['bodies'] if q['name']==f'solder{j}_{face}')['boxes_mm'][0]
            assert s[:2]==pytest.approx([x,y]) and s[3:5]==pytest.approx([w,h])
            assert (s[2]+s[5] if face=='hot' else s[2])==pytest.approx(plane)
    assert a['external_pin_connections']=='NOT IMPLEMENTED'


def test_topology_and_collision_negative_controls():
    d=design();d['legs'][0]['cold_node']=4
    with pytest.raises(ValueError):audit(d)
    d=design();cu=[b for b in d['bodies'] if b['kind']=='Cu'];cu[1]['boxes_mm'].append(cu[0]['boxes_mm'][0])
    with pytest.raises(ValueError):audit(d)
    d=design();d['bodies'][0]['boxes_mm'][0][5]=1.
    with pytest.raises(ValueError):audit(d)


def test_exact_export_and_corrected_unit_reader_have_separate_provenance():
    reg=read(DATA/'registration.json');w=read(DATA/'geometry/cad_writer.json');r=read(DATA/'geometry/si_reader.json')
    assert w['source_sha256']==reg['geometry_producer_sha256']==sha(DATA/'geometry.py.source')
    assert r['reader_source_sha256']==sha(DATA/'geometry_reader_corrected.py.source')==sha(ROOT/'tecooledmct/tec_candidate_geometry.py')
    assert r['STEP_sha256']==w['STEP_sha256']==sha(DATA/'geometry/candidate_mm.step')
    assert r['status']=='PASS' and r['bodies']==361 and r['max_relative_volume_error']<1e-7
    assert r['parsed_units']['metres_per_coordinate_unit']==.001 and w['CAD_imports']==0
    stop=read(DATA/'geometry/initial_reader_STOP.json');assert stop['unchanged_STEP_sha256']==r['STEP_sha256']
    raw=(DATA/'geometry/candidate_mm.step').read_text()
    assert step_units(raw)['metres_per_coordinate_unit']==.001
    assert step_units(raw.replace('SI_UNIT(.MILLI.,.METRE.)','SI_UNIT($,.METRE.)'))['metres_per_coordinate_unit']==1.
    with pytest.raises(ValueError):step_units(raw.replace('SI_UNIT(.MILLI.,.METRE.)','SI_UNIT($,.METRE.)',1))
    # Independently require BOTH physical bbox and cubic volume agreement: wrong
    # coordinate magnitudes by 1e-3 and 1e3 fail, even if the label remains mm.
    row=w['records'][0]
    for factor in (1e-3,1e3):
        assert not np.allclose(np.array(row['bbox_m'])*factor,row['bbox_m'],rtol=0,atol=2.1e-7)
        assert not np.isclose(row['volume_m3']*factor**3,row['volume_m3'],rtol=1e-7,atol=1e-20)


@pytest.mark.parametrize('prefix',['$','.DECI.'])
def test_reader_rejects_invalid_unit_before_any_CAD_import(tmp_path,prefix):
    (tmp_path/'candidate_mm.step').write_text(f'#1=( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT({prefix},.METRE.) );')
    with pytest.raises(ValueError):reader(tmp_path)


def test_registered_no_fit_and_constrained_fit_preserve_originals():
    reg=read(DATA/'registration.json');sr=read(DATA/'study/registration.json')
    assert sha(DATA/'sources.json')==reg['source_audit_sha256']
    note=(ROOT/'docs/SOURCE_CONSTRAINED_TEC_CANDIDATE_20261101.md').read_text().split('## Results')[0]
    assert reg['protocol']==sr['protocol']==note
    assert sr['source_sha256']==sha(DATA/'study/producer.py.source')==sha(ROOT/'tecooledmct/tec_candidate_study.py')
    for p,h in reg['input_sha256'].items():assert sha(ROOT/p)==h
    for p,h in sr['dependency_sha256'].items():assert sha(ROOT/p)==h
    assert len(sr['conditions'])==20 and sr['calibration']==[list(c) for c in CALIBRATION]
    g=geometry();assert [s['couples'] for s in g['stages']]==[29,11,4] and not g['wires']
    assert all(s['leg_area_m2']==.16e-6 and s['leg_length_m']==.0005 for s in g['stages'])
    for S,rho in ((.89,1.),(1.,1.21)):
        with pytest.raises(ValueError):scenario(.2,0.,S=S,rho=rho)


def test_all_real_cases_balances_source_bounds_and_rejections():
    cases=read(DATA/'study/cases.json');a=read(DATA/'study/analysis.json');g=geometry()
    assert a['actual_calls']==len(cases)==155<=240 and a['elapsed_seconds']<600
    assert a['counts']=={'ACCEPTED':150,'REJECTED':5,'NOT RUN':0}
    for r in cases.values():
        assert .9<=r['S_scale']<=1.1 and .8<=r['rho_scale']<=1.2
        if r['status']=='ACCEPTED':
            assert 180<=r['summary']['leg_min_K']<=r['summary']['leg_max_K']<=390
            if r['material']=='g1_constant':continue
            check=balance(scenario(r['current_A'],r['load_W'],r['hot_K'],r['S_scale'],r['rho_scale'],r['attach_k']),g,r['result'])
            assert abs(check['global_error_W'])<1e-8
            for k,v in r['audit'].items():np.testing.assert_allclose(check[k],v,rtol=0,atol=5e-15)
        else:
            assert r['diagnostics']['candidate_is_accepted'] is False
            assert r['diagnostics']['last_candidate_temperatures_k'] and r['diagnostics']['optimizer']
    assert a['attach_invariance_PASS'] and a['physical_qualification'] is False


def test_calibration_SUCCESS_does_not_waive_failed_alignment_or_make_blind_holdouts():
    a=read(DATA/'study/analysis.json')
    assert a['calibration']['optimizer_success']
    assert not a['no_fit_metrics']['alignment_PASS'] and not a['all20_metrics']['alignment_PASS']
    assert a['all20_metrics']['accepted_observables']==40
    assert a['all20_metrics']['max_absolute_lift_K']>25 and a['evaluation16_metrics']['accepted_observables']==32
    assert a['Qmax']==a['DeltaTmax']=='NOT RUN'
    assert all(not r['independent_validation'] for r in a['rows'])
    assert {r['partition'] for r in a['rows']}=={'CALIBRATION previously seen','EVALUATION previously seen'}
    assert len({r['source_id'] for r in a['rows'] if r['partition'].startswith('CALIBRATION')})==8
    # Keeping low aggregate error cannot hide a single failed maximum-error gate.
    fake=[dict(field='delta_t_k',status='ACCEPTED',absolute_difference=25.,signed_difference=-25.,relative_difference=-.3),
          dict(field='voltage_v',status='ACCEPTED',absolute_difference=.01,signed_difference=.01,relative_difference=.01)]
    assert not metrics(fake)['alignment_PASS']


def test_analytic_controls_and_same_domain_BVP_are_actual_not_source_fit():
    assert len(read(DATA/'study/constant_controls.json'))==3
    for r in read(DATA/'study/constant_controls.json'):
        assert r['temperature_error_K']<1e-6 and r['voltage_error']<1e-7 and r['sink_error_W']<1e-8
    for r in read(DATA/'study/independent_BVP.json'):assert r['PASS'] and 180<r['source_min_K']<=r['source_max_K']<300
    S,rho,_=read(DATA/'study/analysis.json')['selected_scales_S_rho_k']
    for polarity in ('P','N'):
        for t in (299.999,300.,300.001,390.):
            p=graded_tec.props(polarity,t)
            assert 1/(rho*p['rho'])>0 and p['sigma']==1/p['rho']
            slope=graded_tec.source().curves[polarity]['S'].slope(min(t,300.))*(.25 if t>300 else 1.)
            assert S*p['thomson_v_k']==pytest.approx(t*S*slope,rel=1e-14)


def test_sources_posthoc_omissions_and_immutable_candidate_ledger():
    sources=read(DATA/'sources.json')
    tec=next(x for x in sources if x['name']=='tec2019.pdf')
    assert tec['sha256']==read(ROOT/'data/g2c/oem2019_curves_v1.json')['original_pdf_sha256']
    historical=next(x for x in sources if x['name']=='historical_RMT2008_web_index')
    assert historical['nominal_05']['couple_multiset']==[4,11,29]
    assert 'NOT locally inspected' in historical['status']
    p=read(DATA/'presentation/comparison.json')
    assert p['common_support_observables']==34
    assert all(not p[key]['full_candidate_qualification'] for key in ('common_support_original','common_support_no_fit','common_support_selected'))
    rho=1.72e-8;d=read(DATA/'geometry/design.json')
    for r in p['post_hoc_Cu_omission_audit']['routes']:
        length=sum(np.linalg.norm(np.array(a)-np.array(b)) for a,b in zip(d['Cu_routes_mm'][r['node']],d['Cu_routes_mm'][r['node']][1:]))*.001
        assert r['R_ohm_estimate']==pytest.approx(rho*length/(.1e-3*.03e-3))
    assert p['candidate_lift_load_secant_K_W']>p['source_lift_load_secant_K_W']
    ledger=read(DATA/'checksums.json')
    for path,h in ledger['artifact_sha256'].items():assert sha(DATA/path)==h
    assert sha(ROOT/'tecooledmct/tec_candidate_presentation.py')==ledger['presentation_source_sha256']


def test_sealed_presentation_cannot_be_overwritten():
    from tecooledmct.tec_candidate_presentation import present
    with pytest.raises(ValueError,match='Sealed checkpoint'):present(DATA)
