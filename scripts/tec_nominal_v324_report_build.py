#!/usr/bin/env python3
"""Stage the additive reader-first report; never overwrites any published PDF."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reports/current';DATA=ROOT/'data/nominal_gas_coupler_20261110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 old=(HERE/'reader_first_nominal_reference_20261110.tex').read_text();new=(HERE/'reader_first_nominal_coupler_20261110.tex').read_text();addition='\\input{v324_nominal_gas_section.tex}\n'
 assert new.count(addition)==1 and new.replace(addition,'',1).replace('\\input{v324_height_geometry_corrected.tex}', '\\input{v318_height_geometry_section.tex}',1)==old
 original_section=(HERE/'v318_height_geometry_section.tex').read_text()
 expected_section=original_section.replace('\\section{Taller pellets: assembly feasibility}','\\section{Taller pellets: historical assembly feasibility}\n\\noindent\\textbf{Historical exploratory study; the original 0.50 mm reference is the active design.}').replace('figures/v318_height_stack.pdf','figures/v324_nominal_stage_geometry.pdf').replace('Source-coordinate plate elevations and their proposed translations. Legs are schematic representatives; no candidate solids, contact mesh, copper paths or gas field are depicted.','Original source 0.50 mm stack and actual P/N centers. The section shows two representative glyphs per stage; the plan views show all 58, 22 and 8 source legs. The alternative height study described here is archival.')
 assert (HERE/'v324_height_geometry_corrected.tex').read_text()==expected_section
 section=(HERE/'v324_nominal_gas_section.tex').read_text()
 for value in ('7.428','5.498','1.979','2.519773','1.188742','0.506549'):
  assert value in section
 env={**os.environ,'SOURCE_DATE_EPOCH':'1794182400','TZ':'UTC'};job='TEC_TO_Reader_First_Assessment_20261110_V324'
 for i in range(1,4):
  with (out/f'build-{i}.log').open('w') as f:subprocess.run(['pdflatex','-halt-on-error','-interaction=nonstopmode','-file-line-error','-jobname',job,'-output-directory',str(out),'reader_first_nominal_coupler_20261110.tex'],cwd=HERE,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 log=(out/'build-3.log').read_text(errors='replace');errors=[x for x in log.splitlines() if any(q in x for q in ('Overfull \\hbox','Overfull \\vbox','undefined references','Undefined control','LaTeX Error','Missing character','multiply defined','Rerun to get'))]
 if errors:raise ValueError('Typesetting failure: '+str(errors[:8]))
 pdf=out/(job+'.pdf');content=subprocess.check_output(['mutool','draw','-q','-F','txt',str(pdf)],stderr=subprocess.DEVNULL).decode()
 for word in ('frozen-boundary transport screen','custom-height assembly','matched-power thermal comparison','robustness','gas-face partition','native gas-face ownership','partial gas exchange','interstage','88','29/11/4'):
  if word.lower() not in ' '.join(content.lower().split()):raise ValueError('Missing substantive text: '+word)
 (out/'reader.txt').write_text(content)
 doc=json.loads(subprocess.check_output(['mutool','draw','-q','-F','stext.json',str(pdf)],stderr=subprocess.DEVNULL));pages=doc['pages'];assert 45<=len(pages)<=60
 for i,page in enumerate(pages):
  for b in page.get('blocks',[]):
   if b.get('type')!='text':continue
   for line in b.get('lines',[]):
    box=line['bbox'];x,y,w,h=(box[k] for k in ('x','y','w','h'))
    if x<0 or y<0 or x+w>596 or y+h>843:raise ValueError('Text out of page '+str(i+1))
 render=out/'renders';render.mkdir();subprocess.run(['mutool','draw','-q','-r','100','-o',str(render/'page-%02d.png'),str(pdf)],check=True,timeout=120)
 v=dict(status='PASS machine checks; visual review required',observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),pages=len(pages),pdf_sha256=sha(pdf),all_pages_rendered=len(list(render.glob('page-*.png')))==len(pages),original_body_identical_after_removing_addition_and_reverting_figure_correction=True,old_report_pdf_sha256=sha(HERE/'TEC_TO_Reader_First_Assessment_20261110_V323.pdf'),source_case_count=0,source_audit_count=0,full_system_solves=0,typesetting_errors=errors)
 assert v['all_pages_rendered'];(out/'validation.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
if __name__=='__main__':main()
