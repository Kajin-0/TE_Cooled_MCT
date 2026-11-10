"""Independent post-solve reconstruction of stage, Cu, lead, gas and sink balances."""
from pathlib import Path
import argparse,json,hashlib,numpy as np
from tecooledmct.height_coupling_v320 import (ORIGINAL,CANDIDATE,read,copper_specs,wire_geometry,interstage_gas_geometry,interstage_gas)
from scripts.v3_r3_sink_wire_sensitivity import geometry as base_geometry
ROOT=Path(__file__).resolve().parents[1]
def close(a,b,tol=1e-8):
 if abs(a-b)>tol:raise ValueError(f'{a} != {b} (tol {tol})')
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',type=Path,required=True);a=p.parse_args();r=read(a.case/'result.json');I=r['operating_current_A'];assert .25<=I<=.55
 d=read(ORIGINAL if r['variant']=='nominal' else CANDIDATE);q=r['source_individual_leg_flux_and_electric_results'];assert len(q)==88
 legs=[];st=[]
 for k in range(3):
  z=[x for x in q if x['stage']==k];assert len(z)==(58,22,8)[k]
  H=sum(x['Qhot_W'] for x in z);C=sum(x['Qcold_W'] for x in z);V=sum(x['terminal_contribution_V'] for x in z)
  for row in z:legs.append(row['Qhot_W']-row['Qcold_W']-I*row['terminal_contribution_V'])
  close(H,r['source_stage_thermoelectric_budget'][k]['qh_w'],1e-11);close(C,r['source_stage_thermoelectric_budget'][k]['qc_w'],1e-11);close(V,r['source_stage_thermoelectric_budget'][k]['voltage_v'],1e-11)
  st.append({'qh':H,'qc':C,'v':V,'residual':H-C-I*V})
 assert max(abs(x) for x in legs)<1e-9
 assert min(x['leg_min_K'] for x in q)>=180 and max(x['leg_max_K'] for x in q)<=390
 n=r['source_full_temperature_nodes_K'];T=[n[x] for x in ('stage0_hot','stage0_cold','stage1_hot','stage1_cold','stage2_hot','stage2_cold','carrier','die')]
 ig=[float(interstage_gas(T[2*j],T[2*j+1],z['gap_m'],z['area_m2'])['Q_W']) for j,z in enumerate(interstage_gas_geometry(d))]
 assert np.allclose(ig,r['internal_interstage_gas_heat_hot_to_cold_W'],atol=1e-12,rtol=1e-12)
 cm=r['Cu_form_tab_electrothermal_result'];spec=copper_specs(d);cp=0.
 for k,v in cm['net_details'].items():
  close(sum(v['face_heat_into_ceramic_W']),v['electric_Joule_W'],1e-11)
  close(v['electric_Joule_W'],I*I*v['electric_resistance_ohm'],1e-12)
  assert np.allclose(v['segment_length_m'],spec[int(k)]['segments_m'],atol=1e-14,rtol=0)
  if k=='88':assert v['contact_electrical_R_ohm'][1]==0
  cp+=v['electric_Joule_W']
 close(cp,cm['total_electrical_power_W'],1e-11)
 lead=r['source_tec_power_leads'];close(sum(lead['face_heats_W'].values()),lead['total_pad_heat_W'],1e-12)
 close(sum(v['joule_wire_W'] for v in lead['per_lead'].values()),I*I*lead['total_R_ohm'],1e-12)
 P=I*(sum(z['v'] for z in st)+I*(lead['total_R_ohm']+r['source_total_solder_and_contact_series_resistance_ohm']+cm['total_electrical_R_ohm']))
 close(P,r['electrical_power_W'],1e-10);close(P,.5956680349614825,1e-8);close(P,I*r['terminal_voltage_V'],1e-12)
 ext=np.array(r['cavity_gas_heat_into_three_ceramics_and_die_W'])+r['gray_radiation_heat_into_three_ceramics_and_die_W']
 joint=I*I*r['one_joint_series_resistance_ohm'];c=cm['heat_into_ceramic_by_stage_W'];dieR=base_geometry()['die_attach_thickness_over_area_m_inverse'];Qa=(T[7]-T[6])/dieR
 wires=wire_geometry(d);Gau=sum(x['G_W_K'] for x in wires if x['name'].startswith('detector_bond'))
 Qd=.002+Gau*(300-T[7])+ext[3];bath=r['bath_heat_rejected_W']
 residual=[st[0]['qc']-st[1]['qh']-80*joint-ext[0]-c[1]-ig[0]+ig[1],st[1]['qc']-st[2]['qh']-30*joint-ext[1]-c[2]-ig[1]+ig[2],st[2]['qc']-Qa-8*joint-ext[2]-ig[2],Qa-Qd,
 bath-(st[0]['qh']+lead['total_pad_heat_W']+58*joint+c[0]-ig[0])]
 global_balance=P+.002+Gau*(300-T[7])+sum(ext)+lead['conduction_into_ceramic_W']-.5*lead['joule_W']-bath
 assert max(abs(x) for x in residual)<1e-7 and abs(global_balance)<1e-7
 for f in r['original_native_source_ceramic_pad_flux_by_face']:assert abs(f['total_flux_mismatch_W'])<5e-8
 with np.load(a.case/'ceramic_fields.npz',allow_pickle=False) as f,np.load(ROOT/'data/tec_height_coupling_20261110/translated_ceramic_nodes.npz',allow_pickle=False) as ref:
  for i in range(4):
   key=f'ceramic{i}';assert np.array_equal(f[key+'_source_node_id_1based'],ref[key+'_source_node_ids_1based'])
   coords=ref[key+'_translated_xyz_mm'].copy()
   if r['variant']=='nominal':coords[:,2]-=.1*i
   assert np.allclose(f[key+'_xyz_mm'],coords,rtol=0,atol=1e-10)
 assert r['max_last_spatial_temperature_update_K']<3e-7
 o={'status':'PASS independent recorded-result reconstruction; engineering gas/exchange proxy remains unvalidated','variant':r['variant'],'I_A':I,'power_W':P,'T_die_K':T[7],
    'stage_boundary_residual_W':residual,'global_energy_residual_W':global_balance,'max_leg_residual_W':max(abs(x) for x in legs),
    'interstage_gas_W':ig,'source_thermal_mapping':'PASS translated coordinates and node IDs','result_sha256':hashlib.sha256((a.case/'result.json').read_bytes()).hexdigest()}
 (a.case/'independent_audit.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o),flush=True)
if __name__=='__main__':main()
