"""Actual nominal ceramic P1 gas load insertion: balanced source mesh control."""
from pathlib import Path
from datetime import datetime,timezone
import json,types,hashlib
import numpy as np
from tecooledmct.nominal_gas_p1_coupler_v325 import SourceP1Gas
from scripts.tec_nominal_v325_coupled import transformed
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_p1_20261111';BASE=R/'scripts/tec_height_v320_coupled.py'
def main():
 c=json.loads((D/'coupled_contract.json').read_text());src=transformed();assert hashlib.sha256(src.encode()).hexdigest()==c['executed_source_sha256']
 o=json.loads((D/'p1_operator.json').read_text());assert o['status'].startswith('PASS');runtime=types.ModuleType('preflight_v325');runtime.__file__=str(BASE);runtime.SourceP1Gas=SourceP1Gas;runtime.GAS_PAIRS=o['pairs'];exec(compile(src,str(BASE)+':preflight','exec'),runtime.__dict__);legs,_=runtime.find_leg_contact_source();sp=runtime.OriginalPlates(legs)
 f=np.load(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz');ids=[p['node_ids'] for p in sp.plates];T=[]
 for i in range(4):
  assert np.array_equal(ids[i],f[f'ceramic{i}_source_node_id_1based']);T.append(f[f'ceramic{i}_temperature_K'])
 g=SourceP1Gas(o['pairs'],ids).evaluate(T);checks=[]
 for i,p in enumerate(sp.plates):
  gas=g['loads'][i];comp=-gas.sum()*p['tagloads'][p['taglist'][0]];rhs=gas+comp;assert abs(rhs.sum())<1e-12
  u=np.r_[0.,p['gas_lu'].solve(rhs[1:])];u-=p['bweight']@u;res=p['K']@u-rhs
  checks.append({'ceramic':i,'gas_net_W':float(gas.sum()),'compensation_W':float(comp.sum()),'max_full_nodal_residual_W':float(np.max(np.abs(res))),'source_nodes':len(ids[i])});assert max(abs(res))<1e-10
 assert abs(sum(float(x.sum()) for x in g['loads']))<1e-12
 out={'observed_UTC':datetime.now(timezone.utc).isoformat(),'status':'PASS selected P1 gas nodal loads on original ceramic stiffness matrices with synthetic compensating pad loads; NOT a coupled package solve','executed_solver_sha256':c['executed_source_sha256'],'gas_links_W':g['links_W'],'global_gas_load_W':sum(float(x.sum()) for x in g['loads']),'checks':checks,'tests':'P1 source node identity; balanced Neumann; full K u - rhs; compensation synthetic'}
 p=D/'fem_preflight.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
