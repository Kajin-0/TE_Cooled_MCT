"""Independent 3-stage, Cu, lead, gas, die and sink reconstruction per case."""
from pathlib import Path
import argparse,json,hashlib,math,numpy as np
from tecooledmct.height_coupling_v320 import ORIGINAL,CANDIDATE,read,copper_specs,wire_geometry
from tecooledmct.integrated_reference import Scenario,gas_transport,radiative_load
from scripts.v3_r3_sink_wire_sensitivity import geometry as base_geometry
R=Path(__file__).resolve().parents[1];DATA=R/'data/tec_height_robustness_20261110'
def close(a,b,tol):
 if abs(a-b)>tol:raise ValueError(f'{a} vs {b} (tolerance {tol})')
def audit(p):
 r=read(p/'result.json');cfg=r['scenario_configuration'];contract=read(DATA/'contract.json');assert cfg==contract['scenarios'][r['scenario']]
 I=r['operating_current_A'];assert .25<=I<=.55;q=r['source_individual_leg_flux_and_electric_results'];assert len(q)==88
 d=read(ORIGINAL if r['variant']=='nominal' else CANDIDATE);b={x['name']:x for x in d['bodies']};st=[];legs=[]
 for k in range(3):
  z=[x for x in q if x['stage']==k];assert len(z)==(58,22,8)[k]
  H=sum(x['Qhot_W'] for x in z);C=sum(x['Qcold_W'] for x in z);V=sum(x['terminal_contribution_V'] for x in z)
  for row in z:legs.append(row['Qhot_W']-row['Qcold_W']-I*row['terminal_contribution_V'])
  for v,key in ((H,'qh_w'),(C,'qc_w'),(V,'voltage_v')):close(v,r['source_stage_thermoelectric_budget'][k][key],1e-11)
  st.append({'qh':H,'qc':C,'v':V})
 assert max(abs(x) for x in legs)<1e-9 and min(x['leg_min_K'] for x in q)>=180 and max(x['leg_max_K'] for x in q)<=390
 n=r['source_full_temperature_nodes_K'];T=[n[x] for x in ('stage0_hot','stage0_cold','stage1_hot','stage1_cold','stage2_hot','stage2_cold','carrier','die')];gas=Scenario(gas='Kr',cavity_pressure_pa=100.,accommodation=.8);ig=[]
 for j in range(3):
  lo=b[f'ceramic{j}']['boxes_mm'][0];up=b[f'ceramic{j+1}']['boxes_mm'][0];ll=[x for x in d['legs'] if x['stage']==j]
  solid=sum(b[f'leg{x["index"]}_{x["polarity"]}']['boxes_mm'][0][3]*b[f'leg{x["index"]}_{x["polarity"]}']['boxes_mm'][0][4] for x in ll)
  A=(up[3]*up[4]-solid)*1e-6;gap=(up[2]-lo[2]-lo[5]-.03)*1e-3;k,jump,below=gas_transport(gas,(T[j*2]+T[j*2+1])/2);assert not below and A>0 and gap>0
  ig.append(cfg['interstage_factor']*float(k*A*(T[2*j]-T[2*j+1])/(gap+2*jump)))
  close(ig[-1],r['internal_interstage_gas_heat_hot_to_cold_W'][j],1e-12)
 ext=[];rad=[]
 for j,(A,t) in enumerate(zip(r['source_exposed_effective_surface_area_m2'],[T[2],T[4],T[6],T[7]])):
  k,jump,below=gas_transport(gas,(300+t)/2);assert not below
  ext.append(float(k*A*(300-t)/(cfg['outer_gap_m']+2*jump)));rad.append(float(radiative_load(300,t,A,.1 if j==3 else .2,.8,.7 if j==3 else .5)))
  close(ext[-1],r['cavity_gas_heat_into_three_ceramics_and_die_W'][j],1e-12);close(rad[-1],r['gray_radiation_heat_into_three_ceramics_and_die_W'][j],1e-12)
 total=np.array(ext)+rad;cm=r['Cu_form_tab_electrothermal_result'];spec=copper_specs(d)
 for k,v in cm['net_details'].items():
  close(sum(v['face_heat_into_ceramic_W']),v['electric_Joule_W'],1e-11);close(v['electric_Joule_W'],I*I*v['electric_resistance_ohm'],1e-12)
  assert np.allclose(v['segment_length_m'],spec[int(k)]['segments_m'],atol=1e-14,rtol=0)
  if k=='88':assert v['contact_electrical_R_ohm'][1]==0
 lead=r['source_tec_power_leads'];close(sum(lead['face_heats_W'].values()),lead['total_pad_heat_W'],1e-12);close(sum(x['joule_wire_W'] for x in lead['per_lead'].values()),I*I*lead['total_R_ohm'],1e-12)
 P=I*(sum(x['v'] for x in st)+I*(lead['total_R_ohm']+r['source_total_solder_and_contact_series_resistance_ohm']+cm['total_electrical_R_ohm']));close(P,r['electrical_power_W'],1e-10);close(P,I*r['terminal_voltage_V'],1e-12);close(P,contract['target_power_W'],1e-8)
 joint=I*I*r['one_joint_series_resistance_ohm'];c=cm['heat_into_ceramic_by_stage_W'];dieR=base_geometry()['die_attach_thickness_over_area_m_inverse'];Qa=(T[7]-T[6])/dieR;Gau=sum(w['G_W_K'] for w in wire_geometry(d) if w['name'].startswith('detector_bond'));bath=r['bath_heat_rejected_W']
 stage=[st[0]['qc']-st[1]['qh']-80*joint-total[0]-c[1]-ig[0]+ig[1],st[1]['qc']-st[2]['qh']-30*joint-total[1]-c[2]-ig[1]+ig[2],st[2]['qc']-Qa-8*joint-total[2]-ig[2],Qa-(.002+Gau*(300-T[7])+total[3]),bath-(st[0]['qh']+lead['total_pad_heat_W']+58*joint+c[0]-ig[0])]
 glob=P+.002+Gau*(300-T[7])+sum(total)+lead['conduction_into_ceramic_W']-.5*lead['joule_W']-bath
 assert max(abs(x) for x in stage)<1e-8 and abs(glob)<1e-8
 base=read(R/'data/v2_integrated_spatial_20261107/attempt02/v2_integrated_result.json')['hot_external_R_without_ceramic0_K_W']
 hot=T[0]-300-(base+cfg['extra_sink_K_W'])*bath-r['original_native_source_ceramic_pad_flux_by_face'][0]['top_minus_bottom_K'];assert abs(hot)<3e-7
 assert r['max_last_spatial_temperature_update_K']<3e-7 and max(abs(f['total_flux_mismatch_W']) for f in r['original_native_source_ceramic_pad_flux_by_face'])<5e-8
 with np.load(p/'ceramic_fields.npz',allow_pickle=False) as f,np.load(R/'data/tec_height_coupling_20261110/translated_ceramic_nodes.npz',allow_pickle=False) as ref:
  for i in range(4):
   stem=f'ceramic{i}';assert np.array_equal(f[stem+'_source_node_id_1based'],ref[stem+'_source_node_ids_1based']);cxyz=ref[stem+'_translated_xyz_mm'].copy()
   if r['variant']=='nominal':cxyz[:,2]-=.1*i
   assert np.allclose(f[stem+'_xyz_mm'],cxyz,atol=1e-10,rtol=0)
 o={'status':'PASS independent balances; gas and contact physics unvalidated','scenario':r['scenario'],'variant':r['variant'],'power_W':P,'die_K':T[7],'top_K':T[6],
 'stage_residual_W':stage,'global_residual_W':glob,'sink_boundary_residual_K':hot,'max_leg_residual_W':max(abs(x) for x in legs),
 'internal_gas_W':ig,'external_gas_W':ext,'radiation_W':rad,'result_sha256':hashlib.sha256((p/'result.json').read_bytes()).hexdigest()}
 (p/'independent_audit.json').write_text(json.dumps(o,indent=2)+'\n');return o
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--case',required=True,type=Path);a=parser.parse_args();print(json.dumps(audit(a.case)))
