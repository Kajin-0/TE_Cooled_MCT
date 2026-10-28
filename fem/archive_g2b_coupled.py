#!/usr/bin/env python3
"""Archive accepted actual coupled results, preserving execution/restart lineage."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess


def main():
    root = Path(__file__).resolve().parents[1]
    run = root/"outputs/fem-g2b-two-terminal"
    out = root/"fem/results/g2b_two_terminal_20261028"
    report = json.loads((run/"summary.json").read_text())
    if report["quick"] or not report["verification"]["passed"] or not report["protected_integrity"]["passed"]:
        raise SystemExit("Refusing failed, quick or unverified coupled evidence")
    if not re.search(r"(?m)^\d+ passed(?:,.*)? in ",(root/"logs/pytest-g2b-coupled.log").read_text()):
        raise SystemExit("Passing completed regressions required before archiving")
    def digest(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()
    sources={**report["source_sha256"],**report.get("supplemental_verification_source_sha256",{})}
    for name, expected in sources.items():
        if digest(root/name) != expected:
            raise SystemExit(f"Source changed after verification: {name}")
    def local(value):
        p = Path(value)
        p = root/p.relative_to("/work") if p.is_relative_to("/work") else p
        if not p.resolve().is_relative_to(root):
            raise ValueError("Evidence must belong to this project")
        return p
    def copy(source, relative):
        target = out/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for name in ("summary.json", "current_sweep.csv", "component_cuts.csv", "mesh_convergence.csv",
                 "current_sweep.png", "current_sweep.svg", "stage_temperatures_heat.png",
                 "mesh_convergence.png", "all_88_leg_currents.png"):
        copy(run/name, name)
    records = {**report["cases"], **{f"convergence_{i}": r for i,r in enumerate(report["convergence"])}}
    unique = {}
    for name, r in records.items():
        case = local(r["case_path"])
        if r["solver_status"]["exit_code"] != 0 or digest(case/"case.sif") != r["sif_sha256"] or digest(case/r["field_source"]) != r["vtu_sha256"]:
            raise ValueError(f"Actual execution artifacts changed: {name}")
        for filename in ("case.sif", "case.json", "solver.log", "solver-status.json"):
            copy(case/filename, f"cases/{name}/{filename}")
        target = out/"cases"/name/"metrics.json"
        target.write_text(json.dumps(r, indent=2, allow_nan=False)+"\n")
        key = str(case)
        if key not in unique:
            unique[key] = {"labels": [], "case_path": r["case_path"], "nodes": r["nodes"],
                           "dofs": r["dofs"], **r["solver_status"]}
        unique[key]["labels"].append(name)
    for i, r in enumerate(report["convergence"]):
        mesh = local(r["mesh_path"])
        expected = report["audits"][i]
        if digest(mesh/"mesh.npz") != expected["mesh_npz_sha256"] or digest(mesh/"connected.msh") != expected["gmsh_mesh_sha256"]:
            raise ValueError("Mesh changed after actual verification")
        for filename in ("mesh.npz", "manifest.json", "audit.json", "tetra_connectivity.json", "gmsh.log", "grid.log", "grid-status.json", "routing.png"):
            copy(mesh/filename, f"meshes/mesh_{i}/{filename}")
        if i == len(report["convergence"])-1:
            copy(mesh/"connected.msh", f"meshes/mesh_{i}/connected.msh")
    positive = local(report["cases"]["loaded_positive"]["case_path"])
    for filename in ("fields_t0001.vtu", "derived.vtu", "temperature_isosurfaces.vtu", "fields.png"):
        copy(positive/filename, f"fields/loaded_positive/{filename}")
    for filename in ("solver.log", "solver-status.json"):
        copy(run/"upstream-thermoelectric"/filename, f"provenance/upstream/{filename}")
    for filename in ("g2b-two-terminal-full.log", "g2b-tetra-connectivity.log", "pytest-g2b-coupled.log", "cli-g2b-coupled.log", "geometry-g2b-coupled.log"):
        copy(root/"logs"/filename, f"provenance/{filename}")
    for filename in ("g2b-first-full-attempt.log", "g2b-sigma-roundoff-attempt.log"):
        if (root/"logs"/filename).exists():
            copy(root/"logs"/filename, f"provenance/incomplete-attempts/{filename}")
    for attempt in run.glob("sigma_roundoff_plateau_*"):
        for filename in ("case.sif", "case.json", "solver.log"):
            if (attempt/filename).exists():
                copy(attempt/filename, f"provenance/incomplete-attempts/{attempt.name}/{filename}")
        target=out/"provenance/incomplete-attempts"/attempt.name/"status.json"
        target.write_text(json.dumps({"accepted":False,"solver_exit_code":None,
            "reason":"private controller stopped at a nonlinear roundoff plateau above its original 1e-10 target; actual case rerun at declared 1e-9 gate"},indent=2)+"\n")
    # Preserve the original cold-start source snapshot for cases resumed across
    # scheduler/restart improvements. .source suffix prevents pytest collection.
    snapshot = run/"initial_execution_source"
    if snapshot.exists():
        for index in snapshot.rglob("source_sha256.json"):
            recorded = json.loads(index.read_text())
            for relative, expected in recorded.items():
                original = index.parent/relative
                candidate = original.with_suffix(original.suffix+".source") if original.suffix == ".py" else original
                if digest(candidate) != expected:
                    raise ValueError("Initial execution source snapshot changed")
        for p in snapshot.rglob("*"):
            if p.is_file() and (p.name.endswith(".source") or p.name == "source_sha256.json" or p.name == "run_g2b.sh"):
                copy(p, Path("provenance/initial_execution_source")/p.relative_to(snapshot))
    with (out/"resource_usage.csv").open("w", newline="") as f:
        columns = ["labels", "case_path", "nodes", "dofs", "elapsed_s", "cpu_s", "peak_rss_kib", "nonlinear_iterations", "exit_code"]
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for record in unique.values():
            writer.writerow({**record, "labels": "+".join(record["labels"])})
    with (out/"stage_temperatures.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case","plate","mean_k","min_k","max_k"])
        writer.writeheader()
        for label, record in report["cases"].items():
            for plate, values in record["plate_temperatures"].items():
                writer.writerow({"case":label,"plate":plate,**values})
    with (out/"stage_heat_budgets.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case","stage","hot_out_w","cold_absorbed_w",
            "electrical_work_control_volume_w","leg_and_local_metal_work_w","balance_residual_w","scope"])
        writer.writeheader()
        for label, record in report["cases"].items():
            for budget in record["stage_control_volume_budgets"]:
                writer.writerow({"case":label,**budget})
    copy(root/"fem/results/g1_20261028/provenance/versions.txt", "provenance/pinned-versions.txt")
    image = subprocess.check_output(["docker", "image", "inspect", "tecooledmct-fem:26.2.1"], text=True)
    (out/"provenance/image.json").write_text(image)
    artifacts = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob("*"))
                 if p.is_file() and p.name != "checksums.json"}
    checksums = {"baseline_git_commit": subprocess.check_output(["git","rev-parse","HEAD"], cwd=root,text=True).strip(),
                 "source_sha256": sources, "artifacts_sha256": artifacts,
                 "elmer_source_commit": report["elmer_commit"], "unique_successful_solver_executions": len(unique),
                 "execution_source_lineage": {"convergence_0,convergence_1":"provenance/initial_execution_source",
                      "convergence_2,loaded_positive,zero_load_positive":"provenance/initial_execution_source/tolerance_parent",
                      "leakage_check,loaded_p0050,loaded_zero,loaded_negative":"source_sha256 in this manifest"},
                 "note": "Actual PDE fields; loaded_positive explicitly reuses its identical fine convergence execution. Earlier source snapshots and incomplete-attempt logs retained separately."}
    (out/"checksums.json").write_text(json.dumps(checksums, indent=2)+"\n")
    print(f"Archived {len(artifacts)} verified files from {len(unique)} unique successful solver executions")


if __name__ == "__main__":
    main()
