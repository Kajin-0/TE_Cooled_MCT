#!/usr/bin/env python3
"""Publish checked cold-ROI evidence without changing any historical acceptance gate."""
import argparse,gzip,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tecooledmct.geometry_rebaseline import sha,write
from tecooledmct.cold_convergence_summary import RAW,CONFIG,read
from tecooledmct.full_presolder_guard import preserve

DEST=ROOT/'fem/results/cold_interface_convergence_20261030'
SOURCES=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'tecooledmct').glob('cold_*.py'))]+[
    'data/cold_convergence/plan.json','data/cold_convergence/projected_initialization_plan.json',
    'tests/test_cold_interfaces.py','fem/archive_cold_convergence.py',
    'COLD_INTERFACE_MESH_CONVERGENCE_WORK_ORDER.md','docs/CORRECTED_THERMAL_INTERFACE_MESH_CONVERGENCE_RESULT.md',
    'docs/COLD_INTERFACE_CONVERGENCE_REPRODUCIBILITY.md']


def guard():
    subprocess.run([sys.executable,str(ROOT/'fem/archive_corrected_thermal.py'),'--verify'],check=True)
    return {'historical':preserve(),'corrected_thermal_ledger_sha256':sha(ROOT/'fem/results/corrected_coupled_thermal_20261030/checksums.json')}


def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)


def compress(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with src.open('rb') as source,dst.open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as output:
        shutil.copyfileobj(source,output)


def hash_sources(hashes,snapshot=None):
    for name,digest in hashes.items():
        if sha(ROOT/name)!=digest:raise ValueError('Source changed: '+name)
        if snapshot and sha(snapshot/(Path(name).name+'.source'))!=digest:raise ValueError('Wrong execution source snapshot')


def copy_small_tree(source,target):
    for p in source.rglob('*'):
        if p.is_file() and not p.is_symlink() and p.suffix.lower() in ('.json','.sif','.f90','.log','.source'):
            copy(p,target/p.relative_to(source))


def failed_source_proof(source,target):
    names=SOURCES+['tecooledmct/corrected_thermal.py','tecooledmct/corrected_thermal_post.py']
    known={Path(n).name:ROOT/n for n in names};hashes={}
    for p in (source/'source_snapshot').glob('*.source'):
        name=p.name.removesuffix('.source')
        if name not in known or sha(p)!=sha(known[name]):raise ValueError('Failed execution source snapshot differs')
        hashes[str(known[name].relative_to(ROOT))]=sha(p)
    if not hashes:raise ValueError('Failed actual execution has no source snapshot')
    write(target/'failed_source_proof.json',{'source_sha256':hashes,'sif_sha256':sha(source/'case.sif'),
        'status_sha256':sha(source/'solver-status.json'),'scope':'retrospective audit of preserved failed-execution snapshots; no final field claim'})


def copy_mesh(mesh,target):
    proof=read(mesh/'audit.json');hash_sources(proof['source_sha256'])
    if not all(proof[k] for k in ('passed','geometrically_identical','only_cold_sizing_changed')) or not read(mesh/'elmer_mapping.json')['passed']:
        raise ValueError('Geometry/contact/conformal mapping failed')
    if sha(mesh/'mesh.npz')!=proof['mesh_sha256'] or sha(mesh/'manifest.json')!=sha(CONFIG[0][1]/'manifest.json'):
        raise ValueError('Mesh changed or different physical registry')
    for p in mesh.iterdir():
        if p.is_file() and p.suffix in ('.json','.npz','.step','.log'):copy(p,target/p.name)
    compress(mesh/'connected.msh',target/'connected.msh.gz')
    for p in (mesh/'elmer').iterdir():
        if p.is_file() and p.name.startswith('mesh.'):compress(p,target/'elmer'/(p.name+'.gz'))


def verify():
    ledger=read(DEST/'checksums.json')
    for key,base in [('source_sha256',ROOT),('artifact_sha256',DEST)]:
        for name,digest in ledger[key].items():
            if sha(base/name)!=digest:raise ValueError('Changed cold-convergence evidence: '+name)
    if guard()!=ledger['preserved']:raise ValueError('Prior evidence changed')
    q=read(DEST/'qualification.json');s=read(DEST/'study.json')
    if q['full_device_qualification'] or q['OEM_validated'] or q['device_GCI_qualified']:raise ValueError('Unfounded qualification')
    if q['actual_coupled_meshes']!=len(s['cases']) or q['actual_coupled_meshes'] not in (2,3) or not q['benchmark_finest_qualified']:
        raise ValueError('Wrong scoped mesh-study count')
    if any(r['primary_checks_passed']!=all(r['primary_checks'].values()) for r in s['cases']):raise ValueError('Gate label inconsistent')
    if q['refined_Cu_ON']!='NOT RUN':raise ValueError('Unsupported matched ON claim')
    print('Verified6 independent HeatSolver fields and',q['actual_coupled_meshes'],'corrected coupled mesh fields; failures and prior evidence preserved')


def publish():
    import numpy as np
    import meshio
    from scipy.spatial import cKDTree
    if DEST.exists():raise ValueError('Immutable archive exists; use --verify')
    preserved=guard();s=read(RAW/'study.json');bench=read(RAW/'benchmark/summary.json')
    if not bench['qualified'] or len(bench['cases'])!=6:raise ValueError('Independent benchmark incomplete')
    if '121 passed' not in (ROOT/'outputs/cold-convergence-all-tests-final.log').read_text():raise ValueError('Full opt-in regressions incomplete')
    for n in ('cli','pellet'):
        if 'Traceback' in (ROOT/f'outputs/cold-convergence-{n}.log').read_text():raise ValueError('Quick demo failed')
    if s['source_sha256']!=sha(ROOT/'tecooledmct/cold_convergence_summary.py') or s['plan_sha256']!=sha(ROOT/'data/cold_convergence/plan.json'):
        raise ValueError('Summary/registered plan changed')
    stage=ROOT/'outputs'/('cold-convergence-publication-'+str(time.time_ns()));stage.mkdir()
    for label,mesh,case,diag,stat in CONFIG:
        if label not in [v['level'] for v in s['cases']]:
            status=read(case/'solver-status.json')
            if not status['exit_code'] or (case/'execution.json').exists():raise ValueError('Inconsistent failed refined run')
            copy_mesh(mesh,stage/'device'/(label+'_FAILED')/'mesh');copy_small_tree(case,stage/'device'/(label+'_FAILED')/'case')
            failed_source_proof(case,stage/'device'/(label+'_FAILED')/'case')
            if (case/'projected_initial_guess.result').exists():compress(case/'projected_initial_guess.result',stage/'device'/(label+'_FAILED')/'case/projected_initial_guess.result.gz')
            continue
        m=read(case/'metrics.json');e=read(case/'execution.json');a=read(diag/'diagnosis.json');status=read(case/'solver-status.json')
        hash_sources(e['source_sha256'],case/'source_snapshot')
        if status!=e['solver_status'] or status['exit_code'] or status['nonlinear_last_relative_change']>=1e-9:raise ValueError('Invalid coupled solve')
        if sha(mesh/'mesh.npz')!=e['mesh_sha256'] or e['mesh_sha256']!=a['mesh_sha256']:raise ValueError('Changed solved mesh')
        if sha(mesh/'manifest.json')!=sha(CONFIG[0][1]/'manifest.json'):raise ValueError('Source geometry registry differs across meshes')
        if a['source_sha256']!=sha(ROOT/'tecooledmct/cold_interface_audit.py'):raise ValueError('Changed independent extraction')
        if e['vtu_sha256']!=a['field_sha256'] or sha(case/e['field_source'])!=e['vtu_sha256'] or sha(case/'case.sif')!=e['sif_sha256']:
            raise ValueError('Changed actual input/field')
        if not all(m['checks'][k] for k in m['checks'] if k!='raw_bath_1percent') or len(m['cuts'])!=177:raise ValueError('Current/energy verification failed')
        if m['passed']!=all(m['checks'].values()):raise ValueError('Primary gate failure hidden')
        if m['cu_leads_on'] or m['au_bonds_on'] or m['current_a']!=.1 or m['deposited_power_w']!=.002:raise ValueError('Unmatched physics')
        d=np.load(mesh/'mesh.npz');field=meshio.read(case/e['field_source']);dist,ix=cKDTree(field.points).query(d['points'])
        if dist.max()>1e-12 or len(np.unique(ix))!=len(d['points']) or len(field.get_cells_type('tetra'))!=len(d['cells']):raise ValueError('Actual field/mesh differs')
        if not np.isfinite(field.point_data['temperature']).all() or not np.isfinite(field.point_data['potential']).all():raise ValueError('Nonfinite solution')
        for n in (diag/'diagnosis.json',stat/'cold_mesh_metrics.json'):
            if sha(n)!=s['reference_sha256'][label][str(n.relative_to(ROOT))]:raise ValueError('Stale summary')
        target=stage/'device'/label
        copy(stat/'cold_mesh_metrics.json',target/'cold_mesh_metrics.json')
        for p in diag.iterdir():copy(p,target/'independent_faces'/p.name)
        if label=='original':
            write(target/'protected_reference.json',{'archive':'fem/results/corrected_coupled_thermal_20261030/cases/cu_off',
                  'mesh_archive':'fem/results/geometry_complete_checkpoint_20261030','execution_sha256':sha(case/'execution.json'),
                  'vtu_sha256':e['vtu_sha256'],'mesh_sha256':e['mesh_sha256']})
            continue
        copy_mesh(mesh,target/'mesh')
        copy_small_tree(case,target/'case')
        hashes={}
        names=[e['field_source'],'derived.vtu','solution.result']
        if (case/'projected_initial_guess.result').exists():names.append('projected_initial_guess.result')
        for name in names:
            compress(case/name,target/'case'/(Path(name).name+'.gz'));hashes[Path(name).name]=sha(case/name)
        write(target/'case/uncompressed_sha256.json',hashes)
    # Retain the32-bit factorization failure and the rejected path-sensitive setup.
    fail=RAW/'cu_off20';status=read(fail/'solver-status.json')
    if not status['exit_code'] or status['nonlinear_iterations'] or (fail/'execution.json').exists():raise ValueError('Failed attempt falsely solved')
    if 'Error occurred in umf4num' not in (fail/'solver.log').read_text():raise ValueError('Missing backend failure evidence')
    copy_small_tree(fail,stage/'attempts/cu_off20_32bit_FAILED')
    failed_source_proof(fail,stage/'attempts/cu_off20_32bit_FAILED')
    copy_small_tree(RAW/'cu_off20_big',stage/'attempts/big_index_setup_rejected_NO_SOLVE')
    retry=RAW/'cu_off20_big_retry';rtext=(retry/'case.sif').read_text();ftext=(fail/'case.sif').read_text()
    if rtext.replace('"big umfpack"','UMFPACK').replace(str(retry),'{CASE}')!=ftext.replace(str(fail),'{CASE}'):
        raise ValueError('64-bit retry changed more than index mode/path')
    secondary_completed=0
    for name in ('cu_off20_big_retry','same_mesh_restart_check'):
        source=RAW/name;target=stage/'attempts'/name;copy_small_tree(source,target)
        status=read(source/'solver-status.json')
        if (source/'execution.json').exists():
            e=read(source/'execution.json');hash_sources(e['source_sha256'],source/'source_snapshot')
            if status['exit_code'] or status!=e['solver_status'] or sha(source/e['field_source'])!=e['vtu_sha256']:
                raise ValueError('Secondary coupled execution invalid')
            secondary_completed+=1;hashes={}
            for filename in (e['field_source'],'derived.vtu','solution.result','projected_initial_guess.result'):
                if (source/filename).exists():
                    compress(source/filename,target/(Path(filename).name+'.gz'));hashes[Path(filename).name]=sha(source/filename)
            write(target/'uncompressed_sha256.json',hashes)
        elif status['exit_code']==0:raise ValueError('Incomplete secondary execution')
        else:failed_source_proof(source,target)
    check=read(RAW/'same_mesh_restart_check/initialization_check.json')
    istatus=read(RAW/'same_mesh_restart_check/solver-status.json');initialization=read(RAW/'same_mesh_restart_check/initialization.json')
    if not check['passed'] or istatus['nonlinear_iterations']!=2 or initialization['maximum_nearest_distance_m']>1e-12:
        raise ValueError('Same-mesh restart format not independently verified')
    for kind in ('flux','source'):
        for level in range(3):
            source=RAW/'benchmark'/kind/str(level);v=read(source/'verification.json');hash_sources(v['source_sha256'])
            if v['solver_status']['exit_code'] or 'ALL DONE' not in (source/'solver.log').read_text():raise ValueError('No genuine HeatSolver execution')
            for filename,key in [('mesh.npz','mesh_sha256'),('case.sif','sif_sha256'),(v['field_source'],'vtu_sha256')]:
                if sha(source/filename)!=v[key]:raise ValueError('Changed analytic benchmark evidence')
            target=stage/'benchmark'/kind/str(level);copy_small_tree(source,target)
            for p in source.glob('*.npz'):copy(p,target/p.name)
            compress(source/'case.msh',target/'case.msh.gz');compress(source/v['field_source'],target/(Path(v['field_source']).name+'.gz'))
            write(target/'uncompressed_sha256.json',{Path(v['field_source']).name:v['vtu_sha256']})
    copy(RAW/'benchmark/summary.json',stage/'benchmark/summary.json');copy(RAW/'study.json',stage/'study.json')
    fig=RAW/'figures';prov=read(fig/'provenance.json')
    if prov['source_sha256']!=sha(ROOT/'tecooledmct/cold_convergence_figures.py') or prov['study_sha256']!=sha(RAW/'study.json'):
        raise ValueError('Stale actual-field figures')
    for label in prov['cases']:
        if prov['cases'][label]['raw_field_sha256']!=read(next(row[2] for row in CONFIG if row[0]==label)/'execution.json')['vtu_sha256']:
            raise ValueError('Figure not from actual field')
    for p in fig.iterdir():copy(p,stage/'figures'/p.name)
    for p in (ROOT/'outputs').glob('cold-convergence-*.log'):copy(p,stage/'verification'/p.name)
    copy(ROOT/'outputs/cold-convergence-runtime-image.txt',stage/'verification/runtime_image.txt')
    write(stage/'qualification.json',{'actual_coupled_meshes':len(s['cases']),'actual_new_coupled_solutions':len(s['cases'])-1+secondary_completed,'actual_new_HeatSolver_solutions':6,
          'benchmark_finest_qualified':True,'device_GCI_qualified':False,'full_device_qualification':False,'OEM_validated':False,
          'cold_interface_5percent_passes':[r['cold_interfaces_passed'] for r in s['cases']],
          'raw_bath_1percent_passes':[r['primary_checks']['raw_bath_1percent'] for r in s['cases']],
          'all177_current_halfpercent_passed':True,'refined_Cu_ON':'NOT RUN','refined_Cu_ON_reason':s['Cu_ON_refined'],
          'historical_bath_failures':'UNCHANGED FAILED; no recovered flux waiver','old_report':'UNCHANGED15 pages',
          'scope':'solid-only synthetic reference, no enclosure/gas/radiation or carrier physics',
          'image_id':(ROOT/'outputs/cold-convergence-runtime-image.txt').read_text().strip(),
          'retained_attempts':{'32bit':'UMFPACK factorization FAILED','64bit_setup':'rejected before solve',
                              '64bit_fresh_start_status':read(RAW/'cu_off20_big_retry/solver-status.json'),
                              'same_mesh_projected_restart':check,'fine_projected_start_failed_levels':s['failed_coupled_levels']}})
    write(stage/'checksums.json',{'source_sha256':{n:sha(ROOT/n) for n in SOURCES},
          'artifact_sha256':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'preserved':preserved})
    stage.rename(DEST);verify()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args();verify() if a.verify else publish()
