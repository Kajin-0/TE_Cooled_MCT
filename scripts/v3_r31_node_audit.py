"""Read actual local MSH node usage; unmeshed CAD vertices are not surface DOFs."""
from pathlib import Path
import hashlib
import json
import gmsh
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r31_local_mesh_20261103'


def main():
    out = DATA/'node_usage.json'
    assert not out.exists()
    rows = {}
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    try:
        for path in sorted((DATA/'cases').glob('*/worker/local_surface.msh')):
            gmsh.clear()
            gmsh.open(str(path))
            tags, _, _ = gmsh.model.mesh.getNodes()
            arrays = gmsh.model.mesh.getElements(2)[2]
            used = np.unique(np.concatenate(arrays))
            rows[path.parent.parent.name] = dict(
                total_native_MSH_nodes=len(tags), nodes_used_by_local_triangles=len(used),
                remaining_catalog_or_curve_nodes=len(tags)-len(used),
                mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    finally:
        gmsh.finalize()
    out.write_text(json.dumps(dict(status='PASS READ-ONLY ACTUAL NODE USAGE', cases=rows,
        caveat='Native MSH retains full source entity catalog and unused 0D CAD vertices; local surface nodes reported separately',
        no_mesh_generation=True, no_PDE=True), indent=2)+'\n')
    print(rows['C_directional_corrected__detector_bonds'])


if __name__ == '__main__':
    main()
