#!/usr/bin/env python3
"""Host-side PDF text/layout/render validation using the existing MuPDF tools."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_files(out):
    audit=json.loads((out/'report_inputs.json').read_text())
    for group in ('generator_sha256','input_sha256'):
        for name,digest in audit[group].items():
            if sha(ROOT/name)!=digest:raise ValueError('Report source/input changed; rebuild without --skip-figures: '+name)
    for name,record in audit['figures'].items():
        if sha(out/'figures'/name)!=record['sha256']:raise ValueError('Report figure changed: '+name)
    return audit


def main(out):
    pdf=out/'HgCdTe_Engineering_Assessment.pdf';audit=verify_files(out)
    if not audit['passed'] or audit['solver_executed_by_report'] or audit['baseline_evidence_modified']:raise ValueError('Report input audit failed')
    if not pdf.exists() or pdf.stat().st_size>15_000_000:raise ValueError('Missing/oversized PDF')
    log=(out/'HgCdTe_Engineering_Assessment.log').read_text(errors='replace')
    bad=[line for line in log.splitlines() if any(x in line for x in ('Overfull \\hbox','Overfull \\vbox','Undefined control','undefined references','LaTeX Error','not found'))]
    if bad:raise ValueError('LaTeX validation failed: '+'; '.join(bad[:8]))
    render=out/'render';render.mkdir(exist_ok=True)
    with (out/'render.log').open('w') as f:subprocess.run(['mutool','draw','-q','-r','100','-F','png','-o',str(render/'page-%02d.png'),str(pdf)],check=True,stdout=f,stderr=subprocess.STDOUT)
    text=subprocess.check_output(['mutool','draw','-q','-F','txt',str(pdf)],text=True,stderr=subprocess.DEVNULL);(out/'extracted_text.txt').write_text(text)
    if not all(s in text for s in ('not qualified','1.51','pre-solder','nitrogen_patch1','268.806','88')):raise ValueError('Required status/numeric/hardware text missing from PDF')
    structured=subprocess.check_output(['mutool','draw','-q','-F','stext.json',str(pdf)],stderr=subprocess.DEVNULL);(out/'page_structure.json').write_bytes(structured);pages=json.loads(structured)['pages'];stats=[]
    for page in pages:
        count=0;outside=[]
        for block in page.get('blocks',[]):
            if block.get('type')!='text':continue
            for line in block.get('lines',[]):
                count+=len(line.get('text','').strip());box=line['bbox']
                if box['x']<-.5 or box['y']<-.5 or box['x']+box['w']>595.276+.5 or box['y']+box['h']>841.89+.5:outside.append(line.get('text',''))
        stats.append({'characters':count,'outside_a4_media_box':len(outside)})
        if outside or count<200:raise ValueError('Clipped or near-blank text page: '+str(stats[-1]))
    # Render pixel/content checks use PIL in the existing scientific image.
    subprocess.run([str(ROOT/'fem/run.sh'),'python','reports/validate_report.py','--pixels','--out',str(Path('/work')/out.relative_to(ROOT))],cwd=ROOT,check=True)
    pixels=json.loads((out/'render_pixel_checks.json').read_text());assert len(pixels)==len(pages)
    result={'passed':True,'pdflatex_version':subprocess.check_output(['pdflatex','--version'],text=True).splitlines()[0],'pdf_sha256':sha(pdf),'pdf_bytes':pdf.stat().st_size,'pages':len(pages),'latex_overflow_errors':bad,'page_text_checks':stats,'render_pixel_checks':pixels,'input_audit_sha256':sha(out/'report_inputs.json'),'baseline_archive_commit':audit['integrity']['baseline_commit'],'full_g3b_qualified':False,'simulation_executed':False}
    (out/'report_validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: PDF compiled, rendered and validated:',len(pages),'pages;',pdf.stat().st_size,'bytes')


def pixels(out):
    import numpy as np
    from PIL import Image
    data=[]
    for f in sorted((out/'render').glob('page-*.png')):
        a=np.asarray(Image.open(f).convert('RGB'));ink=np.min(a,axis=2)<235;fraction=float(ink.mean());border=np.r_[ink[:4].ravel(),ink[-4:].ravel(),ink[:,:4].ravel(),ink[:,-4:].ravel()]
        if fraction<.01 or border.any():raise ValueError('Blank/clipped rendered page '+f.name)
        data.append({'page':f.name,'width':a.shape[1],'height':a.shape[0],'ink_fraction':fraction,'edge_ink':bool(border.any())})
    if not data:raise ValueError('No PDF pages rendered')
    (out/'render_pixel_checks.json').write_text(json.dumps(data,indent=2)+'\n')
    # Contact sheet for visual layout inspection, not a scientific figure.
    thumbs=[]
    for f in sorted((out/'render').glob('page-*.png')):
        im=Image.open(f).convert('RGB');im.thumbnail((248,351));thumbs.append(im)
    sheet=Image.new('RGB',(4*258,((len(thumbs)+3)//4)*371),'#c8c8c8')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%4)*258+5,(i//4)*371+5))
    sheet.save(out/'layout_contact_sheet.png')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--pixels',action='store_true');a=p.parse_args();(pixels if a.pixels else main)(a.out.resolve())
