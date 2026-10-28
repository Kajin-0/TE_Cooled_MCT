"""Geometry-parameterized TEC sweep plus spatial finite-volume single-pellet checks.

Run: python -m tecooledmct.geometry_demo --out outputs/pellet-study
"""
import argparse, csv, json
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar, brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .model import Scenario
from .geometry_sweep import TECGeometry, solve_geometry, sweep_pellet_height
from .pellet_fvm import PelletField, simulate_pellet

def minimum_power_at_target(s,g,target_k=200.):
    cache={}
    def pred(I):
        if I not in cache:cache[I]=solve_geometry(replace(s,current_a=float(I)),g)
        return cache[I]
    # The low-current branch is assumed monotonic; solve within 0.2..1.05A.
    opt=minimize_scalar(lambda i:pred(i)["detector_k"],bounds=(.2,1.05),method="bounded",options={"xatol":1e-3})
    if pred(float(opt.x))["detector_k"]>target_k:
        return {"feasible":False,"power_w":None,"current_a":None,"detector_k":None}
    I=.2 if pred(.2)["detector_k"]<=target_k else brentq(lambda x:pred(x)["detector_k"]-target_k,.2,float(opt.x),xtol=2e-5)
    r=pred(float(I))
    return {"feasible":True,"power_w":r["electrical_power_w"],"current_a":float(I),"detector_k":r["detector_k"]}

def run(output,scenario=Scenario(),target_k=200.):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    baseline_g=TECGeometry()
    factors=np.linspace(.65,1.35,29)
    rows=sweep_pellet_height(scenario,factors,g=baseline_g)
    for r in rows:
        g=replace(baseline_g,leg_lengths_mm=tuple(float(x)*r["factor"] for x in baseline_g.leg_lengths_mm))
        r["optimized"]=minimum_power_at_target(scenario,g,target_k)
    baseline=solve_geometry(scenario,baseline_g)
    def plot(x,y,file,xlabel,ylabel):
        fig,ax=plt.subplots(figsize=(8.4,4.8));ax.plot(x,y);ax.set(xlabel=xlabel,ylabel=ylabel);ax.grid(alpha=.25)
        fig.tight_layout();fig.savefig(out/file,dpi=180);plt.close(fig)
    X=[r["factor"] for r in rows]
    plot(X,[r["detector_k"] for r in rows],"geometry_vs_detector_temperature.png",
         "Pellet length / reference length","Detector temperature at 0.65 A (K)")
    fig,ax=plt.subplots(figsize=(8.4,4.8))
    ax.plot(X,[r["electrical_power_w"] for r in rows],label="Fixed current: 0.65 A")
    ax.plot(X,[r["optimized"]["power_w"] if r["optimized"]["feasible"] else np.nan for r in rows],
            label=f"Min power for {target_k:.0f} K (optimized current)")
    ax.set(xlabel="Pellet length / reference length",ylabel="TEC electrical input (W)")
    ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(out/"geometry_vs_electrical_power.png",dpi=180);plt.close(fig)
    plot(X,[r["TEC_resistance_ohm"] for r in rows],"geometry_vs_tec_resistance.png",
         "Pellet length / reference length","TEC series resistance (ohm)")
    cold=baseline["stage_k"][2];hot=baseline["stage_k"][1]
    fields={}
    fig,ax=plt.subplots(figsize=(8.4,4.8))
    for f in (.7,1.,1.3):
        p=PelletField(stage=2,leg_height_mm=.64*f,leg_side_mm=.4,nx=9,ny=9,nz=30,
              current_a=scenario.current_a,cold_k=cold,hot_k=hot,
              side_h_w_m2k=5.,side_ambient_k=scenario.ambient_k)
        r=simulate_pellet(p)
        fields[str(f)]={"qc_w_per_pellet":r["qc_w_per_pellet"],
             "joule_w_per_pellet":r["joule_heating_w_per_pellet"],
             "side_heat_w_per_pellet":r["heat_out_sides_w_per_pellet"],
             "pde_energy_residual_w":r["pde_energy_residual_w"],
             "centerline_k":r["centerline_k"].tolist()}
        zz=(np.arange(len(r["centerline_k"]))+.5)/p.nz*p.leg_height_mm
        ax.plot(zz,r["centerline_k"],label=f"{f:.0%} length ({p.leg_height_mm:.3f} mm)")
        if f==1.:
            fig2,ax2=plt.subplots(figsize=(7.5,5))
            image=ax2.imshow(r["field_k"][:,p.ny//2,:],origin="lower",
                extent=[0,p.leg_side_mm,0,p.leg_height_mm],aspect="auto",cmap="inferno")
            ax2.set(xlabel="Across pellet (mm)",ylabel="Axial coordinate (mm)",
                    title="3D voxel finite-volume thermal solution, central plane")
            fig2.colorbar(image,ax=ax2,label="Temperature (K)")
            fig2.tight_layout();fig2.savefig(out/"pellet_3d_fvm_slice.png",dpi=180);plt.close(fig2)
    ax.set(xlabel="Distance from cold ceramic (mm)",ylabel="Pellet core temperature (K)")
    ax.legend();ax.grid(alpha=.25);fig.tight_layout();fig.savefig(out/"pellet_3d_fvm_profiles.png",dpi=180);plt.close(fig)
    with (out/"pellet_geometry_sweep.csv").open("w",newline="") as f:
        columns=["scale","bottom_mm","middle_mm","top_mm","detector_k","power_at_fixed_current_w","R_ohm",
                 "target_k","min_power_for_target_w","optimum_current_a"]
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for r in rows:
            opt=r["optimized"];L=r["leg_lengths_mm"]
            writer.writerow(dict(zip(columns,[r["factor"],*L,r["detector_k"],r["electrical_power_w"],
                 r["TEC_resistance_ohm"],target_k,opt["power_w"],opt["current_a"]])))
    selected={str(f):next(r for r in rows if abs(r["factor"]-f)<1e-8) for f in (.7,1.,1.3)}
    report={"baseline":baseline,"target_k":target_k,"selected_designs":selected,"field_solutions":fields,
        "warning":"Geometry-aware *network* + SEPARATE spatial 3D single-pellet FVM. NOT a full-package 3D FEM. Not validated."}
    (out/"pellet_geometry_study.json").write_text(json.dumps(report,indent=2))
    return report

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--out",default="outputs/pellet-study")
    parser.add_argument("--target-k",type=float,default=200.)
    args=parser.parse_args()
    r=run(args.out,target_k=args.target_k)
    print(json.dumps({"baseline_k":r["baseline"]["detector_k"],
           "selected":{k:{"detector_k":v["detector_k"],
           "fixed_power_w":v["electrical_power_w"],"optimized":v["optimized"]}
           for k,v in r["selected_designs"].items()}},indent=2))

if __name__=="__main__":main()
