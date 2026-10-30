#!/usr/bin/env python3
"""Publish only the tested independent source geometry, never device physics."""
import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'fem/results/geometry_rebaseline_20261030'
FILES=['tecooledmct/geometry_registry.py','tecooledmct/geometry_source_trace.py',
       'tecooledmct/geometry_rebaseline.py','tecooledmct/geometry_rebaseline_views.py',
       'tecooledmct/geometry_measurements.py',
       'tests/test_geometry_rebaseline.py','data/geometry_rebaseline/reference_v1.json',
       'data/geometry_rebaseline/vigo_outline_trace.json','GEOMETRY_SOURCE_OF_TRUTH_SPEC.md',
       'docs/GEOMETRY_SOURCE_REBASELINE_20261030.md','fem/archive_geometry_rebaseline.py']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preserved():
    # Compare against the existing HEAD bytes as well as all archived ledgers.
    paths=['reports/generated/HgCdTe_Engineering_Assessment.pdf']
    baseline={}
    for name in paths:
        raw=subprocess.check_output(['git','show','fcbdaa45:'+name],cwd=ROOT)
        digest=hashlib.sha256(raw).hexdigest()
        if sha(ROOT/name)!=digest:raise ValueError('Changed protected report')
        baseline[name]=digest
    for archive in ('g3b_checkpoint_20261029','flux_presolder_checkpoint_20261030'):
        base=ROOT/'fem/results'/archive; ledger=json.loads((base/'checksums.json').read_text())
        for group,parent in [('source_sha256',ROOT),('document_sha256',ROOT),('artifact_sha256',base)]:
            for name,digest in ledger.get(group,{}).items():
                if sha(parent/name)!=digest:raise ValueError('Changed protected evidence: '+name)
        baseline[archive]=sha(base/'checksums.json')
    return baseline


def verify():
    ledger=json.loads((DEST/'checksums.json').read_text())
    for group,parent in [('source_sha256',ROOT),('artifact_sha256',DEST)]:
        for name,digest in ledger[group].items():
            if sha(parent/name)!=digest:raise ValueError('Geometry checkpoint changed: '+name)
    if preserved()!=ledger['preserved']:raise ValueError('Baseline proof changed')
    print('Verified independent geometry source/artifact ledger; prior evidence preserved')


def publish():
    if DEST.exists():raise ValueError('Immutable archive already exists')
    src=ROOT/'outputs/geometry-rebaseline-v2'
    result=json.loads((src/'geometry_audit.json').read_text())
    for name,digest in result['source_sha256'].items():
        if sha(ROOT/'tecooledmct'/name)!=digest:raise ValueError('Changed execution source')
    if not result['actual_mesh']['partial_header_mesh_passed']:raise ValueError('Mesh failed')
    if result['identity']['verified_commercial_assembly']:raise ValueError('False product claim')
    measured=json.loads((src/'measured_dimensions.json').read_text())
    route=json.loads((src/'routing_preview.json').read_text())
    if not measured['geometry_dimensions_passed'] or measured['mesh_sha256']!=sha(src/'mesh.npz'):
        raise ValueError('Actual dimension audit incomplete')
    if measured['measurement_source_sha256']!=sha(ROOT/'tecooledmct/geometry_measurements.py'):
        raise ValueError('Changed measurement source')
    if route['renderer_sha256']!=sha(ROOT/'tecooledmct/geometry_rebaseline_views.py'):
        raise ValueError('Changed renderer source')
    log=ROOT/'outputs/geometry-rebaseline-all-tests.log'
    if '110 passed' not in log.read_text() or ' failed' in log.read_text():raise ValueError('Full opt-in tests incomplete')
    before=preserved();DEST.mkdir(parents=True)
    for name in ('mesh.npz','registry_snapshot.json','geometry_audit.json','source_overlay.png',
                 'pin_views.png','actual_mesh_orthographic.png','actual_mesh_section.png','routing_preview.json',
                 'measured_dimensions.json'):
        shutil.copy2(src/name,DEST/name)
    with (DEST/'reference.step.gz').open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as out:
        out.write((src/'reference.step').read_bytes())
    logs=DEST/'verification';logs.mkdir()
    for name in ('geometry-rebaseline-v1.log','geometry-rebaseline-v2.log','geometry-rebaseline-views.log',
                 'geometry-rebaseline-all-tests.log','geometry-rebaseline-measurements.log',
                 'full-presolder-cli.log','full-presolder-geometry-demo.log'):
        shutil.copy2(ROOT/'outputs'/name,logs/name)
    provenance={'status':'verified independent source geometry only; full revised physics NOT RUN',
                'development_failure':'v1 surface-union returned3 connected faces; corrected3D union in v2; retained log',
                'source_pdfs':'original vendor bytes in ignored outputs, selected numeric trace only published',
                'runtime_image':subprocess.check_output(['docker','image','inspect','tecooledmct-fem:26.2.1','--format','{{.Id}}'],text=True).strip(),
                'limits':'existing wrapper4 CPU/8GiB, network none; no software installation',
                'previous_report_pages':15,'revised_Elmer_physics_executed':False}
    (DEST/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    ledger={'source_sha256':{n:sha(ROOT/n) for n in FILES},
            'artifact_sha256':{str(p.relative_to(DEST)):sha(p) for p in sorted(DEST.rglob('*')) if p.is_file()},
            'preserved':before}
    (DEST/'checksums.json').write_text(json.dumps(ledger,indent=2)+'\n');verify()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true')
    args=parser.parse_args();verify() if args.verify else publish()
