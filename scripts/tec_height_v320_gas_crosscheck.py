"""Independent geometric/algebraic gas link and external proxy check."""
from pathlib import Path
import argparse,json,hashlib
from tecooledmct.integrated_reference import Scenario,gas_transport,radiative_load
from tecooledmct.height_coupling_v320 import ORIGINAL,CANDIDATE,read
R=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True,type=Path);a=p.parse_args();r=read(a.case/'result.json');d=read(ORIGINAL if r['variant']=='nominal' else CANDIDATE);b={x['name']:x for x in d['bodies']};cfg=Scenario(gas='Kr',cavity_pressure_pa=100.,accommodation=.8)
 n=r['source_full_temperature_nodes_K'];t=[n[k] for k in ('stage0_hot','stage0_cold','stage1_hot','stage1_cold','stage2_hot','stage2_cold','carrier','die')];qs=[];areas=[];gaps=[]
 for j in range(3):
  low=b[f'ceramic{j}']['boxes_mm'][0];up=b[f'ceramic{j+1}']['boxes_mm'][0];leg=[x for x in d['legs'] if x['stage']==j]
  solids=sum(b[f'leg{x["index"]}_{x["polarity"]}']['boxes_mm'][0][3]*b[f'leg{x["index"]}_{x["polarity"]}']['boxes_mm'][0][4] for x in leg)
  area=(up[3]*up[4]-solids)*1e-6;gap=(up[2]-(low[2]+low[5])-.03)*1e-3;k,jump,below=gas_transport(cfg,(t[2*j]+t[2*j+1])/2)
  assert not below and area>0 and gap>0;Q=k*area*(t[2*j]-t[2*j+1])/(gap+2*jump);qs.append(float(Q));areas.append(area);gaps.append(gap)
  assert abs(Q-r['internal_interstage_gas_heat_hot_to_cold_W'][j])<1e-12
 # Separate external branch as recorded, explicitly fixed 3mm proxy.
 ext=[];rad=[]
 for j,(A,cold) in enumerate(zip(r['source_exposed_effective_surface_area_m2'],[t[2],t[4],t[6],t[7]])):
  k,jump,below=gas_transport(cfg,(300+cold)/2);q=k*A*(300-cold)/(.003+2*jump);ext.append(float(q))
  eps=.1 if j==3 else .2;view=.7 if j==3 else .5;rad.append(float(radiative_load(300,cold,A,eps,.8,view)))
  assert abs(q-r['cavity_gas_heat_into_three_ceramics_and_die_W'][j])<1e-12
  assert abs(rad[-1]-r['gray_radiation_heat_into_three_ceramics_and_die_W'][j])<1e-12
 bvec=[-qs[0],qs[0]-qs[1],qs[1]-qs[2],qs[2]];assert abs(sum(bvec))<1e-15
 out={'status':'PASS independent geometry/algebra and equal/opposite gas heat; native cavity is NOT validated','area_m2':areas,'gap_m':gaps,'interstage_W':qs,'stage_heat_into_plates_W':bvec,'external_proxy_gas_W':ext,'external_proxy_radiation_W':rad,'source_result_sha256':hashlib.sha256((a.case/'result.json').read_bytes()).hexdigest()}
 (a.case/'gas_crosscheck.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
