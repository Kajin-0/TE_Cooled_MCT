#!/usr/bin/env python3
"""Source-CAD geometry finite-sink / finite-wire reduced conditional R3 controls.

Predeclared 18 = 3 sinks * 2 wire states * 3 selected material/current pairs.
Existing nonlinear 32-cell transport / five-node model, NO 3D PDE, OEM fit,
silently assigned contact law, statistical uncertainty interval or reruns.
"""
from pathlib import Path
import argparse,hashlib,json,math,signal,time
from tecooledmct.integrated_reference import Scenario,solve
from tecooledmct.tec_material_plausibility import HYPOTHESES
from tecooledmct.materials import COPPER,GOLD_WIRE_4N
from scripts.v3_reference_29114_reduced_study import geometry as base_geometry

ROOT=Path(__file__).resolve().parents[1]
CAD=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
BASE=ROOT/'data/v3_reference_29114_reduced_20261107/attempt01/summary.json'
BASEMAN=ROOT/'data/v3_reference_29114_reduced_20261107/attempt01/manifest.json'
SRC=ROOT/'scripts/v3_reference_29114_reduced_study.py'
MAT=ROOT/'tecooledmct/materials.py'
ENGINE=ROOT/'tecooledmct/integrated_reference.py'
NONLINEAR=ROOT/'tecooledmct/nonlinear_tec.py'
FILES=(CAD,BASE,BASEMAN,SRC,MAT,ENGINE,NONLINEAR)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def geometry():
 g=base_geometry()
 j=read(CAD)
 body={x['name']:x for x in j['bodies']}
 wires=[]
 for name,material,proxy in (
     ('TEC_lead1','Cu',COPPER),('TEC_lead9','Cu',COPPER),
     ('detector_bond7','Au',GOLD_WIRE_4N),
     ('detector_bond8','Au',GOLD_WIRE_4N)):
  b=body[name]
  assert b['material']==material and b['shape']=='wire'
  R=b['radius']*1e-3
  L=sum(p['length'] for p in b['parts'])*1e-3
  assert L>0 and R>0
  area=math.pi*R*R
  k=proxy.thermal_conductivity_w_mk
  rho=proxy.electrical_resistivity_ohm_m
  assert 0<k<500 and 0<rho<1e-6
  wires.append({'name':name,'pin':int(name[-1]),
     'material':material,'radius_m':R,'length_m':L,'area_m2':area,
     'k_W_mK_293K_bulk_proxy':k,
     'rho_ohm_m_293K_bulk_proxy':rho,
     'G_W_K':k*area/L,'R_ohm':rho*L/area,
     'source':'original R3 source geometric centerline and old bulk proxy, not measured lead conductivity',
     'uncalibrated_pin_reservoir_K':300.})
 assert len(wires)==4
 assert sorted(w['pin'] for w in wires)==[1,7,8,9]
 assert abs(wires[0]['radius_m']-.0001)<1e-15
 assert abs(wires[2]['radius_m']-.000009)<1e-15
 g['wires']=wires
 return g
def plan():
 return {'scientific_contract':'R3 29/11/4 CAD-derived reduced conditional thermal loss scan; no as-built prediction',
  'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in FILES},
  'source_script_SHA256':sha(Path(__file__)),
  'sinks_K_W':[0.,2.,5.],
  'pin_and_ambient_reservoir_K':300.,
  'current_and_material_pairs':[{'hypothesis':'nominal','current_A':.25},
                                {'hypothesis':'nominal','current_A':.4},
                                {'hypothesis':'higher','current_A':.4}],
  'wire_modes':['OFF','CAD-derived bulk-proxy ON'],
  'fixed_die_load_W':.002,'gas':'OFF','radiation':'OFF',
  'hot_side_finite_sink':'300K ambient + R_sink * actual model computed heat to bath, Cu hot-wire heat treated separately',
  'sink_values_are_scenarios_not_measurements':True,
  'Au_and_Cu_constant_bulk_293K_properties_are_proxies_not_measured_as_built':True,
  'per_case_seconds':12.,'run_budget_seconds':150.,
  'no_extrapolation_pretense':'Temperature>300K uses ALREADY IMPLEMENTED quarter-slope assumed continuation; categorize separately',
  'acceptance':'existing node <1e-8W, stage <1e-9W, global <1e-8W; all leg extrema 180..390K; no reclassification of gate B',
  'original_P1_B':'FAIL/STOP','prospective_P2_B':'STOP','real_3D_C_D':'NOT RUN',
  'no_OEM_fitting_no_new_geometry':True}
def run(out):
 reg=read(out/'registration.json')
 assert reg==plan()
 g=geometry()
 gc={**g,'wires':[]}
 baseline=read(BASE)
 cases=[];start=time.monotonic()
 def alarm(_,__):raise TimeoutError('Registered case wall cap')
 old=signal.signal(signal.SIGALRM,alarm)
 try:
  for p in plan()['current_and_material_pairs']:
   h,I=p['hypothesis'],p['current_A'];scales=HYPOTHESES[h]
   for sink in (0.,2.,5.):
    for mode in ('OFF','CAD-derived bulk-proxy ON'):
     row={'hypothesis':h,'current_A':I,'sink_K_W':sink,'wires_mode':mode}
     if time.monotonic()-start>150:
      row.update(status='NOT RUN',reason='Registered wall budget exhausted')
      cases.append(row);continue
     cfg=gc if mode=='OFF' else g
     s=Scenario(ambient_k=300.,current_a=I,material_model='zhang2025_nonlinear',
       heat_sink_k_w=sink,detector_bias_w=.002,detector_absorbed_w=0.,
       cavity_pressure_pa=0.,cap_emissivity=0.,window_thermal_emissivity=0.,
       ceramic_emissivity=0.,pn_seebeck_scale=scales[0],
       pn_resistivity_scale=scales[1],pn_thermal_conductivity_scale=scales[2],
       die_attach_conductivity_w_mk=1.)
     startcase=time.monotonic()
     signal.setitimer(signal.ITIMER_REAL,min(12.,max(.05,150-(startcase-start))))
     try:
      r=solve(s,cfg,transport_intervals=32)
      stages=r['stage_budget'];ex=[
        min(x['leg_temperature_extrema_k'][0] for x in stages),
        max(x['leg_temperature_extrema_k'][1] for x in stages)]
      ass=any(x['high_T_assumption_applied'] for x in stages)
      good=ex[0]>=180 and ex[1]<=390 and r['max_node_balance_residual_w']<1e-8 and (
        abs(r['global_energy_residual_w'])<1e-8) and (
        max(abs(x['energy_residual_w']) for x in stages)<1e-9)
      row.update(status='ACCEPTED_ASSUMED_GT300K' if good and ass else (
                    'ACCEPTED_SOURCE_MEASURED_T' if good else 'REJECTED'),
       reason=None if good else 'Energy or original bounded transport gate failure',
       temperatures_K=r['temperatures_k'],
       terminal_V=r['terminal_voltage_v'],terminal_power_W=r['terminal_electrical_power_w'],
       rejected_at_sink_W=r['bath_rejected_power_w'],
       cold_stage_Qc_W=stages[2]['qc_w'],
       heat_paths_W=r['heat_paths_w'],
       max_node_residual_W=r['max_node_balance_residual_w'],
       global_energy_error_W=r['global_energy_residual_w'],
       stage_energy_errors_W=[x['energy_residual_w'] for x in stages],
       leg_extrema_K=ex,
       above_300K_assumed_material_law=ass)
      if good and mode=='OFF' and sink==0:
       b=next(x for x in baseline['cases'] if x['hypothesis']==h and x['current_A']==I)
       assert abs(r['MCT_die_k']-b['temperatures_K']['MCT_die'])<1e-8
       assert abs(r['terminal_voltage_v']-b['voltage_V'])<1e-8
       row['exact_prior_R3_ideal_case_control_PASS']=True
     except (ValueError,TimeoutError,RuntimeError,AssertionError,FloatingPointError) as ex:
      row.update(status='REJECTED',reason=str(ex)[:450],
        diagnostics=getattr(ex,'diagnostics',None))
     finally:signal.setitimer(signal.ITIMER_REAL,0.)
     row['seconds']=time.monotonic()-startcase
     cases.append(row)
     (out/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
     print('R3_SINK_WIRE',h,I,sink,mode,row['status'],
           row.get('temperatures_K',{}).get('MCT_die'),flush=True)
 finally:signal.signal(signal.SIGALRM,old)
 summary={'status':'CONDITIONAL R3 FINITE SINK / CAD GEOMETRIC LEAD PROXY: NOT physical OEM prediction',
  'wire_lengths_and_bulk_coefficients':g['wires'],'conditions':plan(),
  'cases':cases,'accepted_source_temperature':sum(x['status']=='ACCEPTED_SOURCE_MEASURED_T' for x in cases),
  'accepted_assumed_gt300K':sum(x['status']=='ACCEPTED_ASSUMED_GT300K' for x in cases),
  'rejected':sum(x['status']=='REJECTED' for x in cases),
  'not_run':sum(x['status']=='NOT RUN' for x in cases),
  'source_430_3D_C_D':'NOT RUN','original_P1_B':'FAIL/STOP','prospective_P2_B':'STOP',
  'production_detector_prediction':'UNQUALIFIED',
  'elapsed_s':time.monotonic()-start}
 with (out/'summary.json').open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
 print('R3_SINK_WIRE_SUMMARY',summary['accepted_source_temperature'],
   summary['accepted_assumed_gt300K'],summary['rejected'],summary['not_run'],flush=True)
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--preflight-only',action='store_true')
 p.add_argument('--out',type=Path)
 a=p.parse_args()
 g=geometry()
 print('R3_SOURCE_WIRE_COEFFICIENTS',[(v['name'],v['length_m'],v['G_W_K'],v['R_ohm']) for v in g['wires']],flush=True)
 if a.preflight_only:return
 assert a.out and a.out.is_dir()
 run(a.out)
if __name__=='__main__':main()
