"""Independent local surface arithmetic/topology controls; no geometry or PDE."""
from __future__ import annotations
import math
import numpy as np


def triangle_metrics(points, triangles, exact_area):
    p = np.asarray(points, float)
    t = np.asarray(triangles, np.int64)
    if t.ndim != 2 or t.shape[1] != 3 or not len(t) or not math.isfinite(exact_area) or exact_area <= 0:
        raise ValueError('missing triangles or invalid CAD area')
    if t.min() < 0 or t.max() >= len(p) or not np.isfinite(p).all():
        raise ValueError('invalid node identity/coordinate')
    v = p[t]
    edges = np.stack((v[:, 1]-v[:, 0], v[:, 2]-v[:, 1], v[:, 0]-v[:, 2]), axis=1)
    lengths = np.linalg.norm(edges, axis=2)
    # Gram determinant, independent of the producer's native-parametric grid.
    u, w = v[:, 1]-v[:, 0], v[:, 2]-v[:, 0]
    gram = np.einsum('ij,ij->i', u, u)*np.einsum('ij,ij->i', w, w)-np.einsum('ij,ij->i', u, w)**2
    if not np.isfinite(gram).all() or np.any(gram <= 0) or np.any(lengths <= 0):
        raise ValueError('degenerate/nonpositive triangle')
    area = .5*np.sqrt(gram)
    err = float(area.sum()/exact_area-1)
    return dict(triangles=len(t), mesh_area_mm2=float(area.sum()), CAD_area_mm2=float(exact_area),
                relative_area_error=err, area_PASS=abs(err) < .01,
                minimum_area_mm2=float(area.min()), min_edge_mm=float(lengths.min()),
                max_edge_mm=float(lengths.max()),
                edge_quantiles_mm=list(map(float, np.quantile(lengths, [0, .01, .5, .99, 1]))),
                max_edge_aspect=float((lengths.max(axis=1)/lengths.min(axis=1)).max()))


def check_face_edges(triangles, curve_segments, boundary_multiplicity):
    """Every CAD curve segment has exactly its source seam multiplicity."""
    t = np.asarray(triangles, np.int64)
    all_edges = np.sort(np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]])), axis=1)
    unique, counts = np.unique(all_edges, axis=0, return_counts=True)
    incidence = {tuple(map(int, e)): int(n) for e, n in zip(unique, counts)}
    if any(n not in (1, 2) for n in counts):
        raise ValueError('nonmanifold face triangulation')
    expected_open = set()
    expected = set()
    for curve, multiplicity in boundary_multiplicity.items():
        segments = np.sort(np.asarray(curve_segments[curve], np.int64), axis=1)
        if not len(segments) or multiplicity not in (1, 2):
            raise ValueError('missing curve or invalid seam multiplicity')
        if len(np.unique(segments, axis=0)) != len(segments):
            raise ValueError('duplicated source curve segment')
        for e in segments:
            key = tuple(map(int, e))
            if key in expected:
                raise ValueError('distinct CAD curves claim same mesh edge')
            expected.add(key)
            if incidence.get(key) != multiplicity:
                raise ValueError('CAD edge nodes/face incidence mismatch')
            if multiplicity == 1:
                expected_open.add(key)
    actual_open = {key for key, n in incidence.items() if n == 1}
    if actual_open != expected_open:
        raise ValueError('unassigned boundary edge/crack')
    return dict(status='PASS EXACT SOURCE-CURVE INCIDENCE', source_curves=len(boundary_multiplicity),
                source_segments=len(expected), open_edges=len(actual_open),
                repeated_seam_curves=sum(n == 2 for n in boundary_multiplicity.values()))


def validate_result(result, inventory):
    if result['status'] != 'PASS LOCAL SURFACE ONLY':
        raise ValueError('local mesh not accepted')
    selected = inventory['groups'][result['fixture']]
    if set(map(int, result['faces'])) != set(selected) or result['extra_meshed_faces']:
        raise ValueError('local face coverage/global-mesh scope violation')
    if result['tetrahedra'] or not result['source_identity_PASS']:
        raise ValueError('unexpected volume mesh or source identity failure')
    for key, face in result['faces'].items():
        src = inventory['faces'][key]
        if face['owners'] != src['owners'] or face['owner_volume_ids'] != src['owner_volume_ids']:
            raise ValueError('native owner identity changed')
        if not math.isfinite(face['relative_area_error']) or abs(face['relative_area_error']) >= .01:
            raise ValueError('strict1% per-face gate')
        if face['triangles'] <= 0 or face['minimum_area_mm2'] <= 0 or not face['area_PASS']:
            raise ValueError('invalid local triangles')
        if not face['conformity']['status'].startswith('PASS'):
            raise ValueError('shared-edge conformity failed')
    for q in result['R2_ancestor_comparison'].values():
        if q['status'] == 'COMPLETE LOCAL DESCENDANTS' and abs(q['relative_area_error']) >= .01:
            raise ValueError('strict1% complete R2 ancestor gate')
    if result['global_mesh_RUN'] or result['PDE_RUN'] or result['solver_ready']:
        raise ValueError('unqualified global/physical claim')
    return True
