#!/usr/bin/env python3
"""Immutable evidence for completed Cold20, verified numerics and retained failures."""
import argparse,gzip,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tecooledmct.geometry_rebaseline import sha,write
from tecooledmct.full_presolder_guard import preserve
from tecooledmct.cold20_analysis import RAW,read,accepted_nonraw

DEST=ROOT/'fem/results/cold20_completion_20261030'
SOURCES=[str(p.relative_to(ROOT)) for folder,pattern in [('tecooledmct','cold20_*.py'),('data/cold20','*.json'),('fem/cold20','*.c')] for p in sorted((ROOT/folder).glob(pattern))]+[
    'fem/archive_cold20.py','fem/restore_cold20.py','tests/test_cold20.py','COLD20_SOLVER_COMPLETION_WORK_ORDER.md',
    'docs/COLD20_SOLVER_COMPLETION_AND_BATH_DIAGNOSIS.md','docs/COLD20_REPRODUCIBILITY.md']


def guard():
    subprocess.run([sys.executable,str(ROOT/'fem/archive_cold_convergence.py'),'--verify'],check=True)
    return {'history':preserve(),'prior_cold_ledger_sha256':sha(ROOT/'fem/results/cold_interface_convergence_20261030/checksums.json')}


def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)


def compress(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with src.open('rb') as inp,dst.open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as out:shutil.copyfileobj(inp,out)


def small_tree(src,dst):
    for p in src.rglob('*'):
        if p.is_file() and not p.is_symlink() and p.suffix.lower() in ('.json','.sif','.f90','.c','.log','.source'):
            copy(p,dst/p.relative_to(src))
        elif p.is_file() and not p.is_symlink() and p.suffix=='.so':compress(p,dst/(str(p.relative_to(src))+'.gz'))


def source_proof(hashes,where):
    for name,digest in hashes.items():
        if sha(ROOT/name)!=digest or sha(where/(Path(name).name+'.source'))!=digest:raise ValueError('Changed execution source/snapshot: '+name)


def verify():
    ledger=read(DEST/'checksums.json')
    for key,base in [('source_sha256',ROOT),('artifact_sha256',DEST)]:
        for name,digest in ledger[key].items():
            if sha(base/name)!=digest:raise ValueError('Changed Cold20 evidence: '+name)
    if guard()!=ledger['preserved']:raise ValueError('Historical evidence changed')
    q=read(DEST/'qualification.json')
    if not q['Cold20_actual_completed_and_nonraw_verified'] or q['full_device_qualification'] or q['OEM_validated'] or q['device_GCI_qualified']:
        raise ValueError('Wrong qualification scope')
    print('Verified actual completed Cold20, immutable prior evidence, numerical benchmarks and explicit failed raw gates')


def publish():
    import numpy as np,meshio
    from scipy.spatial import cKDTree
    if DEST.exists():raise ValueError('Archive immutable; use --verify')
    preserved=guard();accepted_nonraw(RAW/'loaded20_direct_P1')
    if '125 passed' not in (ROOT/'outputs/cold20-all-tests-final.log').read_text():raise ValueError('Full opt-in125+ regressions incomplete')
    for name in ('cli','pellet'):
        if 'Traceback' in (ROOT/f'outputs/cold20-{name}.log').read_text():raise ValueError('Existing CLI/demo failed')
    registry=read(RAW/'configuration_registry.json');study=read(RAW/'study.json')
    if len(study['cases'])!=3 or study['actual_completed_coupled_meshes']!=3:raise ValueError('No three actual completed mesh levels')
    if registry['source_sha256']!=sha(ROOT/'tecooledmct/cold20_analysis.py'):raise ValueError('Comparison registry source changed')
    stage=ROOT/'outputs'/('cold20-publication-'+str(time.time_ns()));stage.mkdir();cases=[]
    meshes={sha(ROOT/'outputs/cold-convergence/mesh30/mesh.npz'):ROOT/'outputs/cold-convergence/mesh30',
            sha(ROOT/'outputs/cold-convergence/mesh20/mesh.npz'):ROOT/'outputs/cold-convergence/mesh20',
            sha(RAW/'bath_mesh/mesh.npz'):RAW/'bath_mesh'}
    primary={Path(registry['primary_case']).name,'loaded20_direct_P1','bath_coupled'}
    for source in sorted(RAW.iterdir()):
        if not source.is_dir() or not (source/'case.sif').exists():continue
        target=stage/'cases'/source.name;small_tree(source,target);status=read(source/'solver-status.json') if (source/'solver-status.json').exists() else None
        row={'case':source.name,'solver_status':status,'genuine_solver_executed':status is not None,'completed_nonlinear':False,'nonraw_physics_passed':False}
        if (source/'backend_registration.json').exists():
            backend=read(source/'backend_registration.json');source_proof(backend['source_sha256'],source/'backend_source_snapshot')
            if 'library_sha256' in backend:
                libs=list((RAW/(source.name+'_library')).glob('*.so'))
                if len(libs)!=1 or sha(libs[0])!=backend['library_sha256']:raise ValueError('Executed numerical wrapper binary changed')
        if (source/'pre_execution.json').exists():source_proof(read(source/'pre_execution.json')['source_sha256'],source/'source_snapshot')
        if (source/'execution.json').exists():
            e=read(source/'execution.json');m=read(source/'metrics.json');source_proof(e['source_sha256'],source/'source_snapshot')
            if e['solver_status']!=status or status['exit_code'] or status['nonlinear_last_relative_change']>=1e-9:raise ValueError('False solver completion')
            if sha(source/'case.sif')!=e['sif_sha256'] or sha(source/e['field_source'])!=e['vtu_sha256'] or e['mesh_sha256'] not in meshes:
                raise ValueError('Changed actual case SIF/field/mesh')
            mesh=meshes[e['mesh_sha256']];d=np.load(mesh/'mesh.npz');field=meshio.read(source/e['field_source']);distance,ix=cKDTree(field.points).query(d['points'])
            if distance.max()>1e-12 or len(np.unique(ix))!=len(d['points']) or len(field.get_cells_type('tetra'))!=len(d['cells']):raise ValueError('Actual solved field has wrong mesh')
            if any(not np.isfinite(field.point_data[k]).all() for k in ('temperature','potential')):raise ValueError('Nonfinite solved field')
            if len(m['cuts'])!=177 or m['passed']!=all(m['checks'].values()):raise ValueError('Wrong current counts/gate labels')
            nonraw=all(v for k,v in m['checks'].items() if k!='raw_bath_1percent')
            if source.name in primary and not nonraw:raise ValueError('Primary numerical case fails independent current/energy gates')
            row.update(completed_nonlinear=True,nonraw_physics_passed=nonraw,checks=m['checks'],die_mean_K=m['die_mean_k'],voltage_V=m['voltage_v'])
            names=[e['field_source'],'solution.result']
            if source.name in primary:names.append('derived.vtu')
            for guess in ('initial_guess.result','initial.result'):
                if (source/guess).exists():names.append(guess)
            hashes={}
            for filename in names:compress(source/filename,target/(Path(filename).name+'.gz'));hashes[Path(filename).name]=sha(source/filename)
            write(target/'uncompressed_sha256.json',hashes)
        else:
            # A failed trial never becomes a mesh-convergence or physical sample.
            for p in source.glob('*.vtu'):compress(p,target/'UNCONVERGED_FIELDS'/(p.name+'.gz'))
            if (source/'initial_guess.result').exists():compress(source/'initial_guess.result',target/'initial_guess.result.gz')
        cases.append(row)
    # Retain failed transfer and all successful interpolation data, separately
    # from genuine solved fields. Verify each declared source/body-aware map.
    for folder in sorted(RAW.glob('transfer_*')):
        small_tree(folder,stage/'initialization'/folder.name)
        for p in folder.glob('*.npz'):copy(p,stage/'initialization'/folder.name/p.name)
        if (folder/'initial_guess.result').exists():compress(folder/'initial_guess.result',stage/'initialization'/folder.name/'INITIAL_GUESS_ONLY.result.gz')
        if (folder/'transfer.json').exists():
            tr=read(folder/'transfer.json')
            for name,h in tr['source_sha256'].items():
                if sha(ROOT/name)!=h:raise ValueError('Transfer source changed')
            for name,key in [('map.npz','map_sha256'),('initial_values.npz','initial_values_sha256'),('initial_guess.result','initial_guess_sha256')]:
                if sha(folder/name)!=tr[key]:raise ValueError('Changed P1 transfer')
            mp=np.load(folder/'map.npz')
            if mp['weights'].min()<0 or abs(mp['weights'].sum(1)-1).max()>1e-12:raise ValueError('Nonconvex transfer weights')
    mesh=RAW/'bath_mesh';proof=read(mesh/'audit.json')
    if not proof['passed'] or not all(proof['cold_cells_byte_identical'].values()) or not read(mesh/'elmer_mapping.json')['passed']:
        raise ValueError('Independent bath/cold invariance proof failed')
    if sha(mesh/'mesh.npz')!=proof['mesh_sha256']:raise ValueError('Changed bath mesh')
    for p in mesh.iterdir():
        if p.is_file() and p.suffix in ('.json','.npz','.log'):copy(p,stage/'bath_mesh'/p.name)
    compress(mesh/'connected.msh',stage/'bath_mesh/connected.msh.gz')
    for p in (mesh/'elmer').glob('mesh.*'):compress(p,stage/'bath_mesh/elmer'/(p.name+'.gz'))
    write(stage/'parent_mesh_references.json',{'Cold30':'fem/results/cold_interface_convergence_20261030/device/cold30um/mesh',
        'Cold20':'fem/results/cold_interface_convergence_20261030/device/cold20um_FAILED/mesh',
        'parent_mesh_sha256':proof['parent_mesh_sha256'],'scope':'existing parent fine geometry was qualified earlier, regardless of then-failed solve'})
    for folder in ('diagnosis20','diagnosis20_refined','diagnosis_bath','bath_native','bath_parent','bath_refined','figures','extra_figures'):
        path=RAW/folder
        if path.exists():
            for p in path.iterdir():
                if p.is_file():copy(p,stage/folder/p.name)
    for name in ('configuration_registry.json','study.json','bath_comparison.json'):copy(RAW/name,stage/name)
    if read(RAW/'figures/provenance.json')['study_sha256']!=sha(RAW/'study.json'):raise ValueError('Stale actual-field figure')
    if read(RAW/'extra_figures/provenance.json')['source_sha256']!=sha(ROOT/'tecooledmct/cold20_figures.py'):raise ValueError('Stale measured figures')
    for folder in RAW.glob('*_library'):small_tree(folder,stage/'builds'/folder.name)
    for name in ('umfpack.h','umf4_f77wrapper.c'):
        copy(RAW/name,stage/'upstream'/name)
    for p in (ROOT/'outputs').glob('cold20-*.log'):copy(p,stage/'verification'/p.name)
    copy(ROOT/'outputs/cold20-runtime-image.txt',stage/'verification/runtime_image.txt')
    bath=read(RAW/'bath_comparison.json');primary_case=Path(registry['primary_case']);accepted_nonraw(primary_case)
    write(stage/'case_status.json',cases)
    write(stage/'qualification.json',{'Cold20_actual_completed_and_nonraw_verified':True,'three_actual_mesh_levels':True,
        'full_device_qualification':False,'OEM_validated':False,'device_GCI_qualified':False,'primary_case':primary_case.name,
        'native_Cold20':read(RAW/'loaded20_direct_P1/solver-status.json'),'same_mesh_refined_parent_passed':read(RAW/'loaded20_refined_replay/same_mesh_agreement.json')['passed'],
        'independent_bath_comparison':bath,'historical_failed_raw_bath_criteria':'UNCHANGED FAILED; no reaction/recovered substitution',
        'old_report':'UNCHANGED15 pages','scope':'solid-only source-traced synthetic reference; no enclosure/gas/radiation/OEM claim',
        'failed_Picard_physical_verification_retained':True,'all_failed_trials_retained':True})
    write(stage/'checksums.json',{'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'artifact_sha256':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'preserved':preserved})
    stage.rename(DEST);verify()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args();verify() if a.verify else publish()
