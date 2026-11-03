"""Local geometry thresholds and source-edge topology controls; no mesh/PDE runs."""
import collections
import copy
import datetime
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from tecooledmct.v3_r31_mesh_integrity import triangle_metrics, check_face_edges, validate_result

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r31_local_mesh_20261103'


def load(name):
    return json.loads((DATA/name).read_text())


def rectangle():
    p = np.array([[0., 0., 0.], [1., 0., 0.], [1., 1., 0.], [0., 1., 0.]])
    t = np.array([[0, 1, 2], [0, 2, 3]])
    curves = {1: [[0, 1]], 2: [[1, 2]], 3: [[2, 3]], 4: [[3, 0]]}
    return p, t, curves


def test_independent_unit_area_and_source_curve_conservation():
    p, t, curves = rectangle()
    q = triangle_metrics(p, t, 1.)
    assert q['area_PASS'] and q['mesh_area_mm2'] == 1.
    assert check_face_edges(t, curves, {e: 1 for e in curves})['open_edges'] == 4


def test_a_periodic_seam_requires_two_incident_triangles():
    p, t, curves = rectangle()
    curves[5] = [[0, 2]]
    mult = {e: 1 for e in curves}
    mult[5] = 2
    assert check_face_edges(t, curves, mult)['repeated_seam_curves'] == 1
    mult[5] = 1
    with pytest.raises(ValueError, match='incidence'):
        check_face_edges(t, curves, mult)


@pytest.mark.parametrize('defect', ['missing_curve', 'duplicate_segment', 'wrong_node',
                                    'crack', 'duplicate_triangle'])
def test_source_edge_mismatch_never_accepted(defect):
    p, t, curves = rectangle()
    mult = {e: 1 for e in curves}
    if defect == 'missing_curve':
        mult.pop(1)
    if defect == 'duplicate_segment':
        curves[1] = [[0, 1], [0, 1]]
    if defect == 'wrong_node':
        curves[1] = [[0, 9]]
    if defect == 'crack':
        t = np.array([[0, 1, 2]])
    if defect == 'duplicate_triangle':
        t = np.concatenate((t, t[:1]))
    with pytest.raises(ValueError):
        check_face_edges(t, curves, mult)


@pytest.mark.parametrize('defect', ['degenerate', 'nan', 'missing_node', 'zero_area'])
def test_positive_triangles_and_finite_units_required(defect):
    p, t, curves = rectangle()
    target = 1.
    if defect == 'degenerate':
        p[1] = p[0]
    if defect == 'nan':
        p[1, 0] = float('nan')
    if defect == 'missing_node':
        t[0, 1] = 9
    if defect == 'zero_area':
        target = 0.
    with pytest.raises(ValueError):
        triangle_metrics(p, t, target)


@pytest.mark.parametrize('segments,accepted', [(6, False), (48, True)])
def test_exact_circular_area_control(segments, accepted):
    theta = 2*np.pi*np.arange(segments)/segments
    points = np.r_[np.zeros((1, 3)), np.c_[np.cos(theta), np.sin(theta), np.zeros(segments)]]
    tri = np.c_[np.zeros(segments, int), np.arange(segments)+1, np.roll(np.arange(segments)+1, -1)]
    q = triangle_metrics(points, tri, np.pi)
    assert q['area_PASS'] == accepted
    exact_polygon = segments*np.sin(2*np.pi/segments)/2
    assert abs(q['mesh_area_mm2']-exact_polygon) < 1e-12


@pytest.mark.parametrize('scale', [1e-3, 1e3])
def test_thousandfold_coordinate_error_fails_area_gate(scale):
    p, t, curves = rectangle()
    assert not triangle_metrics(p*scale, t, 1.)['area_PASS']


def test_inventory_uses_native_source_partitions_without_new_cad():
    inv = load('inventory.json')
    r3 = json.loads((ROOT/'data/v3_analysis_r3_20261103/audit_v2/registry.json').read_text())
    assert inv['selected_faces'] == 54 and inv['source_domains'] == 430
    assert inv['source_faces'] == 2440 and inv['no_CAD_operations']
    selected = set(inv['groups']['leads_jackets'])
    partial = [q for q in r3['shell_regions'] if q['condition'].startswith('PARTIAL')]
    assert len(partial) == 4
    for q in partial:
        assert set(q['covered_R3_faces']+q['bare_R3_faces']) <= selected
    assert all(q['owners'] == r3['face_registry'][f]['owners'] for f, q in inv['faces'].items())


def test_registered_executed_sources_and_original_input_hashes():
    reg = load('registration.json')
    assert len(reg['cases']) == 12 and reg['seconds_per_case'] == 180
    assert reg['No_Global_Surface'] and reg['No_Global_Volume'] and reg['No_PDE']
    for registration in (reg, load('corrective_registration.json')):
        for field in ('sources_sha256', 'inputs_sha256'):
            for path, digest in registration[field].items():
                assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest
        for case in registration['cases']:
            resources = DATA/'cases'/case['id']/'resources.json'
            if resources.exists():
                actual = json.loads(resources.read_text())
                assert datetime.datetime.fromisoformat(registration['observed_UTC']) < datetime.datetime.fromisoformat(actual['observed_start_UTC'])
    assert hashlib.sha256((DATA/'executed_source/preregistered_method.md').read_bytes()).hexdigest() == reg['method_doc_sha256']
    manifest = load('release_manifest.json')
    for field in ('files_sha256', 'sources_sha256'):
        for path, digest in manifest[field].items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest


def test_actual_accepted_local_meshes_keep_all_strict_gates():
    inv = load('inventory.json')
    results = [json.loads(p.read_text()) for p in (DATA/'cases').glob('*/worker/result.json')]
    accepted = [q for q in results if q['status'] == 'PASS LOCAL SURFACE ONLY']
    assert accepted
    for q in accepted:
        assert validate_result(q, inv)


def test_independent_native_mesh_replay_and_lossless_archives():
    replay = load('independent_readback.json')
    archives = load('mesh_archives.json')
    assert replay['no_mesh_generation'] and len(replay['cases']) == 10
    assert sum(q['status'].startswith('PASS') for q in replay['cases']) == 8
    expected = {q['case']: q['mesh_sha256'] for q in replay['cases']}
    for q in archives['files']:
        p = ROOT/q['archive']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == q['archive_sha256']
        with gzip.open(p, 'rb') as inp:
            assert hashlib.sha256(inp.read()).hexdigest() == q['native_MSH_sha256'] == expected[q['case']]


def test_failed_and_unrun_cases_remain_visible():
    s = load('summary.json')
    assert s['accepted_cases'] == 8 and s['rejected_or_censored_cases'] == 4
    assert s['no_global_mesh'] and s['no_PDE'] and s['C_leads_jackets'].startswith('NOT RUN')
    assert s['cases']['A_callback_all__detector_bonds']['timeout']
    assert s['cases']['B_native_all__detector_bonds']['max_area_error'] > .04
    assert not s['cases']['B_native_selective__detector_bonds']['worker_status'].startswith('PASS')


def test_prospective_global_plan_is_unexecuted_and_keeps_source_ownership():
    p = load('prospective_global_algorithm_NOT_RUN.json')
    r = json.loads((ROOT/'data/v3_analysis_r3_20261103/audit_v2/registry.json').read_text())
    assert not p['global_trial_executed'] and p['all_laws'] == 'UNSET'
    assert len(p['face_plan']) == 2440 and p['domains'] == 430
    assert len(p['directional_faces']) == 10 and p['unbenchmarked_global_faces'] == 2386
    for f, q in p['face_plan'].items():
        assert q['owners'] == r['face_registry'][f]['owners']
        assert q['owner_volume_ids'] == r['face_registry'][f]['owner_volume_ids']


@pytest.mark.parametrize('defect', ['one_face', 'missing', 'owner', 'global', 'tetrahedra', 'source', 'conformity'])
def test_false_local_release_is_rejected(defect):
    inv = load('inventory.json')
    paths = sorted((DATA/'cases').glob('*/worker/result.json'))
    q = next(json.loads(p.read_text()) for p in paths if json.loads(p.read_text())['status'].startswith('PASS'))
    q = copy.deepcopy(q)
    first = next(iter(q['faces'].values()))
    if defect == 'one_face':
        first['relative_area_error'] = .01
    if defect == 'missing':
        q['faces'].pop(next(iter(q['faces'])))
    if defect == 'owner':
        first['owners'] = ['fabricated_source']
    if defect == 'global':
        q['global_mesh_RUN'] = True
    if defect == 'tetrahedra':
        q['tetrahedra'] = 1
    if defect == 'source':
        q['source_identity_PASS'] = False
    if defect == 'conformity':
        first['conformity']['status'] = 'FAIL'
    with pytest.raises(ValueError):
        validate_result(q, inv)
