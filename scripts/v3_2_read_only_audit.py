#!/usr/bin/env python3
"""Read-only source-CAD V3.2 saved-result reconstruction, no PDE solve.

Rechecks exact 176 SnSb bulk + 352 contact series losses, independently
sums 88 individual TE legs, stage interface heat balances and every
actual source ceramic face load. Explicitly reports finite outer-loop
pad source mismatch; never silently interprets it as exact agreement.
"""
from collections import defaultdict
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
F=ROOT/'data/v3_2_joint_loss_feedback_20261107/attempt01'
BASE=ROOT/'data/v3_1_native_pad_feedback_20261107/attempt02/result.json'
CONTACT=ROOT/'data/v3_tec_contact_scale_20261107/attempt01/conditional_contact_scale.json'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit():
 a=read(F/'registration.json');r=read(F/'result.json')
 base=read(BASE);contact=read(CONTACT)
 I=r['operating_current_A']
 assert I==.4 and I==base['operating_current_A']
 assert len(r['source_individual_leg_flux_and_electric_results'])==88
 assert len(r['original_native_source_ceramic_pad_flux_by_face'])==4
 assert r['original_ceramic_TET4']==11791
 assert r['source_joint_count']==contact['source_SnSb_joint_solids']==176
 assert r['original_source_SnSb_contact_count']==contact['source_SnSb_native_contact_faces']==352
 assert a['script_SHA256']==sha(ROOT/'scripts/v3_2_joint_loss_feedback.py')
 assert r['source_input_sha256']==a['source_SHA256']
 assert r['source_mesh_sha256']==a['original_mesh_SHA256']
 assert r['source_original_B']=='FAIL/STOP' and r['full_original_430_domain_C_D']=='NOT RUN'
 assert r['source_first_pair_raw_gradient']=='FAIL 8/8'
 assert not r['source_CAD_and_original_mesh_modified']
 assert r['max_last_spatial_temperature_update_K']<a['outer_thermal_field_tolerance_K']
 assert r['max_full_stage_conservation_residual_W']<a['inner_balance_tolerance_W']
 assert r['max_native_plate_net_heat_imbalance_W']<a['local_plate_net_heat_tolerance_W']
 assert r['max_separate_leg_energy_residual_W']<a['individual_leg_energy_tolerance_W']
 assert abs(r['global_thermoelectric_energy_residual_W'])<a['global_energy_tolerance_W']
 assert r['max_mean_plate_temperature_residual_K']<a['outer_thermal_field_tolerance_K']
 assert r['outer_iterations']<=a['outer_steps_cap']
 bulk_R=contact['all_176_SnSb_bulk_electrical_R_ohm']
 interface_R=352*a['unmeasured_hypothetical_contact_rho_e_ohm_m2']/(contact['source_nominal_contact_area_per_face_mm2']*1e-6)
 total_R=bulk_R+interface_R
 total_P=I*I*total_R
 assert abs(total_R-r['source_total_solder_and_contact_series_resistance_ohm'])<1e-14
 assert abs(total_P-r['source_joint_additional_electrical_Joule_W'])<1e-14
 assert abs(I*total_R-r['source_joint_additional_terminal_V'])<1e-14
 assert abs(sum(r['source_4_ceramic_distributed_joint_heating_W'])-total_P)<1e-14
 assert abs(I*r['terminal_voltage_V']-r['electrical_power_W'])<1e-12
 stage=r['source_stage_thermoelectric_budget']
 legs=r['source_individual_leg_flux_and_electric_results']
 for i in range(3):
  group=[z for z in legs if z['stage']==i]
  assert len(group)==(58,22,8)[i]
  assert abs(sum(z['Qhot_W'] for z in group)-stage[i]['qh_w'])<1e-12
  assert abs(sum(z['Qcold_W'] for z in group)-stage[i]['qc_w'])<1e-12
  assert abs(sum(z['terminal_contribution_V'] for z in group)-stage[i]['voltage_v'])<1e-12
  assert max(abs(z['energy_residual_W']) for z in group)<a['individual_leg_energy_tolerance_W']
 joint=r['source_solder_and_interface_energy_per_single_joint_pad_W']
 plates=r['original_native_source_ceramic_pad_flux_by_face']
 Qa=plates[3]['heat_per_source_face_W']['119']
 qbath=r['bath_heat_rejected_W']
 assert abs(stage[0]['qc_w']-stage[1]['qh_w']-80*joint)<a['inner_balance_tolerance_W']
 assert abs(stage[1]['qc_w']-stage[2]['qh_w']-30*joint)<a['inner_balance_tolerance_W']
 assert abs(stage[2]['qc_w']-Qa-8*joint)<a['inner_balance_tolerance_W']
 assert abs(plates[0]['heat_per_source_face_W']['6']+qbath)<a['local_plate_net_heat_tolerance_W']
 discrepancies=[]
 # Last saved ceramic field and new last nonlinear leg update differ
 # by a finite amount. Record it, require original registered budget,
 # never silently call source fields exact.
 for i,plate in enumerate(plates):
  saved={int(k):v for k,v in plate['heat_per_source_face_W'].items()}
  expected=defaultdict(float)
  for l in legs:
   if l['stage']==i:expected[l['hot_tag']]+=l['Qhot_W']+joint
   if l['stage']+1==i:expected[l['cold_tag']]+=-l['Qcold_W']+joint
  if i==0:
   expected[36]+=r['heat_Cu_lead_correction_W']
   expected[6]-=qbath
  if i==3:expected[119]+=Qa
  assert all(tag in saved for tag in expected)
  delta=max(abs(saved.get(k,0.)-v) for k,v in expected.items())
  assert delta<2e-9,(i,delta)
  assert abs(sum(saved.values()))<a['local_plate_net_heat_tolerance_W']
  assert plate['free_thermal_residual_W']<2e-8
  discrepancies.append(dict(ceramic=i,original_TET4=plate['original_tets'],
   original_source_pad_tag_count=len(saved),
   largest_final_face_heat_saved_vs_final_updated_leg_difference_W=delta,
   source_face_net_heat_W=sum(saved.values()),
   source_free_node_thermal_residual_W=plate['free_thermal_residual_W']))
 comparison=r['V3_1_same_current_comparison']
 assert abs(comparison['V3_2_minus_V3_1_die_K']-(r['calculated_detector_temperature_K']-base['calculated_detector_temperature_K']))<1e-12
 assert abs(comparison['V3_2_minus_V3_1_electrical_power_W']-(r['electrical_power_W']-base['electrical_power_W']))<1e-12
 return {
  'status':'PASS independent original source 176 SnSb +352 interface electrical R, 88-leg series and stage junction heat, four native source ceramic pad energy budgets; finite final field-update discrepancies exposed',
  'one_condition_current_A':I,
  'source_original_176_SnSb_bulk_series_R_ohm':bulk_R,
  'source_original_352_interface_series_R_ohm':interface_R,
  'sum_series_R_ohm':total_R,
  'source_total_Joule_W':total_P,
  'V3_1_same_current_Tdie_K':base['calculated_detector_temperature_K'],
  'V3_2_Tdie_K':r['calculated_detector_temperature_K'],
  'delta_Tdie_K':comparison['V3_2_minus_V3_1_die_K'],
  'source_stage0_1_interstage_heat_balance_W':stage[0]['qc_w']-stage[1]['qh_w']-80*joint,
  'source_stage1_2_interstage_heat_balance_W':stage[1]['qc_w']-stage[2]['qh_w']-30*joint,
  'source_stage2_cold_detector_energy_balance_W':stage[2]['qc_w']-Qa-8*joint,
  'separate_original_four_ceramic_pad_flux_closure':discrepancies,
  'max_saved_final_face_heat_mismatch_W':max(d['largest_final_face_heat_saved_vs_final_updated_leg_difference_W'] for d in discrepancies),
  'original_V3_1_P1_gate':'FAIL/STOP, no reclassification',
  'full_430_domain_spatial_coupled_PDE':'NOT RUN',
  'contact_thermal_R_interfacial_Peltier_and_metal_bulk_R':'NOT INCLUDED',
  'new_PDE_solves':0,
  'saved_V3_2_result_SHA256':sha(F/'result.json'),
  'registered_V3_2_input_SHA256':sha(F/'registration.json'),
  'source_contact_scale_SHA256':sha(CONTACT),
  'V3_1_baseline_result_SHA256':sha(BASE)}
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 a=p.parse_args();x=audit()
 if a.verify_only:assert x==read(a.output)
 else:
  assert not a.output.exists()
  a.output.write_text(json.dumps(x,indent=2)+'\n')
 print('V3_2_READ_ONLY_ACCEPTANCE',json.dumps({
  k:x[k] for k in ('status','sum_series_R_ohm','source_total_Joule_W','delta_Tdie_K','max_saved_final_face_heat_mismatch_W')},indent=2))
if __name__=='__main__':main()
