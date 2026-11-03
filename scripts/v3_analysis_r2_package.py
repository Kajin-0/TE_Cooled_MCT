"""Assemble already-qualified R2 geometry with explicit global-volume NON-qualification.

The original attempts remain intact and the release directory is write-once.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[1]
R1=ROOT/'data/v3_derived_multiphysics_20261103'
SRC=ROOT/'data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step'
MASTER=ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')

def main(out):
 if out.exists():raise ValueError('Refuse overwrite')
 b=ROOT/'data/v3_analysis_r2_20261103_attempt05'
 a=ROOT/'data/v3_analysis_r2_audit_20261103_attempt01'
 l=ROOT/'data/v3_analysis_r2_local_20261103_attempt01'
 c=ROOT/'data/v3_analysis_r2_mesh_pilot_20261103_curvature'
 e=ROOT/'data/v3_analysis_r2_mesh_pilot_20261103_edge_only'
 d=ROOT/'data/v3_analysis_r2_mesh_pilot_20261103_attempt01'
 build=json.loads((b/'build_receipt.json').read_text())
 integrity=json.loads((a/'r2_integrity.json').read_text())
 shell=json.loads((a/'shell_projection.json').read_text())
 laws=json.loads((a/'r2_face_law_requirements.json').read_text())
 local=json.loads((l/'meshability.json').read_text())
 dense=json.loads((c/'area_gate.json').read_text())
 assert build['status'].startswith('PASS') and integrity['status'].startswith('PASS')
 assert shell['status'].startswith('PASS') and laws['status'].startswith('PASS')
 assert (build['final_volume_count'],build['face_count'])==(428,2422)
 assert len(integrity['source_to_analysis'])==824 and len(integrity['source_contacts'])==378
 assert (len(integrity['missing_contacts']),len(integrity['area_errors']),len(integrity['unintended_electrical_contacts']))==(0,0,0)
 assert dense['status'].startswith('PASS') and dense['fail_count']==0 and dense['face_count']==2422
 assert dense['max_absolute_error_relative']<.01
 assert local['status'].startswith('PASS') and local['tetrahedra']==38496
 assert build['source_824_STEP_sha256']==sha(SRC)
 assert build['canonical_Rev3_sha256']==sha(MASTER)
 assert build['starting_geometry_sha256']==sha(R1/'analysis_solids_mm.brep')
 out.mkdir(parents=True)
 copied={
   'analysis_solids_mm.brep':b/'r2_reduced_solids_mm.brep',
   'analysis_with_gas_mm.brep':b/'r2_with_gas_mm.brep',
   'analysis_conformal_mm.brep':b/'r2_conformal_mm.brep',
   'geometry_build_receipt.json':b/'build_receipt.json',
   'physical_to_analysis_registry.json':a/'r2_integrity.json',
   'shell_projection.json':a/'shell_projection.json',
   'domain_face_law_requirements.json':a/'r2_face_law_requirements.json',
   'surface_mesh_area_gate.json':c/'area_gate.json',
   'surface_mesh_attempt_receipt.json':c/'mesh_receipt.json',
   'local_lead_pin_mesh.msh':l/'r2_lead_pin_local.msh',
   'local_lead_pin_receipt.json':l/'meshability.json',
   'coarse_surface_area_gate.json':d/'area_gate.json',
   'edge_only_surface_area_gate.json':e/'area_gate.json',
 }
 for name,source in copied.items():
  shutil.copyfile(source,out/name)
 high=c/'r2_global_surface_UNQUALIFIED.msh'
 assert dense['mesh_sha256']==sha(high)
 packed=out/'global_surface_area_pass_VOLUME_UNQUALIFIED.msh.gz'
 with high.open('rb') as src,packed.open('wb') as dst:
  with gzip.GzipFile(filename='',mode='wb',fileobj=dst,compresslevel=9,mtime=0) as zipped:
   shutil.copyfileobj(src,zipped,1024*1024)
 with gzip.open(packed,'rb') as check:
  digest=hashlib.sha256()
  while True:
   part=check.read(1024*1024)
   if not part:break
   digest.update(part)
 assert digest.hexdigest()==dense['mesh_sha256']
 manifest={'status':'RELEASED ANALYSIS-ONLY GEOMETRY, GLOBAL 3D VOLUME MESH NOT QUALIFIED',
   'source_commit':'5c16da87702ce98bc5be3c222680b599ed6353b4',
   'source_physical_STEP_SHA256':sha(SRC),'canonical_Rev3_SHA256':sha(MASTER),
   'upstream_R1_reduced_solids_SHA256':sha(R1/'analysis_solids_mm.brep'),
   'geometry_volumes':428,'geometry_faces':2422,'original_source_bodies':824,
   'finite_contacts_preserved':378,'gas_components':1,
   'surface_candidate_triangles':dense['triangle_count'],'surface_candidate_nodes':dense['mesh_nodes'],
   'max_surface_area_error_relative':dense['max_absolute_error_relative'],
   'global_3D_mesh_status':'NOT RUN, geometry surface candidate too large for registered 4CPU/8GiB local budget',
   'local_3D_lead_pin_tetrahedra':local['tetrahedra'],
   'shell_subface_limits':shell['partial_face_count'],
   'gas_replacement_caveat':'R2 gas occupies two removed polymer jacket volumes; a future shell operator must displace/exclude that gas conduction path or correct gas-side reference area. No solver is authorized to double count gas and polymer thermal conductance.',
   'material_law_status':'ALL UNSET; no PDE authorization',
   'files_sha256':{name:sha(out/name) for name in copied},
   'global_surface_gzip_sha256':sha(packed),
   'decompressed_surface_mesh_sha256':dense['mesh_sha256'],
   'physical_redesign':False,'legacy_electrical_Gate_B':'STOP','issue_2':'OPEN'}
 save(out/'release_manifest.json',manifest)
 print('R2 RELEASE',len(copied),'files + gz + manifest','surface compressed',round(packed.stat().st_size/1e6,2),'MB',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();main(a.out)
