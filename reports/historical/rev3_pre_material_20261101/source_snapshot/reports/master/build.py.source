"""Build/update ONE canonical Revision 3; no new report edition is created."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from .history import ROOT,PUBLIC,sha,preserve,verify_historical
from .validate import validate,verify_current

ACTIVE=ROOT/'reports/master/generated'
SOURCES=['reports/master/build.py','reports/master/figures.py','reports/master/validate.py',
         'reports/master/history.py','reports/master/render.py','reports/master/report.tex',
         'reports/master/references.json','reports/field_geometry.py',
         'reports/rev3_review/build.py','reports/rev3_review/latest_study.py',
         'tecooledmct/graded_tec.py','tecooledmct/material_profiles.py',
         'tecooledmct/nonlinear_tec.py','tecooledmct/integrated_reference.py',
         'tecooledmct/corrected_exchange.py','tecooledmct/exchange_geometry.py']

def write(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')

def prepare(out,*,figures=True):
    preserve()
    out=out.resolve()
    if out==ACTIVE or 'editions' in out.parts:raise ValueError('Prepare in a new outputs staging directory')
    if figures:
        if out.exists():raise ValueError('Choose a new staging directory')
        subprocess.run([str(ROOT/'fem/run.sh'),'python','-m','reports.master.figures','--out',str(out.relative_to(ROOT))],cwd=ROOT,check=True)
    shutil.copy2(ROOT/'reports/master/report.tex',out/'report.tex')
    d=json.loads((out/'report_inputs.json').read_text())
    if not d.get('figure_generators'):raise ValueError('Missing figure-generation source audit; regenerate figures')
    for name,h in d['figure_generators'].items():
        if sha(ROOT/name)!=h:raise ValueError('Figure generator changed; regenerate figures: '+name)
    d['generator']={name:sha(ROOT/name) for name in SOURCES}
    for name in SOURCES:
        target=out/'source_snapshot'/(name+'.source');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    d['derived']={name:sha(out/name) for name in ('report.tex','numerics.tex','master_numerics.tex','section.npz')}
    write(out/'report_inputs.json',d)
    env={**os.environ,'SOURCE_DATE_EPOCH':'1793318400','TZ':'UTC'}
    for i in range(3):
        with (out/f'build-{i+1}.log').open('w') as log:
            subprocess.run(['pdflatex','-halt-on-error','-interaction=nonstopmode','-file-line-error','report.tex'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    return validate(out)

def publish(out):
    preserve();out=out.resolve();v=json.loads((out/'validation.json').read_text());visual=json.loads((out/'visual_review.json').read_text())
    if out==ACTIVE or 'editions' in out.parts:raise ValueError('Publish only from reviewed staging, never historical or live assets')
    digest=sha(out/'report.pdf')
    if (not v['passed'] or not visual['all_pages_inspected'] or visual['pages']!=v['pages']
            or visual.get('inspected_pages')!=list(range(1,v['pages']+1))
            or visual['pdf_sha256']!=digest or v['pdf_sha256']!=digest):
        raise ValueError('Every final page must be visually reviewed and validated')
    reproduction=json.loads((out/'reproducibility.json').read_text())
    if (not reproduction['pdf_exact_bytes_reproduced'] or not reproduction['figures_exact_bytes_reproduced']
            or reproduction['pdf_sha256']!=digest):raise ValueError('Exact report and figure reproduction must pass')
    for name,h in json.loads((out/'report_inputs.json').read_text())['generator'].items():
        if sha(ROOT/name)!=h:raise ValueError('Generator changed after build: '+name)
    write(out/'live_master.json',{'mode':'continuous_rev3_master','canonical':str(PUBLIC.relative_to(ROOT)),
        'historical_original':'reports/historical/rev3_original.json','pdf_sha256':sha(out/'report.pdf')})
    # Retain the legacy manifest name solely for unchanged historical verifiers.
    write(out/'edition_checksums.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*'))
        if p.is_file() and p.name!='edition_checksums.json'})
    from reports.rev3_review.validate import verify_edition
    verify_edition(out)
    if ACTIVE.exists():
        if not (ACTIVE/'live_master.json').exists():raise ValueError('Refuse to overwrite an unknown directory')
        previous=ROOT/'outputs/rev3-master-previous-build'
        if previous.exists():shutil.rmtree(previous)
        ACTIVE.rename(previous)
    ACTIVE.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(out,ACTIVE)
    temporary=PUBLIC.with_suffix('.pdf.pending');shutil.copy2(out/'report.pdf',temporary);temporary.replace(PUBLIC)
    # A compatibility reference is a symlink to the ONE current public PDF.
    (ACTIVE/'report.pdf').unlink();(ACTIVE/'report.pdf').symlink_to(os.path.relpath(PUBLIC,ACTIVE))
    write(ROOT/'reports/rev3_review/current.json',{'edition':str(ACTIVE.relative_to(ROOT)),
        'mode':'continuous_rev3_master','canonical_pdf':str(PUBLIC.relative_to(ROOT)),
        'pdf_sha256':sha(PUBLIC),'review_draft':False,'full_qualification':False,
        'historical_original':'reports/historical/rev3_original.json'})
    verify_current();verify_historical()
    print('Published single canonical Revision 3 master:',PUBLIC)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reuse-figures',action='store_true');p.add_argument('--publish',action='store_true');a=p.parse_args()
    if a.publish:publish(a.out)
    else:print(prepare(a.out,figures=not a.reuse_figures))
