"""No-Gmsh, no-PDE immutable R2 positive and negative tests for CI."""
import copy,json
from pathlib import Path
import pytest
from tecooledmct.v3_analysis_r2_release_integrity import validate,verify_files

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_analysis_r2_release_20261103'
NAMES=['release_manifest.json','geometry_build_receipt.json','physical_to_analysis_registry.json',
 'shell_projection.json','domain_face_law_requirements.json','surface_mesh_area_gate.json',
 'local_lead_pin_receipt.json']

def data():return [json.loads((DATA/p).read_text()) for p in NAMES]

def test_release_accepted_geometry_without_qualified_global_volume():
 m=validate(*data())
 assert m['status'].startswith('PASS') and not m['solver_ready']
 assert m['2d_area_failures']==0 and m['partial_shell_subfaces']==4

def test_protected_parent_step_rev3_and_new_r2_artifact_hashes():
 m=data()[0]
 assert verify_files(DATA,m,
     ROOT/'data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step',
     ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf',
     ROOT/'data/v3_derived_multiphysics_20261103/analysis_solids_mm.brep')

@pytest.mark.parametrize('failure',['missing_source','missing_face','wrong_contact_area',
 'gas_volume_error','bulk_pin','missing_shell','partial_shell_silent','missing_terminal',
 'unqualified_mesh','false_release','failed_surface','missing_gas_displacement_warning'])
def test_corrupt_r2_geometry_and_law_state_fails_closed(failure):
 v=data();m,b,r,s,l,surf,loc=v
 if failure=='missing_source':r['source_to_analysis'].pop('pin1_Au')
 if failure=='missing_face':r['face_registry'].pop(next(iter(r['face_registry'])))
 if failure=='wrong_contact_area':r['source_contacts'][0]['relative_error']=.05
 if failure=='gas_volume_error':b['R2_gas_volume_mm3']+=.02
 if failure=='bulk_pin':l['domain_material_counts']['EFFECTIVE_AXIAL_KOVAR_NI_AU']=0
 if failure=='missing_shell':s['mapping'].pop()
 if failure=='partial_shell_silent':s['mapping'][0]['constitutive_law_status']='QUALIFIED'
 if failure=='missing_terminal':l['terminal_face_counts'].pop('TERMINAL_PIN1')
 if failure=='unqualified_mesh':l['solver_ready']=True
 if failure=='false_release':m['global_3D_mesh_status']='PASS / complete'
 if failure=='failed_surface':surf['fail_count']=1
 if failure=='missing_gas_displacement_warning':m['gas_replacement_caveat']=''
 with pytest.raises(ValueError):validate(*v)
