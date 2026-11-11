import pytest
def test_saved_source_polygon_area_loads_and_positive_form():
 import json
 from pathlib import Path
 import numpy as np
 from scipy.sparse import coo_matrix
 from tecooledmct.nominal_gas_v324 import flux
 R=Path(__file__).resolve().parents[1];o=json.loads((R/'data/nominal_gas_p1_20261111/p1_operator.json').read_text());a=json.loads((R/'data/nominal_gas_p1_20261111/independent_readback.json').read_text())
 assert o['status'].startswith('PASS') and o['summary']['rectangles']==752 and a['pieces']==6109
 assert max(abs(x['error_mm2']) for x in o['summary']['area_rows'])<1e-5 and a['max_single_pair_conservation_W']<1e-12
 pairs=o['pairs'];ids=sorted({n for p in pairs for side in ('hot','cold') for n in p[side]['node_ids']});idx={n:i for i,n in enumerate(ids)};ii=[];jj=[];vv=[]
 for p in pairs:
  nodes=p['hot']['node_ids']+p['cold']['node_ids'];w=p['hot']['weights']+[-x for x in p['cold']['weights']];g=flux(275,275,p['area_mm2'],p['gap_m'],100,.8)['G_W_K']
  for i in range(6):
   for j in range(6):ii.append(idx[nodes[i]]);jj.append(idx[nodes[j]]);vv.append(g*w[i]*w[j])
 K=coo_matrix((vv,(ii,jj)),shape=(len(ids),len(ids))).tocsr();assert np.max(abs((K-K.T).data),initial=0)<1e-15;assert max(abs(K@np.ones(len(ids))))<1e-15
 rng=np.random.default_rng(325)
 for _ in range(5):
  v=rng.normal(size=len(ids));assert v@(K@v)>=-1e-14

def test_partial_coupled_saved_case_and_independent_audits():
 import json,hashlib,numpy as np
 from pathlib import Path
 R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_p1_20261111';C=D/'coupled_attempt01';r=json.loads((C/'result.json').read_text());a=json.loads((C/'independent_audit.json').read_text());p=json.loads((C/'ports_crosscheck.json').read_text());h=hashlib.sha256((C/'result.json').read_bytes()).hexdigest()
 assert a['status'].startswith('PASS') and a['source_result_sha256']==h and p['status'].startswith('PASS') and p['source_result_sha256']==h
 assert r['variant']=='nominal' and r['gas_boundary_scope']=='only 752 source bare-ceramic columns'
 assert all(v==0 for v in r['cavity_gas_heat_into_three_ceramics_and_die_W'])
 assert abs(a['power_residual_W'])<1e-8 and abs(a['global_residual_W'])<1e-8 and a['max_stage_residual_W']<1e-8
 assert r['max_last_spatial_temperature_update_K']<3e-7 and r['spatial_outer_iteration_history'][-1]['max_nodal_update_K']<3e-7
 assert len(r['source_individual_leg_flux_and_electric_results'])==88 and r['Cu_form_tab_electrothermal_result']['net_details']['88']['contact_electrical_R_ohm'][1]==0
 f=np.load(C/'ceramic_fields.npz');assert abs(sum(float(f[f'ceramic{i}_gas_nodal_load_W'].sum()) for i in range(4)))<1e-12
 assert a['die_K']==pytest.approx(218.65910654164801,abs=1e-10)
