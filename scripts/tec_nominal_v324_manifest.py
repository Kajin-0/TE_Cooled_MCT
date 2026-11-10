"""Seal original-only source gas subset, mapping, controls and additive report."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_coupler_20261110';M=D/'manifest.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--verify',action='store_true');args=a.parse_args()
 if args.verify:
  m=json.loads(M.read_text())
  for f,h in {**m['source_sha256'],**m['artifact_sha256']}.items():assert sha(R/f)==h,f
  print('PASS nominal V3.24 manifest:',len(m['artifact_sha256']),'artifacts');return
 assert not M.exists();reg=json.loads((D/'registration.json').read_text());faces=json.loads((D/'nominal_face_temperature_map.json').read_text());x=json.loads((D/'source_field_subset_exchange.json').read_text());a=json.loads((D/'independent_field_gas_audit.json').read_text());v=json.loads((D/'report_verification.json').read_text())
 for f,h in reg['source_sha256'].items():assert sha(R/f)==h,f
 assert faces['faces']==1840 and faces['lead_joint_faces_source_endpoint_proxy']==8 and faces['qualified_gas_BC_faces']==0
 assert x['full_system_solves']==0 and len(x['cells'])==a['cells']==752 and a['max_cell_abs_difference_W']<1e-15
 assert a['source_exchange_sha256']==sha(D/'source_field_subset_exchange.json') and all(abs(t['sum_W'])<1e-15 for t in x['summary'].values())
 assert v['all_51_pages_rendered_and_reviewed'] and v['two_builds_pdf_and_rasters_identical'] and '14 passed' in (D/'focused_tests_release2.log').read_text()
 files=[p for p in D.rglob('*') if p.is_file() and p!=M];files += [R/x for x in ['tecooledmct/nominal_gas_v324.py','scripts/tec_nominal_v324_subset.py','scripts/tec_nominal_v324_face_mapping.py','scripts/tec_nominal_v324_field_gas.py','scripts/tec_nominal_v324_residual_adapter.py','scripts/tec_nominal_v324_independent.py','scripts/tec_nominal_v324_figure.py','scripts/tec_nominal_v324_gas_figure.py','scripts/tec_nominal_v324_report_build.py','scripts/tec_nominal_v324_manifest.py','tests/test_tec_nominal_v324_gas.py','docs/NOMINAL_SOURCE_GAS_COUPLER_20261110.md','reports/current/v324_height_geometry_corrected.tex','reports/current/v324_nominal_gas_section.tex','reports/current/reader_first_nominal_coupler_20261110.tex','reports/current/figures/v324_nominal_stage_geometry.pdf','reports/current/figures/v324_nominal_stage_geometry.png','reports/current/figures/v324_nominal_gas_subset.pdf','reports/current/figures/v324_nominal_gas_subset.png','reports/current/TEC_TO_Reader_First_Assessment_20261110_V324.pdf']]
 o={'observed_UTC':datetime.now(timezone.utc).isoformat(),'status':'PASS original-only fixed-field gas subset and provisional contact mapping; STOP full gas boundary/temperature coupling','source_sha256':reg['source_sha256'],'artifact_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(files)}};M.write_text(json.dumps(o,indent=2)+'\n');print('PASS created nominal V3.24 manifest',len(files))
if __name__=='__main__':main()
