#!/usr/bin/env python3
"""Fast preliminary ONE-AT-A-TIME 29/11/4 complete-device sensitivity screen.

Uses the validated V1 reduced nonlinear whole-device solver at 0.40 A,
original Cu/Au wires, die attachment, CAD geometry and complete hot-side
thermal path. This is a deliberate FAST SCREEN and does NOT re-solve the
V3.2 spatial ceramic / detailed solder contact model. Rankings are
conditional reduced-model responses, NOT statistical uncertainty or
validated absolute physical predictions. V3.2 remains canonical.
"""
from pathlib import Path
import argparse,json,hashlib,time
from tecooledmct.integrated_reference import Scenario,solve
from scripts.v3_r3_sink_wire_sensitivity import geometry
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/v1_integrated_full_package_20261107/attempt01/result.json'
V32=ROOT/'data/v3_2_joint_loss_feedback_20261107/attempt01/result.json'
JOINTS=ROOT/'data/v3_tec_contact_scale_20261107/attempt01/conditional_contact_scale.json'
SRC={
 'V1_baseline':BASE,'V3_2_working_reference':V32,
 'original_source_geometry':'data/synthetic_v3_assembly_20261102/source_final/design.json',
 'original_nonlin_TE_solver':'tecooledmct/nonlinear_tec.py',
 'whole_device_reduced_solver':'tecooledmct/integrated_reference.py',
 'source_cad_wires':'scripts/v3_r3_sink_wire_sensitivity.py',
 'source_material':'tecooledmct/graded_tec.py',
 'source_SnSb_electrical_contact_bounds':JOINTS,
}
CASES=[
 {'id':'baseline','parameter':'none','scale_S_rho_k':[1.,1.,1.],'R_total_K_W':5.281295229192457,'die_W':.002},
 {'id':'S_plus10pct','parameter':'Seebeck_S','scale_S_rho_k':[1.1,1.,1.],'R_total_K_W':5.281295229192457,'die_W':.002},
 {'id':'rho_plus20pct','parameter':'PN_electrical_resistivity','scale_S_rho_k':[1.,1.2,1.],'R_total_K_W':5.281295229192457,'die_W':.002},
 {'id':'k_plus20pct','parameter':'PN_thermal_conductivity','scale_S_rho_k':[1.,1.,1.2],'R_total_K_W':5.281295229192457,'die_W':.002},
 {'id':'radiator_3_vs_2_K_W','parameter':'radiator_incremental_R','scale_S_rho_k':[1.,1.,1.],'R_total_K_W':6.281295229192457,'die_W':.002},
 {'id':'detector_4_vs_2_mW','parameter':'detector_bias_heat','scale_S_rho_k':[1.,1.,1.],'R_total_K_W':5.281295229192457,'die_W':.004},
 {'id':'combined_lower_material','parameter':'coherent lower transport hypothesis','scale_S_rho_k':[.9,1.2,1.2],'R_total_K_W':5.281295229192457,'die_W':.002},
 {'id':'combined_higher_material','parameter':'coherent higher transport hypothesis','scale_S_rho_k':[1.1,.8,.8],'R_total_K_W':5.281295229192457,'die_W':.002},
]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def registration():
 return {
 'model':'Bounded FAST reduced whole-device V1 original source 29/11/4 nonlinear TEC screen, 0.4A; NOT V3.2 spatial run',
 'parent_commit':'15d574621e421578a0f4c18bdf6f443a9c614da7',
 'operating_point_I_A':.4,'reference_ambient_and_Cu_Au_pins_K':300.,
 'same_current_case_screens':CASES,
 'no_statistical_uncertainty_claim':True,
 'V3_2_source_still_canonical':True,
 'V3_2_lumped_solder_and_contact_losses_NOT_REPRESENTED_in_screen':True,
 'no_original_mesh_or_CAD_mutation':True,
 'source_hashes':{k:sha(ROOT/v) if isinstance(v,str) else sha(v) for k,v in SRC.items()},
 'script_sha256':sha(Path(__file__)),
 'base_original_P1_Gate_B':'FAIL/STOP','full_original_430_domain_C_D':'NOT RUN',
 'case_budget_seconds':14.,'all_cases_budget_seconds':135.,
 }
def compute(case,g):
 s,r,k=case['scale_S_rho_k']
 a=Scenario(ambient_k=300.,current_a=.4,material_model='zhang2025_nonlinear',
  heat_sink_k_w=case['R_total_K_W'],detector_bias_w=case['die_W'],
  detector_absorbed_w=0.,cavity_pressure_pa=0.,cap_emissivity=0.,
  window_thermal_emissivity=0.,ceramic_emissivity=0.,
  pn_seebeck_scale=s,pn_resistivity_scale=r,
  pn_thermal_conductivity_scale=k,die_attach_conductivity_w_mk=1.)
 t0=time.monotonic()
 r=solve(a,g,transport_intervals=32)
 assert r['max_node_balance_residual_w']<1e-8
 assert abs(r['global_energy_residual_w'])<1e-8
 assert all(abs(st['energy_residual_w'])<1e-9 for st in r['stage_budget'])
 assert abs(r['terminal_electrical_power_w']-.4*r['terminal_voltage_v'])<1e-12
 return {'id':case['id'],'parameter':case['parameter'],
   'status':'CONDITIONAL_REDUCED_FULL_DEVICE_NUMERICAL_PASS',
   'Tdie_K':r['temperatures_k']['MCT_die'],
   'hot_ceramic_K':r['temperatures_k']['hot_ceramic'],
   'terminal_voltage_V':r['terminal_voltage_v'],
   'electrical_power_W':r['terminal_electrical_power_w'],
   'bath_rejection_W':r['bath_rejected_power_w'],
   'stage3_Q_c_W':r['stage_budget'][-1]['qc_w'],
   'global_energy_residual_W':r['global_energy_residual_w'],
   'max_node_residual_W':r['max_node_balance_residual_w'],
   'extrapolated_PN_above_300K':any(st['high_T_assumption_applied'] for st in r['stage_budget']),
   'wall_s':time.monotonic()-t0,
   'source_original_P1_B':'FAIL/STOP','full_original_430_C_D':'NOT RUN'}
def main():
 a=argparse.ArgumentParser()
 a.add_argument('--registration',type=Path,required=True)
 a.add_argument('--out',type=Path,required=True)
 args=a.parse_args()
 reg=read(args.registration)
 assert reg==registration()
 assert not args.out.exists()
 base=read(BASE);v32=read(V32);contact=read(JOINTS)
 g=geometry();assert [st['couples'] for st in g['stages']]==[29,11,4]
 t0=time.monotonic();rows=[]
 for case in reg['same_current_case_screens']:
  if time.monotonic()-t0>reg['all_cases_budget_seconds']:
   rows.append({'id':case['id'],'status':'NOT_RUN_TIME_BUDGET'})
   continue
  try:
   result=compute(case,g)
   if case['id']=='baseline':
    assert abs(result['Tdie_K']-base['predicted_all_five_thermal_nodes_K']['MCT_die'])<1e-8
    assert abs(result['terminal_voltage_V']-base['terminal_voltage_V'])<1e-8
   rows.append(result)
   print('FAST_FULL_SYSTEM_CASE',result['id'],round(result['Tdie_K'],7),
      'K',round(result['wall_s'],3),'sec',flush=True)
  except Exception as e:
   rows.append({'id':case['id'],'status':'FAILED_NOT_ACCEPTED',
                 'reason':repr(e)[:600]})
   print('FAST_FULL_SYSTEM_CASE_FAIL',case['id'],repr(e),flush=True)
 assert rows[0]['status']=='CONDITIONAL_REDUCED_FULL_DEVICE_NUMERICAL_PASS'
 ref=rows[0]
 for row in rows[1:]:
  if row['status']=='CONDITIONAL_REDUCED_FULL_DEVICE_NUMERICAL_PASS':
   row['delta_Tdie_K']=row['Tdie_K']-ref['Tdie_K']
   row['delta_V_V']=row['terminal_voltage_V']-ref['terminal_voltage_V']
   row['delta_P_W']=row['electrical_power_W']-ref['electrical_power_W']
   row['delta_bath_W']=row['bath_rejection_W']-ref['bath_rejection_W']
 passed=[r for r in rows[1:] if r['status']=='CONDITIONAL_REDUCED_FULL_DEVICE_NUMERICAL_PASS']
 ranked=sorted([r for r in passed if r['id'] not in ('combined_lower_material','combined_higher_material')],
    key=lambda r:abs(r['delta_Tdie_K']),reverse=True)
 data={'status':'V1 SOURCE CAD REDUCED NONLINEAR WHOLE-DEVICE FAST SENSITIVITY SCREEN, NOT V3.2 SPATIAL SENSITIVITY',
  'baseline_V1_Tdie_K':ref['Tdie_K'],
  'V3_2_spatial_current_model_Tdie_K':v32['calculated_detector_temperature_K'],
  'source_29_11_4':True,'conditions':reg['same_current_case_screens'],
  'cases':rows,
  'OAT_rank_for_registered_step_sizes':[{'id':r['id'],'parameter':r['parameter'],
     'delta_die_K':r['delta_Tdie_K'],
     'delta_terminal_V':r['delta_V_V'],'delta_terminal_power_W':r['delta_P_W']} for r in ranked],
  'source_352_contact_rho_e_ohm_m2_exploratory_bounds':[
    {'label':r['label'],'rho_e_ohm_m2':r['assumed_interface_specific_electrical_resistivity_ohm_m2'],
     'contact_series_R_ohm':r['aggregate_352_interface_series_electrical_R_ohm']}
    for r in contact['hypotheses_only_not_as_built_interface_data']],
  'contact_rho_sensitivity_to_die_temperature':'NOT CALCULATED IN THIS REDUCED SCREEN',
  'actual_V3_1_to_V3_2_solder_contact_added_Joule_delta_Tdie_K':
     v32['V3_1_same_current_comparison']['V3_2_minus_V3_1_die_K'],
  'comparability_warning':'V1 screening deltas and V3.2 new-joint delta use different model fidelity; not interchangeable as total statistical error bars or additive budget',
  'not_measured_or_as_built_qualified':True,
  'total_wall_seconds':time.monotonic()-t0,
  'original_P1_B':'FAIL/STOP','original_P1_first_pair_raw':'FAIL 8/8',
  'full_430_domain_C_D':'NOT RUN'}
 args.out.write_text(json.dumps(data,indent=2)+'\n')
 print('FAST_SOURCE_SYSTEM_SENSITIVITY_COMPLETE',
   'passed',len(passed)+1,'total_sec',data['total_wall_seconds'],flush=True)
if __name__=='__main__':main()
