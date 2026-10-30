"""Bounded64-bit-index direct retry; same PDE/mesh/tolerances as failed32-bit case."""
import argparse,datetime,json,shutil
from pathlib import Path
from .geometry_rebaseline import ROOT,sha,write
from .corrected_thermal import write_case
from .corrected_thermal_post import postprocess
from .fem_g2b_physics import execute_solver


def run(mesh,case,failed):
    proof=json.loads((mesh/'audit.json').read_text())
    if not all(proof[k] for k in ('passed','geometrically_identical','only_cold_sizing_changed')):
        raise ValueError('Audited conformal source mesh required')
    if not json.loads((mesh/'elmer_mapping.json').read_text())['passed']:raise ValueError('Elmer mapping failed')
    for n,h in proof['source_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('Changed mesh source')
    if sha(mesh/'mesh.npz')!=proof['mesh_sha256']:raise ValueError('Changed mesh')
    prior=json.loads((failed/'solver-status.json').read_text())
    if prior['exit_code']==0:raise ValueError('Retry only a retained failure')
    sources=[Path(__file__),ROOT/'tecooledmct/corrected_thermal.py',ROOT/'tecooledmct/corrected_thermal_post.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    write_case(mesh,case,current=.1,load=.002,cu=False,au=False,sigma=1e-12)
    sif=case/'case.sif';text=sif.read_text()
    if text.replace(str(case),'{CASE}')!= (failed/'case.sif').read_text().replace(str(failed),'{CASE}'):
        raise ValueError('Retry inputs differ before index-mode change and output-path normalization')
    sif.write_text(text.replace('Linear System Direct Method = UMFPACK','Linear System Direct Method = "big umfpack"'))
    snap=case/'source_snapshot';snap.mkdir()
    for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
    write(case/'retry.json',{'previous_case':str(failed),'previous_status_sha256':sha(failed/'solver-status.json'),
          'previous_sif_sha256':sha(failed/'case.sif'),'only_change':'32-bit to64-bit UMFPACK indexing',
          'primary_source':'https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/DirectSolve.F90'})
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();status=execute_solver(case,timeout=1200)
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Source changed during execution')
    source=sorted(case.rglob('fields*.vtu'))[-1]
    write(case/'execution.json',{'source_sha256':hashes,'mesh_sha256':sha(mesh/'mesh.npz'),'manifest_sha256':sha(mesh/'manifest.json'),
          'sif_sha256':sha(sif),'vtu_sha256':sha(source),'field_source':str(source.relative_to(case)),
          'started_UTC':started,'finished_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'solver_status':status,'initial_state':'fresh300K/phi0','linear_index_mode':'64bit big umfpack; same PDE',
          'scope':'same corrected ROI mesh; no cross-mesh state substitution;4CPU/12GiB pinned runtime'})
    result=postprocess(mesh,case)
    write(case/'roi_scope.json',{'fresh_coupled_execution':True,'mesh_level':proof['level'],'raw_gates_passed':result['passed'],
        'full_device_qualification':False,'spatial_convergence':'assessed separately across actual completed cases'})
    print('64bit ROI solve',case.name,result['die_mean_k'],result['checks'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,required=True);p.add_argument('--case',type=Path,required=True);p.add_argument('--failed',type=Path,required=True)
    a=p.parse_args();run(a.mesh.resolve(),a.case.resolve(),a.failed.resolve())
