#!/usr/bin/env python3
"""Seal/verify original-only V3.25 evidence; never alter registered inputs."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json
R=Path(__file__).resolve().parents[1]; D=R/'data/nominal_gas_p1_20261111'; M=D/'manifest.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--verify',action='store_true'); p.add_argument('--mesh',action='store_true'); a=p.parse_args()
 if a.verify:
  m=json.loads(M.read_text())
  for name,h in m['artifact_sha256'].items(): assert sha(R/name)==h, name
  for name,h in m['source_sha256'].items(): assert sha(R/name)==h, name
  if a.mesh:
   for name,h in m['mesh_sha256'].items(): assert sha(Path(name))==h,name
  print('PASS V3.25 manifest',len(m['artifact_sha256']),'artifacts');return
 assert not M.exists()
 reg=json.loads((D/'registration.json').read_text()); oc=json.loads((D/'operator_contract_release.json').read_text()); cc=json.loads((D/'coupled_contract.json').read_text())
 for items in (reg['source_sha256'],oc['executed_source_sha256'],cc['inputs_sha256']):
  for name,h in items.items(): assert sha(R/name)==h,name
 assert sha(D/'executed_solver.py.source')==cc['executed_source_sha256']
 op=sha(D/'p1_operator.json'); read=json.loads((D/'independent_readback.json').read_text()); assert read['operator_sha256']==op and read['pieces']==6109 and read['max_single_pair_conservation_W']<1e-12
 result=sha(D/'coupled_attempt01/result.json'); audit=json.loads((D/'coupled_attempt01/independent_audit.json').read_text()); port=json.loads((D/'coupled_attempt01/ports_crosscheck.json').read_text())
 assert audit['source_result_sha256']==port['source_result_sha256']==result
 assert max(abs(audit[x]) for x in ['max_stage_residual_W','global_residual_W','power_residual_W'])<1e-8 and abs(audit['gas_global_W'])<1e-12
 v=json.loads((D/'report_verification.json').read_text()); assert v['pages']==52 and v['all_52_raster_pages_identical'] and v['all_pages_visual_contact_sheet_reviewed'] and v['new_page_42_and_corrected_figure_page_35_individually_inspected']
 assert '20 passed' in (D/'focused_tests_release.log').read_text()
 files=[p for p in D.rglob('*') if p.is_file() and p!=M and '__pycache__' not in str(p)]
 files += [R/x for x in ['tecooledmct/nominal_gas_p1_v325.py','tecooledmct/nominal_gas_p1_coupler_v325.py','scripts/tec_nominal_v325_operator.py','scripts/tec_nominal_v325_readback.py','scripts/tec_nominal_v325_coupled.py','scripts/tec_nominal_v325_fem_preflight.py','scripts/tec_nominal_v325_coupled_audit.py','scripts/tec_nominal_v325_coverage.py','scripts/tec_nominal_v325_figure.py','scripts/tec_nominal_v325_report_build.py','scripts/tec_nominal_v325_manifest.py','tests/test_nominal_gas_p1_v325.py','tests/test_nominal_gas_p1_coupler_v325.py','tests/test_nominal_gas_p1_results_v325.py','docs/NOMINAL_P1_GAS_COUPLING_20261111.md','reports/current/v325_nominal_p1_section.tex','reports/current/reader_first_nominal_p1_20261111.tex','reports/current/figures/v325_nominal_p1_gas.pdf','reports/current/figures/v325_nominal_p1_gas.png','reports/current/TEC_TO_Reader_First_Assessment_20261111_V325.pdf']]
 o={'observed_UTC':datetime.now(timezone.utc).isoformat(),'status':'PASS partial gas operator and one conditional coupled solve; STOP complete-cavity physical qualification','source_sha256':reg['source_sha256'],'mesh_sha256':reg['mesh_sha256'],'artifact_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(files)}}
 M.write_text(json.dumps(o,indent=2)+'\n');print('PASS sealed V3.25',len(files),'artifacts')
if __name__=='__main__': main()
