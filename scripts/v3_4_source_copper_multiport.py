"""V3.4 source-CAD interstage conductor multiport (provisional engineering law).
Couples actual face tags at 3 distinct ceramic stage top surfaces.
No geometry changes, no claims of calibrated metal/contact properties.
"""
from pathlib import Path
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
FACES=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
TABS=ROOT/'data/synthetic_v3_assembly_20261102/conductor_geometry_coefficients.json'
PORTS={58:(38,75),80:(79,105),88:(36,74,104)}
STAGES={38:0,75:1,79:1,105:2,36:0,74:1,104:2}
ENDPOINTS={58:(0,1),80:(1,2),88:(0,1,2)}
K_CU_W_MK=385.0
RHO_CU_293_OHM_M=1.724e-8
CU_RHO_ALPHA_K_INV=0.0039
# Neither the selected solder thermal impedance nor Cu material lot is characterized.
THERMAL_CONTACT_R_AREA_M2K_W=1e-6
ELECTRICAL_CONTACT_R_AREA_OHM_M2=1e-11

def specs():
    D=json.loads(DESIGN.read_text())
    F=json.loads(FACES.read_text())['faces']
    C={int(v['net']):v for v in json.loads(TABS.read_text())}
    bodies={b['name']:b for b in D['bodies']}
    out={}
    for net,tags in PORTS.items():
        body=bodies[f'formed_tab{net}']
        links=tuple(f'tab_joint{i}' for i in ({58:(0,1),80:(2,3),88:(4,5,6)}[net]))
        feet=[bodies[x] for x in links]
        for tag,stage in zip(tags,ENDPOINTS[net]):
            f=F[str(tag)]
            assert f['class_']=='SOLID_SOLID'
            assert f['owners'][0]==f'ceramic{stage}'
            assert f['owners'][1]==f'net{net}_plane{(0.5,1.6,2.7)[stage]:.3f}_Cu'
        assert body['shape']=='tab' and body['material']=='Cu'
        assert abs(body['thickness']*body['width']*1e-6-C[net]['cross_section_m2'])<1e-20
        lengths=[float(z['length'])*1e-3 for z in body['parts']]
        foot_center=[(b['bbox_mm'][1]+b['bbox_mm'][4])/2 for b in feet]
        # The physical contact centers sit 0.150 mm inboard from both
        # source foil free ends. A source full-tab end-to-end path would
        # overestimate resistive length between contacted ceramic pads.
        initial=abs(body['parts'][0]['a'][0]-foot_center[0])*1e-3
        final=abs(body['parts'][-1]['b'][0]-foot_center[-1])*1e-3
        if net!=88:
            L=[sum(lengths)-initial-final]
        else:
            midseg=4
            # Middle joint center divides the 0.55 mm intermediate
            # horizontal foot/landing: source y of foot center = 2.30mm.
            midpoint=(body['parts'][midseg]['a'][0]-foot_center[1])*1e-3
            L1=sum(lengths[:midseg])+midpoint-initial
            L=[L1,sum(lengths)-initial-final-L1]
        assert all(l>0 for l in L)
        A=body['thickness']*body['width']*1e-6
        Ac=np.array([(b['bbox_mm'][3]-b['bbox_mm'][0])*
            (b['bbox_mm'][4]-b['bbox_mm'][1])*1e-6 for b in feet])
        assert np.max(abs(Ac-0.06e-6))<1e-17
        out[net]={'net':net,'faces':tags,'stage':ENDPOINTS[net],
            'source_centerline_total_length_m':sum(lengths),
            'contact_centre_span_m':sum(L),'segments_m':tuple(L),
            'cross_section_m2':A,'contact_area_m2':Ac.tolist(),
            'joining_source_solids':links}
        assert sum(L)<C[net]['neutral_path_length_m']
        assert abs(sum(lengths)-C[net]['neutral_path_length_m'])<1e-14
    return out

SPEC=specs()

def copper_rho(T):
    # Selected linear temperature-dependence; only use in 180--390K.
    assert np.all((np.asarray(T)>180)&(np.asarray(T)<390))
    return RHO_CU_293_OHM_M*(1+CU_RHO_ALPHA_K_INV*(np.asarray(T)-293.15))

def evaluate(current_A,plate_T_by_face,thermal_area_resistance=THERMAL_CONTACT_R_AREA_M2K_W,
             electrical_area_resistance=ELECTRICAL_CONTACT_R_AREA_OHM_M2):
    assert current_A>=0
    assert thermal_area_resistance>=0 and electrical_area_resistance>=0
    loads={int(z):0. for tags in PORTS.values() for z in tags}
    detail={}
    for net,s in SPEC.items():
        tags=s['faces'];p=np.array([plate_T_by_face[z] for z in tags])
        assert len(p)==len(s['contact_area_m2'])
        A=s['cross_section_m2'];L=np.array(s['segments_m'])
        G=K_CU_W_MK*A/L
        # Wire J heating is deposited half to each adjacent wire node.
        # Contacts deposit electrical heat at the ceramic face (declared approximation).
        Rseg=copper_rho((p[1:]+p[:-1])/2)*L/A
        pc= current_A**2*electrical_area_resistance/np.asarray(s['contact_area_m2'])
        pj=current_A**2*Rseg
        source=np.zeros(len(tags))
        source[:-1]+=.5*pj;source[1:]+=.5*pj
        if thermal_area_resistance:
            Gc=np.asarray(s['contact_area_m2'])/thermal_area_resistance
            M=np.diag(Gc)
            for j,g in enumerate(G):
                M[j,j]+=g;M[j+1,j+1]+=g
                M[j,j+1]-=g;M[j+1,j]-=g
            foilT=np.linalg.solve(M,Gc*p+source)
            q=Gc*(foilT-p)+pc
        else:
            foilT=p.copy()
            q=source+pc
            q[:-1]-=G*(p[:-1]-p[1:])
            q[1:]+=G*(p[:-1]-p[1:])
        resistance=sum(Rseg)+sum(electrical_area_resistance/np.asarray(s['contact_area_m2']))
        voltage=current_A*resistance
        joule=current_A*voltage
        assert abs(q.sum()-joule)<1e-11,('COPPER_ENERGY',net,q.sum(),joule)
        for tag,val in zip(tags,q):loads[tag]+=float(val)
        detail[str(net)]={'face_tags':list(tags),'plate_temperature_K':p.tolist(),
            'foil_node_temperature_K':foilT.tolist(),'thermal_segment_conductance_W_K':G.tolist(),
            'segment_length_m':L.tolist(),'metal_electrical_segment_R_ohm':Rseg.tolist(),
            'contact_electrical_R_ohm':(electrical_area_resistance/np.asarray(s['contact_area_m2'])).tolist(),
            'face_heat_into_ceramic_W':q.tolist(),'electric_resistance_ohm':float(resistance),
            'electric_Joule_W':float(joule),'electric_voltage_V':float(voltage)}
    qplates=[float(sum(q for t,q in loads.items() if STAGES[t]==stage)) for stage in range(3)]
    totalP=current_A*sum(q['electric_voltage_V'] for q in detail.values())
    assert abs(sum(qplates)-totalP)<1e-11
    return {'heat_into_face_W':loads,'net_details':detail,'heat_into_ceramic_by_stage_W':qplates,
        'total_electrical_power_W':totalP,'total_electrical_R_ohm':totalP/current_A**2 if current_A else 0.}
