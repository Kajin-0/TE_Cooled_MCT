"""Read-only independent acceptance of V3.4 after a *completed* frozen source solve.
No FEM PDE, stage transport, source CAD modification, or fitting is performed.
"""
from pathlib import Path
import json,hashlib,math,sys
from scripts.v3_4_source_copper_multiport import evaluate,PORTS,SPEC

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/v3_4_copper_multiport_20261108/attempt03'
OLD=ROOT/'data/v3_3_cavity_package_feedback_20261108/attempt02/result.json'
OLD_SHA='a7679d0c69b1d53f9fc7b289eb8596af4bac856fa3f3d9ade83b263f998bbd58'

def audit():
    assert hashlib.sha256(OLD.read_bytes()).hexdigest()==OLD_SHA
    reg=json.loads((P/'registration.json').read_text())
    out=json.loads((P/'result.json').read_text())
    assert 'V3.4 PROVISIONAL' in out['status']
    I=reg['current_A']
    cm=out['Cu_form_tab_electrothermal_result']
    face={int(face):float(temp) for v in cm['net_details'].values()
          for face,temp in zip(v['face_tags'],v['plate_temperature_K'])}
    recompute=evaluate(I,face,
        reg['Cu_port_thermal_Rarea_m2K_W'],reg['Cu_port_electrical_Rarea_ohm_m2'])
    deviations=[]
    for net in ('58','80','88'):
        a=cm['net_details'][net]
        b=recompute['net_details'][net]
        for key in ('electric_Joule_W','electric_resistance_ohm','electric_voltage_V'):
            deviations.append(abs(a[key]-b[key]))
        deviations.extend(abs(x-y) for x,y in zip(a['face_heat_into_ceramic_W'],b['face_heat_into_ceramic_W']))
    assert max(deviations)<1e-12
    qm=out['Cu_form_tab_heat_into_ceramic_by_stage_W']
    assert all(abs(x-y)<1e-12 for x,y in zip(qm,recompute['heat_into_ceramic_by_stage_W']))
    assert abs(sum(qm)-out['Cu_form_tab_electrical_Joule_W'])<1e-12
    assert abs(out['Cu_form_tab_electrical_Joule_W']-I*I*out['Cu_form_tab_electrical_R_ohm'])<1e-12
    st=out['source_stage_thermoelectric_budget']
    PJ=out['source_solder_and_interface_energy_per_single_joint_pad_W']
    qgas=out['cavity_gas_heat_into_three_ceramics_and_die_W']
    qrad=out['gray_radiation_heat_into_three_ceramics_and_die_W']
    qext=[a+b for a,b in zip(qgas,qrad)]
    # Derive conserved stage and copper balance from published stage magnitudes,
    # not from the V3.4 solver's private residual array.
    stage1=st[0]['qc_w']-st[1]['qh_w']-80*PJ-qext[0]-qm[1]
    stage2=st[1]['qc_w']-st[2]['qh_w']-30*PJ-qext[1]-qm[2]
    stage3=st[2]['qc_w']-out['detector_bond_heat_and_bias_W']-8*PJ-qext[2]
    hot=st[0]['qh_w']+out['heat_Cu_lead_correction_W']+58*PJ+qm[0]-out['bath_heat_rejected_W']
    assert max(abs(stage1),abs(stage2),abs(stage3),abs(hot))<1e-8,(stage1,stage2,stage3,hot)
    assert abs(out['global_thermoelectric_energy_residual_W'])<1e-8
    assert out['max_last_spatial_temperature_update_K']<reg['outer_thermal_field_tolerance_K']
    assert out['max_native_plate_net_heat_imbalance_W']<5e-8
    assert out['max_separate_leg_energy_residual_W']<1e-9
    assert len(out['source_individual_leg_flux_and_electric_results'])==88
    assert out['original_ceramic_TET4']==11791
    baseline=json.loads(OLD.read_text())
    result={'verdict':'ACCEPTED: provisional source-contact copper network and full-system 88-leg/4-ceramic feedback; NOT measured hardware or 3D metal PDE',
       'source_V3_3_result_sha256':OLD_SHA,
       'source_registration_sha256':hashlib.sha256((P/'registration.json').read_bytes()).hexdigest(),
       'result_sha256':hashlib.sha256((P/'result.json').read_bytes()).hexdigest(),
       'source_copper_independent_recompute_max_abs_difference':max(deviations),
       'copper_heat_minus_electrical_work_W':float(sum(qm)-out['Cu_form_tab_electrical_Joule_W']),
       'source_stage_balance_reconstructed_W':{'stage_1':stage1,'stage_2':stage2,'detector':stage3,'hot_reservoir':hot},
       'original_V3_3_Tdie_K':baseline['calculated_detector_temperature_K'],
       'V3_4_Tdie_K':out['calculated_detector_temperature_K'],
       'difference_V3_4_minus_V3_3_K':out['calculated_detector_temperature_K']-baseline['calculated_detector_temperature_K'],
       'original_V3_3_Vterminal_V':baseline['terminal_voltage_V'],
       'V3_4_Vterminal_V':out['terminal_voltage_V'],
       'difference_terminal_V':out['terminal_voltage_V']-baseline['terminal_voltage_V'],
       'original_V3_3_Pelectric_W':baseline['electrical_power_W'],
       'V3_4_Pelectric_W':out['electrical_power_W'],
       'difference_Pelectric_W':out['electrical_power_W']-baseline['electrical_power_W'],
       'source_copper_energy_W':out['Cu_form_tab_electrical_Joule_W'],
       'source_copper_R_ohm':out['Cu_form_tab_electrical_R_ohm'],
       'source_copper_heat_into_ceramics_W':qm,
       'component_thermal_contact_R_area_m2K_W':reg['Cu_port_thermal_Rarea_m2K_W'],
       'component_electrical_contact_R_area_ohm_m2':reg['Cu_port_electrical_Rarea_ohm_m2'],
       'limitations':['Cu is temperature-dependent 1D foil multiport with assumed property and joint impedances, not true 3D field',
                      'Native plated-face sheet current/heat and solder/foil Peltier effects are excluded',
                      'Original 430-domain FEM global Gate B FAIL/STOP, C/D not run',
                      'No measured hardware comparison, no material confidence interval']}
    dest=P/'independent_read_only_acceptance.json'
    if dest.exists():
        assert json.loads(dest.read_text())==result,'INDEPENDENT_AUDIT_REPLAY_MISMATCH'
    else:
        dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':audit()
