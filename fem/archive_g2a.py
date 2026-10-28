#!/usr/bin/env python3
"""Retain only actual verified G2a runs, with source/SIF/VTU/artifact hashes."""
import hashlib
import json
from pathlib import Path
import shutil


def main():
    root = Path(__file__).resolve().parents[1]
    run, out = root/"outputs/fem-g2a", root/"fem/results/g2a_20261028"
    report = json.loads((run/"summary.json").read_text())
    if report["quick"] or not report["verification"]["passed"] or not report["g1_integrity"]["passed"]:
        raise SystemExit("Refusing unverified G2a evidence")
    for name, digest in report["source_sha256"].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise SystemExit(f"Source changed after actual run: {name}")
    def copy(source, relative):
        target = out/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for filename in ("summary.json", "current_sweep.csv", "component_cuts.csv", "mesh_convergence.csv",
                     "current_sweep.png", "current_sweep.svg", "mesh_convergence.png",
                     "component_currents_joule.png", "topology.png", "topology.svg"):
        copy(run/filename, filename)
    for i in range(len(report["convergence"])):
        for filename in ("stage.msh", "mesh.npz", "manifest.json", "audit.json", "gmsh.log", "grid.log", "grid-status.json"):
            copy(run/f"mesh_{i}"/filename, f"meshes/mesh_{i}/{filename}")
    cases = {**report["cases"], **{f"convergence_{i}": r for i, r in enumerate(report["convergence"])}}
    for name, result in cases.items():
        case = run/name
        status = result["solver_status"]
        assert status["exit_code"] == 0
        for filename, key in (("case.sif", "sif_sha256"), (result["field_source"], "vtu_sha256")):
            assert hashlib.sha256((case/filename).read_bytes()).hexdigest() == status[key], name
        for filename in ("case.sif", "case.json", "metrics.json", "solver.log", "solver-status.json"):
            copy(case/filename, f"cases/{name}/{filename}")
    for filename in ("fields_t0001.vtu", "derived.vtu", "temperature_isosurfaces.vtu", "fields.png"):
        copy(run/"sweep_p0100"/filename, f"fields/sweep_p0100/{filename}")
    for filename in ("solver.log", "solver-status.json"):
        copy(run/"upstream-thermoelectric"/filename, f"provenance/upstream/{filename}")
    for filename in ("g2a-full.log", "pytest-g2a.log", "cli-g2a.log", "geometry-g2a.log"):
        copy(root/"logs"/filename, f"provenance/{filename}")
    artifacts = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(out.rglob("*")) if p.is_file() and p.name != "checksums.json"}
    checksums = {"source_sha256": report["source_sha256"], "artifacts_sha256": artifacts,
                 "baseline_commit": "6dcef127adc887132ae70d407181c1a1a53b28eb",
                 "elmer_commit": report["elmer_commit"],
                 "note": "Original Elmer outputs; full raw cases retained in outputs/fem-g2a on the VPS."}
    (out/"checksums.json").write_text(json.dumps(checksums, indent=2)+"\n")
    print(f"Archived {len(artifacts)} verified G2a files to {out}")


if __name__ == "__main__":
    main()
