"""Pure no-mesher R3.2 global-surface gates and oriented incidence arithmetic."""
from __future__ import annotations
import numpy as np

DIRECTIONAL_FACES = frozenset((*range(2385, 2390), *range(2397, 2402)))


def require(value, reason):
    if not value:
        raise ValueError(reason)


def directed_edges(triangles):
    t = np.asarray(triangles, np.int64)
    e = np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]))
    sign = np.where(e[:, 0] < e[:, 1], 1, -1)
    e.sort(axis=1)
    order = np.lexsort((e[:, 1], e[:, 0]))
    e, sign = e[order], sign[order]
    starts = np.flatnonzero(np.r_[True, np.any(e[1:] != e[:-1], axis=1)])
    counts = np.diff(np.r_[starts, len(e)])
    sums = np.add.reduceat(sign, starts)
    return e[starts], counts, sums


def boundary_sign(triangles, segments, signed_curves):
    """Return +/-1 only if complete boundary agrees with one CAD orientation."""
    e, counts, sums = directed_edges(triangles)
    require(np.all((counts == 1) | (counts == 2)), 'nonmanifold face triangle edges')
    actual = {tuple(map(int, edge)): int(v) for edge, v in zip(e, sums) if v}
    expected = {}
    for signed in signed_curves:
        for a, b in segments[abs(signed)]:
            a, b = int(a), int(b)
            key = (min(a, b), max(a, b))
            value = (1 if signed > 0 else -1)*(1 if a < b else -1)
            expected[key] = expected.get(key, 0)+value
    expected = {e: v for e, v in expected.items() if v}
    require(expected, 'no nonseam CAD boundary; orientation not inferred')
    if actual == expected:
        return 1
    if actual == {e: -v for e, v in expected.items()}:
        return -1
    raise ValueError('face winding not uniformly consistent with exact CAD boundary')


def skin_incidence(triangles):
    e, counts, sums = directed_edges(triangles)
    return dict(edges=len(e), open_or_nonmanifold_edges=int(np.count_nonzero(counts != 2)),
                inconsistent_oriented_edges=int(np.count_nonzero(sums != 0)),
                PASS=bool(np.all(counts == 2) and np.all(sums == 0)))


def validate_registration(registration, source):
    require(registration['runs'] == 1 and registration['wall_limit_seconds'] == 600., 'single600s schedule')
    require(registration['CPUs'] == 4 and registration['memory_GiB'] == 8, 'resource bounds')
    require(registration['triangle_limit'] == 800000, 'surface count limit')
    require(set(registration['directional_faces']) == DIRECTIONAL_FACES, 'exact ten directional faces')
    require(set(source['faces']) == set(source['face_registry']), 'native face metadata missing')
    require(len(source['faces']) == 2440 and len(source['domain_id_map']) == 430, 'full source identities')
    require(registration['tetrahedralization'] == registration['PDE'] == 'NOT AUTHORIZED', 'out-of-scope physics')
    return True


def validate_mesh_evidence(result, check_intersections=True):
    require(set(result['directional_patches']) == set(map(str, DIRECTIONAL_FACES)), 'directional scope changed')
    require(result['surface_faces'] == len(result['faces']) == 2440, 'all2440 faces required')
    require(result['volume_metadata_count'] == 430 and result['tetrahedra'] == 0, '430 metadata/no tets')
    require(result['triangles'] <= 800000, '800000 triangle budget')
    require(not result['missing_faces'] and not result['ownership_errors'], 'physical groups or owners')
    require(result['volume_physical_groups_PASS'] and result['duplicate_element_tags'] == 0,
            'volume labels or duplicate element IDs')
    for q in result['faces'].values():
        require(q['triangles'] > 0 and q['positive_triangles'], 'nonpositive/missing elements')
        require(np.isfinite(q['relative_area_error']) and abs(q['relative_area_error']) < .01, 'strict per-face1%')
        require(q['conformity_PASS'] and q['CAD_winding_PASS'], 'source edge/seam orientation')
    require(len(result['R2_ancestors']) == 2422, 'all R2 ancestor identities')
    require(all(abs(q['relative_area_error']) < .01 for q in result['R2_ancestors'].values()), 'strict ancestor1%')
    require(all(q['PASS'] for q in result['closed_volume_skins'].values()) and len(result['closed_volume_skins']) == 430,
            'closed/oriented skins for every source volume')
    require(result['duplicate_node_triplets'] == result['duplicate_geometric_triplets'] == 0, 'duplicate facets')
    require(result['normal_samples']['mixed_sign_faces'] == [], 'sampled folded normal orientation')
    require(result['normal_samples']['faces_measured'] == 2440 and not result['normal_samples']['unmeasured_faces'],
            'normal sampling incomplete')
    if check_intersections:
        require(result['intersections'].get('traversal_complete', False) and
                result['intersections']['measured_proper_intersections'] == 0, 'intersections fail/unmeasured')
    require(not result['PDE_RUN'] and not result['solver_ready'], 'unqualified physics claim')
    return True
