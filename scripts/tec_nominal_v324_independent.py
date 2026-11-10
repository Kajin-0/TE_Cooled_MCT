"""Recompute saved source-node link fluxes independently of gas operator."""
from pathlib import Path
import json,hashlib,math
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_coupler_20261110'
def main():
 p=D/'source_field_subset_exchange.json';x=json.loads(p.read_text());f=np.load(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz',allow_pickle=False);tables=[]
 for j in range(4):
  ids=f[f'ceramic{j}_source_node_id_1based'];xyz=f[f'ceramic{j}_xyz_mm'];T=f[f'ceramic{j}_temperature_K'];tables.append({int(n):(float(t),z.tolist()) for n,t,z in zip(ids,T,xyz)})
 errors=[];Q={a:[0.,0.,0.] for a in ('0.5','0.8','1.0')}
 for c in x['cells']:
  stage=c['stage'];rec=[]
  for j,side in [(stage,'hot_ceramic_node_proxy'),(stage+1,'cold_ceramic_node_proxy')]:
   node=c[side];t,xyz=tables[j][node['source_node_id_1based']];assert abs(t-node['temperature_K'])<1e-12 and np.allclose(xyz,node['node_xyz_mm'],rtol=0,atol=1e-12);rec.append(t)
  avg=sum(rec)/2;assert 200<=avg<=400;k=float(np.interp(avg,[200,300,400],[.0064,.0095,.0122]));Rgas=99.218;gam=5/3;cp=gam/(gam-1)*Rgas;mu=k/(cp+1.25*Rgas);pr=mu*cp/k;lam=mu/100*math.sqrt(math.pi*Rgas*avg/2)
  rect=c['rect_xy_mm'];area=(rect[2]-rect[0])*(rect[3]-rect[1]);assert abs(area-c['area_mm2'])<1e-12
  for alpha in Q:
   aa=float(alpha);jump=(2-aa)/aa*2*gam/(gam+1)*lam/pr;flux=k*area*1e-6*(rec[0]-rec[1])/(.0006+2*jump);errors.append(abs(flux-c['Q_hot_to_cold_W'][alpha]));Q[alpha][stage]+=flux
 assert max(errors)<1e-15
 for a in Q:assert np.allclose(Q[a],x['summary'][a]['link_W'],rtol=0,atol=1e-15)
 out={'status':'PASS independent saved source-node readback and gas-law rederivation; NOT validation of physical gas transport','cells':len(x['cells']),'max_cell_abs_difference_W':max(errors),'stage_link_W':Q,'source_exchange_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 q=D/'independent_field_gas_audit.json';assert not q.exists();q.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
