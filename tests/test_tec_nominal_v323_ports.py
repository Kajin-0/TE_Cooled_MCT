"""Nominal saved-source controls; no custom geometry or solver rerun."""
from pathlib import Path
import copy,json,hashlib
import pytest
from scripts.tec_nominal_v323_audit import check
from scripts.tec_nominal_v323_budget import check as budget
from scripts.tec_nominal_v323_regime import mean_free_path,ra
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
@pytest.fixture(scope='module')
def data():return read('data/nominal_cavity_ports_20261110/nominal_gas_face_ports.json'),read('data/v3_r32_global_surface_20261103/source_metadata.json')
def test_complete_readback_and_no_invented_gas_boundary(data):
 r=check(*data);assert r['faces']==1840 and r['unique_tags']==1840
 assert r['source_area_mm2']==pytest.approx(903.2150497910573,abs=1e-9)
 assert r['semantic_counts']['patterned_metal']==523 and r['unresolved_semantic_faces']==8
 assert r['implemented_gas_face_BCs']==0
@pytest.mark.parametrize('fault',['duplicate','area','normal','condition','lineage'])
def test_registry_rejects_missing_duplicate_mismapped_and_installed_claim(data,fault):
 r=copy.deepcopy(data[0]);x=r['faces'][0]
 if fault=='duplicate':r['faces'][1]=copy.deepcopy(x)
 if fault=='area':x['area_mm2']*=1.01
 if fault=='normal':x['gas_orientation_sign']*=-1
 if fault=='condition':x['gas_boundary_condition_installed']=True
 if fault=='lineage':x['physical_sources']=['not_a_source_solid']
 with pytest.raises(AssertionError):check(r,data[1])
def test_archived_nominal_stage_and_global_balance():
 r=read('data/tec_height_coupling_20261110/nominal/result.json');a=budget(r)
 assert abs(a['global_energy_residual_W'])<1e-8 and max(map(abs,a['stage_qh_minus_qc_minus_IV_W']))<1e-9
 r['terminal_voltage_V']*=1.01
 with pytest.raises(AssertionError):budget(r)
def test_kr_knudsen_pressure_and_size_controls():
 l=mean_free_path(250,100,.36e-9)
 assert l==pytest.approx(5.994506276938621e-5) and l/.00057==pytest.approx(.10516677678839687)
 assert mean_free_path(250,1000,.36e-9)==pytest.approx(l/10)
 assert ra(250,101325,.003,80)['Ra']>ra(250,101325,.00057,80)['Ra']>0
 with pytest.raises(ValueError):mean_free_path(250,0,.36e-9)

def test_reference_input_identity():
 x=read('data/nominal_cavity_ports_20261110/nominal_reference.json');assert x['leg_length_mm']==.5 and x['couples_by_stage']==[29,11,4]
 for r in x['operator_sources'].values():assert hashlib.sha256((R/r['path']).read_bytes()).hexdigest()==r['sha256']
 assert x['reference']['die_K']==pytest.approx(219.36893852571148)
 for k in ('original_STEP','historical_v311_different_proxy'):
  v=x[k];assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
