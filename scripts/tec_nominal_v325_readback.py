"""Independent triangle-fan P1, source-node and heat-load readback."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,math
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_p1_20261111'
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def bary(t,p):
 a,b,c=t;den=cross(b-a,c-a);v=cross(p-a,c-a)/den;w=cross(b-a,p-a)/den;return np.array([1-v-w,v,w])
def main():
 p=D/'p1_operator.json';o=json.loads(p.read_text());assert o['status'].startswith('PASS');data=np.load(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz',allow_pickle=False);nodes={};temp={}
 for j in range(4):
  for n,x,t in zip(data[f'ceramic{j}_source_node_id_1based'],data[f'ceramic{j}_xyz_mm'],data[f'ceramic{j}_temperature_K']):nodes[int(n)]=np.array(x[:2]);temp[int(n)]=float(t)
 maxarea=0.;maxw=0.;maxq=0.;maxpair=0.;net={a:defaultdict(float) for a in ('0.5','0.8','1.0')};stage={a:np.zeros(3) for a in net}
 for i,x in enumerate(o['pairs']):
  poly=np.array(x['polygon_xy_mm']);origin=poly[0];A=0.;wh=np.zeros(3);wc=np.zeros(3);th=np.array([nodes[z] for z in x['hot']['node_ids']]);tc=np.array([nodes[z] for z in x['cold']['node_ids']])
  for j in range(1,len(poly)-1):
   v,w=poly[j],poly[j+1];area=abs(cross(v-origin,w-origin))/2;center=(origin+v+w)/3;A+=area;wh+=area*bary(th,center);wc+=area*bary(tc,center)
  assert A>0;maxarea=max(maxarea,abs(A-x['area_mm2']));wh/=A;wc/=A;maxw=max(maxw,float(np.max(abs(wh-x['hot']['weights']))),float(np.max(abs(wc-x['cold']['weights']))))
  Th=sum(temp[n]*v for n,v in zip(x['hot']['node_ids'],wh));Tc=sum(temp[n]*v for n,v in zip(x['cold']['node_ids'],wc));avg=(Th+Tc)/2;assert 200<=avg<=400
  k=float(np.interp(avg,[200,300,400],[.0064,.0095,.0122]));Rgas=99.218;gamma=5/3;cp=gamma/(gamma-1)*Rgas;mu=k/(cp+1.25*Rgas);pr=mu*cp/k;lam=mu/100*math.sqrt(math.pi*Rgas*avg/2)
  for a in net:
   alpha=float(a);jump=(2-alpha)/alpha*2*gamma/(gamma+1)*lam/pr;q=k*A*1e-6*(Th-Tc)/(x['gap_m']+2*jump);maxq=max(maxq,abs(q-o['saved_field_results'][a]['pair_heat_hot_to_cold_W'][i]));stage[a][x['stage']]+=q
   hsum=0.;csum=0.
   for n,w in zip(x['hot']['node_ids'],wh):net[a][n]-=q*w;hsum-=q*w
   for n,w in zip(x['cold']['node_ids'],wc):net[a][n]+=q*w;csum+=q*w
   maxpair=max(maxpair,abs(hsum+csum))
 assert maxarea<1e-11 and maxw<1e-7 and maxq<1e-14 and maxpair<1e-12
 maxload=0.
 for a in net:
  expected=o['saved_field_results'][a]['sparse_node_load_W'];assert set(map(str,net[a]))==set(expected)
  maxload=max(maxload,max(abs(q-expected[str(n)]) for n,q in net[a].items()));assert np.allclose(stage[a],o['saved_field_results'][a]['stage_heat_hot_to_cold_W'],rtol=0,atol=1e-13)
 assert maxload<1e-13
 out={'status':'PASS independent fan integration and source-node/flux readback; no native gas physical validation','pieces':len(o['pairs']),'max_polygon_area_difference_mm2':maxarea,'max_P1_weight_difference':maxw,'max_pair_heat_difference_W':maxq,'max_single_pair_conservation_W':maxpair,'max_nodal_load_difference_W':maxload,'operator_sha256':hashlib.sha256(p.read_bytes()).hexdigest()};q=D/'independent_readback.json';assert not q.exists();q.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
