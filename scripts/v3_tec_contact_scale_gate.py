#!/usr/bin/env python3
"""Source-CAD 88-leg solder/interface electrical and thermal scale audit.

Source face/solid identities verified. All R_e and R_th contact values below
are illustrative older Gate-B hypotheses ONLY; no physical release, no
3D coupled FEM, no OEM identification, and no assumption that thermal
contact resistances form one series path for the entire module.
"""
import argparse,collections,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAD=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
BODY=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
OLD=ROOT/'data/v3_interconnect_et_20261102/operator_definitions.json'
PROFILE=ROOT/'data/tec_material_plausibility_20261101/properties.json'
PORT=ROOT/'data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json'
GATE=ROOT/'data/v3_tec_source_identity_20261107/attempt01/source_identity_gate.json'
FILES=(CAD,BODY,OLD,PROFILE,PORT,GATE)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def build():
 c=read(CAD);body=read(BODY);old=read(OLD);prof=read(PROFILE);port=read(PORT);ident=read(GATE)
 assert len(c['domains'])==430 and len(c['faces'])==2440
 assert port['source_leg_articulation_count']==88
 assert ident['as_built_module_identification']=='UNKNOWN'
 assert len(body['bodies'])==824
 dom={v['id']:v for v in c['domains'].values()}
 groups=collections.defaultdict(list)
 for tag,f in c['faces'].items():
  if f['class_']!='SOLID_SOLID':continue
  m=tuple(sorted(dom[i]['material'] for i in f['owner_volume_ids']))
  if 'SnSb' in m:groups[str(m)].append({'face_tag':int(tag),'area_mm2':f['face_area_mm2'],'owners':f['owners']})
 count=collections.Counter()
 for key,v in groups.items(): count[key]=len(v)
 assert sum(count.values())==352 and sorted(count.values())==[88,88,176]
 assert all(abs(x['area_mm2']-.16)<1e-10 for l in groups.values() for x in l)
 solder=[b for b in body['bodies'] if b['material']=='SnSb']
 assert len(solder)==176
 assert all(len(x['boxes_mm'])==1 for x in solder)
 assert all(all(abs(a-b)<1e-11 for a,b in zip(x['boxes_mm'][0][3:6],[.4,.4,.035])) for x in solder)
 leg=[b for b in body['bodies'] if b['material'] in ('P','N')]
 assert len(leg)==88
 assert all(all(abs(a-b)<1e-11 for a,b in zip(x['boxes_mm'][0][3:6],[.4,.4,.5])) for x in leg)
 A=.16e-6
 Ls=.035e-3
 Ll=.5e-3
 rho_s=old['material_constants']['SnSb'][0]
 k_s=old['material_constants']['SnSb'][1]
 assert rho_s==1.7e-7 and k_s==45.
 ip=prof['temperature_K'].index(300.)
 rho_p=prof['hypotheses']['nominal']['polarities']['P']['rho'][ip]
 rho_n=prof['hypotheses']['nominal']['polarities']['N']['rho'][ip]
 kp=prof['hypotheses']['nominal']['polarities']['P']['k'][ip]
 kn=prof['hypotheses']['nominal']['polarities']['N']['k'][ip]
 assert rho_p>0 and rho_n>0 and kp>0 and kn>0
 # Original 29/11/4 stages connect 44 P and 44 N legs in SERIES.
 R_leg=(44*rho_p+44*rho_n)*Ll/A
 R_solder=176*rho_s*Ls/A
 assert R_leg>2 and R_solder<.02
 # 352 separate native contact interfaces are in the single TE
 # electrical chain. All 352 could have identical resistivity only
 # in a disclosed hypothetical model, not actual physical interface.
 rows=[]
 for label,rho_c,rt in [('LOW',1e-12,1e-8),('NOM',1e-11,1e-7),('HIGH',1e-10,1e-6)]:
  R_contacts=352*rho_c/A
  R_total=R_leg+R_solder+R_contacts
  row={'label':label,'assumed_interface_specific_electrical_resistivity_ohm_m2':rho_c,
   'assumed_interface_thermal_areal_resistance_m2_K_W':rt,
   'aggregate_352_interface_series_electrical_R_ohm':R_contacts,
   'solder_bulk_electrical_R_ohm':R_solder,
   'research_300K_PN_leg_only_series_R_ohm':R_leg,
   'hypothetical_full_88_leg_plus_solder_R_at300K_ohm':R_total,
   'interface_series_R_fraction_vs_legs':R_contacts/R_leg,
   'single_contact_R_kelvin_per_W':rt/A,
   'single_solder_joint_R_thermal_K_W':Ls/(k_s*A),
   'one_leg_two_solders_plus_four_contact_R_thermal_K_W':2*Ls/(k_s*A)+4*rt/A,
   'single_P_leg_thermal_R_300K_research_analog_K_W':Ll/(kp*A),
   'single_N_leg_thermal_R_300K_research_analog_K_W':Ll/(kn*A),
   'thermal_1D_contact_path_NOT_comparable_to_module_total_R_K_W':True,
   'both_interface_laws_UNRELEASED':True,
   'currents':[{'A':I,'P_Joule_all_solder_W':I*I*R_solder,
                'P_Joule_all_352_interfaces_W':I*I*R_contacts,
                'contact_delta_V_V':I*R_contacts} for I in (.25,.4)]}
  rows.append(row)
 # Source-specific contact resistivity threshold for just a one-percent
 # cumulative resistance increase relative to all 88 legs at 300K.
 rho_c_one_percent=.01*R_leg*A/352
 # Sensitivity to contact k is most relevant at leg scale, because
 # heat transport is shared in parallel across 29/11/4 stage legs.
 # Required single contact-area resistance at which 4 contacts =1%
 # thermal leg resistance; separately for P and N (illustrative).
 rt_threshold_p=.01*(Ll/(kp*A))*A/4
 rt_threshold_n=.01*(Ll/(kn*A))*A/4
 return {
  'status':'SOURCE CONTACT IDENTITY & CONDITIONAL SCALE AUDIT PASS; ALL PHYSICAL INTERFACE COEFFICIENTS UNRELEASED',
  'method':'Direct original CAD source face tag census plus 1D positive series electrical/individual leg thermal resistance identities at fixed300K',
  'as_built_grade_release':'STOP',
  'source_global_44_P_and_44_N_in_series':True,
  'source_SnSb_joint_solids':len(solder),
  'source_SnSb_native_contact_faces':sum(count.values()),
  'source_contact_material_pair_counts':dict(count),
  'source_nominal_contact_area_per_face_mm2':.16,
  'source_joint_thickness_mm':.035,
  'source_leg_length_mm':.5,
  'source_leg_A_mm2':.16,
  'research_nominal_300K_P_N_resistivities_ohm_m':[rho_p,rho_n],
  'research_nominal_300K_P_N_thermal_conductivities_W_mK':[kp,kn],
  'nominal_300K_unmatched_analog_PN_leg_series_R_ohm':R_leg,
  'source_old_GateB_hypothetical_SnSb_bulk_electrical_rho_ohm_m':rho_s,
  'source_old_GateB_hypothetical_SnSb_bulk_k_W_mK':k_s,
  'all_176_SnSb_bulk_electrical_R_ohm':R_solder,
  'solder_bulk_electrical_R_fraction_of_300K_leg_only':R_solder/R_leg,
  'contact_specific_rho_at_1pct_88_leg_series_R_ohm_m2':rho_c_one_percent,
  'contact_specific_thermal_R_at_4_interfaces_1pct_single_P_leg_m2K_W':rt_threshold_p,
  'contact_specific_thermal_R_at_4_interfaces_1pct_single_N_leg_m2K_W':rt_threshold_n,
  'hypotheses_only_not_as_built_interface_data':rows,
  'source_evidence':['Original 430-domain face tags and 824 source bodies',
   'Zhang 40–300K research unmatched P/N specimens: nominal 300K point only',
   'Earlier 2026-11-02 Gate B interface hypotheses (not real TEC junction measurements)'],
  'important_interface_caveats':[
    'P/N Seebeck jump and contact Peltier heat change thermal interface equation even for low thermal resistance',
    'Real solder, barrier and metallization have temperature-dependent transport, uncertain layer thickness and microcontact area',
    'Series electrical R applies to all 88 leg currents; local thermal resistance is not 88 legs in series due to parallel stage heat paths',
    'Contact-specific rho, rth hypothetical LOW/NOM/HIGH not measured nor correlated to solder/leg/metal contacts',
    'No transfer of thermal contact values from unrelated lead9 GateB coupon can qualify actual TEC joints',
    'At operating field temperatures 180–303K, 300K spot resistivities and bulk k do not replace proper spatial temperature-dependent law',
    'An electrical and thermal coupled subassembly requires valid external source cut-port conditions and thermoelectric interface energy conservation'],
  'original_electrical_Gate_B':'FAIL/STOP',
  'prospective_P2_Gate_B':'STOP',
  'full_physical_430_domain_thermal_C_D':'NOT RUN',
  'new_PDE_runs':0,
  'source_geometry_and_material_laws_unchanged':True,
  'source_input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in FILES}
 }

def main():
 a=argparse.ArgumentParser()
 a.add_argument('--out',type=Path,required=True)
 a.add_argument('--verify-only',action='store_true')
 opts=a.parse_args();r=build()
 if opts.verify_only:assert read(opts.out)==r
 else:
  assert not opts.out.exists()
  opts.out.parent.mkdir(parents=True,exist_ok=True)
  opts.out.write_text(json.dumps(r,indent=2)+'\n')
 print('NATIVE_PN_SOLDER_CONTACT_AUDIT',json.dumps({
  k:r[k] for k in ('source_SnSb_joint_solids','source_SnSb_native_contact_faces',
 'nominal_300K_unmatched_analog_PN_leg_series_R_ohm',
 'all_176_SnSb_bulk_electrical_R_ohm',
 'contact_specific_rho_at_1pct_88_leg_series_R_ohm_m2',
 'contact_specific_thermal_R_at_4_interfaces_1pct_single_P_leg_m2K_W',
 'contact_specific_thermal_R_at_4_interfaces_1pct_single_N_leg_m2K_W')},indent=2))
 for row in r['hypotheses_only_not_as_built_interface_data']:
  print('HYPOTHETICAL',row['label'],'R_INTERFACE_OHM',row['aggregate_352_interface_series_electrical_R_ohm'],
        'P_INTERFACE_AT_0.4A_W',row['currents'][1]['P_Joule_all_352_interfaces_W'])
if __name__=='__main__':main()
