"""Actual coupled two-terminal full-stack solves; fail closed on unmet gates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from .fem_g1 import ELMER_COMMIT
from .fem_g1_run import execute, upstream_test
from .fem_g2b_connected import audit_mesh, connected_manifest, generate_mesh, orthogonal_audit
from .fem_g2b_physics import execute_solver, protected_integrity, write_sif
from .fem_g2b_post import postprocess


def source_hashes():
    root = Path(__file__).resolve().parents[1]
    files = [root/"tecooledmct"/f"fem_g2b_{n}.py" for n in ("connected", "physics", "post", "run")]
    files += [root/"tests/test_fem_g2b_physics.py", root/"fem/run_g2b.sh"]
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}


def prepare_mesh(mesh, size, refine, reuse=False, controlled=False):
    if reuse and (mesh/"mesh.npz").exists():
        import gmsh
        old = json.loads((mesh/"audit.json").read_text())
        if not np.isclose(old["mesh_size_m"], size) or old.get("bridge_gap_refinement_m") != refine or old.get("controlled_background_field",False)!=controlled:
            raise ValueError("Cached mesh parameters differ from requested study")
        m = connected_manifest()
        orthogonal_audit(m)
        data = np.load(mesh/"mesh.npz")
        gmsh.initialize()
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.open(str(mesh/"connected.msh"))
            _, tags, _ = gmsh.model.mesh.getElements(3)
            quality = np.concatenate([gmsh.model.mesh.getElementQualities(t, "minSICN") for t in tags])
        finally:
            gmsh.finalize()
        audit = audit_mesh(m, *(data[k] for k in ("points", "cells", "bodies", "faces", "boundaries")), quality)
        audit.update(mesh_size_m=size, bridge_gap_refinement_m=refine, controlled_background_field=controlled, reaudited_actual_mesh=True)
        (mesh/"audit.json").write_text(json.dumps(audit, indent=2)+"\n")
        previous=json.loads((mesh/"manifest.json").read_text())
        m["physical_boundary_names"]=previous["physical_boundary_names"]
        (mesh/"manifest.json").write_text(json.dumps(m,indent=2)+"\n")
    else:
        audit = generate_mesh(mesh, size, refine, controlled)
    execute(["ElmerGrid", "14", "2", "connected.msh", "-out", "elmer"], mesh, "grid")
    audit["gmsh_mesh_sha256"] = hashlib.sha256((mesh/"connected.msh").read_bytes()).hexdigest()
    audit["mesh_npz_sha256"] = hashlib.sha256((mesh/"mesh.npz").read_bytes()).hexdigest()
    print(f"Actual mesh PASS: {audit['nodes']} nodes / {audit['tetrahedra']} tets / {audit['dofs']} DOFs", flush=True)
    return audit


def run_case(mesh, out, label, current, load, fields=False, sigma=1e-12, resume=False, restart=None):
    case = out/label
    if resume and (case/"metrics.json").exists():
        old=json.loads((case/"metrics.json").read_text())
        if (old["current_a"],old["load_w"],old["alumina_sigma_s_m"])!=(current,load,sigma):
            raise ValueError("Resume BCs differ from recorded execution")
        if hashlib.sha256((case/"case.sif").read_bytes()).hexdigest()!=old["sif_sha256"] or hashlib.sha256((case/old["field_source"]).read_bytes()).hexdigest()!=old["vtu_sha256"]:
            raise ValueError("Resume SIF/VTU hashes changed")
        if old["solver_status"]["exit_code"]!=0:raise ValueError("Cannot resume a failed solver")
        result=postprocess(mesh,case,fields)
        result.update({k:old[k] for k in ("solver_status","mesh_path","sif_sha256","vtu_sha256")})
        result["execution_reused_without_new_solve"]=True
        result["case_path"]=str(case)
        (case/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
        print(f"Revalidated existing actual solve {label}: Tc={result['cold_mean_k']:.6f} K",flush=True)
        return result
    write_sif(case, mesh, current, load, sigma, restart)
    status = execute_solver(case)
    result = postprocess(mesh, case, fields)
    result["solver_status"] = status
    result["mesh_path"] = str(mesh)
    result["case_path"] = str(case)
    result["sif_sha256"] = hashlib.sha256((case/"case.sif").read_bytes()).hexdigest()
    result["vtu_sha256"] = hashlib.sha256((case/result["field_source"]).read_bytes()).hexdigest()
    (case/"metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(f"{label}: I={current:+.3f} A, load={load*1000:g} mW, Tc={result['cold_mean_k']:.6f} K, "
          f"V={result['voltage_v']:.8f} V, bath error={result['bath_gradient_energy_relative_residual']:.3g}, "
          f"leg error={result['max_leg_current_relative_error']}, "
          f"peak RSS={status['peak_rss_kib']/1024:.1f} MiB", flush=True)
    return result


def verify(cases, convergence, audits, quick=False):
    all_cases = [*cases.values(), *convergence]
    checks = {
        "actual_mesh_unique_two_terminal_88_leg_path": all(a["passed"] and a["external_terminals"] == 2 and a["electrical_components"] == 1 and a["legs"] == 88 for a in audits),
        "no_degenerate_or_extreme_sliver_tets": all(a["min_tetra_sicn"] > .01 and a["quality_below_001"] == 0 for a in audits),
        "all_solver_exits_zero": all(r["solver_status"]["exit_code"] == 0 for r in all_cases),
        "nonlinear_converged": all(r["solver_status"]["nonlinear_last_relative_change"] < 1e-9 for r in all_cases),
        "global_weak_energy_below_1pct": all(abs(r["energy_relative_residual"]) < .01 for r in all_cases),
        "electrical_work_below_1pct": all(abs(r["power_work_relative_residual"]) < .01 for r in all_cases),
        "every_fine_leg_current_below_half_pct": all(r["max_leg_current_relative_error"] < .005 for r in cases.values() if r["current_a"]),
        "both_fine_interstage_link_currents_below_half_pct": all(r["max_interstage_link_current_relative_error"] < .005 for r in cases.values() if r["current_a"]),
        "zero_cut_current_absolute_below_1uA": all(max(r[f"max_{kind}_current_absolute_error_a"] for kind in ("leg","bridge","interstage_link")) < 1e-6 for r in cases.values() if not r["current_a"]),
        "terminal_current_below_half_pct": all(r["current_relative_error"] < .005 for r in all_cases if r["current_a"]),
        "zero_terminal_current_below_1uA": all(r["current_absolute_error_a"] < 1e-6 for r in all_cases if not r["current_a"]),
        "all_175_component_cuts_recorded": all(len(r["cuts"]) == 175 for r in all_cases),
        "cut_areas_match": all(abs(c["area_m2"]/c["expected_area_m2"]-1) < 1e-7 for r in all_cases for c in r["cuts"].values()),
        "free_thermal_residual_below_1uW": all(r["free_thermal_residual_l1_w"] < 1e-6 for r in all_cases),
        "free_current_residual_below_1uA": all(r["free_current_residual_l1_a"] < 1e-6 for r in all_cases),
        "dielectric_leakage_below_1pA": all(r["alumina_leakage_upper_bound_a"] < 1e-12 for r in all_cases),
        "stage_control_volume_energy_below_1uW": all(abs(b["balance_residual_w"]) < 1e-6 for r in all_cases for b in r["stage_control_volume_budgets"]),
        "finite_positive_absolute_temperatures": all(0 < r["temperature_min_k"] < 600 and r["temperature_max_k"] < 600 for r in all_cases),
        "positive_drive_cools_and_negative_heats": cases["loaded_positive"]["cold_mean_k"] < 300 < cases["loaded_negative"]["cold_mean_k"],
        "zero_drive_loaded_face_warms": cases["loaded_zero"]["cold_mean_k"] > 300,
        "all_driven_cases_consume_electrical_work": all(r["electrical_input_w"] > 0 and np.sign(r["voltage_v"]) == np.sign(r["current_a"]) for r in all_cases if r["current_a"]),
    }
    if not quick:
        coarse, fine = convergence[0], convergence[-1]
        checks.update({
            "fine_direct_bath_energy_below_1pct": all(abs(r["bath_gradient_energy_relative_residual"]) < .01 for r in cases.values()),
            "every_fine_bridge_current_below_half_pct": all(r["max_bridge_current_relative_error"] < .005 for r in cases.values() if r["current_a"]),
            "cold_mean_mesh_change_below_1pct_lift": abs(fine["cold_mean_k"]-coarse["cold_mean_k"])/abs(fine["delta_t_k"]) < .01,
            "cold_max_mesh_change_below_1pct_lift": abs(fine["cold_max_k"]-coarse["cold_max_k"])/abs(fine["delta_t_k"]) < .01,
            "voltage_mesh_change_below_1pct": abs(fine["voltage_v"]-coarse["voltage_v"])/abs(fine["voltage_v"]) < .01,
            "zero_load_colder_than_loaded": cases["zero_load_positive"]["cold_mean_k"] < cases["loaded_positive"]["cold_mean_k"],
            "ceramic_sigma_100fold_reduction_below_1mK": abs(cases["leakage_check"]["cold_mean_k"]-cases["loaded_positive"]["cold_mean_k"]) < .001,
        })
    checks = {k: bool(v) for k,v in checks.items()}
    return {"passed": all(checks.values()), "quick_smoke_only": quick, "checks": checks}


def plots(out, cases, convergence):
    import matplotlib.pyplot as plt
    loaded = sorted([r for name,r in cases.items() if name.startswith("loaded_")], key=lambda r:r["current_a"])
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, key, label, multiplier in zip(axes.flat, ("delta_t_k","voltage_v","electrical_input_w","bath_gradient_energy_relative_residual"),
                 ("300 K - cold face (K)","Terminal voltage (V)","Input power (mW)","Direct bath energy mismatch (%)"), (1,1,1000,100)):
        ax.plot([r["current_a"] for r in loaded], [multiplier*r[key] for r in loaded], "o-", label="3D FEM")
        if key in ("delta_t_k","voltage_v"):
            ax.plot([r["current_a"] for r in loaded], [r["ideal_cascade_reference"][key] for r in loaded], "--", label="Ideal cascade; no routing shunts")
        ax.set(xlabel="Current (A)", ylabel=label)
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    fig.suptitle("Two-terminal 88-leg coupled FEM: 300 K bath, 2 mW top load\nInferred buried routing / constant illustrative materials, ideal contacts")
    fig.tight_layout()
    fig.savefig(out/"current_sweep.png", dpi=170)
    fig.savefig(out/"current_sweep.svg")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10,4))
    for i in range(4):
        axes[0].plot([r["current_a"] for r in loaded], [r["plate_temperatures"][f"ceramic_{i}"]["mean_k"] for r in loaded], "o-", label=f"Ceramic {i}")
    axes[0].set(xlabel="Current (A)", ylabel="Solved volume-average ceramic T (K)")
    axes[0].legend()
    for key,name in (("hot_out_w","Hot out"),("cold_absorbed_w","Cold absorbed"),("electrical_work_control_volume_w","Electrical work in control volume")):
        axes[1].plot(range(3), [1000*b[key] for b in cases["loaded_positive"]["stage_control_volume_budgets"]], "o-", label=name)
    axes[1].set(xlabel="Stage control volume, hot to cold", ylabel="Heat/work (mW)", xticks=range(3))
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out/"stage_temperatures_heat.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1,3,figsize=(11,3.5))
    for ax,key,label,factor in zip(axes,("cold_mean_k","voltage_v","bath_gradient_energy_relative_residual"),("Cold face (K)","Voltage (V)","Bath energy mismatch (%)"),(1,1,100)):
        ax.plot([r["nodes"] for r in convergence],[factor*r[key] for r in convergence],"o-")
        ax.set(xlabel="Nodes",ylabel=label)
    fig.tight_layout()
    fig.savefig(out/"mesh_convergence.png",dpi=170)
    plt.close(fig)
    legs = [c for c in cases["loaded_positive"]["cuts"].values() if c["kind"] == "leg"]
    fig,ax=plt.subplots(figsize=(10,3))
    ax.plot(range(88), [100*c["current_relative_error"] for c in legs],"o-",markersize=3)
    ax.axhline(.5,color="red",linestyle="--",label="0.5% gate")
    ax.set(xlabel="Leg order, bottom then middle then top",ylabel="Direct interior current error (%)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out/"all_88_leg_currents.png",dpi=170)
    plt.close(fig)
    keys=["current_a","load_w","cold_mean_k","cold_min_k","cold_max_k","delta_t_k","voltage_v","electrical_input_w","hot_out_reaction_w","hot_out_gradient_w","bath_gradient_energy_relative_residual","max_leg_current_relative_error","max_bridge_current_relative_error","max_interstage_link_current_relative_error","nodes","tetrahedra","dofs"]
    for name,rows in (("current_sweep.csv",loaded),("mesh_convergence.csv",convergence)):
        with (out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    columns=list(dict.fromkeys(k for r in cases.values() for c in r["cuts"].values() for k in c))
    with (out/"component_cuts.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["case","component",*columns]);w.writeheader()
        for name,r in cases.items():
            for comp,c in r["cuts"].items():w.writerow({"case":name,"component":comp,**c})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=Path("outputs/fem-g2b-two-terminal"))
    p.add_argument("--mesh-root",type=Path)
    p.add_argument("--reuse-mesh",action="store_true")
    p.add_argument("--quick",action="store_true")
    p.add_argument("--resume",action="store_true",help="revalidate hashed solved cases and continue; never invent solver success")
    args=p.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    mesh_root=args.mesh_root.resolve() if args.mesh_root else out
    if Path("/opt/elmer/provenance/commit").read_text().strip()!=ELMER_COMMIT:raise SystemExit("Wrong solver image")
    hashes=source_hashes(); protected=protected_integrity();upstream=upstream_test(out)
    audits=[];convergence=[];cases={}
    try:
        sizes=[(.18e-3,None,False)] if args.quick else [(.18e-3,None,False),(.12e-3,.04e-3,False),(.12e-3,.025e-3,True)]
        for i,(size,refine,controlled) in enumerate(sizes):
            mesh=mesh_root/f"mesh_{i}"
            audits.append(prepare_mesh(mesh,size,refine,args.reuse_mesh,controlled))
            convergence.append(run_case(mesh,out,f"convergence_{i}",.1,.002,resume=args.resume))
        fine=mesh_root/f"mesh_{len(sizes)-1}"
        drive=.05 if args.quick else .1
        if args.quick:
            cases["loaded_positive"]=run_case(fine,out,"loaded_positive",drive,.002,True,resume=args.resume)
        else:
            # This is the identical fine mesh/current/load point, already solved.
            # Reuse that actual execution explicitly instead of spending another
            # large factorization on a duplicate label; export from real fields.
            label=f"convergence_{len(sizes)-1}"
            cases["loaded_positive"]=run_case(fine,out,label,.1,.002,True,resume=True)
            cases["loaded_positive"]["same_execution_as_convergence_case"]=label
        restart=Path(cases["loaded_positive"]["case_path"])
        if not args.quick:
            cases["zero_load_positive"]=run_case(fine,out,"zero_load_positive",.1,0.,resume=args.resume,restart=restart)
            cases["leakage_check"]=run_case(fine,out,"leakage_check",.1,.002,sigma=1e-14,resume=args.resume,restart=restart)
            cases["loaded_p0050"]=run_case(fine,out,"loaded_p0050",.05,.002,resume=args.resume,restart=restart)
        cases["loaded_zero"]=run_case(fine,out,"loaded_zero",0.,.002,resume=args.resume,restart=restart)
        cases["loaded_negative"]=run_case(fine,out,"loaded_negative",-drive,.002,resume=args.resume,restart=Path(cases['loaded_zero']['case_path']))
        verification=verify(cases,convergence,audits,args.quick)
        plots(out,cases,convergence)
        if hashes!=source_hashes():raise RuntimeError("Source changed during actual run; repeat validation")
        report={"verification":verification,"source_sha256":hashes,"protected_integrity":protected,
                "upstream_test":upstream,"elmer_commit":ELMER_COMMIT,"quick":args.quick,
                "audits":audits,"convergence":convergence,"cases":cases}
        (out/"summary.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
        print(json.dumps(verification,indent=2),flush=True)
        if not verification["passed"]:raise SystemExit("G2b FULL ACCEPTANCE FAILED; raw evidence retained")
    except Exception as e:
        (out/"failure.json").write_text(json.dumps({"error":str(e)},indent=2)+"\n")
        raise


if __name__=="__main__":main()
