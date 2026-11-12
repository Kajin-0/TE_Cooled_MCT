"""Read-only independent audit of every registered copper sensitivity case.

No forward-solve calls. Independently reconstructs source-geometry Cu KCL and
I^2R, 88 TE-leg energy, P1 gas source exchange, gas/window, stage/sink/global
closure and matched-power constraint. Numerical verification != validation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from tecooledmct.nominal_gas_p1_v325 import exchange
from tecooledmct.nominal_gas_visibility_v327 import die_window_exchange
from tecooledmct.height_coupling_v320 import copper_specs, wire_geometry, ORIGINAL, read
from scripts.v3_r3_sink_wire_sensitivity import geometry
from scripts.v3_4_source_copper_multiport import STAGES as CU_STAGES

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/copper_sensitivity_publication_20261112'
PRIOR=ROOT/'data/nominal_gas_visibility_v327_20261111'
POWER=0.5956680349614825
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(x,y,tol=1e-11):
    assert abs(float(x)-float(y))<tol,(x,y,tol)
def main(case):
    assert case in ('k80','k120','contact0p1x','contact10x','foil80','foil120')
    C=D/case
    assert C.is_dir() and not (C/'independent_audit.json').exists()
    reg=read(C/'registration.json')
    r=read(C/'result.json')
    assert reg['scenario']==r['study_case']==case
    assert sha(PRIOR/'coupled_attempt01/result.json')==reg['baseline_result_sha256']
    assert sha(PRIOR/'coupled_attempt01/independent_audit.json')==reg['baseline_audit_sha256']
    assert sha(C/'executed_solver.py.source')==reg['source_sha256']==r['solver_source_sha256']
    assert sha(ROOT/'scripts/tec_copper_publication_sensitivity_20261112.py')==reg['wrapper_sha256']
    p=reg['sensitivity_hypothesis'];I=float(r['operating_current_A'])
    assert 0.25<I<.55
    assert r['variant']=='nominal' and r['Cu_net88_middle_electrical_contact'].startswith('removed')
    close(r['effective_foil_thickness_um'],30*p['cross_section_multiplier'],1e-12)
    close(r['effective_Cu_k_W_mK'],385*p['k_multiplier'],1e-12)

    # Reconstruct Cu thermal-port equations and electrical J from original CAD.
    specs=copper_specs(read(ORIGINAL))
    full=r['Cu_form_tab_electrothermal_result']
    copper_faces={};stages=[0.,0.,0.]
    copper_power=0.;copper_resistance=0.;max_copper_KCL=0.
    for net,original in specs.items():
        d=full['net_details'][str(net)]
        tags=list(original['faces'])
        assert tags==d['face_tags']
        area=original['cross_section_m2']*p['cross_section_multiplier']
        length=np.array(original['segments_m'],float)
        contact_area=np.array(original['contact_area_m2'],float)
        plate=np.array(d['plate_temperature_K'],float)
        foil=np.array(d['foil_node_temperature_K'],float)
        Rseg=(1.724e-8*(1+.0039*(.5*(plate[:-1]+plate[1:])-293.15)))*length/area
        Re=1e-11/contact_area
        if net==88:Re[1]=0.
        G=385*p['k_multiplier']*area/length
        Gc=contact_area/p['contact_Rarea']
        close(d['electric_resistance_ohm'],sum(Rseg)+sum(Re),1e-12)
        close(d['electric_Joule_W'],I**2*(sum(Rseg)+sum(Re)),1e-12)
        assert np.max(abs(Rseg-np.asarray(d['metal_electrical_segment_R_ohm'])))<1e-12
        assert np.max(abs(Re-np.asarray(d['contact_electrical_R_ohm'])))<1e-12
        assert np.max(abs(G-np.asarray(d['thermal_segment_conductance_W_K'])))<1e-12
        # Nodewise metal network conservation with distributed segment Joule.
        distributed=np.zeros(len(tags))
        distributed[:-1]+=.5*I**2*Rseg
        distributed[1:]+=.5*I**2*Rseg
        kcl=Gc*(foil-plate)-distributed
        for j,g in enumerate(G):
            kcl[j]+=g*(foil[j]-foil[j+1])
            kcl[j+1]+=g*(foil[j+1]-foil[j])
        max_copper_KCL=max(max_copper_KCL,float(np.max(abs(kcl))))
        q=Gc*(foil-plate)+I**2*Re
        assert np.max(abs(q-np.asarray(d['face_heat_into_ceramic_W'])))<1e-12
        close(sum(q),d['electric_Joule_W'],1e-12)
        for tag,heat in zip(tags,q):
            copper_faces[tag]=float(heat)
            stages[CU_STAGES[tag]]+=float(heat)
        copper_power+=I**2*(sum(Rseg)+sum(Re))
        copper_resistance+=sum(Rseg)+sum(Re)
    assert max_copper_KCL<1e-12
    assert max(abs(full['heat_into_face_W'][str(t)]-q) for t,q in copper_faces.items())<1e-12
    assert max(abs(full['heat_into_ceramic_by_stage_W'][j]-stages[j]) for j in range(3))<1e-12
    close(copper_power,full['total_electrical_power_W'],1e-12)
    close(copper_resistance,full['total_electrical_R_ohm'],1e-12)
    close(sum(stages),copper_power,1e-12)

    # The saved source P1 ceramic fields independently determine gas links.
    fields=np.load(C/'ceramic_fields.npz')
    base_fields=np.load(PRIOR/'coupled_attempt01/ceramic_fields.npz')
    T={}
    for j in range(4):
        ids=fields[f'ceramic{j}_source_node_id_1based']
        assert np.array_equal(ids,base_fields[f'ceramic{j}_source_node_id_1based'])
        assert np.allclose(fields[f'ceramic{j}_xyz_mm'],
                           base_fields[f'ceramic{j}_xyz_mm'],rtol=0,atol=1e-12)
        for i,t in zip(ids,fields[f'ceramic{j}_temperature_K']):
            T[int(i)]=float(t)
    patch=read(ROOT/'data/nominal_gas_p1_20261111/p1_operator.json')
    gas=exchange(patch['pairs'],T,100.,.8)
    ig=np.asarray(gas['stage_heat_hot_to_cold_W'])
    assert np.max(abs(ig-np.asarray(r['internal_interstage_gas_heat_hot_to_cold_W'])))<1e-8
    assert abs(sum(gas['node_load_W'].values()))<1e-12

    geo=read(PRIOR/'die_window_visibility.json')
    n=r['source_full_temperature_nodes_K']
    x=[n[k] for k in ('stage0_hot','stage0_cold','stage1_hot','stage1_cold',
                      'stage2_hot','stage2_cold','carrier','die')]
    qwin=die_window_exchange(300.,x[-1],geo['paired_area_mm2'],
                             geo['gap_mm']*1e-3,100.,.8)['die_load_W']
    qgas=r['cavity_gas_heat_into_three_ceramics_and_die_W']
    assert all(z==0 for z in qgas[:3])
    close(qgas[3],qwin,1e-12)
    rad=np.asarray(r['gray_radiation_heat_into_three_ceramics_and_die_W'])

    # Stage transport and die/sink balance independently from saved 88 legs.
    legs=r['source_individual_leg_flux_and_electric_results']
    stage=[];leg_error=[]
    for j,num in enumerate((58,22,8)):
        selected=[z for z in legs if z['stage']==j]
        assert len(selected)==num
        H=sum(z['Qhot_W'] for z in selected)
        Cc=sum(z['Qcold_W'] for z in selected)
        V=sum(z['terminal_contribution_V'] for z in selected)
        origin=r['source_stage_thermoelectric_budget'][j]
        assert max(abs(H-origin['qh_w']),abs(Cc-origin['qc_w']),abs(V-origin['voltage_v']))<1e-10
        for z in selected:
            leg_error.append(z['Qhot_W']-z['Qcold_W']-I*z['terminal_contribution_V'])
        stage.append({'h':H,'c':Cc,'v':V})
    assert max(map(abs,leg_error))<1e-9

    lead=r['source_tec_power_leads']
    joint=I**2*r['one_joint_series_resistance_ohm']
    GAu=sum(z['G_W_K'] for z in wire_geometry(read(ORIGINAL))
            if z['name'].startswith('detector_bond'))
    Qa=(x[7]-x[6])/geometry()['die_attach_thickness_over_area_m_inverse']
    bath=r['bath_heat_rejected_W']
    power=I*r['terminal_voltage_V']
    residual=[
      stage[0]['c']-stage[1]['h']-80*joint-rad[0]-stages[1]-ig[0]+ig[1],
      stage[1]['c']-stage[2]['h']-30*joint-rad[1]-stages[2]-ig[1]+ig[2],
      stage[2]['c']-Qa-8*joint-rad[2]-ig[2],
      Qa-(.002+GAu*(300.-x[7])+rad[3]+qwin),
      bath-(stage[0]['h']+lead['total_pad_heat_W']+58*joint+stages[0]-ig[0])
    ]
    global_error=power+.002+GAu*(300.-x[7])+sum(rad)+qwin+lead['conduction_into_ceramic_W']-.5*lead['joule_W']-bath
    voltage=sum(z['v'] for z in stage)+I*(lead['total_R_ohm']+
                r['source_total_solder_and_contact_series_resistance_ohm']+
                copper_resistance)
    close(voltage,r['terminal_voltage_V'],1e-10)
    assert max(abs(z) for z in residual)<1e-8
    assert abs(global_error)<1e-8
    assert abs(power-POWER)<1e-8
    assert max(abs(float(z['total_flux_mismatch_W']))
               for z in r['original_native_source_ceramic_pad_flux_by_face'])<5e-8
    assert r['max_last_spatial_temperature_update_K']<1e-6

    baseline=read(PRIOR/'coupled_attempt01/result.json')
    out={
      'status':'PASS numerical conservation and source Cu electrothermal KCL independently reconstructed; no hardware validation',
      'case':case,'case_params':p,'result_sha256':sha(C/'result.json'),
      'baseline_result_sha256':reg['baseline_result_sha256'],
      'source_sha256':reg['source_sha256'],
      'die_temperature_K':x[7],
      'baseline_die_temperature_K':baseline['calculated_detector_temperature_K'],
      'case_minus_baseline_die_K':x[7]-baseline['calculated_detector_temperature_K'],
      'net_copper_stage_heats_W':stages,
      'copper_joule_W':copper_power,
      'copper_max_nodal_KCL_W':max_copper_KCL,
      'max_stage_residual_W':max(map(abs,residual)),
      'global_energy_residual_W':global_error,
      'max_leg_residual_W':max(map(abs,leg_error)),
      'terminal_voltage_residual_V':voltage-r['terminal_voltage_V'],
      'matched_power_residual_W':power-POWER,
      'gas_exchange_sum_W':sum(gas['node_load_W'].values()),
      'Cu_net88_middle_contact_electrical':'excluded',
      'model_scope':'Original-only V3.27 partial cavity, unmeasured contacts and research P/N laws; full metal electrical Gate B FAIL/STOP',
      'statistical_scope':'Not a confidence interval or empirical uncertainty'
    }
    (C/'independent_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print('INDEPENDENT_AUDIT_PASS',case,'T_K',x[7], 'dT_K',out['case_minus_baseline_die_K'],
          'max_stage_W',out['max_stage_residual_W'],'Cu_KCL_W',max_copper_KCL,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',required=True)
    main(parser.parse_args().case)
