import copy,json
from pathlib import Path
import numpy as np
import pytest
from tecooledmct.v3_et_geometry import qualify_faces,groups
from tecooledmct.v3_et_fem import laminate,LAYERS,SCENARIOS,tensors,controls
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/v3_interconnect_et_20261102'

def test_actual_extracted_source_and_all_port_ownership():
    d=json.loads((BASE/'geometry/geometry.json').read_text());a=qualify_faces(d['groups'],d['faces'])
    assert a['domains']==12 and a['physical_interfaces']==11
    assert len(d['native_sources'])==31
    assert a['explicit_adiabatic_absent']==['C3','HEADER','PIN1_HEAD','DET7','DET8','AMBIENT']
@pytest.mark.parametrize('fault',['missing','duplicate','swap','unknown'])
def test_wrong_ports_fail_closed(fault):
    d=json.loads((BASE/'geometry/geometry.json').read_text());f=copy.deepcopy(d['faces'])
    if fault=='missing':f=[q for q in f if q['thermal_port']!=1]
    elif fault=='duplicate':f.append(copy.deepcopy(f[0]))
    elif fault=='swap':
        for q in f:
            if q['electrical_port']==0:q['electrical_port']=1
    else:f[0]['owners']=[]
    with pytest.raises(ValueError):qualify_faces(d['groups'],f)
def test_finite_contact_and_laminate_hypotheses_are_separate():
    for scenario in SCENARIOS:
        for mode in ('electric','thermal'):
            a=laminate(LAYERS,mode,scenario)
            assert np.all(np.diag(a)>0) and np.array_equal(a,a.T)
    assert SCENARIOS['HIGH']['re']>SCENARIOS['LOW']['re']>0
    assert SCENARIOS['HIGH']['film_factor']>SCENARIOS['LOW']['film_factor']
    with pytest.raises(ValueError):tensors(groups(),scenario='fitted')
def test_explicit_layer_and_anisotropic_grid_controls():
    r=controls();assert r['max_relative_error']<1e-7 and len(r['tests'])==8

def test_analytic_rawcut_gate_is_not_replaced_by_reaction():
    doc=(ROOT/'docs/V3_INTERCONNECT_ELECTROTHERMAL_20261102.md').read_text()
    assert 'maximum of either cut audit is gated' in doc
    assert 'no reaction-only replacement' in doc

def test_original_step_and_report_hashes_preserved():
    import hashlib
    r=json.loads((BASE/'registration.json').read_text())
    for p,h in r['input_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p

def test_historical_failed_coupon_is_not_promoted():
    r=json.loads((BASE/'B/gate_B.json').read_text());down=json.loads((BASE/'B/downstream_NOT_RUN.json').read_text())
    assert r['status']=='FAIL/STOP'
    assert not r['acceptance']['cuts_0p1pct'] and not r['acceptance']['voltage_bounded']
    assert r['R_relative_refinement']<.01 and r['fine_power_relative_error']<.005
    assert down['C'].startswith('NOT RUN') and down['D'].startswith('NOT RUN')
    cuts=json.loads((BASE/'B/fine_field/result.json').read_text())['cuts']
    assert len(cuts)==16 and max(c['gate_error'] for c in cuts)>.8

def test_existing_field_audit_independently_confirms_raw_failure():
    r=json.loads((BASE/'post/independent_audit.json').read_text())
    assert r['fine']['relative_J_reconstruction_error']<1e-7
    assert r['fine']['max_cut_reconstruction_difference_relative']<1e-7
    assert r['fine']['wrong_normals']==0 and r['fine']['uniform_zero_gradient']==0

def test_actual_Elmer_control_evidence_has_one_solve():
    r=json.loads((BASE/'elmer_control/result.json').read_text())
    assert r['solver_runs']==1 and r['max_affine_potential_error_V']<1e-9
    assert (BASE/'elmer_control/mesh/bar_t0001.vtu').is_file()

def test_unit_scale_negative_controls_from_actual_mesh_volume():
    r=json.loads((BASE/'B/fine_mesh/mesh_audit.json').read_text());ratio=r['mesh_volume_m3']/r['CAD_volume_m3']
    assert .5<ratio<2
    for length_scale in (.001,1000.):assert not .5<ratio*length_scale**3<2

def test_millimetre_mesh_file_and_SI_field_mesh_are_explicitly_distinct():
    for level in ('coarse', 'fine'):
        directory = BASE / 'B' / (level+'_mesh')
        # The frozen MSH is ASCII 4.1; inspect its actual node blocks without
        # depending on the optional FEM extra in the minimal CI environment.
        text = (directory/'coupon.msh').read_text()
        assert text.split('$MeshFormat\n', 1)[1].startswith('4.1 0 8\n')
        tokens = iter(text.split('$Nodes\n', 1)[1].split('$EndNodes', 1)[0].split())
        blocks, count, first_tag, last_tag = (int(next(tokens)) for _ in range(4))
        points = []
        for _ in range(blocks):
            dimension, entity, parametric, nodes = (int(next(tokens)) for _ in range(4))
            assert 0 <= dimension <= 3 and parametric == 0
            for _ in range(nodes):
                next(tokens)  # Node tags precede this block's coordinates.
            points.extend([[float(next(tokens)) for _ in range(3)] for _ in range(nodes)])
        assert next(tokens, None) is None and len(points) == count
        with np.load(directory/'mesh.npz') as field_mesh:
            cad_span = np.ptp(np.asarray(points), axis=0)
            si_span = np.ptp(field_mesh['points'], axis=0)
            np.testing.assert_allclose(cad_span*.001, si_span, rtol=1e-12, atol=1e-15)
            assert np.all(si_span < .01) and np.all(si_span > .001)

def test_failed_campaign_source_has_not_been_retuned():
    for name in ('v3_et_geometry', 'v3_et_fem', 'v3_et_run', 'v3_et_elmer_control'):
        assert (ROOT/'tecooledmct'/(name+'.py')).read_bytes() == (BASE/(name+'.executed.py.source')).read_bytes()

@pytest.mark.parametrize('coefficient,contact', [(5e6, 2e-9), (50., 2e-5)])
def test_independent_series_bar_contact_formula_and_passive_operator(coefficient, contact):
    # Small analytic verification only, not a new physical coupon or phase C.
    from tecooledmct.v3_et_fem import structured, control_faces, Operator
    axes = [np.linspace(0, .001, 5), np.linspace(0, .0003, 3), np.linspace(0, .0002, 3)]
    p, t, r = structured(axes, lambda i, j, k: int(i >= 2))
    faces, ids, registry = control_faces(p, t, r, 0)
    op = Operator(p, t, r, faces, ids, dict(groups=[dict(name='left', material='analytic_left'),
                                                dict(name='right', material='analytic_right')], faces=registry),
                  np.array([np.eye(3)*coefficient, np.eye(3)*coefficient/2]), contact)
    result, *_ = op.electrical()
    # Independently written two bulk terms plus contact area impedance.
    expected_R = (.0005/coefficient + .0005/(coefficient/2) + contact)/(.0003*.0002)
    assert abs(result['R_coupon_ohm']/expected_R-1) < 1e-9
    assert result['loss_relative_error'] < 1e-9
    matrix = op.K.toarray()
    scale = np.linalg.norm(matrix, ord=2)
    assert np.max(np.abs(matrix.sum(axis=1))) < 1e-12*scale
    assert np.max(np.abs(matrix-matrix.T)) < 1e-12*scale
    assert np.linalg.eigvalsh(matrix).min() > -1e-12*scale
