#!/usr/bin/env python3
"""Audited solid-only coupled checkpoint; retain local failures and pending mesh gate."""
import argparse,csv,gzip,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tecooledmct.geometry_rebaseline import sha,write
from tecooledmct.full_presolder_guard import preserve

DEST=ROOT/'fem/results/corrected_coupled_thermal_20261030'
RAW=ROOT/'outputs/corrected-thermal';MESH=ROOT/'outputs/geometry-complete-v4'
NAMES=('passive','cu_off','cu_on','cu_on_sigma_low')
SOURCES=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'tecooledmct').glob('corrected_thermal*.py'))]+[
    'tests/test_corrected_thermal.py','data/corrected_thermal/material_assumptions.json',
    'docs/GEOMETRY_CORRECTED_COUPLED_THERMAL_RESULT.md','docs/CORRECTED_COUPLED_THERMAL_REPRODUCIBILITY.md',
    'CORRECTED_GEOMETRY_COUPLED_THERMAL_WORK_ORDER.md','fem/archive_corrected_thermal.py']


def read(path):return json.loads(Path(path).read_text())


def guard():
    subprocess.run([sys.executable,str(ROOT/'fem/archive_geometry_complete.py'),'--verify'],check=True)
    return preserve()


def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)


def compress(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with src.open('rb') as inp,dst.open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as out:shutil.copyfileobj(inp,out)


def verify():
    ledger=read(DEST/'checksums.json')
    for group,parent in [('source_sha256',ROOT),('artifact_sha256',DEST)]:
        for name,digest in ledger[group].items():
            if sha(parent/name)!=digest:raise ValueError('Changed coupled thermal evidence: '+name)
    if guard()!=ledger['preserved']:raise ValueError('Historical evidence changed')
    q=read(DEST/'qualification.json')
    if q['full_thermal_qualification'] or q['spatial_convergence_passed'] or q['local_die_interface_gate_passed'] or q['OEM_validated']:
        raise ValueError('False qualification claim')
    print('Verified4 actual corrected coupled executions; local interface FAIL and spatial NOT RUN retained')


def publish():
    import numpy as np
    import meshio
    from tecooledmct.corrected_thermal import endpoint_weights,link_powers
    if DEST.exists():raise ValueError('Immutable archive exists; use --verify')
    preserved=guard();geo=ROOT/'fem/results/geometry_complete_checkpoint_20261030';geoh=read(geo/'checksums.json')['artifact_sha256']
    for name in ('mesh.npz','manifest.json','wire_routes.json'):
        if sha(MESH/name)!=geoh[name]:raise ValueError('Original corrected geometry input changed')
    if '117 passed' not in (ROOT/'outputs/corrected-thermal-all-tests.log').read_text():raise ValueError('Full opt-in tests incomplete')
    for name in ('corrected-thermal-cli.log','corrected-thermal-pellet.log'):
        if 'Traceback' in (ROOT/'outputs'/name).read_text():raise ValueError('CLI/demo failed')
    stage=ROOT/'outputs'/('corrected-thermal-publication-'+str(time.time_ns()));stage.mkdir();results={};executions={}
    endpoint=endpoint_weights(MESH);d=np.load(MESH/'mesh.npz');p=d['points'];c=d['cells'];budgets=[];summary=[]
    from scipy.spatial import cKDTree
    for name in NAMES:
        case=RAW/name;r=read(case/'metrics.json');e=read(case/'execution.json');meta=read(case/'case.json');status=read(case/'solver-status.json')
        for n,h in e['source_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('PDE/post source changed during/between executions')
            if sha(case/'source_snapshot'/(Path(n).name+'.source'))!=h:raise ValueError('Execution snapshot differs')
        if e['mesh_sha256']!=geoh['mesh.npz'] or e['manifest_sha256']!=geoh['manifest.json']:raise ValueError('Wrong geometry')
        for filename,key in [('case.sif','sif_sha256'),(e['field_source'],'vtu_sha256')]:
            if sha(case/filename)!=e[key] or r[key]!=e[key]:raise ValueError('Changed actual SIF/field')
        if status!=e['solver_status'] or status['exit_code']!=0 or status['timed_out'] or status['nonlinear_last_relative_change']>=1e-9:
            raise ValueError('Coupled convergence not verified')
        if not r['passed'] or not all(r['checks'].values()) or len(r['cuts'])!=177:raise ValueError('Primary per-case gate failed; new review/status needed')
        if not np.isclose(meta['mct_volume_m3'],2e-10,rtol=1e-10):raise ValueError('Wrong actual detector volume')
        if read(case/'endpoint_weights.json')!=endpoint:raise ValueError('Changed endpoint nodes/areas/weights')
        if read(case/'library/compile-status.json')['exit_code']!=0:raise ValueError('Callbacks not compiled')
        text=(case/'case.sif').read_text()
        if 'ThermoElectricSolver' not in text or 'G3b' in text:raise ValueError('Wrong coupled/nonlocal procedure')
        # Check the actual field again; do not trust a success label alone.
        field=meshio.read(case/e['field_source']);dist,ix=cKDTree(field.points).query(p)
        if dist.max()>1e-12 or len(field.points)!=len(p) or len(field.get_cells_type('tetra'))!=len(c):raise ValueError('Actual field geometry differs')
        for key in ('temperature','potential'):
            if not np.isfinite(field.point_data[key]).all():raise ValueError('Nonfinite actual field')
        power,links,parts=link_powers(MESH,field.point_data['temperature'].ravel()[ix],meta,endpoint)
        if abs(parts['wire_conduction'].sum())>1e-12 or abs(parts['wire_joule'].sum()-r['wire_Joule_w'])>1e-12:raise ValueError('Wire source conservation failed')
        if isinstance(meta['initial_state'],dict):
            parent=Path(meta['initial_state']['case']);parent=ROOT/str(parent).removeprefix('/work/') if str(parent).startswith('/work/') else parent
            digest=meta['initial_state']['result_sha256']
            if sha(parent/'solution.result')!=digest or sha(case/'initial.result')!=digest:raise ValueError('Changed actual initial state')
            if read(parent/'execution.json')['mesh_sha256']!=geoh['mesh.npz']:raise ValueError('Cross-mesh initial state forbidden')
        if name in ('cu_off','cu_on'):
            face=read(case/'raw_interface_audit.json')
            if face['field_sha256']!=e['vtu_sha256'] or face['source_sha256']!=sha(ROOT/'tecooledmct/corrected_thermal_interfaces.py'):
                raise ValueError('Changed independent face audit')
            if face['all_extra_interface_checks_passed']:raise ValueError('Expected preserved local diagnostic failures missing')
        target=stage/'cases'/name
        for path in case.rglob('*'):
            if path.is_file() and not path.is_symlink() and path.suffix.lower() in ('.json','.sif','.f90','.log','.source'):
                copy(path,target/path.relative_to(case))
        fields={}
        for filename in (e['field_source'],'derived.vtu'):
            compress(case/filename,target/(Path(filename).name+'.gz'));fields[Path(filename).name]=sha(case/filename)
        write(target/'uncompressed_sha256.json',fields)
        results[name]=r;executions[name]=e
        summary.append({'case':name,**{k:r[k] for k in ('die_mean_k','cold_ceramic_k','hot_ceramic_k','voltage_v','hot_out_reaction_w',
            'hot_out_raw_gradient_w','direct_bath_relative_error','worst_raw_cut_relative_error','passed')}})
        for row in r['stage_control_volumes']:budgets.append({'case':name,'band':row['band'],'hot_out_w':row['hot_out_w'],
            'cold_out_downward_w':row['cold_out_downward_w'],'electrical_work_w':row['electrical_work_w'],'energy_error_w':row['energy_error_w'],
            **{k:v for k,v in row['sources_w'].items()}})
    # Matched comparison: Au and all solid geometry/transport/load settings fixed.
    a=results['cu_off'];b=results['cu_on']
    for key in ('current_a','deposited_power_w','package_sigma_s_m','mct_volume_m3','au_bonds_on'):
        if a[key]!=b[key]:raise ValueError('OFF/ON are not matched')
    if a['au_bonds_on'] or b['au_bonds_on'] or a['cu_leads_on'] or not b['cu_leads_on']:raise ValueError('Wrong wire control')
    figs=RAW/'figures_v2';provenance=read(figs/'provenance.json')
    if provenance['source_sha256']!=sha(ROOT/'tecooledmct/corrected_thermal_figures.py'):raise ValueError('Changed figure source')
    for name in ('cu_off','cu_on'):
        if provenance['cases'][name]['raw_field_sha256']!=executions[name]['vtu_sha256']:raise ValueError('Figure not from actual final field')
    for path in figs.iterdir():copy(path,stage/'figures'/path.name)
    for name in ('corrected-thermal-passive.log','corrected-thermal-cu-off.log','corrected-thermal-cu-on.log','corrected-thermal-sigma-low.log',
                 'corrected-thermal-unit.log','corrected-thermal-all-tests.log','corrected-thermal-cli.log','corrected-thermal-pellet.log',
                 'corrected-thermal-off-interface.log','corrected-thermal-off-interface-v2.log','corrected-thermal-on-interface.log',
                 'corrected-thermal-figures.log','corrected-thermal-figures-v2.log','corrected-thermal-reencode.log','corrected-thermal-baseline-guard.log',
                 'corrected-thermal-runtime-image.txt'):
        copy(ROOT/'outputs'/name,stage/'verification'/name)
    copy(RAW/'reencoded_mesh_check/mapping_audit.json',stage/'verification/reencoded_mapping_audit.json')
    for name,rows in (('case_summary.csv',summary),('stage_heat_budgets.csv',budgets)):
        with (stage/name).open('w') as stream:w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write(stage/'qualification.json',{'status':'verified actual coupled executions; exploratory spatial/local-flux qualification',
        'actual_executions':list(NAMES),'primary_per_case_checks_passed':True,'local_die_interface_gate_passed':False,
        'full_thermal_qualification':False,'spatial_convergence_passed':False,'OEM_validated':False,
        'Au_on_test':'NOT RUN','new_enclosure_radiation_gas':'NOT RUN; none imported/reused',
        'historical_fine_raw_bath_gate':'UNCHANGED FAILED1.65587/1.51412/1.58383%; no recovered substitution',
        'mesh_reference':{'path':str(geo.relative_to(ROOT)),'mesh_sha256':geoh['mesh.npz']},
        'matched_ON_minus_OFF_die_K':b['die_mean_k']-a['die_mean_k'],
        'difference_scope':'small output difference, not resolved cooling benefit; local mesh diagnostics fail',
        'case_summary':summary,'image_id':(ROOT/'outputs/corrected-thermal-runtime-image.txt').read_text().strip()})
    ledger={'source_sha256':{n:sha(ROOT/n) for n in SOURCES},'artifact_sha256':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'preserved':preserved}
    write(stage/'checksums.json',ledger);stage.rename(DEST);verify()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args();verify() if args.verify else publish()
