"""No-mesh, no-PDE negative controls for proposed global mesh area gate."""
from copy import deepcopy
import pytest
from tecooledmct.v3_global_mesh_audit import validate_face_area_records

FACES=[{'face_tag':11,'area_m2':1e-6,'interface_class':'SOLID_SOLID',
 'owners':[{'source_name':'A'},{'source_name':'B'}]},
 {'face_tag':12,'area_m2':2e-6,'interface_class':'GAS_SOLID',
 'owners':[{'source_name':'GAS'},{'source_name':'B'}]}]
GOOD={11:{'mesh_area_mm2':1.0000001,'triangles':8},12:{'mesh_area_mm2':2,'triangles':9}}

def test_clean_face_coverage_and_area_pass():
 d=validate_face_area_records(FACES,GOOD)
 assert d['status'].startswith('PASS') and d['face_count']==2 and d['triangle_count']==17
 assert not d['solver_release']

def test_one_percent_area_gate_rejects_bad_curvature():
 bad=deepcopy(GOOD);bad[11]['mesh_area_mm2']=1.011
 assert validate_face_area_records(FACES,bad)['fail_count']==1

@pytest.mark.parametrize('kind',['missing','extra','duplicate','nan','negative','zero_triangles'])
def test_corrupt_surface_area_fails_closed(kind):
 faces=deepcopy(FACES);d=deepcopy(GOOD)
 if kind=='missing':del d[11]
 if kind=='extra':d[30]=dict(mesh_area_mm2=1,triangles=1)
 if kind=='duplicate':faces[1]['face_tag']=faces[0]['face_tag']
 if kind=='nan':d[11]['mesh_area_mm2']=float('nan')
 if kind=='negative':d[11]['mesh_area_mm2']=-1
 if kind=='zero_triangles':d[11]['triangles']=0
 with pytest.raises(ValueError):validate_face_area_records(faces,d)
