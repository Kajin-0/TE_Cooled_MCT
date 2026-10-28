#!/usr/bin/env python3
"""Archive actual verified G1 evidence and checksums; refuses incomplete runs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=root/"outputs/fem-g1")
    parser.add_argument("--out", type=Path, default=root/"fem/results/g1_20261028")
    args = parser.parse_args()
    run, out = args.run.resolve(), args.out.resolve()
    summary = json.loads((run/"summary.json").read_text())
    if summary["quick"] or not summary["verification"]["passed"]:
        raise SystemExit("Refusing to archive a failed/incomplete G1 benchmark")
    out.mkdir(parents=True, exist_ok=True)
    def copy(source, relative):
        target = out/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for name in ("summary.json", "current_sweep.csv", "mesh_convergence.csv",
                 "current_sweep.png", "current_sweep.svg", "mesh_convergence.png"):
        copy(run/name, name)
    for name in [*summary["cases"], *(f"convergence_{i}" for i in range(len(summary["convergence"])) )]:
        for filename in ("case.sif", "case.json", "metrics.json", "solver.log", "solver-status.json"):
            copy(run/name/filename, f"cases/{name}/{filename}")
    for i in range(len(summary["convergence"])):
        for filename in ("audit.json", "couple.msh", "mesh.npz", "grid.log", "grid-status.json"):
            copy(run/f"mesh_{i}"/filename, f"meshes/mesh_{i}/{filename}")
    for name in ("sweep_m0200", "sweep_p0000", "sweep_p0200", "open_circuit", "temperature_dependent"):
        for filename in ("fields_t0001.vtu", "derived.vtu", "temperature_isosurfaces.vtu", "temperature.png"):
            copy(run/name/filename, f"fields/{name}/{filename}")
    for filename in ("solver.log", "solver-status.json", "grid.log", "grid-status.json"):
        copy(run/"upstream-thermoelectric"/filename, f"provenance/upstream/{filename}")
    for filename in ("versions.txt", "image.json", "disk-before.txt", "disk-after.txt"):
        copy(root/"logs/bootstrap"/filename, f"provenance/{filename}")
    for filename in ("pytest-fem.log", "cli.log", "geometry-demo.log", "full.log"):
        copy(root/"logs"/filename, f"provenance/{filename}")
    source_files = [*sorted((root/"tecooledmct").glob("fem_g1*.py")),
                    root/"tests/test_fem_g1.py", root/"fem/Dockerfile",
                    root/"fem/bootstrap.sh", root/"fem/run.sh", Path(__file__).resolve()]
    source_hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in source_files}
    artifacts = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    manifest = {"baseline_git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                "elmer_source_commit": summary["elmer_commit"],
                "source_sha256": source_hashes, "artifacts_sha256": artifacts,
                "note": "Artifacts from real Gmsh/Elmer runs; run the source to regenerate local mesh paths."}
    (out/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(f"Archived {len(artifacts)} verified artifacts to {out}")


if __name__ == "__main__":
    main()
