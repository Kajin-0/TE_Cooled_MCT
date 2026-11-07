#!/usr/bin/env python3
"""One bounded 29/11/4 CAD-derived, five-node nonlinear 1D TEC sensitivity study.
Conditional unmatched research P/N laws only. NEVER a 3D or OEM validation.
"""
from pathlib import Path
import argparse,hashlib,json,time,resource,signal
from tecooledmct.integrated_reference import Scenario,solve
from tecooledmct.tec_material_plausibility import HYPOTHESES

ROOT=Path(__file__).resolve().parents[1]
FILES=[
 'data/synthetic_v3_assembly_20261102/source_final/design.json',
 'data/v3_r32_global_surface_20261103/source_metadata.json',
 'data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json',
 'data/tec_material_plausibility_20261101/properties.json',
 'data/v3_tec_source_identity_20261107/attempt01/source_identity_gate.json',
 'data/g2c/zhang2025_he_40_300_v2.json',
 'tecooledmct/integrated_reference.py',
 'tecooledmct/nonlinear_tec.py',
 'tecooledmct/graded_tec.py',
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def geometry():
 d=read(ROOT/FILES[0]);native=read(ROOT/FILES[1])
 port=read(ROOT/FILES[2]);prop=read(ROOT/FILES[3]);identity=read(ROOT/FILES[4])
 assert len(native['domains'])==430 and native['stage_leg_counts']=={'0':58,'1':22,'2':8}
 assert port['source_leg_articulation_count']==88
 assert identity['as_built_module_identification']=='UNKNOWN'
 assert prop['source']['measured_K']==[40.,300.]
 body={v['name']:v for v in d['bodies']}
 stages=[]
 for st,n in enumerate((29,11,4)):
  legs=[x for x in d['bodies'] if x['material'] in ('P','N') and x.get('stage')==st]
  assert len(legs)==2*n
  ref=legs[0]['boxes_mm'][0];L=ref[5]*1e-3;A=ref[3]*ref[4]*1e-6
  assert all(abs(x['boxes_mm'][0][5]*1e-3-L)<1e-15 and
             abs(x['boxes_mm'][0][3]*x['boxes_mm'][0][4]*1e-6-A)<1e-15 for x in legs)
  assert abs(L-0.0005)<1e-15 and abs(A-1.6e-7)<1e-17
  stages.append({'couples':n,'leg_length_m':L,'leg_area_m2':A})
 plates=[body[f'ceramic{i}']['boxes_mm'][0] for i in range(4)]
 assert [x[3] for x in plates]==[6.4,5.2,3.8,2.4]
 attach=body['die_attach_EP29LPSP']['boxes_mm'][0]
 die=body['p_HgCdTe_photoconductor']['boxes_mm'][0]
 assert attach[3:6]==[1,1,.02] and die[3:5]==[1,1]
 return {'stages':stages,
   'ceramic_sides_area_m2':[x[3]*x[4]*1e-6 for x in plates],
   'die_area_m2':die[3]*die[4]*1e-6,
   'die_attach_thickness_over_area_m_inverse':attach[5]*1e-3/(attach[3]*attach[4]*1e-6),
   'wires':[],
   'source_sha256':{f:sha(ROOT/f) for f in FILES},
   'source_archive':FILES[0],
   'material_status':'unmatched research P/N analog not production grade'}
def spec():
 return {'version':'R3 29/11/4 source-CAD conditional 1D nine-case benchmark',
  'baseline_commit':'52fc1d9c7f200d087503a099b2df7442e98b34c0',
  'method':'unchanged nonlinear_tec direct 1D 32 midpoint intervals + five-node cascade',
  'material_hypotheses':HYPOTHESES,
  'currents_A':[.15,.25,.4],
  'hot_side_K':300.,'sink_R_K_per_W':0.,'die_load_W':.002,
  'external_wires':'OFF','gas':'OFF','radiation':'OFF','unknown_stage_bypass':'ZERO, OPTIMISTIC',
  'die_attach_conductivity_W_per_mK':1.,
  'source_transport_measured_domain_K':[40,300],
  'allow_assumed_gt300K':False,
  'acceptance':'node balance<1e-8W, each stage energy <1e-9W, global energy <1e-8W, all leg temperatures <=300K and >=40K',
  'per_case_seconds':12,'total_seconds':150,'max_cpu':4,'max_RAM_GiB':6,
  'no_new_3D_FEM':True,'no_OEM_or_grade_match':True,
  'source_sha256':{f:sha(ROOT/f) for f in FILES}}
def evaluate(out):
 s=spec();reg=read(out/'registration.json')
 assert reg['source_sha256']==s['source_sha256']
 assert reg['source_script_sha256']==sha(Path(__file__))
 geo=geometry();record=[];tic=time.monotonic()
 def alarm(sig,frame):raise TimeoutError('Preregistered reduced-case timeout')
 old=signal.signal(signal.SIGALRM,alarm)
 try:
  for name,scales in HYPOTHESES.items():
   for I in (.15,.25,.4):
    case={'hypothesis':name,'current_A':I,'scales_S_rho_k':list(scales)}
    if time.monotonic()-tic>150:
     case.update(status='NOT RUN',reason='Budget exhausted')
     record.append(case);continue
    a=Scenario(ambient_k=300.,current_a=I,material_model='zhang2025_nonlinear',
      heat_sink_k_w=0.,detector_bias_w=.002,detector_absorbed_w=0.,
      cavity_pressure_pa=0.,cap_emissivity=0.,window_thermal_emissivity=0.,
      ceramic_emissivity=0.,pn_seebeck_scale=scales[0],
      pn_resistivity_scale=scales[1],pn_thermal_conductivity_scale=scales[2],
      die_attach_conductivity_w_mk=1.)
    start=time.monotonic()
    signal.setitimer(signal.ITIMER_REAL,min(12.,max(.05,150-(start-tic))))
    try:
     result=solve(a,geo,transport_intervals=32)
     stages=result['stage_budget']
     lo=min(x['leg_temperature_extrema_k'][0] for x in stages)
     hi=max(x['leg_temperature_extrema_k'][1] for x in stages)
     accepted=lo>=40 and hi<=300 and not any(x['high_T_assumption_applied'] for x in stages) and (
      result['max_node_balance_residual_w']<1e-8 and abs(result['global_energy_residual_w'])<1e-8 and
      all(abs(x['energy_residual_w'])<1e-9 for x in stages))
     case.update(status='ACCEPTED' if accepted else 'REJECTED',
       reason=None if accepted else 'Measured-domain or numerical conservation failure',
       temperatures_K=result['temperatures_k'],
       voltage_V=result['terminal_voltage_v'],
       electrical_input_W=result['terminal_electrical_power_w'],
       Qc_cold_stage_W=stages[2]['qc_w'],
       leg_extrema_K=[lo,hi],
       node_residual_W=result['max_node_balance_residual_w'],
       global_energy_residual_W=result['global_energy_residual_w'],
       stage_energy_residual_W=[x['energy_residual_w'] for x in stages],
       assumed_T_above_300K=any(x['high_T_assumption_applied'] for x in stages))
    except (ValueError,TimeoutError,RuntimeError,FloatingPointError) as ex:
     case.update(status='REJECTED',reason=str(ex)[:300],
       original_failure_diagnostics=getattr(ex,'diagnostics',None))
    finally:
     signal.setitimer(signal.ITIMER_REAL,0)
    case['seconds']=time.monotonic()-start
    record.append(case)
    (out/'cases.json').write_text(json.dumps(record,indent=2)+'\n')
    print('R3_REDUCED_CASE',name,I,case['status'],
      case.get('temperatures_K',{}).get('MCT_die'),flush=True)
 finally:signal.signal(signal.SIGALRM,old)
 summary={'status':'CONDITIONAL SOURCE-CONSTRAINED 1D REFERENCE; 3D FULL DEVICE AND OEM UNQUALIFIED',
    'actual_CAD_stage_counts':[29,11,4],
    'geometry':geo,'scenario_registration':s,
    'cases':record,'accepted':sum(x['status']=='ACCEPTED' for x in record),
    'rejected':sum(x['status']=='REJECTED' for x in record),
    'not_run':sum(x['status']=='NOT RUN' for x in record),
    'original_electrical_B':'FAIL/STOP','P2_prospective_B':'STOP',
    'real_3D_thermal_C_D':'NOT RUN','full_CAD_material_laws_released':False,
    'actual_OEM_detector_T':'NOT QUALIFIED',
    'elapsed_s':time.monotonic()-tic,
    'max_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
 with (out/'summary.json').open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
 print('R3_REDUCED_SUMMARY',summary['accepted'],summary['rejected'],summary['not_run'],flush=True)
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--preflight-only',action='store_true')
 p.add_argument('--out',type=Path)
 args=p.parse_args()
 g=geometry()
 print('R3_29_11_4_GEOMETRY',g['stages'],g['ceramic_sides_area_m2'],flush=True)
 if args.preflight_only:return
 assert args.out and args.out.is_dir()
 evaluate(args.out)
if __name__=='__main__':main()
