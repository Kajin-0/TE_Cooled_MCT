#!/usr/bin/env python3
"""Seal and verify original-only V3.26 source and conditional evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_metal_v326_20261111';M=D/'manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
 if a.verify:
  m=json.loads(M.read_text())
  for field in ('source_sha256','artifact_sha256'):
   for name,h in m[field].items():assert sha(R/name)==h,name
  print('PASS V3.26 manifest',len(m['artifact_sha256']),'artifacts');return
 assert not M.exists();reg=json.loads((D/'registration.json').read_text())
 for name,h in reg['source_sha256'].items():assert sha(R/name)==h,name
 g=json.loads((D/'face_temperature_graph.json').read_text());assert g['total_faces']==1840 and g['groups']['UNRESOLVED']['faces']==134 and g['groups']['CONDITIONAL_DISTRIBUTED_TAB_CENTERLINE']['faces']==39
 i=json.loads((D/'independent_geometry_readback.json').read_text());assert i['face_graph_sha256']==sha(D/'face_temperature_graph.json') and i['checked_faces']==39 and i['max_sampled_arclength_difference_mm']<.001
 q=json.loads((D/'conditional_metal_physics.json').read_text());assert q['new_supplemental_gas_pairs']==q['new_coupled_solves']==0 and max(abs(z['energy_residual_W']) for z in q['segments'])<1e-14
 b=json.loads((D/'independent_bath_control.json').read_text());assert b['status'].startswith('PASS') and abs(b['benchmarks'][-1]['independent_global_energy_residual_W'])<1e-8
 v=json.loads((D/'report_verification.json').read_text());assert v['pages']==53 and v['two_deterministic_builds_and_all_rasters_identical'] and v['all_pages_visual_contact_sheet_reviewed'] and v['pdf_sha256']==sha(R/'reports/current/TEC_TO_Reader_First_Assessment_20261111_V326.pdf')
 assert '10 passed' in (D/'focused_tests_final.log').read_text();assert 'Verified two real coupled spatial refinements' in (D/'archive_verification.log').read_text()
 paths=[p for p in D.rglob('*') if p.is_file() and p!=M and '__pycache__' not in str(p)];paths +=[R/x for x in ['tecooledmct/nominal_cavity_metal_v326.py','scripts/tec_nominal_v326_metal_mapping.py','scripts/tec_nominal_v326_quantify.py','scripts/tec_nominal_v326_independent.py','scripts/tec_nominal_v326_independent_geometry.py','scripts/tec_nominal_v326_figure.py','scripts/tec_nominal_v326_report_build.py','scripts/tec_nominal_v326_manifest.py','tests/test_nominal_cavity_metal_v326.py','docs/NOMINAL_CAVITY_METAL_THERMAL_20261111.md','reports/current/reader_first_nominal_metal_20261111.tex','reports/current/v326_nominal_metal_section.tex','reports/current/figures/v326_source_tab_temperature.pdf','reports/current/figures/v326_source_tab_temperature.png','reports/current/TEC_TO_Reader_First_Assessment_20261111_V326.pdf']];out={'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS conditional source Cu mapping and 1D bath controls; STOP native gas geometry qualification','source_sha256':reg['source_sha256'],'artifact_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(paths)}};M.write_text(json.dumps(out,indent=2)+'\n');print('PASS sealed V3.26',len(paths),'artifacts')
if __name__=='__main__':main()
