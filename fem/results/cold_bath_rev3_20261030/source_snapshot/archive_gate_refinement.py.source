#!/usr/bin/env python3
"""Archive scoped raw-flux studies without converting failed gates to passes."""
import argparse,gzip,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tecooledmct.geometry_rebaseline import sha,write
from fem.archive_cold20 import copy,compress,small_tree,source_proof
DEST=ROOT/'fem/results/cold_bath_rev3_20261030'
RAW=ROOT/'outputs/gate-refinement'
SOURCES=['tecooledmct/gate_refinement.py','tecooledmct/gate_refinement_analysis.py','tecooledmct/gate_refinement_study.py','data/gate_refinement/plan.json',
    'data/gate_refinement/bath3_bounds.json','data/gate_refinement/combined_bounds.json',
    'data/gate_refinement/solver_bounds.json','fem/archive_gate_refinement.py','tests/test_gate_refinement.py','tests/test_gate_refinement_archive.py',
    'docs/COLD_BATH_VOLUME_REFINEMENT_RESULT.md','docs/COLD_BATH_VOLUME_REFINEMENT_REPRODUCIBILITY.md']
def read(p):return json.loads(p.read_text())
def guard():
    subprocess.run([sys.executable,str(ROOT/'fem/archive_cold20.py'),'--verify'],check=True)
    return sha(ROOT/'fem/results/cold20_completion_20261030/checksums.json')
def verify():
    d=read(DEST/'checksums.json')
    for key,base in [('sources',ROOT),('artifacts',DEST)]:
        for n,h in d[key].items():
            if sha(base/n)!=h:raise ValueError('Changed scoped evidence: '+n)
    if guard()!=d['prior_ledger_sha256']:raise ValueError('Changed prior archive')
    if read(DEST/'summary.json')['full_numerical_release']:raise ValueError('Unqualified release claim')
    print('Verified new independent volume studies, explicit raw-gate status and preserved earlier evidence')
def publish():
    import numpy as np
    if DEST.exists():raise ValueError('Archive immutable; use --verify')
    old=guard();log=(ROOT/'outputs/rev3-tests-expanded.log').read_text()
    import re
    count=re.search(r'(\d+) passed',log)
    if not count or int(count[1])<125 or 'FAILED' in log:raise ValueError('Full opt-in regression incomplete')
    stage=ROOT/'outputs'/('gate-publication-'+str(time.time_ns()));stage.mkdir()
    summary=read(RAW/'summary.json')
    if summary['full_numerical_release']:raise ValueError('No release without systematically refined passing comparator')
    for label in summary['trials']:
        mesh=RAW/(label+'_mesh');case=RAW/(label+'_case');target=stage/'cases'/label
        a=read(mesh/'audit.json')
        if not a['passed'] or not a['independent_region_lock_passed'] or not read(mesh/'elmer_mapping.json')['passed']:raise ValueError('Geometry proof failed')
        if sha(mesh/'mesh.npz')!=a['mesh_sha256']:raise ValueError('Mesh modified after execution')
        for n,h in a['source_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('Mesh generator or preregistration changed')
        for p in mesh.rglob('*'):
            if not p.is_file():continue
            dst=stage/'meshes'/label/p.relative_to(mesh)
            if p.suffix=='.msh' or p.parent.name=='elmer':compress(p,dst.with_name(dst.name+'.gz'))
            else:copy(p,dst)
        small_tree(case,target)
        backend=read(case/'backend_registration.json');source_proof(backend['source_sha256'],case/'backend_source_snapshot')
        library=RAW/(label+'_case_library')
        if sha(library/'umf_refine.so')!=backend['library_sha256']:raise ValueError('Executed numeric-refinement binary differs')
        small_tree(library,stage/'builds'/label)
        status=read(case/'solver-status.json')
        if (case/'execution.json').exists():
            e=read(case/'execution.json');r=read(case/'metrics.json')
            if status!=e['solver_status'] or status['exit_code'] or status['nonlinear_last_relative_change']>=1e-9:raise ValueError('False coupled completion')
            if e['mesh_sha256']!=a['mesh_sha256'] or e['vtu_sha256']!=sha(case/e['field_source']) or e['sif_sha256']!=sha(case/'case.sif'):raise ValueError('Changed executed inputs/field')
            if r['current_a']!=.1 or r['deposited_power_w']!=.002 or r['cu_leads_on'] or r['au_bonds_on'] or r['package_sigma_s_m']!=1e-12:raise ValueError('Unmatched physical case')
            source_proof(e['source_sha256'],case/'source_snapshot')
            if len(r['cuts'])!=177 or not all(v for k,v in r['checks'].items() if k!='raw_bath_1percent'):raise ValueError('Current or conservation failure')
            audit=read(RAW/(label+'_audit')/'summary.json')
            if audit['mesh_sha256']!=a['mesh_sha256'] or audit['field_sha256']!=e['vtu_sha256']:raise ValueError('Audit field differs')
        hashes={}
        for p in case.iterdir():
            if p.is_file() and (p.suffix in ['.vtu','.result']):
                folder=target if (case/'execution.json').exists() else target/'UNCONVERGED_FIELDS'
                compress(p,folder/(p.name+'.gz'));hashes[p.name]=sha(p)
        write(target/'uncompressed_sha256.json',hashes)
        for folder in [RAW/(label+'_transfer'),RAW/(label+'_audit')]:
            if folder.exists():
                if (folder/'transfer.json').exists():
                    tr=read(folder/'transfer.json')
                    for n,k in [('map.npz','map_sha256'),('initial_values.npz','initial_values_sha256'),('initial_guess.result','initial_guess_sha256')]:
                        if sha(folder/n)!=tr[k]:raise ValueError('Changed P1 initialization')
                    for n,h in tr['source_sha256'].items():
                        if sha(ROOT/n)!=h:raise ValueError('Changed P1 source')
                    mp=np.load(folder/'map.npz')
                    if mp['weights'].min()<0 or abs(mp['weights'].sum(1)-1).max()>1e-12:raise ValueError('Invalid P1 weights')
                for p in folder.rglob('*'):
                    if p.is_file():
                        dst=stage/folder.name/p.relative_to(folder)
                        compress(p,dst.with_name(dst.name+'.gz')) if p.suffix=='.result' else copy(p,dst)
    copy(RAW/'summary.json',stage/'summary.json')
    for p in (ROOT/'outputs').glob('rev3-*.log'):copy(p,stage/'verification'/p.name)
    for n in SOURCES:copy(ROOT/n,stage/'source_snapshot'/(Path(n).name+'.source'))
    for p in stage.rglob('*'):
        if p.is_file() and p.stat().st_size>=100_000_000:raise ValueError('Artifact exceeds repository limit: '+str(p))
    write(stage/'checksums.json',{'sources':{n:sha(ROOT/n) for n in SOURCES},'artifacts':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'prior_ledger_sha256':old})
    stage.rename(DEST);verify()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args();verify() if a.verify else publish()
