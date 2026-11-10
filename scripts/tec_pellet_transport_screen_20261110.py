#!/usr/bin/env python3
"""Frozen-pad, 88-leg transport-only geometry screen. No package solve or CAD edit."""
from pathlib import Path
import argparse,hashlib,json,math,signal,time
import numpy as np
from scipy.optimize import brentq
from tecooledmct.nonlinear_tec import leg

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/tec_pellet_screen_20261110'
BASE=ROOT/'data/v3_11_rev3_backfill_source_20261109/Kr100_I040'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def timeout_handler(*_):raise TimeoutError('Registered per-case wall budget')

def run(case_id):
 reg=read(DATA/'registration.json');manifest=read(DATA/'source_seal.json')
 assert sha(DATA/'registration.json')==manifest['registration_sha256']
 for name,h in {**reg['source_sha256'],**manifest['sources_sha256']}.items():
  if sha(ROOT/name)!=h:raise ValueError('Source identity mismatch: '+name)
 case=next(x for x in reg['geometry_cases'] if x['id']==case_id)
 base=read(BASE/'result.json');old=base['source_individual_leg_flux_and_electric_results']
 assert len(old)==88 and [sum(z['stage']==i for z in old) for i in range(3)]==[58,22,8]
 A=(case['width_mm']*1e-3)**2;L=case['length_mm']*1e-3;assert A>0 and L>0
 aux=base['source_tec_power_leads']['total_R_ohm']+base['source_total_solder_and_contact_series_resistance_ohm']+base['Cu_form_tab_electrical_R_ohm']
 assert aux>0 and abs(sum(z['terminal_contribution_V'] for z in old)+.4*aux-base['terminal_voltage_V'])<1e-11
 out=DATA/'cases'/case_id;out.mkdir(parents=True,exist_ok=False)
 signal.signal(signal.SIGALRM,timeout_handler);signal.setitimer(signal.ITIMER_REAL,reg['case_wall_seconds']);start=time.monotonic()
 evaluated=[];cache={}
 def at(I):
  I=float(I)
  if I in cache:return cache[I]
  if len(cache)>=reg['max_root_evaluations_per_case']+1:raise RuntimeError('Registered evaluation limit')
  stages=[dict(qh_W=0.,qc_W=0.,V=0.,joule_W=0.,energy_residual_W=0.,nlegs=0) for _ in range(3)];rows=[]
  for z in old:
   pol=z['material'];r=leg(pol,z['Th_K'],z['Tc_K'],I/A*(1 if pol=='N' else -1),L,intervals=32,scales=(1.,1.,1.))
   qh=-A*r['q_hot_w_m2'];qc=-A*r['q_cold_w_m2'];v=r['electric_integral_v']*(1 if pol=='N' else -1)
   row=dict(leg=z['original_leg_name'],source_leg_ID=z['source_leg_ID'],stage=z['stage'],material=pol,Th_K=z['Th_K'],Tc_K=z['Tc_K'],Qh_W=qh,Qc_W=qc,V_V=v,joule_W=A*r['joule_w_m2'],energy_error_W=qh-qc-I*v,T_min_K=min(r['temperatures_k']),T_max_K=max(r['temperatures_k']),assumed_above_300K=r['assumed_high_T_continuation_used'])
   if abs(row['energy_error_W'])>=reg['leg_energy_gate_W']:raise ValueError('Leg energy gate')
   s=stages[z['stage']];s['qh_W']+=qh;s['qc_W']+=qc;s['V']+=v;s['joule_W']+=row['joule_W'];s['energy_residual_W']+=row['energy_error_W'];s['nlegs']+=1;rows.append(row)
  assert max(abs(x['energy_residual_W']) for x in stages)<reg['stage_energy_gate_W']
  V=sum(x['V'] for x in stages)+I*aux;P=I*V
  result=dict(current_A=I,terminal_V=V,electrical_power_W=P,stage_budgets=stages,legs=rows,auxiliary_series_R_ohm=aux,source_die_K_FIXED=base['calculated_detector_temperature_K'],source_top_ceramic_K_FIXED=base['source_full_temperature_nodes_K']['stage2_cold'],source_hot_ceramic_K_FIXED=base['source_full_temperature_nodes_K']['stage0_hot'],min_leg_K=min(z['T_min_K'] for z in rows),max_leg_K=max(z['T_max_K'] for z in rows),legs_using_assumed_above_300K=sum(z['assumed_above_300K'] for z in rows))
  cache[I]=result;evaluated.append(dict(I_A=I,V=V,power_W=P,stage_cold_Qc_W=stages[2]['qc_W']))
  print('EVALUATION',case_id,round(I,9),round(P,9),flush=True)
  return result
 result=dict(case=case,status='PENDING',scope=reg['scope'],source_reference_fixed=True,source_CAD_rebuilt=False,detector_or_top_temperature_solved=False,full_system_solves=0,run_started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
 try:
  fixed=at(reg['current_fixed_A']);result['fixed_current']=fixed
  if case_id=='baseline':
   differences=[abs(a[k]-b[oldkey]) for a,b in zip(fixed['legs'],old) for k,oldkey in [('Qh_W','Qhot_W'),('Qc_W','Qcold_W'),('V_V','terminal_contribution_V')]]
   assert max(differences)<reg['baseline_replay_abs_tolerance'] and abs(fixed['terminal_V']-base['terminal_voltage_V'])<reg['baseline_replay_abs_tolerance']
   result['baseline_replay_max_abs_difference']=max(differences)
  target=reg['matched_power_reference_W'];low,high=reg['matched_current_bracket_A'];fl=at(low)['electrical_power_W']-target;fh=at(high)['electrical_power_W']-target
  if not (fl<=0<=fh):raise ValueError(f'Matched power is not bracketed: {fl}, {fh}')
  if case_id=='baseline':root=.4
  else:root=brentq(lambda x:at(x)['electrical_power_W']-target,low,high,xtol=reg['root_current_tolerance_A'],maxiter=reg['max_root_evaluations_per_case']-2)
  matched=at(root)
  assert abs(matched['electrical_power_W']-target)<reg['root_power_abs_tolerance_W']
  result.update(status='ACCEPTED FROZEN-PAD TRANSPORT ONLY',matched_power=matched,matched_power_absolute_error_W=abs(matched['electrical_power_W']-target),power_bracket_A=[low,high],temperature_prediction='NOT RUN')
 except Exception as e:
  result.update(status='STOP CASE; NO CLAIM',error=repr(e),diagnostics=getattr(e,'diagnostics',None),matched_power='NOT RUN OR FAILED')
 finally:
  signal.setitimer(signal.ITIMER_REAL,0.);result['evaluations']=evaluated;result['elapsed_seconds']=time.monotonic()-start
  save(out/'result.json',result)
 print('CASE_RESULT',case_id,result['status'],flush=True)
 return result['status'].startswith('ACCEPTED')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();raise SystemExit(0 if run(a.case) else 1)
