#!/usr/bin/env python3
"""Scoped immutable spatial audit + manufactured operator evidence, not release."""
import argparse,json,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tecooledmct.geometry_rebaseline import sha,write
from fem.archive_cold20 import copy,compress,small_tree
RAW=ROOT/'outputs/bath-spatial';DEST=ROOT/'fem/results/bath_spatial_diagnosis_20261030'
SOURCES=['tecooledmct/bath_spatial_'+x+'.py' for x in ['audit','boundary','benchmark','figures','mesh']]+[
 'data/bath_spatial/diagnostic_plan.json','data/bath_spatial/benchmark_plan.json','data/bath_spatial/benchmark_resource_amendment.json',
 'data/bath_spatial/refinement_plan.json','data/bath_spatial/solver_registry.json',
 'tests/test_bath_spatial.py','tests/test_bath_spatial_archive.py','docs/BATH_SPATIAL_DIAGNOSIS_CHECKPOINT.md','fem/archive_bath_spatial_diagnosis.py','BATH_SPATIAL_FLUX_AND_COMBINED_QUALIFICATION_WORK_ORDER.md']
def read(p):return json.loads(p.read_text())
def guard():
    subprocess.run([sys.executable,str(ROOT/'fem/archive_gate_refinement.py'),'--verify'],check=True)
    from reports.rev3_review.validate import verify_edition
    for label in ['20261030_a','20261030_b']:verify_edition(ROOT/'reports/rev3_review/editions'/label)
    approved=ROOT/'reports/rev3_review/editions/20261030_b/report.pdf'
    if sha(approved)!='d173a8ba952462e1b6bf857739406f58eeb8d5c82b900f9fc65b84d40573acc1':raise ValueError('Approved Rev3 edition changed')
    current=read(ROOT/'reports/rev3_review/current.json');edition=ROOT/current['edition'];verify_edition(edition)
    pdf=ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'
    if sha(pdf)!=current['pdf_sha256'] or sha(pdf)!=sha(edition/'report.pdf'):raise ValueError('Public report does not match a sealed edition')
    return {'prior_ledger':sha(ROOT/'fem/results/cold_bath_rev3_20261030/checksums.json'),'approved_Rev3_edition_B':sha(approved)}
def verify():
    d=read(DEST/'checksums.json')
    for group,base in [('sources',ROOT),('artifacts',DEST)]:
        for n,h in d[group].items():
            if sha(base/n)!=h:raise ValueError('Changed spatial evidence: '+n)
    if guard()!=d['preserved']:raise ValueError('Prior evidence or approved report changed')
    q=read(DEST/'qualification.json')
    if q['device_qualified'] or q['full_device_GCI'] or not q['manufactured_operator_target_passed']:raise ValueError('Incorrect scope')
    print('Verified independent spatial bath audit, real manufactured HeatSolver and unchanged approved Rev3; device NOT qualified')
def tree(src,dst):
    small_tree(src,dst)
    for p in src.rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        rel=p.relative_to(src);target=dst/rel
        if p.suffix=='.npz':copy(p,target)
        elif p.suffix in ['.msh','.vtu'] or p.parent.name=='elmer' and p.name.startswith('mesh.'):
            compress(p,target.with_name(target.name+'.gz'))
def publish():
    if DEST.exists():raise ValueError('Immutable archive; use --verify')
    preserved=guard();tests=(ROOT/'outputs/bath-spatial-tests-initial.log').read_text();match=re.search(r'(\d+) passed',tests)
    if not match or int(match[1])<139:raise ValueError('Full opt-in139+ tests incomplete')
    stage=ROOT/'outputs'/('bath-spatial-diagnosis-publication-'+str(time.time_ns()));stage.mkdir()
    from tecooledmct.bath_spatial_audit import CASES
    summary=read(RAW/'audit/summary.json');inputs={}
    for (label,mesh,case),a in zip(CASES,summary['cases']):
        e=read(case/'execution.json');r=read(case/'metrics.json')
        if a['mesh_sha256']!=e['mesh_sha256'] or a['field_sha256']!=e['vtu_sha256'] or abs(a['identity']['raw_bath_W']-r['hot_out_raw_gradient_w'])>5e-10 or abs(a['identity']['closure_error_W'])>1e-10:raise ValueError('Unverified actual audit')
        if a['new_solver_run'] or a['local_physical_error_known'] or a['qualified_recovery']:raise ValueError('False audit qualification')
        for n,h in a['source_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('Audit source changed')
        for p in (RAW/'audit'/label).iterdir():
            if p.suffix in ['.json','.npz']:copy(p,stage/'audit'/label/p.name)
        for p in [mesh/'mesh.npz',mesh/'manifest.json',case/'execution.json',case/'metrics.json',case/'case.sif',case/(e['field_source']+'.gz')]:inputs[str(p.relative_to(ROOT))]=sha(p)
    copy(RAW/'audit/summary.json',stage/'audit/summary.json');copy(RAW/'boundary_checks.json',stage/'boundary_checks.json')
    if not read(RAW/'boundary_checks.json')['passed']:raise ValueError('Boundary audit failed')
    for p in (RAW/'figures').iterdir():
        if p.is_file():copy(p,stage/'figures'/p.name)
    bench=read(RAW/'benchmark_v3/summary.json')
    if not bench['benchmark_qualified'] or bench['device_qualified'] or len(bench['cases'])!=5:raise ValueError('Manufactured benchmark not qualified')
    for row in bench['cases']:
        folder=RAW/'benchmark_v3'/('affine' if row['affine'] else 'normal_only' if row['normal_only'] else 'full'+str(row['level']))
        if row['solver_status']['exit_code'] or sha(folder/row['field_source'])!=row['field_sha256'] or sha(folder/'case.sif')!=row['sif_sha256']:raise ValueError('Changed genuine benchmark field')
        for n,h in row['source_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('Benchmark source changed')
    tree(RAW/'benchmark_v3',stage/'benchmark')
    for label in ['transverse1','transverse2']:
        mesh=RAW/(label+'_mesh');a=read(mesh/'audit.json')
        if not a['passed'] or sha(mesh/'mesh.npz')!=a['mesh_sha256'] or not all(a['fixed_cell_sets_byte_identical'].values()) or not read(mesh/'elmer_mapping.json')['passed']:raise ValueError('New geometry not independently verified')
        for n,h in a['source_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('Changed geometry producer')
        tree(mesh,stage/'geometry'/label)
    # Preserve input-index failure, preflight rejection and their actually completed fields.
    for label in ['benchmark','benchmark_v2']:tree(RAW/label,stage/'development'/label)
    for p in (ROOT/'outputs').glob('bath-spatial-*.log'):
        if 'coupled' not in p.name and 'mesh' not in p.name:copy(p,stage/'verification'/p.name)
    for n in SOURCES:copy(ROOT/n,stage/'source_snapshot'/(n+'.source'))
    write(stage/'input_references.json',inputs)
    write(stage/'report_at_checkpoint.json',{'approved_public_pdf_sha256':sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'),'current_pointer':read(ROOT/'reports/rev3_review/current.json'),'report_regenerated':False})
    write(stage/'qualification.json',{'manufactured_operator_target_passed':True,'actual_benchmark_executions':5,'archived_field_audits':4,'new_coupled_device_solves_in_this_archive':0,
        'device_qualified':False,'full_device_GCI':False,'original_bath_failures':'all retained FAILED; no reaction/recovery substitution','approved_Rev3':'UNCHANGED15 pages'})
    write(stage/'checksums.json',{'sources':{n:sha(ROOT/n) for n in SOURCES},'artifacts':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'preserved':preserved})
    stage.rename(DEST);verify()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args();verify() if a.verify else publish()
