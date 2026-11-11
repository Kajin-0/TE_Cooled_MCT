"""Map original formed-tab source faces to saved, non-isothermal Cu thermal paths."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import hashlib,json,math
from tecooledmct.nominal_cavity_metal_v326 import project_yz,segment_profile
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_metal_v326_20261111'
def read(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
def main():
 reg=read('data/nominal_cavity_metal_v326_20261111/registration.json')
 for p,h in reg['source_sha256'].items():assert sha(p)==h,p
 design=read('data/synthetic_v3_assembly_20261102/source_final/design.json');bodies={b['name']:b for b in design['bodies']};old=read('data/nominal_gas_coupler_20261110/nominal_face_temperature_map.json');result=read('data/nominal_gas_p1_20261111/coupled_attempt01/result.json');nets=result['Cu_form_tab_electrothermal_result']['net_details'];I=result['operating_current_A']
 # Each source tab has three-dimensional y-z centerline with source x/width.
 # Source solver places first and last thermal nodes at joining-foot centers.
 # On broad planar side faces the CAD area centroid can lie well off this bent
 # centerline; reject such faces rather than silently pretending a local sample.
 entries=[];groups=defaultdict(lambda:{'faces':0,'area_mm2':0.});by_net=defaultdict(list)
 for f in old['entries']:
  o={'face_tag':f['face_tag'],'solid_domain':f['solid_domain'],'semantic_category':f['semantic_category'],'area_mm2':f['area_mm2'],'centroid_mm':f['centroid_mm'],'source_face_registry_sha256':old['source_face_registry_sha256'],'mapping':f['mapping'].copy()}
  if f['semantic_category']=='formed_copper':
   body=bodies[f['solid_domain']];net=int(body['group']);d=nets[str(net)];point=f['centroid_mm'];distance,s=project_yz(body['parts'],point[1:]);start=0.15;end=sum(p['length'] for p in body['parts'])-0.15;segments=[x*1e3 for x in d['segment_length_m']];assert abs(sum(segments)-(end-start))<1e-10
   # Face centroids of circular sectors can lie inside the actual material;
   # 0.025 mm admits the exact 0.020981 mm sector-centroid distance, but
   # rejects broad concave side-face centroids (>=0.0379 mm).
   valid=distance<=0.025+1e-10 and abs(point[0]-body['x'])<=body['width']/2+1e-9 and start-1e-10<=s<=end+1e-10
   if valid:
    s=min(end,max(start,s));j=0 if len(segments)==1 or s<=start+segments[0] else 1;left=start+sum(segments[:j]);u=(s-left)/segments[j];u=min(1.,max(0.,u));T,q0,q1=segment_profile(u,d['foil_node_temperature_K'][j],d['foil_node_temperature_K'][j+1],d['metal_electrical_segment_R_ohm'][j],d['thermal_segment_conductance_W_K'][j],I)
    m={'status':'CONDITIONAL_DISTRIBUTED_TAB_CENTERLINE','net':net,'segment':j,'arclength_from_source_start_mm':s,'local_segment_fraction':u,'endpoint_nodes':[f'tab{net}:foil_node:{j}',f'tab{net}:foil_node:{j+1}'],'endpoint_weights':[1-u,u],'foil_endpoint_temperature_K':d['foil_node_temperature_K'][j:j+2],'temperature_K':T,'joule_rise_K':T-((1-u)*d['foil_node_temperature_K'][j]+u*d['foil_node_temperature_K'][j+1]),'source_contact_thermal_resistance_m2K_W':1e-6,'centroid_to_centerline_mm':distance,'model':'1D constant-k constant-cross-section source segment; uniform segment Joule generation, no surface gas heat; illustrative conditional value, not measured face field','segment_heat_into_conductor_W':[q0,q1]};by_net[net].append(m)
   else:
    m={'status':'UNRESOLVED','reason':'source face centroid cannot localize on modeled contact-centered path (outside span or broad curved-face centroid)','net':net,'centroid_to_centerline_mm':distance,'source_arclength_mm':s,'contact_span_mm':[start,end]}
   o['mapping']=m
  status=o['mapping']['status'];groups[status]['faces']+=1;groups[status]['area_mm2']+=f['area_mm2'];entries.append(o)
 assert len(entries)==1840 and len({e['face_tag'] for e in entries})==1840 and abs(sum(x['area_mm2'] for x in entries)-903.2150497910573)<1e-8
 summary={}
 for net,values in sorted(by_net.items()):
  n=nets[str(net)];temps=[x['temperature_K'] for x in values];summary[str(net)]={'faces':len(values),'area_mm2':sum(e['area_mm2'] for e in entries if e['mapping']['status']=='CONDITIONAL_DISTRIBUTED_TAB_CENTERLINE' and e['mapping']['net']==net),'temperature_span_K':[min(temps),max(temps)],'foil_node_temperature_K':n['foil_node_temperature_K'],'max_joule_profile_rise_K':max(v['joule_rise_K'] for v in values)}
 out={'status':'PASS conditional 1D tab surface-centroid model; unqualified complete cavity','observed_utc':datetime.now(timezone.utc).isoformat(),'baseline_result_sha256':sha('data/nominal_gas_p1_20261111/coupled_attempt01/result.json'),'registry_sha256':old['source_face_registry_sha256'],'total_faces':len(entries),'total_area_mm2':sum(e['area_mm2'] for e in entries),'groups':dict(groups),'tab_summary':summary,'entries':entries};p=D/'face_temperature_graph.json';assert not p.exists();p.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='entries'},indent=2))
if __name__=='__main__':main()
