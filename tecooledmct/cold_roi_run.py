"""Actual coupled executions on newly audited, geometrically identical ROI meshes."""
import argparse,json,datetime,shutil
from pathlib import Path
from .geometry_rebaseline import ROOT,sha,write
from .corrected_thermal import write_case
from .corrected_thermal_post import postprocess
from .fem_g2b_physics import execute_solver


def run(mesh,case,cu=False,restart=None):
    proof=json.loads((mesh/'audit.json').read_text());mapping=json.loads((mesh/'elmer_mapping.json').read_text())
    if not proof['passed'] or not proof['geometrically_identical'] or not proof['only_cold_sizing_changed'] or not mapping['passed']:
        raise ValueError('Need a complete audited216-domain ROI mesh')
    if proof['mesh_sha256']!=sha(mesh/'mesh.npz') or proof['manifest_sha256']!=sha(mesh/'manifest.json'):raise ValueError('Mesh/registry changed')
    for name,digest in proof['source_sha256'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Mesh generation source changed')
    if restart:
        prior=json.loads((restart/'execution.json').read_text())
        if prior['mesh_sha256']!=sha(mesh/'mesh.npz') or prior['solver_status']['exit_code']!=0:raise ValueError('Only genuine same-mesh restarts allowed')
    sources=[Path(__file__),ROOT/'tecooledmct/corrected_thermal.py',ROOT/'tecooledmct/corrected_thermal_post.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    write_case(mesh,case,current=.1,load=.002,cu=cu,au=False,sigma=1e-12,restart=restart)
    snapshot=case/'source_snapshot';snapshot.mkdir()
    for p in sources:shutil.copy2(p,snapshot/(p.name+'.source'))
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();status=execute_solver(case,timeout=1200)
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Source changed during coupled execution')
    source=sorted(case.rglob('fields*.vtu'))[-1]
    write(case/'execution.json',{'source_sha256':hashes,'mesh_sha256':sha(mesh/'mesh.npz'),'manifest_sha256':sha(mesh/'manifest.json'),
       'sif_sha256':sha(case/'case.sif'),'vtu_sha256':sha(source),'field_source':str(source.relative_to(case)),
       'started_UTC':started,'finished_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'solver_status':status,
       'initial_state':'fresh300K/phi0' if restart is None else {'case':str(restart),'result_sha256':sha(restart/'solution.result'),'same_mesh':True},
       'scope':'new corrected ROI mesh; no cross-mesh state substitution, no gas/radiation;4CPU/12GiB pinned runtime'})
    # Reuse frozen numerical checks without changing any tolerance. Its historical
    # one-mesh status string is supplemented, not silently interpreted as GCI.
    result=postprocess(mesh,case)
    write(case/'roi_scope.json',{'fresh_coupled_execution':True,'mesh_level':proof['level'],'raw_gates_passed':result['passed'],
         'full_device_qualification':False,'spatial_convergence':'assessed separately across actual completed cases; not established by this run'})
    print('ROI coupled',case.name,'PASS primary gates' if result['passed'] else 'FAILED retained gates',result['die_mean_k'],result['voltage_v'],result['checks'],flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,required=True);p.add_argument('--case',type=Path,required=True);p.add_argument('--cu',action='store_true');p.add_argument('--restart',type=Path)
    a=p.parse_args();run(a.mesh.resolve(),a.case.resolve(),a.cu,a.restart.resolve() if a.restart else None)
