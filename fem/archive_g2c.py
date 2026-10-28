#!/usr/bin/env python3
"""Publish only accepted actual G2c evidence, retaining failure provenance apart."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,csv,gzip

ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(p):
    p=Path(p)
    if p.is_relative_to('/work'):p=ROOT/p.relative_to('/work')
    if not p.resolve().is_relative_to(ROOT):raise ValueError('Non-project evidence path')
    return p


def main():
    roots={'stage':ROOT/'outputs/fem-g2c','contact':ROOT/'outputs/fem-g2c-contact-fine','stack':ROOT/'outputs/fem-g2c-stack','low_temperature':ROOT/'outputs/fem-g2c-low-temperature'}
    reports={n:json.loads((d/'summary.json').read_text()) for n,d in roots.items()}
    if not(reports['stage']['verification']['passed'] and reports['contact']['passed'] and reports['stack']['passed'] and reports['low_temperature']['passed']):raise SystemExit('Numerical qualification gates must pass')
    test=(ROOT/'logs/pytest-g2c-final.log').read_text()
    if not re.search(r'(?m)^\d+ passed(?:,.*)? in ',test):raise SystemExit('Completed passing full solver tests required')
    sources={};execution_test_versions={}
    for r in reports.values():
        for n,h in r['source_sha256'].items():
            if n.startswith('tests/'):
                execution_test_versions.setdefault(n,set()).add(h)
                continue  # Test fixtures are not PDE inputs; verified separately below.
            if digest(ROOT/n)!=h:raise SystemExit(f'Source changed after actual run: {n}')
            sources[n]=h
    out=ROOT/'fem/results/g2c_20261028';out.mkdir(parents=True,exist_ok=True)
    def copy(src,rel):
        target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
    def write(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    resources=[];meshes=set();runtime={}
    for group,r in reports.items():
        if (roots[group]/'summary-initial-mesh.json').exists():copy(roots[group]/'summary-initial-mesh.json',f'{group}/initial-mesh-unaccepted.json')
        copy(roots[group]/'summary.json',f'{group}/summary.json')
        for label,case in r['cases'].items():
            path=local(case['case_path']);mesh=local(case['mesh_path']);meshes.add((group,mesh))
            if case['current_absolute_error_a']>=1e-6 or case['free_current_residual_l1_a']>=1e-6 or case['free_thermal_residual_l1_w']>=1e-6:raise ValueError('Actual global/free-node current or heat residual exceeded absolute gate')
            if case['solver_status']['nonlinear_last_relative_change']>=1e-9:raise ValueError('Actual nonlinear solve not converged')
            expected_cuts=175 if group=='stack' else 31 if group=='contact' else 1 if label=='thomson_rod' else 15
            if len(case['cuts'])!=expected_cuts or any(abs(c['area_m2']/c['expected_area_m2']-1)>1e-7 for c in case['cuts'].values()):raise ValueError('Missing component cut or mismatched physical area')
            if case['solver_status']['exit_code'] or digest(path/'case.sif')!=case['sif_sha256'] or digest(path/case['field_source'])!=case['vtu_sha256']:raise ValueError(f'Actual execution modified: {group}/{label}')
            for name in ('case.sif','case.json','solver.log','solver-status.json'):copy(path/name,f'{group}/cases/{label}/{name}')
            write(f'{group}/cases/{label}/metrics.json',case)
            resources.append({'group':group,'case':label,'nodes':case['nodes'],'dofs':case['dofs'],**case['solver_status']})
        for source_file in roots[group].rglob('Material.F90'):
            folder=source_file.parent
            for name in ('Material.F90','compile.log','compile-status.json'):
                if (folder/name).exists():copy(folder/name,Path(group)/'libraries'/folder.relative_to(roots[group])/name)
            for file in folder.iterdir():
                if file.is_file():runtime[str(file.relative_to(ROOT))]=digest(file)
    for group,mesh in meshes:
        for name in ('mesh.npz','manifest.json','audit.json','gmsh.log','grid.log','grid-status.json'):
            if (mesh/name).exists():copy(mesh/name,Path(group)/'meshes'/mesh.relative_to(roots[group])/name)
    selection=[('stage','source_3'),('stage','thomson_rod'),('contact','coupled'),('stack','fine'),('low_temperature','source_low_temperature')]
    for group,label in selection:
        c=reports[group]['cases'][label];p=local(c['case_path'])
        for name in (c['field_source'],'derived.vtu','fields.png'):
            if not (p/name).exists():continue
            rel=Path('fields')/f'{group}_{label}'/name
            if (p/name).stat().st_size>48*2**20:
                target=out/(str(rel)+'.gz');target.parent.mkdir(parents=True,exist_ok=True)
                with (p/name).open('rb') as source,gzip.open(target,'wb') as compressed:shutil.copyfileobj(source,compressed)
            else:copy(p/name,rel)
    for p in sorted((ROOT/'outputs/g2c-report').iterdir()):
        if p.is_file():copy(p,Path('charts')/p.name)
    for p in (ROOT/'data/g2c').glob('*.json'):copy(p,Path('sources')/p.name)
    for name in ('g2c-elmer.log','g2c-contact-fine.log','g2c-contact-refine.log','g2c-contact-reverify.log','g2c-stack.log','g2c-low-temperature.log','pytest-g2c-material-checkpoint.log','pytest-g2c-source-focused.log','pytest-g2c-final.log','cli-g2c.log','geometry-g2c.log'):
        copy(ROOT/'logs'/name,Path('provenance')/name)
    if reports['contact'].get('initial_mesh_passive_cases'):
        for label,case in reports['contact']['initial_mesh_passive_cases'].items():
            directory=local(case['case_path']);relative=Path('provenance/development-attempts/contact-initial-passive')/label
            write(relative/'metrics.json',case)
            write(relative/'acceptance.json',{'accepted':False,'reason':'Initial mesh failed absolute zero-current cut gate; replaced by genuine finer execution.'})
            for name in ('case.sif','case.json','solver.log','solver-status.json'):copy(directory/name,relative/name)
    # Failed/development attempts stay distinctly unaccepted; their observed
    # solver status is preserved, including zero exit but failed nonlinear gates.
    attempts=['fem-g2c-rejected-300K','fem-g2c-rod-bc-attempt','fem-g2c-bath-refinement-attempt','fem-g2c-mesh08-attempt','fem-g2c-contact','fem-g2c-contact-quality-attempt','fem-g2c-contact-netgen-attempt','fem-g2c-contact-005-attempt','fem-g2c-contact-hxt006-attempt','fem-g2c-contact-development-stopped','fem-g2c-stage-development']
    for attempt in attempts:
        p=ROOT/'outputs'/attempt
        if not p.exists():continue
        write(f'provenance/development-attempts/{attempt}/status.json',{'accepted':False,'reason':'Development/failed gate; see original logs/status and final report. No failed execution is counted among accepted solves.'})
        case_names={f.parent.name for f in p.glob('*/solver-status.json')}
        for name in sorted(case_names):
            for f in ('case.sif','case.json','solver.log','solver-status.json'):
                if (p/name/f).exists():copy(p/name/f,f'provenance/development-attempts/{attempt}/{name}/{f}')
        if (p/'summary.json').exists():
            old=json.loads((p/'summary.json').read_text());write(f'provenance/development-attempts/{attempt}/gates.json',old.get('verification',old.get('checks',{})))
    for p in [*(ROOT/'logs').glob('g2c-*attempt.log'),*(ROOT/'logs').glob('g2c-*stopped.log')]:copy(p,Path('provenance/development-attempts')/p.name)
    if (ROOT/'logs/g2c-rejected-300K.log').exists():copy(ROOT/'logs/g2c-rejected-300K.log','provenance/development-attempts/g2c-rejected-300K.log')
    rejected=ROOT/'outputs/g2c-axis-error-inputs'
    if rejected.exists():
        write('provenance/rejected-axis-extraction.json',{'accepted':False,'reason':'Prepublication N Seebeck negative-axis origin error. All affected source-dependent PDEs were rerun using corrected v1r1/v2r1. Constant contact fields independently reverified.',
            'quarantined_input_sha256':{p.name:digest(p) for p in rejected.glob('*.json')},'raw_affected_runs':'ignored outputs/*wrong-N-axis; never accepted artifacts'})
    with (out/'resource_usage.csv').open('w',newline='') as f:
        cols=['group','case','nodes','dofs','exit_code','elapsed_s','cpu_s','peak_rss_kib','nonlinear_iterations','nonlinear_last_relative_change']
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(resources)
    # Portable scalar/cut tables retain actual results, distinct from source data.
    scalar_columns=['group','case','current_a','load_w','hot_k','cold_mean_k','cold_min_k','cold_max_k','voltage_v','electrical_input_w','energy_relative_residual','power_work_relative_residual','bath_gradient_energy_relative_residual','max_cut_relative_error','contact_joule_w','extra_contact_joule_w']
    with (out/'operating_points.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=scalar_columns,extrasaction='ignore');w.writeheader()
        for group,r in reports.items():
            for label,c in r['cases'].items():w.writerow({'group':group,'case':label,**c})
    with (out/'component_cuts.csv').open('w',newline='') as f:
        cols=['group','case','component','kind','current_a','relative_error','absolute_error_a','area_m2','expected_area_m2'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for group,r in reports.items():
            for label,c in r['cases'].items():
                for name,v in c['cuts'].items():w.writerow({'group':group,'case':label,'component':name,**v})
    source=json.loads((ROOT/'data/g2c/oem2019_curves_v1.json').read_text())
    with (out/'sources/oem2019_readings.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(source['points'][0]));w.writeheader();w.writerows(source['points'])
    for filename,version in (('zhang2025_he_v1.json','v1'),('zhang2025_he_40_300_v2.json','v2')):
        source=json.loads((ROOT/'data/g2c'/filename).read_text())
        with (out/f'sources/material_readings_{version}.csv').open('w',newline='') as f:
            cols=['profile_id','polarity','sample_id','property','unit','temperature_k','value_si','value_reading_bound_si','temperature_reading_bound_k','pdf_page_index','figure_panel'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
            for polarity,sample in source['specimens'].items():
                for prop,curve in sample['curves'].items():
                    for point in curve['points']:w.writerow({**{k:point[k] for k in ('temperature_k','value_si','value_reading_bound_si','temperature_reading_bound_k')},'profile_id':source['id'],'polarity':polarity,'sample_id':sample['sample_id'],'property':prop,'unit':curve['unit'],'pdf_page_index':curve['pdf_page_index'],'figure_panel':curve['figure_panel']})
    write('provenance/compiled-libraries-sha256.json',runtime)
    image=json.loads(subprocess.check_output(['docker','image','inspect','tecooledmct-fem:26.2.1'],text=True))[0]
    write('provenance/image.json',image)
    copy(ROOT/'fem/results/g1_20261028/provenance/versions.txt','provenance/pinned-versions.txt')
    write('checksums.json',{'baseline_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_sha256':sources,
        'artifacts_sha256':{str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='checksums.json'},
        'unique_successful_solver_executions':len(resources),'device_validation_passed':False,
        'verification_test_source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'tests').glob('test_*.py'))},
        'development_test_versions_at_execution_start':{n:sorted(v) for n,v in execution_test_versions.items()},
        'test_dependency_note':'A coarse source-smoke mesh was refined to meet the same 0.5% current gate after corrected source data. Full tests were rerun; completed production PDE code/data/SIF/VTU remained unchanged. Development test hashes are context, not material/solver inputs.',
        'note':'Accepted real PDE executions only. Published sample curves and OEM readings are separate from actual fields. Generated library binaries remain untracked; source/compiler logs and binary hashes retained.'})
    print('Archived accepted actual G2c evidence:',len(resources),'unique PDE executions')

if __name__=='__main__':main()
