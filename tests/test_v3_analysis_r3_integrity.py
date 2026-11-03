"""Cheap immutable R3 source/geometry controls; no CAD, mesh generation or PDE."""
import json
from pathlib import Path

import pytest

from tecooledmct.v3_analysis_r3_integrity import (
    validate_geometry, validate_scale, validate_surface, verify_hashes,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_analysis_r3_20261103'


def load(name):
    return json.loads((DATA/name).read_text())


def inputs():
    return load('audit_v2/registry.json'), load('geometry_restored/geometry_receipt.json')


def test_exact_restored_jackets_and_source_migration():
    r, g = inputs()
    assert validate_geometry(r, g)
    assert g['new_Boolean_operations'] == g['new_imprints'] == 0
    assert g['meridian_imprint_status'].startswith('STOP')
    assert g['output_BREP_sha256'] == r['input_BREP_sha256']
    assert abs(r['gas_volume_mm3']-1231.6300611682168) < 1e-7


def test_original_tracked_inputs_preserved():
    assert verify_hashes(ROOT, load('protected_inputs.json')['files'])
    manifest = load('release_manifest.json')
    assert verify_hashes(ROOT, manifest['files_sha256'])
    assert verify_hashes(ROOT, manifest['sources_sha256'])
    assert manifest['global_3D_mesh'] == 'NOT RUN'
    assert not manifest['solver_ready'] and not manifest['surface_mesh_qualified']


@pytest.mark.parametrize('defect', [
    'source', 'face', 'contact', 'area', 'normal', 'gas_ownership',
    'partial_average', 'partial_complement', 'double_count', 'gas_volume',
    'jacket_volume', 'bulk_pin', 'short', 'leg_bypass', 'terminal', 'law',
])
def test_reject_incomplete_or_false_geometry_release(defect):
    r, g = inputs()
    if defect == 'source':
        r['source_to_analysis'].pop('pin1_Au')
    if defect == 'face':
        r['face_registry'].pop(next(iter(r['face_registry'])))
    if defect == 'contact':
        r['source_contacts'][0]['relative_error'] = .01
    if defect == 'area':
        next(iter(r['face_registry'].values()))['face_area_mm2'] = 0
    if defect == 'normal':
        f = next(f for f in r['face_registry'].values() if len(f['owners']) == 2)
        f['orientation_signs'] = [1, 1]
    if defect == 'gas_ownership':
        f = next(f for f in r['face_registry'].values() if 'CAVITY_GAS' in f['owners'])
        f['owners'] = ['CAVITY_GAS']
        f['owner_volume_ids'] = [r['domain_id_map']['CAVITY_GAS']]
        f['orientation_signs'] = [1]
    partial = next(q for q in r['shell_regions'] if q['condition'].startswith('PARTIAL'))
    if defect == 'partial_average':
        partial['boundary_quadrature'] = 'WHOLE_FACE_WEIGHTING'
    if defect == 'partial_complement':
        partial['bare_R3_faces'] = []
    if defect == 'double_count':
        r['source_to_analysis']['lead1_insulation']['no_gas_parallel_path'] = False
    if defect == 'gas_volume':
        r['gas_volume_mm3'] += .077162028
    if defect == 'jacket_volume':
        r['excluded_polymer_volume_mm3'] = 0
    if defect == 'bulk_pin':
        r['domains']['pin9']['z_regions_mm'] = [[-12.7, 2.0035, 'Kovar_pin']]
    if defect == 'short':
        r['unintended_cross_net_contacts'] = [['net0', 'net88']]
    if defect == 'leg_bypass':
        r['every_leg_required_for_series_path'] = False
    if defect == 'terminal':
        r['terminal_faces']['pin1'] = []
    if defect == 'law':
        r['domains']['pin1']['law_status'] = 'BULK_KOVAR'
    with pytest.raises(ValueError):
        validate_geometry(r, g)


@pytest.mark.parametrize('scale', [1e-3, 1e3])
def test_thousandfold_length_and_billionfold_volume_errors_rejected(scale):
    with pytest.raises(ValueError, match='SI scale'):
        validate_scale(.001, .001*scale, 1e-9, 1e-9*scale**3)


def test_analytic_one_millimetre_cube_si_units():
    assert validate_scale(.001, .001, 1e-9, .001**3)


def test_measured_dense_reference_replay_remains_strict():
    ref = load('reference_replay/reference.json')
    assert ref['triangles'] == 1416664 and ref['nodes'] == 701952
    assert len(ref['faces']) == 2422
    assert max(abs(v['relative_error']) for v in ref['faces'].values()) < .01


def test_failed_imprint_and_reversed_comparison_are_preserved_failures():
    assert load('geometry/geometry_receipt.json')['status'].startswith('STOP')
    assert load('geometry_corrected/geometry_receipt.json')['status'].startswith('STOP')
    assert load('geometry_completed/geometry_receipt.json')['status'].startswith('STOP')
    assert load('audit/registry.json')['status'].startswith('STOP')
    # Independent controls of the preserved reversed comparison defect.
    reference = .077162028
    actual = inputs()[0]['excluded_polymer_volume_mm3']
    assert abs(actual-reference) < 1e-7
    assert not abs(actual+.01-reference) < 1e-7


def surface_control():
    """Synthetic threshold control only; not an actual completed mesh."""
    r = inputs()[0]
    g = dict(status='PASS', triangles=100, failed_faces=[], failed_R2_parents=[],
             rows={k: {'relative_error': 0.} for k in r['face_registry']},
             R2_parents={k: {'relative_error': 0.} for k in r['R2_face_descendants']})
    return g, r


def test_synthetic_surface_gate_control():
    assert validate_surface(*surface_control())


@pytest.mark.parametrize('defect', ['one_face', 'one_parent', 'missing_face',
                                    'missing_parent', 'triangle_budget', 'STOP'])
def test_surface_gate_never_averages_away_an_individual_failure(defect):
    g, r = surface_control()
    if defect == 'one_face':
        next(iter(g['rows'].values()))['relative_error'] = .01
    if defect == 'one_parent':
        next(iter(g['R2_parents'].values()))['relative_error'] = -.01
    if defect == 'missing_face':
        g['rows'].pop(next(iter(g['rows'])))
    if defect == 'missing_parent':
        g['R2_parents'].pop(next(iter(g['R2_parents'])))
    if defect == 'triangle_budget':
        g['triangles'] = 800001
    if defect == 'STOP':
        g['status'] = 'STOP TIME BUDGET'
    with pytest.raises(ValueError):
        validate_surface(g, r)
