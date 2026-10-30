#!/usr/bin/env python3
"""Audit/publish completed assumed-geometry evidence; never promote failed gates."""
import argparse
import csv
import gzip
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tecooledmct.full_presolder_guard import preserve
from tecooledmct.geometry_rebaseline import sha,write

RAW=ROOT/'outputs/full-presolder'
DEST=ROOT/'fem/results/full_presolder_checkpoint_20261030'
DOCS=['docs/PHASE1_FULL_PACKAGE_PRESOLDER_QUALIFICATION.md',
      'docs/GEOMETRY_PINOUT_LEAD_DISCREPANCY_AUDIT_20261030.md',
      'docs/REPRO_FULL_PACKAGE_PRESOLDER.md','FULL_DEVICE_PRESOLDER_FLUX_NEXT_WORK_ORDER.md',
      'CRITICAL_GEOMETRY_AND_PARASITICS_AUDIT.md']


def read(path):return json.loads(Path(path).read_text())


def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)


def compress(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with Path(src).open('rb') as inp,dst.open('wb') as target:
        with gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as out:shutil.copyfileobj(inp,out)


def actual_sources(execution):
    for name,digest in execution['source_sha256'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Execution source changed: '+name)


def verify():
    import subprocess
    subprocess.run([sys.executable,str(ROOT/'fem/archive_geometry_rebaseline.py'),'--verify'],check=True)
    preserved=preserve();ledger=read(DEST/'checksums.json')
    if ledger['preserved']!=preserved:raise ValueError('Protected evidence changed')
    for group,parent in [('source_sha256',ROOT),('artifact_sha256',DEST)]:
        for name,digest in ledger[group].items():
            if sha(parent/name)!=digest:raise ValueError('Changed checkpoint: '+name)
    summary=read(DEST/'qualification.json')
    if summary['general_recovery_qualified'] or summary['historical_raw_fine_gate_passed'] or summary['corrected_device_physics_qualified']:
        raise ValueError('False qualification claim')
    print('Verified assumed-geometry checkpoint; raw/recovery/interface failures retained')


def publish():
    import numpy as np
    import meshio
    if DEST.exists():raise ValueError('Immutable archive exists; use --verify')
    preserved=preserve();stage=ROOT/'outputs'/('full-presolder-publication-'+str(time.time_ns()));stage.mkdir()
    operator_refs={};cases=[];budget=[]
    names={'legacy_control':'legacy_operator','zero_contact':'zero_operator','contact_hypothesis':'contact_operator','fine_lead_off':None}
    old=ROOT/'fem/results/g3b_checkpoint_20261029'
    for case,opname in names.items():
        source=RAW/case;ex=read(source/'execution.json');result=read(source/'metrics.json');actual_sources(ex)
        status=ex['solver_status']
        if status['exit_code']!=0 or status.get('timed_out',False) or status['nonlinear_last_relative_change']>=1e-9:raise ValueError('Solver not converged')
        if not result['passed'] or not all(result['checks'].values()):raise ValueError('Original per-case gates failed')
        if len(result['component_cuts'])!=175:raise ValueError('Missing current cuts')
        if sha(source/'case.sif')!=ex['sif_sha256'] or sha(source/'fields_t0001.vtu')!=ex['vtu_sha256']:
            raise ValueError('Actual SIF/field changed')
        if result['vtu_sha256']!=ex['vtu_sha256'] or result['sif_sha256']!=ex['sif_sha256']:
            raise ValueError('Metrics refer to different fields')
        if 'ThermoElectricSolver' not in (source/'case.sif').read_text():raise ValueError('Not coupled thermoelectric PDE')
        field=meshio.read(source/'fields_t0001.vtu')
        if len(field.points)!=result['nodes'] or len(field.get_cells_type('tetra'))!=result['tetrahedra']:
            raise ValueError('Actual full field geometry disagrees')
        if not all(np.isfinite(field.point_data[k]).all() for k in ('temperature','potential')):raise ValueError('Invalid actual solved field')
        if opname:
            operator=RAW/opname;proof=read(operator/'independent_reaudit.json')
            if not proof['passed'] or not proof['all_exterior_faces_explicitly_checked'] or not proof['all88legs']:
                raise ValueError('Incomplete actual mesh audit')
            for name,digest in proof['independent_reaudit_source_sha256'].items():
                if sha(ROOT/name)!=digest:raise ValueError('Changed mesh reaudit source')
            if ex['mesh_sha256']!=sha(operator/'mesh.npz') or ex['manifest_sha256']!=sha(operator/'manifest.json'):
                raise ValueError('Mesh or manifest changed')
        else:
            operator=old/'operators/operator_h1'
            if ex['mesh_sha256']!=sha(operator/'mesh.npz'):raise ValueError('Fine mesh not matched')
        target=stage/'cases'/case;target.mkdir(parents=True)
        # Small generated Fortran/compiler/source evidence; skip executable libraries/results.
        for p in source.rglob('*'):
            if p.is_file() and (p.suffix.lower() in ('.json','.sif','.f90','.log','.txt') or 'source_snapshot' in p.parts):
                if p.name=='InitialFields.dat':continue
                relative=p.relative_to(source)
                if p.suffix=='.py':relative=Path(str(relative)+'.source')
                copy(p,target/relative)
        uncompressed={}
        for name in ('fields_t0001.vtu','ExchangeMatrices.bin','ExchangeWeights.dat','InitialFields.dat'):
            if (source/name).exists():
                compress(source/name,target/(name+'.gz'));uncompressed[name]=sha(source/name)
        write(target/'uncompressed_sha256.json',uncompressed)
        cases.append({k:result[k] for k in ('nodes','tetrahedra','die_mean_k','cold_ceramic_k','voltage_v','direct_bath_relative_error','worst_cut_relative_error','passed')}|{'case':case,'operator':opname or 'protected G3b operator_h1','assumed_geometry_sandbox':True})
        for row in result['stage_control_volume_budgets']:
            budget.append({'case':case,**{k:v for k,v in row.items() if k!='sources_w'},**{'source_'+k:v for k,v in row['sources_w'].items()}})
    # New operators reuse protected cavity matrices only because their cavity geometry
    # was unchanged. This reuse is forbidden for the separate source rebaseline.
    for name in ('legacy_operator','zero_operator','contact_operator','refined_operator'):
        source=RAW/name;target=stage/'operators'/name;target.mkdir(parents=True)
        for item in ('manifest.json','patches.json','audit.json','independent_reaudit.json','grid.log','grid-status.json','weights.npz','prolongation.npz','geometry_source.py.snapshot'):
            if (source/item).exists():copy(source/item,target/item)
        original=old/'operators/operator_h0p1'
        refs={}
        for item in ('operators.npz','mesh.npz'):
            if sha(source/item)==sha(original/item):refs[item]={'path':str((original/item).relative_to(ROOT)),'sha256':sha(source/item)}
            else:copy(source/item,target/item)
        write(target/'protected_references.json',refs);operator_refs[name]=refs
    # Recover the exact earlier generator revision by reversing only the three
    # additive exterior-audit lines. Verify its pre-existing execution digests.
    current=(ROOT/'tecooledmct/full_presolder_geometry.py').read_text()
    generation='\n'.join(line for line in current.split('\n') if not line.startswith(('    exterior=','    declared=','    if exterior!=declared:')))
    digest=hashlib.sha256(generation.encode()).hexdigest()
    for name in ('contact_operator','refined_operator'):
        if read(RAW/name/'audit.json')['source_sha256']['tecooledmct/full_presolder_geometry.py']!=digest:raise ValueError('Unaccounted generator revision')
    write(stage/'generator_versions.json',{'old_split_generator_sha256':digest,'current_independent_reaudit_sha256':sha(ROOT/'tecooledmct/full_presolder_geometry.py'),
        'difference':'exact three additional exterior/declared-skin audit lines; generator/PDE unmodified',
        'zero_original_generator_digest':'not captured at generation; exact parent mesh and current independent full reaudit retained',
        'refined_operator_status':'geometry audited only; NO coupled solve'})
    (stage/'split_generation.py.source').write_text(generation)
    for bench in ('oblique_benchmark_v3','curved_benchmark'):
        source=RAW/bench;summary=read(source/'summary.json');actual_sources(summary)
        if summary['benchmark_qualified']:raise ValueError('Expected retained recovery failure changed')
        for level in range(3):
            directory=source/f'level_{level}';execution=read(directory/'execution.json');actual_sources(execution)
            if execution['status']['exit_code']!=0 or not execution['solver_executed']:raise ValueError('Missing genuine benchmark solve')
            for filename,key in [('mesh.npz','mesh_sha256'),('case.sif','sif_sha256'),('elmer/fields_t0001.vtu','vtu_sha256')]:
                if sha(directory/filename)!=execution[key]:raise ValueError('Changed benchmark field/input')
            recovery=np.load(directory/'recovered_reference_fields.npz')
            if abs(recovery['cell_residual_w']).max()>1e-9:raise ValueError('Recovery cell balance failed')
        for p in source.rglob('*'):
            if p.is_file() and (p.suffix in ('.json','.sif','.log','.npz','.vtu') or p.parent.name=='source_snapshot'):
                relative=p.relative_to(RAW)
                if p.suffix=='.py':relative=Path(str(relative)+'.source')
                copy(p,stage/'benchmarks'/relative)
    for name in ('geometry_authority_audit_v2','environment_screen'):
        for p in (RAW/name).iterdir():
            if p.is_file():copy(p,stage/'diagnosis'/name/p.name)
    development=stage/'unaccepted_development';development.mkdir()
    for name in ('oblique_benchmark','oblique_benchmark_v2','geometry_authority_audit'):
        for p in (RAW/name).rglob('*'):
            if p.is_file() and (p.suffix in ('.json','.log','.sif') or p.parent.name=='source_snapshot'):
                relative=p.relative_to(RAW)
                if p.suffix=='.py':relative=Path(str(relative)+'.source')
                copy(p,development/relative)
    partial=RAW/'legacy_control/joint_interface_audit.failed_serialization.partial'
    if partial.exists():copy(partial,development/partial.name)
    verification=stage/'verification';verification.mkdir()
    logs=('full-presolder-all-tests.log','full-presolder-cli.log','full-presolder-geometry-demo.log',
          'full-presolder-geometry-reaudit.log','full-presolder-joint-audit.log','full-presolder-joint-audit-v2.log')
    if '106 passed' not in (ROOT/'outputs/full-presolder-all-tests.log').read_text():raise ValueError('Tests incomplete')
    for name in logs:copy(ROOT/'outputs'/name,verification/name)
    with (stage/'stage_heat_budgets.csv').open('w') as out:
        writer=csv.DictWriter(out,fieldnames=list(budget[0]));writer.writeheader();writer.writerows(budget)
    old_metrics=read(old/'cases/nitrogen_patch1/metrics.json');control=read(RAW/'legacy_control/metrics.json')
    if abs(control['die_mean_k']-old_metrics['die_mean_k'])>1e-5 or abs(control['voltage_v']-old_metrics['voltage_v'])>1e-7:
        raise ValueError('Same-physics control did not reproduce')
    zero=read(RAW/'zero_contact/joint_interface_audit.json');contact=read(RAW/'contact_hypothesis/joint_interface_audit.json')
    if zero['all_extra_interface_diagnostics_passed'] or not contact['all_extra_interface_diagnostics_passed']:
        raise ValueError('Interface diagnostic statuses changed')
    historical=[]
    for name in ('nitrogen_fine_verified','nitrogen_bath','nitrogen_feedthrough'):
        p=old/'unaccepted_development'/name/'metrics.json';r=read(p)
        if r['checks']['direct_bath_1pct'] or abs(r['direct_bath_relative_error'])<=.01:raise ValueError('Original failed gate changed')
        historical.append({'case':name,'raw_bath_relative_error':r['direct_bath_relative_error'],'gate_passed':False,'protected_metrics_sha256':sha(p)})
    summary={'status':'TESTED SCOPED EVIDENCE; assumed geometry only; full qualification incomplete',
             'general_recovery_qualified':False,'historical_raw_fine_gate_passed':False,
             'corrected_device_physics_qualified':False,'presolder_two_resolution_physics_qualified':False,
             'zero_contact_extra_interface_gate_passed':False,'contact_extra_interface_gate_passed':True,
             'old_1percent_gate_unchanged':True,'actual_coupled_cases':cases,'historical_failed_cases':historical,
             'source_geometry_checkpoint':'5fe8a663b06d0b8fcf41044114e5f4b4b443c746',
             'recovery_scope':'RT0 constrained balance is not independent accuracy; oblique bath1.08018%, curved P2 Cauchy7.24799% fail',
             'environment_scope':'fixed-field algebraic screen only; high-pressure1D gap results are model-form unqualified',
             'derived_3D_fields':'raw3D T/phi+mesh archived; reproduce q/J/Joule using frozen postprocessor; complete derived.vtu retained in ignored raw outputs',
             'publication_order':'independent source geometry committed/pushed first; this archive preserves earlier completed sandbox runs'}
    write(stage/'qualification.json',summary)
    sources=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'tecooledmct').glob('full_presolder_*.py'))]
    sources+=DOCS+['tests/test_full_presolder.py','data/full_presolder/reference_authorities.json','fem/archive_full_presolder_checkpoint.py']
    ledger={'source_sha256':{n:sha(ROOT/n) for n in sources},'artifact_sha256':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'preserved':preserved}
    write(stage/'checksums.json',ledger);stage.rename(DEST);verify()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    verify() if args.verify else publish()
