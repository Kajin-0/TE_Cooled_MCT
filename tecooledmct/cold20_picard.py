"""Existing thermoelectric Picard branch to the SAME nonlinear physical residual."""
import argparse,shutil
from pathlib import Path
from . import cold20_solver as runner
from .geometry_rebaseline import ROOT,sha,write

PLAN=ROOT/'data/cold20/picard_plan.json'


def run(mesh,case,restart=None,projection=None,reference=None,timeout=400):
    original=runner.write_case;sources=[Path(__file__),PLAN,ROOT/'tecooledmct/cold20_solver.py'];hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    def registered_writer(*args,**kwargs):
        result=original(*args,**kwargs);sif=case/'case.sif';text=sif.read_text()
        for old,new in [('Nonlinear System Newton After Iterations = 2','Nonlinear System Newton After Iterations = 60'),
                        ('Nonlinear System Newton After Tolerance = 1e-7','Nonlinear System Newton After Tolerance = 0')]:
            if text.count(old)!=1:raise ValueError('Unexpected nonlinear settings')
            text=text.replace(old,new)
        sif.write_text(text);snap=case/'backend_source_snapshot';snap.mkdir()
        for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
        write(case/'backend_registration.json',{'source_sha256':hashes,'registered_before_solver':True,
            'backend':'existing Picard linearization with unchanged physical residual/nonlinear1e-9 and GMRES/ILU1',
            'scope':'numerical linearization only; no Joule/Peltier/Seebeck/Fourier term or BC changed'})
        return result
    runner.write_case=registered_writer
    try:r=runner.run(mesh,case,'gmres_ilu1',restart,projection,reference,timeout=timeout)
    finally:runner.write_case=original
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Picard extension changed during run')
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('mesh','case'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('restart','projection','reference'):p.add_argument('--'+n,type=Path)
    p.add_argument('--timeout',type=int,default=400);a=p.parse_args()
    run(a.mesh.resolve(),a.case.resolve(),a.restart.resolve() if a.restart else None,a.projection.resolve() if a.projection else None,a.reference.resolve() if a.reference else None,a.timeout)
