"""Read-only metadata preparation and old-mesh orientation controls. NO meshing."""
from pathlib import Path
import collections
import json
import math
import time
import resource
import gmsh
import numpy as np
from tecooledmct.v3_r32_surface_integrity import boundary_sign, DIRECTIONAL_FACES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r32_global_surface_20261103'
R3 = ROOT/'data/v3_analysis_r3_20261103'
R31 = ROOT/'data/v3_r31_local_mesh_20261103'


def main():
    out = DATA/'source_metadata.json'
    assert not out.exists()
    r = json.loads((R3/'audit_v2/registry.json').read_text())
    g = json.loads((R3/'geometry_restored/geometry_receipt.json').read_text())
    local = json.loads((R31/'inventory.json').read_text())
    start = time.monotonic()
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.option.setString('Geometry.OCCTargetUnit', 'MM')
    try:
        gmsh.model.occ.importShapes(str(R3/'geometry_restored/R3_conformal_mm.brep'))
        gmsh.model.occ.synchronize()
        assert len(gmsh.model.getEntities(3)) == 430 and len(gmsh.model.getEntities(2)) == 2440
        for name, tag in r['domain_id_map'].items():
            assert abs(gmsh.model.occ.getMass(3, tag)/g['domains'][name]['area_or_volume']-1) < 1e-7
        curves = {}
        for d, e in gmsh.model.getEntities(1):
            lo, hi = gmsh.model.getParametrizationBounds(1, e)
            curvature = gmsh.model.getCurvature(1, e, np.linspace(float(lo[0]), float(hi[0]), 9))
            curves[str(e)] = dict(type=gmsh.model.getType(1, e),
                length_mm=gmsh.model.occ.getMass(1, e), max_curvature_per_mm=float(max(abs(curvature))),
                parameter_bounds=[float(lo[0]), float(hi[0])])
        faces = {}
        for key, q in r['face_registry'].items():
            f = int(key)
            assert sorted(map(int, gmsh.model.getAdjacencies(2, f)[0])) == q['owner_volume_ids']
            assert abs(gmsh.model.occ.getMass(2, f)/q['face_area_mm2']-1) < 1e-7
            signed = [int(e) for d, e in gmsh.model.getBoundary([(2, f)], combined=False, oriented=True)]
            lo, hi = gmsh.model.getParametrizationBounds(2, f)
            ks = []
            for a in (.25, .5, .75):
                k1, k2, _, _ = gmsh.model.getPrincipalCurvatures(f, (1-a)*lo+a*hi)
                ks.append([float(k1[0]), float(k2[0])])
            faces[key] = dict(q, signed_boundary_curves=signed,
                boundary_with_multiplicity=list(map(abs, signed)), parameter_bounds=[lo.tolist(), hi.tolist()],
                principal_curvatures_per_mm=ks,
                curves={str(abs(e)): curves[str(abs(e))] for e in signed})
            if f in DIRECTIONAL_FACES:
                assert q['owners'] == local['faces'][key]['owners']
                for e, c in faces[key]['curves'].items():
                    old = local['faces'][key]['curves'][e]
                    assert abs(c['length_mm']/old['length_mm']-1) < 1e-7
        # Read existing local artifacts only; no generated control mesh.
        controls = {}
        for case in ('B_native_selective__leads_jackets', 'C_directional_corrected__detector_bonds'):
            gmsh.clear()
            gmsh.open(str(R31/'cases'/case/'worker/local_surface.msh'))
            seen = {}
            fixture = 'leads_jackets' if 'leads' in case else 'detector_bonds'
            for f in local['groups'][fixture]:
                types, _, arrays = gmsh.model.mesh.getElements(2, f)
                assert list(types) == [2]
                tri = np.asarray(arrays[0], np.int64).reshape(-1, 3)
                segments = {int(e): np.asarray(gmsh.model.mesh.getElements(1, int(e))[2][0], np.int64).reshape(-1, 2)
                            for e in faces[str(f)]['curves']}
                seen[str(f)] = boundary_sign(tri, segments, faces[str(f)]['signed_boundary_curves'])
            controls[case] = seen
        result = dict(status='PASS READ-ONLY SOURCE METADATA; NO MESH', faces=faces, face_registry=r['face_registry'],
            curves=curves, domain_id_map=r['domain_id_map'], domains=r['domains'],
            R2_face_descendants=r['R2_face_descendants'], source_to_analysis=r['source_to_analysis'],
            source_contacts=r['source_contacts'], shell_regions=r['shell_regions'],
            gas_volume_mm3=r['gas_volume_mm3'], excluded_polymer_volume_mm3=r['excluded_polymer_volume_mm3'],
            stage_leg_counts=r['stage_leg_counts'], terminal_faces=r['terminal_faces'],
            every_leg_required_for_series_path=r['every_leg_required_for_series_path'],
            source_orientation_controls=controls, physical_geometry_changed=False,
            seconds=time.monotonic()-start, peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        print('PASS430/2440; curves',len(curves),'old orientation signs',
              {k: dict(collections.Counter(q.values())) for k, q in controls.items()},flush=True)
    finally:
        gmsh.finalize()


if __name__ == '__main__':
    main()
