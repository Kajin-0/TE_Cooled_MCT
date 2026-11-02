"""Deterministic factual registry projection; no geometry modification or solves."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/physical_geometry_audit_20261102'
V2='data/tec_candidate_29114_v2_20261102'
NATIVE='fem/results/geometry_complete_checkpoint_20261030/manifest.json'
CODE='tecooledmct/tec_candidate_v2.py'


def read(p):return json.loads((ROOT/p).read_text())


def build():
    sources={s['id']:s for s in read(str(BASE.relative_to(ROOT)/'source_catalog.json'))['sources']}
    native=read(NATIVE);d=read(V2+'/source_final/design.json');cfg=read('data/corrected_enclosure/geometry_hypothesis_v1.json')
    rows=[]
    def add(pid,component,value,unit,sids,feature,*,bounds=None,basis='UNKNOWN: no sourced physical interval/tolerance',
            cls='INFERRED_TESTABLE',code=CODE,symbol='design',domain=None,impact=None,closure=None,
            contradiction=None,mesh='V2: no mesh/field; original28/12/4 fields use different geometry',
            property_ref='NOT ASSIGNED toV2 physics',manufacturing='NOT QUALIFIED',priority='P0',sensitivity=None):
        if pid.startswith('v2.'):sids=list(sids)+['V2-IMPL']
        if pid.startswith('material.') and pid not in ('material.BiTe_S','material.BiTe_rho','material.BiTe_k','material.MCT_composition'):
            sids=list(sids)+['NUM-01']
        refs=[{k:sources[sid][k] for k in ('id','publisher','product_identity','revision','location','url')} for sid in sids]
        lines=[i for i,line in enumerate((ROOT/code).read_text().splitlines(),1) if symbol in line] if (ROOT/code).is_file() else []
        rows.append(dict(parameter_id=pid,component=component,value_SI=value,units=unit,range_SI=bounds,range_basis=basis,
            source_refs=refs,evidence_class=cls,implementation=dict(path=code,symbol=symbol,matching_lines=lines[:4]),
            CAD=dict(manifest=V2+'/source_final/design.json' if pid.startswith('v2.') else NATIVE,feature=feature,
                     STEP=V2+'/cad/candidate_v2_mm.step' if pid.startswith('v2.') else 'Native/header/cap sources remain distinct; see source manifest'),
            mesh_property_prediction=dict(actual_mesh_field_use=mesh,property_ref=property_ref,
                prediction_impact=impact or 'Can change heat/electrical paths; matched device impact NOT RUN'),
            material_specimen_domain=domain or 'Geometry/process; temperature/current/cycling limits UNKNOWN',
            validation=dict(source='Selected exact dimensions only' if cls=='DOCUMENTED_EXACT_PRODUCT' else 'Hypothesis/analogy; no exact construction proof',
                CAD='Existing nominal topology/SI checks only; no manufacturing acceptance',manufacturing=manufacturing,
                independent_status='NOT REVIEWED per parameter; separate reviewer report governs'),
            contradiction_or_gap=contradiction or 'No independent process/metrology constraint; nominal is not a measured tolerance',
            identifiability='Do not infer dimension/grade/contact from fitted OEM lift/voltage; common A/L-rho-k gauge applies where relevant',
            sensitivity=sensitivity or dict(status='NOT RUN at matchedV2 target',metric=None),
            closure_test=dict(owner='Independent physical reviewer + supplier/process or metrology evidence',priority=priority,
                test=closure or 'Independent dimension/process specification and tolerance witness; source-to-CAD recheck before accepting physical use')))

    # Every inherited package dimension is retained with its original scoped range.
    for key,r in native['registry']['dimensions'].items():
        factor=.001 if r['unit']=='mm' else math.pi/180 if r['unit']=='deg' else 1.
        val=r['simulated']*factor
        if r['nominal'] is not None and r['tolerance'] is not None:
            bounds=[(r['nominal']-r['tolerance'])*factor,(r['nominal']+r['tolerance'])*factor];basis='Printed source tolerance for this selected envelope only'
        elif r['hypothesis_range']:
            bounds=[v*factor for v in r['hypothesis_range']];basis='PREEXISTING SCENARIO range; not physically measured or independently qualified'
        else:bounds=None;basis='UNKNOWN component tolerance; generalISO2768-mK noted onVIGO drawing, not evaluated as a numeric process bound'
        exact=r['source'] in ('vigo','tec');sid='PKG-01' if r['source']=='vigo' else 'TEC-01'
        add('native.'+key,'Inherited package/reference geometry',val,'m' if r['unit']=='mm' else 'rad' if r['unit']=='deg' else r['unit'],[sid],
            'registry.dimensions.'+key,bounds=bounds,basis=basis,cls='DOCUMENTED_EXACT_PRODUCT' if exact else 'SCENARIO',
            code='tecooledmct/geometry_registry.py',symbol='value',mesh='Original216-body3D mesh and native gas geometry; V2 uses envelope context only',
            contradiction=r['definition']+'; original source/assumption label '+r['certainty']+' is not composite OEM validation',
            closure='Check source line endpoints and assembly tolerance/actual mount/wire interfaces; preserve original registry bytes')

    for key,val,unit,sids,bounds,basis,feature in [
        ('stage_couples',[29,11,4],'1',['RMT-01-D','KRY-01'],None,'UNKNOWN exact allocation; original28/12/4 is a distinct44-couple hypothesis; Kry31/11/4 totals46,not interchangeable','stage_couples_hot_to_cold'),
        ('leg_count',88,'1',['RMT-01-D'],[88,88],'Fixed selected candidate design,not proof ofTEC2019 internals','legs'),
        ('leg_section',[.0004,.0004],'m',['RMT-01'],None,'RMT-family nominal; per-specimen tolerance UNKNOWN','bodies[kind=P/N].boxes_mm[3:5]'),
        ('leg_length',.0005,'m',['RMT-01-D'],None,'RMT2019/Z2 drawing analogy; selected TEC2019 internal dimension not given','bodies[kind=P/N].boxes_mm[5]'),
        ('leg_pitch',.00058,'m',['TEC-01'],None,'UNKNOWN; inferred placement','design serpentine pitch'),
        ('ceramic_width0',.0064,'m',['TEC-01'],[.0063,.0065],'Printed bottom envelope±0.1mm','ceramic0'),
        ('ceramic_width1',.0052,'m',['TEC-01'],None,'UNKNOWN internal width,not dimensioned','ceramic1'),
        ('ceramic_width2',.0038,'m',['TEC-01'],None,'UNKNOWN internal width,not dimensioned','ceramic2'),
        ('ceramic_width3',.0024,'m',['TEC-01'],[.0023,.0025],'Printed top envelope±0.1mm','ceramic3'),
        ('ceramic_thickness',.0005,'m',['TEC-03'],None,'Separate ceramic service offers0.5mm; actualMC04 layer/tolerance UNKNOWN','ceramic0…3 thickness'),
        ('stack_height',.0038,'m',['TEC-01'],[.00365,.00395],'Printed assembly height±0.15mm; constituent tolerance chain UNKNOWN','ceramic3 top minusceramic0 bottom'),
        ('Cu_face_edge_film',15e-6,'m',['TEC-02','TEC-03'],None,'UNKNOWN internal layer/process interval','layers_mm.copper_film;face/edge boxes'),
        ('foil_thickness',30e-6,'m',['TEC-01','KRY-01'],None,'UNKNOWN formed-foil gauge/process/rating','bridges[].foil_box_mm'),
        ('foil_track_width',.0002,'m',['TEC-01','TEC-03'],None,'UNKNOWN internal Cu process; externalAu width guideline is analogy only','layers_mm.trace_width'),
        ('SnSb_thickness',35e-6,'m',['TEC-01'],None,'Solder identity documented; joint thickness UNKNOWN','solder0_hot…solder87_cold'),
        ('edge_wrap_support',.0005,'m',['PAT-01','TEC-01'],None,'Constructed ceramic sidewall support; adhesion/corner coverage UNKNOWN','bridges[].edge_film_box_mm'),
        ('foil_gap',.0006,'m',['KRY-01','TEC-01'],None,'Constructed open span,not continuous support or fatigue rating','bridges[].free_gap_mm'),
        ('declared_land_inset',.0001,'m',['TEC-03'],None,'Film land inset; does NOT establish a100um foil lap joint','bridges[].lap_mm'),
        ('actual_foil_inward_foot',0.,'m',['TEC-01'],None,'Actual frozen foil box has no inward foot; process UNKNOWN','bridges[].foil_box_mm relative ceramic edge'),
        ('PN_pad_width',.00044,'m',['TEC-01'],None,'UNKNOWN pad/registration process','Cu pads under176 P/N contacts'),
        ('pad_pullback',.00011,'m',['TEC-03'],None,'Calculated minimum forP/N pads only,not ALL edge metal','source_audit.minimum_pad_pullback_mm'),
        ('unrelated_Cu_gap',.00014,'m',['TEC-03'],None,'Calculated nominal gap; etch/placement tolerances UNKNOWN','source_audit.minimum_Cu_gap_mm'),
        ('full_pad_registration_budget',20e-6,'m',['TEC-01'],None,'Derived ideal half pad-minus-leg width,not a measured tolerance','1760.4mm faces on0.44mm pads'),
        ('stage_join_height',.0011,'m',['TEC-01'],None,'Constructed0.6+0.5mm; not a measured connector','nets58/80'),
        ('return_height',.0022,'m',['TEC-01'],None,'Two explicit constructed steps,nonlocal thermal destinations','net88'),
        ('hot_terminal_A',[-.00203,-.0028,.000515],'m',['TEC-01'],None,'Hypothetical hot land; no pin1 conductor','Cu_node0'),
        ('hot_terminal_B',[.00087,.0028,.000515],'m',['TEC-01'],None,'Hypothetical hot land; no pin9 conductor','Cu_node88'),
        ('header_gap',.00005,'m',['PKG-01'],None,'World mount offset hypothesis; V2 does not include mounting-joint solid','offset1.55mm versus header1.5mm'),
        ('MCT_dimensions',[.001,.001,.0002],'m',['PKG-01'],None,'1mm-square optical area is family option,bulk thickness/composition UNKNOWN','hypothetical_MCT'),
        ('die_attach_thickness',30e-6,'m',['PKG-01'],None,'UNKNOWN die attach construction','auxiliary_attach')]:
        exact=key in ('ceramic_width0','ceramic_width3','stack_height')
        add('v2.'+key,'Separate compactV2',val,unit,sids,feature,bounds=bounds,basis=basis,
            cls='DOCUMENTED_EXACT_PRODUCT' if exact else 'INFERRED_TESTABLE')
    for net in (0,58,80,88):
        add(f'v2.net{net}_topology','Full series metal route',net,'1',['TEC-01','KRY-01'],f'Cu_node{net}',
            cls='PHYSICS_CONSTRAINT',symbol='trace(',impact='Net88 contacts ceramics0/1/2; geometry connectivity is not thermal qualification',
            closure='Verify actual full pin-to-pin circuit and physical bonds at every face/edge/gap; independent Cu/ceramic contact mapping')
    add('v2.physical_pin1_9_connections','Package electrical closure',None,'1',['PKG-01'],'ABSENT fromV2',cls='UNKNOWN',
        contradiction='Two hot lands do not reach actual pins1/9; V2 external_pin_wires=OFF',
        closure='Real pin1→net0 andnet88→pin9 wires/joints with clearances and isolated detector7/8,then review before physics')
    add('v2.detector_bonds','Detector electrical closure',None,'1',['PKG-01'],'ABSENT fromV2',cls='UNKNOWN',
        closure='Specified die pad metallurgy and actual pin7/8 bond geometry; do not invent a bond from a render')
    add('v2.foil_joint_process','Interstage joining',None,'process',['TEC-01','TEC-02','KRY-01'],'ideal Cu union;no resolved foil solder fillet',cls='UNKNOWN',
        contradiction='No qualified100um mechanical lap,finite bend radius,barrier,adhesion or reflow sequence',
        closure='Independent dimensioned foil-foot/joint cross-section with material stack,solder fillet,bend/strain/tolerance and contactR/G bounds')
    add('v2.header_mount_joint','Hot ceramic mounting',None,'process',['PKG-01','TEC-01'],'No hot mounting solid inV2',cls='UNKNOWN',
        closure='Mount joint thickness/alloy/wetting/contact area and bath/sink mechanical connection,with source-backed bounds')
    for key in ('cap_height_above_header_m','cap_wall_thickness_m','cap_roof_thickness_m','window_diameter_m','window_thickness_m'):
        add('enclosure.'+key,'Corrected cap/window',cfg[key],'m',['PKG-01'],'accepted cap derivative '+key,
            bounds=cfg['assumed_parameter_ranges'][key],basis='PREEXISTING SCENARIO range; not manufacturer metrology',cls='SCENARIO',
            code='tecooledmct/corrected_enclosure.py',symbol='assumptions',mesh='Native standalone cap/gas fixture uses it; no V2 coupled mesh/field',
            closure='Verify section endpoints,wall/window cross-section,seals and tolerances; no optical throughput inference')
    for name,value,unit,dom,ref in [
        ('Cu_rho',1.72e-8,'ohm m','Approximately300K bulk proxy; thin-film rho(T)/contacts UNKNOWN','Existing constant-Cu verification assumption'),
        ('Cu_k',400.,'W/(m K)','Approximately300K bulk proxy; film/foil k(T) UNKNOWN','Existing constant-Cu verification assumption'),
        ('Al2O3_k',30.,'W/(m K)','Numerical90–400K proxy; real grade/tensor UNKNOWN','corrected_thermal.material'),
        ('Kovar_pin_k',17.3,'W/(m K)','Numerical90–400K proxy; actual Kovar/pin grades UNKNOWN','corrected_thermal.material'),
        ('glass_k',1.,'W/(m K)','Numerical90–400K proxy; seal composition UNKNOWN','corrected_thermal.material'),
        ('Au_k',315.,'W/(m K)','Numerical90–400K proxy; real wire metallurgy/contact UNKNOWN','corrected_thermal.material'),
        ('attach_k',1.,'W/(m K)','Numerical90–400K assumption; die attach process UNKNOWN','corrected_thermal.material'),
        ('presolder_k',35.,'W/(m K)','Numerical290–320K only; joint alloy unidentified','corrected_thermal.material')]:
        add('material.'+name,'Inherited numerical material proxy',value,unit,['PKG-01','TEC-01'],ref,cls='SCENARIO',code='tecooledmct/corrected_thermal.py',symbol='material',
            domain=dom,property_ref=ref,mesh='Archived original solidSIF; V2 geometry contains no assigned transport field',
            closure='Same-grade/orientation temperature-dependent measurements or qualified process data; bulk numerical constant is not film/current validation')
    for name,unit in [('S','V/K'),('rho','ohm m'),('k','W/(m K)')]:
        add('material.BiTe_'+name,'Zhang research P/N analog',None,unit,['RES-01'],'Measured source table reference,notV2 field',cls='INDEPENDENT_ANALOG',
            code='tecooledmct/graded_tec.py',symbol='props',property_ref='data/g2c/zhang2025_he_40_300_v2.json',
            domain=dict(specimens=['P-HE','N-HE-1'],measured_K=[40,300],active_K=[180,390],above300='Assumed0.25final-tangent continuation',matched_commercial_grade=False),
            impact='Existing28/12/4 sensitivities are conditional; noV2 prediction. A/L-rho-k degeneracy prevents grade identification',
            closure='Matched same-grade P/N S,rho,k with orientation,process and180–350K coverage,plus independent dimensions',
            sensitivity={'status':'Existing DIFFERENT baseline only','source':'docs/TEC_MATERIAL_PLAUSIBILITY_20261101.md','endpoint_temperature_span_K':{'S':14.172527,'rho':4.959973,'k':23.348849}[name],'V2_matched_target':'NOT RUN'})
    add('material.active_law_identities','Nonlinear source law',None,'functional',['RES-01'],'sigma=1/rho;Thomson=T*dS/dT',cls='PHYSICS_CONSTRAINT',
        code='tecooledmct/graded_tec.py',symbol='props',domain='Right derivative at interior knots,measured left at300K,quarter tangent above300,left limit390K',
        closure='Preserve source/sign/domain tests; independently identify real grade rather than fit it')
    add('material.MCT_composition','Detector thermal analog',.29,'mole fraction',['MAT-01','NUM-01'],'Original x=.29 thermal proxy,not measured candidate composition',
        cls='INDEPENDENT_ANALOG',code='tecooledmct/corrected_thermal.py',symbol='MCTHeat',domain='Numerical90–400K table; source DOI10.1364/AO.47.000578 Table2; NOT reinspected in this audit',
        property_ref='k(T) at90/148/298/400K=2.41/1.61/.973/.790 W/(m K)',
        closure='Actual die composition,carrier/attach construction and bias self-heating; source thermal proxy does not characterize detector electronics')
    for pid,value,unit,reason in [('cap_material',None,'grade','Steel-like analogue; no certified steel alloy'),('window_material',None,'grade','ZnSe candidate; actual Al2O3/ZnSe AR and immersion lens choice unknown'),
                                  ('contact_Re',None,'ohm m2','Electrical interface impedance UNKNOWN'),('contact_Rth',None,'m2 K/W','Thermal interface impedance UNKNOWN')]:
        add('material.'+pid,'Unqualified grade/contact',value,unit,['PKG-01','TEC-01'],reason,cls='UNKNOWN',property_ref=reason,
            closure='Independent supplier/process/measurement evidence; no ideal contact inferred from coincident CAD faces')
    for pid,value,unit,bounds,reason in [('gas_pressure',None,'Pa',None,'Device pressure/species UNKNOWN; failed native control is not device load'),
        ('gas_control_N2_pressure',101325.,'Pa',[101325.,101325.],'Standalone old flow-suppressed control only'),
        ('gas_control_k',.0259,'W/(m K)',None,'Old300K constantN2 control,not a qualified gas budget'),
        ('radiation_emissivity',None,'1',None,'Native surfaces/coatings/view factors UNKNOWN; filled-core proxy is separate'),
        ('sink_Rtheta',None,'K/W',[0.,10.],'Existing scenario interval,not measured hardware'),
        ('die_bias_heat',.002,'W',None,'Imposed scenario source,not measured detector bias')]:
        add('boundary.'+pid,'Boundary/omitted path',value,unit,['PKG-01'],reason,bounds=bounds,basis='PREEXISTING SCENARIO/control only' if bounds else 'UNKNOWN physical bound',
            cls='SCENARIO' if value is not None else 'UNKNOWN',code='tecooledmct/integrated_reference.py',symbol='Scenario',
            mesh='Original solid/old standalone gas/reduced contexts only; noV2 coupled field',
            closure='Measure matched environment and heat/current reservoirs after geometry acceptance; preserve gas32.6274%,bath1%,cold5%,side-port7.277% failures')
    profile=read('data/g2c/zhang2025_he_40_300_v2.json')
    for row in rows:
        if row['parameter_id'].startswith('enclosure.'):
            row['CAD']=dict(manifest='data/corrected_enclosure/geometry_hypothesis_v1.json',feature=row['CAD']['feature'],
                STEP='data/isolated_cap_native_gas_20261101/phase_A/cap_window_mm_derivative.step')
        if row['parameter_id'] in ('material.BiTe_S','material.BiTe_rho','material.BiTe_k'):
            key=row['parameter_id'].split('_')[-1]
            row['value_SI']={p:[{'temperature_K':pt['temperature_k'],'value_SI':pt['value_si']} for pt in profile['specimens'][p]['curves'][key]['points']] for p in ('P','N')}
            row['range_basis']='Functional source points40–300K; actual matched-grade uncertainty UNKNOWN; do not treat temperature variation as an error band'
    return dict(schema='physical-evidence-traceability-v1',review_target='e1c431caf5f6dd34e3c6d8d11737aba0ed7ac555',
        source_catalog='data/physical_geometry_audit_20261102/source_catalog.json',source_registry_is_builder_evidence=True,
        independent_release='NOT REVIEWED until separate serial audit; builder cannot clear issue2',parameters=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('New registry output required; preserve evidence')
    a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(build(),indent=2,allow_nan=False)+'\n')
