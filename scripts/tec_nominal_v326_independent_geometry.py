"""Independent sampled source-centerline geometry and saved 1D map readback."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,numpy as np
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_metal_v326_20261111'
def main():
 graph=json.loads((D/'face_temperature_graph.json').read_text());design=json.loads((R/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text());bodies={x['name']:x for x in design['bodies']};r=json.loads((R/'data/nominal_gas_p1_20261111/coupled_attempt01/result.json').read_text());worst_s=0.;worst_d=0.;worst_t=0.;n=0
 for f in graph['entries']:
  m=f['mapping']
  if m['status']!='CONDITIONAL_DISTRIBUTED_TAB_CENTERLINE':continue
  b=bodies[f['solid_domain']];p=np.asarray(f['centroid_mm'][1:]);best=(float('inf'),None);s=0.
  for part in b['parts']:
   u=np.linspace(0,1,1001);a=np.array(part['a']);z=np.array(part['b'])
   if part['type']=='line':samples=a[None,:]+u[:,None]*(z-a)
   elif part['type']=='arc':
    c=np.array(part['c']);a0=math.atan2(*(a-c)[::-1]);a1=math.atan2(*(z-c)[::-1]);ang=(a1-a0+math.pi)%(2*math.pi)-math.pi;theta=a0+u*ang;samples=c[None,:]+part['r']*np.column_stack((np.cos(theta),np.sin(theta)))
   else:raise ValueError('unknown source geometry')
   dist=np.linalg.norm(samples-p,axis=1);j=int(np.argmin(dist));cand=(float(dist[j]),s+float(u[j])*part['length']);best=min(best,cand,key=lambda x:x[0]);s+=part['length']
  worst_d=max(worst_d,abs(best[0]-m['centroid_to_centerline_mm']));worst_s=max(worst_s,abs(best[1]-m['arclength_from_source_start_mm']));net=r['Cu_form_tab_electrothermal_result']['net_details'][str(m['net'])];j=m['segment'];u=m['local_segment_fraction'];T0,T1=net['foil_node_temperature_K'][j:j+2];power=r['operating_current_A']**2*net['metal_electrical_segment_R_ohm'][j];g=net['thermal_segment_conductance_W_K'][j];T=(1-u)*T0+u*T1+power/(2*g)*u*(1-u);worst_t=max(worst_t,abs(T-m['temperature_K']));n+=1
 assert n==39 and worst_s<.001 and worst_d<1e-5 and worst_t<1e-12
 out={'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS independent dense sampled centerline and independent source-node Joule readback','checked_faces':n,'max_sampled_arclength_difference_mm':worst_s,'max_sampled_distance_difference_mm':worst_d,'max_temperature_difference_K':worst_t,'face_graph_sha256':hashlib.sha256((D/'face_temperature_graph.json').read_bytes()).hexdigest(),'sampling':'1001 points per original line/arc; empirical sampling comparator, not independent CAD trim or gas visibility'};(D/'independent_geometry_readback.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
