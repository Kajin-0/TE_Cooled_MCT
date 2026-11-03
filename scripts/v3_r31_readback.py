"""Independent saved-MSH cross-product/owner/incidence replay; no meshing."""
from pathlib import Path
import collections
import hashlib
import json
import time
import resource
import gmsh
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r31_local_mesh_20261103'


def main():
    out = DATA/'independent_readback.json'
    assert not out.exists()
    inv = json.loads((DATA/'inventory.json').read_text())
    results = []
    start = time.monotonic()
    for path in sorted((DATA/'cases').glob('*/worker/local_surface.msh')):
        saved = json.loads((path.parent/'result.json').read_text())
        faces = inv['groups'][saved['fixture']]
        gmsh.initialize()
        gmsh.option.setNumber('General.Terminal', 0)
        try:
            gmsh.open(str(path))
            tags, xyz, _ = gmsh.model.mesh.getNodes()
            tags = np.asarray(tags, np.int64)
            p = np.asarray(xyz).reshape(-1, 3)
            lookup = np.full(int(tags.max())+1, -1, np.int64)
            lookup[tags] = np.arange(len(tags))
            extra = [f for d, f in gmsh.model.getEntities(2) if f not in faces and any(len(a) for a in gmsh.model.mesh.getElements(2, f)[1])]
            assert not extra and not any(len(a) for a in gmsh.model.mesh.getElements(3)[1])
            assert len(gmsh.model.getEntities(3)) == 430
            rows = {}
            for f in faces:
                src = inv['faces'][str(f)]
                assert sorted(map(int, gmsh.model.getAdjacencies(2, f)[0])) == src['owner_volume_ids']
                assert f in gmsh.model.getPhysicalGroupsForEntity(2, f)
                types, _, arrays = gmsh.model.mesh.getElements(2, f)
                assert list(types) == [2]
                tri = np.asarray(arrays[0], np.int64).reshape(-1, 3)
                xyz_tri = p[lookup[tri]]
                areas = np.linalg.norm(np.cross(xyz_tri[:, 1]-xyz_tri[:, 0], xyz_tri[:, 2]-xyz_tri[:, 0]), axis=1)/2
                assert np.isfinite(areas).all() and np.all(areas > 0)
                err = float(areas.sum()/src['face_area_mm2']-1)
                assert abs(err-saved['faces'][str(f)]['relative_area_error']) < 1e-10
                # Counter implementation independent of the worker's np.unique.
                incidence = collections.Counter(tuple(sorted((int(a), int(b))))
                    for a, b in np.concatenate((tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]])))
                assert all(n in (1, 2) for n in incidence.values())
                open_expected = set()
                for curve, multiplicity in collections.Counter(src['boundary_with_multiplicity']).items():
                    kinds, _, curves = gmsh.model.mesh.getElements(1, curve)
                    assert list(kinds) == [1]
                    seg = np.asarray(curves[0], np.int64).reshape(-1, 2)
                    for a, b in seg:
                        key = tuple(sorted((int(a), int(b))))
                        assert incidence[key] == multiplicity
                        if multiplicity == 1:
                            open_expected.add(key)
                assert {e for e, n in incidence.items() if n == 1} == open_expected
                rows[str(f)] = dict(triangles=len(tri), relative_area_error=err,
                                   area_PASS=abs(err) < .01, ownership_PASS=True,
                                   native_boundary_incidence_PASS=True)
            passed = all(q['area_PASS'] for q in rows.values())
            assert passed == saved['status'].startswith('PASS')
            results.append(dict(case=path.parent.parent.name, mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 status='PASS SAVED LOCAL MESH' if passed else 'REPRODUCED AREA FAIL',
                 faces=rows, no_global_mesh=True, no_PDE=True))
        finally:
            gmsh.finalize()
        print(results[-1]['case'], results[-1]['status'], flush=True)
    out.write_text(json.dumps(dict(status='PASS INDEPENDENT REPLAY; FAILURES RETAINED', cases=results,
        seconds=time.monotonic()-start, peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        no_mesh_generation=True, no_PDE=True), indent=2)+'\n')


if __name__ == '__main__':
    main()
