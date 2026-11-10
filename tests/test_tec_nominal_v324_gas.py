"""Nominal source subset, negative controls, conservation and contact lineage."""
from pathlib import Path
import json,hashlib,math
import pytest
from tecooledmct.nominal_gas_v324 import flux,stage_loads,nominal_residual_adjustment
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_coupler_20261110'
def load(n):return json.loads((D/n).read_text())
def test_complete_mapping_and_source_connected_joints():
 r=load('nominal_face_temperature_map.json');assert r['faces']==1840 and len({x['face_tag'] for x in r['entries']})==1840
 assert r['qualified_gas_BC_faces']==0 and r['lead_joint_faces_source_endpoint_proxy']==8
 h=hashlib.sha256((R/'data/v3_r32_global_surface_20261103/source_metadata.json').read_bytes()).hexdigest()
 assert all(x['original_R3_registry_sha256']==h for x in r['entries'])
 assert r['groups']['UNRESOLVED']['faces']==173 and r['approx_mapped_faces']==1667
 source=json.loads((R/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text());contacts=source['explicit_contacts']
 for x in r['entries']:
  m=x['mapping']
  if 'nodes' in m:assert sum(n['weight'] for n in m['nodes'])==pytest.approx(1,abs=1e-12)
  if m['status']=='SOURCE_CONTACT_ENDPOINT_PROXY':
   assert len(m['source_contacts'])==2
   assert all(any({c['a'],c['b']}=={x['solid_domain'],peer} for c in contacts) for peer in m['source_contacts'])
 assert sum(v['area_mm2'] for v in r['groups'].values())==pytest.approx(r['face_area_mm2'],abs=1e-8)
def test_unblocked_cells_against_all_original_solid_bboxes():
 x=load('source_bare_column_subset.json');d=json.loads((R/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
 for p in x['patches']:
  cap=next(b for b in d['bodies'] if b['name']=='cap_shell');q=p['domain_xy_mm']
  assert max(math.hypot(a-cap['base'][0],b-cap['base'][1]) for a in (q[0],q[2]) for b in (q[1],q[3]))<cap['inner_radius']
  for i,a in enumerate(p['cells_xy_mm']):
   for b in p['cells_xy_mm'][i+1:]:
    assert max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))<1e-14
  area=0.
  for cell in p['cells_xy_mm']:
   area+=(cell[2]-cell[0])*(cell[3]-cell[1])
   for body in d['bodies']:
    if body['name'] in ('ceramic'+str(p['stage']),'ceramic'+str(p['stage']+1),'cap_shell'):continue
    q=body['bbox_mm'];bs=body.get('boxes_mm') if body['shape']=='boxes' else [[q[0],q[1],q[2],q[3]-q[0],q[4]-q[1],q[5]-q[2]]]
    for b in bs:
     if b[2]+b[5]<=p['z0_mm']+1e-9 or b[2]>=p['z1_mm']-1e-9:continue
     overlap=max(0,min(cell[2],b[0]+b[3])-max(cell[0],b[0]))*max(0,min(cell[3],b[1]+b[4])-max(cell[1],b[1]))
     assert overlap<1e-14,(p['stage'],body['name'],overlap)
  assert area==pytest.approx(p['unobstructed_column_area_mm2'],abs=1e-10)
  assert p['gap_m']==pytest.approx(.0006)
 assert [x['hot_gas_face_tag'] for x in x['patches']]==[7,73,103]
def test_passive_gas_controls_and_pressure():
 q=flux(300,250,1,.0006,100,.8);r=flux(250,300,1,.0006,100,.8)
 assert q['Q_hot_to_cold_W']>0 and q['Q_hot_to_cold_W']==pytest.approx(-r['Q_hot_to_cold_W'])
 assert flux(300,250,1,.0006,0,.8)['G_W_K']==0
 assert flux(300,300,1,.0006,100,.8)['Q_hot_to_cold_W']==0
 high=flux(300,250,1,.0006,101325,.8)
 assert high['G_W_K']>q['G_W_K']
 assert high['G_W_K']==pytest.approx(high['k_W_mK']*1e-6/.0006,rel=.003)
 for args in [(300,250,1,0,100,.8),(300,250,1,.0006,-1,.8),(300,250,1,.0006,100,0)]:
  with pytest.raises(ValueError):flux(*args)
def test_actual_source_field_cells_and_residual_adapter_conserve():
 r=load('source_field_subset_exchange.json');p=load('source_bare_column_subset.json');a=load('source_residual_adapter.json')
 assert r['full_system_solves']==0 and len(r['cells'])==sum(len(x['cells_xy_mm']) for x in p['patches'])==752
 for alpha,v in r['summary'].items():
  assert abs(sum(v['stage_heat_into_ceramic_W']))<1e-15
  assert v['link_W']==pytest.approx([sum(x['Q_hot_to_cold_W'][alpha] for x in r['cells'] if x['stage']==j) for j in range(3)])
 assert a['stage_die_residual_delta_W']==pytest.approx(nominal_residual_adjustment(a['old_interstage_W'],a['old_external_gas_W'],a['new_interstage_W'])['stage_die_residual_delta_W'])
 assert r['max_nearest_xy_distance_mm']<.2


def test_original_figure_leg_counts_and_dimensions():
 d=json.loads((R/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text());body={b['name']:b for b in d['bodies']}
 assert [sum(x['stage']==i for x in d['legs']) for i in range(3)]==[58,22,8]
 for leg in d['legs']:
  q=body[f"leg{leg['index']}_{leg['polarity']}"]['boxes_mm'][0]
  assert q[3:6]==pytest.approx([.4,.4,.5],abs=1e-12)
