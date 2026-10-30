"""Explicit projected INITIAL GUESS only; final evidence requires actual coupled PDE."""
import argparse,datetime,json,shutil
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import ROOT,sha,write
from .corrected_thermal import write_case
from .corrected_thermal_post import postprocess
from .fem_g2b_physics import execute_solver

PLAN=ROOT/'data/cold_convergence/projected_initialization_plan.json'


def run(mesh,case,seed,same_mesh_check=None):
    import meshio
    proof=json.loads((mesh/'audit.json').read_text())
    if not all(proof[k] for k in ('passed','geometrically_identical','only_cold_sizing_changed')):raise ValueError('Audited corrected mesh required')
    if not json.loads((mesh/'elmer_mapping.json').read_text())['passed']:raise ValueError('Elmer mapping failed')
    for n,h in proof['source_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('Changed mesh source')
    prior=json.loads((seed/'execution.json').read_text());fieldpath=seed/prior['field_source']
    if prior['solver_status']['exit_code'] or sha(fieldpath)!=prior['vtu_sha256']:raise ValueError('Need genuine completed seed field')
    same=sha(mesh/'mesh.npz')==prior['mesh_sha256']
    if not same:
        if same_mesh_check is None:raise ValueError('Same-mesh ASCII restart format must be verified first')
        check=json.loads((same_mesh_check/'initialization_check.json').read_text())
        if not check['passed'] or check['mesh_sha256']!=prior['mesh_sha256']:raise ValueError('Restart-format proof failed')
    sources=[Path(__file__),ROOT/'tecooledmct/corrected_thermal.py',ROOT/'tecooledmct/corrected_thermal_post.py',PLAN]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    write_case(mesh,case,current=.1,load=.002,cu=False,au=False,sigma=1e-12)
    # Elmer node IDs, not NPZ/VTU order, define the identity-permutation guess.
    nodes=np.loadtxt(mesh/'elmer/mesh.nodes');nodes=nodes[np.argsort(nodes[:,0])]
    if not np.array_equal(nodes[:,0],np.arange(1,len(nodes)+1)):raise ValueError('Contiguous Elmer node IDs required')
    field=meshio.read(fieldpath);dist,ix=cKDTree(field.points).query(nodes[:,2:5]);T=field.point_data['temperature'].ravel()[ix];phi=field.point_data['potential'].ravel()[ix]
    N=len(nodes);guess=case/'projected_initial_guess.result'
    with guess.open('w') as out:
        out.write(f' ASCII 3\n!Projected initial guess ONLY; never a solved field\n Degrees of freedom: \npot[temperature:1 potential:1] : {2*N} {N} 2 : thermoelectric\ntemperature : {N} {N} 1 : thermoelectric\npotential : {N} {N} 1 : thermoelectric\n Total DOFs: 2\n Number Of Nodes: {N}\nTime: 1 1 1.00000000E+000\ntemperature\nPerm: {N} {N}\n')
        for i in range(1,N+1):out.write(f'{i} {i}\n')
        np.savetxt(out,T,fmt='%.17e');out.write('potential\nPerm: use previous\n');np.savetxt(out,phi,fmt='%.17e')
    sif=case/'case.sif';text=sif.read_text().replace('Linear System Direct Method = UMFPACK','Linear System Direct Method = "big umfpack"')
    text=text.replace(' Output File = "solution.result"',' Restart File = "projected_initial_guess.result"\n Restart Position = 0\n Output File = "solution.result"');sif.write_text(text)
    initialization={'method':'nearest actual field node; INITIAL GUESS ONLY','same_mesh':same,'seed_field_sha256':sha(fieldpath),
         'seed_case':str(seed),'maximum_nearest_distance_m':float(dist.max()),'distance_quantiles_m':np.quantile(dist,[0,.5,.95,1]).tolist(),
         'initial_guess_sha256':sha(guess),'plan_sha256':sha(PLAN),'same_mesh_format_proof':str(same_mesh_check) if same_mesh_check else None}
    write(case/'initialization.json',initialization);meta=json.loads((case/'case.json').read_text());meta['initial_state']=initialization;write(case/'case.json',meta)
    snap=case/'source_snapshot';snap.mkdir()
    for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();status=execute_solver(case,timeout=1200)
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Source changed during solve')
    source=sorted(case.rglob('fields*.vtu'))[-1]
    write(case/'execution.json',{'source_sha256':hashes,'mesh_sha256':sha(mesh/'mesh.npz'),'manifest_sha256':sha(mesh/'manifest.json'),
          'sif_sha256':sha(sif),'vtu_sha256':sha(source),'field_source':str(source.relative_to(case)),
          'started_UTC':started,'finished_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'solver_status':status,
          'initial_state':initialization,'linear_index_mode':'64bit big umfpack; same PDE','scope':'projected initial guess only; final genuine coupled solve on its own fine mesh'})
    r=postprocess(mesh,case)
    if same:
        old=json.loads((seed/'metrics.json').read_text());dt=r['die_mean_k']-old['die_mean_k'];dv=r['voltage_v']-old['voltage_v']
        passed=abs(dt)<1e-6 and abs(dv)<1e-8 and r['checks']==old['checks']
        write(case/'initialization_check.json',{'passed':passed,'mesh_sha256':prior['mesh_sha256'],'die_difference_K':dt,'voltage_difference_V':dv,
            'proof':'actual same-mesh coupled rerun from identity-permutation ASCII3 guess; no analytical output substitution'})
        if not passed:raise ValueError('Same-mesh restart-format check failed')
    write(case/'roi_scope.json',{'fresh_coupled_execution':True,'mesh_level':proof['level'],'projected_guess_not_final':True,
          'raw_gates_passed':r['passed'],'full_device_qualification':False,'spatial_convergence':'assessed separately across actual completed cases'})
    print('Projected INITIAL-GUESS actual coupled solve',case.name,r['die_mean_k'],r['voltage_v'],r['checks'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,required=True);p.add_argument('--case',type=Path,required=True);p.add_argument('--seed',type=Path,required=True);p.add_argument('--same-mesh-check',type=Path)
    a=p.parse_args();run(a.mesh.resolve(),a.case.resolve(),a.seed.resolve(),a.same_mesh_check.resolve() if a.same_mesh_check else None)
