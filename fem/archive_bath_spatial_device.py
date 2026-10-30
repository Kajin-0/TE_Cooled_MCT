#!/usr/bin/env python3
"""Archive the bounded real coupled pair and retain its failed raw gate."""
import argparse,gzip,json,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tecooledmct.geometry_rebaseline import sha,write
from fem.archive_cold20 import copy,compress,small_tree,source_proof
from fem.archive_bath_spatial_diagnosis import guard as prior_guard
RAW=ROOT/'outputs/bath-spatial';DEST=ROOT/'fem/results/bath_spatial_device_20261030';GEOMETRY=ROOT/'fem/results/bath_spatial_diagnosis_20261030/geometry'
SOURCES=['tecooledmct/bath_spatial_'+x+'.py' for x in ['device','modes','results']]+[
 'fem/archive_bath_spatial_device.py','fem/restore_bath_spatial.py','tests/test_bath_spatial_device.py','tests/test_bath_spatial_device_archive.py',
 'docs/BATH_SPATIAL_FLUX_AND_COMBINED_QUALIFICATION.md','docs/BATH_SPATIAL_DEVICE_REPRODUCIBILITY.md']
def read(p):return json.loads(p.read_text())
def guard():
    subprocess.run([sys.executable,str(ROOT/'fem/archive_bath_spatial_diagnosis.py'),'--verify'],check=True)
    return {'diagnosis_ledger':sha(ROOT/'fem/results/bath_spatial_diagnosis_20261030/checksums.json'),'prior':prior_guard()}
def pack(source,target):
    compress(source,target)
    if target.stat().st_size<=90_000_000:return
    gzsha=sha(target);parts=[]
    with target.open('rb') as stream:
        j=0
        while chunk:=stream.read(48*1024*1024):
            name=target.name+f'.part{j:03d}';part=target.with_name(name);part.write_bytes(chunk);parts.append({'name':name,'sha256':sha(part),'bytes':len(chunk)});j+=1
    write(target.with_name(target.name+'.parts.json'),{'gzip_sha256':gzsha,'parts':parts,'scope':'exact concatenation of compressed bytes; not reduced or quantized fields'})
    target.unlink()
def verify():
    ledger=read(DEST/'checksums.json')
    for group,base in [('sources',ROOT),('artifacts',DEST)]:
        for n,h in ledger[group].items():
            if sha(base/n)!=h:raise ValueError('Changed actual coupled spatial evidence: '+n)
    if guard()!=ledger['preserved']:raise ValueError('Prior evidence changed')
    s=read(DEST/'device_summary.json')
    if s['full_numerical_release'] or s['combined_case_permitted'] or any(c['bath_raw_1percent_passed'] for c in s['cases']):raise ValueError('Wrong failed-gate scope')
    print('Verified two real coupled spatial refinements, original failed1% bath, combined NOT RUN and unchanged approved Rev3')
def publish():
    import numpy as np
    from tecooledmct.cold20_analysis import accepted_nonraw
    from tecooledmct.cold20_solver import timed_source
    if DEST.exists():raise ValueError('Archive immutable; use --verify')
    preserved=guard();log=(ROOT/'outputs/bath-spatial-tests-final.log').read_text();match=re.search(r'(\d+) passed',log)
    if not match or int(match[1])<145:raise ValueError('Full opt-in regression incomplete')
    summary=read(RAW/'device_summary.json')
    if summary['source_sha256']!=sha(ROOT/'tecooledmct/bath_spatial_results.py') or summary['combined_case_permitted']:raise ValueError('Wrong current scope/summary producer')
    stage=ROOT/'outputs'/('bath-spatial-device-publication-'+str(time.time_ns()));stage.mkdir()
    for row in summary['cases']:
        label=row['case'];case=RAW/(label+'_case');mesh=RAW/(label+'_mesh');target=stage/'cases'/label;r=accepted_nonraw(case);e=read(case/'execution.json');a=read(RAW/(label+'_audit')/'summary.json')
        if e['mesh_sha256']!=sha(GEOMETRY/label/'mesh.npz') or e['mesh_sha256']!=sha(mesh/'mesh.npz') or e['vtu_sha256']!=sha(case/e['field_source']) or e['sif_sha256']!=sha(case/'case.sif'):raise ValueError('Changed genuine field/input')
        if a['field_sha256']!=e['vtu_sha256'] or a['mesh_sha256']!=e['mesh_sha256'] or r['current_a']!=.1 or r['deposited_power_w']!=.002 or r['cu_leads_on'] or r['au_bonds_on']:raise ValueError('Changed physics or wrong audit')
        source_proof(e['source_sha256'],case/'source_snapshot');backend=read(case/'backend_registration.json');source_proof(backend['source_sha256'],case/'backend_source_snapshot')
        upstream=Path('/opt/elmer/provenance/ThermoElectricSolver.F90');timed=case/'timed/TimedThermoElectricSolver.F90'
        if sha(upstream)!=e['upstream_sha256'] or sha(timed)!=e['timed_source_sha256'] or timed.read_text()!=timed_source(upstream.read_text()) or not e['assembly_byte_identical_after_timer_removal']:raise ValueError('Timed source changed physical assembly')
        library=RAW/(label+'_case_library')
        if sha(library/'umf_refine.so')!=backend['library_sha256']:raise ValueError('Different executed numeric library')
        for n,h in a['source_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('Audit source changed')
        small_tree(case,target);small_tree(library,stage/'builds'/label);hashes={}
        write(target/'runtime_binary_fingerprints.json',{'numeric_wrapper_sha256':backend['library_sha256'],'timed_solver_sha256':sha(case/'timed/Cold20Timed.so'),'source_instrumentation_reproduced':True})
        for p in case.iterdir():
            if p.is_file() and not p.is_symlink() and (p.suffix in ['.vtu','.result'] or p.name.startswith('mesh.')):
                pack(p,target/(p.name+'.gz'));hashes[p.name]=sha(p)
        write(target/'uncompressed_sha256.json',hashes)
        for folder in [RAW/(label+'_audit'),RAW/(label+'_transfer')]:
            if (folder/'transfer.json').exists():
                tr=read(folder/'transfer.json')
                for n,key in [('map.npz','map_sha256'),('initial_values.npz','initial_values_sha256'),('initial_guess.result','initial_guess_sha256')]:
                    if sha(folder/n)!=tr[key]:raise ValueError('Changed body-aware transfer')
                mapping=np.load(folder/'map.npz')
                if mapping['weights'].min()<0 or abs(mapping['weights'].sum(1)-1).max()>1e-12:raise ValueError('Nonconvex initial guess')
            for p in folder.rglob('*'):
                if p.is_file():
                    dst=stage/folder.name/p.relative_to(folder)
                    if p.suffix=='.result':pack(p,dst.with_name(dst.name+'.gz'))
                    else:copy(p,dst)
    for name in ['device_summary.json','polynomial_modes.json']:copy(RAW/name,stage/name)
    for p in (RAW/'device_figures_release').iterdir():
        if p.is_file():copy(p,stage/'figures'/p.name)
    for p in (ROOT/'outputs').glob('bath-spatial-*.log'):copy(p,stage/'verification'/p.name)
    write(stage/'geometry_references.json',{row['case']:{'path':str((GEOMETRY/row['case']).relative_to(ROOT)),'mesh_sha256':row['mesh_sha256']} for row in summary['cases']})
    for n in SOURCES:copy(ROOT/n,stage/'source_snapshot'/(n+'.source'))
    if any(p.stat().st_size>100_000_000 for p in stage.rglob('*') if p.is_file()):raise ValueError('Repository artifact size bound exceeded')
    write(stage/'checksums.json',{'sources':{n:sha(ROOT/n) for n in SOURCES},'artifacts':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'preserved':preserved})
    stage.rename(DEST);verify()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args();verify() if a.verify else publish()
