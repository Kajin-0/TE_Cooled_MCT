"""Reproducible Gmsh -> ElmerGrid -> ThermoElectricSolver -> verification."""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np

from .fem_g1 import ELMER_COMMIT, generate_mesh, write_sif
from .fem_g1_post import postprocess


def execute(command, directory, name, timeout=600):
    start = time.monotonic()
    try:
        process = subprocess.run(command, cwd=directory, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, timeout=timeout)
        output, code = process.stdout, process.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        code = 124
    (directory/f"{name}.log").write_text(output)
    status = {"command": command, "exit_code": code, "elapsed_s": time.monotonic()-start}
    (directory/f"{name}-status.json").write_text(json.dumps(status, indent=2)+"\n")
    if code or re.search(r"\b(FATAL|ERROR):", output, re.I):
        raise RuntimeError(f"{name} failed: see {directory}/{name}.log (exit {code})")
    return status, output


def run_case(mesh, root, label, current, load=.002, fixed_cold=None,
             slopes=False, alumina_sigma=1e-12, export_fields=True):
    directory = root/label
    directory.mkdir(parents=True, exist_ok=True)
    write_sif(directory/"case.sif", mesh/"elmer", current, load, fixed_cold,
              slopes=slopes, alumina_sigma=alumina_sigma)
    status, log = execute(["ElmerSolver", "case.sif"], directory, "solver")
    changes = re.findall(r"ThermoElectricSolver:\s+Relative Change\s*:\s*([\d.Ee+\-]+)", log)
    if not changes or float(changes[-1]) > 1e-9:
        raise RuntimeError(f"Nonlinear solver did not converge in {directory}")
    result = postprocess(mesh, directory, export_fields=export_fields)
    result["solver_status"] = {**status, "nonlinear_last_relative_change": float(changes[-1]),
                               "nonlinear_iterations": len(changes)}
    (directory/"metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(f'{label}: I={current:+.3f} A, Tc={result["cold_mean_k"]:.6f} K, '
          f'V={result["voltage_v"]:.8g} V, energy={result["energy_relative_residual"]:.2g}, '
          f'current={result["current_relative_residual"]:.2g}', flush=True)
    return result


def upstream_test(out):
    test = out/"upstream-thermoelectric"
    test.mkdir(exist_ok=True)
    for path in Path("/opt/elmer/provenance/upstream-test").iterdir():
        if path.is_file():
            shutil.copy(path, test/path.name)
    execute(["ElmerGrid", "1", "2", "square.grd"], test, "grid")
    status, log = execute(["ElmerSolver", "ptest.sif"], test, "solver")
    # RUN + Reference Norm in the official SIF invokes Elmer's own norm test.
    if "PASSED all 1 tests!" not in log or "ALL DONE" not in log or "FAILED" in log:
        raise RuntimeError("Official Elmer reference-norm test failed")
    return status


def verify(results, convergence, quick=False):
    checks = {}
    checks["all_solver_exits_zero"] = all(r["solver_status"]["exit_code"] == 0 for r in results.values())
    checks["nonlinear_convergence"] = all(r["solver_status"]["nonlinear_last_relative_change"] < 1e-9 for r in results.values())
    checks["global_energy_below_1pct"] = all(abs(r["energy_relative_residual"]) < .01 for r in results.values())
    checks["finest_bath_gradient_energy_below_1pct"] = all(abs(r["bath_gradient_energy_relative_residual"]) < .01 for n, r in results.items() if not n.startswith("convergence_"))
    checks["current_mismatch_below_half_pct"] = all(abs(r["current_relative_residual"]) < .005 for r in results.values())
    checks["interior_driven_section_current_below_half_pct"] = all(r["section_current_relative_residual"] < .005 for r in results.values() if r["current_a"])
    checks["zero_current_section_absolute_error_below_1uA"] = all(r["section_current_absolute_error_a"] < 1e-6 for r in results.values() if not r["current_a"])
    checks["electrical_work_below_1pct"] = all(abs(r["power_work_relative_residual"]) < .01 for r in results.values())
    checks["free_weak_thermal_residual_below_1uW"] = all(r["free_thermal_residual_l1_w"] < 1e-6 for r in results.values())
    checks["free_weak_current_residual_below_1uA"] = all(r["free_current_residual_l1_a"] < 1e-6 for r in results.values())
    checks["alumina_leakage_below_1pA"] = all(r["alumina_leakage_upper_bound_a"] < 1e-12 for r in results.values())
    checks["polarity_temperature"] = results["sweep_p0200"]["cold_mean_k"] < 300 < results["sweep_m0200"]["cold_mean_k"]
    checks["open_circuit_seebeck_below_1pct"] = abs(results["open_circuit"]["open_circuit_seebeck_relative_error"]) < .01
    checks["zero_current_passive_load_warms_cold_face"] = results["sweep_p0000"]["cold_mean_k"] > 300
    if not quick:
        fine, medium = convergence[-1], convergence[-2]
        checks["finest_cold_temperature_change_below_1pct"] = abs(fine["cold_mean_k"]-medium["cold_mean_k"])/abs(fine["cold_mean_k"]) < .01
        checks["finest_delta_t_change_below_1pct"] = abs(fine["delta_t_k"]-medium["delta_t_k"])/abs(fine["delta_t_k"]) < .01
        checks["finest_voltage_change_below_1pct"] = abs(fine["voltage_v"]-medium["voltage_v"])/abs(fine["voltage_v"]) < .01
        checks["positive_current_absorbs_heat_at_clamped_cold_face"] = results["clamped_positive"]["cold_out_reaction_w"] < 0
        checks["negative_current_rejects_heat_at_clamped_cold_face"] = results["clamped_negative"]["cold_out_reaction_w"] > 0
        checks["insulator_regularization_cold_change_below_1mK"] = abs(results["insulator_check"]["cold_mean_k"]-results["sweep_p0300"]["cold_mean_k"]) < .001
        checks["constant_couple_temperature_reference_below_1pct"] = all(abs(r["cold_reference_relative_error"]) < .01 for n, r in results.items() if n.startswith("sweep_"))
        checks["constant_couple_voltage_reference_below_2pct"] = all(abs(r["voltage_reference_relative_error"]) < .02 for n, r in results.items() if n.startswith("sweep_") and abs(r["current_a"]) > 0)
    checks = {name: bool(value) for name, value in checks.items()}
    return {"passed": all(checks.values()), "checks": checks}


def plot_summary(out, results, convergence):
    import matplotlib.pyplot as plt
    sweep = sorted((r for n, r in results.items() if n.startswith("sweep_")), key=lambda x: x["current_a"])
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, key, ylabel, factor in zip(axes.flat,
            ("delta_t_k", "voltage_v", "electrical_input_w", "energy_relative_residual"),
            ("300 K - loaded cold face (K)", "N terminal - P ground (V)",
             "Electrical input (W)", "Energy residual (%)"), (1, 1, 1, 100)):
        ax.plot([r["current_a"] for r in sweep], [factor*r[key] for r in sweep], "o-", label="3D FEM")
        refkey = {"delta_t_k": "delta_t_k", "voltage_v": "voltage_v", "electrical_input_w": "power_w"}.get(key)
        if refkey:
            ax.plot([r["current_a"] for r in sweep], [r["ideal_reference"][refkey] for r in sweep], "--", label="Ideal constant couple")
        ax.set(xlabel="Current, N pad -> bridge -> P pad (A)", ylabel=ylabel)
        ax.grid(alpha=.3)
        ax.legend()
    fig.suptitle("G1 single couple: 300 K bath, 2 mW cold-face load\nConstant illustrative materials; zero contact resistances")
    fig.tight_layout()
    fig.savefig(out/"current_sweep.png", dpi=170)
    fig.savefig(out/"current_sweep.svg")
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
    for ax, key, label in zip(axes, ("cold_mean_k", "voltage_v", "bath_gradient_energy_relative_residual"),
                              ("Loaded cold mean (K)", "Voltage (V)", "Bath gradient energy residual")):
        ax.plot([r["nodes"] for r in convergence], [r[key] for r in convergence], "o-")
        ax.set(xlabel="Mesh nodes", ylabel=label)
        ax.grid(alpha=.3)
    fig.suptitle("G1 mesh convergence at +0.3 A, 2 mW load")
    fig.tight_layout()
    fig.savefig(out/"mesh_convergence.png", dpi=170)
    plt.close(fig)
    # Homogeneous, numeric CSV columns; full metadata is in JSON.
    keys = [k for k, v in sweep[0].items() if isinstance(v, (float, int)) and not isinstance(v, bool)]
    for name, rows in (("current_sweep.csv", sweep), ("mesh_convergence.csv", convergence)):
        with (out/name).open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)


def reprocess_run(out):
    """Recompute diagnostics from stored real fields without rerunning Elmer."""
    report = json.loads((out/"summary.json").read_text())
    convergence = []
    for i, old in enumerate(report["convergence"]):
        result = postprocess(out/f"mesh_{i}", out/f"convergence_{i}", export_fields=False)
        result["solver_status"] = old["solver_status"]
        convergence.append(result)
    fine = out/f"mesh_{len(convergence)-1}"
    results = {}
    for name, old in report["cases"].items():
        result = postprocess(fine, out/name, export_fields=(out/name/"derived.vtu").exists())
        result["solver_status"] = old["solver_status"]
        results[name] = result
    combined = {**results, **{f"convergence_{i}": r for i, r in enumerate(convergence)}}
    for name, result in combined.items():
        (out/name/"metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    verification = verify(combined, convergence, report["quick"])
    plot_summary(out, results, convergence)
    report.update(cases=results, convergence=convergence, verification=verification)
    (out/"summary.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps(verification, indent=2), flush=True)
    if not verification["passed"]:
        raise SystemExit("G1 verification FAILED after postprocessing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/fem-g1"))
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--postprocess-only", action="store_true",
                        help="recompute plots/checks from an existing run's actual fields")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out/"failure.json").exists():
        (out/"failure.json").rename(out/f"failure-{time.time_ns()}.json")
    if not shutil.which("ElmerSolver") or not shutil.which("ElmerGrid"):
        raise SystemExit("Use fem/bootstrap.sh and fem/run.sh; actual Elmer binaries required")
    if Path("/opt/elmer/provenance/commit").read_text().strip() != ELMER_COMMIT:
        raise SystemExit("Unexpected Elmer source commit")
    if args.postprocess_only:
        reprocess_run(out)
        return
    upstream = upstream_test(out)
    sizes = [.10] if args.quick else [.16, .10, .065]
    meshes, convergence, results = [], [], {}
    try:
        for i, size in enumerate(sizes):
            mesh = out/f"mesh_{i}"
            generate_mesh(mesh, size*1e-3)
            execute(["ElmerGrid", "14", "2", "couple.msh", "-out", "elmer"], mesh, "grid")
            meshes.append(mesh)
            convergence.append(run_case(mesh, out, f"convergence_{i}", .3, export_fields=False))
        fine = meshes[-1]
        currents = [-.2, 0., .2] if args.quick else [-.4, -.2, 0., .1, .2, .3, .4]
        for current in currents:
            label = f'sweep_{"m" if current < 0 else "p"}{round(abs(current)*1000):04d}'
            results[label] = run_case(fine, out, label, current,
                                      export_fields=current in (0., .2, -.2))
        results["open_circuit"] = run_case(fine, out, "open_circuit", 0., fixed_cold=280.)
        if not args.quick:
            results["clamped_positive"] = run_case(fine, out, "clamped_positive", .2, fixed_cold=300., export_fields=False)
            results["clamped_negative"] = run_case(fine, out, "clamped_negative", -.2, fixed_cold=300., export_fields=False)
            results["temperature_dependent"] = run_case(fine, out, "temperature_dependent", .2, slopes=True)
            results["insulator_check"] = run_case(fine, out, "insulator_check", .3, alumina_sigma=1e-14, export_fields=False)
        verification = verify({**results, **{f"convergence_{i}": r for i, r in enumerate(convergence)}}, convergence, args.quick)
        plot_summary(out, results, convergence)
        report = {"elmer_commit": ELMER_COMMIT, "upstream_test": upstream,
                  "quick": args.quick, "verification": verification,
                  "convergence": convergence, "cases": results}
        (out/"summary.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
        print(json.dumps(verification, indent=2), flush=True)
        if not verification["passed"]:
            raise SystemExit("G1 verification FAILED; inspect summary.json")
    except Exception as exc:
        (out/"failure.json").write_text(json.dumps({"error": str(exc)}, indent=2)+"\n")
        raise


if __name__ == "__main__":
    main()
