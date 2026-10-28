"""Execute and verify real G2a multi-couple thermoelectric FEM; preserve G1."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from .fem_g1 import ELMER_COMMIT
from .fem_g1_run import execute, upstream_test
from .fem_g2a import Stage, generate_mesh, stage_manifest, write_sif
from .fem_g2a_post import postprocess


def source_hashes():
    root = Path(__file__).resolve().parents[1]
    files = [*sorted((root/"tecooledmct").glob("fem_g2a*.py")), root/"tests/test_fem_g2a.py"]
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files if p.exists()}


def g1_integrity():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root/"fem/results/g1_20261028/manifest.json").read_text())
    for name, digest in manifest["source_sha256"].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"G1 source changed: {name}")
    for name, digest in manifest["artifacts_sha256"].items():
        if hashlib.sha256((root/"fem/results/g1_20261028"/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Published G1 artifact changed: {name}")
    return {"source_files_verified": len(manifest["source_sha256"]),
            "published_artifacts_verified": len(manifest["artifacts_sha256"]), "passed": True}


def run_case(mesh, out, name, current, load=.008, fixed_cold=None, fields=False):
    case = out/name
    write_sif(case/"case.sif", mesh, current, load, fixed_cold)
    status, log = execute(["ElmerSolver", "case.sif"], case, "solver", timeout=600)
    changes = re.findall(r"ThermoElectricSolver:\s+Relative Change\s*:\s*([\d.Ee+\-]+)", log)
    if not changes or float(changes[-1]) >= 1e-9 or "ALL DONE" not in log:
        raise RuntimeError(f"Unconverged actual coupled solve: {case}")
    result = postprocess(mesh, case, fields)
    result["solver_status"] = {**status, "nonlinear_last_relative_change": float(changes[-1]),
                               "nonlinear_iterations": len(changes),
                               "sif_sha256": hashlib.sha256((case/"case.sif").read_bytes()).hexdigest(),
                               "vtu_sha256": hashlib.sha256((case/result["field_source"]).read_bytes()).hexdigest()}
    (case/"metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(f'{name}: I={current:+.3f} A; Tc={result["cold_mean_k"]:.6f} K; '
          f'V={result["voltage_v"]:.8f} V; energy={result["bath_gradient_energy_relative_residual"]:.3g}; '
          f'leg cut error={result["max_leg_current_relative_error"]}', flush=True)
    return result


def verify(cases, convergence, audits, quick=False, couples=4):
    all_results = [*cases.values(), *convergence]
    checks = {
        "all_mesh_and_netlist_audits": all(a["passed"] and a["mesh_graph"]["unique_path"] for a in audits),
        "all_solver_exits_zero": all(r["solver_status"]["exit_code"] == 0 for r in all_results),
        "all_nonlinear_converged": all(r["solver_status"]["nonlinear_last_relative_change"] < 1e-9 for r in all_results),
        "global_energy_below_1pct": all(abs(r["energy_relative_residual"]) < .01 for r in all_results),
        "finest_bath_gradient_energy_below_1pct": all(abs(r["bath_gradient_energy_relative_residual"]) < .01 for r in cases.values()),
        "electrical_work_below_1pct": all(abs(r["power_work_relative_residual"]) < .01 for r in all_results),
        "terminal_current_below_half_pct": all(r["current_relative_error"] < .005 for r in all_results if r["current_a"]),
        "zero_terminal_current_below_1uA": all(r["current_absolute_error_a"] < 1e-6 for r in all_results if not r["current_a"]),
        "every_leg_current_below_half_pct": all(r["max_leg_current_relative_error"] < .005 for r in cases.values() if r["current_a"]),
        "every_bridge_current_below_half_pct": all(r["max_bridge_current_relative_error"] < .005 for r in cases.values() if r["current_a"]),
        "zero_cut_currents_below_1uA": all(max(r["max_leg_current_absolute_error_a"], r["max_bridge_current_absolute_error_a"]) < 1e-6 for r in cases.values() if not r["current_a"]),
        "leg_joule_matches_I2R_within_2pct": all(r["max_leg_joule_relative_error"] < .02 for r in cases.values() if r["current_a"]),
        "all_cut_areas_match": all(abs(c["area_m2"]/c["expected_area_m2"]-1) < 1e-8 for r in all_results for c in r["cuts"].values()),
        "all_legs_and_bridges_measured": all(len(r["cuts"]) == 4*couples-1 for r in all_results),
        "free_thermal_residual_below_1uW": all(r["free_thermal_residual_l1_w"] < 1e-6 for r in all_results),
        "free_current_residual_below_1uA": all(r["free_current_residual_l1_a"] < 1e-6 for r in all_results),
        "alumina_leakage_below_1pA": all(r["alumina_leakage_upper_bound_a"] < 1e-12 for r in all_results),
        "loaded_polarity_direction": cases["sweep_p0100"]["cold_mean_k"] < 300 < cases["sweep_m0100"]["cold_mean_k"],
        "zero_current_passive_warming": cases["sweep_p0000"]["cold_mean_k"] > 300,
        "open_seebeck_within_1pct": abs(cases["open_circuit"]["open_circuit_seebeck_relative_error"]) < .01,
        "loaded_temperature_reference_within_1pct": all(abs(r["cold_reference_relative_error"]) < .01 for name, r in cases.items() if name.startswith("sweep")),
        "loaded_voltage_reference_within_2pct": all(abs(r["voltage_reference_relative_error"]) < .02 for name, r in cases.items() if name.startswith("sweep") and r["current_a"]),
    }
    if not quick:
        fine, medium = convergence[-1], convergence[-2]
        checks["finest_mean_temperature_change_below_1pct_lift"] = abs(fine["cold_mean_k"]-medium["cold_mean_k"])/abs(fine["delta_t_k"]) < .01
        checks["finest_voltage_change_below_1pct"] = abs(fine["voltage_v"]-medium["voltage_v"])/abs(fine["voltage_v"]) < .01
        # Requirement also tests the maximum cold-face temperature statistic.
        checks["finest_cold_max_change_below_1pct_lift"] = abs(fine["cold_max_k"]-medium["cold_max_k"])/abs(fine["delta_t_k"]) < .01
        checks["clamped_positive_absorbs_cold_heat"] = cases["clamped_positive"]["cold_heat_absorbed_w"] > 0
        checks["clamped_negative_rejects_cold_heat"] = cases["clamped_negative"]["cold_heat_absorbed_w"] < 0
        checks["clamped_voltage_scales_from_G1_within_3pct"] = abs(cases["clamped_positive"]["g1_voltage_scaling_relative_error"]) < .03
        checks["open_voltage_scales_from_G1_within_3pct"] = abs(cases["open_circuit"]["g1_voltage_scaling_relative_error"]) < .03
    checks = {name: bool(value) for name, value in checks.items()}
    return {"passed": all(checks.values()), "checks": checks}


def plots(out, cases, convergence, manifest):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    sweep = sorted((r for n, r in cases.items() if n.startswith("sweep")), key=lambda r: r["current_a"])
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, key, label, ideal_key, factor in zip(axes.flat,
            ("delta_t_k", "voltage_v", "electrical_input_w", "hot_out_reaction_w"),
            ("300 K - cold face (K)", "Terminal voltage (mV)", "Electrical input (mW)", "Heat budget (mW)"),
            ("delta_t_k", "voltage_v", "power_w", None), (1, 1e3, 1e3, 1e3)):
        x = [r["current_a"] for r in sweep]
        ax.plot(x, [factor*r[key] for r in sweep], "o-", label="3D FEM" if ideal_key else "Hot out")
        if ideal_key:
            ax.plot(x, [factor*r["ideal_reference"][ideal_key] for r in sweep], "--", label="Ideal network + estimated Cu R")
        else:
            for k, name in (("cold_heat_absorbed_w", "Cold load"), ("electrical_input_w", "Electrical input"),
                            ("irreversible_joule_w", "Volume Joule")):
                ax.plot(x, [1e3*r[k] for r in sweep], "o--", label=name)
        ax.set(xlabel="Current (A)", ylabel=label)
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    fig.suptitle(f"G2a {manifest['config']['couples']} series couples: 300 K bath, "
                 f"{sweep[0]['load_w']*1e3:g} mW cold load\nIllustrative constant materials, ideal contacts")
    fig.tight_layout()
    fig.savefig(out/"current_sweep.png", dpi=170)
    fig.savefig(out/"current_sweep.svg")
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
    for ax, key, label, factor in zip(axes, ("cold_mean_k", "voltage_v", "bath_gradient_energy_relative_residual"),
                        ("Loaded cold mean (K)", "Voltage (mV)", "Bath gradient energy residual (%)"), (1, 1e3, 100)):
        ax.plot([r["nodes"] for r in convergence], [factor*r[key] for r in convergence], "o-")
        ax.set(xlabel="Mesh nodes", ylabel=label)
        ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(out/"mesh_convergence.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, side in zip(axes, ("hot", "cold")):
        for b in manifest["bodies"]:
            x, y, _, dx, dy, _ = np.array(b["box_m"])*1e3
            if b["kind"] in ("bridge", "terminal") and b["side"] == side:
                ax.add_patch(Rectangle((x, y), dx, dy, color="#bf853c", alpha=.6))
                ax.text(x+dx/2, y+dy/2, str(b["id"]), ha="center", va="center", fontsize=8)
            elif b["kind"] == "leg":
                ax.add_patch(Rectangle((x, y), dx, dy, fill=False, edgecolor="navy" if b["material"] == "N" else "darkred"))
                ax.text(x+dx/2, y+dy/2, f"{b['order']}:{b['material']}", ha="center", va="center", fontsize=8)
        ax.autoscale()
        ax.margins(.08)
        ax.set(title=f"{side.capitalize()} face routing; numbers = body IDs", xlabel="x (mm)", ylabel="y (mm)", aspect="equal")
    fig.suptitle("Actual non-overlapping Cu artwork / explicit P-N netlist")
    fig.tight_layout()
    fig.savefig(out/"topology.png", dpi=170)
    fig.savefig(out/"topology.svg")
    plt.close(fig)
    cut_case = cases.get("sweep_p0150", cases["sweep_p0100"])
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    cuts = cut_case["cuts"]
    names = list(cuts)
    axes[0].bar(range(len(names)), [cuts[n]["current_a"] for n in names])
    axes[0].axhline(cut_case["current_a"], color="black", linestyle="--", label="Prescribed current")
    axes[0].set(xticks=range(len(names)), xticklabels=names, ylabel="Signed current (A)")
    axes[0].tick_params(axis="x", labelrotation=90, labelsize=7)
    axes[0].legend()
    legs = [n for n in names if cuts[n]["kind"] == "leg"]
    axes[1].bar(range(len(legs)), [cuts[n]["joule_w"]*1e3 for n in legs], label="Integrated 3D Joule")
    axes[1].plot(range(len(legs)), [cuts[n]["ideal_joule_w"]*1e3 for n in legs], "kx", label="I² L/(sigma A)")
    axes[1].set(xticks=range(len(legs)), xticklabels=legs, ylabel="Leg Joule power (mW)")
    axes[1].tick_params(axis="x", labelrotation=90, labelsize=8)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(out/"component_currents_joule.png", dpi=170)
    plt.close(fig)
    numeric = [k for k, value in sweep[0].items() if isinstance(value, (float, int))]
    for filename, rows in (("current_sweep.csv", sweep), ("mesh_convergence.csv", convergence)):
        with (out/filename).open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=numeric, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    with (out/"component_cuts.csv").open("w", newline="") as f:
        columns = list(dict.fromkeys(k for cut in cuts.values() for k in cut))
        writer = csv.DictWriter(f, fieldnames=["case", "component", *columns], extrasaction="ignore")
        # Bridge entries omit the last two leg-specific values.
        writer.writeheader()
        for name, r in cases.items():
            for component, cut in r["cuts"].items():
                writer.writerow({"case": name, "component": component, **cut})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/fem-g2a"))
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--couples", type=int, default=4)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--leg-width-mm", type=float, default=.4)
    parser.add_argument("--leg-height-mm", type=float, default=1.)
    parser.add_argument("--gap-mm", type=float, default=.4)
    args = parser.parse_args()
    if Path("/opt/elmer/provenance/commit").read_text().strip() != ELMER_COMMIT:
        raise SystemExit("Unexpected solver version: use the existing fem/run.sh image")
    config = Stage(couples=args.couples, columns=args.columns, leg_width_m=args.leg_width_mm*1e-3,
                   leg_height_m=args.leg_height_mm*1e-3, gap_m=args.gap_mm*1e-3)
    manifest = stage_manifest(config)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    hashes = source_hashes()
    integrity = g1_integrity()
    upstream = upstream_test(out)
    convergence, audits, cases = [], [], {}
    sizes = [.10] if args.quick else [.16, .10, .065]
    for i, size in enumerate(sizes):
        mesh = out/f"mesh_{i}"
        audit = generate_mesh(mesh, size*1e-3, config)
        execute(["ElmerGrid", "14", "2", "stage.msh", "-out", "elmer"], mesh, "grid")
        audits.append(audit)
        print(f"Mesh {i}: {audit['nodes']} nodes, {audit['tetrahedra']} tetrahedra; topology PASS", flush=True)
        convergence.append(run_case(mesh, out, f"convergence_{i}", .15, load=.002*config.couples))
    currents = [-.1, 0., .1] if args.quick else [-.1, -.05, 0., .05, .1, .15, .2]
    fine = out/f"mesh_{len(sizes)-1}"
    for current in currents:
        name = f"sweep_{'m' if current < 0 else 'p'}{round(abs(current)*1000):04d}"
        cases[name] = run_case(fine, out, name, current, load=.002*config.couples, fields=current == .1)
    cases["open_circuit"] = run_case(fine, out, "open_circuit", 0., fixed_cold=280.)
    if not args.quick:
        cases["clamped_positive"] = run_case(fine, out, "clamped_positive", .2, fixed_cold=300.)
        cases["clamped_negative"] = run_case(fine, out, "clamped_negative", -.2, fixed_cold=300.)
        root = Path(__file__).resolve().parents[1]
        g1 = json.loads((root/"fem/results/g1_20261028/summary.json").read_text())["cases"]
        for name in ("open_circuit", "clamped_positive"):
            measured = cases[name]["voltage_v"]
            expected = config.couples*g1[name]["voltage_v"]
            cases[name]["g1_voltage_scaling_relative_error"] = (measured-expected)/expected
            cases[name]["g1_voltage_ratio"] = measured/g1[name]["voltage_v"]
            (out/name/"metrics.json").write_text(json.dumps(cases[name], indent=2)+"\n")
    verification = verify(cases, convergence, audits, args.quick, config.couples)
    plots(out, cases, convergence, manifest)
    if hashes != source_hashes():
        raise RuntimeError("Simulation source changed during the run; repeat verification")
    report = {"elmer_commit": ELMER_COMMIT, "source_sha256": hashes,
              "g1_integrity": integrity, "upstream_test": upstream, "quick": args.quick,
              "config": asdict(config), "audits": audits, "verification": verification,
              "convergence": convergence, "cases": cases}
    (out/"summary.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps(verification, indent=2), flush=True)
    if not verification["passed"]:
        raise SystemExit("G2a FAILED; numerical diagnostics are retained")


if __name__ == "__main__":
    main()
