import json,math
from pathlib import Path
import pytest
from tecooledmct.nominal_gas_visibility_v327 import open_rectangles,overlap,rectangle_poly,intersection,die_window_exchange
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_visibility_v327_20261111'

def test_rectangles_blocker_union_and_disjoint():
 r=open_rectangles((0,0,2,2),[(.5,.5,1.5,1.5),(1,1,2,2)])
 area=sum((x[2]-x[0])*(x[3]-x[1]) for x in r)
 assert area==pytest.approx(2.25)
 assert all(not overlap(a,b) for i,a in enumerate(r) for b in r[i+1:])
 assert all(not overlap(a,b) for a in r for b in [(.5,.5,1.5,1.5),(1,1,2,2)])

def test_fully_blocked_and_unblocked():
 assert open_rectangles((0,0,1,1),[(-1,-1,2,2)])==[]
 assert open_rectangles((0,0,1,1),[])==[(0,0,1,1)]

@pytest.mark.parametrize('bounds,blocks', [((1,0,0,1),[]),((0,0,1,0),[]),((0,0,1,1),[(1,0,0,1)]),((0,0,math.nan,1),[])])
def test_invalid_geometry_rejected(bounds,blocks):
 with pytest.raises(ValueError):open_rectangles(bounds,blocks)

def test_triangle_common_projection_and_ownership():
 a,_,_=intersection([(0,0),(2,0),(0,2)],rectangle_poly((.5,0,1.5,1)))
 assert a==pytest.approx(.875)
 assert intersection([(0,0),(1,0),(0,1)],rectangle_poly((2,2,3,3)))[0]==0

@pytest.mark.parametrize('p,a,b',[(0,300,220),(100,250,250),(100,300,220),(100,220,300)])
def test_gas_passivity_and_reciprocity(p,a,b):
 r=die_window_exchange(a,b,.5,.004,p,.8);assert r['die_load_W']==-r['window_load_W'];assert r['die_load_W']*(a-b)>=0
 if p==0 or a==b:assert r['die_load_W']==0

@pytest.mark.parametrize('area,gap,p,alpha',[(-1,.004,100,.8),(1,0,100,.8),(1,.004,-1,.8),(1,.004,100,0),(1,.004,100,1.1)])
def test_invalid_gas_inputs(area,gap,p,alpha):
 with pytest.raises(ValueError):die_window_exchange(300,220,area,gap,p,alpha)

def test_saved_independent_original_geometry_gates():
 v=json.loads((D/'die_window_visibility.json').read_text());a=json.loads((D/'independent_readback.json').read_text());assert v['source_faces']==[2335,2410] and v['all_source_solid_count']==824 and v['paired_area_mm2']==pytest.approx(.6945997335999441)
 assert len(v['patches'])==a['patches']==301 and a['max_area_error_mm2']<1e-12 and abs(a['pair_global_W'])<1e-12 and a['max_old_column_top_z_mm']<a['new_column_bottom_z_mm']
