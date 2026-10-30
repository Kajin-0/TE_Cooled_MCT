"""Compare actual solved meshes; distinguish local sensitivity from qualified GCI."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from .geometry_rebaseline import ROOT,sha,write

RAW=ROOT/'outputs/cold-convergence'
CONFIG=[('original',ROOT/'outputs/geometry-complete-v4',ROOT/'outputs/corrected-thermal/cu_off',RAW/'coarse_diagnosis',RAW/'coarse_mesh'),
        ('cold30um',RAW/'mesh30',RAW/'cu_off30',RAW/'diagnosis30',RAW/'mesh30'),
        ('cold20um',RAW/'mesh20',RAW/'cu_off20_projected',RAW/'diagnosis20',RAW/'mesh20')]


def read(p):return json.loads(p.read_text())


def power_fit(h,q):
    """Unequal-spacing power fit is diagnostic; three points cannot prove asymptotia."""
    h=np.array(h,dtype=float);q=np.array(q,dtype=float);d=np.diff(q);r=h[:-1]/h[1:]
    result={'refinement_ratios':r.tolist(),'adjacent_changes':d.tolist(),'qualified_GCI':False}
    if len(q)!=3:return dict(result,status='SENSITIVITY ONLY: fewer than three actual solved meshes')
    if np.any(r<1.3):return dict(result,status='SENSITIVITY ONLY: effective ratio below1.3')
    if d[0]*d[1]<=0:return dict(result,status='NO GCI: nonmonotone or zero differences')
    ratio=d[0]/d[1];a=h[0]/h[1];b=h[1]/h[2]
    def f(p):return (a**p-1)/(1-b**(-p))-ratio
    if f(.01)*f(6.)>=0:return dict(result,status='NO GCI: no positive observed order in0.01..6')
    p=brentq(f,.01,6.);limit=q[-1]+(q[-1]-q[-2])/(b**p-1)
    result.update(observed_order=p,three_point_limit=float(limit),fit_fine_error=float(q[-1]-limit),
                  status='CONDITIONAL POWER FIT ONLY: mixed local refinement; independent asymptotic evidence absent')
    return result


def summarize(out):
    rows=[];baseline=None;references={};failed=[]
    for label,mesh,case,diag,stat in CONFIG:
        if not (case/'execution.json').exists():
            status=read(case/'solver-status.json')
            if not status['exit_code']:raise ValueError('Postprocessing missing for apparently completed solve')
            failed.append({'level':label,'case':str(case.relative_to(ROOT)),'solver_status':status,
                           'status':'FAILED actual execution; no final coupled field or QoI','mesh_sha256':sha(mesh/'mesh.npz')})
            continue
        m=read(case/'metrics.json');e=read(case/'execution.json');a=read(diag/'diagnosis.json');h=read(stat/'cold_mesh_metrics.json')
        if sha(mesh/'mesh.npz')!=e['mesh_sha256'] or e['vtu_sha256']!=a['field_sha256']:raise ValueError('Changed actual mesh/field diagnosis')
        if e['solver_status']['exit_code']!=0 or e['solver_status']['nonlinear_last_relative_change']>=1e-9:raise ValueError('Unsolved mesh')
        inputs={k:m[k] for k in ('current_a','deposited_power_w','pbias_w','parametric_absorption_w','cu_leads_on','au_bonds_on','package_sigma_s_m','material_status','boundary_scope')}
        if baseline is None:baseline=inputs
        if inputs!=baseline:raise ValueError('Unmatched physics in mesh sequence')
        if not np.isclose(m['mct_volume_m3'],2e-10,rtol=1e-10):raise ValueError('Source volume changed')
        row={'level':label,**{k:m[k] for k in ('nodes','tetrahedra','die_mean_k','cold_ceramic_k','hot_ceramic_k','voltage_v','hot_out_reaction_w',
            'hot_out_raw_gradient_w','direct_bath_relative_error','worst_raw_cut_relative_error','global_energy_error_w','free_thermal_residual_L1_w','free_current_residual_L1_a')},
            'die_min_k':m['domain_temperatures']['303']['min_k'],'die_max_k':m['domain_temperatures']['303']['max_k'],
            'regions':h['regions'],'axial_ray_segments':h['axial_ray_segments'],'interfaces':a['interfaces'],
            'hot_interfaces':m['interfaces'][:2],'whole_body_raw_balance':a['whole_body_raw_balance'],
            'primary_checks':m['checks'],'primary_checks_passed':m['passed'],'cold_interfaces_passed':a['all_local_gates_passed'],
            'stage_heat_budgets':m['stage_control_volumes'],'solver_status':e['solver_status']}
        rows.append(row);references[label]={str(p.relative_to(ROOT)):sha(p) for p in (mesh/'mesh.npz',case/'metrics.json',case/'execution.json',diag/'diagnosis.json',stat/'cold_mesh_metrics.json')}
    h=[v['regions']['fixed_cold_ROI']['h_eff_m'] for v in rows]
    fits={k:power_fit(h,[r[k] for r in rows]) for k in ('die_mean_k','voltage_v','cold_ceramic_k','hot_ceramic_k','hot_out_reaction_w','hot_out_raw_gradient_w')}
    fits['bath_region']={'qualified_GCI':False,'refinement_ratios':[rows[i]['regions']['bath_Kovar']['h_eff_m']/rows[i+1]['regions']['bath_Kovar']['h_eff_m'] for i in range(len(rows)-1)],
                       'status':'NO bath GCI: bath sizing fixed, not a bath-refinement sequence'}
    fits['attach_region']={'qualified_GCI':False,'refinement_ratios':[rows[i]['regions']['attach']['h_eff_m']/rows[i+1]['regions']['attach']['h_eff_m'] for i in range(len(rows)-1)],
                         'status':'NO attach GCI: fewer than three solved levels or final attach-specific effective ratio below1.3'}
    bench=read(RAW/'benchmark/summary.json');benchrows=[v for v in bench['cases'] if v['kind']=='distributed_MCT_source'];bfit={}
    for name,q,exact in [('MCT_bottom_raw_W',[r['interfaces'][1]['raw_outward_w'][1] for r in benchrows],.002),
                         ('MCT_mean_K',[r['MCT_mean_k'] for r in benchrows],benchrows[0]['analytic_MCT_mean_k'])]:
        fit=power_fit([r['h_m'] for r in benchrows],q);p=fit['observed_order'];expected=1 if name.endswith('W') else 2
        if abs(p-expected)>.001:raise ValueError('Benchmark observed order disagrees with analytic P1 prediction')
        err=abs(q[-1]-exact);gci=1.25*abs(fit['fit_fine_error'])
        fit.update(qualified_GCI=True,status='manufactured benchmark only; uniform r2 and analytic asymptotic error confirmed',
                   analytic_limit=exact,actual_fine_error=err,fine_GCI_absolute=gci,fine_GCI_relative=gci/abs(q[-1]),safety_factor=1.25)
        if abs(fit['three_point_limit']-exact)>1e-7:raise ValueError('Analytic benchmark extrapolation failed')
        bfit[name]=fit
    result={'actual_completed_coupled_meshes':len(rows),'failed_coupled_levels':failed,'matched_inputs':baseline,'cases':rows,'device_power_fits':fits,'benchmark_power_fits':bfit,
            'benchmark_finest_preregistered_gates_passed':bench['qualified'],'device_spatial_qualification_passed':False,
            'Cu_ON_refined':'NOT RUN: OFF bath1% and/or cold5% gates fail; do not infer physical30uK benefit',
            'original_failed_bath_criteria':'UNCHANGED FAILED; historic1.65587/1.51412/1.58383% not replaced by recovered flux',
            'full_device_qualification':False,'OEM_validated':False,'enclosure_gas_radiation':'NOT RUN; none imported',
            'reference_sha256':references,'source_sha256':sha(Path(__file__)),'plan_sha256':sha(ROOT/'data/cold_convergence/plan.json')}
    write(out,result);print(len(rows),'actual mesh solutions compared; cold/bath criteria retained; no device GCI claimed',flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();summarize(a.out.resolve())
