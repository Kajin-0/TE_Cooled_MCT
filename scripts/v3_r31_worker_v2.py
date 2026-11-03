"""One <=180s native-face benchmark worker. Never generates global or3D mesh."""
from pathlib import Path
import argparse
import collections
from contextlib import contextmanager
import datetime
import json
import math
import resource
import time

import gmsh
import numpy as np
from scipy.spatial import cKDTree

from scripts.v3_analysis_r3_surface import configure
from tecooledmct.v3_r31_mesh_integrity import triangle_metrics, check_face_edges, validate_result

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r31_local_mesh_20261103'
R3 = ROOT/'data/v3_analysis_r3_20261103'


def read(p):
    return json.loads(Path(p).read_text())


def save(p, value):
    p = Path(p)
    temporary = p.with_suffix(p.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(p)


class Profile:
    def __init__(self, out):
        self.out = out
        self.start = time.monotonic()
        self.phases = {}
        self.api = {}
        self.callback = dict(calls=0, body_seconds=0., by_dimension={}, by_face={})
        self.phase = 'startup'
        self.last_progress = 0.

    def progress(self, force=False):
        now = time.monotonic()
        if not force and now-self.last_progress < 1:
            return
        self.last_progress = now
        save(self.out/'progress.json', dict(status='RUNNING', phase=self.phase,
             observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             seconds=now-self.start, CPU_seconds=time.process_time(), phases=self.phases,
             callback=self.callback, api=self.api,
             peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))

    @contextmanager
    def stage(self, name):
        self.phase = name
        self.progress(True)
        w, c = time.monotonic(), time.process_time()
        try:
            yield
        finally:
            self.phases[name] = dict(wall_seconds=time.monotonic()-w, CPU_seconds=time.process_time()-c)
            self.progress(True)

    def wrap(self, parent, name, category):
        original = getattr(parent, name)
        def wrapped(*args, **kwargs):
            start = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                elapsed = time.perf_counter()-start
                q = self.api.setdefault(category+'.'+name, dict(calls=0, seconds=0.))
                q['calls'] += 1
                q['seconds'] += elapsed
        setattr(parent, name, wrapped)

    def install_callback_counter(self):
        original = gmsh.model.mesh.setSizeCallback
        def install(callback):
            def counted(dim, tag, x, y, z, lc):
                begin = time.perf_counter()
                result = callback(dim, tag, x, y, z, lc)
                q = self.callback
                q['body_seconds'] += time.perf_counter()-begin
                q['calls'] += 1
                key = str(dim)
                q['by_dimension'][key] = q['by_dimension'].get(key, 0)+1
                if dim == 2:
                    q['by_face'][str(tag)] = q['by_face'].get(str(tag), 0)+1
                self.progress()
                return result
            return original(counted)
        gmsh.model.mesh.setSizeCallback = install


def corners(face):
    edges = list(dict.fromkeys(abs(e) for d, e in gmsh.model.getBoundary([(2, face)], combined=False, oriented=True)))
    ends = {e: [abs(v) for d, v in gmsh.model.getBoundary([(1, e)], combined=False, oriented=True)] for e in edges}
    adjacency = collections.defaultdict(list)
    for e, vv in ends.items():
        if len(vv) != 2:
            raise ValueError('registered quadrilateral lost exact corners')
        for v in vv:
            adjacency[v].append(e)
    if len(edges) != 4 or len(adjacency) != 4 or any(len(v) != 2 for v in adjacency.values()):
        raise ValueError('registered quadrilateral topology changed')
    v, previous = next(iter(adjacency)), None
    result = []
    for i in range(4):
        result.append(v)
        e = next(e for e in adjacency[v] if e != previous)
        v = ends[e][0] if ends[e][1] == v else ends[e][1]
        previous = e
    return result, edges


def native_fields(faces, plan, include_boundary):
    sizes = collections.defaultdict(list)
    for f in faces:
        sizes[plan['face_h_mm'][str(f)]].append(f)
    restricted = []
    for h, ff in sizes.items():
        value = gmsh.model.mesh.field.add('MathEval')
        gmsh.model.mesh.field.setString(value, 'F', format(h, '.17g'))
        restrict = gmsh.model.mesh.field.add('Restrict')
        gmsh.model.mesh.field.setNumber(restrict, 'InField', value)
        gmsh.model.mesh.field.setNumber(restrict, 'IncludeBoundary', int(include_boundary))
        gmsh.model.mesh.field.setNumbers(restrict, 'SurfacesList', ff)
        restricted.append(restrict)
    minimum = gmsh.model.mesh.field.add('Min')
    gmsh.model.mesh.field.setNumbers(minimum, 'FieldsList', restricted)
    gmsh.model.mesh.field.setAsBackgroundMesh(minimum)
    return dict(native_fields=len(restricted), include_boundary=include_boundary)


def constraint_setup(strategy, faces, inv, plan):
    selected = set(faces)
    edges = {int(e) for f in faces for e in inv['faces'][str(f)]['curves']}
    if strategy == 'B_native_all':
        constrained = set(map(int, plan['shared_edge_counts']))
        quads = plan['quad_face_tags']
    else:
        quads = [f for f in plan['quad_face_tags'] if f in selected]
        constrained = {e for f in quads for e in corners(f)[1]}
        for f in faces:
            for key, q in inv['faces'][str(f)]['curves'].items():
                if q['max_curvature_per_mm'] > 1e-7:
                    constrained.add(int(key))
    for e in sorted(constrained):
        gmsh.model.mesh.setTransfiniteCurve(e, plan['shared_edge_counts'][str(e)]+1)
    for f in quads:
        gmsh.model.mesh.setTransfiniteSurface(f, 'AlternateLeft', corners(f)[0])
    result = native_fields(faces, plan, strategy == 'B_native_selective')
    result.update(constrained_curves=len(constrained), local_curves=len(edges), quad_faces=len(quads))
    return result


def directional_constraints(faces, inv, plan):
    curves = {}
    critical = set()
    periodic = {}
    for f in faces:
        q = inv['faces'][str(f)]
        curves.update({int(e): x for e, x in q['curves'].items()})
        if any(n.startswith(('TEC_lead', 'lead1_insulation', 'lead9_insulation', 'detector_bond')) for n in q['owners']):
            critical.update(map(int, q['curves']))
        if q['type'] not in ('Cylinder', 'Torus'):
            continue
        lo, hi = map(np.array, q['parameter_bounds'])
        axis = 0 if q['type'] == 'Cylinder' else 1
        if abs(hi[axis]-lo[axis]-2*math.pi) > 1e-6:
            raise ValueError('STOP C unsupported nonperiodic curved patch '+str(f))
        mult = collections.Counter(q['boundary_with_multiplicity'])
        seams = [e for e, n in mult.items() if n == 2]
        if len(seams) != 1:
            raise ValueError('STOP C nonunique saved periodic seam '+str(f))
        periodic[f] = dict(axis=axis, seam=seams[0], lo=lo, hi=hi)
    counts = {}
    for e, q in curves.items():
        h = .08 if e in critical else .30
        counts[e] = max(1, math.ceil(q['length_mm']/h-1e-8),
                        math.ceil(q['length_mm']*q['max_curvature_per_mm']/(math.pi/24)-1e-8))
        gmsh.model.mesh.setTransfiniteCurve(e, counts[e]+1)
    native_fields(faces, plan, False)
    return periodic, counts


def seed_periodic(periodic, counts):
    from scipy.spatial import Delaunay
    nodes, xyz, _ = gmsh.model.mesh.getNodes()
    nodes = np.asarray(nodes, np.int64)
    xyz = np.asarray(xyz).reshape(-1, 3)
    lookup = {int(n): p for n, p in zip(nodes, xyz)}
    next_node = int(nodes.max())+1
    all_element_ids = gmsh.model.mesh.getElements()[1]
    next_element = max((int(a.max()) for a in all_element_ids if len(a)), default=0)+1
    records = {}
    for f, q in periodic.items():
        axis, lo, hi = q['axis'], q['lo'], q['hi']
        n = np.array([48, counts[q['seam']]] if axis == 0 else [counts[q['seam']], 48])
        boundary_curves = {abs(e) for d, e in gmsh.model.getBoundary([(2, f)], combined=False, oriented=True)}
        boundary_nodes = set()
        for e in boundary_curves:
            ids, _, _ = gmsh.model.mesh.getNodes(1, e, includeBoundary=True)
            boundary_nodes.update(map(int, ids))
        seam_ids, _, _ = gmsh.model.mesh.getNodes(1, q['seam'], includeBoundary=True)
        seam_ids = set(map(int, seam_ids))
        candidates = np.array(sorted(boundary_nodes), np.int64)
        source_xyz = np.array([lookup[int(i)] for i in candidates])
        source_uv = np.asarray(gmsh.model.getParametrization(2, f, source_xyz.ravel())).reshape(-1, 2)
        uv, identities = [], []
        for node, value in zip(candidates, source_uv):
            value = value.copy()
            value[axis] = lo[axis]+(value[axis]-lo[axis]) % (2*math.pi)
            other = 1-axis
            if abs(value[other]-lo[other]) < 1e-7:
                value[other] = lo[other]
            elif abs(value[other]-hi[other]) < 1e-7:
                value[other] = hi[other]
            if node in seam_ids:
                if min(abs(value[axis]-lo[axis]), abs(value[axis]-hi[axis])) > 1e-7:
                    raise ValueError('STOP C source seam parametrization inconsistent')
                for edge_value in (lo[axis], hi[axis]):
                    v = value.copy();v[axis] = edge_value
                    uv.append(v);identities.append(int(node))
            else:
                if min(abs(value[other]-lo[other]), abs(value[other]-hi[other])) > 1e-7:
                    raise ValueError('STOP C source boundary is not a rectangular periodic patch')
                uv.append(value);identities.append(int(node))
        uv = np.asarray(uv)
        identities = np.asarray(identities, np.int64)
        roundtrip = np.asarray(gmsh.model.getValue(2, f, uv.ravel())).reshape(-1, 3)
        distances = np.linalg.norm(roundtrip-np.array([lookup[int(i)] for i in identities]), axis=1)
        if not np.isfinite(distances).all() or distances.max() > 1e-8:
            raise ValueError('STOP C exact source boundary UV roundtrip failed')
        us = np.linspace(lo[0], hi[0], n[0]+1)[1:-1]
        vs = np.linspace(lo[1], hi[1], n[1]+1)[1:-1]
        interior = np.stack(np.meshgrid(us, vs, indexing='ij'), axis=-1).reshape(-1, 2)
        new_ids = np.arange(next_node, next_node+len(interior), dtype=np.int64)
        next_node += len(new_ids)
        if len(interior):
            interior_xyz = gmsh.model.getValue(2, f, interior.ravel())
            gmsh.model.mesh.addNodes(2, f, new_ids, interior_xyz, interior.ravel())
        boundary_count = len(uv)
        uv = np.concatenate((uv, interior))
        identities = np.r_[identities, new_ids]
        scaled = (uv-lo)/(hi-lo)*n
        simplices = Delaunay(scaled).simplices
        if set(simplices.ravel()) != set(range(len(uv))):
            raise ValueError('STOP C Delaunay omitted a source/grid vertex; no perturbation allowed')
        cross = np.cross(uv[simplices[:, 1]]-uv[simplices[:, 0]], uv[simplices[:, 2]]-uv[simplices[:, 0]])
        if np.any(cross == 0):
            raise ValueError('STOP C degenerate source UV triangle')
        negative = cross < 0
        simplices[negative] = simplices[negative][:, [0, 2, 1]]
        tri = identities[simplices]
        if any(len(set(map(int, t))) != 3 for t in tri):
            raise ValueError('STOP C collapsed periodic element')
        element_ids = np.arange(next_element, next_element+len(tri), dtype=np.int64)
        next_element += len(tri)
        gmsh.model.mesh.addElementsByType(f, 2, element_ids, tri.ravel())
        records[str(f)] = dict(method='EXACT_NATIVE_BOUNDARY_UV_DELAUNAY', periodic_axis=axis,
            periodic_interior_divisions=48, axial_divisions=int(counts[q['seam']]), triangles=len(tri),
            source_seam=q['seam'], exact_boundary_UV_vertices=boundary_count,
            interior_nodes=len(interior), max_boundary_roundtrip_mm=float(distances.max()),
            no_boundary_resampling=True, no_coordinate_perturbation=True)
    return records


def validate_mesh(faces, inv, reg, reference):
    ids, xyz, _ = gmsh.model.mesh.getNodes()
    ids = np.asarray(ids, np.int64)
    points = np.asarray(xyz).reshape(-1, 3)
    index = np.full(int(ids.max())+1, -1, np.int64)
    index[ids] = np.arange(len(ids))
    extra = [t for d, t in gmsh.model.getEntities(2) if t not in faces and any(len(a) for a in gmsh.model.mesh.getElements(2, t)[1])]
    if extra:
        raise ValueError('SOURCE_SCOPE unselected face meshed '+str(extra))
    if any(len(a) for a in gmsh.model.mesh.getElements(3)[1]):
        raise ValueError('SOURCE_SCOPE unexpected tetrahedra')
    curves = {int(e) for f in faces for e in inv['faces'][str(f)]['curves']}
    segments = {}
    for e in curves:
        kinds, _, arrays = gmsh.model.mesh.getElements(1, e)
        if list(kinds) != [1]:
            raise ValueError('missing native1D curve '+str(e))
        segments[e] = np.asarray(arrays[0], np.int64).reshape(-1, 2)
    rows = {}
    total = 0
    for f in faces:
        q = inv['faces'][str(f)]
        kinds, _, arrays = gmsh.model.mesh.getElements(2, f)
        if list(kinds) != [2]:
            raise ValueError('missing/nontriangular native face '+str(f))
        tri = np.asarray(arrays[0], np.int64).reshape(-1, 3)
        metrics = triangle_metrics(points, index[tri], q['face_area_mm2'])
        conformity = check_face_edges(tri, segments, collections.Counter(q['boundary_with_multiplicity']))
        rows[str(f)] = dict(metrics, conformity=conformity, owners=q['owners'],
                            owner_volume_ids=q['owner_volume_ids'], R2_ancestors=q['R2_ancestors'])
        if q['principal_curvatures_per_mm']:
            curvature = max(abs(k) for pair in q['principal_curvatures_per_mm'] for k in pair)
            rows[str(f)]['minimum_edge_times_max_curvature'] = metrics['min_edge_mm']*curvature
        total += len(tri)
    ancestors = {}
    for parent, children in reg['R2_face_descendants'].items():
        used = sorted(set(children) & set(faces))
        if not used:
            continue
        old = reference['faces'][parent]
        if set(used) != set(children):
            ancestors[parent] = dict(status='NOT COMPARABLE incomplete local descendants')
            continue
        exact = sum(inv['faces'][str(f)]['face_area_mm2'] for f in used)
        area = sum(rows[str(f)]['mesh_area_mm2'] for f in used)
        ancestors[parent] = dict(status='COMPLETE LOCAL DESCENDANTS', R3_children=used,
             CAD_area_mm2=exact, mesh_area_mm2=area, relative_area_error=area/exact-1,
             triangles=sum(rows[str(f)]['triangles'] for f in used),
             R2_reference_triangles=old['triangles'], R2_reference_relative_error=old['relative_error'])
    return dict(faces=rows, R2_ancestor_comparison=ancestors, triangles=total, nodes=len(ids),
                extra_meshed_faces=extra, tetrahedra=0,
                max_area_error=max(abs(q['relative_area_error']) for q in rows.values()))


def run(strategy, fixture, out):
    out.mkdir(exist_ok=False, parents=True)
    p = Profile(out)
    inv = read(DATA/'inventory.json')
    reg = read(R3/'audit_v2/registry.json')
    reference = read(R3/'reference_replay/reference.json')
    old_plan = read(R3/'surface/surface_0/size_plan.json')
    faces = inv['groups'][fixture]
    result = dict(status='PENDING', strategy=strategy, fixture=fixture, source_identity_PASS=False,
                  global_mesh_RUN=False, PDE_RUN=False, solver_ready=False)
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.option.setString('Geometry.OCCTargetUnit', 'MM')
    gmsh.option.setNumber('General.NumThreads', 4)
    gmsh.option.setNumber('Mesh.MaxNumThreads1D', 4)
    gmsh.option.setNumber('Mesh.MaxNumThreads2D', 4)
    for name, value in [('Mesh.MeshOnlyVisible', 1), ('Mesh.MeshSizeMin', .0015),
                        ('Mesh.MeshSizeMax', .30), ('Mesh.MeshSizeFromPoints', 0),
                        ('Mesh.MeshSizeFromCurvature', 0), ('Mesh.MeshSizeExtendFromBoundary', 0),
                        ('Mesh.MinimumCirclePoints', 12), ('Mesh.Algorithm', 6),
                        ('Mesh.SaveAll', 1), ('Mesh.Binary', 1)]:
        gmsh.option.setNumber(name, value)
    gmsh.logger.start()
    try:
        with p.stage('import_source_visibility'):
            gmsh.model.occ.importShapes(str(R3/'geometry_restored/R3_conformal_mm.brep'))
            gmsh.model.occ.synchronize()
            if len(gmsh.model.getEntities(3)) != 430 or len(gmsh.model.getEntities(2)) != 2440:
                raise ValueError('SOURCE_IDENTITY domain/face count changed')
            for f in faces:
                q = inv['faces'][str(f)]
                if sorted(map(int, gmsh.model.getAdjacencies(2, f)[0])) != q['owner_volume_ids'] or abs(gmsh.model.occ.getMass(2, f)/q['face_area_mm2']-1) >= 1e-7:
                    raise ValueError('SOURCE_IDENTITY face owner/area changed')
                gmsh.model.addPhysicalGroup(2, [f], f)
                gmsh.model.setPhysicalName(2, f, 'R3_native_face_'+str(f))
            for name, tag in reg['domain_id_map'].items():
                gmsh.model.addPhysicalGroup(3, [tag], tag)
                gmsh.model.setPhysicalName(3, tag, name)
            gmsh.model.setVisibility(gmsh.model.getEntities(), 0)
            gmsh.model.setVisibility([(2, f) for f in faces], 1, recursive=True)
            if {t for d, t in gmsh.model.getEntities(2) if gmsh.model.getVisibility(2, t)} != set(faces):
                raise ValueError('SOURCE_SCOPE visibility not strictly local')
            result['source_identity_PASS'] = True
        for name in ('getParametrizationBounds', 'getPrincipalCurvatures', 'getCurvature', 'getValue', 'getParametrization'):
            p.wrap(gmsh.model, name, 'parametrization')
        for name in ('setTransfiniteCurve', 'setTransfiniteSurface'):
            p.wrap(gmsh.model.mesh, name, 'sizing')
        for name in ('add', 'setNumber', 'setNumbers', 'setString', 'setAsBackgroundMesh'):
            p.wrap(gmsh.model.mesh.field, name, 'sizing')
        p.install_callback_counter()
        with p.stage('setup_sizing'):
            if strategy == 'A_callback_all':
                plan = configure(reg, reference, {})
                if plan != old_plan:
                    raise ValueError('SOURCE_IDENTITY R3 sizing replay changed')
                result['sizing'] = dict(constrained_curves=len(plan['shared_edge_counts']),
                                         quad_faces=plan['curved_quad_faces'], callback=True)
            elif strategy.startswith('B_native'):
                result['sizing'] = constraint_setup(strategy, faces, inv, old_plan)
            elif strategy == 'C_directional':
                periodic, counts = directional_constraints(faces, inv, old_plan)
                result['sizing'] = dict(constrained_curves=len(counts), periodic_faces=len(periodic), callback=False)
            else:
                raise ValueError('unregistered strategy')
        with p.stage('native_1D_meshing'):
            gmsh.model.mesh.generate(1)
            selected_curves = {int(e) for f in faces for e in inv['faces'][str(f)]['curves']}
            if any(any(len(a) for a in gmsh.model.mesh.getElements(1, e)[1]) for d, e in gmsh.model.getEntities(1) if e not in selected_curves):
                raise ValueError('SOURCE_SCOPE nonlocal curve meshed')
        if strategy == 'C_directional':
            with p.stage('source_parametric_grid'):
                result['directional_patches'] = seed_periodic(periodic, counts)
            gmsh.option.setNumber('Mesh.MeshOnlyEmpty', 1)
        with p.stage('native_2D_meshing'):
            gmsh.model.mesh.generate(2)
        with p.stage('write_native_MSH'):
            gmsh.write(str(out/'local_surface.msh'))
        with p.stage('independent_area_topology_validation'):
            result.update(validate_mesh(faces, inv, reg, reference))
            result['status'] = 'PASS LOCAL SURFACE ONLY'
            validate_result(result, inv)
    except Exception as ex:
        result.update(status='STOP LOCAL FIXTURE', error=repr(ex))
    finally:
        result.update(phases=p.phases, API_profile=p.api, callback=p.callback,
            wall_seconds=time.monotonic()-p.start, CPU_seconds=time.process_time(),
            peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save(out/'result.json', result)
        save(out/'gmsh_tail.json', gmsh.logger.get()[-100:])
        gmsh.logger.stop()
        gmsh.finalize()
    print(strategy, fixture, result['status'], result.get('triangles'), flush=True)
    return 0 if result['status'].startswith('PASS') else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', required=True)
    parser.add_argument('--fixture', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.strategy, args.fixture, args.out))
