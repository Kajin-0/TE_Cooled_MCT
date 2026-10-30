"""Bounded genuine88-leg coupled runs; failed raw gates remain failed evidence."""
import argparse,gzip,json,shutil,tempfile,resource,time
from pathlib import Path
import numpy as np
from .g2d_data import ROOT,sha,dump
from .full_presolder_guard import preserve
from .full_presolder_physics import write_case
from .full_presolder_post import postprocess
from .fem_g2b_physics import execute_solver
from .fem_g1_run import execute
from .flux_presolder_common import node_map


def initialize(operator,case):
    import meshio
    archive=ROOT/'fem/results/g3b_checkpoint_20261029';source=archive/'fields/nitrogen_patch1'
    cache=ROOT/'outputs/full-presolder-cache';cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        raw=Path(tmp)/'fields.vtu'
        with gzip.open(source/'fields_t0001.vtu.gz','rb') as inp,raw.open('wb') as out:shutil.copyfileobj(inp,out)
        expected=json.loads((source/'uncompressed_sha256.json').read_text())['fields_t0001.vtu']
        if sha(raw)!=expected:raise ValueError('Changed accepted source field')
        field=meshio.read(raw)
    original=np.load(archive/'operators/operator_h0p1/mesh.npz');target=np.load(operator/'mesh.npz');ix,_=node_map(original['points'],field.points)
    n=len(original['points'])
    if not np.array_equal(target['points'][:n],original['points']):raise ValueError('Original nodes moved; warm start unqualified')
    values=list(np.column_stack([field.point_data['temperature'].ravel()[ix],field.point_data['potential'].ravel()[ix]]))
    prolong=operator/'prolongation.npz'
    if prolong.exists():
        data=np.load(prolong)
        for u,v,t in data['edges']:values.append((1-t)*values[int(u)]+t*values[int(v)])
    values=np.array(values)
    if len(values)!=len(target['points']):raise ValueError('Missing exact P1 prolongation')
    rows=np.loadtxt(operator/'elmer/mesh.nodes');mapping,_=node_map(target['points'],rows[:,2:5]);ids=rows[mapping,0].astype(int);ordered=np.empty_like(values);ordered[ids-1]=values
    np.savetxt(case/'InitialFields.dat',ordered,fmt='%.17e',header=str(len(ordered)),comments='')
    text='''MODULE JointInitialData
 USE DefUtils
 LOGICAL,SAVE :: loaded=.FALSE.
 REAL(KIND=dp),ALLOCATABLE,SAVE :: a(:,:)
CONTAINS
 SUBROUTINE Load()
 INTEGER :: u,n,i
 IF(loaded) RETURN
 OPEN(NEWUNIT=u,FILE='InitialFields.dat',STATUS='old')
 READ(u,*)n
 ALLOCATE(a(n,2))
 DO i=1,n
 READ(u,*)a(i,:)
 END DO
 CLOSE(u)
 loaded=.TRUE.
 END SUBROUTINE
END MODULE
FUNCTION JointInitialT(Model,node,x) RESULT(v)
 USE JointInitialData
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: x,v
 CALL Load()
 v=a(node,1)
END FUNCTION
FUNCTION JointInitialPhi(Model,node,x) RESULT(v)
 USE JointInitialData
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: x,v
 CALL Load()
 v=a(node,2)
END FUNCTION
'''
    lib=case/'initial_library';lib.mkdir();(lib/'Initial.F90').write_text(text);execute(['elmerf90','-ffree-line-length-none','-o','JointInitial','Initial.F90'],lib,'compile')
    sif=(case/'case.sif').read_text();start=sif.index('Initial Condition 1\n');end=sif.index('\nEnd',start)
    sif=sif[:start]+f'Initial Condition 1\n Temperature = Variable Coordinate 1\n  Real Procedure "{(lib/"JointInitial").resolve()}" "JointInitialT"\n Potential = Variable Coordinate 1\n  Real Procedure "{(lib/"JointInitial").resolve()}" "JointInitialPhi"'+sif[end:];(case/'case.sif').write_text(sif)
    meta=json.loads((case/'case.json').read_text());meta['initial_actual_state']={'accepted_source_vtu_sha256':expected,'method':'exact identical old nodes plus P1 edge interpolation only inside passive joint; all conductor values unchanged; both fields subsequently solved','initial_field_sha256':sha(case/'InitialFields.dat'),'new_passive_nodes':len(values)-n};dump(case/'case.json',meta)


def run(operator,case,timeout=900):
    integrity=preserve()
    if case.exists():raise ValueError('Preserve execution labels')
    sources=[ROOT/'tecooledmct'/f'full_presolder_{s}.py' for s in ('guard','reference','physics','post','run')]
    hashes={str(path.relative_to(ROOT)):sha(path) for path in sources};case.mkdir(parents=True);snap=case/'source_snapshot';snap.mkdir()
    for p in sources:shutil.copy2(p,snap/p.name)
    write_case(operator,case,current=.1,pbias=.0015,poptical=.0005,gas='N2',pressure=100.)
    initialize(operator,case);start=time.monotonic();status=execute_solver(case,timeout=timeout)
    if any(sha(ROOT/name)!=digest for name,digest in hashes.items()):raise ValueError('PDE source changed during execution')
    execution={'source_sha256':hashes,'solver_status':status,'operator_path':str(operator),'mesh_sha256':sha(operator/'mesh.npz'),'manifest_sha256':sha(operator/'manifest.json'),'sif_sha256':sha(case/'case.sif'),'vtu_sha256':sha(sorted(case.glob('fields*.vtu'))[-1]),'baseline_integrity':integrity,'wall_seconds':time.monotonic()-start,'max_child_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'cpu_cap':4,'memory_cap_gib':12}
    dump(case/'execution.json',execution);r=postprocess(operator,case);r['solver_status']=status;r['qualification_scope']='original per-case raw gates only; historical full fine-mesh G3b qualification still FAILED; no recovered substitution';dump(case/'metrics.json',r)
    print(case.name,'PASS' if r['passed'] else 'FAILED',r['die_mean_k'],r['voltage_v'],r['direct_bath_relative_error'],flush=True)
    if not r['passed']:raise RuntimeError('Retain failed original numerical gates')
    return r

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--operator',type=Path,required=True);parser.add_argument('--case',type=Path,required=True);parser.add_argument('--timeout',type=float,default=900);a=parser.parse_args();run(a.operator.resolve(),a.case.resolve(),a.timeout)
