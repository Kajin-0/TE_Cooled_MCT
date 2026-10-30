"""Matched fine-mesh ideal-lead control; never relabel original gate failures."""
import argparse,gzip,json,shutil,tempfile,time
from pathlib import Path
import numpy as np
from .g2d_data import ROOT,sha,dump
from .full_presolder_guard import preserve
from .flux_presolder_common import node_map
from .fem_g3b_physics import write_case
from .fem_g3b_post import postprocess
from .fem_g2b_physics import execute_solver
from .fem_g1_run import execute


def run(case,timeout=1800):
    preserve();archive=ROOT/'fem/results/g3b_checkpoint_20261029';source=archive/'unaccepted_development/nitrogen_fine_verified';operator=ROOT/'outputs/fem-g3b/operator_h1';published=archive/'operators/operator_h1'
    if case.exists():raise ValueError('Retain previous control')
    if sha(operator/'mesh.npz')!=sha(published/'mesh.npz'):raise ValueError('Fine actual mesh differs')
    old=json.loads((source/'metrics.json').read_text());execution=json.loads((source/'execution.json').read_text())
    if execution['solver_status']['exit_code'] or any(not value for name,value in old['checks'].items() if name!='direct_bath_1pct'):raise ValueError('Initial source must fail only original raw bath gate')
    case.mkdir(parents=True);snapshot=case/'source_snapshot';snapshot.mkdir()
    sources=[Path(__file__),ROOT/'tecooledmct/fem_g3b_physics.py',ROOT/'tecooledmct/fem_g3b_post.py',ROOT/'tecooledmct/fem_g3b_reference.py',ROOT/'tecooledmct/full_presolder_guard.py'];hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    for p in sources:shutil.copy2(p,snapshot/p.name)
    write_case(operator,case,current=.1,pbias=.0015,poptical=.0005,gas='N2',pressure=100.,lead_scale=0.)
    import meshio
    with tempfile.TemporaryDirectory(dir=ROOT/'outputs/full-presolder-cache') as tmp:
        raw=Path(tmp)/'field.vtu'
        with gzip.open(source/'fields_t0001.vtu.gz','rb') as inp,raw.open('wb') as out:shutil.copyfileobj(inp,out)
        expected=json.loads((source/'uncompressed_sha256.json').read_text())['fields_t0001.vtu']
        if sha(raw)!=expected:raise ValueError('Changed converged-but-unaccepted field')
        field=meshio.read(raw)
    data=np.load(operator/'mesh.npz');ix,_=node_map(data['points'],field.points);values=np.column_stack([field.point_data['temperature'].ravel()[ix],field.point_data['potential'].ravel()[ix]])
    rows=np.loadtxt(operator/'elmer/mesh.nodes');mapping,_=node_map(data['points'],rows[:,2:5]);ordered=np.empty_like(values);ordered[rows[mapping,0].astype(int)-1]=values;np.savetxt(case/'InitialFields.dat',ordered,fmt='%.17e',header=str(len(values)),comments='')
    lib=case/'initial_library';lib.mkdir();shutil.copy2(source/'initial_library/Initial.F90',lib/'Initial.F90');execute(['elmerf90','-ffree-line-length-none','-o','LeadInitial','Initial.F90'],lib,'compile')
    sif=(case/'case.sif').read_text();a=sif.index('Initial Condition 1\n');z=sif.index('\nEnd',a);sif=sif[:a]+f'Initial Condition 1\n Temperature = Variable Coordinate 1\n  Real Procedure "{(lib/"LeadInitial").resolve()}" "InitialT"\n Potential = Variable Coordinate 1\n  Real Procedure "{(lib/"LeadInitial").resolve()}" "InitialPhi"'+sif[z:];(case/'case.sif').write_text(sif)
    dump(case/'input_manifest.json',{'source_sha256':hashes,'initial_source_accepted':False,'initial_source_failure':'original raw bath1% gate only','initial_vtu_sha256':expected,'initial_F90_sha256':sha(lib/'Initial.F90'),'mesh_sha256':sha(operator/'mesh.npz'),'sif_sha256':sha(case/'case.sif'),'scope':'assumed-geometry fine-mesh lead-off diagnostic only; gold/gas/radiation and full88leg current remain; no manufactured-device prediction or physically corrected lead routing'})
    status=execute_solver(case,timeout=timeout)
    if any(sha(ROOT/name)!=digest for name,digest in hashes.items()):raise ValueError('Execution source changed')
    dump(case/'execution.json',{'source_sha256':hashes,'solver_status':status,'operator_path':str(operator),'mesh_sha256':sha(operator/'mesh.npz'),'sif_sha256':sha(case/'case.sif'),'vtu_sha256':sha(sorted(case.glob('fields*.vtu'))[-1])})
    r=postprocess(operator,case);r['solver_status']=status;dump(case/'metrics.json',r);dump(case/'scope.json',{'manufactured_device':False,'assumed_geometry_sandbox':True,'original_historical_raw_gate_remains_failed':True,'physically_rerouted_return_trace_implemented':False,'new_case_gates_passed':r['passed']})
    print('Fine matched lead-off:',r['die_mean_k'],r['voltage_v'],r['direct_bath_relative_error'],r['checks'],flush=True)
    if not r['passed']:raise RuntimeError('Retain failed original gate(s), no recovered substitution')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--case',type=Path,required=True);parser.add_argument('--timeout',type=float,default=1800);a=parser.parse_args();run(a.case.resolve(),a.timeout)
