"""Run reproducible proof-of-concept sweeps and write machine-readable outputs."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .model import Scenario, solve, calibration_check
from .experiments import compare_gases, monte_carlo, sweep, simulate_transient


def run(output:Path, scenario:Scenario, quick=False):
    output.mkdir(parents=True,exist_ok=True)
    baseline=solve(scenario)
    current=sweep(scenario,'current_a',np.linspace(.15,1.0,18 if quick else 43))
    pressure=sweep(scenario,'gas_pressure_pa',np.geomspace(1,101325,14 if quick else 35))
    aperture=sweep(scenario,'aperture_area_mm2',np.linspace(0,50,8 if quick else 21))
    bias=sweep(scenario,'detector_bias_v',np.linspace(0,2,9 if quick else 21))
    gases=compare_gases(scenario)
    mc=monte_carlo(scenario,30 if quick else 200)
    tr=simulate_transient(scenario,120,241)
    payload={'scenario':asdict(scenario),'baseline':baseline,'calibration':calibration_check(),
             'gas_comparison':gases,'current_sweep':current,'pressure_sweep':pressure,
             'aperture_sweep':aperture,'detector_bias_sweep':bias,
             'uncertainty_sweep':mc,'transient':tr}
    (output/'results.json').write_text(json.dumps(payload,indent=2))
    def graph(rows,xname,yname,fn, xlabel,ylabel, marker=None):
        rows=[r for r in rows if r.get('status','converged')=='converged']
        fig,ax=plt.subplots(figsize=(8,4.7))
        ax.plot([r[xname] for r in rows],[r[yname] for r in rows],marker=marker)
        ax.set(xlabel=xlabel,ylabel=ylabel);ax.grid(alpha=.25)
        fig.tight_layout();fig.savefig(output/fn,dpi=180);plt.close(fig)
    graph(current,'input','detector_k','current_vs_detector.png','TEC current (A)','Detector temperature (K)')
    graph(pressure,'input','detector_k','pressure_vs_detector.png','Gas pressure (Pa)','Detector temperature (K)')
    graph(aperture,'input','detector_k','aperture_vs_detector.png','Added warm aperture area (mm²)','Detector temperature (K)')
    graph(bias,'input','detector_k','bias_vs_detector.png','Detector bias (V)','Detector temperature (K)')
    gases_names=[r['gas'] for r in gases]
    fig,ax=plt.subplots(figsize=(8,4.7));ax.bar(gases_names,[r['detector_k'] for r in gases]);ax.set_ylabel('Detector temperature (K)');ax.tick_params(axis='x',rotation=25);fig.tight_layout();fig.savefig(output/'gas_comparison.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.7))
    for k,label in [('bottom_k','Stage 1'),('middle_k','Stage 2'),('detector_k','Stage 3 / Detector'),('hot_k','Hot-side')]:ax.plot(tr['time_s'],tr[k],label=label)
    ax.set(xlabel='Time (s)',ylabel='Temperature (K)');ax.legend();ax.grid(alpha=.25);fig.tight_layout();fig.savefig(output/'cooldown_transient.png',dpi=180);plt.close(fig)
    summary={"baseline_detector_k":round(baseline['detector_k'],3),"baseline_stages_k":[round(x,3) for x in baseline['stage_k']],"calibration":payload['calibration'],"gases_ranked":[(r['gas'],round(r['detector_k'],3)) for r in gases],"sensitivity_k_p05_p95":[mc['p05_k'],mc['p95_k']]}
    (output/'summary.json').write_text(json.dumps(summary,indent=2))
    return summary


def main():
    ap=argparse.ArgumentParser(description='Preliminary HgCdTe three-stage TEC multiphysics proof-of-concept')
    ap.add_argument('--out',default='outputs/demo')
    ap.add_argument('--scenario',help='JSON file overriding Scenario fields')
    ap.add_argument('--quick',action='store_true')
    args=ap.parse_args()
    params=json.loads(Path(args.scenario).read_text()) if args.scenario else {}
    s=Scenario(**params).validate()
    print(json.dumps(run(Path(args.out),s,args.quick),indent=2))
if __name__=='__main__':main()
