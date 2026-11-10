"""Independent re-derivation of source-metal and lead heat/current partitions."""
from pathlib import Path
import argparse,json,hashlib,numpy as np,math
from tecooledmct.height_coupling_v320 import ORIGINAL,CANDIDATE,read
R=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True,type=Path);a=p.parse_args();r=read(a.case/'result.json');d=read(ORIGINAL if r['variant']=='nominal' else CANDIDATE);b={x['name']:x for x in d['bodies']};I=r['operating_current_A'];out=[]
 for net,ids in ((58,(0,1)),(80,(2,3)),(88,(4,5,6))):
  q=r['Cu_form_tab_electrothermal_result']['net_details'][str(net)];body=b[f'formed_tab{net}'];parts=body['parts'];L=[x['length']*1e-3 for x in parts];feet=[b[f'tab_joint{i}'] for i in ids];y=[(x['bbox_mm'][1]+x['bbox_mm'][4])/2 for x in feet];initial=abs(parts[0]['a'][0]-y[0])*1e-3;last=abs(parts[-1]['b'][0]-y[-1])*1e-3
  if net==88:
   first=sum(L[:4])+(parts[4]['a'][0]-y[1])*1e-3-initial;segs=np.array([first,sum(L)-initial-last-first])
  else:segs=np.array([sum(L)-initial-last])
  area=body['width']*body['thickness']*1e-6;T=np.array(q['plate_temperature_K']);Tf=np.array(q['foil_node_temperature_K']);resist=1.724e-8*(1+.0039*((T[:-1]+T[1:])/2-293.15))*segs/area
  Ac=np.array([(x['bbox_mm'][3]-x['bbox_mm'][0])*(x['bbox_mm'][4]-x['bbox_mm'][1])*1e-6 for x in feet]);re=1e-11/Ac
  if net==88:re[1]=0
  joule=I*I*resist;injection=np.zeros(len(T));injection[:-1]+=.5*joule;injection[1:]+=.5*joule
  G=385*area/segs;Q=Ac/1e-6*(Tf-T)+I*I*re
  assert np.allclose(Q,q['face_heat_into_ceramic_W'],atol=1e-12,rtol=0)
  balance=Ac/1e-6*(Tf-T)-injection;balance[:-1]+=G*(Tf[:-1]-Tf[1:]);balance[1:]-=G*(Tf[:-1]-Tf[1:])
  assert max(abs(balance))<1e-12 and abs(sum(Q)-I*I*(sum(resist)+sum(re)))<1e-12
  out.append({'net':net,'max_foil_node_energy_error_W':float(max(abs(balance))),'port_heat_W':Q.tolist(),'electrical_W':float(I*I*(sum(resist)+sum(re)))})
 leads=[]
 for name,v in r['source_tec_power_leads']['per_lead'].items():
  w=b[name];length=sum(x['length'] for x in w['parts'])*1e-3;area=math.pi*(w['radius']*1e-3)**2;res=1.72e-8*length/area;conduct=400*area/length*(300-v['temperature_pad_K']);power=I*I*res
  assert abs(res-v['R_ohm'])<1e-12 and abs(conduct-v['conduction_into_tec_W'])<1e-12 and abs(power-v['joule_wire_W'])<1e-12 and abs(conduct+.5*power-v['heat_into_tec_pad_W'])<1e-12
  leads.append({'name':name,'length_m':length,'conduction_W':conduct,'joule_W':power})
 result={'status':'PASS independently reconstructed 3 copper port networks and 2 lead pathways','copper':out,'leads':leads,'source_result_sha256':hashlib.sha256((a.case/'result.json').read_bytes()).hexdigest()}
 (a.case/'ports_crosscheck.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
