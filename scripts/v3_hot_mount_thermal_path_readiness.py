#!/usr/bin/env python3
"""No-PDE source R3 hot mounting thermal pathway: 1D terms and topology STOP.
Uses original CAD physical face tags and named hypothesis bulk k.
DO NOT interpret 1D header full-patch area as a valid spreading bound.
"""
from pathlib import Path
import argparse,hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
FILES=[
 'data/v3_r32_global_surface_20261103/source_metadata.json',
 'data/synthetic_v3_assembly_20261102/source_final/design.json',
 'data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json',
 'data/v3_r3_sink_wire_20261107/attempt01/summary.json',
 'tecooledmct/materials.py',
 'docs/V3_INTERCONNECT_ELECTROTHERMAL_20261102.md']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def calculate():
 from tecooledmct.materials import KOVAR,ALUMINA_96,ALUMINA_HIGH_PURITY
 meta=read(ROOT/FILES[0]);cad=read(ROOT/FILES[1]);ports=read(ROOT/FILES[2]);results=read(ROOT/FILES[3])
 face=meta['faces']
 bodies={v['name']:v for v in cad['bodies']}
 stack=[('header_finish_Ni',2228,'VIGO_reference_header','header_finish_Ni',0.002,None,'NO RELEASE: composite effective tensor and plating unknown'),
        ('hot_mount_In52Sn48',2298,'header_finish_Ni','hot_mount_In52Sn48',0.080,30.,'ENGINEERING HYPOTHESIS: In52Sn48 k 30 W/m/K, NOT measured'),
        ('underside_Au',2303,'hot_mount_In52Sn48','underside_Au',0.00025,None,'NO RELEASE: composite multilayer k and interfaces unknown'),
        ('ceramic0',6,'underside_Au','ceramic0',0.500,ALUMINA_HIGH_PURITY.thermal_conductivity_w_mk,'ANALOG: CoorsTek AD995 99.5% alumina, NOT actual TEC grade')]
 assert ports['thermal_hot_stack_native_contact_sequence'][0]['source_face_tag']==2228
 terms=[]
 for name,tag,aa,bb,thickness,conductivity,confidence in stack:
  f=face[str(tag)]
  assert set(f['owners'])=={aa,bb},tag
  box=bodies[name]['boxes_mm'][0]
  assert abs(box[5]-thickness)<1e-10
  A=f['face_area_mm2']*1e-6
  R=(thickness*1e-3)/(conductivity*A) if conductivity is not None else None
  terms.append({'source_CAD_name':name,'source_face_tag':tag,'owner_pair':f['owners'],
   'source_registered_area_m2':A,'source_thickness_m':thickness*1e-3,
   'effective_thermal_conductivity_W_mK':conductivity,
   'one_dimensional_R_K_W_using_local_face_area':R,
   'applicability':'ASSUMED UNIFORM AXIAL HEAT FLOW, not full 3D or full device' if R is not None else 'UNRESOLVED',
   'evidence_status':confidence})
 # Header underside is the actual downward facing surface (z=0),
 # not the sum of its sidewalls/top and hole bore surfaces.
 underside=face['2225'];top=face['2226']
 assert underside['owners']==['VIGO_reference_header'] and underside['class_']=='EXTERIOR'
 assert abs(underside['center_mm'][2])<1e-10
 assert abs(top['center_mm'][2]-1.5)<1e-10
 assert abs(face['2298']['face_area_mm2']-36)<1e-8
 Acontact=36e-6;Aunder=underside['face_area_mm2']*1e-6
 Rheader_axial_small_patch=.0015/(KOVAR.thermal_conductivity_w_mk*Acontact)
 Rheader_axial_full_underside=.0015/(KOVAR.thermal_conductivity_w_mk*Aunder)
 # Two idealized 1D columns are not strict upper/lower bounds for 3D
 # lateral spreading with unspecified mounting contact distribution.
 Rmount=terms[1]['one_dimensional_R_K_W_using_local_face_area']
 Ra995=terms[3]['one_dimensional_R_K_W_using_local_face_area']
 Ra96=.0005/(ALUMINA_96.thermal_conductivity_w_mk*face['6']['face_area_mm2']*1e-6)
 # Do not assign the source-qualified interface coefficient.
 Rcontact_cold_start=None
 # actual prior sink bath heat rates, rather than pretending Q=IV
 sample=next(x for x in results['cases'] if x['hypothesis']=='nominal' and
       x['current_A']==.4 and x['sink_K_W']==5. and x['wires_mode']!='OFF')
 Q=sample['rejected_at_sink_W']
 assert .58<Q<.62
 # model in prior run R_sink=5 is effective hot CERAMIC->300K,
 # so mounting and header resistance are components of the same
 # equivalent path; they must NOT be simply added on top of 5K/W.
 terms_known=Rmount+Ra995
 assert all(x['law_status']=='UNSET' for x in (meta['domains']['ceramic0'],meta['domains']['hot_mount_In52Sn48']))
 out={
  'status':'STOP full hot mount resistance: geometry-derived 1D bulk terms identified; header spreading, contact and sink unknown',
  'source_frozen':True,'new_PDE_runs':0,'source_material_laws_modified':False,
  'hot_stack_R3_CAD_face_tags':[2228,2298,2303,6],
  'registered_bulk_path_terms':terms,
  'header':{
   'CAD_name':'VIGO_reference_header',
   'CAD_volume_id':meta['domains']['VIGO_reference_header']['id'],
   'original_exterior_underside_face_tag':2225,
   'actual_exterior_underside_area_m2':Aunder,
   'original_top_exterior_face_tag':2226,
   'original_top_exterior_area_m2':top['face_area_mm2']*1e-6,
   'mount_solder_contact_area_m2':Acontact,
   'contact_to_exterior_underside_area_ratio':Acontact/Aunder,
   'source_header_thickness_m':.0015,
   'reference_k_Kovar_W_mK':KOVAR.thermal_conductivity_w_mk,
   'header_1D_uniform_contact_patch_R_K_W':Rheader_axial_small_patch,
   'header_1D_uniform_entire_underside_R_K_W':Rheader_axial_full_underside,
   'spreading_solver':'NOT RUN',
   'both_1D_values_are_illustrative_not_true_mathematical_bounds':True,
   'real_sink_footprint_thermal_conductance_pressure_T':'UNKNOWN',
   'contact_sink_thermal_boundary':'UNSET'},
  'ceramic_k_ALUMINA_96_grade_proxy_W_mK':ALUMINA_96.thermal_conductivity_w_mk,
  'ceramic_1D_R_AD96_analog_K_W':Ra96,
  'ceramic_1D_R_AD995_analog_K_W':Ra995,
  'solder_In52Sn48_hypothesis_k_W_mK':30.,
  'solder_1D_R_hypothesis_K_W':Rmount,
  'two_bulk_layer_1D_sum_AD995_K_W':terms_known,
  'unreleased_hot_mount_terms':['header spreading and nonuniform heat flow',
   'header finish Ni composite tensor k and layer interfaces',
   'effective underside Au multilayer tensor k and layer interfaces',
   'In52Sn48 alloy k(T) and as-built joint geometry/void fraction',
   'Al2O3 actual grade k(T), nonuniform ceramic spreading and local pad heat',
   'finite solid-solid contact thermal area resistances at faces 2228/2298/2303/6',
   'actual exterior sink mounting footprint and sink/pad pressure/contact resistance',
   'actual header temperature field, external sink T and calorimetry'],
  'previous_R3_reference_case':{
   'hypothesis':'nominal','current_A':.4,'effective_sink_scenario_K_W':5.,
   'prior_T_hot_K':sample['temperatures_K']['hot_ceramic'],
   'prior_T_die_K':sample['temperatures_K']['MCT_die'],
   'prior_calculated_Q_sink_W':Q,
   'prior_assumed_transport_above_300K':True,
   'Q_based_illustrative_1D_deltaT_InSn_K':Q*Rmount,
   'Q_based_illustrative_1D_deltaT_Al2O3_AD995_K':Q*Ra995,
   'Q_based_illustrative_1D_deltaT_total_two_bulk_terms_K':Q*terms_known,
   'Q_based_1D_header_full_underside_K':Q*Rheader_axial_full_underside,
   'Q_based_1D_header_local_patch_K':Q*Rheader_axial_small_patch,
   'do_not_add_these_terms_to_existing_5_K_W_effective_sink':True},
  'source_input_SHA256':{f:sha(ROOT/f) for f in FILES},
  'gate_status':{'source_material_and_contact_laws':'UNSET',
   'old_original_P1_electrical_B':'FAIL/STOP','prospective_P2':'STOP',
   'physical_430_domain_C_D':'NOT RUN','as_built_detector_operating_T':'UNQUALIFIED'},
  'decision':'NO GO for a physically released R_sink: source mount/pad dimensions alone are insufficient for header spreading and external contact'}
 return out
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--out',type=Path)
 p.add_argument('--verify-only',action='store_true')
 args=p.parse_args()
 out=calculate()
 if args.verify_only:
  assert args.out and args.out.exists() and read(args.out)==out
 elif args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  with args.out.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print('HOT_MOUNT_NO_SOLVE',json.dumps({k:out[k] for k in ('solder_1D_R_hypothesis_K_W','ceramic_1D_R_AD995_analog_K_W','ceramic_1D_R_AD96_analog_K_W','two_bulk_layer_1D_sum_AD995_K_W','decision')},indent=2))
 print('SOURCE_HEADER_EXTERIOR_AREA_MM2',out['header']['actual_exterior_underside_area_m2']*1e6)
 print('Q_SINK_W',out['previous_R3_reference_case']['prior_calculated_Q_sink_W'])
if __name__=='__main__':main()
