"""Run immutable-labelled actual package cases; no substitute network fields."""
import argparse,json
from pathlib import Path
from .g2d_data import ROOT,sha,dump
from .fem_g3a_data import preserve
from .fem_g3a_physics import write_case
from .fem_g3a_post import postprocess
from .fem_g2b_physics import execute_solver


def run(mesh,case,current,pbias=0.,poptical=0.,wire_scale=1.,sigma=1e-12,attach_scale=1.,mount_scale=1.,restart=None,resume=False):
    preserve();files=[ROOT/'tecooledmct'/f'fem_g3a_{s}.py' for s in ('data','physics')];hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
    if resume:
        ex=json.loads((case/'execution.json').read_text());meta=json.loads((case/'case.json').read_text())
        requested={'current_a':current,'pbias_w':pbias,'poptical_thermal_w':poptical,'wire_scale':wire_scale,'package_sigma_s_m':sigma,'attach_k_scale':attach_scale,'mount_k_scale':mount_scale}
        if any(meta[k]!=v for k,v in requested.items()) or ex['sif_sha256']!=sha(case/'case.sif') or ex['status']['exit_code']!=0:raise ValueError('Cannot reuse a different/incomplete actual execution')
        for n,h in ex['source_sha256'].items():
            if n in hashes and h!=sha(ROOT/n):raise ValueError('Actual PDE input source changed')
    else:
        if case.exists():raise ValueError('Case label already exists; retain history and use a new label')
        write_case(mesh,case,current,pbias,poptical,wire_scale,sigma,attach_scale,mount_scale,restart);status=execute_solver(case)
        if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('PDE source changed during run')
        dump(case/'execution.json',{'source_sha256':hashes,'status':status,'sif_sha256':sha(case/'case.sif'),'mesh_npz_sha256':sha(mesh/'mesh.npz')})
    result=postprocess(mesh,case);result['solver_status']=json.loads((case/'solver-status.json').read_text());dump(case/'metrics.json',result)
    if not result['passed']:raise RuntimeError('Package numerical acceptance failure: '+str(case))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,default=Path('outputs/fem-g3a/mesh_0'));p.add_argument('--case',required=True,type=Path);p.add_argument('--current',type=float,default=.1);p.add_argument('--pbias',type=float,default=.0015);p.add_argument('--optical',type=float,default=.0005);p.add_argument('--wire-scale',type=float,default=1.);p.add_argument('--sigma',type=float,default=1e-12);p.add_argument('--attach-scale',type=float,default=1.);p.add_argument('--mount-scale',type=float,default=1.);p.add_argument('--restart',type=Path);p.add_argument('--resume',action='store_true');a=p.parse_args();run(a.mesh.resolve(),a.case.resolve(),a.current,a.pbias,a.optical,a.wire_scale,a.sigma,a.attach_scale,a.mount_scale,a.restart.resolve() if a.restart else None,a.resume)
