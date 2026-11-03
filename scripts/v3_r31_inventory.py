"""Read-only inventory of native R3 faces for the local meshing benchmark."""
from pathlib import Path
import collections
import json
import math
import time
import resource
import gmsh
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
R3 = ROOT/'data/v3_analysis_r3_20261103'
OUT = ROOT/'data/v3_r31_local_mesh_20261103'


def main():
    out = OUT/'inventory.json'
    assert not out.exists()
    r = json.loads((R3/'audit_v2/registry.json').read_text())
    start = time.monotonic()
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.option.setString('Geometry.OCCTargetUnit', 'MM')
    try:
        gmsh.model.occ.importShapes(str(R3/'geometry_restored/R3_conformal_mm.brep'))
        gmsh.model.occ.synchronize()
        assert len(gmsh.model.getEntities(3)) == 430
        assert len(gmsh.model.getEntities(2)) == 2440
        groups = {'leads_jackets': [], 'detector_bonds': [], 'pin_planes_contacts': []}
        for key, q in r['face_registry'].items():
            f = int(key)
            if any(n in ('TEC_lead1', 'TEC_lead9', 'lead1_insulation', 'lead9_insulation') for n in q['owners']):
                groups['leads_jackets'].append(f)
            if any(n.startswith('detector_bond') for n in q['owners']):
                groups['detector_bonds'].append(f)
            if q['type'] == 'Cylinder' and 'pin1' in q['owners']:
                groups['pin_planes_contacts'].append(f)
        groups['pin_planes_contacts'] += r['terminal_faces']['pin1']
        ceramic = [n for n, q in r['domains'].items() if q['material'] == 'Al2O3']
        for name in (ceramic[0], ceramic[-1]):
            possible = [(int(f), q) for f, q in r['face_registry'].items() if name in q['owners'] and q['type'] == 'Plane']
            groups['pin_planes_contacts'].append(max(possible, key=lambda x: x[1]['face_area_mm2'])[0])
        for name in ('P', 'SnBi57_43'):
            contact = next(c for c in r['source_contacts'] if c['type'] == 'FINITE_SHARED_FACE' and
                any(r['domains'][n]['material'] == name for n in c['mapped']))
            groups['pin_planes_contacts'] += contact['face_tags']
        groups = {k: sorted(set(v)) for k, v in groups.items()}
        allfaces = sorted({f for v in groups.values() for f in v})
        ancestor = collections.defaultdict(list)
        for parent, children in r['R2_face_descendants'].items():
            for f in children:
                ancestor[f].append(parent)
        faces = {}
        for f in allfaces:
            q = r['face_registry'][str(f)]
            assert sorted(map(int, gmsh.model.getAdjacencies(2, f)[0])) == q['owner_volume_ids']
            area = gmsh.model.occ.getMass(2, f)
            assert abs(area/q['face_area_mm2']-1) < 1e-7
            bounds = gmsh.model.getParametrizationBounds(2, f)
            kk = []
            for a in (.25, .5, .75):
                uv = (1-a)*bounds[0]+a*bounds[1]
                k1, k2, _, _ = gmsh.model.getPrincipalCurvatures(f, uv)
                kk.append([float(k1[0]), float(k2[0])])
            boundary = [abs(e) for d, e in gmsh.model.getBoundary([(2, f)], combined=False, oriented=True)]
            curves = {}
            for e in dict.fromkeys(boundary):
                lo, hi = gmsh.model.getParametrizationBounds(1, e)
                k = gmsh.model.getCurvature(1, e, np.linspace(float(lo[0]), float(hi[0]), 9))
                curves[str(e)] = dict(type=gmsh.model.getType(1, e), length_mm=gmsh.model.occ.getMass(1, e),
                    vertices=[abs(v) for d, v in gmsh.model.getBoundary([(1, e)], combined=False, oriented=True)],
                    parameter_bounds=[float(lo[0]), float(hi[0])], max_curvature_per_mm=float(max(abs(k))))
            faces[str(f)] = dict(q, R2_ancestors=ancestor[f],
                parameter_bounds=[list(map(float, b)) for b in bounds],
                principal_curvatures_per_mm=kk, boundary_with_multiplicity=boundary, curves=curves)
        result = dict(status='PASS READ-ONLY NATIVE FACE INVENTORY; NO MESH', groups=groups, faces=faces,
            selected_faces=len(faces), selected_curves=len({e for q in faces.values() for e in q['curves']}),
            source_domains=430, source_faces=2440, original_source_bodies=824, original_finite_contacts=378,
            no_CAD_operations=True, no_PDE=True, seconds=time.monotonic()-start,
            peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        print({k: len(v) for k, v in groups.items()}, len(allfaces), flush=True)
    finally:
        gmsh.finalize()


if __name__ == '__main__':
    main()
