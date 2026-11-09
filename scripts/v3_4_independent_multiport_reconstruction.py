"""Independent no-solve numerical reconstruction of V3.4 from archived inputs.
No imports of V3.4 copper, axial TEC or FEM solver modules.
Evaluates the physical circuit algebra separately, not a source-code replay.
"""
from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'data/v3_4_copper_multiport_20261108/attempt03'
BASE=ROOT/'data/v3_3_cavity_package_feedback_20261108/attempt02/result.json'
FILE=DIR/'result.json'
REG=DIR/'registration.json'
NETS={58:(38,75),80:(79,105),88:(36,74,104)}
STAGE={38:0,75:1,79:1,105:2,36:0,74:1,104:2}
def independent_reconstruct():
    d=json.loads(FILE.read_text());reg=json.loads(REG.read_text())
    I=reg['current_A'];k=385.;rho=1.724e-8;alpha=.0039
    Re=reg['Cu_port_electrical_Rarea_ohm_m2']
    Rt=reg['Cu_port_thermal_Rarea_m2K_W']
    source=reg['source_Cu_cad']
    saved=d['Cu_form_tab_electrothermal_result']
    qbyface={};circuit={}
    for n,tags in NETS.items():
        s=source[str(n)]
        q=saved['net_details'][str(n)]
        t=np.array(q['plate_temperature_K'],dtype=float)
        L=np.array(s['segments_m'],dtype=float)
        A=float(s['cross_section_m2'])
        area=np.array(s['contact_area_m2'],dtype=float)
        assert tuple(s['faces'])==tags and len(L)==len(tags)-1
        R=((rho*(1+alpha*(.5*(t[:-1]+t[1:])-293.15)))*L/A)
        G=k*A/L
        Rc=Re/area
        J=I*I*R
        sourceJ=np.zeros(len(tags),dtype=float)
        sourceJ[:-1]+=.5*J
        sourceJ[1:]+=.5*J
        if Rt>0:
            contact=area/Rt
            M=np.diag(contact)
            for i,g in enumerate(G):
                M[i,i]+=g;M[i+1,i+1]+=g
                M[i,i+1]-=g;M[i+1,i]-=g
            foilT=np.linalg.solve(M,contact*t+sourceJ)
            qin=contact*(foilT-t)+I*I*Rc
        else:
            foilT=t.copy()
            qin=sourceJ+I*I*Rc
            for i,g in enumerate(G):
                qin[i]-=g*(t[i]-t[i+1])
                qin[i+1]+=g*(t[i]-t[i+1])
        check=np.array(q['face_heat_into_ceramic_W'])
        assert np.max(np.abs(qin-check))<5e-13,(n,qin,check)
        assert np.max(np.abs(foilT-np.array(q['foil_node_temperature_K'])))<1e-9
        assert abs(R.sum()+Rc.sum()-q['electric_resistance_ohm'])<1e-13
        assert abs(sum(qin)-I*I*(R.sum()+Rc.sum()))<1e-12
        circuit[str(n)]={'thermal_flux_into_faces_W':{str(z):float(x) for z,x in zip(tags,qin)},
                         'electrical_resistance_ohm':float(R.sum()+Rc.sum()),
                         'electrical_Joule_W':float(I*I*(R.sum()+Rc.sum())),
                         'thermal_interface_R_area_m2K_W':Rt}
        qbyface.update({z:float(x) for z,x in zip(tags,qin)})
    stageQ=[sum(v for t,v in qbyface.items() if STAGE[t]==i) for i in range(3)]
    assert max(abs(a-b) for a,b in zip(stageQ,d['Cu_form_tab_heat_into_ceramic_by_stage_W']))<1e-12
    st=d['source_stage_thermoelectric_budget']
    Pjoint=d['source_solder_and_interface_energy_per_single_joint_pad_W']
    gas=d['cavity_gas_heat_into_three_ceramics_and_die_W']
    rad=d['gray_radiation_heat_into_three_ceramics_and_die_W']
    residuals={
       'interstage0_W':st[0]['qc_w']-st[1]['qh_w']-(58+22)*Pjoint-gas[0]-rad[0]-stageQ[1],
       'interstage1_W':st[1]['qc_w']-st[2]['qh_w']-(22+8)*Pjoint-gas[1]-rad[1]-stageQ[2],
       'top_W':st[2]['qc_w']-d['detector_bond_heat_and_bias_W']-8*Pjoint-gas[2]-rad[2],
       'reservoir_W':st[0]['qh_w']+d['heat_Cu_lead_correction_W']+58*Pjoint+stageQ[0]-d['bath_heat_rejected_W']}
    assert max(abs(z) for z in residuals.values())<1e-8
    assert abs(sum(stageQ)-I*I*sum(x['electrical_resistance_ohm'] for x in circuit.values()))<1e-12
    report={'status':'PASS separate algebraic Cu multiport reconstruction without V3.4 solver imports; no PDE run',
        'archived_result_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),
        'original_V3_3_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),
        'registered_input_sha256':hashlib.sha256(REG.read_bytes()).hexdigest(),
        'independent_net_budget':circuit,'net_heat_into_ceramic_stage_W':stageQ,
        'stage_heat_residual_W':residuals,
        'maximum_absolute_stage_residual_W':max(abs(x) for x in residuals.values()),
        'Cu_net_electrical_Joule_W':I*I*sum(x['electrical_resistance_ohm'] for x in circuit.values())}
    target=DIR/'independent_physics_reconstruction.json'
    if target.exists():
        assert json.loads(target.read_text())==report,'SEPARATE_PHYSICS_REPLAY_MISMATCH'
    else:
        target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='independent_net_budget'},indent=2))
if __name__=='__main__':independent_reconstruct()
