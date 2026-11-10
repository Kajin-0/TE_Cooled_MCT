#!/usr/bin/env python3
"""Stage the additive reader-first report; never overwrites any published PDF."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reports/current';DATA=ROOT/'data/tec_height_060_cad_20261110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 old=(HERE/'reader_first_height_20261110.tex').read_text();new=(HERE/'reader_first_060assembly_20261110.tex').read_text();addition='\\input{v319_height_assembly_section.tex}\n'
 assert new.count(addition)==1 and new.replace(addition,'',1)==old
 section=(HERE/'v319_height_assembly_section.tex').read_text(); reader=json.loads((DATA/'cad_attempt01/si_reader.json').read_text());brep=json.loads((DATA/'imported_contact_audit_attempt01.json').read_text());clearance=json.loads((DATA/'clearance_audit.json').read_text())
 assert reader['body_count']==824 and brep['independent_contacts']==923 and brep['curved_overlap_pairs']==58
 assert clearance['radial_shell_clearance_lower_bound_mm']>.785 and clearance['roof_clearance_lower_bound_mm']>3.185
 for text in ('824','556','176 + 176','0.160','923','1,250','0.785','3.186','1.783'):
  assert text in section,text
 env={**os.environ,'SOURCE_DATE_EPOCH':'1794182400','TZ':'UTC'};job='TEC_TO_Reader_First_Assessment_20261110_V319'
 for i in range(1,4):
  with (out/f'build-{i}.log').open('w') as f:subprocess.run(['pdflatex','-halt-on-error','-interaction=nonstopmode','-file-line-error','-jobname',job,'-output-directory',str(out),'reader_first_060assembly_20261110.tex'],cwd=HERE,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 log=(out/'build-3.log').read_text(errors='replace');errors=[x for x in log.splitlines() if any(q in x for q in ('Overfull \\hbox','Overfull \\vbox','undefined references','Undefined control','LaTeX Error','Missing character','multiply defined','Rerun to get'))]
 if errors:raise ValueError('Typesetting failure: '+str(errors[:8]))
 pdf=out/(job+'.pdf');content=subprocess.check_output(['mutool','draw','-q','-F','txt',str(pdf)],stderr=subprocess.DEVNULL).decode()
 for word in ('frozen-boundary transport screen','taller pellets: assembly feasibility','custom-height assembly','923','1,250','89','88','29/11/4'):
  if word.lower() not in ' '.join(content.lower().split()):raise ValueError('Missing substantive text: '+word)
 (out/'reader.txt').write_text(content)
 doc=json.loads(subprocess.check_output(['mutool','draw','-q','-F','stext.json',str(pdf)],stderr=subprocess.DEVNULL));pages=doc['pages'];assert 45<=len(pages)<=58
 for i,page in enumerate(pages):
  for b in page.get('blocks',[]):
   if b.get('type')!='text':continue
   for line in b.get('lines',[]):
    box=line['bbox'];x,y,w,h=(box[k] for k in ('x','y','w','h'))
    if x<0 or y<0 or x+w>596 or y+h>843:raise ValueError('Text out of page '+str(i+1))
 render=out/'renders';render.mkdir();subprocess.run(['mutool','draw','-q','-r','100','-o',str(render/'page-%02d.png'),str(pdf)],check=True,timeout=120)
 v=dict(status='PASS machine checks; visual review required',observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),pages=len(pages),pdf_sha256=sha(pdf),all_pages_rendered=len(list(render.glob('page-*.png')))==len(pages),original_body_byte_identical_after_removing_one_input=True,old_report_pdf_sha256=sha(HERE/'TEC_TO_Reader_First_Assessment_20261110_V318.pdf'),source_case_count=1,source_audit_count=3,full_system_solves=0,typesetting_errors=errors)
 assert v['all_pages_rendered'];(out/'validation.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
if __name__=='__main__':main()
