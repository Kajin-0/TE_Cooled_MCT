"""Additive timed numerical backends for the unchanged corrected coupled PDE."""
import argparse,datetime,json,re,shutil
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .corrected_thermal import write_case
from .corrected_thermal_post import postprocess
from .fem_g1_run import execute
from .fem_g2b_physics import execute_solver

PLAN=ROOT/'data/cold20/plan.json'


def read(p):return json.loads(p.read_text())


def timed_source(text):
    substitutions=[('  REAL(KIND=dp):: NewtonTol, NonlinTol, RelativeChange','  REAL(KIND=dp):: NewtonTol, NonlinTol, RelativeChange\n  REAL(KIND=dp) :: cold_t0,cold_t1,cold_t2'),
        ('    CALL DefaultInitialize()','    CALL CPU_TIME(cold_t0)\n    CALL DefaultInitialize()'),
        ('    Norm = DefaultSolve()','    CALL CPU_TIME(cold_t1)\n    Norm = DefaultSolve()\n    CALL CPU_TIME(cold_t2)\n    WRITE(Message,*) "COLD20_TIMING",iter,cold_t1-cold_t0,cold_t2-cold_t1\n    CALL Info("Cold20Profile",Message,Level=1)')]
    out=text
    for before,after in substitutions:
        if out.count(before)!=1:raise ValueError('Unexpected pinned ThermoElectricSolver source')
        out=out.replace(before,after)
    restored=out
    for before,after in reversed(substitutions):restored=restored.replace(after,before)
    if restored!=text:raise ValueError('Instrumentation changed physical assembly')
    return out


def linear_settings(backend):
    if backend=='big_umfpack':return ' Linear System Solver = Direct\n Linear System Direct Method = "big umfpack"'
    pre={'gmres_ilu1':'ILU1','gmres_ilu2':'ILU2','gmres_ilut':'ILUT'}[backend]
    return f''' Linear System Solver = Iterative
 Linear System Iterative Method = GMRES
 Linear System Preconditioning = {pre}
 Linear System GMRES Restart = 100
 Linear System Max Iterations = 5000
 Linear System Convergence Tolerance = 1e-13
 Linear System Abort Not Converged = Logical True
 Linear System Residual Output = 100
 Linear System ILUT Tolerance = 1e-5'''


def compare(case,reference):
    r=read(case/'metrics.json');old=read(reference/'metrics.json');tol=read(PLAN)['same_mesh_agreement']
    cuts=max(abs(r['cuts'][key]['current_a']-old['cuts'][key]['current_a']) for key in r['cuts'])
    d={'die_mean_K':r['die_mean_k']-old['die_mean_k'],'voltage_V':r['voltage_v']-old['voltage_v'],
       'each177_cut_A':cuts,'raw_bath_W':r['hot_out_raw_gradient_w']-old['hot_out_raw_gradient_w']}
    checks={k:abs(v)<tol[k] for k,v in d.items()};checks['same_primary_gate_booleans']=r['checks']==old['checks']
    result={'differences':d,'checks':checks,'passed':all(checks.values()),'reference_execution_sha256':sha(reference/'execution.json'),
            'plan_sha256':sha(PLAN),'scope':'same exact mesh/physics; raw failures preserved'}
    write(case/'same_mesh_agreement.json',result);print('Same-mesh agreement',result,flush=True)
    if not result['passed']:raise ValueError('Numerical backend has NOT qualified')
    return result


def run(mesh,case,backend,restart=None,projection=None,reference=None,current=.1,load=.002,timeout=400):
    proof=read(mesh/'audit.json')
    if not proof['passed'] or not read(mesh/'elmer_mapping.json')['passed'] or sha(mesh/'mesh.npz')!=proof['mesh_sha256']:
        raise ValueError('Need exact audited mesh and Elmer mapping')
    for n,h in proof['source_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('Changed mesh producer')
    if restart and read(restart/'execution.json')['mesh_sha256']!=sha(mesh/'mesh.npz'):raise ValueError('Genuine restart requires identical mesh')
    sources=[Path(__file__),PLAN,ROOT/'tecooledmct/corrected_thermal.py',ROOT/'tecooledmct/corrected_thermal_post.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    write_case(mesh,case,current=current,load=load,cu=False,au=False,sigma=1e-12,restart=restart)
    upstream=Path('/opt/elmer/provenance/ThermoElectricSolver.F90');code=upstream.read_text()
    lib=case/'timed';lib.mkdir();source=lib/'TimedThermoElectricSolver.F90';source.write_text(timed_source(code))
    execute(['elmerf90','-O2','-fPIC','-shared','-o','Cold20Timed.so',source.name],lib,'compile',timeout=120)
    sif=case/'case.sif';text=sif.read_text();old=' Linear System Solver = Direct\n Linear System Direct Method = UMFPACK'
    if text.count(old)!=1:raise ValueError('Unexpected solver template')
    text=text.replace(old,linear_settings(backend)).replace('Procedure = "ThermoElectricSolver" "ThermoElectricSolver"',f'Procedure = "{(lib/"Cold20Timed").resolve()}" "ThermoElectricSolver"')
    initialization={'same_mesh_restart':str(restart)} if restart else 'uniform300K/phi0'
    if projection:
        transfer=read(projection/'transfer.json')
        if transfer['target_mesh_sha256']!=sha(mesh/'mesh.npz') or not transfer['passed']:raise ValueError('Wrong/failed P1 transfer')
        shutil.copy2(projection/'initial_guess.result',case/'initial_guess.result')
        if sha(case/'initial_guess.result')!=transfer['initial_guess_sha256']:raise ValueError('Changed projected guess')
        text=text.replace(' Output File = "solution.result"',' Restart File = "initial_guess.result"\n Restart Position = 0\n Output File = "solution.result"')
        initialization={'P1_initial_guess_only':str(projection),'transfer_sha256':sha(projection/'transfer.json'),'guess_sha256':sha(case/'initial_guess.result')}
    sif.write_text(text);snap=case/'source_snapshot';snap.mkdir()
    for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
    write(case/'pre_execution.json',{'source_sha256':hashes,'mesh_sha256':sha(mesh/'mesh.npz'),'manifest_sha256':sha(mesh/'manifest.json'),
        'sif_sha256':sha(sif),'backend':backend,'initial_state':initialization,'upstream_sha256':sha(upstream),'timed_source_sha256':sha(source),
        'assembly_byte_identical_after_timer_removal':True,'timeout_seconds':timeout,'physical_equations_and_gates_unchanged':True,
        'started_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    status=execute_solver(case,timeout=timeout)
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Source changed during solve')
    raw=sorted(case.rglob('fields*.vtu'))[-1]
    e=read(case/'pre_execution.json');e.update(field_source=str(raw.relative_to(case)),vtu_sha256=sha(raw),solver_status=status,
        finished_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat());write(case/'execution.json',e)
    timings=[]
    for line in (case/'solver.log').read_text().splitlines():
        if 'COLD20_TIMING' in line:
            fields=line.split('COLD20_TIMING')[1].split();timings.append({'iteration':int(fields[0]),'assembly_cpu_s':float(fields[1]),'linear_cpu_s':float(fields[2])})
    write(case/'timings.json',{'iterations':timings,'upstream_sha256':sha(upstream),'instrumentation_only':True})
    r=postprocess(mesh,case)
    write(case/'scope.json',{'actual_coupled_execution':True,'backend':backend,'full_device_qualification':False,
          'primary_checks_passed':r['passed'],'note':'original postprocessor historical one-mesh string superseded only by separately audited comparison'})
    if reference:compare(case,reference)
    print('Actual timed coupled',backend,case.name,r['die_mean_k'],r['voltage_v'],r['checks'],flush=True)
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,required=True);p.add_argument('--case',type=Path,required=True)
    p.add_argument('--backend',choices=('big_umfpack','gmres_ilu1','gmres_ilu2','gmres_ilut'),required=True)
    for name in ('restart','projection','reference'):p.add_argument('--'+name,type=Path)
    p.add_argument('--current',type=float,default=.1);p.add_argument('--load',type=float,default=.002);p.add_argument('--timeout',type=int,default=400)
    a=p.parse_args();run(a.mesh.resolve(),a.case.resolve(),a.backend,a.restart.resolve() if a.restart else None,a.projection.resolve() if a.projection else None,a.reference.resolve() if a.reference else None,a.current,a.load,a.timeout)
