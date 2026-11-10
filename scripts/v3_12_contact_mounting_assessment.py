"""V3.12: sourced, no-PDE conductor/contact and mounting assessment.

All complete-system temperatures are read from previously accepted archives;
all new thermal-contact screens retain the archived ceramic face temperatures.
This does NOT predict a newly coupled device temperature for a hypothetical solder.
"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/v3_12_contact_mounting_assessment_20261109'
REPORT=ROOT/'reports/current/figures'
V35=ROOT/'data/v3_5_power_lead_and_copper_sensitivity_20261108'
V38=ROOT/'data/v3_8_rev3_transport_and_sink_20261109'
V311=ROOT/'data/v3_11_rev3_backfill_source_20261109'
CURRENT=0.400
AREAL_NOMINAL=1e-6
CONTACT_AREA=0.06e-6
K_SNSB=28.0 # 300 K Indium Corporation Indalloy 133 reference; not measurement on source device
K_SAC305=61.0 # Indium Corporation SAC305 300 K reference; counterfactual alloy only
SOURCE_URL_SNSB='https://scp.indium.com/download-files/solder_thermal_interface_materials_98049_r1.pdf'
SOURCE_URL_SAC='https://documents.indium.com/qdynamo/download.php?docid=5418'

def data(file):
    p=ROOT/file
    assert p.is_file(),p
    return json.loads(p.read_text())

def checked(folder):
    p=ROOT/folder
    d=json.loads((p/'result.json').read_text())
    a=json.loads((p/'independent_energy_audit.json').read_text())
    assert a['verdict'].startswith('PASS'),(folder,a.get('verdict'))
    assert hashlib.sha256((p/'result.json').read_bytes()).hexdigest()==a['result_sha256']
    assert abs(a['global_energy_residual_W']) < 1e-8
    return d

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    nominal=checked('data/v3_5_power_lead_and_copper_sensitivity_20261108/copper_native_pad')
    high=checked('data/v3_5_power_lead_and_copper_sensitivity_20261108/high_interstage_contact_R')
    gas=checked('data/v3_11_rev3_backfill_source_20261109/Kr100_I040')
    mount_cases={name:checked('data/v3_8_rev3_transport_and_sink_20261109/'+name)
        for name in ['base_I040','sink_plus05_I040','sink_plus10_I040',
                     'sink_plus05_matched_refined','sink_plus10_matched_refined']}
    assert abs(nominal['calculated_detector_temperature_K']-gas['calculated_detector_temperature_K'])<1e-10
    # Source-CAD actual geometry and native-face thermal operating point.
    sys.path.insert(0,str(ROOT))
    from scripts.v3_4_source_copper_multiport import SPEC, evaluate
    tags={}
    for v in nominal['Cu_form_tab_electrothermal_result']['net_details'].values():
        for tag,t in zip(v['face_tags'],v['plate_temperature_K']):
            assert tag not in tags
            tags[tag]=t
    base=evaluate(CURRENT,tags,AREAL_NOMINAL)
    archived=nominal['Cu_form_tab_electrothermal_result']
    assert abs(base['total_electrical_power_W']-archived['total_electrical_power_W'])<1e-12
    assert np.max(np.abs(np.array(base['heat_into_ceramic_by_stage_W'])-
                         np.array(nominal['Cu_form_tab_heat_into_ceramic_by_stage_W'])))<1e-12
    assert sum(x['electric_Joule_W'] for x in archived['net_details'].values())==archived['total_electrical_power_W'] or abs(sum(x['electric_Joule_W'] for x in archived['net_details'].values())-archived['total_electrical_power_W'])<1e-12
    assert [round(SPEC[i]['contact_area_m2'][0]/1e-6,6) for i in [58,80,88]]==[.06,.06,.06]
    assert all(abs(SPEC[i]['cross_section_m2']-9e-9)<1e-20 for i in [58,80,88])
    # Thin dense homogeneous bondline: R''=t/k. This assumes full area, no IMC
    # or voids, no finite lateral ceramic/film spreading, and no mechanical flaw.
    cases=[]
    for alloy,k in [('Sn95Sb5',K_SNSB),('SAC305 counterfactual',K_SAC305)]:
        for thickness_um in (20,25,35):
            areal=thickness_um*1e-6/k
            result=evaluate(CURRENT,tags,areal)
            upper=result['heat_into_ceramic_by_stage_W'][2]
            cases.append(dict(alloy=alloy,k_bulk_300K_W_mK=k,
                assumed_bondline_thickness_um=thickness_um,
                bulk_only_Rarea_m2K_W=areal,
                single_contact_R_K_W=areal/CONTACT_AREA,
                fixed_field_upper_Cu_heat_mW=upper*1e3,
                fixed_field_upper_Cu_delta_vs_nominal_mW=1e3*(upper-base['heat_into_ceramic_by_stage_W'][2]),
                fixed_field_copper_Joule_mW=1e3*result['total_electrical_power_W']))
    nominal_equiv_um=AREAL_NOMINAL*K_SNSB*1e6
    extreme_equiv_um=1e-4*K_SNSB*1e6
    mount=[]
    ref=mount_cases['base_I040']
    for name in ['base_I040','sink_plus05_I040','sink_plus10_I040',
                  'sink_plus05_matched_refined','sink_plus10_matched_refined']:
        d=mount_cases[name]
        item=dict(case=name,detector_T_K=d['calculated_detector_temperature_K'],
            current_A=d['operating_current_A'],input_W=d['electrical_power_W'],
            delta_T_vs_baseline_K=d['calculated_detector_temperature_K']-ref['calculated_detector_temperature_K'],
            extra_power_vs_baseline_percent=100*(d['electrical_power_W']/ref['electrical_power_W']-1))
        mount.append(item)
    assert abs(ref['calculated_detector_temperature_K']-nominal['calculated_detector_temperature_K'])<1e-9
    q_upper=1e3*nominal['Cu_form_tab_heat_into_ceramic_by_stage_W'][2]
    q_gas=1e3*sum(nominal['cavity_gas_heat_into_three_ceramics_and_die_W'])
    q_rad=1e3*sum(nominal['gray_radiation_heat_into_three_ceramics_and_die_W'])
    lead=nominal['source_tec_power_leads']['face_heats_W']
    component={'Cu_net_58_mW':1e3*archived['net_details']['58']['face_heat_into_ceramic_W'][-1],
        'Cu_net_80_upper_mW':1e3*archived['net_details']['80']['face_heat_into_ceramic_W'][-1],
        'Cu_net_88_upper_mW':1e3*archived['net_details']['88']['face_heat_into_ceramic_W'][-1],
        'Cu_net_88_middle_mW':1e3*archived['net_details']['88']['face_heat_into_ceramic_W'][1],
        'Cu_into_hot_ceramic_mW':1e3*nominal['Cu_form_tab_heat_into_ceramic_by_stage_W'][0],
        'Cu_into_middle_ceramic_mW':1e3*nominal['Cu_form_tab_heat_into_ceramic_by_stage_W'][1],
        'Cu_into_upper_ceramic_mW':q_upper,
        'Cu_total_Joule_mW':1e3*nominal['Cu_form_tab_electrical_Joule_W'],
        'Cu_total_electrical_R_ohm':nominal['Cu_form_tab_electrical_R_ohm'],
        'pin1_into_ceramic_mW':1e3*lead['8'],
        'pin9_into_ceramic_mW':1e3*lead['36'],
        'two_leads_net_into_ceramic_mW':1e3*sum(lead.values()),
        'two_leads_Joule_mW':1e3*nominal['source_tec_power_leads']['joule_W'],
        'gas_total_into_four_branches_mW':q_gas,
        'radiation_total_into_four_branches_mW':q_rad,
        'TEC_stage3_cold_leg_heat_lift_mW':1e3*nominal['source_stage_thermoelectric_budget'][2]['qc_w'],
        'detector_imposed_external_heat_mW':2.0,
        'TEC_input_W':nominal['electrical_power_W'],
        'die_temperature_K':nominal['calculated_detector_temperature_K']}
    assert abs(sum(nominal['Cu_form_tab_heat_into_ceramic_by_stage_W'])-nominal['Cu_form_tab_electrical_Joule_W'])<1e-11
    assert abs(component['Cu_net_80_upper_mW']+component['Cu_net_88_upper_mW']-q_upper)<1e-9
    output={'scope':'Source CAD + frozen-state conductor/mount screen; no newly coupled temperature predictions',
      'model':'29/11/4 couples, 88 legs, 300 K reservoir, 0.400 A, 100 Pa Kr, 2 mW externally imposed die heat',
      'nominal_interface_Rarea_m2K_W':AREAL_NOMINAL,
      'high_hypothetical_Rarea_m2K_W':1e-4,
      'joint_contact_area_m2':CONTACT_AREA,
      'Cu_foil_cross_section_m2':9e-9,
      'source_solder_design_identity':'95Sn5Sb synthetic source design only; actual OEM alloy unknown',
      'solder_reference_properties':{'Sn95Sb5_k_300K_W_mK':K_SNSB,'SAC305_k_W_mK':K_SAC305,
                                    'sources':[SOURCE_URL_SNSB,SOURCE_URL_SAC]},
      'joint_nominal_equivalent_SnSb_bulk_thickness_um':nominal_equiv_um,
      'joint_high_hypothesis_equivalent_SnSb_bulk_thickness_um':extreme_equiv_um,
      'source_component_budget':component,
      'fixed_ceramic_face_hypotheses':cases,
      'accepted_mounting_cases':mount,
      'fully_coupled_extreme_contact_comparison':{'nominal_T_K':nominal['calculated_detector_temperature_K'],
             'extreme_hypothesis_T_K':high['calculated_detector_temperature_K'],
             'delta_T_K':high['calculated_detector_temperature_K']-nominal['calculated_detector_temperature_K'],
             'extreme_interface_not_build_recommendation':True},
      'limitations':['Manufacturer bulk k at 300K not qualified over whole cooler temperature range',
         'No measured as-built solder thickness, wetting fraction, intermetallic layer or plated spreading',
         'Static copper face temperatures for all six bulk-bondline screens; no new FEM',
         'Extreme contact full solve is an intentionally unphysical limiting hypothesis',
         'Mounting cases derive from original V3.8 with provisional HgCdTe Joule proxy, unlike fixed 2mW V3.5; reference matches but off-baseline load responds differently'],
      'input_hashes_sha256':{},'output_plot_sha256':{}}
    paths=[V35/'copper_native_pad/result.json',V35/'copper_native_pad/independent_energy_audit.json',
       V35/'high_interstage_contact_R/result.json',V35/'high_interstage_contact_R/independent_energy_audit.json',
       V311/'Kr100_I040/result.json',V311/'Kr100_I040/independent_energy_audit.json',
       ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json',
       ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json',
       ROOT/'data/synthetic_v3_assembly_20261102/conductor_geometry_coefficients.json']
    for name in mount_cases:
        paths.extend([V38/name/'result.json',V38/name/'independent_energy_audit.json'])
    output['input_hashes_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    # Clearly separate true solved components from hypothetical fixed-field conductance.
    fig=plt.figure(figsize=(9.1,4.2),facecolor='white')
    ax=fig.add_axes([.13,.29,.74,.54])
    labels=['Hot ceramic','Middle ceramic','Upper ceramic']
    signed=[component['Cu_into_hot_ceramic_mW'],component['Cu_into_middle_ceramic_mW'],q_upper]
    y=np.arange(3)
    ax.barh(y,signed,color=['#6285a2','#dca064','#ba744a'],height=.52)
    ax.set_yticks(y,labels);ax.invert_yaxis()
    ax.set_xlim(-133,115)
    ax.axvline(0,color='#334455',lw=1)
    for yi,v in zip(y,signed):
        # Place both long signed labels INSIDE their bars, avoiding overlap
        # with the physical stage labels and the figure's right boundary.
        if v < 0 or v > 55:
            tx = -3 if v < 0 else 5
            ha = 'right' if v < 0 else 'left'
            fg = 'white'
        else:
            tx,ha,fg = v+4,'left','#24384d'
        ax.text(tx,yi,f'{v:+.2f} mW',va='center',ha=ha,
                color=fg,fontsize=10,fontweight='bold')
    ax.set_xlabel('Net formed-Cu heat into ceramic (mW; positive = heating)')
    ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    fig.text(.055,.947,'Native formed-Cu network redistributes heat across TEC stages',
             fontsize=14,weight='bold',color='#24384d')
    fig.text(.055,.885,'Accepted 0.400 A / 300 K / 100 Pa Kr source solution; all three nets and contacts included',
             fontsize=9,color='#54667b')
    fig.text(.055,.075,'The signed total equals +2.082 mW copper Joule heat. The ~87 mW cold-stage input is NOT additional electrical power.',
             fontsize=8.5,color='#54667b')
    figs=[]
    for suffix in ['pdf','png']:
        target=REPORT/f'v312_source_copper_heat_ledger.{suffix}'
        kw={'metadata':{'CreationDate':None,'ModDate':None,'Creator':'V3.12 source heat ledger'}} if suffix=='pdf' else {'dpi':180}
        fig.savefig(target,bbox_inches='tight',**kw)
        figs.append(target)
    plt.close(fig)
    fig=plt.figure(figsize=(9.1,4.5),facecolor='white')
    ax=fig.add_axes([.13,.27,.76,.59])
    for alloy,color,mark in [('Sn95Sb5','#2c6685','o'),('SAC305 counterfactual','#b97950','s')]:
        rows=[r for r in cases if r['alloy']==alloy]
        ax.plot([r['assumed_bondline_thickness_um'] for r in rows],
                [r['fixed_field_upper_Cu_heat_mW'] for r in rows],mark+'-',color=color,
                label=alloy,markersize=7,lw=1.7)
    ax.axhline(q_upper,color='#5d6f83',ls='--',lw=1.3,label='Existing nominal source contact assumption')
    ax.set_xlim(18,37)
    ax.set_xticks([20,25,35]);ax.set_xlabel('Assumed fully dense solder thickness (µm)')
    ax.set_ylabel('Fixed-field Cu heat into upper ceramic (mW)')
    ax.grid(alpha=.18);ax.legend(frameon=False,fontsize=9,loc='best')
    fig.text(.06,.951,'Solder bondline screening against the nominal contact assumption',
             fontsize=13.8,weight='bold',color='#24384d')
    fig.text(.06,.898,'Native Cu network, frozen source face temperatures, constant reference 300 K solder k',
             fontsize=9,color='#54667b')
    fig.text(.06,.065,'Source alloy is Sn95Sb5; SAC305 is comparison only. No coupled new detector temperatures are inferred.',
             fontsize=8.5,color='#54667b')
    for suffix in ['pdf','png']:
        target=REPORT/f'v312_solder_contact_fixed_field_screen.{suffix}'
        kw={'metadata':{'CreationDate':None,'ModDate':None,'Creator':'V3.12 source contact screen'}} if suffix=='pdf' else {'dpi':180}
        fig.savefig(target,bbox_inches='tight',**kw)
        figs.append(target)
    plt.close(fig)
    output['output_plot_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in figs}
    (OUT/'assessment.json').write_text(json.dumps(output,indent=2)+'\n')
    print('NOMINAL_SNSB_UM',nominal_equiv_um,'HIGH_EQUIVALENT_UM',extreme_equiv_um)
    print('COMPONENT',json.dumps(component,indent=2))
    print('FIXED_FIELD CASES',json.dumps(cases,indent=2))
    print('MOUNTING',json.dumps(mount,indent=2))
    print('OUTPUT',OUT/'assessment.json')

if __name__=='__main__':main()
