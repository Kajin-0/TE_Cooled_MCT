"""Independent scalar gas and whole-package balance readback; no new solve."""
from pathlib import Path
import hashlib,json
import numpy as np
from tecooledmct.nominal_gas_p1_v325 import exchange
from tecooledmct.height_coupling_v320 import wire_geometry,ORIGINAL,read
from scripts.v3_r3_sink_wire_sensitivity import geometry
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_p1_20261111';C=D/'coupled_attempt01'
def main():
 r=read(C/'result.json');p=read(D/'p1_operator.json');f=np.load(C/'ceramic_fields.npz');src=np.load(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz');T={};node_plate={}
 for i in range(4):
  ids=f[f'ceramic{i}_source_node_id_1based'];xyz=f[f'ceramic{i}_xyz_mm'];vals=f[f'ceramic{i}_temperature_K'];assert np.array_equal(ids,src[f'ceramic{i}_source_node_id_1based']) and np.allclose(xyz,src[f'ceramic{i}_xyz_mm'],atol=1e-12,rtol=0)
  for nid,val in zip(ids,vals):T[int(nid)]=float(val);node_plate[int(nid)]=i
 g=exchange(p['pairs'],T,100.,.8);assert np.allclose(g['stage_heat_hot_to_cold_W'],r['gas_final_links_W'],rtol=0,atol=1e-8)
 for i in range(4):
  ids=f[f'ceramic{i}_source_node_id_1based'];load=f[f'ceramic{i}_gas_nodal_load_W'];expected=np.array([g['node_load_W'].get(int(k),0.) for k in ids]);assert np.max(abs(load-expected))<1e-12
 assert abs(sum(g['node_load_W'].values()))<1e-12
 I=r['operating_current_A'];legs=r['source_individual_leg_flux_and_electric_results'];assert len(legs)==88;st=[];lr=[]
 for i,n in enumerate((58,22,8)):
  group=[x for x in legs if x['stage']==i];assert len(group)==n;H=sum(x['Qhot_W'] for x in group);Cq=sum(x['Qcold_W'] for x in group);V=sum(x['terminal_contribution_V'] for x in group)
  for x in group:lr.append(x['Qhot_W']-x['Qcold_W']-I*x['terminal_contribution_V'])
  raw=r['source_stage_thermoelectric_budget'][i];assert max(abs(H-raw['qh_w']),abs(Cq-raw['qc_w']),abs(V-raw['voltage_v']))<1e-11;st.append({'h':H,'c':Cq,'v':V})
 assert max(map(abs,lr))<1e-9 and min(x['leg_min_K'] for x in legs)>=180 and max(x['leg_max_K'] for x in legs)<=390
 assert not any(r['cavity_gas_heat_into_three_ceramics_and_die_W']);n=r['source_full_temperature_nodes_K'];Ts=[n[k] for k in ('stage0_hot','stage0_cold','stage1_hot','stage1_cold','stage2_hot','stage2_cold','carrier','die')];rad=np.asarray(r['gray_radiation_heat_into_three_ceramics_and_die_W']);ig=g['stage_heat_hot_to_cold_W'];cm=r['Cu_form_tab_electrothermal_result'];c=cm['heat_into_ceramic_by_stage_W'];lead=r['source_tec_power_leads'];joint=I*I*r['one_joint_series_resistance_ohm'];Gau=sum(x['G_W_K'] for x in wire_geometry(read(ORIGINAL)) if x['name'].startswith('detector_bond'));Qa=(Ts[7]-Ts[6])/geometry()['die_attach_thickness_over_area_m_inverse'];bath=r['bath_heat_rejected_W'];power=I*r['terminal_voltage_V']
 residual=[st[0]['c']-st[1]['h']-80*joint-rad[0]-c[1]-ig[0]+ig[1],st[1]['c']-st[2]['h']-30*joint-rad[1]-c[2]-ig[1]+ig[2],st[2]['c']-Qa-8*joint-rad[2]-ig[2],Qa-(.002+Gau*(300-Ts[7])+rad[3]),bath-(st[0]['h']+lead['total_pad_heat_W']+58*joint+c[0]-ig[0])]
 glob=power+.002+Gau*(300-Ts[7])+sum(rad)+lead['conduction_into_ceramic_W']-.5*lead['joule_W']-bath
 assert max(map(abs,residual))<1e-8 and abs(glob)<1e-8 and abs(power-.5956680349614825)<1e-8
 for k,v in cm['net_details'].items():assert abs(sum(v['face_heat_into_ceramic_W'])-v['electric_Joule_W'])<1e-11
 assert cm['net_details']['88']['contact_electrical_R_ohm'][1]==0
 assert max(abs(float(x['total_flux_mismatch_W'])) for x in r['original_native_source_ceramic_pad_flux_by_face'])<5e-8
 out={'status':'PASS independently reconstructed original-only partial-cavity balance; physical full cavity not qualified','source_result_sha256':hashlib.sha256((C/'result.json').read_bytes()).hexdigest(),'max_stage_residual_W':max(map(abs,residual)),'global_residual_W':glob,'power_residual_W':power-.5956680349614825,'max_leg_residual_W':max(map(abs,lr)),'gas_global_W':sum(g['node_load_W'].values()),'gas_links_W':ig,'die_K':Ts[7],'top_K':Ts[6],'sink_W':bath,'P_W':power,'I_A':I,'V_V':r['terminal_voltage_V'],'other_gas_surfaces':'adiabatic, not physical cavity validation'}
 q=C/'independent_audit.json';assert not q.exists();q.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
