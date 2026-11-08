#!/usr/bin/env python3
"""Fail-closed source-grade thermoelectric material readiness, NO model solve.

Inspect active P/N source table, on-disk solver extension, two different
original research specimens, matched-OEM evidence, per-point digitization
bounds, and exact 88 V3.2 leg hot/cold values. A linear-length temperature
fraction is a proxy only; actual nonlinear axial T profiles are NOT
reconstructed by this ledger. Existing released V3.2 remains unchanged.
"""
from pathlib import Path
import json,hashlib,argparse,math,statistics
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/g2c/zhang2025_he_40_300_v2.json'
V32=ROOT/'data/v3_2_joint_loss_feedback_20261107/attempt01/result.json'
V32REG=ROOT/'data/v3_2_joint_loss_feedback_20261107/attempt01/registration.json'
SENS=ROOT/'data/v3_2_bounded_sensitivity_20261107/attempt01/fast_results.json'
OLDREG=ROOT/'data/g2c/source_registry.json'
SCRIPTS=[
 ROOT/'tecooledmct/graded_tec.py',ROOT/'tecooledmct/nonlinear_tec.py',
 ROOT/'tecooledmct/material_profiles.py'
]
def read(f):return json.loads(f.read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def analyze():
 p=read(SOURCE);v=read(V32);r=read(V32REG);old=read(OLDREG)
 assert p['schema_version']==1 and p['status']=='published_sample_plot_digitization'
 assert p['id']=='zhang2025_he_digitized_40_300_v2r1'
 assert p['valid_temperature_k']==[40,300]
 assert p['extrapolation_policy']=='reject'
 assert p['oem_grade_matched'] is False and p['paired_module_specimens'] is False
 assert p['doi']=='10.1088/0256-307X/42/5/056304'
 assert old['oem_material']['grade_matched_profile_available'] is False
 assert v['operating_current_A']==.4 and v['source_stage_couples']==[29,11,4]
 assert v['source_individual_leg_count']==88
 assert v['source_original_B']=='FAIL/STOP' and v['full_original_430_domain_C_D']=='NOT RUN'
 assert v['temperature_above_research_transport_300K']=='ASSUMED CONTINUATION'
 assert r['nominal_research_transport_above_300K']=='unmeasured extrapolation used'
 grouped={}
 checks=[]
 values={}
 required={'S':'V/K','rho':'ohm m','k':'W/(m K)'}
 for pol in ('P','N'):
  record=p['specimens'][pol]
  assert record['same_specimen_triple_properties']
  assert record['sample_id'] in ('P-HE','N-HE-1')
  assert record['supplier_grade']=='not named in main paper; supplement unavailable'
  checked=[]
  for name,unit in required.items():
   curve=record['curves'][name]
   assert curve['unit']==unit
   arr=curve['points']
   assert len(arr)==14
   t=[pt['temperature_k'] for pt in arr]
   a=[pt['value_si'] for pt in arr]
   assert t==list(range(40,301,20))
   assert all(math.isfinite(x) for x in a+t)
   assert all(a0>0 for a0 in a) if name!='S' else all(
    (x>0 if pol=='P' else x<0) for x in a)
   assert all(pt['value_reading_bound_si']>0 for pt in arr)
   assert all(pt['temperature_reading_bound_k']>0 for pt in arr)
   assert all(pt['temperature_reading_bound_k']<2. for pt in arr)
   assert all(pt['value_reading_bound_si'] < max(abs(x)*.25,1e-15)
        for pt,x in zip(arr,a))
   checked.append(name)
   def extract(temp):
    pt=arr[t.index(temp)]
    return {'value_si':pt['value_si'],
      'digitized_graph_reading_only_bound_si':pt['value_reading_bound_si'],
      'source_temperature_reading_bound_K':pt['temperature_reading_bound_k']}
   checks.append({'polarity':pol,'specimen':record['sample_id'],
     'property':name,'source_figure_panel':curve['figure_panel'],
     'SI_unit':unit,'points':len(arr),
     'source_figure_range_K':[40,300],
     '200K':extract(200),'300K':extract(300),
     'same_specimen_triple_property':True,
     'value_evidence':'PUBLISHED FIGURE MARKER DIGITIZATION, not laboratory raw measurements',
     'reading_bounds_not_physical_uncertainty':True,
     'transport_law_ready_for_assumed_research_analog_40_300K':True,
     'matched_exact_TEC_module_grade':False})
   values[(pol,name)]=arr
  assert set(checked)==set(required)
  grouped[pol]={'source_specimen':record['sample_id'],
     'source_composition':record['composition'],'process':record['process'],
     'nominal_supplier_grade':None,
     'P_N_actual_module_pair_matched':False}
 assert len(checks)==6 and sum(c['points'] for c in checks)==84
 stage={}
 hot_missing=[]
 leg_rows=v['source_individual_leg_flux_and_electric_results']
 for s in range(3):
  rows=[x for x in leg_rows if x['stage']==s]
  assert len(rows)==[58,22,8][s]
  crossing=[]
  for z in rows:
   th,tc=z['Th_K'],z['Tc_K']
   assert 180<tc<th<390
   high=th>300.
   if high: hot_missing.append(z['source_leg_ID'])
   # This is a *linear interpolation of END temperatures only*;
   # nonlinear actual 33-node TE profile is not archived here.
   high_proxy=max(0.,min(1.,(th-300.)/(th-tc)))
   crossing.append({'original_leg_id':z['source_leg_ID'],
     'source_polarity':z['material'],
     'hot_T_K':th,'cold_T_K':tc,
     'published_curve_all_leg_endpoint_covered':not high,
     'terminal_beyond_300K_K':max(0.,th-300.),
     'linear_axial_over_300_fraction_PROXY':high_proxy,
     'actual_nonlinear_leg_fraction_above_300':'NOT COMPUTED IN THIS READ ONLY AUDIT'})
  stage[str(s)]={'source_leg_count':len(rows),
   'legs_with_hot_end_above_300K':sum(z['hot_T_K']>300. for z in crossing),
   'stage_hot_boundary_extrema_K':[min(z['hot_T_K'] for z in crossing),max(z['hot_T_K'] for z in crossing)],
   'stage_cold_boundary_extrema_K':[min(z['cold_T_K'] for z in crossing),max(z['cold_T_K'] for z in crossing)],
   'max_hot_overshoot_above_published_K':max(z['terminal_beyond_300K_K'] for z in crossing),
   'mean_linear_axial_above_300_fraction_PROXY':statistics.mean(z['linear_axial_over_300_fraction_PROXY'] for z in crossing),
   'source_legs':crossing}
 assert len(hot_missing)==58 and all(z['hot_T_K']<=300 for s in ('1','2') for z in stage[s]['source_legs'])
 maxhot=max(z['Th_K'] for z in leg_rows)
 mincold=min(z['Tc_K'] for z in leg_rows)
 assert maxhot>300 and mincold>200
 src=self_sources={
  'active_research_specimen_digitized_P_N':SOURCE,
  'whole_V3_2_88_leg_operating_point':V32,
  'whole_V3_2_registration':V32REG,
  'old_public_source_registry':OLDREG,
  'fast_whole_system_sensitivity_reference':SENS
 }
 src.update({f'active_law_{f.name}':f for f in SCRIPTS})
 prior=read(SENS)
 assert prior['source_29_11_4']
 return {
  'status':'PHYSICAL MATERIAL CONTRACT: RESEARCH-SPECIMEN TRANSPORT IS NUMERICALLY USABLE WITH DECLARED EXTRAPOLATION; OEM MATERIAL PREDICTION FAIL-CLOSED',
  'source_DOI':p['doi'],'published_source_URL':p['source_url'],
  'source_identity':p['id'],'original_source_pdf_SHA256':p['original_pdf_sha256'],
  'source_specimens':grouped,
  'P_N_actual_material_grade_matched':False,
  'same_P_N_specimen_or_manufactured_module':False,
  'six_curve_coverage_and_figure_reading_bounds':checks,
  'total_digitized_plot_point_count':84,
  'published_all_six_property_temperature_intersection_K':[40.,300.],
  'actual_active_solver_material_range_K':[180.,390.],
  'working_V3_2_temperature_extrema_K':[mincold,maxhot],
  'source_88_leg_original_CAD_contacts_evaluated':88,
  'source_P_N_legs_with_hot_boundary_above_published_300K':len(hot_missing),
  'source_P_N_legs_above_300K_by_stage':[stage[str(i)]['legs_with_hot_end_above_300K'] for i in range(3)],
  'max_original_leg_hot_temperature_above_published_300K_K':maxhot-300.,
  'per_stage_original_leg_temperature_and_extrapolation_audit':stage,
  'solver_high_T_policy':'300<T<=390K: take source 300K value + (T-300K)*(0.25 final 280..300K plotted tangent); no published measurements above 300K; not an OEM grade',
  'source_digitization_error_kind':'graph axis and red marker position only; excludes published instrument measurement uncertainty and between specimen systematic differences',
  'physical_device_uncertainty_or_OEM_matching':'UNAVAILABLE',
  'material_readiness_gate':{
    'research_analog_source_six_curves_are_source_traceable':True,
    'model_accepted_as_conditional_hypothesis':True,
    'actual_installed_TEC_P_grade_evidence':'MISSING',
    'actual_installed_TEC_N_grade_evidence':'MISSING',
    'P_and_N_same_TEC_purchase_specification':'UNVERIFIED',
    'matched_P_and_N_measurement_uncertainty_at_200_to_305K':'MISSING',
    'actual_extrapolated_hot_side_300_to_305K_source_curve':'MISSING',
    'actual_TE_manufacturer_thermocouple_contact_and_transport_law':'MISSING',
    'actual_module_current_voltage_vs_ambient_and_load':'MISSING',
    'release_source_as_as_built_predictive_material_law':False
   },
  'highest_value_missing_data':[
   'Actual TEC manufacturer model/part and P/N grade or lot identifiers',
   'P and N S(T), rho(T), k(T) from actual installed material for ~200..305K, uncertainty and current direction',
   'At least source module I/V and detector or cold plate T at known heat load and 300K hot-side boundary',
   'Electrical contact and thermal interface resistance measurements/traceable manufacturer specification'
  ],
  'source_sha256':{k:sha(q) for k,q in src.items()},
  'script_SHA256':sha(Path(__file__)),
  'original_P1_Gate_B':'FAIL/STOP',
  'first_original_P1_pair_raw_current':'FAIL 8/8',
  'full_original_430_domain_C_D':'NOT RUN',
  'new_3D_PDE_or_refit_runs':0,
  'original_CAD_and_model_source_modified':False
 }
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 args=p.parse_args()
 result=analyze()
 if args.verify_only:
  assert result==read(args.output)
 else:
  assert not args.output.exists()
  args.output.write_text(json.dumps(result,indent=2)+'\n')
 print('MATERIAL_READINESS_AUDIT',json.dumps({
 'source':result['source_identity'],
 'source_properties':len(result['six_curve_coverage_and_figure_reading_bounds']),
 'digitized_points':result['total_digitized_plot_point_count'],
 'original_source_leg_high_T_count':result['source_P_N_legs_with_hot_boundary_above_published_300K'],
 'hot_above_300K_K':result['max_original_leg_hot_temperature_above_published_300K_K'],
 'actual_OEM_material_release':result['material_readiness_gate']['release_source_as_as_built_predictive_material_law'],
 },indent=2))
if __name__=='__main__':main()
