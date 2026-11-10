"""Inventory archived nominal gas faces without inventing gas boundary conditions."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,math,re
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_ports_20261110'
META=R/'data/v3_r32_global_surface_20261103/source_metadata.json';SOURCE=R/'data/synthetic_v3_assembly_20261102/source_final/design.json';BASE=R/'data/tec_height_coupling_20261110/nominal/result.json';AUDIT=R/'data/tec_height_coupling_20261110/nominal/independent_audit.json'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def classify(owner,body,centre):
 """Semantic destination is informational; no gas boundary operator is installed."""
 if re.fullmatch(r'ceramic[0-3]',owner):return 'ceramic_field',owner,'3D ceramic exists; gas-face interpolation NOT IMPLEMENTED'
 if owner.startswith('net') and '_plane' in owner:
  return 'patterned_metal',f"net{body.get('net','?')}@plane{body.get('plane','?')}",'spatial net surface, not an isothermal node; gas coupling NOT IMPLEMENTED'
 if owner.startswith('formed_tab'):
  return 'formed_copper',owner,'1D multisegment thermal model exists; gas surface-to-segment mapping NOT IMPLEMENTED'
 if re.fullmatch(r'leg\d+_[NP]',owner):
  return 'PN_leg',owner,'nonlinear axial leg model exists; distributed side-gas coupling NOT IMPLEMENTED'
 if owner.startswith('solder') or owner.startswith('tab_joint') or owner.startswith('fillet'):
  return 'joint_or_fillet',owner,'joint location known; gas port and thermal split NOT IMPLEMENTED'
 if owner.startswith('detector_bond') or owner.startswith('TEC_lead') or owner.startswith('lead1_insulation') or owner.startswith('lead9_insulation'):
  return 'lead_or_insulation',owner,'lead is distributed; surface gas/insulation coupling NOT IMPLEMENTED'
 if owner in ('cap_shell','cap_roof','window'):
  return 'housing_window',owner,'ideal CAD wall; spatial/thermal wall model and seal qualification NOT IMPLEMENTED'
 if owner in ('VIGO_reference_header','header_finish_Ni') or re.fullmatch(r'(pin|glass)\d+(_.*)?',owner):
  return 'header_pin_seal',owner,'nominal bath connection is a reduced approximation; gas-face coupling NOT IMPLEMENTED'
 if owner in ('p_HgCdTe_photoconductor','sapphire_carrier') or owner.startswith(('die_attach','carrier_attach','det7_','det8_','cold_finish')):
  return 'die_carrier_attach',owner,'die/carrier thermal node or attach exists; exact face mapping NOT IMPLEMENTED'
 if owner.startswith('underside_') or owner.startswith('hot_mount_'):
  return 'mount_interface',owner,'mount contact has reduced resistance; distributed gas port NOT IMPLEMENTED'
 return 'unresolved',owner,'source owner recognized but thermal destination not established'

def build(meta,source):
 by={x['name']:x for x in source['bodies']};domains=meta['domains'];registry=meta['face_registry'];faces=[];seen=set();cats=defaultdict(lambda:{'count':0,'area_mm2':0.})
 for key,v in sorted(meta['faces'].items(),key=lambda x:int(x[0])):
  if v['class_']!='GAS_SOLID':continue
  tag=int(key);assert tag==v['face_tag'] and tag not in seen;seen.add(tag)
  assert len(v['owners'])==2 and v['owners'].count('CAVITY_GAS')==1 and len(v['orientation_signs'])==2 and sum(v['orientation_signs'])==0 and set(v['orientation_signs'])=={-1,1}
  side=1-v['owners'].index('CAVITY_GAS');owner=v['owners'][side];vol=v['owner_volume_ids'];assert vol[v['owners'].index('CAVITY_GAS')]==430 and vol[side]==domains[owner]['id']
  ref=registry[str(tag)];assert ref['owners']==v['owners'] and ref['orientation_signs']==v['orientation_signs'] and ref['face_area_mm2']==v['face_area_mm2']
  area=float(v['face_area_mm2']);assert math.isfinite(area) and area>0
  src=domains[owner]['sources'];assert src and all(name in by for name in src),(owner,src)
  body=by.get(owner,{});cat,node,status=classify(owner,body,v['center_mm']);cats[cat]['count']+=1;cats[cat]['area_mm2']+=area
  faces.append({'face_tag':tag,'solid_domain':owner,'solid_volume_id':vol[side],'gas_volume_id':430,'area_mm2':area,'centre_mm':v['center_mm'],'bbox_mm':v['bbox_mm'],'cad_surface_type':v['type'],'gas_orientation_sign':v['orientation_signs'][v['owners'].index('CAVITY_GAS')],'solid_orientation_sign':v['orientation_signs'][side],'physical_sources':src,'semantic_category':cat,'semantic_node_or_element':node,'thermal_mapping_status':status,'gas_boundary_condition_installed':False})
 assert len(faces)==1840 and len(seen)==1840
 return {'status':'PASS archival nominal CSG face ownership inventory; gas transfer operator NOT QUALIFIED','geometry_scope':'derived nominal R3 analysis geometry: coalesced layers and ideal enclosure, not as-built package','gas_domain':430,'nominal_gas_volume_mm3':meta['gas_volume_mm3'],'count':len(faces),'area_mm2':sum(x['area_mm2'] for x in faces),'unique_solid_owners':len({x['solid_domain'] for x in faces}),'semantic_categories':dict(cats),'gas_boundary_conditions_installed':0,'faces':faces}

def main():
 reg=read(D/'registration.json')
 for p,h in reg['source_sha256'].items():assert sha(R/p)==h,p
 source=read(SOURCE);assert len(source['bodies'])==824 and len(source['legs'])==88
 result=build(read(META),source);result['source_metadata_sha256']=sha(META);result['physical_source_sha256']=sha(SOURCE)
 p=D/'nominal_gas_face_ports.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 r=read(BASE);a=read(AUDIT);assert sha(BASE)==a['result_sha256'] and a['status'].startswith('PASS') and r['variant']=='nominal'
 legs=Counter(x['stage'] for x in source['legs']);assert [legs[i] for i in range(3)]==[58,22,8]
 m={'status':'CONDITIONAL synthetic original reference; not experimentally validated','design_source_sha256':sha(SOURCE),'source_824_solids':True,'leg_cross_section_mm':[.4,.4],'leg_length_mm':.5,'couples_by_stage':[29,11,4], 'gas_face_registry_sha256':sha(p),'conditions':{'ambient_K':300,'Kr_pressure_Pa':100,'imposed_die_W':.002,'electrical_power_W':r['electrical_power_W']},'reference':{'case':'V3.20 nominal with internal plus external proxy gas','result_sha256':sha(BASE),'independent_audit_sha256':sha(AUDIT),'current_A':r['operating_current_A'],'voltage_V':r['terminal_voltage_V'],'power_W':r['electrical_power_W'],'die_K':r['calculated_detector_temperature_K'],'top_ceramic_K':r['source_full_temperature_nodes_K']['carrier'],'hot_ceramic_K':r['source_full_temperature_nodes_K']['stage0_hot'],'bath_W':r['bath_heat_rejected_W'],'stage_budget':r['source_stage_thermoelectric_budget'],'external_gas_W':r['cavity_gas_heat_into_three_ceramics_and_die_W'],'internal_gas_W':r['internal_interstage_gas_heat_hot_to_cold_W'],'radiation_W':r['gray_radiation_heat_into_three_ceramics_and_die_W'],'copper_stage_heat_W':r['Cu_form_tab_heat_into_ceramic_by_stage_W'],'lead_model':r['source_tec_power_leads'],'audit':a},'operators':{'PN':'88 nonlinear 1D source research legs; >300K assumed','ceramics':'four source 3D ceramic FEM fields','copper':'reduced 1D multiport, 3D electrical gate FAIL/STOP','leads':'reduced thermal/electrical wires','gas':'overlapping-possible external and interstage approximations, no source-native gas-face BC','radiation':'effective gray proxy','detector':'2mW thermal load only','heat_sink':'finite external mount proxy','calibration':'no measured experimental validation'},'unresolved':['per-face gas thermal mapping and contact law','metal temperature interpolation','native gas-flux 32.6274% FAIL','native 3D metal electrical gate FAIL/STOP','package sealing and actual specimen properties']}
 operator_paths={'coupled_nominal':'scripts/tec_height_v320_coupled.py','nonlinear_leg':'tecooledmct/nonlinear_tec.py','source_transport':'tecooledmct/graded_tec.py','ceramic_field':'scripts/v2_source_ceramic_spatial.py','copper_multiport':'scripts/v3_4_source_copper_multiport.py','lead_wire':'scripts/v3_5_supply_lead_boundary.py','gas_radiation':'tecooledmct/integrated_reference.py','gas_properties':'tecooledmct/fem_g3b_exchange.py'}
 m['operator_sources']={k:{'path':v,'sha256':sha(R/v)} for k,v in operator_paths.items()}
 step=R/'data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step';legacy=R/'data/v3_11_rev3_backfill_source_20261109/Kr100_I040/result.json';legacy_audit=R/'data/v3_11_rev3_backfill_source_20261109/Kr100_I040/independent_energy_audit.json';r11=read(legacy);a11=read(legacy_audit);assert a11['result_sha256']==sha(legacy) and a11['verdict'].startswith('PASS')
 m['original_STEP']={'path':str(step.relative_to(R)),'sha256':sha(step)}
 m['historical_v311_different_proxy']={'path':str(legacy.relative_to(R)),'sha256':sha(legacy),'audit_sha256':sha(legacy_audit),'I_A':r11['operating_current_A'],'power_W':r11['electrical_power_W'],'die_K':r11['calculated_detector_temperature_K'],'note':'different gas and net88 model from V3.20, not a measurement'}
 f=D/'nominal_reference.json';assert not f.exists();f.write_text(json.dumps(m,indent=2,allow_nan=False)+'\n')
 print('faces',result['count'],'owners',result['unique_solid_owners'],'area mm2',result['area_mm2']);print(json.dumps(result['semantic_categories'],indent=2));print('ready gas-face boundary conditions',result['gas_boundary_conditions_installed'])
if __name__=='__main__':main()
