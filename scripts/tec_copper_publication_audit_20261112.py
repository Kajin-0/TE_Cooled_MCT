"""Independent readback for copper thermal-off publication ablation.

No imports from the forward solver or the copper-ablation source. Reconstructs
copper Joule partition, passive-conduction absence, source 88-leg conservation,
gas exchange, stage, sink, and whole-system energy from saved artifacts.
Does not validate real metal properties, complete cavity or measured hardware.
"""
from pathlib import Path
import hashlib, json
import numpy as np
from tecooledmct.nominal_gas_p1_v325 import exchange
from tecooledmct.nominal_gas_visibility_v327 import die_window_exchange
from tecooledmct.height_coupling_v320 import wire_geometry,ORIGINAL,read
from scripts.v3_r3_sink_wire_sensitivity import geometry
from scripts.v3_4_source_copper_multiport import STAGES

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/copper_ablation_publication_20261112'
PRIOR=ROOT/'data/nominal_gas_visibility_v327_20261111'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    r=read(D/'result.json');reg=read(D/'registration.json')
    assert digest(PRIOR/'coupled_attempt01/result.json')==reg['baseline_result_sha256']
    assert digest(PRIOR/'coupled_attempt01/independent_audit.json')==reg['baseline_audit_sha256']
    assert r['ablation_executed_source_sha256']==reg['new_executed_source_sha256']
    I=r['operating_current_A']
    cm=r['Cu_form_tab_electrothermal_result']
    copper_faces={};copper_stage=[0.,0.,0.];total_electrical=0.
    for k,net in cm['net_details'].items():
        faces=[int(i) for i in net['face_tags']]
        rhoR=np.asarray(net['metal_electrical_segment_R_ohm'])
        contactR=np.asarray(net['contact_electrical_R_ohm'])
        # Independently reconstruct endpoint Joule distribution, without
        # importing the forward ablation operator.
        q=I**2*contactR
        q[:-1]+=.5*I**2*rhoR
        q[1:]+=.5*I**2*rhoR
        assert len(q)==len(faces)
        assert max(abs(q-np.asarray(net['face_heat_into_ceramic_W'])))<1e-12
        assert abs(sum(q)-net['electric_Joule_W'])<1e-12
        assert all(q>=0) and all(x==0 for x in net['thermal_segment_conductance_W_K'])
        assert abs(sum(contactR)+sum(rhoR)-net['electric_resistance_ohm'])<1e-12
        if k=='88':assert contactR[1]==0.
        for f,h in zip(faces,q):
            copper_faces[f]=float(h);copper_stage[STAGES[f]]+=float(h)
        total_electrical+=I**2*(sum(contactR)+sum(rhoR))
    assert max(abs(copper_stage[i]-cm['heat_into_ceramic_by_stage_W'][i]) for i in range(3))<1e-12
    assert max(abs(copper_faces[f]-cm['heat_into_face_W'][str(f)]) for f in copper_faces)<1e-12
    assert abs(sum(copper_stage)-total_electrical)<1e-12
    assert abs(total_electrical-cm['total_electrical_power_W'])<1e-12
    assert abs(total_electrical-I**2*cm['total_electrical_R_ohm'])<1e-12

    # Rebuild original discretized gas loads from the saved 3D FEM nodal fields.
    fields=np.load(D/'ceramic_fields.npz')
    src=np.load(PRIOR/'coupled_attempt01/ceramic_fields.npz')
    T={}
    for j in range(4):
        ids=fields[f'ceramic{j}_source_node_id_1based']
        assert np.array_equal(ids,src[f'ceramic{j}_source_node_id_1based'])
        assert np.allclose(fields[f'ceramic{j}_xyz_mm'],
                           src[f'ceramic{j}_xyz_mm'],rtol=0,atol=1e-12)
        for i,t in zip(ids,fields[f'ceramic{j}_temperature_K']):
            T[int(i)]=float(t)
    patch=read(ROOT/'data/nominal_gas_p1_20261111/p1_operator.json')
    gas=exchange(patch['pairs'],T,100.,.8)
    ig=gas['stage_heat_hot_to_cold_W']
    assert np.max(np.abs(np.asarray(ig)-np.asarray(r['internal_interstage_gas_heat_hot_to_cold_W'])))<1e-8
    assert abs(sum(gas['node_load_W'].values()))<1e-12

    geo=read(PRIOR/'die_window_visibility.json')
    node=r['source_full_temperature_nodes_K']
    x=[node[k] for k in ('stage0_hot','stage0_cold','stage1_hot',
        'stage1_cold','stage2_hot','stage2_cold','carrier','die')]
    qwin=die_window_exchange(300.,x[-1],geo['paired_area_mm2'],
                             geo['gap_mm']*1e-3,100.,.8)['die_load_W']
    qgas=r['cavity_gas_heat_into_three_ceramics_and_die_W']
    assert all(z==0 for z in qgas[:3]) and abs(qgas[3]-qwin)<1e-12
    rad=np.asarray(r['gray_radiation_heat_into_three_ceramics_and_die_W'])

    legs=r['source_individual_leg_flux_and_electric_results']
    stages=[];leg_err=[]
    for j,n in enumerate((58,22,8)):
        selected=[z for z in legs if z['stage']==j]
        assert len(selected)==n
        H=sum(z['Qhot_W'] for z in selected)
        C=sum(z['Qcold_W'] for z in selected)
        V=sum(z['terminal_contribution_V'] for z in selected)
        assert max(abs(H-r['source_stage_thermoelectric_budget'][j]['qh_w']),
                   abs(C-r['source_stage_thermoelectric_budget'][j]['qc_w']),
                   abs(V-r['source_stage_thermoelectric_budget'][j]['voltage_v']))<1e-10
        for z in selected:
            leg_err.append(z['Qhot_W']-z['Qcold_W']-I*z['terminal_contribution_V'])
        stages.append(dict(h=H,c=C,v=V))
    assert max(map(abs,leg_err))<1e-9
    lead=r['source_tec_power_leads']
    joint=I**2*r['one_joint_series_resistance_ohm']
    AuG=sum(q['G_W_K'] for q in wire_geometry(read(ORIGINAL))
            if q['name'].startswith('detector_bond'))
    Qa=(x[7]-x[6])/geometry()['die_attach_thickness_over_area_m_inverse']
    bath=r['bath_heat_rejected_W'];power=I*r['terminal_voltage_V']
    residual=[
      stages[0]['c']-stages[1]['h']-80*joint-rad[0]-copper_stage[1]-ig[0]+ig[1],
      stages[1]['c']-stages[2]['h']-30*joint-rad[1]-copper_stage[2]-ig[1]+ig[2],
      stages[2]['c']-Qa-8*joint-rad[2]-ig[2],
      Qa-(.002+AuG*(300.-x[7])+rad[3]+qwin),
      bath-(stages[0]['h']+lead['total_pad_heat_W']+58*joint+copper_stage[0]-ig[0])]
    global_err=power+.002+AuG*(300.-x[7])+sum(rad)+qwin+lead['conduction_into_ceramic_W']-.5*lead['joule_W']-bath
    # Separate terminal-voltage closure; electrical resistance/Joule retained.
    volt=sum(s['v'] for s in stages)+I*(lead['total_R_ohm']+
         r['source_total_solder_and_contact_series_resistance_ohm']+
         cm['total_electrical_R_ohm'])
    assert abs(volt-r['terminal_voltage_V'])<1e-10
    assert max(map(abs,residual))<1e-8
    assert abs(global_err)<1e-8
    assert abs(power-reg['matched_terminal_input_W'])<1e-8
    assert max(abs(float(z['total_flux_mismatch_W'])) for z in r['original_native_source_ceramic_pad_flux_by_face'])<5e-8
    assert r['max_last_spatial_temperature_update_K']<1e-6
    prior=read(PRIOR/'coupled_attempt01/result.json')
    delta=r['calculated_detector_temperature_K']-prior['calculated_detector_temperature_K']
    assert abs(delta-r['comparison_nominal_V327_delta_die_K'])<1e-10
    out=dict(status='PASS independent electrothermal conservation and isolated electrical-only Cu readback; NOT physical validation',
      new_result_sha256=digest(D/'result.json'),baseline_result_sha256=reg['baseline_result_sha256'],
      model='V3.27 partial cavity; other gas faces adiabatic',
      baseline_die_K=prior['calculated_detector_temperature_K'],
      ablation_die_K=r['calculated_detector_temperature_K'],
      nominal_minus_ablation_die_K=-delta,
      delta_ablation_minus_nominal_K=delta,
      baseline_copper_upper_W=prior['Cu_form_tab_heat_into_ceramic_by_stage_W'][2],
      ablation_copper_upper_W=copper_stage[2],
      copper_joule_W=total_electrical,
      independent_copper_face_heat_W={str(k):v for k,v in copper_faces.items()},
      stage_residuals_W=residual,max_stage_residual_W=max(map(abs,residual)),
      global_residual_W=global_err,terminal_voltage_residual_V=volt-r['terminal_voltage_V'],
      power_residual_W=power-reg['matched_terminal_input_W'],
      max_leg_residual_W=max(map(abs,leg_err)),
      source_gas_sum_W=sum(gas['node_load_W'].values()),
      original_native_metal_gate='FAIL/STOP; 3D metal not solved',
      publication_caution='Copper thermal-off diagnostic is nonphysical; no measured validation, partial gas only')
    assert not (D/'independent_audit.json').exists()
    (D/'independent_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
