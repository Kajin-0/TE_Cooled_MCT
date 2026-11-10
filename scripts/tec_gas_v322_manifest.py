"""Create or verify the V3.22 face-accounting and blocked-gate receipt."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'data/tec_gas_partition_20261110';M=D/'manifest.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');a=ap.parse_args()
 if a.verify:
  m=json.loads(M.read_text())
  for f,v in m['source_sha256'].items():assert sha(R/f)==v,f
  for f,v in m['artifact_sha256'].items():assert sha(R/f)==v,f
  print('PASS V3.22 source and artifacts',len(m['artifact_sha256']));return
 assert not M.exists();reg=json.loads((D/'registration.json').read_text());part=json.loads((D/'source_partition.json').read_text());v=json.loads((D/'report_verification.json').read_text())
 for f,h in reg['sources_sha256'].items():assert sha(R/f)==h,f
 assert v['all_48_page_contact_sheets_inspected'] and v['two_builds_pdf_and_rasters_identical']
 for obj in part['designs'].values():
  assert len(obj['faces'])==24
  for x in obj['faces']:
   assert abs(sum(x['partition_mm2'].values())-x['area_mm2'])<1e-8
   assert abs(x['source_vs_R3_contact_difference_mm2'])<1e-7
 assert '14 passed' in (D/'focused_tests_final.log').read_text()
 files=[p for p in D.rglob('*') if p.is_file() and p!=M]
 files += [R/x for x in ['tecooledmct/gas_partition_v322.py','scripts/tec_gas_v322_partition.py','scripts/tec_gas_v322_figure.py','scripts/tec_gas_v322_report_build.py','scripts/tec_gas_v322_manifest.py','tests/test_tec_gas_v322_partition.py','docs/TEC_CAVITY_GAS_FACE_PARTITION_20261110.md','reports/current/v322_gas_partition_section.tex','reports/current/reader_first_gas_partition_20261110.tex','reports/current/figures/v322_gas_face_partition.png','reports/current/figures/v322_gas_face_partition.pdf','reports/current/TEC_TO_Reader_First_Assessment_20261110_V322.pdf']]
 m={'UTC':datetime.now(timezone.utc).isoformat(),'status':'PASS ceramic face accounting and generic link controls; STOP complete physical gas mapping; zero coupled solves','source_sha256':reg['sources_sha256'],'artifact_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(files)}}
 M.write_text(json.dumps(m,indent=2)+'\n');print('PASS created V3.22 manifest',len(files))
if __name__=='__main__':main()
