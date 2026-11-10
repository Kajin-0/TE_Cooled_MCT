"""Map nominal R3 gas faces to saved nominal thermal representations.

Nearest-node and endpoint/linear models are explicitly provisional, never
qualified native-gas boundary conditions. No new physics solve is performed.
"""
from pathlib import Path
from collections import Counter
import json,hashlib,re,math
import numpy as np
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_coupler_20261110'
def read(p):return json.loads(p.read_text())
def main():
 design=read(R/'data/synthetic_v3_assembly_20261102/source_final/design.json');by={b['name']:b for b in design['bodies']};faces=read(R/'data/nominal_cavity_ports_20261110/nominal_gas_face_ports.json')['faces'];result=read(R/'data/tec_height_coupling_20261110/nominal/result.json');legs={r['original_leg_name']:r for r in result['source_individual_leg_flux_and_electric_results']};n=result['source_full_temperature_nodes_K'];lead=result['source_tec_power_leads']['per_lead'];contacts=design['explicit_contacts'];npz=np.load(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz',allow_pickle=False);fields=[]
 for i in range(4):
  xyz=npz[f'ceramic{i}_xyz_mm'];fields.append((xyz,npz[f'ceramic{i}_temperature_K'],npz[f'ceramic{i}_source_node_id_1based'],cKDTree(xyz)))
 def nearest(point,only=None):
  cand=[]
  for i,(xyz,t,ids,tree) in enumerate(fields):
   if only is not None and i!=only:continue
   distance,j=tree.query(point);cand.append((float(distance),i,int(j),xyz,t,ids))
  dist,i,j,xyz,t,ids=min(cand,key=lambda x:x[0]);return {'temperature_K':float(t[j]),'nodes':[{'id':f'ceramic{i}:node:{int(ids[j])}','weight':1.}],'sample_distance_mm':dist,'sample_xyz_mm':xyz[j].tolist()}
 meta_hash=hashlib.sha256((R/'data/v3_r32_global_surface_20261103/source_metadata.json').read_bytes()).hexdigest()
 out=[]
 for f in faces:
  name=f['solid_domain'];point=f['centre_mm'];cat=f['semantic_category'];b=by.get(name,{});m={'status':'UNRESOLVED','reason':'no source-verified local temperature model for this face'}
  if cat=='ceramic_field':
   m=nearest(point,int(name[-1]));m.update(status='NEAREST_SOURCE_CERAMIC_NODE_PROXY',reason='nearest node at face centroid; not finite-element interpolation or qualified gas BC')
  elif cat=='patterned_metal':
   m=nearest(point);m.update(status='NEAREST_CERAMIC_NODE_METAL_PROXY',reason='assumes locally negligible film/ceramic temperature drop; no in-plane metal field')
  elif cat=='PN_leg':
   r=legs[name];q=b['boxes_mm'][0];u=(point[2]-q[2])/q[5]
   if not -1e-6<=u<=1+1e-6:raise ValueError((name,u))
   m={'status':'LINEAR_LEG_ENDPOINT_PROXY','temperature_K':(1-u)*r['Th_K']+u*r['Tc_K'],'nodes':[{'id':name+':hot','weight':1-u},{'id':name+':cold','weight':u}],'reason':'linear interpolation between archived endpoints; not the nonlinear BVP interior profile'}
  elif re.fullmatch(r'solder\d+_(hot|cold)',name):
   k=re.match(r'solder(\d+)_(hot|cold)',name);legname=f'leg{k[1]}_'+next(x['polarity'] for x in design['legs'] if x['index']==int(k[1]));r=legs[legname];side=k[2];m={'status':'LEG_ENDPOINT_JOINT_PROXY','temperature_K':r['Th_K' if side=='hot' else 'Tc_K'],'nodes':[{'id':legname+':'+side,'weight':1.}],'reason':'joint approximated at adjoining leg endpoint; joint temperature drop not resolved'}
  elif re.fullmatch(r'lead[19]_(land|pin)_joint',name):
   k=re.match(r'lead([19])_(land|pin)_joint',name);pin=int(k[1]);side=k[2];wire=f'TEC_lead{pin}';peer=(f'net{0 if pin==1 else 88}_plane0.500_Au' if side=='land' else f'pin{pin}_Au');assert any({c['a'],c['b']}=={name,wire} for c in contacts) and any({c['a'],c['b']}=={name,peer} for c in contacts)
   T=lead[wire]['temperature_pad_K' if side=='land' else 'temperature_header_K'];node=(f'ceramic0:pad_face:{lead[wire]["face"]}' if side=='land' else f'pin{pin}:header_endpoint');m={'status':'SOURCE_CONTACT_ENDPOINT_PROXY','temperature_K':T,'nodes':[{'id':node,'weight':1.}],'reason':'source joint contacts both wire and '+peer+'; zero joint temperature drop is an unqualified endpoint approximation','source_contacts':[wire,peer]}
  elif cat=='housing_window':m={'status':'RESERVOIR_TEMPERATURE_PROXY','temperature_K':300.,'nodes':[{'id':'ambient_reservoir','weight':1.}],'reason':'existing 300 K external proxy; no wall-temperature field or seal qualification'}
  elif cat=='header_pin_seal':m={'status':'HEADER_RESERVOIR_PROXY','temperature_K':300.,'nodes':[{'id':'header_reservoir','weight':1.}],'reason':'existing header endpoint assumption; pin/seal spatial fields not solved'}
  elif name=='p_HgCdTe_photoconductor':m={'status':'DIE_LUMPED_NODE_PROXY','temperature_K':n['die'],'nodes':[{'id':'die','weight':1.}],'reason':'existing lumped thermal die, not detector electronics'}
  elif name=='sapphire_carrier':m={'status':'CARRIER_LUMPED_NODE_PROXY','temperature_K':n['carrier'],'nodes':[{'id':'carrier','weight':1.}],'reason':'existing carrier temperature node; no 3D carrier field'}
  out.append({'face_tag':f['face_tag'],'solid_domain':name,'semantic_category':cat,'area_mm2':f['area_mm2'],'centroid_mm':point,'original_R3_registry_sha256':meta_hash,'thermal_model':'V3.20 archived nominal, proxy mapping V3.24','mapping':m})
 total=sum(x['area_mm2'] for x in out);resolved=[x for x in out if x['mapping']['status']!='UNRESOLVED'];leadface=[x for x in out if re.fullmatch(r'lead[19]_(land|pin)_joint',x['solid_domain'])];assert len(out)==1840 and len(leadface)==8 and all(x['mapping']['status']=='SOURCE_CONTACT_ENDPOINT_PROXY' for x in leadface)
 groups={}
 for status in sorted({x['mapping']['status'] for x in out}):
  rr=[x for x in out if x['mapping']['status']==status];groups[status]={'faces':len(rr),'area_mm2':sum(x['area_mm2'] for x in rr)}
 obj={'status':'PROVISIONAL original-only source thermal representations; all gas BCs unqualified','source_face_registry_sha256':hashlib.sha256((R/'data/nominal_cavity_ports_20261110/nominal_gas_face_ports.json').read_bytes()).hexdigest(),'source_state_sha256':hashlib.sha256((R/'data/tec_height_coupling_20261110/nominal/result.json').read_bytes()).hexdigest(),'faces':len(out),'face_area_mm2':total,'approx_mapped_faces':len(resolved),'approx_mapped_area_mm2':sum(x['area_mm2'] for x in resolved),'qualified_gas_BC_faces':0,'lead_joint_faces_source_endpoint_proxy':len(leadface),'groups':groups,'entries':out}
 p=D/'nominal_face_temperature_map.json';assert not p.exists();p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n');print({k:v for k,v in obj.items() if k!='entries'})
if __name__=='__main__':main()
