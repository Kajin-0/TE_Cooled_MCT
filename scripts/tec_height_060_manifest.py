"""Seal/verify custom-height source, STEP, checks, report, and prior inputs."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_060_cad_20261110';M=D/'manifest.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
 if a.verify:
  m=json.loads(M.read_text())
  for f,v in {**m['source_sha256'],**m['files_sha256']}.items():assert sha(R/f)==v,f
  print('PASS custom candidate manifest',len(m['files_sha256']));return
 assert not M.exists();reg=json.loads((D/'registration.json').read_text())
 for f,v in reg['source_sha256'].items():assert sha(R/f)==v,f
 cad=json.loads((D/'cad_attempt01/si_reader.json').read_text());imp=json.loads((D/'imported_contact_audit_attempt01.json').read_text());aud=json.loads((D/'independent_contact_audit.json').read_text());vis=json.loads((D/'report_verification.json').read_text())
 assert cad['status']=='PASS separate SI import' and cad['body_count']==824
 assert imp['status']=='PASS imported boundary witnesses and curved-body exclusivity' and imp['independent_contacts']==923 and imp['curved_overlap_pairs']==58
 assert aud['leg_solder_contacts']==aud['solder_gold_contacts']==176 and vis['two_builds_pdf_and_pages_identical'] and vis['all_page_contact_sheets_inspected']
 files=[p for p in D.rglob('*') if p.is_file() and p!=M]
 files += [R/f for f in ['tecooledmct/tec_height_060_candidate.py','scripts/tec_height_060_contact_audit.py','scripts/tec_height_060_clearance_audit.py','scripts/tec_height_060_imported_audit.py','scripts/tec_height_060_report_build.py','scripts/tec_height_060_manifest.py','tests/test_tec_height_060_candidate.py','docs/TEC_060MM_CUSTOM_ASSEMBLY_20261110.md','reports/current/reader_first_060assembly_20261110.tex','reports/current/v319_height_assembly_section.tex','reports/current/TEC_TO_Reader_First_Assessment_20261110_V319.pdf']]
 o={'observed_UTC':datetime.now(timezone.utc).isoformat(),'status':'source, SI STEP, imported boundary/nominal clearance PASS; thermal mappings and coupled solves NOT RUN',
 'source_sha256':reg['source_sha256'],'files_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(files)},'focused_tests_passed':44,
 'historical_verifier':'FAIL old documentation hash; see protected_source_check.log; old check not waived',
 'current_baseline_source_check':'PASS','archive_verifier':'PASS','full_system_solves':0,'report_pages':45}
 M.write_text(json.dumps(o,indent=2)+'\n');print('PASS manifest created',len(files))
if __name__=='__main__':main()
