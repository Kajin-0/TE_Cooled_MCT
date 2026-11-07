#!/usr/bin/env python3
"""Build immutable source-keyed physical-input readiness ledgers from accepted R3 CAD.

NO material assignment, coefficient guess, PDE, FEM, remesh, optimization,
physical-law release or property calibration. Existing literature P/N profile
is merely a candidate analog with a source-data coverage declaration.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GEOM=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
PROFILE=ROOT/'data/tec_material_plausibility_20261101/properties.json'
TRANSPORT=ROOT/'data/tec_material_plausibility_20261101/transport_verification.json'
DESIGN=ROOT/'data/tec_candidate_29114_v2_20261102/source_final/design.json'
INPUT_GATE=ROOT/'data/v3_physical_blocker_closure_20261106/attempt01/readiness_audit.json'
GATE_B=ROOT/'data/v3_interconnect_et_20261102/B/gate_B.json'
SOURCE_META=ROOT/'docs/TEC_MATERIAL_PLAUSIBILITY_20261101.md'

MATERIAL_PATHS={
 'N':('thermoelectric_active','P_OR_N_S_RHO_K_T_THOMSON'),
 'P':('thermoelectric_active','P_OR_N_S_RHO_K_T_THOMSON'),
 'COMPOSITE_MULTILAYER':('effective_multilayer','ANISOTROPIC_EFFECTIVE_SIGMA_K_AND_LAYER_CONTACTS'),
 'EFFECTIVE_AXIAL_KOVAR_NI_AU':('effective_axial_multilayer','AXIAL_SIGMA_K_AND_KOVAR_NI_AU_INTERFACE'),
 'IDEALIZED_CAVITY_GAS':('gas_and_exchange','GAS_P_T_K_ACCOMMODATION_AND_RADIATION'),
 'pHgCdTe_PC':('semiconductor_detector','DOPING_COMPOSITION_SIGMA_K_T_BIAS_CONTACT'),
 'Polyimide_candidate':('candidate_polymer','TEMPERATURE_DEPENDENT_DIELECTRIC_K_AND_IDENTITY'),
 'SnSb':('solder_joint','SOLDER_GRADE_SIGMA_K_T_AND_FINITE_CONTACT'),
 'SnBi57_43':('solder_joint','SOLDER_GRADE_SIGMA_K_T_AND_FINITE_CONTACT'),
 'In52Sn48':('solder_joint','SOLDER_GRADE_SIGMA_K_T_AND_FINITE_CONTACT'),
 'Cu':('metal','SIGMA_K_T_GEOMETRY_AND_PLATING'),
 'Au':('metal','SIGMA_K_T_AND_FINITE_CONTACT'),
 'Al2O3':('ceramic','K_T_GRADE_GEOMETRY_AND_INTERFACE'),
 'Sapphire':('die_carrier','ANISOTROPIC_K_T_CRYSTAL_ORIENTATION'),
 'EP29LPSP':('adhesive','CURED_GRADE_K_T_CONTACT_VOID_FRACTION'),
 'Kovar_pin':('alloy','ALLOY_K_SIGMA_T_AND_SURFACE_LAYERS'),
 'Kovar':('alloy','ALLOY_K_SIGMA_T_AND_SURFACE_LAYERS'),
 'Glass':('dielectric_seal','GLASS_COMPOSITION_K_T_AND_SEAL_CONTACT'),
 'Steel':('package_housing','ALLOY_K_EMISSIVITY_AND_THERMAL_BOUNDARY'),
 'ZnSe_candidate':('candidate_window','OPTICAL_THERMAL_K_EMISSIVITY_AND_IDENTITY'),
}
TE_PROFILE_DOC="docs/TEC_MATERIAL_PLAUSIBILITY_20261101.md"
PROFILE_REL="data/tec_material_plausibility_20261101/properties.json"
GEOM_REL="data/v3_r32_global_surface_20261103/source_metadata.json"

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4<<20),b''):h.update(block)
    return h.hexdigest()

def load(p):
    return json.loads(p.read_text())

def generate():
    cad=load(GEOM)
    props=load(PROFILE)
    techeck=load(TRANSPORT)
    design=load(DESIGN)
    prior=load(INPUT_GATE)
    gate=load(GATE_B)
    assert len(cad['domains'])==430 and len(cad['faces'])==2440
    assert len(cad['source_contacts'])==378
    assert len(MATERIAL_PATHS)==len(set(x['material'] for x in cad['domains'].values()))
    assert cad['stage_leg_counts']=={'0':58,'1':22,'2':8}
    assert design['stage_couples_hot_to_cold']==[29,11,4]
    assert len(design['legs'])==88
    assert gate['status']=='FAIL/STOP'
    assert prior['physical_input_population']['source_solver_ready_domains']==0
    assert props['source']['source_id']=='zhang2025_he_digitized_40_300_v2r1'
    assert props['source']['measured_K']==[40.0,300.0]
    assert props['source']['commercial_grade_matched'] is False
    assert techeck['passed'] is True
    for key in ('P','N'):
        data=props['hypotheses']['nominal']['polarities'][key]
        for prop in ('S','rho','k'):
            assert len(data[prop])==len(props['temperature_K'])
    evidence={
      'E_001':{
        'class':'RESEARCH_SPECIMEN_ANALOG_NOT_AS_BUILT',
        'source':PROFILE_REL,
        'citation_doi':props['source']['source_doi'],
        'source_identifier':props['source']['source_id'],
        'published_source_profile_SHA256':props['source']['file_sha256'],
        'digitized_profile_file_SHA256':digest(PROFILE),
        'measured_coverage_K':[40,300],
        'research_P_and_N_different_specimens':True,
        'matched_commercial_P_N_module':False,
        'high_temperature_profile_above_300K':'ASSUMED; cannot count as measured',
        'solver_readiness':'NOT RELEASED'},
      'E_002':{
        'class':'PRIOR_REDUCED_MODEL_SENSITIVITY_NOT_V3_CALIBRATION',
        'source':TE_PROFILE_DOC,
        'source_SHA256':digest(SOURCE_META),
        'stage_counts_in_prior_model':[28,12,4],
        'stage_counts_in_current_R3':[29,11,4],
        'physics_scope':'Reduced 1D model; real cooler grades, contacts, bypasses, radiation not qualified',
        'solver_readiness':'NOT RELEASED'},
      'E_003':{
        'class':'GEOMETRIC_IDENTITY_ONLY',
        'source':GEOM_REL,
        'source_SHA256':digest(GEOM),
        'solver_readiness':'NOT RELEASED'},
    }
    volumes=[]
    for name,v in sorted(cad['domains'].items(),key=lambda x:x[1]['id']):
        mat=v['material']
        role,required=MATERIAL_PATHS[mat]
        is_leg=mat in ('N','P')
        obj={
         'volume_id':v['id'],'cad_name':name,
         'material_label_from_CAD':mat,
         'material_role':role,
         'stage':v.get('stage'),
         'required_constitutive_data':required,
         'original_constitutive_requirement':v['constitutive_requirement'],
         'original_law_status':v['law_status'],
         'original_solver_ready':v['solver_ready'],
         'geometry_source':[GEOM_REL],
         'as_built_material_identification':'NOT ESTABLISHED',
         'permitted_candidate_evidence_refs':['E_001'] if is_leg else [],
         'candidate_provenance':'RESEARCH_ANALOG_ONLY' if is_leg else 'SOURCE_GEOMETRY_ONLY',
         'measured_assigned_transport':None,
         'released_temperature_range_K':None,
         'released_sigma_electrical_S_m':None,
         'released_k_thermal_W_per_mK':None,
         'released_Seebeck_V_per_K':None,
         'released_uncertainty':None,
         'material_law_release':'STOP',
         'law_release_blocker':required,
         'layer_stack_source':v.get('layer_stack'),
        }
        if is_leg:
            obj['candidate_research_analog']={
                'evidence_ref':'E_001',
                'polarity':mat,
                'measured_coverage_K':[40,300],
                'not_grade_matched':True,
                'candidate_profile_path':PROFILE_REL,
                'actual_stage_geometry_qualified':False,
                'usable_for_physical_release':False}
        volumes.append(obj)
    assert [x['volume_id'] for x in volumes]==list(range(1,431))
    volume_by_id={v['volume_id']:v for v in volumes}
    faces=[]
    witness_tags=collections.Counter()
    for x in cad['source_contacts']:
        for t in x['face_tags']:
            witness_tags[int(t)]+=1
    assert len(witness_tags)>0
    for tag,f in sorted(cad['faces'].items(),key=lambda x:int(x[0])):
        t=int(tag);owners=f['owner_volume_ids']
        cls=f['class_']
        if cls=='SOLID_SOLID':
            needed='CONTACT_CONDUCTANCE_ELECTRICAL_THERMAL_AND_THERMOELECTRIC_JUNCTION_IF_APPLICABLE'
        elif cls=='GAS_SOLID':
            needed='GAS_COMPOSITION_PRESSURE_EXCHANGE_AND_RADIATION'
        else:
            needed='SIGNED_EXTERNAL_PORT_OR_HEAT_FLUX_CONVECTION_RADIATION_OR_INSULATION'
        faces.append({
          'face_tag':t,'face_class':cls,
          'owner_volume_ids':owners,
          'owner_CAD_names':f['owners'],
          'CAD_area_mm2':f['face_area_mm2'],
          'CAD_center_mm':f['center_mm'],
          'source_face_type':f['type'],
          'source_finite_contact_witness_count':witness_tags.get(t,0),
          'original_law_status':f['law_status'],
          'needed_law_for_eventual_release':needed,
          'contact_electrical_area_resistance_ohm_m2':None,
          'contact_thermal_area_resistance_m2_K_W':None,
          'thermoelectric_interface_Peltier_law':None,
          'gas_or_radiative_exchange_law':None,
          'external_electrical_BC':None,
          'external_thermal_BC':None,
          'assigned_uncertainty':None,
          'physical_law_release':'STOP',
          'source':GEOM_REL,
        })
    assert [x['face_tag'] for x in faces]==list(range(1,2441))
    assert sum(f['source_finite_contact_witness_count'] for f in faces)>=378
    counts=collections.Counter(x['face_class'] for x in faces)
    assert counts=={'GAS_SOLID':1840,'SOLID_SOLID':557,'EXTERIOR':43}
    # Select a REAL contiguous P-N pair, not a generic fixture.
    names=['ceramic0','ceramic1',
           'leg0_N','solder0_hot','solder0_cold',
           'leg1_P','solder1_hot','solder1_cold',
           'net0_plane0.500_Cu','net1_plane1.100_Cu','net2_plane0.500_Cu']
    ids={cad['domains'][name]['id'] for name in names}
    assert len(ids)==11
    def iface(a,b):
        aa=cad['domains'][a]['id'];bb=cad['domains'][b]['id']
        selected=[v for v in faces if set(v['owner_volume_ids'])=={aa,bb}
                  and v['face_class']=='SOLID_SOLID']
        assert len(selected)==1,(a,b,len(selected))
        return selected[0]
    links=[
     ('leg0_N','solder0_hot'),
     ('leg0_N','solder0_cold'),
     ('leg1_P','solder1_hot'),
     ('leg1_P','solder1_cold'),
     ('solder0_hot','net0_plane0.500_Cu'),
     ('solder0_cold','net1_plane1.100_Cu'),
     ('solder1_cold','net1_plane1.100_Cu'),
     ('solder1_hot','net2_plane0.500_Cu'),
     ('net0_plane0.500_Cu','ceramic0'),
     ('net2_plane0.500_Cu','ceramic0'),
     ('net1_plane1.100_Cu','ceramic1')]
    true_links=[]
    for left,right in links:
        f=iface(left,right)
        true_links.append({
          'first':left,'second':right,
          'CAD_face_tag':f['face_tag'],
          'area_mm2':f['CAD_area_mm2'],
          'owner_volume_ids':f['owner_volume_ids'],
          'law_ready':False})
    assert len(true_links)==11
    # This is a subassembly geometry selection only; does not isolate actual
    # ceramic into private tiles or fake two new electrical terminal faces.
    remaining_faces=[]
    internal_faces=[]
    for f in faces:
        common=ids.intersection(f['owner_volume_ids'])
        if not common:continue
        if set(f['owner_volume_ids']).issubset(ids):
            internal_faces.append(f['face_tag'])
        elif len(common)==1:
            remaining_faces.append(f['face_tag'])
    assert len(remaining_faces)>0
    assert len(internal_faces)>0
    high_priority=[
      {'id':'H1','issue':'Identify actual P- and N-type TE leg grades and S(T), rho(T), k(T) on real material at all operating temperatures, including Thomson derivative','target_volume_ids':[5,8],'status':'STOP','measurement_or_evidence':'Supplier-grade curves or separately measured same-grade P/N specimens over full hot/cold range; exclude 300 K-plus extrapolated quarter-slope'},
      {'id':'H2','issue':'Qualify 0.035 mm SnSb solders and metal pad contact laws, electrical and thermal','target_volume_ids':[6,7,9,10,269,270,271],'status':'STOP','measurement_or_evidence':'As-built solder alloy composition, K(T), sigma(T), interfacial area resistance/thermal boundary resistance and joining process'},
      {'id':'H3','issue':'Define actual couple subassembly electrical ports and external circuit constraints','target_face_tags':remaining_faces,'status':'STOP','measurement_or_evidence':'A single exposed copper port each side with measured drive/current sign and treatment of the rest of the 88-leg network. No invented insulating cuts'},
      {'id':'H4','issue':'Define physical ceramic hot/cold temperatures, bath/sink and heat loads with contact area/heat-spreading','target_volume_ids':[1,2],'status':'STOP','measurement_or_evidence':'Measured hot/cold ceramic boundary T or calibrated heat sink and stage heat flow; unknown gas/radiation bypass separately accounted'},
      {'id':'H5','issue':'Resolve full 430 region/2440 face assembly law and numerical Gate B before whole-device prediction','status':'STOP','measurement_or_evidence':'Current density/flux consistency, meaningful physical terminal conservation and independent TEC validation'},
    ]
    for f in faces:
        assert f['physical_law_release']=='STOP'
    out={
      'status':'STOP physical 3D electrothermal subassembly; geometry-chain evidence PASS, actual properties and ports NOT RELEASED',
      'scientific_scope':'No-solve, source-keyed ledger and actual selected P/N geometry',
      'source_CAD_domains':430,'source_CAD_faces':2440,'source_contacts':378,
      'source_stage_leg_counts_hot_to_cold':[58,22,8],
      'source_stage_couples_hot_to_cold':[29,11,4],
      'source_thermoelectric_polarity_counts':dict(collections.Counter(v['material_label_from_CAD'] for v in volumes if v['material_label_from_CAD'] in ('P','N'))),
      'source_material_counts':dict(collections.Counter(x['material_label_from_CAD'] for x in volumes)),
      'source_face_class_counts':dict(counts),
      'unreleased_volume_laws':430,'unreleased_face_laws':2440,
      'volume_law_rows':volumes,'face_law_rows':faces,
      'candidate_source_evidence':evidence,
      'R3_exact_source_terminal_faces':cad['terminal_faces'],
      'selected_actual_P_N_subassembly':{
        'selection_name':'First real R3 stage0 N/P pair with shared cold net1 metal pad',
        'selected_CAD_names':names,
        'selected_volume_ids':sorted(ids),
        'selected_volume_count':len(ids),
        'actual_native_internal_links':true_links,
        'internal_face_tags':internal_faces,
        'cut_boundary_face_tags':remaining_faces,
        'cut_boundary_faces_count':len(remaining_faces),
        'contains_whole_original_ceramic0_and_ceramic1':True,
        'requires_independent_thermal_port_partition':True,
        'actual_operating_electrical_ports_qualified':False,
        'circuit_endpoint_and_isolation_method':'NOT ASSIGNED',
        'model_S_rho_k':None,
        'contact_laws':None,
        'heat_boundary_conditions':None,
        'electric_boundary_conditions':None,
        'finite_contact_reactions':'NOT RUN',
        'coupled_FEM':'NOT RUN',
        'electrical_current_closure':'NOT RUN',
        'thermal_energy_closure':'NOT RUN',
        'decision':'NO GO physical solve pending H1..H4'},
      'priority_evidence_blockers':high_priority,
      'mathematical_operator_contract_not_yet_qualified':{
       'electrical':'J=sigma*(-grad(V)-S*grad(T)); choose potential and Seebeck convention consistently',
       'heat_flux':'q=Pi*J-k*grad(T), Pi=S*T, with Joule/Thomson and correct sign',
       'thermal_residual':'div(q)+J dot grad(V) = 0 only for a defined consistent heat/energy convention; derive with Peltier terms explicitly before solver',
       'external':'Total electrical current closure and integrated energy balance must include all retained external boundary ports',
       'Peltier_interfaces':'Jump in Pi at electrically joined P/N/metal must be included in energy balance; no arbitrary contact heat partition',
       'no_regression_claim':'Original P1 Gate B and stopped prospective P2 remain unchanged'},
      'release_status':{'original_electrical_Gate_B':'FAIL/STOP',
        'prospective_P2_electrical_gate':'STOP','thermal_Gate_C':'NOT RUN',
        'electrothermal_Gate_D':'NOT RUN','source_constitutive_law_release':'STOP',
        'full_430_domain_solver':'NOT RUN','current_stage_temperature_prediction':'UNQUALIFIED'},
      'source_input_SHA256':{
       str(p.relative_to(ROOT)):digest(p) for p in
       (GEOM,PROFILE,TRANSPORT,DESIGN,INPUT_GATE,GATE_B,SOURCE_META)}
    }
    assert out['source_thermoelectric_polarity_counts']=={'N':44,'P':44}
    assert len({x['face_tag'] for x in out['face_law_rows']})==2440
    return out

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--out',type=Path)
    a.add_argument('--verify-only',action='store_true')
    args=a.parse_args()
    o=generate()
    if args.verify_only:
        assert args.out and args.out.is_file()
        assert load(args.out)==o,'Archived physical-input mapping differs from current source'
    elif args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        # Human diff-friendly: one complete native volume/face ledger row
        # per line, while preserving other metadata in indented JSON.
        # The representation is valid JSON and fully reproducible.
        with args.out.open('x') as f:
            f.write('{\n')
            items=list(o.items())
            for n,(k,v) in enumerate(items):
                f.write('  '+json.dumps(k)+': ')
                if k in ('volume_law_rows','face_law_rows'):
                    f.write('[\n')
                    for idx,row in enumerate(v):
                        f.write('    '+json.dumps(row,sort_keys=True,separators=(',',':')))
                        f.write(',\n' if idx+1<len(v) else '\n')
                    f.write('  ]')
                else:
                    f.write(json.dumps(v,indent=2))
                f.write(',\n' if n+1<len(items) else '\n')
            f.write('}\n')
    print('ACTUAL_R3_PHYSICAL_INPUT_LEDGER',json.dumps({
      'status':o['status'],'material_counts':o['source_material_counts'],
      'face_counts':o['source_face_class_counts'],
      'subassembly_volumes':o['selected_actual_P_N_subassembly']['selected_volume_ids'],
      'native_interfaces':[(x['first'],x['second'],x['CAD_face_tag']) for x in o['selected_actual_P_N_subassembly']['actual_native_internal_links']],
      'unknown_thermal_electrical_CAD_cut_faces':o['selected_actual_P_N_subassembly']['cut_boundary_faces_count'],
      'evidence_blockers':[x['id'] for x in o['priority_evidence_blockers']]
    },indent=2))
if __name__=='__main__':
    main()
