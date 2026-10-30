"""Exact-zero sparse storage compaction on a PRIVATE per-linear-solve matrix."""
import argparse,datetime,shutil
from pathlib import Path
from .geometry_rebaseline import ROOT,sha,write
from .cold20_solver import read,timed_source,compare
from .corrected_thermal import write_case
from .corrected_thermal_post import postprocess
from .fem_g1_run import execute
from .fem_g2b_physics import execute_solver

PLAN=ROOT/'data/cold20/compaction_plan.json'


def compact_source(upstream):
    text=timed_source(upstream)
    text=text.replace('  USE DefUtils','  USE DefUtils\n  USE CRSMatrix, ONLY: CRS_RemoveZeros',1)
    before='  REAL(KIND=dp) :: cold_t0,cold_t1,cold_t2'
    text=text.replace(before,before+'\n  TYPE(Matrix_t), POINTER :: cold_original,cold_work\n  INTEGER :: cold_nnz0,cold_nnz1',1)
    before='    Norm = DefaultSolve()'
    after='''    ! Private deep copies of all sparse-operator arrays. Keep the original
    ! assembly topology intact: Newton may create entries that are zero NOW.
    cold_original => Solver % Matrix
    ALLOCATE(cold_work)
    cold_work = cold_original
    ALLOCATE(cold_work % Rows(SIZE(cold_original % Rows)))
    ALLOCATE(cold_work % Cols(SIZE(cold_original % Cols)))
    ALLOCATE(cold_work % Diag(SIZE(cold_original % Diag)))
    ALLOCATE(cold_work % Values(SIZE(cold_original % Values)))
    ALLOCATE(cold_work % rhs(SIZE(cold_original % rhs)))
    cold_work % Rows = cold_original % Rows
    cold_work % Cols = cold_original % Cols
    cold_work % Diag = cold_original % Diag
    cold_work % Values = cold_original % Values
    cold_work % rhs = cold_original % rhs
    cold_work % UMFPack_Numeric = 0
    cold_nnz0 = SIZE(cold_work % Values)
    CALL CRS_RemoveZeros(cold_work,RemoveEps=0.0_dp)
    cold_nnz1 = SIZE(cold_work % Values)
    WRITE(Message,*) "COLD20_STORAGE",iter,cold_nnz0,cold_nnz1
    CALL Info("Cold20Profile",Message,Level=1)
    Solver % Matrix => cold_work
    Norm = DefaultSolve()
    Solver % Matrix => cold_original
    DEALLOCATE(cold_work % Rows,cold_work % Cols,cold_work % Diag)
    DEALLOCATE(cold_work % Values,cold_work % rhs)
    DEALLOCATE(cold_work)'''
    if text.count(before)!=1:raise ValueError('Unexpected timed source')
    text=text.replace(before,after)
    # The mathematical bulk and boundary assembly sections are untouched.
    if text.split('CONTAINS',1)[1]!=upstream.split('CONTAINS',1)[1]:raise ValueError('Physical local assembly changed')
    return text


def run(mesh,case,restart=None,projection=None,reference=None,timeout=400):
    proof=read(mesh/'audit.json')
    if not proof['passed'] or not read(mesh/'elmer_mapping.json')['passed'] or sha(mesh/'mesh.npz')!=proof['mesh_sha256']:raise ValueError('Audited exact mesh required')
    for n,h in proof['source_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('Changed mesh source')
    if restart and read(restart/'execution.json')['mesh_sha256']!=sha(mesh/'mesh.npz'):raise ValueError('Wrong restart mesh')
    sources=[Path(__file__),ROOT/'tecooledmct/cold20_solver.py',PLAN,ROOT/'data/cold20/plan.json',ROOT/'tecooledmct/corrected_thermal.py',ROOT/'tecooledmct/corrected_thermal_post.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    write_case(mesh,case,current=.1,load=.002,cu=False,au=False,sigma=1e-12,restart=restart)
    upstream=Path('/opt/elmer/provenance/ThermoElectricSolver.F90');lib=case/'compact';lib.mkdir();source=lib/'CompactThermoElectric.F90';source.write_text(compact_source(upstream.read_text()))
    execute(['elmerf90','-O2','-fPIC','-shared','-o','Cold20Compact.so',source.name],lib,'compile',timeout=120)
    sif=case/'case.sif';text=sif.read_text().replace('Linear System Direct Method = UMFPACK','Linear System Direct Method = "big umfpack"')
    text=text.replace('Procedure = "ThermoElectricSolver" "ThermoElectricSolver"',f'Procedure = "{(lib/"Cold20Compact").resolve()}" "ThermoElectricSolver"')
    initialization={'same_mesh_restart':str(restart)} if restart else 'uniform300K/phi0'
    if projection:
        tr=read(projection/'transfer.json')
        if not tr['passed'] or tr['target_mesh_sha256']!=sha(mesh/'mesh.npz'):raise ValueError('Wrong/failed P1 initial transfer')
        shutil.copy2(projection/'initial_guess.result',case/'initial_guess.result')
        if sha(case/'initial_guess.result')!=tr['initial_guess_sha256']:raise ValueError('Changed initial guess')
        text=text.replace(' Output File = "solution.result"',' Restart File = "initial_guess.result"\n Restart Position = 0\n Output File = "solution.result"')
        initialization={'P1_initial_guess_only':str(projection),'transfer_sha256':sha(projection/'transfer.json'),'guess_sha256':sha(case/'initial_guess.result')}
    sif.write_text(text);snap=case/'source_snapshot';snap.mkdir()
    for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
    e={'source_sha256':hashes,'mesh_sha256':sha(mesh/'mesh.npz'),'manifest_sha256':sha(mesh/'manifest.json'),'sif_sha256':sha(sif),
       'upstream_sha256':sha(upstream),'instrumented_source_sha256':sha(source),'backend':'exact-zero private-copy64bit UMFPACK',
       'initial_state':initialization,'timeout_seconds':timeout,'physical_equations_and_gates_unchanged':True,'bulk_boundary_assembly_byte_identical':True,
       'started_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()};write(case/'pre_execution.json',e)
    status=execute_solver(case,timeout=timeout)
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Source changed during execution')
    raw=sorted(case.rglob('fields*.vtu'))[-1];e.update(solver_status=status,field_source=str(raw.relative_to(case)),vtu_sha256=sha(raw),finished_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat());write(case/'execution.json',e)
    timings=[];storage=[]
    for line in (case/'solver.log').read_text().splitlines():
        for label,rows,names in [('COLD20_TIMING',timings,['iteration','assembly_cpu_s','linear_cpu_s']),('COLD20_STORAGE',storage,['iteration','stored_entries','nonzero_entries'])]:
            if label in line:
                values=line.split(label)[1].split();rows.append(dict(zip(names,[int(values[0]),*[float(v) for v in values[1:]]])))
    write(case/'timings.json',{'iterations':timings,'storage':storage,'remove_epsilon':0,'private_copy_original_pattern_retained':True})
    r=postprocess(mesh,case);write(case/'scope.json',{'actual_coupled_execution':True,'primary_checks_passed':r['passed'],'full_device_qualification':False})
    if reference:compare(case,reference)
    print('Exact-zero private-copy coupled',case.name,r['die_mean_k'],r['voltage_v'],r['checks'],flush=True)
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('mesh','case'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('restart','projection','reference'):p.add_argument('--'+n,type=Path)
    p.add_argument('--timeout',type=int,default=400);a=p.parse_args()
    run(a.mesh.resolve(),a.case.resolve(),a.restart.resolve() if a.restart else None,a.projection.resolve() if a.projection else None,a.reference.resolve() if a.reference else None,a.timeout)
