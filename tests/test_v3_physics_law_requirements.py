import copy,json
from pathlib import Path
import pytest
from tecooledmct.v3_physics_law_requirements import generate_requirements

p=Path(__file__).resolve().parents[1]/'data/v3_derived_multiphysics_20261103/face_ownership.json'
def load():return json.loads(p.read_text())

def test_complete_explicit_unqualified_contract():
 d=generate_requirements(load())
 assert (d['volume_count'],d['face_count'])==(438,2456)
 assert d['volume_material_counts']['COMPOSITE_MULTILAYER']==98
 assert d['volume_material_counts']['P']==44 and d['volume_material_counts']['N']==44
 assert not d['solver_ready'] and all(not x['solver_admissibility'] for x in d['domain_requirements'].values())

@pytest.mark.parametrize('corruption',['bulk','unknown','missing_stage','unknown_face'])
def test_unqualified_law_does_not_silently_fallback(corruption):
 d=load()
 if corruption=='bulk':d['domain_metadata']['net0_plane0.500_Cu']['material']='UnassignedBulkCu'
 if corruption=='unknown':d['domain_metadata']['ceramic0']['material']='imaginary'
 if corruption=='missing_stage':d['domain_metadata']['leg0_N']['stage']=None
 if corruption=='unknown_face':d['interface_records'][0]['electrical_material_category']=''
 with pytest.raises(ValueError):generate_requirements(d)
