"""Historical global-mesh STOP and exact artifact identities remain non-promotable."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_global_mesh_gate_20261103'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def test_saved_surface_attempt_is_stopped_not_solver_ready():
 d=json.loads((DATA/'mesh_gate.json').read_text());a=json.loads((DATA/'face_area_audit.json').read_text())
 assert 'STOP GLOBAL MESH' in d['status']
 assert d['saved_surface_mesh_sha256']==sha(DATA/'unqualified_global_surface.msh')
 assert d['input_conformal_brep_sha256']==sha(ROOT/'data/v3_derived_multiphysics_20261103/analysis_conformal_mm.brep')
 assert d['input_face_registry_sha256']==sha(ROOT/'data/v3_derived_multiphysics_20261103/face_ownership.json')
 assert (a['face_count'],a['fail_count'],a['triangle_count'])==(2456,174,49863)
 assert not a['solver_release'] and not d['saved_surface_mesh_qualified']
 assert [e['volume_requested'] for e in d['attempts']]==[False,True,True]
 assert all('surface 2395' in e['volume_error'] for e in d['attempts'][1:])

def test_no_material_law_is_silently_qualified():
 d=json.loads((DATA/'physics_law_requirements.json').read_text())
 assert d['volume_count']==438 and d['face_count']==2456
 assert d['volume_material_counts']['COMPOSITE_MULTILAYER']==98
 assert d['volume_material_counts']['IDEALIZED_CAVITY_GAS']==1
 assert not d['solver_ready'] and d['no_implicit_bulk_fallback']
 assert all(x['value_assignment']=='UNSET' and not x['solver_admissibility']
   for x in d['domain_requirements'].values())
