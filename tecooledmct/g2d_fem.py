"""Bounded actual Elmer directions; constants are diagnostics, never OEM grades."""
from pathlib import Path
import hashlib,json,re,shutil
import numpy as np
from .g2d_data import ROOT,DATA,sha,dump,preserve
from .fem_g2a import PROPERTIES
from .material_profiles import Curve,Profile,load_profile,DATA as MATERIAL_DATA
from .fem_g2b_physics import write_sif,execute_solver
from .fem_g2c import compile_profile,write_case
from .fem_g2c_post import postprocess
from .fem_g2c_mesh import verify_elmer_tetra_mapping
from .fem_g2b_connected import audit_mesh
from .fem_g2b_connectivity import connectivity
from .fem_g1_run import execute


def constant_profile(s_scale=1.,k_scale=1.):
    curves={}
    for p in ('P','N'):
        k,sigma,s=PROPERTIES[p][:3]
        curves[p]={'k':Curve((1.,1500.),(k*k_scale,k*k_scale),'W/(m K)',True),
            'rho':Curve((1.,1500.),(1/sigma,1/sigma),'ohm m',True),'S':Curve((1.,1500.),(s*s_scale,s*s_scale),'V/K')}
    return Profile({'id':f'constant_diagnostic_S{s_scale}_k{k_scale}','status':'MATHEMATICAL CONSTANT LAW; no measured wide-T/OEM-grade validity'},curves)


def prepare(out,mesh_index=2):
    import gmsh
    mesh=out/'mesh';mesh.mkdir(parents=True,exist_ok=True)
    source=ROOT/'fem/results/g2b_two_terminal_20261028/meshes'/f'mesh_{mesh_index}'
    for name in ('mesh.npz','manifest.json','connected.msh'):shutil.copy2(source/name,mesh/name)
    m=json.loads((mesh/'manifest.json').read_text());d=np.load(mesh/'mesh.npz');gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(mesh/'connected.msh'));_,tt,_=gmsh.model.mesh.getElements(3)
        q=np.concatenate([gmsh.model.mesh.getElementQualities(t,'minSICN') for t in tt])
    finally:gmsh.finalize()
    audit=audit_mesh(m,*(d[k] for k in ('points','cells','bodies','faces','boundaries')),q)
    audit['actual_tetra_connectivity']=connectivity(d['cells'],d['bodies'],{b['id'] for b in m['bodies'] if b['material']!='Alumina'})
    execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],mesh,'grid');audit['elmer_tetra_mapping']=verify_elmer_tetra_mapping(mesh)
    audit['mesh_npz_sha256']=sha(mesh/'mesh.npz');dump(mesh/'audit.json',audit);return mesh,audit


def solve_constant(out,mesh,label,current,s_scale=1.,k_scale=1.,restart=None):
    case=out/label;write_sif(case,mesh,current,0.,restart_from=restart)
    text=(case/'case.sif').read_text()
    for mid,polarity in ((1,'P'),(2,'N')):
        start=text.index(f'Material {mid}\n');end=text.index('\nEnd',start);block=text[start:end]
        for key,value in (('Heat Conductivity',PROPERTIES[polarity][0]*k_scale),('Seebeck Coefficient',PROPERTIES[polarity][2]*s_scale)):
            block=re.sub(rf'  {key} = Real [^\n]+',f'  {key} = Real {value:.16g}',block)
        text=text[:start]+block+text[end:]
    (case/'case.sif').write_text(text);meta=json.loads((case/'case.json').read_text());profile=constant_profile(s_scale,k_scale)
    meta.update(fixed_cold_k=None,profile_id=profile.metadata['id'],profile_status=profile.metadata['status'],
        material_coverage='constant diagnostic, no measured-T domain assertion',ambient='vacuum',seebeck_scale=s_scale,k_scale=k_scale)
    dump(case/'case.json',meta);status=execute_solver(case);r=postprocess(mesh,case,profile,export=True)
    r.update(solver_status=status,sif_sha256=sha(case/'case.sif'),vtu_sha256=sha(case/r['field_source']),case_path=str(case),mesh_path=str(mesh),
        comparison_role='preregistered calibration point, not held-out selection',coefficient_validity='constant-law diagnostic only; no measured wide-T grade validation')
    dump(case/'metrics.json',r);print(label,'actual Tc/V',r['cold_mean_k'],r['voltage_v'],'cut',r['max_cut_relative_error'],flush=True);return r


def main():
    out=ROOT/'outputs/fem-g2d';out.mkdir(parents=True,exist_ok=True);protected=preserve()
    files=[ROOT/'tecooledmct/g2d_fem.py',ROOT/'tecooledmct/g2d_data.py',DATA/'preregistration.json',DATA/'parameters.json']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in files};mesh,audit=prepare(out)
    # Strict real full-stack 300 K source-domain probe, before diagnostic constants.
    profile=load_profile(MATERIAL_DATA/'zhang2025_he_40_300_v2.json');lib=compile_profile(out/'probe_library',profile);case=out/'source_300K_probe'
    write_case(case,mesh,profile,lib,.1,0.,hot=300.,stack=True)
    try:
        status=execute_solver(case)
        metric=postprocess(mesh,case,profile)
        probe={'status':'CONVERGED IN SOURCE DOMAIN','solver_status':status,'metrics':metric,'source_backed_300k_possible':True}
    except RuntimeError:
        log=(case/'solver.log').read_text();status=json.loads((case/'solver-status.json').read_text())
        if 'Local temperature outside qualified profile interval' not in log:raise
        rejected=re.findall(r'Rejected local T:\s*([\d.Ee+\-]+)',log)
        probe={'status':'BLOCKED BY ACTUAL LOCAL-T COVERAGE','source_backed_300k_possible':False,'solver_status':status,
            'rejected_temperature_k':float(rejected[-1]) if rejected else None,'no_clamping_or_extrapolation':True,'accepted_performance_prediction':False}
    dump(case/'probe.json',probe);print('Source-domain probe:',probe['status'],probe.get('rejected_temperature_k'),flush=True)
    reg=json.loads((DATA/'preregistration.json').read_text());cases={};restart=None
    for direction in reg['pde_directions_preregistered']:
        label=direction['id'];cases[label]=solve_constant(out,mesh,label,direction['current_a'],direction['seebeck_scale'],direction['k_scale'],restart)
        if label=='baseline':restart=out/label
    base=cases['baseline'];effects={}
    for label in ('seebeck_minus10','k_plus10'):
        r=cases[label];effects[label]={'delta_cold_k':r['cold_mean_k']-base['cold_mean_k'],'delta_voltage_v':r['voltage_v']-base['voltage_v'],
            'delta_input_w':r['electrical_input_w']-base['electrical_input_w'],'method':'actual coupled 3D Elmer finite perturbation, no FEM fit'}
    checks={'actual_mesh_audit':audit['passed'],'all_actual_solver_converged':all(r['solver_status']['exit_code']==0 and r['solver_status']['nonlinear_last_relative_change']<1e-9 for r in cases.values()),
        'all_175_component_cuts_below_half_pct':all(len(r['cuts'])==175 and r['max_cut_relative_error']<.005 for r in cases.values()),
        'direct_bath_energy_below_1pct':all(abs(r['bath_gradient_energy_relative_residual'])<.01 for r in cases.values()),
        'global_energy_work_below_1pct':all(max(abs(r['energy_relative_residual']),abs(r['power_work_relative_residual']))<.01 for r in cases.values()),
        'free_residuals_below_1uW_1uA':all(r['free_thermal_residual_l1_w']<1e-6 and r['free_current_residual_l1_a']<1e-6 for r in cases.values()),
        'all_cut_areas_match':all(abs(c['area_m2']/c['expected_area_m2']-1)<1e-7 for r in cases.values() for c in r['cuts'].values()),
        'sources_unchanged':all(sha(ROOT/n)==h for n,h in hashes.items())}
    checks={k:bool(v) for k,v in checks.items()};result={'passed':all(checks.values()),'checks':checks,'cases':cases,'effects':effects,'source_domain_probe':probe,
        'source_sha256':hashes,'protected_integrity':protected,'audit':audit,'qualification':'OEM grade/identification NOT ESTABLISHED; constant diagnostic directions, source-domain limit enforced',
        'mesh_limitation':'Reused verified fine G2b grid; current/energy checked for each new point. No new parameter-direction mesh refinement study claimed.'}
    dump(out/'summary.json',result);print(json.dumps(checks,indent=2),flush=True)
    if not result['passed']:raise SystemExit('Actual G2d FEM acceptance gate failed')

if __name__=='__main__':main()
