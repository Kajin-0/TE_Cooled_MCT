"""Seal and verify V3.21 sources, results, report, and preregistered input hashes."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_robustness_20261110';M=D/'manifest.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');args=ap.parse_args()
 if args.verify:
  m=json.loads(M.read_text())
  for f,h in m['files_sha256'].items():assert sha(R/f)==h,f
  print('PASS V3.21 manifest',len(m['files_sha256']));return
 assert not M.exists()
 contract=json.loads((D/'contract.json').read_text());s=json.loads((D/'summary.json').read_text());v=json.loads((D/'report_verification.json').read_text())
 for f,h in contract['source_sha256'].items():assert sha(R/f)==h,f
 assert s['new_full_system_solves_with_audit'] == 2*s['new_paired_scenarios'] <= contract['max_full_system_solves']
 assert v['all_page_contact_sheets_inspected'] and v['two_builds_pdf_and_rasters_identical']
 for z in s['pairs']:
  if not z['new_solves']:continue
  for var in ('nominal','custom_060'):
   p=D/'cases'/z['scenario']/var;h=sha(p/'result.json')
   for a in ('independent_audit.json','ports_crosscheck.json'):
    j=json.loads((p/a).read_text());assert j['status'].startswith('PASS') and h in (j.get('result_sha256'),j.get('source_result_sha256'))
 files=[p for p in D.rglob('*') if p.is_file() and p!=M]
 files += [R/x for x in ['docs/TEC_HEIGHT_ROBUSTNESS_20261110.md','reports/current/v321_height_robustness_section.tex','reports/current/reader_first_height_robustness_20261110.tex','reports/current/figures/v321_height_robustness.pdf','reports/current/figures/v321_height_robustness.png','reports/current/TEC_TO_Reader_First_Assessment_20261110_V321.pdf','tests/test_tec_height_v321_robustness.py','tests/test_tec_height_v321_results.py']]
 files += sorted((R/'scripts').glob('tec_height_v321_*.py'))
 o={'observed_UTC':datetime.now(timezone.utc).isoformat(),'status':'conditional paired samples; native gas and metal field NOT qualified','full_system_solves':s['new_full_system_solves_with_audit'],'paired_scenarios':s['new_paired_scenarios'],'incomplete':s['incomplete'],'files_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(files)}}
 M.write_text(json.dumps(o,indent=2)+'\n');print('PASS sealed V3.21',len(files))
if __name__=='__main__':main()
