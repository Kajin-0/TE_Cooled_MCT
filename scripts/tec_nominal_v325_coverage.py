"""Report disjoint area and honest partial-face/lead-endpoint status."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_p1_20261111'
def main():
 f=json.loads((R/'data/nominal_gas_coupler_20261110/nominal_face_temperature_map.json').read_text());o=json.loads((D/'p1_operator.json').read_text());source=json.loads((R/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text());r=json.loads((R/'data/tec_height_coupling_20261110/nominal/result.json').read_text());subset=json.loads((R/'data/nominal_gas_coupler_20261110/source_bare_column_subset.json').read_text());selected={tag for x in subset['patches'] for tag in (x['hot_gas_face_tag'],x['cold_gas_face_tag'])};assert selected=={7,43,73,91,103,113}
 unresolved=defaultdict(lambda:{'faces':0,'area_mm2':0.});joints=[]
 for x in f['entries']:
  m=x['mapping']
  if m['status']=='UNRESOLVED':unresolved[x['semantic_category']]['faces']+=1;unresolved[x['semantic_category']]['area_mm2']+=x['area_mm2']
  if m['status']=='SOURCE_CONTACT_ENDPOINT_PROXY':
   name=x['solid_domain'];pin='1' if name.startswith('lead1_') else '9';side='land' if '_land_' in name else 'pin';wire='TEC_lead'+pin;mate=('net0_plane0.500_Au' if pin=='1' else 'net88_plane0.500_Au') if side=='land' else 'pin'+pin+'_Au'
   witness=[c for c in source['explicit_contacts'] if name in (c['a'],c['b'])];assert any({c['a'],c['b']}=={name,wire} for c in witness) and any({c['a'],c['b']}=={name,mate} for c in witness)
   T=r['source_tec_power_leads']['per_lead'][wire]['temperature_pad_K' if side=='land' else 'temperature_header_K'];assert abs(T-m['temperature_K'])<1e-12
   joints.append({'face_tag':x['face_tag'],'source_joint':name,'witness_contacts':witness,'endpoint_model_temperature_K':T,'temperature_scope':'exact endpoint bookkeeping in reduced lead model; physical joint temperature and drop unqualified'})
 assert len(joints)==8 and sum(x['faces'] for x in unresolved.values())==173
 A=sum(x['overlap_area_mm2'] for x in o['summary']['area_rows'])*2;total=f['face_area_mm2'];out={'observed_UTC':datetime.now(timezone.utc).isoformat(),'status':'PASS accounting; P1 face subpatches only, all other mappings provisional/unresolved','whole_gas_faces':1840,'whole_gas_area_mm2':total,'P1_partially_covered_face_count':len(selected),'P1_subface_area_mm2_both_sides':A,'P1_area_percent':100*A/total,'P1_unallocated_other_area_mm2':total-A,'fully_covered_gas_faces':0,'provisional_map_faces':f['approx_mapped_faces'],'provisional_map_area_mm2':f['approx_mapped_area_mm2'],'unresolved_map_faces':173,'unresolved_area_mm2':f['groups']['UNRESOLVED']['area_mm2'],'unresolved_categories':dict(unresolved),'qualified_full_cavity_gas_BC_faces':0,'lead_joint_endpoint_proxies':joints,'note':'partial P1 face count and provisional/proxy categories overlap; area counts only paired bare subpatches, not physical gas validation'}
 p=D/'coverage_and_lead_audit.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='lead_joint_endpoint_proxies'},indent=2))
if __name__=='__main__':main()
