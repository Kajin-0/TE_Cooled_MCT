"""Bounded-by-worker-time complete BVH traversal of linear facet intersections.

Expected boundary-only contacts are not positive-area/interior intersections.
All distances are in the mesh's millimetres; no CAD or mesh is modified.
"""
import time
import numpy as np


def intersect_pairs(a, b, relative_tolerance=1e-10, coplanar_distance_mm=1e-9):
    a, b = np.asarray(a, float), np.asarray(b, float)
    hit = np.zeros(len(a), bool)
    if not len(a):
        return hit
    na = np.cross(a[:, 1]-a[:, 0], a[:, 2]-a[:, 0])
    nb = np.cross(b[:, 1]-b[:, 0], b[:, 2]-b[:, 0])
    an, bn = np.linalg.norm(na, axis=1), np.linalg.norm(nb, axis=1)
    parallel = np.linalg.norm(np.cross(na, nb), axis=1) <= relative_tolerance*an*bn
    plane = np.max(abs(np.einsum('nvi,ni->nv', b-a[:, :1], na)), axis=1)/an
    coplanar = parallel & (plane <= coplanar_distance_mm)
    if np.any(coplanar):
        aa, bb, normal = a[coplanar], b[coplanar], na[coplanar]
        drop = np.argmax(abs(normal), axis=1)
        axes = np.stack(((drop+1) % 3, (drop+2) % 3), axis=1)
        aa = np.take_along_axis(aa, axes[:, None, :], axis=2)
        bb = np.take_along_axis(bb, axes[:, None, :], axis=2)
        e = np.concatenate((np.roll(aa, -1, axis=1)-aa, np.roll(bb, -1, axis=1)-bb), axis=1)
        normals = np.stack((-e[:, :, 1], e[:, :, 0]), axis=-1)
        pa = np.einsum('nvi,nai->nva', aa, normals)
        pb = np.einsum('nvi,nai->nva', bb, normals)
        overlap = np.minimum(pa.max(axis=1), pb.max(axis=1))-np.maximum(pa.min(axis=1), pb.min(axis=1))
        hit[coplanar] = np.all(overlap > 1e-10*np.linalg.norm(normals, axis=2), axis=1)
    nonparallel = ~parallel
    if np.any(nonparallel):
        aa, bb = a[nonparallel], b[nonparallel]
        result = np.zeros(len(aa), bool)
        for segment, triangle in ((aa, bb), (bb, aa)):
            e1, e2 = triangle[:, 1]-triangle[:, 0], triangle[:, 2]-triangle[:, 0]
            for j in range(3):
                start, end = segment[:, j], segment[:, (j+1) % 3]
                d = end-start
                h = np.cross(d, e2)
                det = np.einsum('ni,ni->n', e1, h)
                scale = np.linalg.norm(d, axis=1)*np.linalg.norm(e1, axis=1)*np.linalg.norm(e2, axis=1)
                valid = abs(det) > relative_tolerance*scale
                inv = np.zeros(len(det))
                inv[valid] = 1/det[valid]
                s = start-triangle[:, 0]
                u = inv*np.einsum('ni,ni->n', s, h)
                q = np.cross(s, e1)
                v = inv*np.einsum('ni,ni->n', d, q)
                t = inv*np.einsum('ni,ni->n', e2, q)
                eps = relative_tolerance
                result |= valid & (u > eps) & (v > eps) & (u+v < 1-eps) & (t >= -eps) & (t <= 1+eps)
        hit[nonparallel] = result
    return hit


def full_intersection_check(points, triangles, face_ids, progress=None, leaf_size=16):
    start = time.monotonic()
    xyz = np.asarray(points)[np.asarray(triangles)]
    lower, upper = xyz.min(axis=1), xyz.max(axis=1)
    center = (lower+upper)/2
    order = np.arange(len(xyz), dtype=np.int64)
    bounds_lo, bounds_hi, left, right, starts, ends = [], [], [], [], [], []

    def build(lo, hi):
        ident = len(left)
        ids = order[lo:hi]
        bounds_lo.append(lower[ids].min(axis=0));bounds_hi.append(upper[ids].max(axis=0))
        left.append(-1);right.append(-1);starts.append(lo);ends.append(hi)
        if hi-lo > leaf_size:
            axis = int(np.argmax(np.ptp(center[ids], axis=0)))
            count = (hi-lo)//2
            partition = np.argpartition(center[ids, axis], count)
            order[lo:hi] = ids[partition]
            left[ident] = build(lo, lo+count)
            right[ident] = build(lo+count, hi)
        return ident

    build(0, len(xyz))
    bounds_lo, bounds_hi = np.asarray(bounds_lo), np.asarray(bounds_hi)
    stack = [(0, 0)]
    visited = candidates = tested = 0
    last_progress = time.monotonic()
    while stack:
        i, j = stack.pop();visited += 1
        if np.any(bounds_lo[i] > bounds_hi[j]+1e-10) or np.any(bounds_lo[j] > bounds_hi[i]+1e-10):
            continue
        if i == j and left[i] >= 0:
            stack.extend(((left[i], left[i]), (left[i], right[i]), (right[i], right[i])))
            continue
        if left[i] >= 0 or left[j] >= 0:
            if left[j] < 0 or (left[i] >= 0 and ends[i]-starts[i] >= ends[j]-starts[j]):
                stack.extend(((left[i], j), (right[i], j)))
            else:
                stack.extend(((i, left[j]), (i, right[j])))
            continue
        a, b = np.meshgrid(order[starts[i]:ends[i]], order[starts[j]:ends[j]], indexing='ij')
        a, b = a.ravel(), b.ravel()
        if i == j:
            keep = a < b;a, b = a[keep], b[keep]
        candidates += len(a)
        keep = np.all(lower[a] <= upper[b]+1e-10, axis=1) & np.all(lower[b] <= upper[a]+1e-10, axis=1)
        a, b = a[keep], b[keep]
        tested += len(a)
        if len(a):
            hits = intersect_pairs(xyz[a], xyz[b])
            if np.any(hits):
                pairs = [(int(x), int(y)) for x, y in zip(a[hits], b[hits])]
                return dict(status='FAIL MEASURED FACET INTERSECTION', traversal_complete=False,
                    measured_proper_intersections=len(pairs), witnesses=[dict(triangles=[x, y],
                        native_faces=[int(face_ids[x]), int(face_ids[y])]) for x, y in pairs[:16]],
                    visited_node_pairs=visited, broad_candidate_pairs=candidates, tested_pairs=tested,
                    seconds=time.monotonic()-start, boundary_touching_excluded=True)
        if progress and time.monotonic()-last_progress > 1:
            progress(dict(visited_node_pairs=visited, broad_candidate_pairs=candidates,
                          tested_pairs=tested, stack_remaining=len(stack), seconds=time.monotonic()-start))
            last_progress = time.monotonic()
    return dict(status='PASS COMPLETE LINEAR FACET INTERSECTION CHECK', traversal_complete=True,
        measured_proper_intersections=0, witnesses=[], visited_node_pairs=visited,
        broad_candidate_pairs=candidates, tested_pairs=tested, seconds=time.monotonic()-start,
        boundary_touching_excluded=True, leaf_size=leaf_size,
        relative_tolerance=1e-10, coplanar_distance_mm=1e-9)
