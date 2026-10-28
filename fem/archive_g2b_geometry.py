#!/usr/bin/env python3
"""Archive a passing geometry-only proof; never label it solved TEC physics."""
import hashlib
import json
from pathlib import Path
import shutil


def main():
    root = Path(__file__).resolve().parents[1]
    run, out = root/"outputs/fem-g2b-geometry", root/"fem/results/g2b_geometry_20261028"
    audit = json.loads((run/"audit.json").read_text())
    grid = json.loads((run/"grid-status.json").read_text())
    assert audit["passed"] and not audit["coupled_solution"] and grid["exit_code"] == 0
    assert audit["legs"] == 88 and audit["electrical_components"] == 3
    out.mkdir(parents=True, exist_ok=True)
    for filename in ("assembly.msh", "mesh.npz", "manifest.json", "audit.json", "geometry_only.vtu",
                     "geometry_only.png", "gmsh.log", "grid.log", "grid-status.json"):
        shutil.copy2(run/filename, out/filename)
    for filename in ("g2b-geometry.log", "pytest-g2b.log"):
        shutil.copy2(root/"logs"/filename, out/filename)
    source = [root/"tecooledmct/fem_g2b_geometry.py", root/"tests/test_fem_g2b_geometry.py", Path(__file__).resolve()]
    manifest = {"scope": "geometry/netlist/mesh only; coupled_solution=false",
                "g2a_verified_commit": "f43d07835c5c58a336f661054b42023eeb5a50d5",
                "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source},
                "artifacts_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()
                                     if p.is_file() and p.name != "checksums.json"}}
    (out/"checksums.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(f"Archived geometry-only evidence to {out}")


if __name__ == "__main__":
    main()
