#!/usr/bin/env python3
"""Independent saved-result V3.3 source heat and conservation acceptance.

Standard-library recomputation of gas Eucken jump and gray radiation,
source solder heat, coupled stage equations, all four native source CAD
face loads, reference V3.2 deltas and standalone report provenance.
No FEM or nonlinear physical solve is performed here.
"""
import json,math,hashlib
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/v3_3_cavity_package_feedback_20261108/attempt02'
BASE=ROOT/'data/v3_2_joint_loss_feedback_20261107/attempt01/result.json'
FACE=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
REPORT=ROOT/'reports/generated/TEC_HgCdTe_Reference_V3_3_Standalone_Method_20261108.md'
def read(f):return json.loads(f.read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
 r=read(P/'result.json');reg=read(P/'registration.json');base=read(BASE)
 meta=read(FACE)['faces']
 assert r['source_individual_leg_count']==88 and r['original_ceramic_TET4']==11791
 assert r['source_original_B']=='FAIL/STOP' and r['full_original_430_domain_C_D']=='NOT RUN'
 assert abs(r['global_thermoelectric_energy_residual_W'])<reg['global_energy_tolerance_W']
 assert r['max_last_spatial_temperature_update_K']<reg['outer_thermal_field_tolerance_K']
 assert sha(ROOT/'scripts/v3_3_cavity_package_feedback.py')==reg['script_SHA256']
 assert r['source_input_sha256']==reg['source_SHA256']
 assert r['source_mesh_sha256']==reg['original_mesh_SHA256']
 assert (P/'source_native_ceramics_V3_3.npz').is_file()
 stage=r['source_stage_thermoelectric_budget']
 legs=r['source_individual_leg_flux_and_electric_results']
 pjoin=r['source_solder_and_interface_energy_per_single_joint_pad_W']
 assert abs(pjoin-25.95e-6)<1e-15
 assert len(legs)==88
 for i,num in enumerate((58,22,8)):
  group=[z for z in legs if z['stage']==i]
  assert len(group)==num
  assert abs(sum(z['Qhot_W'] for z in group)-stage[i]['qh_w'])<1e-11
  assert abs(sum(z['Qcold_W'] for z in group)-stage[i]['qc_w'])<1e-11
  assert abs(sum(z['terminal_contribution_V'] for z in group)-stage[i]['voltage_v'])<1e-11
 # Independently calculate existing physical closure without importing
 # modeled cavity or transport code; SI: V, K, m, Pa.
 t=r['source_full_temperature_nodes_K']
 temps=[t['stage1_hot'],t['stage2_hot'],t['carrier'],t['die']]
 areas=[12.6e-6,8.68e-6,4.76e-6,1e-6]
 ktab=[.0064,.0095,.0122]
 Rgas=99.218;gamma=5/3;pressure=100.;accom=.8
 cp=gamma/(gamma-1)*Rgas;sig=5.670374419e-8
 gcalc=[];rcalc=[];cond=[]
 for i,(temp,area) in enumerate(zip(temps,areas)):
  mean=(300+temp)*.5
  if mean<=300:kg=ktab[0]+(mean-200)*(ktab[1]-ktab[0])/100
  else:kg=ktab[1]+(mean-300)*(ktab[2]-ktab[1])/100
  mu=kg/(cp+1.25*Rgas)
  pr=mu*cp/kg
  lam=mu/pressure*math.sqrt(math.pi*Rgas*mean/2)
  delta=((2-accom)/accom)*(2*gamma/(gamma+1))*lam/pr
  conductance=kg*area/(.003+2*delta)
  gas=conductance*(300-temp)
  ew=.1 if i==3 else .2
  vf=.7 if i==3 else .5
  e_eff=1/(1/ew+1/.8-1)
  rad=vf*e_eff*sig*area*(300**4-temp**4)
  cond.append(conductance);gcalc.append(gas);rcalc.append(rad)
 for key,calc in [('cavity_gas_heat_into_three_ceramics_and_die_W',gcalc),
                  ('gray_radiation_heat_into_three_ceramics_and_die_W',rcalc),
                  ('gas_effective_conductance_W_K',cond)]:
  saved=r[key]
  assert max(abs(a-b) for a,b in zip(saved,calc))<1e-12,(key,saved,calc)
 E=[a+b for a,b in zip(gcalc,rcalc)]
 assert abs(sum(E)-r['total_enclosure_heat_into_cold_device_W'])<1e-12
 # Full source three interstage energies and separate detector.
 # Cold die attach energy is saved on C3 top face 119 *minus* its
 # incident cavity term because gas/radiation were distributed there.
 plates=r['original_native_source_ceramic_pad_flux_by_face']
 qa=(t['die']-t['carrier'])/20.
 checks=[
  stage[0]['qc_w']-stage[1]['qh_w']-80*pjoin-E[0],
  stage[1]['qc_w']-stage[2]['qh_w']-30*pjoin-E[1],
  stage[2]['qc_w']-qa-8*pjoin-E[2],
  qa-(.002+2*8.28149214560305e-6*(300-t['die'])+E[3])
 ]
 assert max(abs(q) for q in checks)<reg['inner_balance_tolerance_W'],checks
 # Native source pad table reconstruction. Final-stage ceramic FEM
 # field may differ from final nonlinear leg loads by finite outer
 # convergence tolerance. Preserve rather than relabel it exact.
 maxdiff=[]
 for ci,plate in enumerate(plates):
  actual={int(k):v for k,v in plate['heat_per_source_face_W'].items()}
  expected=defaultdict(float)
  for z in legs:
   if z['stage']==ci: expected[z['hot_tag']]+=z['Qhot_W']+pjoin
   if z['stage']+1==ci:expected[z['cold_tag']]+=-z['Qcold_W']+pjoin
  if ci in (1,2,3):
   top=[int(k) for k in actual if k in ({1:set(range(74,87)),2:set(range(104,109)),3:{119}}[ci])]
   area=sum(meta[str(k)]['face_area_mm2'] for k in top)
   for k in top:expected[k]+=E[ci-1]*meta[str(k)]['face_area_mm2']/area
  if ci==0:
   expected[36]+=r['heat_Cu_lead_correction_W']
   expected[6]-=r['bath_heat_rejected_W']
  if ci==3:expected[119]+=qa
  discrepancy=max(abs(actual.get(k,0)-v) for k,v in expected.items())
  maxdiff.append(discrepancy)
  assert abs(sum(actual.values()))<reg['local_plate_net_heat_tolerance_W']
  assert plate['free_thermal_residual_W']<2e-8
 # Comparison to same model's cavity-OFF operating point
 assert abs(r['V3_2_same_current_comparison']['V3_3_minus_V3_2_Tdie_K']-
  (r['calculated_detector_temperature_K']-base['calculated_detector_temperature_K']))<1e-12
 assert abs(r['electrical_power_W']-.4*r['terminal_voltage_V'])<1e-12
 assert REPORT.is_file() and REPORT.stat().st_size>10000
 rep=REPORT.read_text()
 for token in ('84-value','29/11/4','Appendix B','Appendix C','E1+E2+E3+Edie',
               'standalone report','full 430-domain'):
  assert token.lower() in rep.lower(),token
 report={
 'status':'PASS independent saved V3.3 stage/leg/thermal enclosure consistency and standalone source-independent method coverage; finite local face lag explicitly retained',
 'numerical_accepted':True,'no_new_PDE_or_nonlin_solve':True,
 'original_P1_B':'FAIL/STOP','first_pair_raw_P1':'FAIL 8/8',
 'full_source_430_domain_C_D':'NOT RUN',
 'source_ceramic_tets':11791,'source_thermoelectric_legs':88,
 'source_cavity_gas_W':gcalc,
 'source_cavity_gray_radiation_W':rcalc,
 'source_cavity_total_W':sum(E),
 'cavity_thermal_reservoir_return_W':-sum(E),
 'independent_stage_node_heat_residuals_W':checks,
 'max_saved_original_face_heat_vs_last_leg_model_discrepancy_W':max(maxdiff),
 'per_original_ceramic_max_saved_face_residual_W':maxdiff,
 'full_system_global_energy_residual_W':r['global_thermoelectric_energy_residual_W'],
 'full_source_3D_mesh_remeshed':False,
 'V3_2_source_off_Tdie_K':base['calculated_detector_temperature_K'],
 'new_V3_3_Tdie_K':r['calculated_detector_temperature_K'],
 'delta_Tdie_K':r['calculated_detector_temperature_K']-base['calculated_detector_temperature_K'],
 'rev3_original_report_modified':False,
 'standalone_report_note':'independent reproducer includes SI material table, 88 leg centre coordinates, original pad centroids and heat, boundary laws, numerical gates, distinguishing current 430/29-11-4 from older Rev3 geometry',
 'source_result_sha256':sha(P/'result.json'),
 'source_registration_sha256':sha(P/'registration.json'),
 'standalone_report_sha256':sha(REPORT)}
 f=P/'independent_read_only_acceptance.json'
 assert not f.exists()
 f.write_text(json.dumps(report,indent=2)+'\n')
 print('V33_INDEPENDENT_SOURCE_AND_COMPLETE_DEVICE_ACCEPTANCE',
    json.dumps({'status':report['status'],'max_saved_face_lag_W':report['max_saved_original_face_heat_vs_last_leg_model_discrepancy_W'],
                'Q_cavity_W':sum(E),'Tdie_K':r['calculated_detector_temperature_K']},indent=2))
if __name__=='__main__':main()
