"""Versioned Krylov configuration extension of the frozen timed runner.

The isolated CLI process substitutes only its linear-settings provider. The
extension source/config are registered and copied BEFORE PDE execution; original
runner source, PDE, timing instrumentation and all checks remain unchanged.
"""
import argparse,shutil
from pathlib import Path
from . import cold20_solver as runner
from .geometry_rebaseline import ROOT,sha,write

PLAN=ROOT/'data/cold20/krylov_plan.json'


def settings(name):
    p=runner.read(PLAN)['profiles'][name]
    text=f''' Linear System Solver = Iterative
 Linear System Iterative Method = {p['method']}
 Linear System Preconditioning = {p['preconditioner']}
 Linear System Max Iterations = 5000
 Linear System Convergence Tolerance = 1e-13
 Linear System Abort Not Converged = Logical True
 Linear System Robust = Logical True
 Linear System Residual Mode = Logical True
 Linear System Residual Output = 10'''
    return text+('\n Linear System GCR Restart = 40' if name=='gcr_ilu2' else '\n BiCGStabL Polynomial Degree = 4')


def run(mesh,case,backend,restart=None,projection=None,reference=None,timeout=400):
    original_writer=runner.write_case;original_settings=runner.linear_settings
    sources=[Path(__file__),PLAN,ROOT/'tecooledmct/cold20_solver.py'];hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    def registered_writer(*args,**kwargs):
        result=original_writer(*args,**kwargs);snap=case/'backend_source_snapshot';snap.mkdir()
        for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
        write(case/'backend_registration.json',{'source_sha256':hashes,'backend':backend,'linear_settings':settings(backend),
             'override_scope':'linear-settings provider in this isolated Python process ONLY; math/BC/assembly unchanged',
             'registered_before_solver':True})
        return result
    runner.write_case=registered_writer;runner.linear_settings=settings
    try:result=runner.run(mesh,case,backend,restart,projection,reference,timeout=timeout)
    finally:runner.write_case=original_writer;runner.linear_settings=original_settings
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Backend extension source changed during run')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('mesh','case'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('restart','projection','reference'):p.add_argument('--'+n,type=Path)
    p.add_argument('--backend',choices=('gcr_ilu2','bicgstabl_ilu2'),required=True);p.add_argument('--timeout',type=int,default=400);a=p.parse_args()
    run(a.mesh.resolve(),a.case.resolve(),a.backend,a.restart.resolve() if a.restart else None,a.projection.resolve() if a.projection else None,a.reference.resolve() if a.reference else None,a.timeout)
