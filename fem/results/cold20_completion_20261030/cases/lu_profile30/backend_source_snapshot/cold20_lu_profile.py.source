"""Pass-through timing of pinned UMFPACK symbolic/numeric calls; same-mesh check."""
import argparse,os,shutil
from pathlib import Path
from . import cold20_solver as runner
from .geometry_rebaseline import ROOT,sha,write
from .fem_g1_run import execute


def run(mesh,case,reference):
    src=ROOT/'fem/cold20/umf_trace.c';library=case.parent/(case.name+'_library');library.mkdir(parents=True,exist_ok=False)
    shutil.copy2(src,library/src.name);execute(['gcc','-shared','-fPIC','-O2','-o','umf_trace.so',src.name,'-ldl'],library,'compile',timeout=60)
    original=runner.write_case;old=os.environ.get('LD_PRELOAD');sources=[Path(__file__),src,ROOT/'tecooledmct/cold20_solver.py'];hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    def registered(*args,**kwargs):
        r=original(*args,**kwargs);snap=case/'backend_source_snapshot';snap.mkdir()
        for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
        write(case/'backend_registration.json',{'source_sha256':hashes,'registered_before_solver':True,'operation':'pass unchanged arguments to original umf4_l_sym/num via RTLD_NEXT; timers/report only',
          'library_sha256':sha(library/'umf_trace.so'),'UMFPACK_Info_indices_source':'pinned umfpack/src/umfpack/include/umfpack.h','no_physical_or_solver_parameter_change':True})
        return r
    runner.write_case=registered;os.environ['LD_PRELOAD']=str((library/'umf_trace.so').resolve())
    try:r=runner.run(mesh,case,'big_umfpack',restart=reference,reference=reference,timeout=400)
    finally:
        runner.write_case=original
        if old is None:os.environ.pop('LD_PRELOAD',None)
        else:os.environ['LD_PRELOAD']=old
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Profiling source changed during execution')
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('mesh','case','reference'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.mesh.resolve(),a.case.resolve(),a.reference.resolve())
