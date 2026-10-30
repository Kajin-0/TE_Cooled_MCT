"""Existing UMFPACK LU + native residual refinement, never a changed PDE."""
import argparse,os,shutil
from pathlib import Path
from . import cold20_solver as runner
from .geometry_rebaseline import ROOT,sha,write
from .fem_g1_run import execute

PLAN=ROOT/'data/cold20/refinement_plan.json'


def run(mesh,case,restart=None,projection=None,reference=None,timeout=400):
    src=ROOT/'fem/cold20/umf_refine.c';lib=case.parent/(case.name+'_library');lib.mkdir(parents=True,exist_ok=False)
    shutil.copy2(src,lib/src.name);execute(['gcc','-shared','-fPIC','-O2','-o','umf_refine.so',src.name,'-ldl'],lib,'compile',timeout=60)
    writer=runner.write_case;old=os.environ.get('LD_PRELOAD');sources=[Path(__file__),PLAN,src,ROOT/'tecooledmct/cold20_solver.py'];hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    def registered(*args,**kwargs):
        r=writer(*args,**kwargs);snap=case/'backend_source_snapshot';snap.mkdir()
        for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
        write(case/'backend_registration.json',{'source_sha256':hashes,'registered_before_solver':True,'operation':'same original current64bit UMFPACK LU, native solr residual refinement max4, no stale LU or matrix modifications',
            'library_sha256':sha(lib/'umf_refine.so'),'physical_equations_and_gates_unchanged':True})
        return r
    runner.write_case=registered;os.environ['LD_PRELOAD']=str((lib/'umf_refine.so').resolve())
    try:r=runner.run(mesh,case,'big_umfpack',restart,projection,reference,timeout=timeout)
    finally:
        runner.write_case=writer
        if old is None:os.environ.pop('LD_PRELOAD',None)
        else:os.environ['LD_PRELOAD']=old
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Refinement source changed during execution')
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('mesh','case'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('restart','projection','reference'):p.add_argument('--'+n,type=Path)
    p.add_argument('--timeout',type=int,default=400);a=p.parse_args()
    run(a.mesh.resolve(),a.case.resolve(),a.restart.resolve() if a.restart else None,a.projection.resolve() if a.projection else None,a.reference.resolve() if a.reference else None,a.timeout)
