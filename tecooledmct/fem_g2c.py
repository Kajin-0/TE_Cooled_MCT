"""Opt-in local-temperature adapter for the pinned genuine coupled Elmer solver."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
import numpy as np
from .material_profiles import Profile
from .fem_g1_run import execute
from .fem_g2a import write_sif as stage_sif
from .fem_g2b_physics import write_sif as stack_sif,protected_integrity


def intact_checkpoints():
    result=protected_integrity();root=Path(__file__).resolve().parents[1]
    for folder in ('g2b_two_terminal_20261028',):
        out=root/'fem/results'/folder;data=json.loads((out/'checksums.json').read_text())
        for name,h in data['source_sha256'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=h:raise ValueError(f'Protected G2b source changed: {name}')
        for name,h in data['artifacts_sha256'].items():
            if hashlib.sha256((out/name).read_bytes()).hexdigest()!=h:raise ValueError(f'Protected G2b evidence changed: {name}')
    return {**result,'connected_g2b_unchanged':True}


def compile_profile(out:Path,profile:Profile,freeze_k=None):
    out.mkdir(parents=True,exist_ok=True);parts=[]
    for polarity in ('P','N'):
        for key,name in (('rho','Electric'),('k','Heat'),('S','Seebeck')):
            c=profile.curves[polarity][key];ts=c.temperature_k
            ys=c.values if freeze_k is None else tuple(float(c.evaluate(freeze_k)) for _ in ts)
            def numbers(values):return ', '.join(f'{x:.16e}_dp' for x in values)
            parts.append(f'''FUNCTION {polarity}{name}(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx({len(ts)}) = [ {numbers(ts)} ]
 REAL(KIND=dp),PARAMETER :: yy({len(ts)}) = [ {numbers(ys)} ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx({len(ts)}))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,{len(ts)-1}
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,{len(ts)-1})
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 {"v=1.0_dp/v" if key=='rho' else ''}
END FUNCTION {polarity}{name}
''')
    source=out/'Material.F90';source.write_text('\n'.join(parts))
    execute(['elmerf90','-ffree-line-length-none','-o','G2cMaterial',source.name],out,'compile')
    return out/'G2cMaterial'


def write_case(case,mesh,profile,library,current=.05,load=.002,freeze_k=None,hot=300.,cold=None,stack=False,restart_from=None):
    if not profile.interval[0]<=hot<=profile.interval[1] or (cold is not None and not profile.interval[0]<=cold<=profile.interval[1]):
        raise ValueError('Boundary temperatures outside complete profile coverage')
    if stack:stack_sif(case,mesh,current,load)
    else:stage_sif(case/'case.sif',mesh,current,load,cold)
    text=(case/'case.sif').read_text()
    # Boundary and initial changes occur only in this newly generated case.
    text=text.replace('Temperature = Real 300',f'Temperature = Real {hot}')
    text=text.replace('Nonlinear System Max Iterations = 40','Nonlinear System Max Iterations = 60')
    text=text.replace('Nonlinear System Convergence Tolerance = 1e-10','Nonlinear System Convergence Tolerance = 1e-9')
    for polarity,mid in (('P',1),('N',2)):
        start=text.index(f'Material {mid}\n');end=text.index('\nEnd',start)
        block=text[start:end]
        for key,symbol in (('Heat Conductivity','Heat'),('Electric Conductivity','Electric'),('Seebeck Coefficient','Seebeck')):
            block=re.sub(rf'  {key} = Real [^\n]+',f'  {key} = Variable Temperature\n    Real Procedure "{library.resolve()}" "{polarity}{symbol}"',block)
        text=text[:start]+block+text[end:]
    restart_metadata=None
    if restart_from is not None:
        import shutil
        initial=Path(restart_from)/'solution.result'
        if not initial.is_file():raise ValueError('Warm start requires a genuine solved result')
        shutil.copy2(initial,case/'initial.result')
        text=text.replace('  Output File = "solution.result"','  Restart File = "initial.result"\n  Restart Position = 0\n  Output File = "solution.result"')
        restart_metadata={'source_case':str(restart_from),'result_sha256':hashlib.sha256(initial.read_bytes()).hexdigest()}
    (case/'case.sif').write_text(text)
    meta=json.loads((case/'case.json').read_text());meta.update(profile_id=profile.metadata['id'],profile_status=profile.metadata['status'],
        profile_interval_k=list(profile.interval),profile_freeze_k=freeze_k,hot_k=hot,fixed_cold_k=cold,initial_state=restart_metadata or 'uniform initial temperature',
        coefficients='local nodal T functions; coefficients interpolated at quadrature as in pinned ThermoElectricSolver',
        thomson='implicit in divergence(T*S(T)*J); no additional duplicate source',oem_grade_matched=False)
    (case/'case.json').write_text(json.dumps(meta,indent=2)+'\n')
