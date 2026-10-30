"""Standalone scientific reader, content, layout and live-master provenance gates."""
import json
import re
import subprocess
import unicodedata
from pathlib import Path

from .history import ROOT,PUBLIC,sha,verify_historical
from reports.rev3_review.validate import provenance,verify_edition
from reports.validate_report import validate_reader_text,decode_pdf_metadata


def reader(text):
    validate_reader_text(text)
    s=' '.join(unicodedata.normalize('NFKC',text).casefold().split())
    forbidden=r'\b(?:codex|agents?|todo|github|checkpoints?|usernames?|ci)\b|/home/|\boutputs/|\.(?:py|json|npz|vtu|tex|csv|msh|step)\b|\breview draft\b|\brev(?:ision)?\s*4\b'
    if re.search(forbidden,s):raise ValueError('Internal/administrative identifier in public reader content')
    if 'revision 3' not in s:raise ValueError('Wrong canonical report revision')
    return s


def required_content(text):
    s=reader(text)
    for value in ('hypothetical reference article','numerical release incomplete',
                  '88','216','177','647,657','265.616','232.209','1.15193',
                  '52','63','0.04043','1.069','1.2885','1.2907','6.48%',
                  '40','300','390','quarter','stepped','native','not implemented',
                  'radiation','gas','sensitivity','fail','references'):
        if value not in s:raise ValueError('Required scientific evidence missing: '+value)
    return True


def validate(out):
    d=json.loads((out/'report_inputs.json').read_text());provenance(d)
    for name,h in d['inputs'].items():
        if sha(ROOT/name)!=h:raise ValueError('Changed report evidence: '+name)
    for name,h in d['figures'].items():
        if sha(out/'figures'/name)!=h:raise ValueError('Changed report figure: '+name)
    log=(out/'build-3.log').read_text(errors='replace')
    errors=[line for line in log.splitlines() if any(v in line for v in (
        'Overfull \\hbox','Overfull \\vbox','undefined references','Undefined control',
        'LaTeX Error','Missing character','multiply defined','Rerun to get'))]
    if errors:raise ValueError('Unresolved typesetting errors: '+'; '.join(errors[:8]))
    pdf=out/'report.pdf'
    text=subprocess.check_output(['mutool','draw','-q','-F','txt',str(pdf)],stderr=subprocess.DEVNULL).decode()
    required_content(text);(out/'reader.txt').write_text(text)
    metadata=decode_pdf_metadata(subprocess.check_output(['mutool','show',str(pdf),'trailer/Info']).decode())
    validate_reader_text(metadata)
    if re.search(r'/Author\s*\((?!\s*\))',metadata):raise ValueError('Personal PDF author metadata')
    if re.search(r'codex|/home/|github|review draft',metadata,re.I):raise ValueError('Administrative PDF metadata')
    (out/'metadata.txt').write_text(metadata)
    structured=subprocess.check_output(['mutool','draw','-q','-F','stext.json',str(pdf)],stderr=subprocess.DEVNULL)
    (out/'page_structure.json').write_bytes(structured);pages=json.loads(structured)['pages'];stats=[]
    if not 18<=len(pages)<=40:raise ValueError('Unexpected master pagination')
    for i,page in enumerate(pages):
        count=0
        for block in page.get('blocks',[]):
            if block.get('type')!='text':continue
            for line in block.get('lines',[]):
                count+=len(line.get('text','').strip());b=line['bbox']
                if b['x']<0 or b['y']<0 or b['x']+b['w']>596 or b['y']+b['h']>843:
                    raise ValueError('Text outside A4 on page '+str(i+1))
        if count<180:raise ValueError('Near blank page '+str(i+1))
        stats.append(count)
    render=out/'renders';render.mkdir(exist_ok=True)
    for p in render.glob('page-*.png'):p.unlink()
    subprocess.run(['mutool','draw','-q','-r','110','-o',str(render/'page-%02d.png'),str(pdf)],check=True)
    subprocess.run([str(ROOT/'fem/run.sh'),'python','-m','reports.master.render',
                    '--out',str(out.relative_to(ROOT))],cwd=ROOT,check=True)
    result={'passed':True,'report_revision':3,'review_draft':False,'full_qualification':False,
        'OEM_validated':False,'pages':len(pages),'pdf_sha256':sha(pdf),
        'all_pages_rendered':len(list(render.glob('page-*.png')))==len(pages),
        'page_text_characters':stats,'reader_and_metadata_checked':True,
        'corrected_field_provenance_checked':True,'typesetting_errors':[],
        'render_pixel_checks':json.loads((out/'render_pixel_checks.json').read_text()),
        'historical_snapshot_verified':verify_historical(),
        'visual_inspection':'required separately for every rendered page before canonical publication'}
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def verify_current():
    verify_historical()
    current=json.loads((ROOT/'reports/rev3_review/current.json').read_text())
    if current.get('mode')!='continuous_rev3_master' or current['review_draft']:
        raise ValueError('Current report is not the canonical live master')
    out=ROOT/current['edition']
    verify_edition(out)
    if sha(PUBLIC)!=current['pdf_sha256'] or sha(out/'report.pdf')!=sha(PUBLIC):
        raise ValueError('Canonical master/reference mismatch')
    required_content((out/'reader.txt').read_text())
    d=json.loads((out/'report_inputs.json').read_text())
    if d['master_scope']['new_enclosed_3D_field'] or d['master_scope']['full_native_cavity_visibility']:
        raise ValueError('False physical scope')
    return True


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);p.add_argument('--current',action='store_true');a=p.parse_args()
    print(verify_current() if a.current else validate(a.out.resolve()))
