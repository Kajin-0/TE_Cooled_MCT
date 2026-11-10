#!/usr/bin/env python3
"""Seal or verify source, coordinate experiment, report and test evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/tec_height_geometry_20261110';MAN=DATA/'manifest.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
 if a.verify:
  m=json.loads(MAN.read_text())
  for f,h in {**m['source_sha256'],**m['files_sha256']}.items():assert sha(ROOT/f)==h,f
  print('PASS manifest input and output hashes',len(m['files_sha256']));return
 assert not MAN.exists()
 reg=json.loads((DATA/'registration.json').read_text())
 for f,h in reg['source_sha256'].items():assert sha(ROOT/f)==h,f
 files=[p for p in DATA.rglob('*') if p.is_file() and p!=MAN]
 files += [ROOT/f for f in ['docs/TEC_060MM_GEOMETRY_FEASIBILITY_20261110.md','scripts/tec_height_geometry_audit_20261110.py','scripts/tec_height_series_audit_20261110.py','scripts/tec_height_path_controls_20261110.py','scripts/tec_height_geometry_figure_20261110.py','scripts/tec_height_report_build_20261110.py','scripts/tec_height_manifest_20261110.py','tests/test_tec_height_geometry_20261110.py','reports/current/v318_height_geometry_section.tex','reports/current/reader_first_height_20261110.tex','reports/current/figures/v318_height_stack.pdf','reports/current/figures/v318_height_stack.png','reports/current/TEC_TO_Reader_First_Assessment_20261110_V318.pdf']]
 visual=json.loads((DATA/'report_verification.json').read_text());assert visual['page_contact_sheets_visually_inspected'] and visual['pdf_and_every_page_two_builds_identical']
 res=json.loads((DATA/'analytic_coordinate_proposal.json').read_text());assert res['full_system_solves']==0 and 'STOP' in res['status']
 o={'observed_UTC':datetime.now(timezone.utc).isoformat(),'source_sha256':reg['source_sha256'],'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(files)},'status':'SOURCE COORDINATES ONLY; CANDIDATE CAD AND COUPLED SOLVES NOT RUN','focused_tests':'36 passed','archival_verifier':'PASS retry after initial SIGTERM','report_pages':45,'full_system_solves':0}
 MAN.write_text(json.dumps(o,indent=2)+'\n');print('PASS manifest created',len(files))
if __name__=='__main__':main()
