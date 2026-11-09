"""Independent V3.8 TEC stage, HgCdTe Joule and external sink energy closure; no PDE re-run.

Does not import the V3.5 model, the V3.4 copper network, or original FEM.
Uses saved source geometry, registered laws, stage balances and local face temperatures.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_8_rev3_transport_and_sink_20261109'
CAD=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
FACES=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
V34=ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(case):
    folder=DATA/case
    reg=json.loads((folder/'registration.json').read_text())
    d=json.loads((folder/'result.json').read_text())
    assert d['status'].startswith('V3.8 CONDITIONAL')
    assert sha(V34)=='2aa84432098907c3ac37d276fa3b430652ac77ce53a5fbac1174828b9e5d63bb'
    assert len(d['source_individual_leg_flux_and_electric_results'])==88
    assert d['original_ceramic_TET4']==11791
    I=float(reg['current_A'])
    # Independently reconstruct the correct external sink thermal drop
    # from the native 3D ceramic mean drop and the calculated hot heat.
    source_Rext_K_W=json.loads((ROOT/'data/v2_integrated_spatial_20261107/attempt02/v2_integrated_result.json').read_text())['hot_external_R_without_ceramic0_K_W']
    added=reg['additional_external_mounting_sink_R_K_W']
    required=source_Rext_K_W+added
    assert abs(d['base_external_sink_R_K_W']-source_Rext_K_W)<1e-12
    assert abs(d['additional_external_sink_R_K_W']-added)<1e-12
    assert abs(d['total_external_sink_R_K_W']-required)<1e-12
    stage0=d['source_full_temperature_nodes_K']['stage0_hot']
    gap0=d['original_native_source_ceramic_pad_flux_by_face'][0]['top_minus_bottom_K']
    sink_delta=stage0-reg['ambient_K']-gap0-required*d['bath_heat_rejected_W']
    assert abs(sink_delta)<4e-7,('sink thermal closure K',sink_delta)
    factors=[float(v) for v in reg['P_N_scale_tuple']]
    assert factors==d['source_thermoelectric_scale_S_rho_k']
    assert sum(v!=1. for v in factors)<=1
    assert (added==0 or factors==[1.,1.,1.])
    assert len(d['source_individual_leg_flux_and_electric_results'])==88
    assert max(abs(z['energy_residual_W']) for z in d['source_individual_leg_flux_and_electric_results'])<1e-9

    # Completely independent algebraic reproduction of detector temperature-to-
    # resistance-to-bias heat. Avoid the forward solver's HgCdTe helper.
    import math
    Tdie=float(d['calculated_detector_temperature_K'])
    E=float(reg['effective_resistance_activation_eV'])
    T0=float(reg['reference_T_K'])
    R0=float(reg['reference_R_ohm'])
    Vdet=float(reg['detector_bias_V'])
    Popt=float(reg['absorbed_optical_W'])
    kB=8.617333262145e-5
    Rdet=R0*math.exp(E/kB*(1/Tdie-1/T0))
    Idet=Vdet/Rdet
    Pbias=Vdet*Idet
    dPdT=Pbias*E/(kB*Tdie*Tdie)
    Pdet=Pbias+Popt
    z=d['source_HgCdTe_electrothermal_at_T']
    assert abs(Rdet-z['dark_resistance_ohm'])<1e-9
    assert abs(Idet-z['detector_dark_current_A'])<1e-14
    assert abs(Pbias-z['detector_bias_Joule_W'])<1e-14
    assert abs(Popt-z['absorbed_optical_heat_W'])<1e-14
    assert abs(dPdT-z['d_bias_Joule_dT_W_K_at_constant_V'])<1e-14
    assert abs(Pdet-d['detector_imposed_heat_W'])<1e-14
    assert abs(Pdet-d['source_HgCdTe_bias_heat_W']-d['source_HgCdTe_optical_heat_W'])<1e-14

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
    # Use the preserved original Au conductance from the CAD geometry (two identical bonds).
    au=[body[f'detector_bond{i}'] for i in (7,8)]
    Gau=sum(315*np.pi*(x['radius']*.001)**2/(sum(z['length'] for z in x['parts'])*.001) for x in au)
    Au=Gau*(reg['ambient_K']-Tdie)
    energy=I*V+Pdet+Au+sum(gas)+sum(rad)+qcond-.5*jlead-d['bath_heat_rejected_W']
    assert abs(energy)<reg['global_energy_tolerance_W'],energy
    result={'verdict':'PASS V3.8 detector Joule, source copper/stage/global balance, mounted sink drop; NO nonlinear PDE rerun',
        'scenario':case,'result_sha256':sha(folder/'result.json'),'registration_sha256':sha(folder/'registration.json'),
        'source_transport_scales_S_rho_k':factors,'base_R_sink_K_W':source_Rext_K_W,'added_R_sink_K_W':added,'total_sink_R_K_W':required,'independent_sink_T_closure_K':sink_delta,
        'lead_source_native_faces':distinct,'Cu_source_networks':detail,
        'independently_reconstructed_stage_heat_W':{str(k):v for k,v in stage.items()},
        'independently_reconstructed_stage_energy_residual_W':residual,
        'max_stage_energy_residual_W':maxres,'global_energy_residual_W':energy,
        'copper_heat_minus_Joule_W':qcopper-I*I*rbridge,
        'lead_ceramic_heat_minus_conduction_and_half_Joule_W':qlead-qcond-.5*jlead,
        'detector_T_K':d['calculated_detector_temperature_K'],
        'detector_bias_V':Vdet,'detector_R_ohm':Rdet,'detector_I_A':Idet,'detector_bias_P_W':Pbias,'detector_absorbed_P_W':Popt,'detector_dPdT_W_K':dPdT,'detector_total_heat_W':Pdet,'current_A':I,
        'terminal_V':d['terminal_voltage_V'],
        'lead_material':scenario,'Cu_contact_Rth_m2K_W':rt,
        'limitations':'P/N source transport law scaled rather than independently recomputed; HgCdTe R(T) is unmeasured, sink is lumped; 3D ceramic FEM but not 430-domain metal PDE.'}
    p=folder/'independent_energy_audit.json'
    if p.exists():assert json.loads(p.read_text())==result
    else:p.write_text(json.dumps(result,indent=2)+'\n')
    print(case, result['verdict'],'Tdie',result['detector_T_K'],
          'global W',energy,'max stage W',maxres)
if __name__=='__main__':
    for item in sys.argv[1:]:audit(item)
