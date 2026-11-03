"""No-PDE acceptance of preserved V3 R2 analysis geometry and its STOP boundaries."""
from __future__ import annotations
from collections import Counter
import hashlib,math

ORIGINAL_COUNTS={'GAS_SOLID':1832,'SOLID_SOLID':547,'EXTERIOR':43}
EXPECTED_TERMINALS={'TERMINAL_PIN1','TERMINAL_PIN7','TERMINAL_PIN8','TERMINAL_PIN9'}

def req(condition,reason):
    if not condition:raise ValueError(reason)

def validate(manifest,build,integrity,shell,laws,surface,local):
    req(manifest['geometry_volumes']==428 and manifest['geometry_faces']==2422,'R2 dimension count')
    req(build['status'].startswith('PASS') and
        build['final_volume_count']==428 and build['face_count']==2422,'R2 BREP not accepted')
    req(integrity['status'].startswith('PASS') and integrity['volume_count']==428
        and integrity['face_count']==2422,'R2 source/face registry fail')
    req(len(integrity['source_to_analysis'])==manifest['original_source_bodies']==824,
        'physical source identity missing')
    req(len(integrity['source_contacts'])==manifest['finite_contacts_preserved']==378,
        'source contacts incomplete')
    req(not integrity['missing_contacts'] and not integrity['area_errors']
        and not integrity['unintended_electrical_contacts'],'contact/short gate failed')
    req(all(c.get('relative_error',0)<1e-6 for c in integrity['source_contacts']),
        'contact source area drift')
    names=integrity['domain_id_map']
    req(len(names)==428 and len(set(names.values()))==428,
        'duplicate domain identity')
    req(integrity['face_class_counts']==ORIGINAL_COUNTS,
        'incomplete registered face groups')
    req(len(integrity['face_registry'])==2422,'face registry missing')
    for item in integrity['face_registry'].values():
        owners=item['owner_volume_ids']
        req(len(owners) in (1,2) and len(set(owners))==len(owners),'invalid face ownership')
        req(all(n in names and names[n]==t for n,t in zip(item['owners'],owners)),
            'invalid face owner map')
        req(item['face_area_mm2']>0 and math.isfinite(item['face_area_mm2']),
            'invalid exact CAD face area')
    req(integrity['gas_components']==manifest['gas_components']==1,'gas disconnected')
    req('double count' in manifest.get('gas_replacement_caveat',''),
        'unqualified gas/polymer displacement correction missing')
    jacket=sum(x['source_3d_polyimide_mm3'] for x in build['lead_jacket_records'])
    req(abs(jacket-(build['R2_gas_volume_mm3']-1231.6300611682168))<1e-7,
        'gas occupied-volume exclusion vs polymer shell mismatch')
    for cap in build['pin_caps']:
        req(abs(cap['new_effective_pin_mm3']-cap['original_pin_mm3']-
                cap['effective_axial_cap_area_mm2']*cap['thin_film_effective_thickness_mm'])<1e-8,
            'effective pin cap volume not preserved')
    req(shell['status'].startswith('PASS') and
        len(shell['mapping'])==10 and shell['full_face_count']==6 and
        shell['partial_face_count']==manifest['shell_subface_limits']==4,
        'missing shell partial coverage evidence')
    req(all(q['constitutive_law_status']=='UNSET' for q in shell['mapping']),
        'unqualified shell law assigned')
    req(any(q['condition']=='PARTIAL_SUBFACE_OPERATOR_REQUIRED' for q in shell['mapping']),
        'stripped-end geometry cannot be silently homogenized')
    req(laws['status'].startswith('PASS') and not laws['solver_ready'] and
        len(laws['domain_requirements'])==428 and len(laws['face_requirements'])==2422,
        'law coverage incomplete')
    req(laws['domain_material_counts']['COMPOSITE_MULTILAYER']==98 and
        laws['domain_material_counts']['EFFECTIVE_AXIAL_KOVAR_NI_AU']==4,
        'effective bulk fallback')
    req(laws['domain_material_counts']['IDEALIZED_CAVITY_GAS']==1 and
        laws['stage_leg_counts']=={'0':58,'1':22,'2':8},
        'thermoelectric material identity changed')
    req(set(laws['terminal_face_counts'])==EXPECTED_TERMINALS
        and all(x==1 for x in laws['terminal_face_counts'].values()),
        'electrical terminal coverage not unique')
    req(all(q['law_status']=='UNSET' and not q['solver_ready']
        for q in laws['domain_requirements'].values()),'unqualified volumetric law')
    req(all(q['coefficient_status']=='UNSET' and not q['solver_ready']
        for q in laws['face_requirements']),'unqualified interface law')
    req(surface['status'].startswith('PASS') and surface['face_count']==2422
        and surface['fail_count']==0,'global surface fails CAD area gate')
    req(surface['max_absolute_error_relative']<.01 and
        surface['triangle_count']==manifest['surface_candidate_triangles'] and
        surface['mesh_nodes']==manifest['surface_candidate_nodes'],
        'surface accuracy or density inaccurate')
    req(local['status'].startswith('PASS') and local['domain_count']==4
        and local['tetrahedra']==manifest['local_3D_lead_pin_tetrahedra'] and
        all(v['relative_volume_error']<.01 for v in local['volumes'].values()),
        'local 3D mesh inaccurate')
    req(manifest['legacy_electrical_Gate_B']=='STOP' and manifest['issue_2']=='OPEN'
        and not manifest['physical_redesign'] and
        manifest['global_3D_mesh_status'].startswith('NOT RUN'),
        'historical STOP or physical redesign violated')
    return {'status':'PASS GEOMETRIC R2 SOURCE/FACE/LOCAL MESH GATES; GLOBAL VOLUME/PDE UNQUALIFIED',
       'domains':428,'faces':2422,'source_bodies':824,'contacts':378,
       'partial_shell_subfaces':4,'2d_surface_triangles':surface['triangle_count'],
       '2d_area_failures':0,'local_tets':local['tetrahedra'],
       'global_volume_mesh':'NOT RUN','solver_ready':False}

def verify_files(directory,manifest,source_step,master,r1_solids):
    req(hashlib.sha256(source_step.read_bytes()).hexdigest()==manifest['source_physical_STEP_SHA256'],
        'original STEP altered')
    req(hashlib.sha256(master.read_bytes()).hexdigest()==manifest['canonical_Rev3_SHA256'],
        'canonical Rev3 altered')
    req(hashlib.sha256(r1_solids.read_bytes()).hexdigest()==manifest['upstream_R1_reduced_solids_SHA256'],
        'original R1 computational BREP altered')
    for filename,digest in manifest['files_sha256'].items():
        req(hashlib.sha256((directory/filename).read_bytes()).hexdigest()==digest,
            'R2 artifact altered: '+filename)
    archive=directory/'global_surface_area_pass_VOLUME_UNQUALIFIED.msh.gz'
    req(hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['global_surface_gzip_sha256'],
        'R2 mesh archive altered')
    return True
