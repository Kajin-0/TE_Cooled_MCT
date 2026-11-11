import pytest
from tecooledmct.nominal_gas_p1_v325 import clip,centroid_area,weights,exchange

def test_clipping_and_p1_exact_integrals():
 p=clip([(0,0),(2,0),(0,2)],[(0,0),(1,0),(1,1),(0,1)]);a,c=centroid_area(p)
 assert a==pytest.approx(1.) and c==pytest.approx((.5,.5))
 assert weights([(0,0),(2,0),(0,2)],c)==pytest.approx([.5,.25,.25])
 assert centroid_area(clip([(0,0),(1,0),(0,1)],[(2,2),(3,2),(3,3),(2,3)]))[0]==0

def test_pair_conservation_entropy_and_zero_controls():
 p={'stage':0,'area_mm2':1.,'gap_m':.0006,'hot':{'node_ids':[1,2,3],'weights':[.2,.3,.5]},'cold':{'node_ids':[4,5,6],'weights':[.3,.4,.3]}}
 T={1:300,2:300,3:300,4:250,5:250,6:250};r=exchange([p],T);assert sum(r['node_load_W'].values())==pytest.approx(0,abs=1e-16);assert r['entropy_generation_W_K']>0
 assert exchange([p],T,p=0)['stage_heat_hot_to_cold_W'][0]==0
 assert exchange([p],{n:250 for n in T})['stage_heat_hot_to_cold_W'][0]==0
 a=exchange([p],T,alpha=.5)['stage_heat_hot_to_cold_W'][0];b=exchange([p],T,alpha=1.)['stage_heat_hot_to_cold_W'][0];assert 0<a<b


def test_tiny_polygon_centroid_at_nonzero_origin():
 p=[(2.6,2.3),(2.600001,2.3),(2.600001,2.3000001),(2.6,2.3000001)]
 a,c=centroid_area(p);assert a==pytest.approx(1e-13,rel=2e-8) and c==pytest.approx((2.6000005,2.30000005),abs=1e-12)
