"""Preregistered V3.20 scenario adapter; no original source or outputs mutated.

A byte-audited source transformation substitutes only the three specified
physical knobs and a converged source-state warm start. All nonlinear iterations,
ceramic solves, residuals and acceptance gates remain the V3.20 implementation.
"""
from pathlib import Path
import argparse,hashlib,json,time,types,numpy as np
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_robustness_20261110';BASE=R/'scripts/tec_height_v320_coupled.py'
SCENARIOS={
 'interstage_off':{'interstage_factor':0.,'outer_gap_m':.003,'extra_sink_K_W':0.},
 'outer_gap_1p5mm':{'interstage_factor':1.,'outer_gap_m':.0015,'extra_sink_K_W':0.},
 'sink_plus5':{'interstage_factor':1.,'outer_gap_m':.003,'extra_sink_K_W':5.},
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def transformed():
 s=BASE.read_text()
 def sub(old,new):
  nonlocal s
  assert s.count(old)==1,(old[:80],s.count(old));s=s.replace(old,new)
 sub("previous=read(ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json')", "previous=read(ROOT/'data/tec_height_coupling_20261110'/variant/'result.json')")
 sub("Rext=read(V2)['hot_external_R_without_ceramic0_K_W']", "Rext=read(V2)['hot_external_R_without_ceramic0_K_W']+CONFIG['extra_sink_K_W']")
 sub("I=reg['current_A']\n A_joint=", "I=float(previous['operating_current_A'])\n A_joint=")
 sub("reg['gas_gap_m']+2*jump", "CONFIG['outer_gap_m']+2*jump")
 sub("return np.array([interstage_gas(y[2*j],y[2*j+1],g['gap_m'],g['area_m2'],reg['gas_pressure_Pa'])['Q_W'] for j,g in enumerate(gas_spec)])", "return CONFIG['interstage_factor']*np.array([interstage_gas(y[2*j],y[2*j+1],g['gap_m'],g['area_m2'],reg['gas_pressure_Pa'])['Q_W'] for j,g in enumerate(gas_spec)])")
 sub('warm_start_I=0.4','warm_start_I=float(previous[\'operating_current_A\'])')
 sub('spatial.solve(plus_solder_into_ceramic(init_rows,warm_start_I**2*R_joint),s3,CuJoule,qcu,Qbath,Qa,',"spatial.solve(plus_solder_into_ceramic(init_rows,warm_start_I**2*R_joint,gas_W=previous['internal_interstage_gas_heat_hot_to_cold_W']),s3,CuJoule,qcu,Qbath,Qa,")
 sub("external_ceramic_W=[0.]+[a+b for a,b in zip(previous['cavity_gas_heat_into_three_ceramics_and_die_W'][:3],previous['gray_radiation_heat_into_three_ceramics_and_die_W'][:3])])", "external_ceramic_W=[0.]+[a+b for a,b in zip(previous['cavity_gas_heat_into_three_ceramics_and_die_W'][:3],previous['gray_radiation_heat_into_three_ceramics_and_die_W'][:3])],lead_face_heat_W={int(k):v for k,v in previous['source_power_lead_native_faces_W'].items()})")
 return s
def source_hash():return hashlib.sha256(transformed().encode()).hexdigest()
def run(case,variant):
 c=json.loads((D/'contract.json').read_text());assert case in SCENARIOS and variant in ('nominal','custom_060') and c['scenarios'][case]==SCENARIOS[case]
 for p,h in c['source_sha256'].items():assert sha(R/p)==h,p
 assert source_hash()==c['transformed_solver_sha256'];out=D/'cases'/case/variant;out.mkdir(parents=True,exist_ok=False)
 runtime=types.ModuleType('tec_height_v321_executed');runtime.__file__=str(BASE);runtime.CONFIG=SCENARIOS[case].copy()
 try:
  exec(compile(transformed(),str(BASE)+':v321','exec'),runtime.__dict__)
  reg=runtime.expected('copper',1.,1e-6,.4,.002,'Kr',100.)
  (out/'execution_registration.json').write_text(json.dumps({'scenario':case,'variant':variant,'configuration':SCENARIOS[case],'transformed_solver_sha256':source_hash(),'original_expected_registration':reg},indent=2)+'\n')
  result,arrays=runtime.solve(reg,variant)
  result['scenario']=case;result['scenario_configuration']=SCENARIOS[case];result['solver_source_sha256']=source_hash()
  result['external_enclosure_model']=f"effective outer gas gap {SCENARIOS[case]['outer_gap_m']} m; reduced proxy, not native cavity"
  result['model_version_vs_material_physics']='v321: paired source-height models with one registered gas or sink perturbation; source ceramics and reduced copper preserved'
  result['warm_start']='saved same-geometry V3.20 full state; all spatial fields and residuals recomputed to convergence'
  (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');np.savez_compressed(out/'ceramic_fields.npz',**arrays)
  print('V321_SUCCESS',case,variant,result['calculated_detector_temperature_K'],result['electrical_power_W'],flush=True)
 except BaseException as e:
  (out/'failure.json').write_text(json.dumps({'status':'STOP','scenario':case,'variant':variant,'error':repr(e)},indent=2)+'\n');raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--scenario',required=True,choices=SCENARIOS);p.add_argument('--variant',required=True,choices=('nominal','custom_060'));a=p.parse_args();run(a.scenario,a.variant)
