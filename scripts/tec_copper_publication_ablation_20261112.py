"""Controlled thermal-conduction ablation of source Cu interstage links.

Original 0.50-mm TEC only. Matched terminal power, unchanged electrical
resistance/Joule heat and corrected net88 electrical topology. This is a
diagnostic nonphysical control, NOT a disconnected or manufacturable circuit.
Uses V3.27's partial source-gas operator; other gas faces remain adiabatic.
"""
from pathlib import Path
import argparse, hashlib, json, types
import numpy as np
from scripts.tec_nominal_v327_coupled import transformed as v327_source
from tecooledmct.nominal_gas_p1_coupler_v325 import SourceP1Gas
from tecooledmct.nominal_gas_visibility_v327 import die_window_exchange
from tecooledmct.height_coupling_v320 import copper_eval as copper_full
from scripts.v3_4_source_copper_multiport import STAGES as COPPER_STAGES

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT/'data/nominal_gas_visibility_v327_20261111'
OUT = ROOT/'data/copper_ablation_publication_20261112'
BASE = ROOT/'scripts/tec_height_v320_coupled.py'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def electrical_only_copper(spec, current, face_temperature, thermal_Rarea, electrical_Rarea):
    """Suppress passive Cu thermal conductance only. Keep all metal R and I^2R.

    Segment Joule heat is split equally between its adjacent landed nodes;
    contact Joule heat is deposited at the electrical contacts. This is the
    G->0 limit of the declared axial Cu model, not a physical replacement.
    """
    full = copper_full(spec, current, face_temperature,
                       thermal_Rarea=thermal_Rarea, electrical_Rarea=electrical_Rarea)
    faces = {}; details = {}; stage = [0., 0., 0.]
    for net, d in full['net_details'].items():
        tags = [int(x) for x in d['face_tags']]
        rseg = np.array(d['metal_electrical_segment_R_ohm'], dtype=float)
        rcontact = np.array(d['contact_electrical_R_ohm'], dtype=float)
        joule = current*current*rseg
        q = current*current*rcontact
        q = q.copy()
        q[:-1] += 0.5*joule
        q[1:] += 0.5*joule
        assert abs(float(q.sum())-d['electric_Joule_W']) < 1e-12
        for face, val in zip(tags, q):
            faces[face] = float(val)
            stage[COPPER_STAGES[face]] += float(val)
        details[net] = dict(d,
            foil_node_temperature_K=d['plate_temperature_K'],
            thermal_segment_conductance_W_K=[0.]*len(rseg),
            face_heat_into_ceramic_W=q.tolist())
    total = full['total_electrical_power_W']
    assert abs(sum(stage)-total)<1e-12
    assert abs(total-current**2*full['total_electrical_R_ohm'])<1e-12
    return dict(heat_into_face_W=faces, net_details=details,
                heat_into_ceramic_by_stage_W=stage,
                total_electrical_power_W=total,
                total_electrical_R_ohm=full['total_electrical_R_ohm'])

def sealed_source():
    base = v327_source()
    assert hashlib.sha256(base.encode()).hexdigest() == sha(PRIOR/'executed_solver.py.source')
    needle = '  return copper_eval(tab_spec,current,Tface,'
    assert base.count(needle)==1
    edited = base.replace(needle,'  return copper_eval_ablation(tab_spec,current,Tface,',1)
    return edited

def preflight():
    assert json.loads((PRIOR/'coupled_attempt01/independent_audit.json').read_text())['status'].startswith('PASS')
    baseline=json.loads((PRIOR/'coupled_attempt01/result.json').read_text())
    assert abs(baseline['calculated_detector_temperature_K']-218.6933026695397)<1e-8
    assert baseline['Cu_net88_middle_electrical_contact'].startswith('removed')
    src=sealed_source(); source_hash=hashlib.sha256(src.encode()).hexdigest()
    # No-conduction electric/Joule checks, including the middle thermal-only foot.
    from tecooledmct.height_coupling_v320 import copper_specs,read,ORIGINAL
    spec=copper_specs(read(ORIGINAL))
    t={36:303.,38:302.,74:267.,75:270.,79:265.,104:245.,105:244.}
    v=electrical_only_copper(spec,.4,t,1e-6,1e-11)
    w=copper_full(spec,.4,t,thermal_Rarea=1e-6,electrical_Rarea=1e-11)
    assert abs(v['total_electrical_power_W']-w['total_electrical_power_W'])<1e-14
    assert v['net_details']['88']['contact_electrical_R_ohm'][1] == 0
    assert all(q>=0 for q in v['heat_into_face_W'].values())
    assert any(q<0 for q in w['heat_into_face_W'].values())
    return source_hash,baseline

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--preflight',action='store_true')
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    assert a.preflight != a.run
    source_hash,baseline=preflight()
    if a.preflight:
        print(json.dumps(dict(status='PREFLIGHT_PASS',baseline_K=baseline['calculated_detector_temperature_K'],
                              baseline_power_W=baseline['electrical_power_W'],
                              ablation_source_sha256=source_hash),indent=2))
        return
    assert not OUT.exists(), 'Output already exists; preserve all prior attempts'
    OUT.mkdir(parents=True)
    raw = sealed_source()
    registration = {
      'experiment':'Zero passive heat flow through Cu 58, 80, 88',
      'interpretation':'Mathematical ablation only; thermal conduction off, electrical conduction and Joule unchanged',
      'model':'V3.27 source-derived partial cavity, NOT complete gas/hardware model',
      'matched_terminal_input_W':0.5956680349614825,
      '300K_bath_K':300.,'Kr_pressure_Pa':100.,'alpha':.8,
      'detector_heat_W':.002,'original_pellet_height_mm':.5,
      'baseline_result_sha256':sha(PRIOR/'coupled_attempt01/result.json'),
      'baseline_audit_sha256':sha(PRIOR/'coupled_attempt01/independent_audit.json'),
      'base_v327_source_sha256':sha(PRIOR/'executed_solver.py.source'),
      'new_executed_source_sha256':source_hash,
      'ablation_wrapper_sha256':sha(__file__),
      'numerical_status':'NOT STARTED', 'release_condition':'independent audit required'
    }
    (OUT/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
    (OUT/'executed_solver.py.source').write_text(raw)
    try:
        gas=json.loads((ROOT/'data/nominal_gas_p1_20261111/p1_operator.json').read_text())
        vis=json.loads((PRIOR/'die_window_visibility.json').read_text())
        runtime=types.ModuleType('copper_ablation_executed')
        runtime.__file__=str(BASE)
        runtime.SourceP1Gas=SourceP1Gas;runtime.GAS_PAIRS=gas['pairs']
        runtime.die_window_exchange=die_window_exchange
        runtime.DIE_WINDOW_AREA_MM2=vis['paired_area_mm2']
        runtime.DIE_WINDOW_GAP_M=vis['gap_mm']*1e-3
        runtime.copper_eval_ablation=electrical_only_copper
        exec(compile(raw,str(BASE)+':copper_thermal_off','exec'),runtime.__dict__)
        reg=runtime.expected('copper',1.,1e-6,.4,.002,'Kr',100.)
        result,fields=runtime.solve(reg,'nominal')
        result['status']='CONDITIONAL zero-Cu-thermal-conduction ablation: original 0.5-mm model, electrically intact Cu; not physical build'
        result['Cu_interstage_passive_conduction']='OFF for diagnostic; Cu electrical R and I^2R retained'
        result['ablation_executed_source_sha256']=source_hash
        result['ablation_code_sha256']=sha(__file__)
        result['baseline_result_sha256']=registration['baseline_result_sha256']
        result['solver_source_sha256']=source_hash
        result['comparison_nominal_V327_delta_die_K']=result['calculated_detector_temperature_K']-baseline['calculated_detector_temperature_K']
        (OUT/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        np.savez_compressed(OUT/'ceramic_fields.npz',**fields)
        print('ABLATION_CONVERGED',result['calculated_detector_temperature_K'],
              result['electrical_power_W'],
              result['comparison_nominal_V327_delta_die_K'],flush=True)
    except BaseException as e:
        (OUT/'failure.json').write_text(json.dumps(dict(status='STOP',error=repr(e)),indent=2)+'\n')
        raise

if __name__=='__main__':main()
