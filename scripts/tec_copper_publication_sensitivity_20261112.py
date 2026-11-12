"""Source-geometry-informed Cu interstage sensitivity cases for publication.

This does not update synthetic CAD or claim OEM-grade interfaces. Six cases
are conditional one-factor screens against the accepted V3.27 source baseline.
The original 0.50-mm/29-11-4 configuration and partial-gas model stay fixed.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import types
from datetime import datetime, timezone

import numpy as np
from scripts.tec_nominal_v327_coupled import transformed as v327_source
from scripts.tec_copper_publication_ablation_20261112 import electrical_only_copper
from tecooledmct.height_coupling_v320 import copper_eval as copper_nominal
from tecooledmct.nominal_gas_p1_coupler_v325 import SourceP1Gas
from tecooledmct.nominal_gas_visibility_v327 import die_window_exchange
from scripts.v3_4_source_copper_multiport import (
    K_CU_W_MK, copper_rho, STAGES as CU_STAGES)

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'scripts/tec_height_v320_coupled.py'
PRIOR=ROOT/'data/nominal_gas_visibility_v327_20261111'
ABL=ROOT/'data/copper_ablation_publication_20261112'
OUT=ROOT/'data/copper_sensitivity_publication_20261112'
POWER=0.5956680349614825

# All boundaries are scenario hypotheses; none is a confidence interval.
CASES={
  'k80':       dict(k_multiplier=.8,  cross_section_multiplier=1., contact_Rarea=1e-6),
  'k120':      dict(k_multiplier=1.2, cross_section_multiplier=1., contact_Rarea=1e-6),
  'contact0p1x': dict(k_multiplier=1.,  cross_section_multiplier=1., contact_Rarea=1e-7),
  'contact10x': dict(k_multiplier=1., cross_section_multiplier=1., contact_Rarea=1e-5),
  'foil80':    dict(k_multiplier=1.,  cross_section_multiplier=.8, contact_Rarea=1e-6),
  'foil120':   dict(k_multiplier=1.,  cross_section_multiplier=1.2, contact_Rarea=1e-6),
}
# The contact cases are 0.1x and 10x nominal areal thermal resistance.

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def copper_with_parameters(spec, current, faceT, thermal_Rarea, electrical_Rarea,
                           k_multiplier, cross_section_multiplier):
    """Same conservative reduced Cu axial/contact law as current V3.27.
    Scale k alone or effective foil thickness; interface pad area remains fixed.
    Correct net88 mid-foot as thermal-only, not electrical-series contact.
    """
    assert k_multiplier >= 0 and cross_section_multiplier > 0
    assert thermal_Rarea > 0 and electrical_Rarea >= 0
    assert current >= 0
    loads={int(t):0. for v in spec.values() for t in v['faces']}
    details={}
    for net,s in spec.items():
        tags=list(s['faces'])
        plate=np.array([faceT[t] for t in tags],float)
        area=s['cross_section_m2']*cross_section_multiplier
        length=np.array(s['segments_m'],float)
        conductance=K_CU_W_MK*k_multiplier*area/length
        contact_area=np.array(s['contact_area_m2'],float)
        contactG=contact_area/thermal_Rarea
        segmentR=copper_rho((plate[:-1]+plate[1:])/2)*length/area
        contactR=electrical_Rarea/contact_area
        if int(net)==88:contactR[1]=0.
        p_seg=current**2*segmentR
        p_con=current**2*contactR
        source=np.zeros(len(tags))
        source[:-1]+=.5*p_seg
        source[1:]+=.5*p_seg
        matrix=np.diag(contactG)
        for j,G in enumerate(conductance):
            matrix[j,j]+=G
            matrix[j+1,j+1]+=G
            matrix[j,j+1]-=G
            matrix[j+1,j]-=G
        foilT=np.linalg.solve(matrix,contactG*plate+source)
        heat=contactG*(foilT-plate)+p_con
        resistance=float(sum(segmentR)+sum(contactR))
        electrical_power=float(current**2*resistance)
        assert abs(sum(heat)-electrical_power)<1e-11
        for tag,q in zip(tags,heat):loads[int(tag)]+=float(q)
        details[str(net)]={
            'face_tags':tags,
            'plate_temperature_K':plate.tolist(),
            'foil_node_temperature_K':foilT.tolist(),
            'thermal_segment_conductance_W_K':conductance.tolist(),
            'segment_length_m':length.tolist(),
            'metal_electrical_segment_R_ohm':segmentR.tolist(),
            'contact_electrical_R_ohm':contactR.tolist(),
            'face_heat_into_ceramic_W':heat.tolist(),
            'electric_resistance_ohm':resistance,
            'electric_Joule_W':electrical_power,
            'electric_voltage_V':float(current*resistance),
        }
    by_stage=[float(sum(q for tag,q in loads.items() if CU_STAGES[tag]==s))
              for s in (0,1,2)]
    total=float(sum(n['electric_Joule_W'] for n in details.values()))
    assert abs(sum(by_stage)-total)<1e-11
    R=float(sum(n['electric_resistance_ohm'] for n in details.values()))
    assert abs(total-current**2*R)<1e-11
    return {
        'heat_into_face_W':loads,'net_details':details,
        'heat_into_ceramic_by_stage_W':by_stage,
        'total_electrical_power_W':total,
        'total_electrical_R_ohm':R,
    }

def source():
    base=v327_source()
    assert hashlib.sha256(base.encode()).hexdigest()==sha(PRIOR/'executed_solver.py.source')
    needle='  return copper_eval(tab_spec,current,Tface,'
    assert base.count(needle)==1
    base=base.replace(needle,'  return copper_eval_sensitivity(tab_spec,current,Tface,',1)
    # Only broaden the accepted thermal-contact registration range.
    old='assert Cu_contact_Rth in (1e-6,1e-5,1e-4)'
    assert base.count(old)==1
    base=base.replace(old,'assert Cu_contact_Rth in (1e-7,1e-6,1e-5,1e-4)',1)
    return base

def preflight():
    baseline=json.loads((PRIOR/'coupled_attempt01/result.json').read_text())
    independent=json.loads((PRIOR/'coupled_attempt01/independent_audit.json').read_text())
    ablation=json.loads((ABL/'independent_audit.json').read_text())
    assert independent['status'].startswith('PASS')
    assert ablation['status'].startswith('PASS')
    assert abs(baseline['calculated_detector_temperature_K']-218.6933026695397)<1e-8
    assert abs(ablation['nominal_minus_ablation_die_K']-7.634421834512921)<1e-8
    from tecooledmct.height_coupling_v320 import copper_specs,ORIGINAL,read
    spec=copper_specs(read(ORIGINAL))
    temps={36:303.,38:302.,74:267.,75:270.,79:265.,104:245.,105:244.}
    reference=copper_nominal(spec,.4,temps,1e-6,1e-11)
    calc=copper_with_parameters(spec,.4,temps,1e-6,1e-11,1.,1.)
    assert abs(reference['total_electrical_power_W']-calc['total_electrical_power_W'])<1e-12
    assert max(abs(reference['heat_into_face_W'][j]-calc['heat_into_face_W'][j])
               for j in reference['heat_into_face_W'])<1e-12
    zero=copper_with_parameters(spec,.4,temps,1e-6,1e-11,0.,1.)
    off=electrical_only_copper(spec,.4,temps,1e-6,1e-11)
    assert max(abs(zero['heat_into_face_W'][j]-off['heat_into_face_W'][j])
               for j in off['heat_into_face_W'])<1e-12
    assert calc['net_details']['88']['contact_electrical_R_ohm'][1] == 0.
    assert len(CASES)==6
    assert not OUT.exists(), 'Do not overwrite registered or prior attempts'
    return hashlib.sha256(source().encode()).hexdigest()

def registration(case,source_digest):
    p=CASES[case]
    return {
      'scenario':case,'sensitivity_hypothesis':p,
      'temperature_scope_K':[180,390],
      'baseline_source_sha256':sha(PRIOR/'executed_solver.py.source'),
      'baseline_result_sha256':sha(PRIOR/'coupled_attempt01/result.json'),
      'baseline_audit_sha256':sha(PRIOR/'coupled_attempt01/independent_audit.json'),
      'copper_off_audit_sha256':sha(ABL/'independent_audit.json'),
      'variant':'ORIGINAL_0p50_MM_ONLY',
      'matched_terminal_input_W':POWER,
      'bath_K':300.,
      'Kr_Pa':100.,
      'accommodation':.8,
      'imposed_die_heat_W':.002,
      'thermal_conductivity_W_mK':385*p['k_multiplier'],
      'effective_copper_foil_thickness_um':30*p['cross_section_multiplier'],
      'copper_to_ceramic_areal_thermal_R_m2K_W':p['contact_Rarea'],
      'note':'CAD and contact pad area held at baseline; foil cases change only effective Cu cross-section, hence both Cu electrical R and thermal conductance.',
      'not_uncertainty':'Hypothetical one-factor endpoints, not measured manufacturing tolerances or probability bounds.',
      'gas_limit':'V3.27 partial source-mapped subset; all other gas faces adiabatic.',
      'P_N_limit':'Research constitutive laws; no measured OEM-grade transport data.',
      'source_sha256':source_digest,
      'wrapper_sha256':sha(__file__),
      'recovery':'Each case uses its own immutable output directory; a failed case stops the campaign.'
    }

def run(case):
    assert case in CASES
    assert OUT.exists()
    dst=OUT/case
    assert not dst.exists()
    dst.mkdir()
    raw=source()
    ssha=hashlib.sha256(raw.encode()).hexdigest()
    (dst/'registration.json').write_text(json.dumps(registration(case,ssha),indent=2)+'\n')
    (dst/'executed_solver.py.source').write_text(raw)
    try:
        p=CASES[case]
        gas=json.loads((ROOT/'data/nominal_gas_p1_20261111/p1_operator.json').read_text())
        vis=json.loads((PRIOR/'die_window_visibility.json').read_text())
        runtime=types.ModuleType('copper_sensitivity_'+case)
        runtime.__file__=str(BASE)
        runtime.SourceP1Gas=SourceP1Gas
        runtime.GAS_PAIRS=gas['pairs']
        runtime.die_window_exchange=die_window_exchange
        runtime.DIE_WINDOW_AREA_MM2=vis['paired_area_mm2']
        runtime.DIE_WINDOW_GAP_M=vis['gap_mm']*1e-3
        runtime.copper_eval_sensitivity=lambda spec,I,Tface,thermal_Rarea,electrical_Rarea: copper_with_parameters(
            spec,I,Tface,thermal_Rarea,electrical_Rarea,
            p['k_multiplier'],p['cross_section_multiplier'])
        exec(compile(raw,str(BASE)+':'+case,'exec'),runtime.__dict__)
        reg=runtime.expected('copper',1.,p['contact_Rarea'],.4,.002,'Kr',100.)
        result,fields=runtime.solve(reg,'nominal')
        result['status']='CONDITIONAL source-Cu one-factor sensitivity; no calibrated hardware'
        result['study_case']=case
        result['publication_sensitivity_hypothesis']=p
        result['effective_foil_thickness_um']=30*p['cross_section_multiplier']
        result['effective_Cu_k_W_mK']=385*p['k_multiplier']
        result['source_copper_model_scope']='Native CAD UNMODIFIED; reduced 1D Cu law only'
        result['solver_source_sha256']=ssha
        result['publication_wrapper_sha256']=sha(__file__)
        result['published_model_comparison']='V3.27 partial cavity; matched electrical input power'
        (dst/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        np.savez_compressed(dst/'ceramic_fields.npz',**fields)
        print('CASE_CONVERGED',case,
              result['calculated_detector_temperature_K'],
              result['electrical_power_W'],
              result['Cu_form_tab_heat_into_ceramic_by_stage_W'][2],flush=True)
    except BaseException as e:
        (dst/'failure.json').write_text(json.dumps(
            {'case':case,'status':'STOP','error':repr(e)},indent=2)+'\n')
        raise

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--preflight',action='store_true')
    a.add_argument('--init',action='store_true')
    a.add_argument('--case',choices=tuple(CASES))
    args=a.parse_args()
    assert sum([bool(args.preflight),bool(args.init),bool(args.case)])==1
    if args.preflight:
        print('PREFLIGHT_PASS',preflight(),json.dumps(CASES,sort_keys=True))
        return
    if args.init:
        ssha=preflight()
        OUT.mkdir()
        (OUT/'campaign_registration.json').write_text(json.dumps({
            'status':'REGISTERED; NOT VALIDATED',
            'registered_UTC':datetime.now(timezone.utc).isoformat(),
            'cases':CASES,'run_order':list(CASES),
            'source_sha256':ssha,
            'source_repository_commit':'ab92c4c3a8b023dd09363473693961ad83aa0b83',
            'publication_gate':'All six cases independently audited PASS',
            'no_full_3d_metal':'3D source metal Gate B FAIL/STOP',
            'no_full_cavity':'3.45424% registered gas-facing area covered in V3.27'
        },indent=2)+'\n')
        print('CAMPAIGN_REGISTERED',OUT)
        return
    run(args.case)

if __name__=='__main__':main()
