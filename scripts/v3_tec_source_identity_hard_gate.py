#!/usr/bin/env python3
"""Original V3 CAD vs manufacturer source identity/readiness hard gate.

This source comparison DOES NOT assume VIGO's detector package contains
TEC Microsystems' 3MC04-044-05. Exact as-built assembly remains unknown.
External OEM values are manually verified public citations; locally
SHA-256 pin only source CAD and previously versioned source specification.
NO PDE, mesh or material law release.
"""
from pathlib import Path
import argparse,hashlib,json,collections
ROOT=Path(__file__).resolve().parents[1]
GEOM=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
SPEC=ROOT/'GEOMETRY_SOURCE_OF_TRUTH_SPEC.md'
EVIDENCE=ROOT/'docs/TEC_GEOMETRY_EVIDENCE_LIBRARY_20261102.md'
MAT=ROOT/'data/v3_physical_law_readiness_20261106/attempt01/law_and_subassembly_inventory.json'
PORT=ROOT/'data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json'
SOURCE_TEC='https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf'
SOURCE_VIGO='https://vigophotonics.com/app/uploads/2024/07/PCI-12-detector-series-datasheet.pdf'
SOURCE_PIN='https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf'

def read(x):return json.loads(x.read_text())
def sha(x):
 h=hashlib.sha256()
 with x.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
def generate():
 cad=read(GEOM);mat=read(MAT);ports=read(PORT)
 spec=SPEC.read_text();ev=EVIDENCE.read_text()
 assert len(cad['domains'])==430 and len(cad['faces'])==2440
 assert cad['stage_leg_counts']=={'0':58,'1':22,'2':8}
 assert ports['source_leg_articulation_count']==88
 assert ports['TEC_pin_port_face_tags']=={'pin1':2414,'pin9':2426}
 assert mat['unreleased_volume_laws']==430 and mat['unreleased_face_laws']==2440
 assert 'not proven to exist commercially' in spec
 assert '29/11/4' in ev and 'INFERRED' in ev
 assert 'does **not** establish' in ev or 'do **not** establish' in ev
 assert '3MC04-044-05' in spec
 assert 'VIGO' in spec
 assert len([d for d in cad['domains'] if 'thermistor' in d.lower()])==0
 a=cad['domains']
 assert a['pin5']['id']==394 and a['pin6']['id']==396
 sfaces=[(int(t),f) for t,f in cad['faces'].items() if f['class_']=='SOLID_SOLID']
 # Source CAD: both pins 5/6 have only their own glass solid boundary;
 # no modeled thermistor connection to the actual pin material.
 for pin in ('pin5','pin6'):
  vid=a[pin]['id']
  other=[f for _,f in sfaces if vid in f['owner_volume_ids']]
  assert len(other)==1 and other[0]['owners'][1].startswith('glass')
 assert ports['connected_conductor_component_sizes'][:4]==[389,4,4,4]
 return {
  'scientific_verdict':'STOP: source-constrained synthetic reference CAD, not a verified as-built VIGO + TEC Microsystems assembly',
  'source_checked_scope':'Manual primary-manufacturer source PDFs and pinned local docs; external PDF bytes not archived by this audit',
  'as_built_module_identification':'UNKNOWN',
  'model_authority':'SOURCE-CONSTRAINED REFERENCE DESIGN (not an OEM-verified combination)',
  'candidate_primary_tec':{
    'manufacturer':'TEC Microsystems GmbH',
    'part':'3MC04-044-05',
    'datasheet_year':2019,
    'source_url':SOURCE_TEC,
    'source_page':1,
    'conditions':'hot-side=300K, vacuum; ideal performance with stabilized hot-side temperature',
    'specified_couple_count':44,
    'stages':3,
    'deltaTmax_K_at_zero_heatload':113.0,
    'Qmax_W_at_zero_deltaT':0.5,
    'Imax_A':1.0,
    'Umax_V':3.5,
    'ACR_ohm':2.9,
    'hot_ceramic_width_mm':6.4,
    'cold_ceramic_width_mm':2.4,
    'module_height_mm':3.8,
    'manufacturing_description':'hot-extruded BiTe, nominal Al2O3 ceramics, unspecified Sn-Sb formulation, Au plated exterior ceramic faces',
    'physical_P_N_transport_curves_available':False,
    'P_N_independent_sample_grade_identified':False,
    'specific_internal_stage_couple_split_published':False,
    'ACR_is_DC_resistance':False,
    'performance_maxima_simultaneously_attainable':False,
    'as_built_VIGO_CAD_module_identity_proven':False
  },
  'separate_detector_family':{
    'manufacturer':'VIGO Photonics',
    'family':'PCI-12, 3TE-TO66 nine-pin option',
    'source_url':SOURCE_VIGO,
    'datasheet_revision':'V2.0 2026-05-06',
    'data_page_1':1,'absolute_max_rating_page':2,
    'typical_Tchip_K_at_Tambient293K':210,
    'typical_Tchip_is_absolute_maximum_or_guaranteed':False,
    'absolute_max_TEC_current_A':0.45,
    'absolute_max_TEC_voltage_V':3.6,
    '3TE_thermistor_listed':True,
    'VIGO_TEC_proprietary_build_known':False,
    'identical_to_tec_microsystems_candidate':'NOT ESTABLISHED',
    'VIGO_max_rating_applicable_as_actual_reference_CAD_safe_limit':False
  },
  'package_pin_family':{
    'source_url':SOURCE_PIN,
    'drawing':'ZTM-TO66-Z030 Rev9 2024-03-01',
    'TEC_positive_pin':1,
    'TEC_negative_pin':9,
    'detector_active_pins':[7,8],
    'specified_thermistor_pins':[5,6],
    'model_includes_thermistor_volume':False,
    'model_pin5_and_pin6_volumes':[394,396],
    'model_thermistor_material_and_R_T':'NOT PRESENT / NOT MEASURED',
    'model_detector_thermometry_feedback_qualified':False,
    'model_thermistor_omission':'As-built completeness gap; NO automatic CAD insertion without source shape and resistor calibration'
  },
  'source_cad_provenance':{
    'total_domains':430,'source_faces':2440,
    'leg_count':88,'P_count':44,'N_count':44,
    'inferred_hot_to_cold_couples':[29,11,4],
    'reference_44_couples_matches_candidate_product_total':True,
    'reference_stage_distribution_verified_by_specific_selected_TEC_OEM':False,
    'electrical_pin1_pin9_path_geometrically_verified':True,
    'as_built_TEC_series_layout_verified':False,
    'all_domains_and_faces_released':False
  },
  'cross_reference_non_equivalence':{
    'tec_ref_Imax_A':1.0,
    'vigo_reference_absolute_max_current_A':0.45,
    'reference_current_ratio_tec_over_vigo':1.0/0.45,
    'risk':'Do NOT transfer a TEC Microsystems 1A Imax to a VIGO 3TE packaged device; different manufacturers, components and performance conditions',
    'TEC_reference_no_load_theoretical_cold_K_if_Thot300K':300.-113.,
    'VIGO_reference_typical_Tchip_at_Tamb293K':210.,
    'temperatures_not_comparable_as_matched_validation':True,
    'prior_reduced_material_research_conditional_not_as_built':True,
    'no_inferred_manufacturer_approval':True
  },
  'blocking_ranked_evidence_acquisition':[
   {'priority':'P0','item':'Actual cooler/detector matched OEM part/revision and as-built stage split, leg grade, wiring and thermistor inclusion','release':'Manufacturer BOM, cross-section/X-ray and original as-built performance/part identifiers; current composite identity unknown'},
   {'priority':'P1','item':'Same-grade thermoelectric P/N transport curves','release':'S_P,N(T),rho_P,N(T),k_P,N(T), polarity, grade, range, uncertainty and independent specimen identity; 40–300K unrelated research analog not accepted as grade match'},
   {'priority':'P2','item':'Electrical + thermal contact laws and interconnects','release':'Actual solder recipe, metallization stack and interface rho_c(T), r_th(T), geometric layer thickness and uncertainty; no arbitrary constants'},
   {'priority':'P3','item':'Physical heat sink, optical/gas load and detector bias/thermistor data','release':'Independent measured source T/heat-flow, sink mounting/coupling, gas pressure, absorbed optical load, detector electrical power and thermistor R(T) / thermistor connection'},
   {'priority':'P4','item':'Independent I-V, deltaT vs current and heat-load measurements','release':'Same actual product, matching T_hot and environment, with independent holdouts; cannot calibrate all unknowns from one cold-temperature number'}
  ],
  'permitted_next_model_label':'Reference-design feasibility/sensitivity only, never as-built detector performance',
  'physical_material_law_release':'STOP',
  'model_completeness_as_built_release':'STOP',
  'full_430_domain_C_D':'NOT RUN',
  'original_P1_Gate_B':'FAIL/STOP',
  'prospective_P2_Gate_B':'STOP',
  'new_PDE_runs':0,
  'source_original_CAD_modified':False,
  'source_local_SHA256':{str(p.relative_to(ROOT)):sha(p) for p in (GEOM,SPEC,EVIDENCE,MAT,PORT)}
 }

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--out',type=Path)
 p.add_argument('--verify-only',action='store_true')
 args=p.parse_args()
 r=generate()
 if args.verify_only:
  assert args.out and args.out.is_file()
  assert json.loads(args.out.read_text())==r
 elif args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  with args.out.open('x') as f:
   json.dump(r,f,indent=2)
   f.write('\n')
 print('SOURCE_IDENTITY_HARD_GATE',r['scientific_verdict'])
 print('MODEL_MISSING_THERMISTOR',not r['package_pin_family']['model_includes_thermistor_volume'])
 print('CROSS_OEM_CURRENT_SPECS_Amps',r['cross_reference_non_equivalence']['tec_ref_Imax_A'],r['cross_reference_non_equivalence']['vigo_reference_absolute_max_current_A'])
 print('AS_BUILT_PROPERTIES',r['physical_material_law_release'])
if __name__=='__main__':main()
