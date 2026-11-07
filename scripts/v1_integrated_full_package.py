#!/usr/bin/env python3
"""V1 first working integrated conditional R3 29/11/4 TEC/detector system.

One existing nonlinear five-node+32-slice stage solver, real source-CAD leg
geometry, source-curved Cu and Au wires, source die attach, source solder and
ceramic 1D terms, archived source-TET4 3D Kovar+TIM effective thermal
resistance, plus independently OEM-recommended 2 K/W radiator.

One fixed operating case, source-hashed, no new PDE, no sweeping, no
as-built inference. The header/ceramic/solder remain a scalar approximate
series path, not a jointly spatially coupled 3D solution. Electrical solder
and contact Joule transport are NOT included in the stage solver; do not
claim all 430 material laws or full electrical 3D current precision.
"""
from pathlib import Path
from dataclasses import asdict
import argparse, hashlib, json, math, time
from tecooledmct.integrated_reference import Scenario, solve, OperatingPointFailure
from scripts.v3_r3_sink_wire_sensitivity import geometry as original_geometry

ROOT=Path(__file__).resolve().parents[1]
FILES=[
 'data/v3_r32_global_surface_20261103/source_metadata.json',
 'data/synthetic_v3_assembly_20261102/source_final/design.json',
 'data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json',
 'data/v3_hot_mount_readiness_20261107/attempt01/thermal_path_audit.json',
 'data/v3_header_tim_robin_20261107/attempt01/result.json',
 'data/v3_oem_sink_boundary_20261107/attempt01/boundary_evidence.json',
 'data/v3_r3_sink_wire_20261107/attempt01/summary.json',
 'data/v3_reference_29114_reduced_20261107/attempt01/summary.json',
 'tecooledmct/integrated_reference.py',
 'tecooledmct/nonlinear_tec.py',
 'tecooledmct/graded_tec.py',
 'tecooledmct/materials.py',
 'scripts/v3_reference_29114_reduced_study.py',
 'scripts/v3_r3_sink_wire_sensitivity.py',
]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def thermal_path():
 hot=read(ROOT/FILES[3])
 header=read(ROOT/FILES[4])
 oem=read(ROOT/FILES[5])
 assert header['source_header_volume_ID']==386
 assert header['source_header_top_face_tag']==2228
 assert header['source_header_bottom_face_tag']==2225
 assert header['source_header_tetrahedra']==47702
 assert header['source_sink_relative_power_error']<1e-8
 assert header['discrete_energy_relative_error']<1e-8
 assert oem['OEM']['recommended_heatsink_to_environment_thermal_resistance_K_per_W_1TE_2TE_3TE']==2.
 assert oem['unknown_R_contact_K_W'] is None
 assert hot['hot_stack_R3_CAD_face_tags']==[2228,2298,2303,6]
 assert header['radiator_lumped_R_to_ambient_K_W']==2.
 components=[
  ('radiator_to_ambient_OEM_design_reference',header['radiator_lumped_R_to_ambient_K_W']),
  ('native_R3_3D_header_plus_reference_TIM',header['header_plus_local_TIM_effective_R_K_W']),
  ('source_In52Sn48_mount_solder_1D_hypothesis',hot['solder_1D_R_hypothesis_K_W']),
  ('source_ceramic0_Al2O3_AD995_1D_analog',hot['ceramic_1D_R_AD995_analog_K_W']),
 ]
 assert len(components)==4 and all(0<v<5 for _,v in components)
 summed=sum(v for _,v in components)
 assert abs(summed-(header['radiator_plus_header_plus_TIM_effective_R_K_W']+
  hot['two_bulk_layer_1D_sum_AD995_K_W']))<1e-12
 return components, summed

def expected_registration():
 components,total=thermal_path()
 return {
  'version':'V1 coarse integrated full package source-CAD 29/11/4, one operating condition',
  'parent_git_commit':'9f294830b072203e40b2475cf1845ec66c83e31c',
  'source_29_11_4':True,
  'model':'existing nonlinear source-geometry 32-slice TE stages + 5-node TEC/die equations + CAD Cu/Au wires + thermal-series-derived hot boundary; NO 3D full device PDE',
  'operating_point':{'current_A':.4,'ambient_and_pin_reservoir_K':300.,
    'P_N_material':'Zhang P-HE/N-HE-1 unmatched research analog nominal scales',
    'detector_dissipation_W':.002,'optical_load_W':0.,
    'die_attach_k_W_mK':1.,
    'cavity_gas_pressure_Pa':0.,'cavity_radiation':'OFF',
    'wire_model':'source CAD Cu & Au geometry, constant 293K bulk coefficients'},
  'thermal_path_components_K_W':dict(components),
  'thermal_path_total_K_W':total,
  'unmodeled_or_unverified':['grade-matched actual TEC P/N','SnSb electrical series/contact losses',
    'contact Peltier/junction Joule','full 3D ceramic and solder spreading',
    'metal multilayer effective thermal tensors','real header TIM bondline/coverage/pressure',
    'as-built radiator heat flow and T','gas transport and enclosure radiation',
    'full 430-solid coupled spatial electric/thermal fields'],
  'actual_sink_or_device_measurements':'NONE',
  'source_transport_temperature_domain_K':[40.,300.],
  'above_300K_existing_research_continuation':'FLAG REQUIRED, not source measured',
  'numerical_gate':'one source-I point, stage residual <1e-9W, node & global energy <1e-8W, P=IV and positive signed bath heat',
  'preservation':{'historical_P1_B':'FAIL/STOP','P2_prospective':'STOP',
    'new_source_3D_pair_raw_contact':'FAIL 8/8','full_430_C_D':'NOT RUN'},
  'source_inputs_sha256':{f:sha(ROOT/f) for f in FILES},
  'script_sha256':sha(Path(__file__)),
  'one_condition_no_sweep':True
 }

def compute(reg):
 assert reg==expected_registration()
 path,total=thermal_path()
 g=original_geometry()
 assert [s['couples'] for s in g['stages']]==[29,11,4]
 assert {w['pin'] for w in g['wires']}=={1,9,7,8}
 a=Scenario(ambient_k=300.,current_a=.4,material_model='zhang2025_nonlinear',
  heat_sink_k_w=total,detector_bias_w=.002,detector_absorbed_w=0.,
  cavity_pressure_pa=0.,cap_emissivity=0.,window_thermal_emissivity=0.,
  ceramic_emissivity=0.,pn_seebeck_scale=1.,
  pn_resistivity_scale=1.,pn_thermal_conductivity_scale=1.,
  die_attach_conductivity_w_mk=1.)
 start=time.monotonic()
 r=solve(a,g,transport_intervals=32)
 t=r['temperatures_k']
 stages=r['stage_budget']
 Q=r['bath_rejected_power_w']
 assert 0<Q<2
 assert r['max_node_balance_residual_w']<1e-8
 assert abs(r['global_energy_residual_w'])<1e-8
 assert all(abs(s['energy_residual_w'])<1e-9 for s in stages)
 assert abs(r['terminal_electrical_power_w']-.4*r['terminal_voltage_v'])<1e-12
 assert abs(t['hot_ceramic']-300-Q*total)<1e-8
 # The genuine physical meaning of 300K < local hot leg T:
 # research curves are continued by existing hypothetical rule.
 lo=min(s['leg_temperature_extrema_k'][0] for s in stages)
 hi=max(s['leg_temperature_extrema_k'][1] for s in stages)
 assert 180<=lo<=hi<390
 assumed_continuation=any(s['high_T_assumption_applied'] for s in stages)
 assert assumed_continuation == (hi>300)
 # A passive series resistor network has equal magnitude Q through
 # each part. It is NOT a 3D multibody temperature reconstruction.
 nodes={'ambient':300.}
 running=300.
 temperature_drop={}
 for label,R in path:
  delta=Q*R
  temperature_drop[label]=delta
  running+=delta
  nodes['after_'+label]=running
 assert abs(running-t['hot_ceramic'])<1e-8
 # Existing correctly signed loss paths include pin Joule partition,
 # Au wire infeed, die attach, stage thermo electric flux and sink.
 paths=r['heat_paths_w']
 wire_au=paths['Au_wires_into_die_w']
 q_cold=stages[2]['qc_w']
 assert abs(q_cold-(.002+wire_au+sum(paths['gas_w'])+
   sum(paths['radiation_w'])))<1e-8
 # Verifiable, conservative previous V0 comparison at same operating
 # point (same research law, same CAD, wires, detector, zero gas/rad),
 # changing ONLY effective hot thermal path R=5 to CAD-backed 5.281.
 archive=read(ROOT/FILES[6])
 baseline=next(c for c in archive['cases'] if c['hypothesis']=='nominal' and
  c['current_A']==.4 and c['sink_K_W']==5. and
  c['wires_mode']=='CAD-derived bulk-proxy ON')
 assert baseline['status'].startswith('ACCEPTED')
 assert abs(baseline['temperatures_K']['MCT_die']-208.98531200217116)<1e-10
 delta_die=t['MCT_die']-baseline['temperatures_K']['MCT_die']
 out={
  'status':'V1 COARSE SOURCE-CAD FULL PACKAGE CONDITIONAL END-TO-END RUN NUMERICALLY PASS',
  'development_scope':'Integrated reduced electrothermal circuit, 29/11/4 actual stage geometry; full spatial 430-domain PDE NOT RUN',
  'one_current_A':.4,
  'all_source_stage_couples':[29,11,4],
  'P_N_specimens':'Zhang2025 P-HE/N-HE-1 unmatched, conditional',
  'thermal_path_components_K_W':dict(path),
  'thermal_path_total_effective_K_W':total,
  'external_reference_temperature_K':300.,
  'hot_path_temperatures_K':nodes,
  'hot_path_temperature_drops_K':temperature_drop,
  'predicted_all_five_thermal_nodes_K':t,
  'terminal_voltage_V':r['terminal_voltage_v'],
  'module_voltage_V':r['module_voltage_v'],
  'terminal_electrical_input_W':r['terminal_electrical_power_w'],
  'module_electrical_input_W':r['module_electrical_power_w'],
  'total_bath_heat_rejected_W':Q,
  'stage_heat_current_and_power_budgets':stages,
  'detector_load_W':.002,
  'detector_Au_wire_parasitic_W':wire_au,
  'detector_die_attach_heat_to_cold_stage_W':paths['die_attach_into_cold_w'],
  'Cu_hot_side_lead_conduction_W':paths['Cu_conduction_into_hot_w'],
  'Cu_lead_Joule_W':paths['Cu_total_joule_w'],
  'global_energy_balance_residual_W':r['global_energy_residual_w'],
  'max_node_energy_residual_W':r['max_node_balance_residual_w'],
  'max_stage_energy_residual_W':max(abs(st['energy_residual_w']) for st in stages),
  'P_IV_consistency_W':r['terminal_electrical_power_w']-.4*r['terminal_voltage_v'],
  'hot_series_temperature_closure_K':running-t['hot_ceramic'],
  'leg_local_temperature_min_max_K':[lo,hi],
  'assumed_transport_extension_above_300K':assumed_continuation,
  'source_transport_measured_interval_K':[40,300],
  'relative_to_V0_5K_W_wire_ON_identical_other_inputs':{
    'V0_die_temperature_K':baseline['temperatures_K']['MCT_die'],
    'V1_die_temperature_K':t['MCT_die'],
    'delta_die_temperature_K':delta_die,
    'V0_terminal_voltage_V':baseline['terminal_V'],
    'delta_terminal_voltage_V':r['terminal_voltage_v']-baseline['terminal_V'],
    'V0_bath_heat_W':baseline['rejected_at_sink_W'],
    'delta_bath_heat_W':Q-baseline['rejected_at_sink_W']},
  'physics_exclusions_from_registration':reg['unmodeled_or_unverified'],
  'source_data_and_code_sha256':reg['source_inputs_sha256'],
  'registered_script_sha256':reg['script_sha256'],
  'original_P1_B':'FAIL/STOP','original_prospective_P2':'STOP',
  'source_3D_pair_raw_contact':'FAIL 8/8','real_430_domain_C_D':'NOT RUN',
  'actual_OEM_detector_temperature_qualified':False,
  'one_solve_elapsed_s':time.monotonic()-start
 }
 return out
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--registration',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 a=p.parse_args()
 r=read(a.registration)
 out=compute(r)
 if a.verify_only:
  saved=read(a.output)
  for k,v in out.items():
   if k=='one_solve_elapsed_s':continue
   if isinstance(v,float):assert abs(v-saved[k])<=max(1e-8*abs(v),1e-10),(k,v,saved[k])
   else:assert v==saved[k],k
 else:
  assert not a.output.exists()
  with a.output.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print('V1_INTEGRATED_COMPLETE',json.dumps({
  k:out[k] for k in ('status','one_current_A',
 'thermal_path_total_effective_K_W','predicted_all_five_thermal_nodes_K',
 'terminal_voltage_V','terminal_electrical_input_W','total_bath_heat_rejected_W',
 'global_energy_balance_residual_W','max_node_energy_residual_W',
 'assumed_transport_extension_above_300K','one_solve_elapsed_s')},indent=2))
if __name__=='__main__':main()
