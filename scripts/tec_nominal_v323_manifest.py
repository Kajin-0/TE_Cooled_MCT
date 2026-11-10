"""Seal nominal-only face inventory, reference and report artifacts."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_ports_20261110';M=D/'manifest.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');a=ap.parse_args()
 if a.verify:
  m=json.loads(M.read_text())
  for f,v in {**m['source_sha256'],**m['artifact_sha256']}.items():assert sha(R/f)==v,f
  print('PASS original nominal manifest:',len(m['artifact_sha256']),'artifacts');return
 assert not M.exists();reg=json.loads((D/'registration.json').read_text());ref=json.loads((D/'nominal_reference.json').read_text());audit=json.loads((D/'independent_ports_audit_v2.json').read_text());budget=json.loads((D/'nominal_budget_audit.json').read_text());v=json.loads((D/'report_verification.json').read_text())
 for f,h in reg['source_sha256'].items():assert sha(R/f)==h,f
 for item in ref['operator_sources'].values():assert sha(R/item['path'])==item['sha256']
 for item in ('original_STEP','historical_v311_different_proxy'):assert sha(R/ref[item]['path'])==ref[item]['sha256']
 assert audit['faces']==1840 and audit['implemented_gas_face_BCs']==0 and audit['unresolved_semantic_faces']==8
 assert abs(budget['global_energy_residual_W'])<1e-8 and v['all_49_pages_rendered_and_reviewed'] and v['two_builds_pdf_and_rasters_identical']
 assert '9 passed' in (D/'focused_tests_final2.log').read_text()
 files=[p for p in D.rglob('*') if p.is_file() and p!=M];files += [R/x for x in ['scripts/tec_nominal_v323_ports.py','scripts/tec_nominal_v323_audit.py','scripts/tec_nominal_v323_budget.py','scripts/tec_nominal_v323_regime.py','scripts/tec_nominal_v323_report_build.py','scripts/tec_nominal_v323_manifest.py','tests/test_tec_nominal_v323_ports.py','docs/NOMINAL_CAVITY_PORTS_AND_REGIME_20261110.md','reports/current/v323_nominal_gas_ports_section.tex','reports/current/reader_first_nominal_reference_20261110.tex','reports/current/TEC_TO_Reader_First_Assessment_20261110_V323.pdf']]
 m={'observed_UTC':datetime.now(timezone.utc).isoformat(),'status':'PASS nominal CSG face-ownership readback and saved-budget audit; STOP native gas physical closure; no new coupled solve','source_sha256':reg['source_sha256'],'artifact_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(files)}};M.write_text(json.dumps(m,indent=2)+'\n');print('PASS created nominal manifest',len(files))
if __name__=='__main__':main()
