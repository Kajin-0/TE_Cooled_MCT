import math,copy,json
from pathlib import Path
import pytest
from tecooledmct.gas_partition_v322 import allocate,exchange
from scripts.tec_gas_v322_partition import partition
R=Path(__file__).resolve().parents[1]

def link():return {'a':{'face':'fa','port':'a','rect':[0,0,1,1]},'b':{'face':'fb','port':'b','rect':[0,0,1,1]},'gap_m':.0005}
B={'fa':[0,0,2,2],'fb':[0,0,2,2]}
def test_source_rectangles_are_disjoint_and_union_does_not_double_count():
 a,owners=partition((0,0,4,4),[('film',(0,0,2,2)),('film',(1,1,3,3))],(0,0,4,2))
 assert a==pytest.approx({'solid_contact':7,'facing_gap_unblocked_at_face':3,'outer_unblocked_at_face':6});assert owners['film']==pytest.approx(7)
 with pytest.raises(ValueError):partition((0,0,4,4),[('a',(0,0,2,2)),('b',(1,1,3,3))],None)
def test_gas_zero_equal_reciprocal_and_conservation():
 l=[link()];a=exchange(B,l,{'a':300,'b':250},100);b=exchange(B,l,{'a':250,'b':300},100)
 assert a['heat_into_ports_W']['a']<0 and sum(a['heat_into_ports_W'].values())==pytest.approx(0,abs=1e-20)
 assert a['links'][0]['a_to_b_W']==pytest.approx(-b['links'][0]['a_to_b_W'])
 assert exchange(B,l,{'a':300,'b':250},0)['links'][0]['a_to_b_W']==0
 assert exchange(B,l,{'a':300,'b':300},100)['links'][0]['a_to_b_W']==0

def test_negative_controls():
 l=link()
 with pytest.raises(ValueError):allocate(B,[l,copy.deepcopy(l)])
 q=copy.deepcopy(l);q['b']['port']='a'
 with pytest.raises(ValueError):allocate(B,[q])
 q=copy.deepcopy(l);q['a']['rect']=[0,0,3,1]
 with pytest.raises(ValueError):allocate(B,[q])
 q=copy.deepcopy(l);q['gap_m']=0
 with pytest.raises(ValueError):allocate(B,[q])
 with pytest.raises(ValueError):exchange(B,[l],{'a':300,'b':250},-1)

def test_archived_surface_closure_and_rigid_translation():
 d=json.loads((R/'data/tec_gas_partition_20261110/source_partition.json').read_text())['designs'];n=d['nominal'];c=d['custom']
 assert len(n['faces'])==len(c['faces'])==24
 for a,b in zip(n['faces'],c['faces']):
  assert sum(a['partition_mm2'].values())==pytest.approx(a['area_mm2'],abs=1e-8)
  assert a['partition_mm2']==pytest.approx(b['partition_mm2'],abs=1e-8)
  assert abs(a['source_vs_R3_contact_difference_mm2'])<1e-7
  assert a['derived_R3_gas_mm2']==pytest.approx(a['area_mm2']-a['partition_mm2']['solid_contact'],abs=1e-7)
  assert len(a['derived_R3_faces'])>0
 assert [x-y for x,y in zip(c['substrate_gaps_mm'],n['substrate_gaps_mm'])]==pytest.approx([.1]*3,abs=1e-12)
