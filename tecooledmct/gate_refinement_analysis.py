"""Independent actual-field gate registry; separate meshes never imply release."""
import argparse,json
from pathlib import Path
from .geometry_rebaseline import ROOT,sha,write
from .cold20_analysis import accepted_nonraw,bath
from .cold_interface_audit import device

def analyze(mesh,case,out):
    if out.exists():raise ValueError('New audit label required')
    r=accepted_nonraw(case);out.mkdir(parents=True)
    cold=device(mesh,case,out/'cold');hot=bath(mesh,case,out/'bath')
    e=json.loads((case/'execution.json').read_text())
    result={'genuine_completed_coupled':True,'all_nonraw_gates_passed':True,'mesh_sha256':sha(mesh/'mesh.npz'),
        'field_sha256':e['vtu_sha256'],'source_sha256':sha(Path(__file__)),
        'tetrahedra':r['tetrahedra'],'nodes':r['nodes'],'die_mean_K':r['die_mean_k'],'voltage_V':r['voltage_v'],
        'cold_mismatches':[x['mismatch'] for x in cold['interfaces']],
        'cold_owner_height_um_quantiles':[x['owner_height_um_quantiles'] for x in cold['interfaces']],
        'bath_relative_error':hot['raw_relative_error'],'bath_owner_height_um_quantiles':hot['owner_normal_height_um_quantiles'],
        'same_case_raw_gates_passed':bool(cold['all_local_gates_passed'] and hot['one_percent_passed']),
        'nonlinear':e['solver_status'],'worst_cut_relative':r['worst_raw_cut_relative_error'],
        'global_heat_error_W':r['global_energy_error_w'],'free_heat_L1_W':r['free_thermal_residual_L1_w'],
        'free_current_L1_A':r['free_current_residual_L1_a'],
        'stage_control_volumes':r['stage_control_volumes'],'full_numerical_release':False,
        'scope':'actual raw owner gradients, unchanged5%/1%; same production mesh plus systematically refined comparator still required'}
    write(out/'summary.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,required=True);p.add_argument('--case',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();analyze(a.mesh.resolve(),a.case.resolve(),a.out.resolve())
