#!/usr/bin/env python3
"""V3 OEM heat-sink-guidance boundary audit: exact source CAD, no new PDE.

Keep VIGO recommended radiator-to-air ~2 K/W separate from
unknown header-to-radiator thermal interface. One existing one-mesh
3D header component, one illustrative 1D solder/ceramic estimate.
Never add components to the earlier reduced total effective sink R.
"""
from pathlib import Path
import hashlib,json,argparse
ROOT=Path(__file__).resolve().parents[1]
HOT=ROOT/'data/v3_hot_mount_readiness_20261107/attempt01/thermal_path_audit.json'
HEADER=ROOT/'data/v3_r3_header_spreading_20261107/attempt01/result.json'
SOURCE=ROOT/'data/v3_tec_source_identity_20261107/attempt01/source_identity_gate.json'
CAD=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
OEM_URL='https://vigophotonics.com/app/uploads/2024/07/Thermoelectric-cooling-heat-sinking.pdf'
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
def j(x):return json.loads(x.read_text())
def build():
 hot=j(HOT);head=j(HEADER);identity=j(SOURCE);cad=j(CAD)
 assert len(cad['domains'])==430 and len(cad['faces'])==2440
 assert head['original_CAD_Kovar_header_volume_ID']==386
 assert head['original_bottom_sink_face_tag']==2225
 assert head['original_top_source_face_tag']==2228
 assert hot['hot_stack_R3_CAD_face_tags']==[2228,2298,2303,6]
 assert head['3D_full_430_domain_C_D']=='NOT RUN'
 assert identity['as_built_module_identification']=='UNKNOWN'
 Q=head['source_power_W']
 assert abs(Q-hot['previous_R3_reference_case']['prior_calculated_Q_sink_W'])<1e-12
 R_solder=hot['solder_1D_R_hypothesis_K_W']
 R_ceramic=hot['ceramic_1D_R_AD995_analog_K_W']
 R_header=head['mean_face_temperature_weighted_effective_header_R_K_W']
 R_radiator=2.
 # Independent physical roles: bulk header, solder, ceramic and
 # radiator environmental boundary; all mounting/interfacial values UNSET
 line=[('ceramic0_through_thickness_1D_analog',R_ceramic),
       ('hot_In52Sn48_1D_hypothesis',R_solder),
       ('Kovar_header_original_mesh_3D_one_BC',R_header),
       ('radiator_heatsink_to_environment_OEM_typical_recommendation',R_radiator)]
 R_known=sum(v for _,v in line)
 return {
  'status':'SOURCE-QUALIFIED DESIGN GUIDANCE ACQUIRED; PHYSICAL AS-BUILT SINK CONTACT AND FULL TEC STILL STOP',
  'OEM':{
   'manufacturer':'VIGO Photonics',
   'title':'Thermoelectric cooling, heat sinking',
   'revision':'V3.0 11.09.2025',
   'document_url':OEM_URL,
   'document_page':1,
   'recommended_heatsink_to_environment_thermal_resistance_K_per_W_1TE_2TE_3TE':2.,
   'recommended_heatsink_to_environment_thermal_resistance_K_per_W_4TE':1.,
   'mounting_instruction':'Detector header BASE firmly attached to sink using thin heat-conductive epoxy or silicone thermal grease; cap/screw-only insufficient',
   'heat_concentration_at_header_base':'nearly all TEC heat leaves header base (OEM qualitative guidance)',
   'source_is_general_guidance_not_specific_product_mount_measurement':True,
   'external_manufacturer_PDF_bytes_in_repository':False
  },
  'thermal_path_topology':['cold detector/TEC ceramic source','Al2O3 ceramic0 bulk','Au composite and joint contacts: UNKNOWN',
       'In52Sn48 mount solder bulk','Ni composite and joint contacts: UNKNOWN',
       '3D Kovar header','header/radiator thermal grease or epoxy interface: UNKNOWN',
       'radiator external heat sink to 300K surrounding'],
  'component_R_K_W':{k:v for k,v in line},
  'component_R_sum_K_W_if_these_all_apply':R_known,
  'sum_definition':'illustrative sequential path only; actual 3D solder-pad and ceramic lateral conduction plus contact coupling need independent qualification',
  'unknown_R_contact_K_W':None,
  'unknown_R_composite_effective_K_W':None,
  'unknown_R_3D_ceramic_spreading_K_W':None,
  'unknown_R_header_external_clamp_patch_K_W':None,
  'installed_radiator_R_to_ambient_measured_K_W':None,
  'source_prior_Q_conditional_W':Q,
  'illustrative_deltaT_across_named_component_sum_K':Q*R_known,
  'illustrative_hot_temperature_if_no_unknowns_K':300+Q*R_known,
  'header_3D_rise_K':Q*R_header,
  'solder_1D_rise_K':Q*R_solder,
  'alumina_1D_rise_K':Q*R_ceramic,
  'radiator_typical_recommendation_rise_K':Q*R_radiator,
  'ratio_known_to_previous_entire_effective_sink_5K_W':R_known/5.,
  'do_not_add_components_to_previous_effective_R5_K_W':True,
  'do_not_equate_OEM_recommended_2K_W_with_header_mount_interface':True,
  'do_not_call_illustrative_hot_temperature_a_coupled_prediction':True,
  'no_new_3D_or_reduced_PDE_solutions':True,
  'as_built_qualified':False,
  'source_input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (HOT,HEADER,SOURCE,CAD)},
  'gates':{'P1_original_B':'FAIL/STOP','P2_candidate':'STOP','full_3D_thermal_C_D':'NOT RUN',
       'actual_430_2440_property_release':'STOP','OEM_CAD_identity':'UNKNOWN'}
 }
def main():
 a=argparse.ArgumentParser()
 a.add_argument('--out',type=Path,required=True)
 a.add_argument('--verify-only',action='store_true')
 opts=a.parse_args();o=build()
 if opts.verify_only:assert j(opts.out)==o
 else:
  assert not opts.out.exists()
  opts.out.parent.mkdir(parents=True,exist_ok=True)
  opts.out.write_text(json.dumps(o,indent=2)+'\n')
 print('OEM_THERMAL_SINK_BOUNDARY',json.dumps({
  'R_named_components_K_W':o['component_R_K_W'],
  'sum_K_W':o['component_R_sum_K_W_if_these_all_apply'],
  'prior_Q_W':o['source_prior_Q_conditional_W'],
  'illustrative_total_rise_K':o['illustrative_deltaT_across_named_component_sum_K'],
  'unknown_interface_R':o['unknown_R_contact_K_W'],
  'next_gate':o['status']
 },indent=2))
if __name__=='__main__':main()
