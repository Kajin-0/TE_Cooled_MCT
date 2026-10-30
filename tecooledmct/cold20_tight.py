"""Tighter inner residual, unchanged physical/nonlinear acceptance criteria."""
import argparse,shutil
from pathlib import Path
from . import cold20_solver as runner
from .geometry_rebaseline import ROOT,sha,write

PLAN=ROOT/'data/cold20/tight_plan.json'


def run(mesh,case,restart=None,reference=None,projection=None,timeout=400):
    writer=runner.write_case;linear=runner.linear_settings
    sources=[Path(__file__),PLAN,ROOT/'tecooledmct/cold20_solver.py'];hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    def tight_linear(name):return linear(name).replace('Linear System Convergence Tolerance = 1e-13','Linear System Convergence Tolerance = 1e-15')
    def registered(*args,**kwargs):
        r=writer(*args,**kwargs);sif=case/'case.sif';text=sif.read_text().replace('Nonlinear System Newton After Iterations = 2','Nonlinear System Newton After Iterations = 60').replace('Nonlinear System Newton After Tolerance = 1e-7','Nonlinear System Newton After Tolerance = 0');sif.write_text(text)
        snap=case/'backend_source_snapshot';snap.mkdir()
        for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
        write(case/'backend_registration.json',{'source_sha256':hashes,'registered_before_solver':True,
             'backend':'Picard GMRES/ILU1 with tighter1e-15 inner residual; physical gates and nonlinear1e-9 unchanged'})
        return r
    runner.write_case=registered;runner.linear_settings=tight_linear
    try:r=runner.run(mesh,case,'gmres_ilu1',restart,projection,reference,timeout=timeout)
    finally:runner.write_case=writer;runner.linear_settings=linear
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Tight backend source changed during solve')
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('mesh','case'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('restart','projection','reference'):p.add_argument('--'+n,type=Path)
    p.add_argument('--timeout',type=int,default=400);a=p.parse_args()
    run(a.mesh.resolve(),a.case.resolve(),a.restart.resolve() if a.restart else None,a.reference.resolve() if a.reference else None,a.projection.resolve() if a.projection else None,a.timeout)
