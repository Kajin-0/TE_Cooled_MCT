"""New independent canonical-registry CAD and conformal header mesh checkpoint.

The cooler is represented by its two external ceramics, NOT by a fake 88-leg
solver. Cap outline, hot-pad markers and wire paths are previews only. Revised
electrical/thermal physics must pass separate gates before any device claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from .geometry_registry import load, value, pins, profile, analytic_metrics, ROOT


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2)+'\n')


def cad_outline(occ, data, scale=1.):
    """Exact CAD arcs/common tangents; independent of mesh primitive CSG."""
    R = value(data, 'central_radius')*scale; r = value(data, 'ear_radius')*scale
    d = value(data, 'hole_pitch')/2*scale; a = (R-r)/d; b = np.sqrt(1-a*a)
    # CCW from lower right ear tangent.
    xy = [(d+a*r, -b*r), (d+a*r, b*r), (a*R, b*R), (-a*R, b*R),
          (-d-a*r, b*r), (-d-a*r, -b*r), (-a*R, -b*R), (a*R, -b*R)]
    pts = [occ.addPoint(x, y, 0) for x, y in xy]
    centers = [occ.addPoint(x, 0, 0) for x in (d, 0, -d)]
    edges = [occ.addCircleArc(pts[0], centers[0], pts[1]), occ.addLine(pts[1], pts[2]),
             occ.addCircleArc(pts[2], centers[1], pts[3]), occ.addLine(pts[3], pts[4]),
             occ.addCircleArc(pts[4], centers[2], pts[5]), occ.addLine(pts[5], pts[6]),
             occ.addCircleArc(pts[6], centers[1], pts[7]), occ.addLine(pts[7], pts[0])]
    return occ.addPlaneSurface([occ.addWire(edges)])


def mesh_outline(occ, data):
    """SI construction by union of three disks and two tangent trapezoids."""
    R = value(data, 'central_radius')*.001; r = value(data, 'ear_radius')*.001
    d = value(data, 'hole_pitch')*.0005; a = (R-r)/d; b = np.sqrt(1-a*a)
    surfaces = [(2, occ.addDisk(0, 0, 0, R, R)),
                (2, occ.addDisk(-d, 0, 0, r, r)), (2, occ.addDisk(d, 0, 0, r, r))]
    for sign in (-1, 1):
        pts = [occ.addPoint(sign*x, y, 0) for x, y in
               ((a*R, b*R), (d+a*r, b*r), (d+a*r, -b*r), (a*R, -b*R))]
        loop = occ.addWire([occ.addLine(pts[i], pts[(i+1)%4]) for i in range(4)])
        surfaces.append((2, occ.addPlaneSurface([loop])))
    result, _ = occ.fuse(surfaces[:1], surfaces[1:])
    return [tag for dim, tag in result if dim == 2]


def solids(gmsh, data, mode):
    occ = gmsh.model.occ; s = 1. if mode == 'cad' else .001
    h = value(data, 'header_thickness')*s
    faces = [cad_outline(occ, data, s)] if mode == 'cad' else mesh_outline(occ, data)
    volumes = []
    for face in faces:
        ext = occ.extrude([(2, face)], 0, 0, h)
        volumes.extend((dim, tag) for dim, tag in ext if dim == 3)
    if len(volumes) > 1:
        volumes, _ = occ.fuse(volumes[:1], volumes[1:])
    if len(volumes) != 1:
        raise ValueError('Disconnected flange volume')
    header = volumes[0][1]
    hole_r = value(data, 'hole_diameter')/2*s; d = value(data, 'hole_pitch')/2*s
    holes = [(3, occ.addCylinder(x, 0, 0, 0, 0, h, hole_r)) for x in (-d, d)]
    glass_r = value(data, 'glass_od')/2*s; pin_r = value(data, 'pin_diameter')/2*s
    rows = pins(data); pinxy = np.array([row['xy_mm'] for row in rows])*s
    holes += [(3, occ.addCylinder(x, y, 0, 0, 0, h, glass_r)) for x, y in pinxy]
    cut, _ = occ.cut([(3, header)], holes)
    if len(cut) != 1:
        raise ValueError('Header cut failed')
    bodies = [(1, 'Kovar_header', cut[0][1])]
    below = value(data, 'pin_below_header')*s; stub = value(data, 'pin_stub')*s
    for row, (x, y) in zip(rows, pinxy):
        i = row['pin']; outer = occ.addCylinder(x, y, 0, 0, 0, h, glass_r)
        inner = occ.addCylinder(x, y, 0, 0, 0, h, pin_r)
        annulus, _ = occ.cut([(3, outer)], [(3, inner)])
        bodies.append((10+i, f'glass_pin{i}', annulus[0][1]))
        metal = occ.addCylinder(x, y, -below, 0, 0, below+h+stub, pin_r)
        bodies.append((20+i, f'metal_pin{i}_{row["function"]}', metal))
    w = value(data, 'tec_hot_width')*s; t = value(data, 'presolder_thickness')*s
    c = value(data, 'ceramic_thickness')*s; top = h+t+value(data, 'tec_height')*s
    cold = value(data, 'tec_cold_width')*s
    bodies += [(30, 'presolder_geometry_hypothesis', occ.addBox(-w/2, -w/2, h, w, w, t)),
               (31, 'hot_alumina_candidate', occ.addBox(-w/2, -w/2, h+t, w, w, c)),
               (32, 'cold_alumina_candidate_envelope_only', occ.addBox(-cold/2, -cold/2, top-c, cold, cold, c))]
    raw = [(3, row[2]) for row in bodies]
    _, mapping = occ.fragment(raw[:1], raw[1:]); occ.synchronize()
    mapped = []
    for (body, name, _), entities in zip(bodies, mapping):
        tags = [tag for dim, tag in entities if dim == 3]
        if len(tags) != 1:
            raise ValueError('Unexpected overlap/split: '+name)
        gmsh.model.addPhysicalGroup(3, tags, body); gmsh.model.setPhysicalName(3, body, name)
        mapped.append({'body': body, 'name': name, 'volume_entity': tags[0],
                       'volume_mm3': occ.getMass(3, tags[0])/s**3,
                       'surface_mm2': sum(occ.getMass(2, abs(tag)) for dim, tag in
                           gmsh.model.getBoundary([(3, tags[0])], oriented=False))/s**2})
    return mapped


def audit_mesh(gmsh, data, bodies, cad):
    nodeids, coords, _ = gmsh.model.mesh.getNodes(); order = np.argsort(nodeids)
    xyz = np.array(coords).reshape(-1, 3)[order]; ids = nodeids[order]
    cells = []; tags = []
    for row in bodies:
        types, _, node = gmsh.model.mesh.getElements(3, row['volume_entity'])
        if list(types) != [4]:
            raise ValueError('Only actual linear tetrahedra are audited')
        c = np.searchsorted(ids, np.array(node[0]).reshape(-1, 4)); cells.append(c)
        tags.extend([row['body']]*len(c))
    cells = np.concatenate(cells); tags = np.array(tags); p = xyz[cells]
    vol = abs(np.linalg.det(p[:, 1:]-p[:, :1]))/6
    faces = cells[:, [[1, 2, 3], [0, 3, 2], [0, 1, 3], [0, 2, 1]]].reshape(-1, 3)
    sortedf = np.sort(faces, axis=1); uniq, inv, count = np.unique(sortedf, axis=0, return_inverse=True, return_counts=True)
    if count.max() > 2 or vol.min() <= 0:
        raise ValueError('Invalid actual tetrahedron topology')
    sort = np.argsort(inv); offsets = np.r_[0, np.cumsum(count)]
    shared = np.where(count == 2)[0]; pairs = []
    for f in shared:
        a, b = tags[sort[offsets[f]:offsets[f+1]]//4]
        if a != b:
            pairs.append(tuple(sorted((int(a), int(b)))))
    adjacent = set(pairs)
    expected = {(1, 30), (30, 31)} | {(1, 10+i) for i in range(1, 10)} | {(10+i, 20+i) for i in range(1, 10)}
    if adjacent != expected:
        raise ValueError('Material-specific actual adjacency differs: '+str(adjacent ^ expected))
    audit = []; cad_by = {r['body']: r for r in cad}
    node_sets = {}
    for row in bodies:
        body = row['body']; ix = tags == body; nv = vol[ix].sum()*1e9
        subset = set(np.unique(cells[ix]).tolist()); node_sets[body] = subset
        # Material skin also includes shared contacts, independently of physical surface labels.
        first_body = tags[sort[offsets[:-1]]//4]
        last_body = tags[sort[offsets[1:]-1]//4]
        selected = np.flatnonzero((first_body == body) | (last_body == body))
        skin = selected[(count[selected] == 1) | (first_body[selected] != last_body[selected])]
        q = xyz[uniq[skin]]; area = (np.linalg.norm(np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0]), axis=1)/2).sum()*1e6
        cv = cad_by[body]['volume_mm3']; err = nv/cv-1
        if abs(err) > .01:
            raise ValueError('CAD to mesh volume exceeds1%: '+row['name'])
        audit.append({'body': body, 'name': row['name'], 'tetrahedra': int(ix.sum()),
                      'CAD_volume_mm3': cv, 'mesh_volume_mm3': float(nv),
                      'volume_relative_error': float(err), 'CAD_surface_mm2': cad_by[body]['surface_mm2'],
                      'mesh_surface_mm2': float(area),
                      'bbox_mm': [xyz[list(subset)].min(0).tolist(), xyz[list(subset)].max(0).tolist()]})
        audit[-1]['bbox_mm'] = (np.array(audit[-1]['bbox_mm'])*1000).tolist()
    # Pin metal must not even share a vertex with header or another pin.
    for i in range(21, 30):
        if node_sets[i] & node_sets[1]:
            raise ValueError('Pin/header short')
        for j in range(i+1, 30):
            if node_sets[i] & node_sets[j]:
                raise ValueError('Pin/pin short')
    return xyz, cells, tags, {'nodes': len(xyz), 'tetrahedra': len(cells), 'domains': len(bodies),
        'material_contacts': [list(p) for p in sorted(adjacent)], 'metal_pin_isolation_passed': True,
        'partial_header_mesh_passed': True, 'full_88leg_series_gate': 'NOT RUN: external ceramic envelopes only',
        'detector_and_thermistor_circuits': 'pin identities correct; internal bonds/circuits pending',
        'cold_envelope_disconnection': 'deliberate; no internal TEC solids in this first geometry checkpoint',
        'bodies': audit}


def overlay(data, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    curve = profile(data); trace = json.loads((ROOT/'data/geometry_rebaseline/vigo_outline_trace.json').read_text())
    source = np.array(trace['xy_mm']); closed = np.vstack([curve, curve[:1]])
    # Point to polyline distances, so long straight source segments are handled fairly.
    def distance(points, line):
        a = line; b = np.roll(line, -1, axis=0); v = b-a
        t = np.clip(np.einsum('pni,ni->pn', points[:, None]-a, v)/(v*v).sum(1), 0, 1)
        return np.linalg.norm(points[:, None]-(a+t[:, :, None]*v), axis=2).min(1)
    forward = distance(source, curve); backward = distance(curve, source)
    maximum = float(max(forward.max(), backward.max()))
    # Predeclared engineering overlay target includes source plot vectorization;
    # it is not a manufacturing contour tolerance or an as-built measurement.
    if maximum > .08:
        raise ValueError('Source silhouette discrepancy exceeds0.08mm')
    fig, ax = plt.subplots(figsize=(11, 5)); ax.plot(*np.vstack([source, source[:1]]).T, color='black', lw=2, label='Source top-view numerical trace')
    ax.plot(*closed.T, '--', color='#b13c36', label='Independent tangent CAD reference')
    ax.add_patch(plt.Circle((0, 0), value(data, 'cap_od')/2, fill=False, color='#7393ad', label='Source case OD envelope'))
    for x in (-value(data, 'hole_pitch')/2, value(data, 'hole_pitch')/2):
        ax.add_patch(plt.Circle((x, 0), value(data, 'hole_diameter')/2, fill=False, color='black'))
    for row in pins(data):
        ax.add_patch(plt.Circle(row['xy_mm'], value(data, 'pin_diameter')/2, color='#33758a'))
        ax.annotate(str(row['pin']), row['xy_mm'], xytext=(4, 3), textcoords='offset points', fontsize=8)
    w = value(data, 'tec_hot_width'); c = value(data, 'tec_cold_width')
    for width in (w, c):ax.add_patch(plt.Rectangle((-width/2, -width/2), width, width, fill=False, color='#8d713b'))
    ax.annotate('31.5 mm', (0, 9.6), ha='center'); ax.annotate('24.4 mm hole pitch', (0, -10), ha='center')
    ax.plot([13, 14], [-8, -8], color='black', lw=3); ax.text(13.5, -7.6, '1 mm', ha='center')
    ax.set(xlabel='Top-view x (mm)', ylabel='Top-view y (mm)', title=f'Selected reference geometry — source overlay max {maximum:.3f} mm\nHousing + independent TEC candidate; commercial compatibility unverified')
    ax.set_aspect('equal'); ax.set_xlim(-17, 17); ax.set_ylim(-11, 11); ax.legend(fontsize=8, loc='upper left'); fig.tight_layout(); fig.savefig(out/'source_overlay.png', dpi=300); plt.close(fig)
    fig, axs = plt.subplots(1, 2, figsize=(11, 5))
    for ax, view in zip(axs, ('bottom', 'top')):
        for row in pins(data, view):
            ax.add_patch(plt.Circle(row['xy_mm'], value(data, 'pin_diameter')/2, color='#a1483d' if row['pin'] in (1, 9) else '#33758a'))
            ax.annotate(f'{row["pin"]}: {row["function"]}', row['xy_mm'], xytext=(5, 5), textcoords='offset points', fontsize=8)
        ax.plot([4, 5], [-6, -6], lw=3, color='black'); ax.text(4.5, -5.7, '1 mm', ha='center')
        ax.set(xlim=(-7.5, 7.5), ylim=(-7, 7), xlabel='x (mm)', ylabel='y (mm)', title=view+' view'); ax.set_aspect('equal'); ax.grid(alpha=.2)
    fig.suptitle('Explicit mirror with page-up fixed: x_top = −x_bottom; y_top = y_bottom'); fig.tight_layout(); fig.savefig(out/'pin_views.png', dpi=300); plt.close(fig)
    return {'max_bidirectional_polyline_distance_mm': maximum, 'source_reading_uncertainty_mm': trace['reading_uncertainty_mm'],
            'acceptance_target_mm': .08, 'target_kind': 'source drawing comparison, not manufactured tolerance',
            'trace_sha256': sha(ROOT/'data/geometry_rebaseline/vigo_outline_trace.json')}


def build(out, h_mm=.8):
    import gmsh
    data = load(); out.mkdir(parents=True, exist_ok=False)
    write(out/'registry_snapshot.json', data); before = sha(ROOT/'data/geometry_rebaseline/reference_v1.json')
    gmsh.initialize(); gmsh.option.setNumber('General.NumThreads', 4)
    try:
        gmsh.model.add('independent_mm_CAD'); cad = solids(gmsh, data, 'cad')
        gmsh.write(str(out/'reference.step'))
        gmsh.clear(); gmsh.model.add('independent_SI_mesh_CSG'); body = solids(gmsh, data, 'mesh')
        gmsh.option.setNumber('Mesh.MeshSizeMax', h_mm*.001)
        gmsh.option.setNumber('Mesh.MeshSizeMin', .00004)
        gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 40)
        gmsh.option.setNumber('Mesh.MinimumCirclePoints', 40)
        gmsh.option.setNumber('Mesh.Algorithm3D', 10)
        gmsh.model.mesh.generate(3); gmsh.write(str(out/'geometry.msh'))
        xyz, cells, tags, audit = audit_mesh(gmsh, data, body, cad)
        np.savez_compressed(out/'mesh.npz', points=xyz, cells=cells, bodies=tags)
    finally:gmsh.finalize()
    if before != sha(ROOT/'data/geometry_rebaseline/reference_v1.json'):
        raise ValueError('Registry changed during generation')
    independent = analytic_metrics(data)
    header = next(r for r in cad if r['body'] == 1)
    if not np.isclose(header['volume_mm3'], independent['header_volume_mm3'], rtol=1e-8):
        raise ValueError('Independent analytic/CAD flange volume disagreement')
    if not np.isclose(header['surface_mm2'], independent['header_surface_mm2'], rtol=1e-8):
        raise ValueError('Independent analytic/CAD flange surface disagreement')
    source_check = overlay(data, out)
    write(out/'geometry_audit.json', {'scope': data['meshing_scope'], 'identity': data['identity'],
        'registry_sha256': before, 'h_max_mm': h_mm, 'analytic': independent,
        'CAD': cad, 'actual_mesh': audit, 'source_overlay': source_check,
        'revised_full_device_physics': 'NOT RUN', 'preserved_raw_bath_gate': 'historical fine points remain FAILED',
        'source_sha256': {p.name: sha(p) for p in [Path(__file__), ROOT/'tecooledmct/geometry_registry.py', ROOT/'tecooledmct/geometry_source_trace.py']}})
    print('New independent geometry checkpoint passed:', audit['nodes'], 'nodes,', audit['tetrahedra'], 'tets;', source_check, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--h-mm', type=float, default=.8); args = parser.parse_args()
    if not .3 <= args.h_mm <= 1.2:raise ValueError('Bounded geometry mesh0.3..1.2mm')
    build(args.out.resolve(), args.h_mm)
