"""Hashed actual-field interpolation for an initial guess only; new PDE still solves."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import LinearNDInterpolator
from .g2d_data import sha,dump
from .fem_g1_run import execute


def initialize(operator,case,source_case):
    import meshio
    accepted=json.loads((source_case/'metrics.json').read_text())
    execution=json.loads((source_case/'execution.json').read_text())
    if not accepted['passed'] or execution['solver_status']['exit_code']!=0:raise ValueError('Initial fields require a genuine accepted source solve')
    meta=json.loads((source_case/'case.json').read_text());source_operator=Path(meta['operator_path']) if 'operator_path' in meta else (source_case/'mesh.nodes').resolve().parent.parent;m=np.load(source_operator/'mesh.npz');target=np.load(operator/'mesh.npz');field_path=sorted(source_case.glob('fields*.vtu'))[-1];f=meshio.read(field_path)
    if sha(field_path)!=execution['vtu_sha256']:raise ValueError('Changed actual initial-source VTU')
    dist,ix=cKDTree(f.points).query(m['points'])
    if dist.max()>1e-12:raise ValueError('Actual initial-source field/mesh mismatch')
    ff={k.lower():v.ravel()[ix] for k,v in f.point_data.items()};values=np.column_stack([ff['temperature'],ff['potential']]);result=np.zeros((len(target['points']),2));counts=np.zeros(len(result));fallback=0
    for bid in np.unique(target['bodies']):
        old=np.unique(m['cells'][m['bodies']==bid]);new=np.unique(target['cells'][target['bodies']==bid]);x=m['points'][old];y=values[old];interp=LinearNDInterpolator(x,y)(target['points'][new]);bad=~np.isfinite(interp).all(axis=1)
        if bad.any():
            _,nearest=cKDTree(x).query(target['points'][new][bad]);interp[bad]=y[nearest];fallback+=int(bad.sum())
        result[new]+=interp;counts[new]+=1
    if np.any(counts==0):raise ValueError('Uninitialized new body nodes')
    result/=counts[:,None];rows=np.loadtxt(operator/'elmer/mesh.nodes');dd,ix=cKDTree(rows[:,2:5]).query(target['points']);ids=rows[ix,0].astype(int);ordered=np.empty_like(result);ordered[ids-1]=result;np.savetxt(case/'InitialFields.dat',ordered,fmt='%.17e',header=str(len(ordered)),comments='')
    source='''MODULE G3bInitialData
 USE DefUtils
 IMPLICIT NONE
 LOGICAL,SAVE :: loaded=.FALSE.
 REAL(KIND=dp),ALLOCATABLE,SAVE :: vals(:,:)
CONTAINS
 SUBROUTINE LoadInitial()
 INTEGER :: u,n,i
 IF(loaded) RETURN
 OPEN(NEWUNIT=u,FILE='InitialFields.dat',STATUS='old')
 READ(u,*)n;ALLOCATE(vals(n,2))
 DO i=1,n
 READ(u,*)vals(i,:)
 END DO
 CLOSE(u);loaded=.TRUE.
 END SUBROUTINE LoadInitial
END MODULE G3bInitialData
FUNCTION InitialT(Model,node,x) RESULT(v)
 USE G3bInitialData
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: x,v
 CALL LoadInitial();v=vals(node,1)
END FUNCTION InitialT
FUNCTION InitialPhi(Model,node,x) RESULT(v)
 USE G3bInitialData
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: x,v
 CALL LoadInitial();v=vals(node,2)
END FUNCTION InitialPhi
'''
    lib=case/'initial_library';lib.mkdir();(lib/'Initial.F90').write_text(source);execute(['elmerf90','-ffree-line-length-none','-o','G3bInitial','Initial.F90'],lib,'compile');library=lib/'G3bInitial';sif=(case/'case.sif').read_text();a=sif.index('Initial Condition 1\n');b=sif.index('\nEnd',a);sif=sif[:a]+f'Initial Condition 1\n Temperature = Variable Coordinate 1\n  Real Procedure "{library.resolve()}" "InitialT"\n Potential = Variable Coordinate 1\n  Real Procedure "{library.resolve()}" "InitialPhi"'+sif[b:];(case/'case.sif').write_text(sif)
    info={'actual_source_case':str(source_case),'actual_vtu_sha256':sha(field_path),'source_mesh_sha256':sha(source_operator/'mesh.npz'),'initial_field_sha256':sha(case/'InitialFields.dat'),'body_node_fallback_count':fallback,'method':'per-body piecewise-linear interpolated initial guess, nearest source node outside old chordal hull; not a prescribed/solved final field'};meta=json.loads((case/'case.json').read_text());meta['initial_actual_state']=info;dump(case/'case.json',meta);return info
