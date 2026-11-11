from pathlib import Path
import json,numpy as np,pytest
from tecooledmct.nominal_gas_p1_coupler_v325 import SourceP1Gas
R=Path(__file__).resolve().parents[1]
def test_source_vectorized_matches_independent_saved_operator():
 o=json.loads((R/'data/nominal_gas_p1_20261111/p1_operator.json').read_text());d=np.load(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz');ids=[d[f'ceramic{i}_source_node_id_1based'] for i in range(4)];temps=[d[f'ceramic{i}_temperature_K'] for i in range(4)];g=SourceP1Gas(o['pairs'],ids)
 for alpha in (.5,.8,1.):
  a=g.evaluate(temps,100,alpha);b=o['saved_field_results'][str(alpha)];assert a['links_W']==pytest.approx(b['stage_heat_hot_to_cold_W'],abs=1e-14)
  for i in range(4):
   assert all(a['loads'][i][j]==pytest.approx(b['sparse_node_load_W'].get(str(int(n)),0),abs=1e-15) for j,n in enumerate(ids[i]))
  assert abs(sum(x.sum() for x in a['loads']))<1e-12 and a['entropy_W_K']>=0
 assert max(abs(x).max() for x in g.evaluate(temps,0)['loads'])==0
 assert max(abs(x).max() for x in g.evaluate([np.full(len(i),250.) for i in ids],100)['loads'])==0
