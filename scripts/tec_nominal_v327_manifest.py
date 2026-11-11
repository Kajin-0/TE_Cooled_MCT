#!/usr/bin/env python3
"""Seal original-only V3.27 visibility and coupled partial-cavity evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_visibility_v327_20261111';M=D/'manifest.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');p.add_argument('--mesh',action='store_true');a=p.parse_args()
 if a.verify:
  m=json.loads(M.read_text())
  for key in ('source_sha256','artifact_sha256'):
   for name,h in m[key].items():assert sha(R/name)==h,name
  if a.mesh:
   for name,h in m['mesh_sha256'].items():assert sha(name)==h,name
  print('PASS V3.27 manifest',len(m['artifact_sha256']),'artifacts');return
 assert not M.exists();reg=json.loads((D/'registration.json').read_text());g=json.loads((D/'geometry_receipt.json').read_text());c=json.loads((D/'coupled_contract.json').read_text());gate=json.loads((D/'coupled_gate.json').read_text())
 for group in (reg['source_sha256'],g['source_sha256'],c['inputs_sha256']):
  for name,h in group.items():assert sha(R/name)==h,name
 for name,h in gate['evidence_sha256'].items():assert sha(D/name)==h,name
 assert sha(R/'scripts/tec_nominal_v327_coupled_audit.py')==gate['audit_source_sha256'];assert sha(D/'executed_solver.py.source')==c['executed_source_sha256'];assert sha(D/'die_window_visibility.json')==g['result_sha256']
 v=json.loads((D/'die_window_visibility.json').read_text());i=json.loads((D/'independent_readback.json').read_text());assert i['source_visibility_sha256']==sha(D/'die_window_visibility.json') and i['status'].startswith('PASS') and len(v['patches'])==i['patches']==301 and abs(v['area_closure_mm2'])<1e-5 and v['V325_face_ids_disjoint'] and i['max_old_column_top_z_mm']<i['new_column_bottom_z_mm']
 C=D/'coupled_attempt01';r=json.loads((C/'result.json').read_text());audit=json.loads((C/'independent_audit.json').read_text());port=json.loads((C/'ports_crosscheck.json').read_text());node=json.loads((D/'node_label_audit.json').read_text());h=sha(C/'result.json');assert audit['source_result_sha256']==port['source_result_sha256']==node['source_result_sha256']==h and r['variant']=='nominal' and r['outer_iterations']==14
 assert max(abs(audit[k]) for k in ('max_stage_residual_W','global_residual_W','power_residual_W'))<1e-8 and abs(audit['die_window_pair_balance_W'])<1e-12 and r['max_last_spatial_temperature_update_K']<1e-6
 assert '28 passed' in (D/'focused_tests_final.log').read_text() and 'Verified two real coupled spatial refinements' in (D/'archive_verification.log').read_text()
 qa=json.loads((D/'report_verification.json').read_text());assert qa['pages']==54 and qa['two_deterministic_builds_and_all_rasters_identical'] and qa['all_pages_visual_contact_sheet_reviewed'] and qa['pdf_sha256']==sha(R/'reports/current/TEC_TO_Reader_First_Assessment_20261111_V327.pdf')
 paths=[p for p in D.rglob('*') if p.is_file() and p!=M and '__pycache__' not in str(p)];paths +=[R/x for x in ['tecooledmct/nominal_gas_visibility_v327.py','scripts/tec_nominal_v327_visibility.py','scripts/tec_nominal_v327_independent.py','scripts/tec_nominal_v327_coupled.py','scripts/tec_nominal_v327_coupled_audit.py','scripts/tec_nominal_v327_figure.py','scripts/tec_nominal_v327_report_build.py','scripts/tec_nominal_v327_manifest.py','tests/test_nominal_gas_visibility_v327.py','tests/test_nominal_gas_v327_coupled.py','docs/NOMINAL_DIE_WINDOW_GAS_VISIBILITY_20261111.md','reports/current/reader_first_die_window_20261111.tex','reports/current/v327_die_window_section.tex','reports/current/figures/v327_die_window_visibility.pdf','reports/current/figures/v327_die_window_visibility.png','reports/current/TEC_TO_Reader_First_Assessment_20261111_V327.pdf']];src=dict(reg['source_sha256']);extra='data/nominal_gas_coupler_20261110/source_bare_column_subset.json';src[extra]=sha(R/extra);out={'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS source-mesh die/window visibility and one conditional original coupled solve; STOP complete gas physics','source_sha256':src,'mesh_sha256':reg['mesh_sha256'],'artifact_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(paths)}};M.write_text(json.dumps(out,indent=2)+'\n');print('PASS sealed V3.27',len(paths),'artifacts')
if __name__=='__main__':main()
