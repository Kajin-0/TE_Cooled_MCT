#!/usr/bin/env python3
"""Read-only source SHA and numerical conservation verification of V3.2 fast screen.

Audits completed V1 reduced conditional whole-device cases, separately
records STOPPED high-fidelity V3.2 sensitivity attempt with ZERO results.
No simulation solves or parameter tuning.
"""
from pathlib import Path
import argparse,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
ARCH=ROOT/'data/v3_2_bounded_sensitivity_20261107/attempt01'
MAPPING={
 'V1_baseline':'data/v1_integrated_full_package_20261107/attempt01/result.json',
 'V3_2_working_reference':'data/v3_2_joint_loss_feedback_20261107/attempt01/result.json',
 'original_source_geometry':'data/synthetic_v3_assembly_20261102/source_final/design.json',
 'original_nonlin_TE_solver':'tecooledmct/nonlinear_tec.py',
 'whole_device_reduced_solver':'tecooledmct/integrated_reference.py',
 'source_cad_wires':'scripts/v3_r3_sink_wire_sensitivity.py',
 'source_material':'tecooledmct/graded_tec.py',
 'source_SnSb_electrical_contact_bounds':'data/v3_tec_contact_scale_20261107/attempt01/conditional_contact_scale.json',
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def audit():
 reg=read(ARCH/'fast_registration.json')
 results=read(ARCH/'fast_results.json')
 stopped=read(ARCH/'stopped_timebox.json')
 base=read(ROOT/MAPPING['V1_baseline'])
 v32=read(ROOT/MAPPING['V3_2_working_reference'])
 assert stopped['accepted_cases']==0
 assert stopped['status']=='STOPPED_BY_ANTI_CHURN_TIMEBOX'
 assert len(reg['same_current_case_screens'])==8
 assert len(results['cases'])==8
 assert set(MAPPING)==set(reg['source_hashes'])
 for label,p in MAPPING.items():assert sha(ROOT/p)==reg['source_hashes'][label],label
 assert sha(ROOT/'scripts/v3_2_fast_system_sensitivity.py')==reg['script_sha256']
 assert results['original_P1_B']=='FAIL/STOP'
 assert results['full_430_domain_C_D']=='NOT RUN'
 assert results['original_P1_first_pair_raw']=='FAIL 8/8'
 assert results['not_measured_or_as_built_qualified']
 assert results['source_29_11_4']
 assert results['total_wall_seconds']<reg['all_cases_budget_seconds']
 assert abs(results['baseline_V1_Tdie_K']-base['predicted_all_five_thermal_nodes_K']['MCT_die'])<1e-8
 assert abs(results['V3_2_spatial_current_model_Tdie_K']-v32['calculated_detector_temperature_K'])<1e-8
 cases=results['cases']
 assert [c['id'] for c in cases]==[c['id'] for c in reg['same_current_case_screens']]
 assert all(c['status']=='CONDITIONAL_REDUCED_FULL_DEVICE_NUMERICAL_PASS' for c in cases)
 for c in cases:
  assert abs(c['global_energy_residual_W'])<1e-8
  assert c['max_node_residual_W']<1e-8
  assert abs(c['terminal_voltage_V']*.4-c['electrical_power_W'])<1e-12
  assert c['source_original_P1_B']=='FAIL/STOP'
  assert c['full_original_430_C_D']=='NOT RUN'
 ref=cases[0]
 for c in cases[1:]:
  assert abs(c['delta_Tdie_K']-(c['Tdie_K']-ref['Tdie_K']))<1e-12
  assert abs(c['delta_V_V']-(c['terminal_voltage_V']-ref['terminal_voltage_V']))<1e-12
  assert abs(c['delta_P_W']-(c['electrical_power_W']-ref['electrical_power_W']))<1e-12
 ranked=sorted((c for c in cases[1:] if not c['id'].startswith('combined')),
   key=lambda c:abs(c['delta_Tdie_K']),reverse=True)
 assert [r['id'] for r in ranked]==[x['id'] for x in results['OAT_rank_for_registered_step_sizes']]
 assert ranked[0]['id']=='k_plus20pct'
 return {
 'status':'READ ONLY VERIFIED: 8 reduced whole-device V1 source physics screening cases, no spatial V3.2 sensitivity completed; earlier expensive V3.2 campaign visibly STOPPED',
 'complete_reduced_source_cases':8,
 'fully_spatial_V3_2_sensitivity_case_results':0,
 'reduced_baseline_die_T_K':ref['Tdie_K'],
 'V3_2_canonical_spatial_baseline_die_T_K':v32['calculated_detector_temperature_K'],
 'ranked_5_OAT_step_sizes':[
  {'id':c['id'],'delta_die_K':c['delta_Tdie_K'],
   'delta_terminal_V':c['delta_V_V'],'delta_input_power_W':c['delta_P_W']}
  for c in ranked],
 'coherent_lower_transport_delta_Tdie_K':next(c['delta_Tdie_K'] for c in cases if c['id']=='combined_lower_material'),
 'coherent_higher_transport_delta_Tdie_K':next(c['delta_Tdie_K'] for c in cases if c['id']=='combined_higher_material'),
 'screening_vs_current_spatial_model':'DIFFERENT fidelity, screen is not V3.2 sensitivity; do not add independent temperature deltas as error bars',
 'original_P1_B':'FAIL/STOP',
 'first_original_P1_contact_raw':'FAIL 8/8',
 'full_430_C_D':'NOT RUN',
 'source_registration_SHA256':sha(ARCH/'fast_registration.json'),
 'screen_output_SHA256':sha(ARCH/'fast_results.json'),
 'terminated_full_run_receipt_SHA256':sha(ARCH/'stopped_timebox.json'),
 'source_3D_or_reduced_PDE_solutions_computed_by_this_audit':0
 }
def main():
 a=argparse.ArgumentParser()
 a.add_argument('--output',type=Path,required=True)
 a.add_argument('--verify-only',action='store_true')
 o=a.parse_args()
 j=audit()
 if o.verify_only:assert read(o.output)==j
 else:
  assert not o.output.exists()
  o.output.write_text(json.dumps(j,indent=2)+'\n')
 print('FAST_REDUCED_SYSTEM_OAT_INDEPENDENT_ACCEPTANCE',
  j['complete_reduced_source_cases'],'accepted,',
  j['fully_spatial_V3_2_sensitivity_case_results'],'spatial sensitivity cases')
if __name__=='__main__':main()
