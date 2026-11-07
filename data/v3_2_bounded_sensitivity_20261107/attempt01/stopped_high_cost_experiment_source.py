#!/usr/bin/env python3
"""Bounded V3.2 whole-system one-at-a-time sensitivity.

Reuse the *unchanged* canonical OriginalPlates source-CAD 3D FEM,
actual source leg graph, original 32-interval nonlinear TE transport,
Cu/Au/die/header paths and native-pad Joule distribution. Factor the
original 4 ceramic matrices ONCE; run fixed declared scenarios only.
No new global mesh, material validation, parameter optimization, or
post-hoc fabricated uncertainty interval.
"""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from tecooledmct.nonlinear_tec import leg
from scripts.v3_2_joint_loss_feedback import (
    ROOT, OriginalPlates, find_leg_contact_source, original_geometry,
    V2, JOINTS, PATHS, sha, read
)

BASE = ROOT/'data/v3_2_joint_loss_feedback_20261107/attempt01/result.json'
BASE_REG = ROOT/'data/v3_2_joint_loss_feedback_20261107/attempt01/registration.json'
BASE_ENGINE = ROOT/'scripts/v3_2_joint_loss_feedback.py'
FILES = {
    'canonical_V3_2_result':BASE,
    'canonical_V3_2_registration':BASE_REG,
    'canonical_V3_2_integrated_solver':BASE_ENGINE,
    'original_nonlin_PN_transport':ROOT/'tecooledmct/nonlinear_tec.py',
    'original_grade_analog_source':ROOT/'tecooledmct/graded_tec.py',
    'original_88_leg_CAD_mapping':ROOT/'scripts/v3_integrated_leg_resolved.py',
    'original_CAD_metadata':ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json',
    'actual_824_body_design':ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json',
    'source_joints_contact_bounds':JOINTS,
    'source_Cu_Au_leads':ROOT/'scripts/v3_r3_sink_wire_sensitivity.py',
    'source_reduced_NP_stage':ROOT/'scripts/v3_reference_29114_reduced_study.py',
    '3D_original_ceramic_source':ROOT/'scripts/v2_source_ceramic_spatial.py',
    'archived_3D_header_TIM':ROOT/'data/v3_header_tim_robin_20261107/attempt01/result.json'
}
CASES = [
 {'id':'S_plus10pct','param':'P_N_Seebeck','factor':1.1},
 {'id':'rho_plus20pct','param':'P_N_resistivity','factor':1.2},
 {'id':'k_plus20pct','param':'P_N_thermal_conductivity','factor':1.2},
 {'id':'contact_times10','param':'electrical_specific_contact_resistivity','factor':10.},
 {'id':'radiator_3_vs_2_K_W','param':'radiator_total_resistance_K_W','nominal':2.,'target':3.},
 {'id':'detector_4_vs_2_mW','param':'detector_bias_heat_W','nominal':.002,'target':.004}
]
def registration():
 return {
  'status':'PREREGISTERED BOUNDED SOURCE V3.2 ONE AT A TIME SENSITIVITY, six scenarios, no source rewrite or new mesh',
  'baseline_git_commit':'15d574621e421578a0f4c18bdf6f443a9c614da7',
  'baseline_temperature_K':read(BASE)['calculated_detector_temperature_K'],
  'baseline_current_A':.4,
  'input_cases':CASES,
  'base_contact_rho_ohm_m2':1e-11,
  'base_radiator_total_R_K_W':2.,
  'base_die_load_W':.002,
  'temperature_material_interval_K':[40,300],
  'above_300_material_transport':'source hypothetical extrapolation, never measured',
  'ceramics_k_W_mK':30.,
  'fixed_original_ceramic_P1_regions':[1,2,3,4],
  'original_ceramic_tetra':11791,
  'original_stage_couples':[29,11,4],
  'one_model_perturbation_per_case':True,
  'iterations_cap':18,
  'same_spatial_convergence_tolerance_K':2e-7,
  'same_nonlinear_heat_residual_W':1e-8,
  'same_individual_leg_energy_tolerance_W':1e-9,
  'same_global_energy_tolerance_W':1e-8,
  'failed_case_policy':'FAIL visibly, do not infer a response or rerun hidden cases',
  'whole_study_wall_budget_seconds':660.,
  'source_file_sha256':{k:sha(v) for k,v in FILES.items()},
  'source_mesh_sha256':{k:sha(v) for k,v in PATHS.items()},
  'script_sha256':sha(Path(__file__)),
  'old_original_P1_B':'FAIL/STOP',
  'original_first_couple_raw_P1':'FAIL 8/8',
  'full_original_430_C_D':'NOT RUN',
  'not_as_built_OEM_prediction':True
 }

class SensitivityRunner:
 def __init__(self):
  self.base=read(BASE);self.legs,_=find_leg_contact_source()
  self.spatial=OriginalPlates(self.legs)
  self.geo=original_geometry()
  assert len(self.legs)==88 and len(self.spatial.plates)==4
  assert [x['couples'] for x in self.geo['stages']]==[29,11,4]
  cu=[x for x in self.geo['wires'] if x['material']=='Cu']
  au=[x for x in self.geo['wires'] if x['material']=='Au']
  assert len(cu)==len(au)==2
  self.Gcu=sum(x['G_W_K'] for x in cu)
  self.Rcu=sum(x['R_ohm'] for x in cu)
  self.Gau=sum(x['G_W_K'] for x in au)
  self.area=self.geo['stages'][0]['leg_area_m2']
  self.length=self.geo['stages'][0]['leg_length_m']
  self.dieR=self.geo['die_attach_thickness_over_area_m_inverse']
  self.Rext=read(V2)['hot_external_R_without_ceramic0_K_W']
  self.I=.4
  joints=read(JOINTS)
  assert joints['source_SnSb_joint_solids']==176
  assert joints['source_SnSb_native_contact_faces']==352
  self.Rbulk=(
    joints['source_old_GateB_hypothetical_SnSb_bulk_electrical_rho_ohm_m']
    *joints['source_joint_thickness_mm']*1e-3
    /(joints['source_nominal_contact_area_per_face_mm2']*1e-6))
  self.Rcontact=(1e-11/(joints['source_nominal_contact_area_per_face_mm2']*1e-6))
  self.stage_joints=(58,22,8)
  n=self.base['source_full_temperature_nodes_K']
  self.initT=np.array([n[k] for k in (
   'stage0_hot','stage0_cold','stage1_hot','stage1_cold',
   'stage2_hot','stage2_cold','carrier','die')])
  self.baseline_rows=self.base['source_individual_leg_flux_and_electric_results']
  self.baseline_st=self.base['source_stage_thermoelectric_budget']
  self.baseline_Qbath=self.base['bath_heat_rejected_W']
  self.baseline_Qa=self.base['original_native_source_ceramic_pad_flux_by_face'][3]['heat_per_source_face_W']['119']
  assert self.baseline_Qa>0 and self.dieR>0

 def run(self,c):
  tic=time.monotonic()
  scales=[1.,1.,1.]
  contactmult=1.; radiator=2.; load=.002
  param=c['param']
  if param=='P_N_Seebeck':scales[0]=c['factor']
  elif param=='P_N_resistivity':scales[1]=c['factor']
  elif param=='P_N_thermal_conductivity':scales[2]=c['factor']
  elif param=='electrical_specific_contact_resistivity':contactmult=c['factor']
  elif param=='radiator_total_resistance_K_W':radiator=c['target']
  elif param=='detector_bias_heat_W':load=c['target']
  else:raise ValueError('Unexpected preregistered parameter')
  I=self.I
  Rj=self.Rbulk+2*self.Rcontact*contactmult
  Pj=I*I*Rj
  Rtotal=176*Rj
  # Loss correction is the ONLY electrical-contact change in the case.
  Qsource=176*Pj
  Rext=self.Rext+(radiator-2.)
  assert Rext>0
  baseline=self.base
  legs=self.legs
  qcu=self.Gcu*(300-self.initT[0]);CuJoule=I*I*self.Rcu
  # Seed with the previous converged V3.2 spatial heat distribution:
  # electrical-contact variant replaces only old Pj; other cases
  # reuse it until their first new full-model iteration.
  old_pj=baseline['source_solder_and_interface_energy_per_single_joint_pad_W']
  def with_joint(rows,old=0.):
   return [{
     'stage':z['stage'],'hot_tag':z['hot_tag'],'cold_tag':z['cold_tag'],
     'Qhot_W':z['Qhot_W']+Pj-old,
     'Qcold_W':z['Qcold_W']-Pj+old
    } for z in rows]
  init=with_joint(self.baseline_rows,old=0.)
  qbath=self.baseline_Qbath+(58*(Pj-old_pj))
  Qa=self.baseline_Qa
  # For non-baseline joint cases, seed heat at net bath sink by updated
  # hot solder Joule. Original source 3D operator is solved using same
  # registered physical Neumann face mapping as canonical V3.2.
  fields,offset=self.spatial.solve(init,self.baseline_st,CuJoule,qcu,qbath,Qa)
  x=self.initT.copy()
  logs=[]
  last=None
  def with_solder_heat(rows):
   return [{**z,'Qhot_W':z['Qhot_W']+Pj,
             'Qcold_W':z['Qcold_W']-Pj} for z in rows]
  for iteration in range(1,19):
   gaps=np.array([f['top_minus_bottom_K'] for f in fields])
   x[0]=300+Rext*qbath+gaps[0]
   def model(y):
    stage=[dict(qh_w=0.,qc_w=0.,voltage_v=0.,joule_w=0.,
                 energy_residual_w=0.,nlegs=0) for _ in range(3)]
    rows=[]
    for z in legs:
     s=z['stage']
     th=y[2*s]+offset[z['hot']['original_pad_face_tag']]
     tc=y[2*s+1]+offset[z['cold']['original_pad_face_tag']]
     pol=z['material']
     v=leg(pol,th,tc,I/self.area*(1 if pol=='N' else -1),
       self.length,intervals=32,scales=tuple(scales))
     qh=-self.area*v['q_hot_w_m2'];qc=-self.area*v['q_cold_w_m2']
     elecv=v['electric_integral_v']*(1 if pol=='N' else -1)
     stage[s]['qh_w']+=qh;stage[s]['qc_w']+=qc
     stage[s]['voltage_v']+=elecv
     stage[s]['joule_w']+=self.area*v['joule_w_m2']
     stage[s]['energy_residual_w']+=qh-qc-I*elecv
     stage[s]['nlegs']+=1
     rows.append({'stage':s,
      'hot_tag':z['hot']['original_pad_face_tag'],
      'cold_tag':z['cold']['original_pad_face_tag'],
      'Qhot_W':qh,'Qcold_W':qc,
      'source_name':z['leg_name'],
      'source_region_ID':z['original_region_ID'],
      'voltage_V':elecv,'energy_W':qh-qc-I*elecv})
    qa=(y[7]-y[6])/self.dieR
    detector=load+self.Gau*(300-y[7])
    qcu=self.Gcu*(300-y[0])
    cujoule=I*I*self.Rcu
    bath=stage[0]['qh_w']+qcu+.5*cujoule+58*Pj
    return stage,rows,qa,detector,qcu,cujoule,bath
   def residual(y):
    st,rows,qa,detector,qcu,cujoule,bath=model(y)
    return np.array([
     st[0]['qc_w']-st[1]['qh_w']-80*Pj,
     st[1]['qc_w']-st[2]['qh_w']-30*Pj,
     st[2]['qc_w']-qa-8*Pj,
     qa-detector,
     y[2]-y[1]-gaps[1],
     y[4]-y[3]-gaps[2],
     y[6]-y[5]-gaps[3],
     y[0]-300-Rext*bath-gaps[0]])
   weights=np.array([10.,10.,100.,100.,.1,.1,.1,.5])
   opt=least_squares(lambda y:weights*residual(y),x,
     bounds=(np.full(8,180.00001),np.full(8,389.99999)),
     x_scale=np.full(8,10.),max_nfev=45,
     ftol=1e-12,xtol=1e-12,gtol=1e-12)
   assert opt.success,opt.message
   x=opt.x
   st,rows,Qa,Qd,qcu,CuJoule,qbath=model(x)
   updated,newoffset=self.spatial.solve(
      with_solder_heat(rows),st,CuJoule,qcu,qbath,Qa)
   newgaps=np.array([z['top_minus_bottom_K'] for z in updated])
   pad_change=max(abs(newoffset[k]-offset[k]) for k in offset)
   gap_change=float(max(abs(newgaps-gaps)))
   maxdelta=max(pad_change,gap_change)
   logs.append({'step':iteration,'pad_delta_K':pad_change,
    'plate_drop_delta_K':gap_change,'Tdie_K':float(x[7]),
    'terminal_V':float(sum(z['voltage_v'] for z in st)+I*(self.Rcu+Rtotal)),
    'inner_nfev':int(opt.nfev)})
   if maxdelta<2e-7:
    fields=updated;offset=newoffset
    last='CONVERGED';break
   alpha=.7
   offset={k:offset[k]*(1-alpha)+newoffset[k]*alpha for k in offset}
   for idx in range(4):
    fields[idx]['top_minus_bottom_K']=(
      fields[idx]['top_minus_bottom_K']*(1-alpha)+newgaps[idx]*alpha)
  if last!='CONVERGED':raise RuntimeError('Spatial iteration did not converge '+str(logs[-1]))
  st,rows,Qa,Qd,qcu,CuJoule,qbath=model(x)
  r=residual(x)
  assert max(abs(r[:4]))<1e-8,('stage energy',r)
  assert max(abs(r[4:]))<2e-7,('surface thermal',r)
  assert max(abs(t['energy_residual_w']) for t in st)<1e-9
  assert max(abs(t['energy_W']) for t in rows)<1e-9
  assert max(abs(t['total_flux_mismatch_W']) for t in fields)<5e-8
  assert max(abs(t['free_thermal_residual_W']) for t in fields)<2e-8
  V=sum(z['voltage_v'] for z in st)+I*(self.Rcu+Rtotal)
  P=I*V
  global_err=P+load+self.Gau*(300-x[7])+qcu-.5*CuJoule-qbath
  assert abs(global_err)<1e-8,('global energy',global_err)
  assert 180<min(x)<max(x)<390
  assert len(rows)==88 and [s['nlegs'] for s in st]==[58,22,8]
  return {
   'id':c['id'],'parameter':param,
   'perturbation':c,
   'status':'CONVERGED_CONDITIONAL_INTEGRATED_V3_2_SYSTEM',
   'source_29_11_4':True,'current_A':I,
   'material_property_scales_S_rho_k':scales,
   'electrical_contact_rho_e_factor':contactmult,
   'radiator_thermal_R_K_W':radiator,
   'detector_heat_load_W':load,
   'die_temperature_K':float(x[7]),
   'terminal_voltage_V':float(V),
   'terminal_input_W':float(P),
   'heat_rejected_to_bath_W':float(qbath),
   'stage_hot_cold_mean_K':[float(q) for q in x],
   'stage_heat_and_power':st,
   'added_solder_and_contacts_total_R_ohm':Rtotal,
   'added_solder_and_contacts_Joule_W':Qsource,
   'max_absolute_native_ceramic_net_heat_W':max(abs(f['total_flux_mismatch_W']) for f in fields),
   'max_free_spatial_thermal_residual_W':max(abs(f['free_thermal_residual_W']) for f in fields),
   'global_energy_balance_W':float(global_err),
   'max_source_leg_energy_W':max(abs(r['energy_W']) for r in rows),
   'last_spatial_delta_K':maxdelta,
   'outer_iteration_count':len(logs),
   'trace':logs,
   'wall_s':time.monotonic()-tic,
   'original_P1_B':'FAIL/STOP','source_raw_first_pair':'FAIL 8/8',
   'full_original_430_C_D':'NOT RUN','as_built_physical_validation':False
  }

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--registration',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 reg=read(a.registration)
 assert reg==registration()
 assert not a.output.exists()
 run=SensitivityRunner()
 baseline=read(BASE)
 runs=[]
 start=time.monotonic()
 for c in reg['input_cases']:
  if time.monotonic()-start>reg['whole_study_wall_budget_seconds']:
   runs.append({'id':c['id'],'status':'NOT_RUN_WALL_BUDGET'})
   continue
  print('SENSITIVITY_CASE_BEGIN',c['id'],flush=True)
  try:
   result=run.run(c)
   result['delta_Tdie_vs_V3_2_K']=result['die_temperature_K']-baseline['calculated_detector_temperature_K']
   result['delta_terminal_V_vs_V3_2_V']=result['terminal_voltage_V']-baseline['terminal_voltage_V']
   result['delta_input_W_vs_V3_2_W']=result['terminal_input_W']-baseline['electrical_power_W']
   result['delta_bath_W_vs_V3_2_W']=result['heat_rejected_to_bath_W']-baseline['bath_heat_rejected_W']
   # Only normalized if this is multiplicative scaling of ONE input.
   if 'factor' in c:
    result['Tdie_delta_per_fractional_100pct_input_change_K']=result['delta_Tdie_vs_V3_2_K']/(c['factor']-1)
   else:
    result['Tdie_delta_per_input_unit_K']=result['delta_Tdie_vs_V3_2_K']/(c['target']-c['nominal'])
   runs.append(result)
   print('SENSITIVITY_CASE_PASS',c['id'],'DIE_K',result['die_temperature_K'],
    'DELTA_K',result['delta_Tdie_vs_V3_2_K'],
    'V',result['terminal_voltage_V'],'ITER',result['outer_iteration_count'],
    'SEC',round(result['wall_s'],2),flush=True)
  except Exception as e:
   runs.append({'id':c['id'],'parameter':c['param'],
    'status':'FAILED_NO_RESULT','reason':repr(e)[:650]})
   print('SENSITIVITY_CASE_FAIL',c['id'],repr(e),flush=True)
  a.output.write_text(json.dumps({'status':'PARTIAL_UNTIL_ALL_RECORDED',
    'registered_cases':len(reg['input_cases']),
    'completed_cases':len(runs),
    'source_V3_2_baseline':{
      'Tdie_K':baseline['calculated_detector_temperature_K'],
      'terminal_V':baseline['terminal_voltage_V'],
      'electrical_W':baseline['electrical_power_W'],
      'bath_W':baseline['bath_heat_rejected_W']},
    'cases':runs},indent=2)+'\n')
 passed=[x for x in runs if x['status']=='CONVERGED_CONDITIONAL_INTEGRATED_V3_2_SYSTEM']
 summary={'status':'BOUNDED V3_2 OAT PHYSICAL ASSUMPTION SCREEN, NOT STATISTICAL UNCERTAINTY OR OEM VALIDATION',
  'preregistered_cases':len(reg['input_cases']),
  'passed':len(passed),'failed':sum(x['status']=='FAILED_NO_RESULT' for x in runs),
  'not_run':sum(x['status']=='NOT_RUN_WALL_BUDGET' for x in runs),
  'rank_by_absolute_reference_perturbation_delta_Tdie':[
    {'id':x['id'],'param':x['parameter'],
     'delta_Tdie_K':x['delta_Tdie_vs_V3_2_K'],
     'abs_delta_Tdie_K':abs(x['delta_Tdie_vs_V3_2_K']),
     'terminal_delta_V':x['delta_terminal_V_vs_V3_2_V'],
     'input_power_delta_W':x['delta_input_W_vs_V3_2_W']} for x in sorted(
       passed,key=lambda v:abs(v['delta_Tdie_vs_V3_2_K']),reverse=True)],
  'wall_s':time.monotonic()-start,
  'original_P1_B':'FAIL/STOP','first_pair_raw_cut':'FAIL 8/8',
  'full_original_430_C_D':'NOT RUN'}
 (a.output.parent/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print('SENSITIVITY_SUMMARY',json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
