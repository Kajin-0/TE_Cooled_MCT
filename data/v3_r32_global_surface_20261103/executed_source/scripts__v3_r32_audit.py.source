"""Global surface metrics on the current model; no meshing, CAD change or PDE."""
import collections
import numpy as np
import gmsh
from tecooledmct.v3_r31_mesh_integrity import triangle_metrics, check_face_edges
from tecooledmct.v3_r32_surface_integrity import boundary_sign, skin_incidence

PERCENTILES = [0, .01, .05, .5, .95, .99, 1]
LABELS = ['min', 'p01', 'p05', 'median', 'p95', 'p99', 'max']


def distribution(values):
    return dict(zip(LABELS, map(float, np.quantile(values, PERCENTILES))))


def mesh_arrays():
    tags, xyz, _ = gmsh.model.mesh.getNodes()
    tags = np.asarray(tags, np.int64)
    points = np.asarray(xyz).reshape(-1, 3)
    lookup = np.full(int(tags.max())+1, -1, np.int64)
    lookup[tags] = np.arange(len(tags))
    return tags, points, lookup


def curves(source):
    out = {}
    for e in source['curves']:
        kinds, _, arrays = gmsh.model.mesh.getElements(1, int(e))
        if list(kinds) != [1]:
            raise ValueError('Missing/nonlinear native curve '+e)
        out[int(e)] = np.asarray(arrays[0], np.int64).reshape(-1, 2)
    return out


def normalize_winding(source):
    segments = curves(source)
    reverse, failures = [], {}
    for f, q in source['faces'].items():
        kinds, _, arrays = gmsh.model.mesh.getElements(2, int(f))
        if list(kinds) != [2]:
            failures[f] = 'missing/nonlinear face'
            continue
        try:
            sign = boundary_sign(np.asarray(arrays[0], np.int64).reshape(-1, 3), segments, q['signed_boundary_curves'])
            if sign < 0:
                reverse.append(int(f))
        except ValueError as ex:
            failures[f] = str(ex)
    if reverse:
        gmsh.model.mesh.reverse([(2, f) for f in reverse])
    return dict(status='PASS CAD WINDING NORMALIZATION' if not failures else 'FAIL CAD WINDING',
                reversed_faces=reverse, incompatible_faces=failures,
                physical_geometry_changed=False, source_oriented_boundaries=True)


def metrics(source, result, progress=None, CAD_normals=True):
    tags, points, lookup = mesh_arrays()
    if not np.isfinite(points).all():
        raise ValueError('Nonfinite coordinates')
    segments = curves(source)
    rows, tri_by_face, ids_by_face = {}, {}, {}
    quality, lengths, aspects = [], [], []
    normal_angles, normal_distances = [], []
    normal_faces, mixed, unavailable = {}, [], {}
    missing, owners = [], []
    element_ids, blocks, block_faces = [], [], []
    for index, (f, src) in enumerate(source['faces'].items()):
        face = int(f)
        up = sorted(map(int, gmsh.model.getAdjacencies(2, face)[0]))
        if up != src['owner_volume_ids'] or face not in gmsh.model.getPhysicalGroupsForEntity(2, face):
            owners.append(face)
        kinds, ids, arrays = gmsh.model.mesh.getElements(2, face)
        if list(kinds) != [2]:
            missing.append(face)
            rows[f] = dict(triangles=0, mesh_area_mm2=0., CAD_area_mm2=src['face_area_mm2'],
                           relative_area_error=-1., positive_triangles=False, conformity_PASS=False,
                           CAD_winding_PASS=False, owners=src['owners'], owner_volume_ids=up)
            unavailable[f] = 'No linear native face mesh'
            continue
        tri = np.asarray(arrays[0], np.int64).reshape(-1, 3)
        if np.any(lookup[tri] < 0):
            raise ValueError('Triangle references missing node')
        tri_by_face[face] = tri
        ids_by_face[face] = np.asarray(ids[0], np.int64)
        v = points[lookup[tri]]
        metrics_row = triangle_metrics(points, lookup[tri], src['face_area_mm2'])
        cross = np.cross(v[:, 1]-v[:, 0], v[:, 2]-v[:, 0])
        area2 = np.linalg.norm(cross, axis=1)
        edge = np.stack((v[:, 1]-v[:, 0], v[:, 2]-v[:, 1], v[:, 0]-v[:, 2]), axis=1)
        ll = np.linalg.norm(edge, axis=2)
        qq = 2*np.sqrt(3)*area2/np.sum(ll*ll, axis=1)
        aa = ll.max(axis=1)/ll.min(axis=1)
        quality.append(qq);lengths.append(ll.ravel());aspects.append(aa)
        conformity_PASS = winding_PASS = True
        err = {}
        try:
            check_face_edges(tri, segments, collections.Counter(src['boundary_with_multiplicity']))
        except ValueError as ex:
            conformity_PASS = False;err['conformity'] = str(ex)
        try:
            winding_PASS = boundary_sign(tri, segments, src['signed_boundary_curves']) == 1
        except ValueError as ex:
            winding_PASS = False;err['winding'] = str(ex)
        rows[f] = dict(metrics_row, positive_triangles=bool(np.all(area2 > 0)),
            conformity_PASS=conformity_PASS, CAD_winding_PASS=winding_PASS,
            owners=src['owners'], owner_volume_ids=up, errors=err,
            quality=distribution(qq), edge_aspect=distribution(aa))
        element_ids.append(ids_by_face[face]);blocks.append(tri);block_faces.extend([face]*len(tri))
        if CAD_normals:
            try:
                sample = np.unique(np.linspace(0, len(tri)-1, min(8, len(tri)), dtype=int))
                center = v[sample].mean(axis=1)
                closest, uv = gmsh.model.getClosestPoint(2, face, center.ravel())
                closest = np.asarray(closest).reshape(-1, 3)
                nn = np.asarray(gmsh.model.getNormal(face, uv)).reshape(-1, 3)
                nt = cross[sample]/area2[sample, None]
                nn /= np.linalg.norm(nn, axis=1)[:, None]
                dot = np.einsum('ij,ij->i', nn, nt)
                if not np.isfinite(dot).all():
                    raise ValueError('nonfinite normal sample')
                angle = np.degrees(np.arccos(np.clip(abs(dot), 0, 1)))
                distance = np.linalg.norm(center-closest, axis=1)
                if np.any(dot > 1e-8) and np.any(dot < -1e-8):
                    mixed.append(face)
                normal_faces[f] = dict(samples=len(sample), max_unsigned_angle_deg=float(angle.max()),
                    max_centroid_distance_mm=float(distance.max()), positive_dot=int(np.count_nonzero(dot > 0)),
                    negative_dot=int(np.count_nonzero(dot < 0)))
                normal_angles.extend(map(float, angle));normal_distances.extend(map(float, distance))
            except Exception as ex:
                unavailable[f] = repr(ex)
        if progress and index % 50 == 0:
            progress(dict(measured_faces=index+1, current_face=face,
                          area_failures=[k for k, q in rows.items() if abs(q['relative_area_error']) >= .01]))
    tri = np.concatenate(blocks)
    by_face = np.asarray(block_faces, np.int64)
    ids = np.concatenate(element_ids)
    sorted_tri = np.sort(tri, axis=1)
    duplicate = len(sorted_tri)-len(np.unique(sorted_tri, axis=0))
    quantized = np.rint(points/1e-10).astype(np.int64)
    _, coordinate_ids = np.unique(quantized, axis=0, return_inverse=True)
    geometric_tri = np.sort(coordinate_ids[lookup[tri]], axis=1)
    duplicate_geo = len(tri)-len(np.unique(geometric_tri, axis=0))
    ancestors = {}
    for p, children in source['R2_face_descendants'].items():
        exact = sum(source['faces'][str(f)]['face_area_mm2'] for f in children)
        actual = sum(rows[str(f)]['mesh_area_mm2'] for f in children)
        ancestors[p] = dict(children=children, CAD_area_mm2=exact, mesh_area_mm2=actual,
                            relative_area_error=actual/exact-1)
    skins = {}
    for name, volume in source['domain_id_map'].items():
        parts = []
        for f, q in source['faces'].items():
            if volume in q['owner_volume_ids'] and int(f) in tri_by_face:
                t = tri_by_face[int(f)]
                sign = q['orientation_signs'][q['owner_volume_ids'].index(volume)]
                parts.append(t if sign > 0 else t[:, [0, 2, 1]])
        if not parts:
            skins[name] = dict(PASS=False, error='no skin');continue
        skins[name] = skin_incidence(np.concatenate(parts))
        skins[name]['surface_triangles'] = sum(len(t) for t in parts)
        expected_faces = [int(f) for f, q in source['faces'].items() if volume in q['owner_volume_ids']]
        if any(f in missing for f in expected_faces):
            skins[name]['PASS'] = False
    result.update(surface_faces=len(rows), faces=rows, R2_ancestors=ancestors,
        triangles=len(tri), nodes=len(tags), used_surface_nodes=len(np.unique(tri)),
        volume_metadata_count=len(gmsh.model.getEntities(3)), tetrahedra=sum(len(a) for a in gmsh.model.mesh.getElements(3)[1]),
        volume_physical_groups_PASS=all(tag in gmsh.model.getPhysicalGroupsForEntity(3,tag) for tag in source['domain_id_map'].values()),
        missing_faces=missing, ownership_errors=owners, duplicate_node_triplets=duplicate,
        duplicate_geometric_triplets=duplicate_geo, duplicate_element_tags=len(ids)-len(np.unique(ids)),
        quality=distribution(np.concatenate(quality)), edge_lengths_mm=distribution(np.concatenate(lengths)),
        edge_aspect=distribution(np.concatenate(aspects)), closed_volume_skins=skins,
        normal_samples=dict(faces_measured=len(normal_faces), faces=normal_faces, mixed_sign_faces=mixed,
            unmeasured_faces=unavailable,
            unsigned_angle_deg=distribution(normal_angles) if normal_angles else None,
            centroid_distance_mm=distribution(normal_distances) if normal_distances else None,
            definition='<=8 stratified triangles/face; chord centroid projected to underlying CAD, unsigned normal; not exhaustive/trim-aware Hausdorff'),
        maximum_face_area_error=max(abs(q['relative_area_error']) for q in rows.values()),
        failed_face_areas=[k for k, q in rows.items() if abs(q['relative_area_error']) >= .01],
        maximum_ancestor_area_error=max(abs(q['relative_area_error']) for q in ancestors.values()),
        failed_ancestor_areas=[k for k, q in ancestors.items() if abs(q['relative_area_error']) >= .01])
    poly_faces=[q for f,q in rows.items() if any('insulation' in n for n in q['owners'])]
    bond_faces=[rows[str(f)] for f in result['directional_face_ids'] if str(f) in rows]
    pins={}
    for name in ('pin1','pin7','pin8','pin9'):
        t=np.concatenate([tri_by_face[int(f)] for f,q in source['faces'].items() if name in q['owners'] and int(f) in tri_by_face])
        z=points[lookup[np.unique(t)],2]
        pins[name]=dict(nearest_node_to_axial_datums_mm={str(d):float(min(abs(z-d))) for d in (2.,2.002,2.0035)},
            law='EXPLICIT_AXIAL_KOVAR_NI_AU; UNSET', film_volume_mesh='NOT RUN')
    result['feature_resolution']=dict(
        jackets=dict(source_thickness_mm=.015, minimum_surface_edge_mm=min(q['min_edge_mm'] for q in poly_faces),
                     through_thickness_volume_resolution='NOT RUN'),
        directional_bonds=dict(source_radius_mm=.009, minimum_edge_mm=min(q['min_edge_mm'] for q in bond_faces),
                               interior_circumferential_divisions=48, axial_target_mm=.08),
        effective_pin_finishes=pins)
    return points, tri, by_face, lookup
