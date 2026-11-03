"""No-Gmsh acceptance of R3 geometric evidence; never grants solver readiness."""
from __future__ import annotations

import hashlib
import math


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_geometry(registry, geometry):
    r, g = registry, geometry
    require(r['status'].startswith('PASS') and g['status'].startswith('PASS'),
            'source geometry not accepted')
    require(r['volume_count'] == len(r['domains']) == len(r['domain_id_map']) == 430,
            '430-domain identity missing')
    require(len(set(r['domain_id_map'].values())) == 430, 'duplicate domain IDs')
    require(len(r['source_to_analysis']) == 824, 'physical source missing')
    require(len(r['source_contacts']) == 378, 'contact witness missing')
    require(len(r['R2_face_descendants']) == 2422, 'R2 face parent missing')
    require(len(r['face_registry']) == r['face_count'] == 2440,
            'unimprinted face registry incomplete')
    require(r['face_class_counts'] == {'GAS_SOLID': 1840, 'SOLID_SOLID': 557,
                                      'EXTERIOR': 43}, 'face class migration changed')
    for name, q in r['source_to_analysis'].items():
        require(q['name'] in r['domain_id_map'] and
                q['id'] == r['domain_id_map'][q['name']], 'source owner map incomplete')
    for c in r['source_contacts']:
        require(c['type'] in ('COLLAPSED_COMPOSITE', 'FINITE_SHARED_FACE'),
                'unknown contact representation')
        require(c.get('relative_error', 0) < 1e-6, 'contact CAD area drift')
        require(c['source_witness_mm2'] > 0, 'zero finite contact')
    for f in r['face_registry'].values():
        require(math.isfinite(f['face_area_mm2']) and f['face_area_mm2'] > 0,
                'invalid source face area')
        n = len(f['owners'])
        require(n in (1, 2) and len(set(f['owners'])) == n, 'nonmanifold ownership')
        require([r['domain_id_map'][name] for name in f['owners']] ==
                f['owner_volume_ids'], 'wrong face owner IDs')
        require(len(f['orientation_signs']) == n and
                all(s in (-1, 1) for s in f['orientation_signs']), 'missing normal orientation')
        require(n == 1 or sum(f['orientation_signs']) == 0, 'nonopposing interface normals')
        require('CAVITY_GAS' not in f['owners'] or n == 2, 'open gas wall')
    regions = r['shell_regions']
    require(len(regions) == 10 and r['full_shell_regions'] == 6 and
            r['partial_shell_regions'] == 4, 'six full/four partial regions missing')
    for q in regions:
        require(q['covered_R3_faces'] and q['boundary_quadrature'] == 'REAL_CAD_SUBFACES',
                'shell area silently averaged')
        covered = q['covered_R3_faces']
        require(len(covered) == len(set(covered)), 'duplicate polymer coverage')
        require(abs(q['exact_covered_mm2']/q['physical_inner_area_mm2']-1) < 1e-6,
                'source polymer area drift')
        for f in covered:
            require(set(r['face_registry'][str(f)]['owners']) ==
                    {q['physical_Cu'], q['physical_jacket']}, 'false polymer ownership')
        partial = q['condition'].startswith('PARTIAL')
        require(bool(q['bare_R3_faces']) == partial, 'partial complement missing')
        require(abs(q['exact_covered_mm2']+q['exact_bare_mm2']-
                    q['derived_face_area_mm2']) < 1e-7, 'polymer/bare area mismatch')
    for name in ('lead1_insulation', 'lead9_insulation'):
        q = r['source_to_analysis'][name]
        require(q['kind'] == 'EXPLICIT_VOLUMETRIC_DIELECTRIC' and
                q['no_gas_parallel_path'], 'gas and dielectric double count')
    require(r['gas_components'] == 1 and not r['unintended_cross_net_contacts'],
            'gas disconnected or electrical short')
    require(r['every_leg_required_for_series_path'] and
            r['stage_leg_counts'] == {'0': 58, '1': 22, '2': 8}, 'series leg bypass')
    require(abs(r['excluded_polymer_volume_mm3']-.077162028) < 1e-7,
            'source polymer volume changed')
    require(abs(g['R2_gas_volume_mm3']-r['gas_volume_mm3']-
                r['excluded_polymer_volume_mm3']) < 1e-7, 'gas displacement mismatch')
    require(set(r['terminal_faces']) == {'pin1', 'pin7', 'pin8', 'pin9'} and
            all(len(v) == 1 for v in r['terminal_faces'].values()), 'terminal identity missing')
    for n in (1, 7, 8, 9):
        q = r['domains']['pin'+str(n)]
        require(q['material'] == 'EFFECTIVE_AXIAL_KOVAR_NI_AU' and
                q['z_regions_mm'] == [[-12.7, 2., 'Kovar_pin'], [2., 2.002, 'Ni'],
                                      [2.002, 2.0035, 'Au']], 'bulk Kovar fallback')
    require(not r['solver_ready'] and not g['solver_ready'] and
            all(q['law_status'] == 'UNSET' and not q['solver_ready']
                for q in r['domains'].values()), 'unqualified material law')
    require(not r['physical_redesign'] and not g['physical_redesign'], 'physical redesign')
    return True


def validate_surface(gate, registry):
    require(gate['status'] == 'PASS', 'surface gate not passed')
    require(set(gate['rows']) == set(registry['face_registry']), 'surface face missing')
    require(set(gate['R2_parents']) == set(registry['R2_face_descendants']),
            'source ancestor mesh area missing')
    require(not gate['failed_faces'] and not gate['failed_R2_parents'], 'failed area gates')
    require(gate['triangles'] <= 800000 and gate['triangles'] > 0, 'surface budget')
    for q in list(gate['rows'].values()) + list(gate['R2_parents'].values()):
        require(math.isfinite(q['relative_error']) and abs(q['relative_error']) < .01,
                'strict per-face area gate')
    return True


def validate_scale(reference_length_m, actual_length_m, reference_volume_m3,
                   actual_volume_m3):
    require(reference_length_m > 0 and reference_volume_m3 > 0, 'invalid unit reference')
    require(math.isfinite(actual_length_m) and math.isfinite(actual_volume_m3),
            'nonfinite unit measure')
    require(abs(actual_length_m/reference_length_m-1) < 1e-7 and
            abs(actual_volume_m3/reference_volume_m3-1) < 1e-7, 'SI scale mismatch')
    return True


def verify_hashes(root, records):
    for filename, record in records.items():
        digest = record if isinstance(record, str) else record['sha256']
        require(hashlib.sha256((root/filename).read_bytes()).hexdigest() == digest,
                'protected identity changed: '+filename)
    return True
