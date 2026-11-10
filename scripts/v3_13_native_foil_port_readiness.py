#!/usr/bin/env python3
"""V3.13 read-only source-net88 three-landing port and archived 3D gate audit.

Builds a complete conditional thermal port matrix at the ORIGINAL source
CAD face locations using the accepted reduced model, not a new 3D PDE.
Keeps historical 3D Gate B current-gradient FAIL and distinguishes weak
contact-reaction flux from independent one-sided field gradients.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.v3_4_source_copper_multiport import SPEC,evaluate
OUT=ROOT/'data/v3_13_native_foil_port_readiness_20261109'
SAVED=ROOT/'data/v3_5_power_lead_and_copper_sensitivity_20261108/copper_native_pad/result.json'
A=ROOT/'data/v3_interconnect_et_20261102/B/gate_B.json'
B=ROOT/'data/v3_gate_B_original_P2_20261106/attempt01/P2_coupon_result.json'
C=ROOT/'data/v3_interconnect_et_20261102/B/fine_mesh/mesh.npz'
D=ROOT/'data/v3_interconnect_et_20261102/B/fine_mesh/registry.json'
DES=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    d=json.loads(SAVED.read_text());p1=json.loads(A.read_text());p2=json.loads(B.read_text());registry=json.loads(D.read_text());design=json.loads(DES.read_text())
    byname={b['name']:b for b in design['bodies']}
    assert p1['status']=='FAIL/STOP' and p2['status'].startswith('STOP')
    assert p2['P2_raw_cut_max_relative_error']>0.001
    mid=next(x for x in p2['P2_cuts'] if x.get('pair')==['tab88','joint5'])
    assert mid['expected_fraction']==0
    assert byname['tab_joint5']['material']=='SnBi57_43'
    assert all(byname[f'tab_joint{i}']['material']=='SnBi57_43' for i in range(7))
    source=d['Cu_form_tab_electrothermal_result']['net_details']
    ports={int(k):float(v) for net in source.values() for k,v in zip(net['face_tags'],net['plate_temperature_K'])}
    assert len(ports)==7
    base=evaluate(.4,ports)
    assert abs(base['total_electrical_power_W']-d['Cu_form_tab_electrothermal_result']['total_electrical_power_W'])<1e-12
    tags=(36,74,104)
    assert tuple(SPEC[88]['faces'])==tags
    assert np.allclose([ports[t] for t in tags],source['88']['plate_temperature_K'],atol=1e-12)
    # Exact reduced-operator 3-port reconstruction by unit temperature columns:
    # G positive with port heat INTO the foil (the reverse of heat into ceramic).
    K=np.zeros((3,3))
    for j in range(3):
        inp={t:300.0 for t in ports}
        inp[tags[j]]=301.0
        raw=evaluate(0,inp)['heat_into_face_W']
        K[:,j]=[-raw[t] for t in tags]
    assert max(abs(K.sum(axis=0)))<1e-12
    assert max(abs(K.sum(axis=1)))<1e-12
    assert np.max(abs(K-K.T))<1e-12
    eig=np.linalg.eigvalsh(K)
    assert eig[0]>-1e-12 and eig[1]>0 and eig[2]>0
    T=np.asarray([ports[t] for t in tags]);q0=-K@T
    q4=np.asarray([base['heat_into_face_W'][t] for t in tags]);pj=q4-q0
    assert abs(sum(pj)-source['88']['electric_Joule_W'])<1e-11
    assert np.max(abs(q4-np.asarray(source['88']['face_heat_into_ceramic_W'])))<1e-11
    # Present physical source: tab88/joint5 contact is a *thermal* port but
    # the original 3D electrical coupon registered it as a dead-end branch.
    # No current normal to joint5 => no I²*r contact heating at that foot.
    r_mid=float(source['88']['contact_electrical_R_ohm'][1])
    e_at_04=.4**2*r_mid
    assert abs(r_mid-1e-11/6e-8)<1e-12
    assert abs(e_at_04-0.0000266666666666667)<1e-12
    # No fully re-coupled T/V can be obtained just by subtracting these terms.
    mesh=np.load(C)
    assert mesh['cells'].shape==(28691,4)
    assert len(registry['groups'])==12
    assert len(p2['P2_cuts'])==16
    status={
     'title':'V3.13 source-net88 local 3D coupon readiness / reduced multiport audit',
     'interpretation':'SOURCE-GROUNDED REDUCED THREE-PORT PASS; INDEPENDENT 3D ELECTRICAL B FAIL/STOP; THERMAL C/D NOT RUN',
     'new_FEM_solves':0,'original_3D_mesh_tetrahedra':28691,
     'old_coupon_material_regions':len(registry['groups']),
     'old_coupon_scope':'Actual net88 + lead9 12-region mesh, not full TEC or just bare copper',
     'foil_ports_CAD_tags':list(tags),
     'foil_ports_temperature_K':T.tolist(),
     'thermal_G_positive_heat_into_foil_W_K':K.tolist(),
     'thermal_G_eigenvalues_W_K':eig.tolist(),
     'heat_into_ceramic_at_I0_W':q0.tolist(),
     'heat_into_ceramic_at_I040_W':q4.tolist(),
     'Joule_port_allocation_current_reduced_W':pj.tolist(),
     'net88_copper_and_contacts_Joule_current_model_W':float(source['88']['electric_Joule_W']),
     'original_reduced_R_net88_ohm':float(source['88']['electric_resistance_ohm']),
     'electrical_dead_end_midfoot':{
        'CAD_foot':'tab_joint5','source_alloy':'SnBi57_43',
        'P2_expected_current_fraction':mid['expected_fraction'],
        'P2_weak_reaction_current_A_at_1V':mid['natural_A'],
        'middle_contact_series_R_mistaken_if_assumed_through_current_ohm':r_mid,
        'middle_contact_Joule_overcount_if_no_branch_current_at_0p4A_W':e_at_04,
        'potential_corrected_net88_contact_and_foil_R_ohm_if_no_mid_current':float(source['88']['electric_resistance_ohm']-r_mid),
        'status':'OPEN prospective electrical-interface mapping correction; no source-state mutation or T prediction'
     },
     '3D_electrical_gates':{
       'P1_original_gate':p1['status'],
       'P1_worst_raw_current_cut_relative':p1['worst_fine_cut_relative_error'],
       'P2_raw_current_cut_relative':p2['P2_raw_cut_max_relative_error'],
       'P2_raw_cuts_failed':p2['P2_raw_cuts_failing_count'],
       'cut_release_threshold_relative':p2['current_gate_limit'],
       'P2_voltage_min_V':p2['P2_minimum_voltage_V'],
       'P2_voltage_bound_tolerance_V':p2['voltage_bound_tolerance_V'],
       'P2_IV_minus_losses_rel':p2['P2_IV_minus_losses_relative'],
       'thermal_C_gate':'NOT RUN; B FAIL',
       'Joule_coupled_D_gate':'NOT RUN; B FAIL',
       'caveat':'Weak-form conservation and IV power agreement do not qualify raw one-sided 3D contact gradient fluxes.'},
     'boundary_contract_for_next_3D_attempt':{
        'source_mesh':'Use immutable original net88/lead9 CAD source; no stage terminal invention',
        'electric':'Actual P87 source cut to pin9 head cut; middle pad floating (no direct current port)',
        'thermal':'Original three ceramic underside ports C0/C1/C2 plus physical pin9 and PN87 thermal cuts, no fictitious ambient Dirichlet',
        'contact':'Distinct electronic and thermal finite-contact laws for Bi57Sn43 joints and multilayer metallization, not P/N Sn95Sb5',
        'port_sign':'Positive thermal Q is INTO coupon, PSD G; ceramic heat opposite sign',
        'acceptance':'Original 0.1% raw one-sided current cut error, bounded voltage, 0.5% energy, mesh resistance convergence; no relaxation',
        'sequential_gate':'Electrical B PASS required BEFORE new physical thermal C and coupled Joule D. No unlimited retries.'},
     'scientific_limitation':'The accepted 3x3 G is a reconstruction of the existing 1D/source-geometry multiport, NOT a spatial 3D thermal PDE or a validation of 3D spreading.',
     'source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in (SAVED,A,B,C,D,DES)}
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'port_readiness.json').write_text(json.dumps(status,indent=2)+'\n')
    print('G_MILLIWATTS_PER_K',np.around(K*1e3,9))
    print('PHYSICAL_JOINT',status['electrical_dead_end_midfoot'])
    print('OLD_B',status['3D_electrical_gates'])
    print('REPRO',OUT/'port_readiness.json')
if __name__=='__main__':main()
