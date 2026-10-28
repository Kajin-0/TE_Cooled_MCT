"""Adaptive zero-current refinement; reverify completed actual driven fields.

This explicitly replaces two failed-accuracy passive cases with genuine finer
PDE executions. Original fields/statuses remain retained as unaccepted initial
mesh cases; no completed solve is attributed to an execution that did not occur.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil
import numpy as np
from .fem_g2c_contact import manifest,transition_profile
from .fem_g2c_mesh import generate_transition_mesh,verify_elmer_tetra_mapping
from .fem_g2b_connectivity import connectivity
from .fem_g2c import compile_profile,write_case,intact_checkpoints
from .fem_g2c_post import postprocess
from .fem_g2b_physics import execute_solver
from .fem_g1_run import execute
from .material_profiles import synthetic_profile
from .g2c_qualification import Contact


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,data):p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=Path('outputs/fem-g2c-contact-fine'));args=p.parse_args()
    out=args.out.resolve();root=Path(__file__).resolve().parents[1];old=json.loads((out/'summary.json').read_text())
    failed={k for k,v in old['checks'].items() if not v}
    if failed!={'zero_drive_absolute_cut_currents'}:raise SystemExit(f'Unexpected initial failed gates: {failed}')
    source=json.loads((root/'outputs/fem-g2c/summary.json').read_text())['source_sha256']
    source[str(Path(__file__).resolve().relative_to(root))]=digest(Path(__file__).resolve())
    for n,h in source.items():
        if digest(root/n)!=h:raise SystemExit(f'Frozen execution dependency changed: {n}')
    shutil.copy2(out/'summary.json',out/'summary-initial-mesh.json')
    base=synthetic_profile(False);cases={}
    # Independent fresh verification of four successful original driven fields.
    for label in ('zero_excess','electrical','fixed_reference','coupled'):
        r=old['cases'][label];case=Path(r['case_path']);mesh=Path(r['mesh_path'])
        if digest(case/'case.sif')!=r['sif_sha256'] or digest(case/r['field_source'])!=r['vtu_sha256'] or r['solver_status']['exit_code']!=0:raise ValueError('Original execution modified/failed')
        cp=transition_profile(base,Contact(**{k:r['contact'][k] for k in ('electrical_ohm_m2','thermal_m2_k_w','thickness_m')}))
        fresh=postprocess(mesh,case,base,contact_profile=cp)
        if abs(fresh['cold_mean_k']-r['cold_mean_k'])>1e-10 or abs(fresh['voltage_v']-r['voltage_v'])>1e-12:raise ValueError('Reverification changed field observables')
        fresh.update({k:r[k] for k in ('solver_status','sif_sha256','vtu_sha256','case_path','mesh_path')});fresh['execution_reverified_without_new_solve']=True
        cases[label]=fresh;save(case/'metrics.json',fresh)
    work=out/'zero_refinement';work.mkdir(exist_ok=True);mesh=work/'mesh';m=manifest();audit=generate_transition_mesh(mesh,.03e-3,m)
    d=np.load(mesh/'mesh.npz');audit['actual_tetra_connectivity']=connectivity(d['cells'],d['bodies'],{b['id'] for b in m['bodies'] if b['material']!='Alumina'})
    execute(['ElmerGrid','14','2','stage.msh','-out','elmer'],mesh,'grid');audit['elmer_tetra_mapping']=verify_elmer_tetra_mapping(mesh);save(mesh/'audit.json',audit)
    proxy=work/'input_template';proxy.mkdir(exist_ok=True);normalized=json.loads(json.dumps(m))
    for b in normalized['bodies']:b['material']=b['material'].replace('_contact','')
    save(proxy/'manifest.json',normalized)
    if not (proxy/'elmer').exists():(proxy/'elmer').symlink_to((mesh/'elmer').resolve(),target_is_directory=True)
    lib=compile_profile(work/'base_library',base)
    for label,rth in (('passive_reference',0.),('thermal',1e-5)):
        contact=Contact(0.,rth,m['transition_model']['thickness_m']);cp=transition_profile(base,contact);clib=compile_profile(work/('library_'+label),cp);case=work/label
        write_case(case,proxy,base,lib,0.,0.,hot=295.,cold=285.,restart_from=work/'passive_reference' if label=='thermal' else None)
        text=(case/'case.sif').read_text()
        for b in m['bodies']:
            if b['kind']=='contact_layer':text=re.sub(rf'(Body {b["id"]}\n.*?\n  Material = )\d+',rf'\g<1>{5 if b["material"].startswith("P") else 6}',text,flags=re.S)
        for polarity,mid in (('P',5),('N',6)):
            text+=f'\nMaterial {mid}\n'
            for key,symbol in (('Heat Conductivity','Heat'),('Electric Conductivity','Electric'),('Seebeck Coefficient','Seebeck')):text+=f'  {key} = Variable Temperature\n    Real Procedure "{clib.resolve()}" "{polarity}{symbol}"\n'
            text+='  Density = Real 7529\n  Heat Capacity = Real 544\nEnd\n'
        (case/'case.sif').write_text(text);meta=json.loads((case/'case.json').read_text());meta.update(contact=contact.layer_parameters(.4e-3**2),transition_model=m['transition_model']);meta['contact']['solver_gate']='ACTUAL EXPLICIT 3D TRANSITION DOMAINS';save(case/'case.json',meta)
        status=execute_solver(case);r=postprocess(mesh,case,base,contact_profile=cp)
        r.update(solver_status=status,sif_sha256=digest(case/'case.sif'),vtu_sha256=digest(case/r['field_source']),case_path=str(case),mesh_path=str(mesh));cases[label]=r;save(case/'metrics.json',r)
        print(label,'actual refined max cut A',max(c['absolute_error_a'] for c in r['cuts'].values()),flush=True)
    checks=dict(old['checks']);checks.update(
        zero_drive_absolute_cut_currents=all(max(c['absolute_error_a'] for c in cases[k]['cuts'].values())<1e-6 for k in ('passive_reference','thermal')),
        thermal_resistance_reduces_passive_heat=abs(cases['thermal']['cold_out_w'])<abs(cases['passive_reference']['cold_out_w']),
        global_energy_and_work=all(max(abs(r['energy_relative_residual']),abs(r['power_work_relative_residual']))<.01 for r in cases.values()),
        refined_zero_mesh_quality=audit['min_tetra_sicn']>.01,
        all_original_and_refined_cuts_have_expected_areas=all(len(r['cuts'])==31 and all(abs(c['area_m2']/c['expected_area_m2']-1)<1e-7 for c in r['cuts'].values()) for r in cases.values()),
        all_real_nonlinear_solves_converged=all(r['solver_status']['exit_code']==0 and r['solver_status']['nonlinear_last_relative_change']<1e-9 for r in cases.values()),
        sources_unchanged=all(digest(root/n)==h for n,h in source.items()))
    checks={k:bool(v) for k,v in checks.items()}
    result={**old,'passed':all(checks.values()),'checks':checks,'cases':cases,'source_sha256':source,'protected_integrity':intact_checkpoints(),
        'refined_zero_mesh_audit':audit,'initial_mesh_passive_cases':{k:old['cases'][k] for k in ('passive_reference','thermal')},
        'execution_note':'Four completed driven PDEs independently reverified, not rerun. Two genuine finer zero-drive solves replace initial accuracy failures; original fields/logs/status retained separately.'}
    save(out/'summary.json',result);print(json.dumps(checks,indent=2),flush=True)
    if not result['passed']:raise SystemExit('Adaptive contact qualification FAILED')

if __name__=='__main__':main()
