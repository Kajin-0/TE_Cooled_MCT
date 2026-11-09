"""V3.5 source-derived separate TEC supply leads, finite lead segments.

Hardware reference: pin1 joins ceramic0 original face8 and pin9 joins
ceramic0 original face36. Factory-supplied excess length beyond the pin-side
solder is NOT modeled as extra cooler-to-header thermal resistance.
Source internal wire diameter and path are retained unchanged.
"""
from pathlib import Path
import json,math,hashlib
ROOT=Path(__file__).resolve().parents[1]
CAD=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
META=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
BOUNDARY_FACES={'TEC_lead1':8,'TEC_lead9':36}
JOIN_FACES={'TEC_lead1':2352,'TEC_lead9':2366}
PINS={'TEC_lead1':1,'TEC_lead9':9}
MODELS={
 'copper':{'k_W_mK':400.,'rho_ohm_m':1.72e-8,
           'meaning':'Frozen V3.4 source copper material proxy'},
 'nickel_proxy':{'k_W_mK':90.,'rho_ohm_m':7.0e-8,
           'meaning':'Selected near-room-temperature pure-Ni proxy; not lead vendor identity'},
 'fecral_screen':{'k_W_mK':11.,'rho_ohm_m':1.45e-6,
           'meaning':'Illustrative Kanthal A1-like FeCrAl; no claim this alloy solders/ships with TEC'}}
def src_sha():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (CAD,META)}
def original_leads():
    d=json.loads(CAD.read_text()); f=json.loads(META.read_text())['faces']
    b={z['name']:z for z in d['bodies']}
    out={}
    for name,face in BOUNDARY_FACES.items():
        w=b[name]
        assert w['material']=='Cu' and w['shape']=='wire'
        r=w['radius']*1e-3;L=sum(z['length'] for z in w['parts'])*1e-3
        area=math.pi*r*r
        assert abs(r-1e-4)<1e-15
        assert f[str(face)]['owners']==['ceramic0',f'net{0 if PINS[name]==1 else 88}_plane0.500_Cu']
        assert name in f[str(JOIN_FACES[name])]['owners']
        out[name]={'pin':PINS[name],'ceramic_face_tag':face,'source_radius_m':r,
           'source_internal_length_m':L,'area_m2':area,
           'source_land_join_face_tag':JOIN_FACES[name],
           'factory_supplied_extra_length':'NOT INSIDE SOURCE INTERNAL ASSEMBLY'}
    assert set(out)==set(PINS)
    return out
LEADS=original_leads()
SOURCE_SHA=src_sha()

def evaluate(face_temperatures_K,alloy='copper',internal_length_factor=1.0,
             current_A=0.4,header_temperature_K=300.):
    assert alloy in MODELS and 0.5<=internal_length_factor<=3.
    assert 0 <= current_A<=2
    p=MODELS[alloy];k=p['k_W_mK'];rho=p['rho_ohm_m']
    rows={};qface={};Qcond=0.;J=0.;R=0.;Qsource=0.
    for name,w in LEADS.items():
        tag=w['ceramic_face_tag'];Tc=float(face_temperatures_K[tag])
        L=w['source_internal_length_m']*internal_length_factor
        A=w['area_m2']
        G=k*A/L;Ri=rho*L/A
        cond=G*(header_temperature_K-Tc)
        joule=current_A**2*Ri
        # Uniform-wire central heating split 50% to each terminal.
        pad=cond+.5*joule
        rows[name]={'pin':w['pin'],'face':tag,'temperature_pad_K':Tc,
            'temperature_header_K':header_temperature_K,'length_m':L,
            'thermal_G_W_K':G,'R_ohm':Ri,'conduction_into_tec_W':cond,
            'joule_wire_W':joule,'heat_into_tec_pad_W':pad,
            'wire_heating_to_header_W':.5*joule}
        qface[tag]=pad
        R+=Ri;J+=joule;Qcond+=cond;Qsource+=pad
    assert abs(sum(qface.values())-Qcond-.5*J)<1e-13
    return {'alloy_scenario':alloy,'length_factor_from_internal_CAD':internal_length_factor,
        'face_heats_W':qface,'per_lead':rows,'total_R_ohm':R,'joule_W':J,
        'conduction_into_ceramic_W':Qcond,'total_pad_heat_W':Qsource,
        'source_SHA256':SOURCE_SHA}
