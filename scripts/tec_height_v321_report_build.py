#!/usr/bin/env python3
"""Stage the additive reader-first report; never overwrites any published PDF."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reports/current';DATA=ROOT/'data/tec_height_robustness_20261110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 old=(HERE/'reader_first_height_coupled_20261110.tex').read_text();new=(HERE/'reader_first_height_robustness_20261110.tex').read_text();addition='\\input{v321_height_robustness_section.tex}\n'
 assert new.count(addition)==1 and new.replace(addition,'',1)==old
 section=(HERE/'v321_height_robustness_section.tex').read_text();summary=json.loads((DATA/'summary.json').read_text())
 assert summary['new_full_system_solves_with_audit'] == 2*summary['new_paired_scenarios']
 for row in summary['pairs']:
  for value in (row['nominal']['die_K'], row['custom_060']['die_K'], row['delta_die_K']):
   assert f"{value:.3f}" in section, (row['scenario'],value)
 env={**os.environ,'SOURCE_DATE_EPOCH':'1794182400','TZ':'UTC'};job='TEC_TO_Reader_First_Assessment_20261110_V321'
 for i in range(1,4):
  with (out/f'build-{i}.log').open('w') as f:subprocess.run(['pdflatex','-halt-on-error','-interaction=nonstopmode','-file-line-error','-jobname',job,'-output-directory',str(out),'reader_first_height_robustness_20261110.tex'],cwd=HERE,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 log=(out/'build-3.log').read_text(errors='replace');errors=[x for x in log.splitlines() if any(q in x for q in ('Overfull \\hbox','Overfull \\vbox','undefined references','Undefined control','LaTeX Error','Missing character','multiply defined','Rerun to get'))]
 if errors:raise ValueError('Typesetting failure: '+str(errors[:8]))
 pdf=out/(job+'.pdf');content=subprocess.check_output(['mutool','draw','-q','-F','txt',str(pdf)],stderr=subprocess.DEVNULL).decode()
 for word in ('frozen-boundary transport screen','custom-height assembly','matched-power thermal comparison','robustness','interstage','88','29/11/4'):
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
 v=dict(status='PASS machine checks; visual review required',observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),pages=len(pages),pdf_sha256=sha(pdf),all_pages_rendered=len(list(render.glob('page-*.png')))==len(pages),original_body_byte_identical_after_removing_one_input=True,old_report_pdf_sha256=sha(HERE/'TEC_TO_Reader_First_Assessment_20261110_V320.pdf'),source_case_count=summary['new_full_system_solves_with_audit'],source_audit_count=summary['new_full_system_solves_with_audit'],full_system_solves=summary['new_full_system_solves_with_audit'],typesetting_errors=errors)
 assert v['all_pages_rendered'];(out/'validation.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
if __name__=='__main__':main()
