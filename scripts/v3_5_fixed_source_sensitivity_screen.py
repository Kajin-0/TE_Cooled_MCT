"""V3.5 bounded screening at the frozen V3.4 native pad field, NO coupled solve.

Distinguish fixed-field sensitivity from full nonlinear detector-temperature predictions.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from scripts.v3_4_source_copper_feedback import OriginalPlates,find_leg_contact_source
from scripts.v3_4_source_copper_multiport import evaluate as bridge_eval
from scripts.v3_5_supply_lead_boundary import evaluate as lead_eval, LEADS
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/v3_4_copper_multiport_20261108/attempt03'
BASE=ROOT/'data/v3_5_power_lead_and_copper_sensitivity_20261108'
def screen():
    legs,_=find_leg_contact_source()
    original=OriginalPlates(legs).plates[0]
    with np.load(SOURCE/'source_native_ceramics_V3_4.npz',allow_pickle=False) as d:
        t=np.array(d['ceramic0_temperature_K'])
    faces={tag:float(original['tagloads'][tag]@t) for tag in (8,36)}
    assert faces[8]>300 and faces[36]<300
    old=json.loads((SOURCE/'result.json').read_text())
    cu_t={int(face):float(T) for n in old['Cu_form_tab_electrothermal_result']['net_details'].values()
          for face,T in zip(n['face_tags'],n['plate_temperature_K'])}
    wires=[]
    for alloy in ('copper','nickel_proxy','fecral_screen'):
        for length in (0.5,1.,2.):
            q=lead_eval(faces,alloy,length)
            wires.append({'alloy':alloy,'internal_wire_routing_length_factor':length,
                'lead_total_R_ohm':q['total_R_ohm'],
                'lead_Joule_W':q['joule_W'],
                'lead_conduction_to_tec_W':q['conduction_into_ceramic_W'],
                'total_two_pad_heat_W':q['total_pad_heat_W'],
                'separate_native_pad_heat_W':{str(k):v for k,v in q['face_heats_W'].items()}})
    bridges=[]
    for rt in (0.,1e-7,1e-6,1e-5,1e-4):
        q=bridge_eval(.4,cu_t,thermal_area_resistance=rt)
        bridges.append({'r_thermal_contact_area_m2K_W':rt,
                        'original_source_Cu_heat_into_stage_mW':[1000*x for x in q['heat_into_ceramic_by_stage_W']],
                        'Cu_Joule_mW':1000*q['total_electrical_power_W']})
    output={'study':'V3.5 frozen actual source-ceramic local face temperature screen only; NO self-consistent detector temperature is inferred',
      'model_lineage':'frozen accepted V3.4 source 88-leg 4-ceramic 0.4A/300K/2mW/100Pa Kr',
      'original_source_8_36_thermal_pad_K':{str(k):v for k,v in faces.items()},
      'original_source_form_tab_face_temperatures_K':{str(k):v for k,v in cu_t.items()},
      'original_source_SHA256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
          for p in (SOURCE/'result.json',SOURCE/'source_native_ceramics_V3_4.npz')},
      'factory_wire_trim_invariant':'Only final INTERNAL route between the soldered ceramic and header pin determines this modeled TEC heat path. Extra OEM wire outside the soldered header pin is not included in L.',
      'lead_model_hypotheses':'Copper original source reference; nickel selected commercial alternative; FeCrAl Kanthal-like hypothetical only, not identified commercial material; k and rho at near-room temperature are constant proxies',
      'lead_screen':wires,'interstage_Cu_contact_screen':bridges}
    BASE.mkdir(exist_ok=True,parents=True)
    dest=BASE/'fixed_source_field_screen.json'
    if dest.exists():assert json.loads(dest.read_text())==output
    else:dest.write_text(json.dumps(output,indent=2)+'\n')
    print('SCREEN',dest,'PAD',faces)
    for row in wires:
        if row['internal_wire_routing_length_factor']==1.:
            print('LEADS',row['alloy'],'total pad mW',row['total_two_pad_heat_W']*1000,
                  'Joule mW',row['lead_Joule_W']*1000)
    for row in bridges:print('BRIDGE',row['r_thermal_contact_area_m2K_W'],
        'upper_Cu_mW',row['original_source_Cu_heat_into_stage_mW'][2])
if __name__=='__main__':screen()
