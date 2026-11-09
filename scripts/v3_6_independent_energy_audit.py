"""Independent no-PDE verification of V3.6 TEC operating-current and detector-load cases.

Does not import the V3.5 model, the V3.4 copper network, or original FEM.
Uses saved source geometry, registered laws, stage balances and local face temperatures.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_6_operating_envelope_20261109'
CAD=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
FACES=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
V34=ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(case):
    folder=DATA/case
    reg=json.loads((folder/'registration.json').read_text())
    d=json.loads((folder/'result.json').read_text())
    assert d['status'].startswith('V3.6 CONDITIONAL')
    assert sha(V34)=='2aa84432098907c3ac37d276fa3b430652ac77ce53a5fbac1174828b9e5d63bb'
    assert len(d['source_individual_leg_flux_and_electric_results'])==88
    assert d['original_ceramic_TET4']==11791
    I=float(reg['current_A'])
    raw=json.loads(CAD.read_text())
    body={z['name']:z for z in raw['bodies']}
    f=json.loads(FACES.read_text())['faces']
    scenario=reg['lead_alloy_scenario']
    mat=reg['lead_alloy_selected_properties'][scenario]
    Lfac=reg['lead_internal_path_length_factor']
    led=d['source_tec_power_leads']
    qlead=0.;qcond=0.;jlead=0.;rlead=0.
    distinct={}
    for pin,tag in ((1,8),(9,36)):
        name=f'TEC_lead{pin}';b=body[name]
        assert f[str(tag)]['owners'][0]=='ceramic0'
        area=np.pi*(b['radius']*.001)**2
        L=sum(x['length'] for x in b['parts'])*.001*Lfac
        R=mat['rho_ohm_m']*L/area;G=mat['k_W_mK']*area/L
        z=led['per_lead'][name];T=z['temperature_pad_K']
        Q=G*(reg['ambient_K']-T);J=I*I*R;pad=Q+.5*J
        assert abs(pad-z['heat_into_tec_pad_W'])<1e-13
        assert abs(z['R_ohm']-R)<1e-13
        assert abs(z['thermal_G_W_K']-G)<1e-13
        assert abs(float(led['face_heats_W'][str(tag)])-pad)<1e-13
        qlead+=pad;qcond+=Q;jlead+=J;rlead+=R
        distinct[str(pin)]={'face_tag':tag,'pad_T_K':T,'electrical_R_ohm':R,'Q_into_ceramic_W':pad}
    assert abs(qlead-d['heat_Cu_lead_correction_W'])<1e-12
    assert abs(rlead-led['total_R_ohm'])<1e-13
    assert abs(jlead-led['joule_W'])<1e-13
    Cu=d['Cu_form_tab_electrothermal_result']
    rt=reg['Cu_port_thermal_Rarea_m2K_W'];re=reg['Cu_port_electrical_Rarea_ohm_m2']
    stage={0:0.,1:0.,2:0.};rbridge=0.;qcopper=0.; detail={}
    for net in ('58','80','88'):
        s=reg['source_Cu_cad'][net];v=Cu['net_details'][net]
        tags=s['faces'];assert tags==v['face_tags']
        T=np.array(v['plate_temperature_K'],float)
        L=np.array(s['segments_m'],float)
        A=s['cross_section_m2']
        C=np.array(s['contact_area_m2'],float)
        rho=1.724e-8*(1+.0039*(.5*(T[1:]+T[:-1])-293.15))
        R=rho*L/A;G=385.*A/L
        Joule=I**2*R;node=np.zeros(len(T))
        node[:-1]+=.5*Joule;node[1:]+=.5*Joule
        gc=C/rt
        M=np.diag(gc)
        for j,g in enumerate(G):
            M[j,j]+=g;M[j+1,j+1]+=g
            M[j,j+1]-=g;M[j+1,j]-=g
        u=np.linalg.solve(M,gc*T+node)
        q=gc*(u-T)+I*I*re/C
        assert np.max(abs(q-np.array(v['face_heat_into_ceramic_W'])))<5e-13
        Rtot=float(R.sum()+(re/C).sum())
        assert abs(q.sum()-I*I*Rtot)<1e-11
        assert abs(Rtot-v['electric_resistance_ohm'])<1e-12
        qcopper+=sum(q);rbridge+=Rtot
        for face,heat in zip(tags,q):
            level=0 if face in (36,38) else 1 if face in (74,75,79) else 2
            stage[level]+=float(heat)
        detail[net]={'Cu_Joule_W':I*I*Rtot,'heat_into_source_faces_W':{str(t):float(y) for t,y in zip(tags,q)}}
    assert max(abs(stage[i]-d['Cu_form_tab_heat_into_ceramic_by_stage_W'][i]) for i in range(3))<1e-12
    Pjoint=d['source_solder_and_interface_energy_per_single_joint_pad_W']
    st=d['source_stage_thermoelectric_budget']
    gas=d['cavity_gas_heat_into_three_ceramics_and_die_W'];rad=d['gray_radiation_heat_into_three_ceramics_and_die_W']
    residual={
      'hot_sink_W':st[0]['qh_w']+qlead+58*Pjoint+stage[0]-d['bath_heat_rejected_W'],
      'middle0_W':st[0]['qc_w']-st[1]['qh_w']-80*Pjoint-gas[0]-rad[0]-stage[1],
      'middle1_W':st[1]['qc_w']-st[2]['qh_w']-30*Pjoint-gas[1]-rad[1]-stage[2],
      'detector_ceramic_W':st[2]['qc_w']-d['detector_bond_heat_and_bias_W']-8*Pjoint-gas[2]-rad[2]}
    maxres=max(abs(x) for x in residual.values())
    assert maxres<reg['inner_balance_tolerance_W'],residual
    assert d['max_last_spatial_temperature_update_K']<reg['outer_thermal_field_tolerance_K']
    assert d['max_native_plate_net_heat_imbalance_W']<reg['local_plate_net_heat_tolerance_W']
    Rjoint=d['source_total_solder_and_contact_series_resistance_ohm']
    V=sum(x['voltage_v'] for x in st)+I*(rlead+Rjoint+rbridge)
    assert abs(V-d['terminal_voltage_V'])<1e-11
    assert abs(I*V-d['electrical_power_W'])<1e-11
    Tdie=d['source_full_temperature_nodes_K']['die']
    # Directly reconstruct Au wire load from the V3.4 frozen Au paths, which remain unchanged in V3.5.
    base=json.loads(V34.read_text())
    # Use the preserved original Au conductance from the CAD geometry (two identical bonds).
    au=[body[f'detector_bond{i}'] for i in (7,8)]
    Gau=sum(315*np.pi*(x['radius']*.001)**2/(sum(z['length'] for z in x['parts'])*.001) for x in au)
    Au=Gau*(reg['ambient_K']-Tdie)
    energy=I*V+reg['detector_heat_W']+Au+sum(gas)+sum(rad)+qcond-.5*jlead-d['bath_heat_rejected_W']
    assert abs(energy)<reg['global_energy_tolerance_W'],energy
    result={'verdict':'PASS V3.6 independent saved-source lead/pad/multiport/stage/global energy reconstruction; NO nonlinear PDE/transport rerun',
        'scenario':case,'result_sha256':sha(folder/'result.json'),'registration_sha256':sha(folder/'registration.json'),
        'lead_source_native_faces':distinct,'Cu_source_networks':detail,
        'independently_reconstructed_stage_heat_W':{str(k):v for k,v in stage.items()},
        'independently_reconstructed_stage_energy_residual_W':residual,
        'max_stage_energy_residual_W':maxres,'global_energy_residual_W':energy,
        'copper_heat_minus_Joule_W':qcopper-I*I*rbridge,
        'lead_ceramic_heat_minus_conduction_and_half_Joule_W':qlead-qcond-.5*jlead,
        'detector_T_K':d['calculated_detector_temperature_K'],
        'detector_imposed_heat_W':reg['detector_heat_W'],'current_A':I,
        'terminal_V':d['terminal_voltage_V'],
        'lead_material':scenario,'Cu_contact_Rth_m2K_W':rt,
        'limitations':'Cu thermal/electrical 1D proxy, leads metal constant k/rho; no actual certification or full source 430-domain 3D field.'}
    p=folder/'independent_energy_audit.json'
    if p.exists():assert json.loads(p.read_text())==result
    else:p.write_text(json.dumps(result,indent=2)+'\n')
    print(case, result['verdict'],'Tdie',result['detector_T_K'],
          'global W',energy,'max stage W',maxres)
if __name__=='__main__':
    for item in sys.argv[1:]:audit(item)
