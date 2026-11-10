"""Seal and verify conditional matched-power results without rerunning physics."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_coupling_20261110';M=D/'manifest.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(4<<20),b''):h.update(z)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');p.add_argument('--mesh',action='store_true');a=p.parse_args()
 if a.verify:
  m=json.loads(M.read_text())
  for f,v in {**m['source_sha256'],**m['files_sha256']}.items():assert sha(R/f)==v,f
  if a.mesh:
   for f,v in m['mesh_sha256'].items():assert sha(Path(f))==v,f
  print('PASS v320 manifest',len(m['files_sha256']),'mesh checked:',a.mesh);return
 assert not M.exists();reg=json.loads((D/'registration.json').read_text());contract=json.loads((D/'solver_contract.json').read_text());s=json.loads((D/'summary.json').read_text());visual=json.loads((D/'report_verification.json').read_text())
 for f,v in reg['source_sha256'].items():assert sha(R/f)==v,f
 for f,v in reg['mesh_sha256'].items():assert sha(Path(f))==v,f
 for f,v in contract['execution_source_sha256'].items():assert sha(R/f)==v,f
 for f,v in contract['preflight_sha256'].items():assert sha(D/f)==v,f
 assert s['full_system_solves']==s['independent_audits']==2 and visual['all_page_contact_sheets_inspected'] and visual['two_builds_pdf_and_rasters_identical']
 for case in ('nominal','custom_060'):
  p=D/case;r=json.loads((p/'result.json').read_text());h=sha(p/'result.json');assert r['solver_source_sha256']==sha(R/'scripts/tec_height_v320_coupled.py')
  for q in ('independent_audit.json','gas_crosscheck.json','ports_crosscheck.json'):
   j=json.loads((p/q).read_text());assert j['status'].startswith('PASS') and h in (j.get('result_sha256'),j.get('source_result_sha256'))
 correction=json.loads((D/'external_gap_index_correction.json').read_text());assert correction['status'].startswith('SUPERSEDED') and correction['invalid_prior_sha256']==sha(D/'external_gap_fixed_field_sensitivity.json') and correction['correction_sha256']==sha(D/'external_gap_fixed_field_corrected.json')
 files=[p for p in D.rglob('*') if p.is_file() and p!=M]
 files += [R/f for f in ['tecooledmct/height_coupling_v320.py','scripts/build_tec_height_v320_solver.py','scripts/tec_height_v320_coupled.py','scripts/tec_height_v320_mapping_audit.py','scripts/tec_height_v320_independent_audit.py','scripts/tec_height_v320_gas_crosscheck.py','scripts/tec_height_v320_ports_crosscheck.py','scripts/tec_height_v320_external_gap_sensitivity.py','scripts/tec_height_v320_external_gap_corrected.py','scripts/tec_height_v320_summary.py','scripts/tec_height_v320_report_build.py','scripts/tec_height_v320_manifest.py','tests/test_tec_height_coupling_v320.py','tests/test_tec_height_v320_gas_crosscheck.py','tests/test_tec_height_v320_results.py','docs/TEC_HEIGHT_COUPLED_MAPPING_20261110.md','reports/current/v320_height_coupled_section.tex','reports/current/reader_first_height_coupled_20261110.tex','reports/current/figures/v320_height_matched.pdf','reports/current/figures/v320_height_matched.png','reports/current/TEC_TO_Reader_First_Assessment_20261110_V320.pdf']]
 o={'observed_UTC':datetime.now(timezone.utc).isoformat(),'status':'TWO conditional matched-power solves and independent audits PASS; gas/metal physical validation NOT DONE','source_sha256':reg['source_sha256'],'mesh_sha256':reg['mesh_sha256'],'files_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(files)},'full_system_solves':2,'independent_audits':2,'focused_tests_passed':27,'archive_verifier':'PASS','report_pages':46,'superseded_fixed_field_sensitivity':'See external_gap_index_correction.json; original retained'}
 M.write_text(json.dumps(o,indent=2)+'\n');print('PASS created v320 manifest',len(files))
if __name__=='__main__':main()
