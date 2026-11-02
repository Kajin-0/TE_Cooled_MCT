"""Manufacturing traceability from saved V3 design; no new physical result."""
import argparse,collections,hashlib,json
from pathlib import Path

def main(src,out):
    d=json.loads((src/'design.json').read_text());prior=json.loads(Path('data/tec_assembly_v3_20261102/source_catalog.json').read_text())
    rows=[];bom=collections.defaultdict(lambda:dict(count=0,volume_m3=0.))
    for b in d['bodies']:
        m=b['material'];bom[m]['count']+=1;bom[m]['volume_m3']+=b['volume_mm3']*1e-9
        if b['name'].startswith(('leg','solder','ceramic')):sources=['TEC-01','RMT-2008','SYN-V3-DRW'];family='Retained source-inspired module;dimensions not identified OEM internals'
        elif b['shape']=='tab' or b['name'].startswith(('tab_joint','fillet')):sources=['KRY-01','ASM-04','SYN-V3-DRW'];family='Formed tab/solder family;all detailed dimensions selected'
        elif '_plane' in b['name'] or 'finish' in b['name'] or 'underside' in b['name']:sources=['ASM-01','ASM-02','ASM-08','SYN-V3-DRW'];family='Ceramic thin-film/plated stack;custom thickness and pattern'
        elif b['name'].startswith(('det','p_Hg','sapphire','carrier')):sources=['NIST-SP40094','HAGER-1978','MB-EP29','SYN-V3-DRW'];family='Selected p-type photoconductor with hard Au bond pads;not characterized detector'
        elif b['name'].startswith('hot_mount'):sources=['ASM-03','ASM-04','SYN-V3-DRW'];family='Metallized low-temperature InSn mount family'
        elif 'attach' in b['name']:sources=['MB-EP29','SYN-V3-DRW'];family='Insulating cryogenic epoxy candidate;assembly qualification pending'
        else:sources=['PKG-01','ASM-10','SYN-V3-DRW'];family='Independent VIGO housing envelope plus synthetic internal interfaces'
        rows.append(dict(id=b['name'],value_SI=dict(bbox_m=[q*.001 for q in b['bbox_mm']],volume_m3=b['volume_mm3']*1e-9),material=m,group=b['group'],
            tolerance_ref='drawing_requirements.json;bounded selected dimensions,not supplier capability',source_ids=sources,evidence_class=family,
            implementation='tecooledmct/tec_assembly_v3.py:design/make_body',CAD='cad_02/synthetic_v3_mm.step;unique per-body SI record',mesh='NOT RUN',property_boundary_prediction='NOT RUN;no physical field assigned',
            qualification='Nominal CAD/source checks only;independent physical review pending',closure='Incoming material certificate,dimensional metrology andprocess coupon;physical review',priority='critical' if b['shape'] in ('tab','wire') or '_joint' in b['name'] else 'supporting'))
    rules={
      'dimensions_mm':{'leg':[.4,.4,.5],'ceramic_widths':[6.4,5.2,3.8,2.4],'ceramic_t':.5,'pitch':.58,'pad_width':.50,'tab_width':.30,'tab_t':.030,'tab_Rneutral':.075,'tab_Rinner':.060,'tab_joint':[.30,.20,.020],'land':[.40,.30],'finished_mount_t':.080,'die':[1,1,.200],'carrier':[1.6,1.6,.150],'epoxy_t':.020,'Cu_wire_d':.20,'Au_wire_d':.018,'pin_d':.76,'PCD':10.8},
      'independent_absolute_limits_mm':{'ceramic_t':.005,'leg_t':.005,'SnSb_t':.003,'metal_stack_total':.001,'leg_pattern_registration':.015,'pattern_location':.005,'pattern_outline':.005,'leg_width':.005,'tab_width':.010,'tab_t':.003,'tab_placement':.010,'bend_radius':.005,'tab_joint_t':.005,'fillet_width_min':.005,'fillet_width_max':.015,'foot_position':.010,'mount_t':.020,'finished_mount_flatness':.010,'carrier_t':.010,'die_t':.010,'epoxy_t':.005,'bond_loop_envelope':.150},
      'layer_limits_um':{'Ti':[.05,.10],'TiW':[.03,.07],'Cu':[12.9,14.35],'Ni':[.85,1.15],'Au':[.20,.30],'total_internal_stack':[14,16],'outer_stack':[1.5,2.5]},
      'tooling':{'thermode_footprint_mm':[.35,.25],'normal_access':'bridge land outside upper ceramic;join before cap and detector;no solder through ceramic','bond_tool':'special Au wedge tool;75C workstage;flat Ni/Au pins'},
      'classification':'Selected inspectable supplier drawing requirements,NOT measured capability;deterministic sums,no RSS',
      'sources':{'sourced_external_height_mm':[3.65,3.95],'sourced_flatness_max_um':30,'sourced_parallelism_max_um':50,'selected_finished_flatness_max_um':10},
      'process_C':{'core_SnSb_melt_about':230,'complete_TEC_conservative_limit':220,'bridge_SnBi_melt':138,'bridge_peak_selected':[155,165],'bridge_dwell_s_max':45,'global_TEC_selected_max':180,'mount_InSn_melt':117,'mount_peak_selected':[125,132],'mount_dwell_s_max':60,'epoxy_stage_selected':79.4,'epoxy_stage_hours':7,'Au_bond_workstage_selected':75},
      'open_risks':['1A current rating NOT QUALIFIED','Au dissolution/intermetallics,Ni adhesion andfoil fatigue needcoupon','No hermetic cap/window assembly process qualified;cap/window mating inherited as ideal supplied component','Detector composition,bias andcryogenic contact resistance UNKNOWN','Polyimide candidate outgassing/adhesion not qualified','P/N measured40-300K distinct specimens;300-390K continuation assumed;no new law or field','Glass/header thermal seal capability belongs tosupplier;1.3mm glassOD analyst assumption retained']}
    for r in rows:
        if r['material']=='SnBi57_43':r['material_composition_ref']='material_definitions.json:SnBi57_43;57Bi/43Sn bymass,NOT reverse'
    for n,v in [('component_registry.json',rows),('BOM.json',dict(bom)),('drawing_requirements.json',rules)]:
        p=out/n
        if p.exists():raise ValueError('Preserve existing '+n)
        p.write_text(json.dumps(v,indent=2)+'\n')
    print('Registry',len(rows),'bodies;',len(bom),'materials')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.source,a.out)
