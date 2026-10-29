"""Actual coupled G3b cases with immutable labels, source hashes and independent postchecks."""
import argparse,json
import numpy as np
from pathlib import Path
from .g2d_data import ROOT,sha,dump
from .fem_g3b_data import preserve
from .fem_g3b_physics import write_case
from .fem_g3b_post import postprocess
from .fem_g2b_physics import execute_solver


def verify_used_source(case,name,digest):
    current=ROOT/name
    if sha(current)==digest:return
    snapshot=case/'source_snapshot'/(current.name+'.source')
    if not snapshot.exists() or sha(snapshot)!=digest:raise ValueError('Execution source changed without its exact snapshot: '+name)
    if current.name!='fem_g3b_physics.py':raise ValueError('Physical dependency changed: '+name)
    # Permit exactly the known startup patch, byte for byte. No other change
    # (including node maps, I/O, coefficients or physical expressions) is allowed.
    text=current.read_text()
    replacements=[(' LOGICAL,SAVE :: initialized=.FALSE.,have_response=.FALSE.',' LOGICAL,SAVE :: initialized=.FALSE.'),
                  ('  IF(.NOT.have_response) THEN\n   power=rawpower;have_response=.TRUE.\n  ELSE\n',''),
                  ('  END IF\n  oldpower=power','  oldpower=power')]
    for new,old in replacements:
        if text.count(new)!=1:raise ValueError('Unknown iteration source version: '+name)
        text=text.replace(new,old,1)
    if text!=snapshot.read_text():raise ValueError('Source differs beyond the exact startup patch: '+name)


def verify_initial_bulk(operator,initial):
    """Potential transfer is qualified only on the identical bulk discretization."""
    meta=json.loads((initial/'case.json').read_text())
    source=Path(meta['operator_path']) if 'operator_path' in meta else (initial/'mesh.nodes').resolve().parent.parent
    with np.load(source/'mesh.npz') as old,np.load(operator/'mesh.npz') as new:
        if any(not np.array_equal(old[k],new[k]) for k in ('points','cells','bodies')):
            raise ValueError('Cross-mesh potential interpolation is unqualified; use fem_g3b_refine temperature-only initialization')


def run(operator,case,resume=False,restart=None,initial=None,**config):
    preserve();sources=[ROOT/'tecooledmct'/f'fem_g3b_{s}.py' for s in ('data','reference','exchange','physics')]
    if initial:sources.append(ROOT/'tecooledmct/fem_g3b_initial.py')
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    if resume:
        ex=json.loads((case/'execution.json').read_text());meta=json.loads((case/'case.json').read_text())
        if ex['solver_status']['exit_code'] or sha(case/'case.sif')!=ex['sif_sha256'] or sha(sorted(case.glob('fields*.vtu'))[-1])!=ex['vtu_sha256'] or ex['mesh_sha256']!=sha(operator/'mesh.npz'):raise ValueError('Changed/incomplete actual execution')
        for n,h in ex['source_sha256'].items():
            verify_used_source(case,n,h)
        for k,v in config.items():
            alias={'pressure':'pressure_pa','radiation':'radiation_on','window_eps':'window_emissivity','sigma':'package_sigma_s_m','pbias':'pbias_w','poptical':'poptical_thermal_w','current':'current_a'}.get(k,k)
            if meta[alias]!=v:raise ValueError('Resume conditions differ '+k)
    else:
        if case.exists():raise ValueError('Case label exists; retain history and use another label')
        if initial:verify_initial_bulk(operator,initial)
        if restart:
            old=json.loads((restart/'case.json').read_text());oldop=Path(old['operator_path'])
            if any(sha(oldop/'elmer'/n)!=sha(operator/'elmer'/n) for n in ('mesh.nodes','mesh.elements')):raise ValueError('Restart requires exact same bulk mesh; use interpolated initial fields for a new mesh')
        case.mkdir(parents=True);snap=case/'source_snapshot';snap.mkdir()
        for p in sources:(snap/(p.name+'.source')).write_bytes(p.read_bytes())
        write_case(operator,case,restart=restart,**config)
        if initial:
            from .fem_g3b_initial import initialize
            initialize(operator,case,initial)
        status=execute_solver(case)
        if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Actual PDE source changed during execution')
        dump(case/'execution.json',{'source_sha256':hashes,'solver_status':status,'operator_path':str(operator),'mesh_sha256':sha(operator/'mesh.npz'),'sif_sha256':sha(case/'case.sif'),'vtu_sha256':sha(sorted(case.glob('fields*.vtu'))[-1])})
    r=postprocess(operator,case);r['solver_status']=json.loads((case/'solver-status.json').read_text());dump(case/'metrics.json',r)
    if not r['passed']:raise RuntimeError('G3b numerical acceptance failed: '+str(case))
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--operator',type=Path,default=Path('outputs/fem-g3b/operator_h0'));p.add_argument('--case',type=Path,required=True);p.add_argument('--current',type=float,default=.1);p.add_argument('--pbias',type=float,default=.0015);p.add_argument('--optical',type=float,default=.0005);p.add_argument('--gas',default='N2');p.add_argument('--pressure',type=float,default=0.);p.add_argument('--radiation-off',action='store_true');p.add_argument('--lead-off',action='store_true');p.add_argument('--window-eps',type=float,default=.1);p.add_argument('--sigma',type=float,default=1e-12);p.add_argument('--restart',type=Path);p.add_argument('--initial',type=Path);p.add_argument('--resume',action='store_true');a=p.parse_args();run(a.operator.resolve(),a.case.resolve(),a.resume,a.restart.resolve() if a.restart else None,a.initial.resolve() if a.initial else None,current=a.current,pbias=a.pbias,poptical=a.optical,gas=a.gas,pressure=a.pressure,radiation=not a.radiation_off,lead_scale=0. if a.lead_off else 1.,window_eps=a.window_eps,sigma=a.sigma)
