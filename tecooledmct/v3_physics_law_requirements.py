"""Fail-closed specifications for V3 domain and boundary laws, never inferred values."""
from collections import Counter

# A type is permitted only if its required constitutive measurements/models are explicit.
REQUIREMENTS={
 'COMPOSITE_MULTILAYER':('constituent bulk sigma(T),k(T),E,CTE','effective anisotropic sigma_parallel/sigma_normal(T)','effective k_parallel/k_normal(T)','explicit finite inter-layer electrical/thermal contact laws','multilayer thin-film equivalence control'),
 'P':('sigma(T)','k(T)','Seebeck(T)','Thomson/dSeebeck_dT','elasticity and CTE(T)','grade/provenance/temperature-range'),
 'N':('sigma(T)','k(T)','Seebeck(T)','Thomson/dSeebeck_dT','elasticity and CTE(T)','grade/provenance/temperature-range'),
 'IDEALIZED_CAVITY_GAS':('species/mixture','pressure(T)','regime Knudsen/Rayleigh applicability','k(T,P)','molecular accommodation where applicable','gas-solid interface transport'),
 'SnSb':('bulk sigma(T),k(T)','finite contact specific R_e(T)','finite thermal contact R_t(T)','joining and reliability evidence'),
 'SnBi57_43':('bulk sigma(T),k(T)','finite contact specific R_e(T)','finite thermal contact R_t(T)','joining and reliability evidence'),
 'In52Sn48':('bulk sigma(T),k(T)','finite contact specific R_e(T)','finite thermal contact R_t(T)','joining and reliability evidence'),
}
STANDARD={
 'Cu','Au','Ni','Kovar_pin','Glass','Al2O3','EP29LPSP','Polyimide_candidate','Steel',
 'Kovar','Sapphire','pHgCdTe_PC','ZnSe_candidate'
}

def generate_requirements(registry):
    domains=registry['domain_metadata'];faces=registry['interface_records']
    if len(domains)!=438 or len(faces)!=2456:
        raise ValueError('incomplete domain/face registry')
    unsupported={q['material'] for q in domains.values()}-set(REQUIREMENTS)-STANDARD
    if unsupported:raise ValueError('unknown material without a policy: '+str(sorted(unsupported)))
    out={};bytype=Counter()
    for name,q in domains.items():
        material=q['material'];bytype[material]+=1
        req=list(REQUIREMENTS.get(material,('temperature-dependent thermoelastic and heat transport law','electrical conductivity or explicit dielectric','provenance and range')))
        if material=='COMPOSITE_MULTILAYER':
            if not q.get('layer_stack') or q.get('constitutive_assignment')!='REQUIRES_EFFECTIVE_TENSOR_AND_INTERFACE_LAW':
                raise ValueError('bulk composite fallback: '+name)
        if material in ('P','N') and q.get('stage') not in (0,1,2):
            raise ValueError('unassigned thermoelectric stage: '+name)
        out[name]={'domain_tag':q['tag'],'material_role':material,'required':req,'value_assignment':'UNSET',
                   'source_names':q['source_names'],'stage':q.get('stage'),'solver_admissibility':False}
    fgroups=Counter(f['interface_class'] for f in faces)
    if fgroups!=Counter({'GAS_SOLID':1848,'SOLID_SOLID':565,'EXTERIOR':43}):
        raise ValueError('face class coverage is inconsistent')
    for f in faces:
        if not f.get('electrical_material_category') or not f.get('structural_condition') or not f.get('thermal_condition'):
            raise ValueError('silent interface law fallback face '+str(f['face_tag']))
        if f['interface_class']=='GAS_SOLID' and not f['radiation_condition']:
            raise ValueError('gas/radiation boundary classification missing')
    return {'status':'PASS COMPLETE REQUIREMENT ENUMERATION; ALL COEFFICIENTS UNQUALIFIED',
     'solver_ready':False,'volume_count':len(out),'face_count':len(faces),'volume_material_counts':dict(bytype),
     'boundary_counts':dict(fgroups),'domain_requirements':out,
     'face_law_contract':{'SOLID_SOLID':['decide bonded / finite resistance / dielectric insulation per interface',
          'thermal contact conductance and structural bond/slip','electric normal-current continuity or explicit isolation'],
         'GAS_SOLID':['qualified gas conduction regime','radiation flux is a separate additive physical term','gas-solid accommodation and optical status'],
         'EXTERIOR':['thermal environmental boundary or insulation','mechanical restraint/traction','electrical terminal or insulation','optical flux where applicable']},
     'release_blockers':['Global 3D conformal volume mesh does not exist','Global 2D surface candidate failed CAD/triangle area gate','No qualified device-specific material tensor, contact law or gas/radiation closure','Original electrical solver Gate B remains STOP'],
     'no_implicit_bulk_fallback':True}
