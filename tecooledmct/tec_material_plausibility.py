"""Registered reduced transport hypotheses; no OEM fitting or production FEM.

Uses the existing five-node/nonlinear algorithms unchanged. Wire OFF is an
explicit reduced boundary control; geometry/material source archives are read-only.
"""
import argparse
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import signal
import time

import numpy as np

from . import graded_tec,nonlinear_tec
from .integrated_reference import Scenario,geometry,solve,failure_diagnostics

ROOT=Path(__file__).resolve().parents[1]
NOTE=ROOT/'docs/TEC_MATERIAL_PLAUSIBILITY_20261101.md'
HYPOTHESES={'nominal':(1.,1.,1.),'lower':(.9,1.2,1.2),'higher':(1.1,.8,.8)}
CURRENTS=(0.,.1,.15,.2,.25,.3,.4,.5,.6,.8,1.)
SOURCES=('tecooledmct/graded_tec.py','tecooledmct/nonlinear_tec.py',
 'tecooledmct/integrated_reference.py','tecooledmct/material_profiles.py',
 'tecooledmct/oem_phase_a.py','tecooledmct/fem_g2a.py',
 'data/g2c/zhang2025_he_40_300_v2.json','data/g2c/oem2019_curves_v1.json',
 'data/g2c/source_registry.json','data/g2d/oem_source_review.json',
 'data/g2d/preregistration.json','data/g2d/calibration_reserved.json','data/g2d/validation_holdout.json',
 'fem/results/geometry_complete_checkpoint_20261030/manifest.json',
 'fem/results/geometry_complete_checkpoint_20261030/wire_routes.json')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,data):
    def convert(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        raise TypeError(type(x).__name__)
    Path(path).write_text(json.dumps(data,indent=2,default=convert,allow_nan=False)+'\n')


def material_properties(polarity,t,scales):
    """Characterization includes measured 40..180 K, outside active leg solver."""
    t=np.asarray(t,float)
    if polarity not in ('P','N') or not np.isfinite(t).all() or np.any(t<40) or np.any(t>390) or not np.isfinite(scales).all() or min(scales)<=0:
        raise ValueError('Invalid hypothesis property query')
    measured=graded_tec.source().properties(polarity,np.minimum(t,300.))
    above=np.maximum(t-300.,0.)
    out={}
    for key,scale in zip(('S','rho','k'),scales):
        slope=graded_tec.source().curves[polarity][key].slope(300.)
        out[key]=(measured[key]+above*.25*slope)*scale
    derivative=graded_tec.source().curves[polarity]['S'].slope(np.minimum(t,300.))*np.where(t>300.,.25,1.)*scales[0]
    out.update(sigma=1/out['rho'],thomson_v_k=t*derivative,S_prime=derivative,
               zT=out['S']**2*t/(out['rho']*out['k']))
    if np.any(out['rho']<=0) or np.any(out['k']<=0) or np.any(out['S']*(1 if polarity=='P' else -1)<=0):raise ValueError('Nonpassive property hypothesis')
    return out


def characterization():
    t=np.array([40.,60.,100.,140.,180.,200.,220.,240.,260.,280.,300.,300.000001,330.,390.])
    rows={}
    for name,scales in HYPOTHESES.items():
        pn={p:material_properties(p,t,scales) for p in ('P','N')}
        alpha=pn['P']['S']-pn['N']['S'];rho=pn['P']['rho']+pn['N']['rho'];k=pn['P']['k']+pn['N']['k']
        zt=alpha**2*t/(rho*k)
        rows[name]={'scales_S_rho_k':scales,'polarities':pn,'equal_area_couple_ZT':zt,
                    'couple_compatibility_per_V':(np.sqrt(1+zt)-1)/(alpha*t)}
    return {'temperature_K':t,'hypotheses':rows,'source':graded_tec.source_evidence(),
            'meaning':'Dissimilar research specimens; coherent scaled engineering hypotheses, not measured commercial grades; >300 K assumed'}


class ScaledMeasuredProfile:
    interval=(40.,300.)
    def __init__(self,scales):self.scales=scales
    def properties(self,polarity,t):
        p=graded_tec.source().properties(polarity,t)
        for key,scale in zip(('S','rho','k'),self.scales):p[key]=p[key]*scale
        p['sigma']=1/p['rho'];p['thomson_v_k']=p['thomson_v_k']*self.scales[0]
        return p


def independent_transport_checks(g):
    from .oem_phase_a import bounded_leg
    rows=[]
    for h,scales in HYPOTHESES.items():
        for idx,hot,cold,I in ((0,295.,250.,.15),(2,260.,210.,.3)):
            geom=g['stages'][idx];A=geom['leg_area_m2'];n=geom['couples']
            direct=nonlinear_tec.Transport(32).stage(geom,hot,cold,I,alpha_scale=scales[0],rho_scale=scales[1],k_scale=scales[2])
            pn={p:bounded_leg(ScaledMeasuredProfile(scales),p,hot,cold,I/A*(1 if p=='N' else -1),geom['leg_length_m'],intervals=32) for p in ('P','N')}
            qc=-n*A*sum(v['q_cold_w_m2'] for v in pn.values())
            V=n*(pn['N']['electric_integral_v']-pn['P']['electric_integral_v'])
            row={'hypothesis':h,'stage_index':idx,'hot_K':hot,'cold_K':cold,'current_A':I,
                 'Qc_absolute_error_W':abs(direct['qc_w']-qc),'V_absolute_error_V':abs(direct['voltage_v']-V),
                 'reference_leg_min_K':min(v['min_k'] for v in pn.values()),'reference_leg_max_K':max(v['max_k'] for v in pn.values()),
                 'stage_energy_error_W':direct['energy_residual_w']}
            row['passed']=row['Qc_absolute_error_W']<3e-8 and row['V_absolute_error_V']<3e-7 and 180<row['reference_leg_min_K']<=row['reference_leg_max_K']<300
            rows.append(row)
    return {'rows':rows,'passed':all(r['passed'] for r in rows),'scope':'Independent bounded measured-domain same-grid BVP check; no OEM accuracy claim'}


def case(group,hyp,current,load=.002,hot=300.,wires=False,scales=None,attach=1.,material='zhang2025_nonlinear',label=None):
    return {'group':group,'hypothesis':hyp,'current_A':float(current),'die_load_W':float(load),
            'hot_K':float(hot),'wires_ON':bool(wires),'scales':list(HYPOTHESES[hyp] if scales is None else scales),
            'attach_k_W_mK':float(attach),'material_model':material,'label':label}


def registered_cases(oem):
    cases=[]
    for h in HYPOTHESES:
        for wires in (False,True):
            cases.extend(case('core',h,i,wires=wires) for i in CURRENTS)
    cases.extend(case('G1_control','nominal',i,material='g1_constant') for i in CURRENTS)
    for h in HYPOTHESES:
        for hot in (290.,310.):
            for load in (0.,.005):
                cases.extend(case('hot_load',h,i,load,hot) for i in (.15,.4))
    for index,key,bounds in [(0,'S',(.9,1.1)),(1,'rho',(.8,1.2)),(2,'k',(.8,1.2))]:
        for value in bounds:
            scales=[1.,1.,1.];scales[index]=value
            cases.append(case('OAT','nominal',.25,scales=scales,label=f'{key}_{value}'))
    for hot in (290.,310.):cases.append(case('OAT','nominal',.25,hot=hot,label=f'hot_{hot}'))
    for load in (0.,.005):cases.append(case('OAT','nominal',.25,load=load,label=f'load_{load}'))
    for attach in (.5,3.):cases.append(case('OAT','nominal',.25,attach=attach,label=f'attach_{attach}'))
    conditions=sorted({(p['current_a'],p['load_w']) for p in oem['points'] if p['panel']=='300K_vacuum'})
    for h in HYPOTHESES:cases.extend(case('OEM_literal','nominal' if h=='nominal' else h,i,q,300.15) for i,q in conditions)
    cases.extend(case('OEM_300K_reference','nominal',i,0.,300.) for i in (.1,.2,.4,.6,.8,1.))
    for attach in (.5,3.):cases.append(case('attach_invariance','nominal',.2,.1,300.15,attach=attach))
    return [dict(c,id=f'{i:03d}') for i,c in enumerate(cases)]


def scenario(c):
    a,r,k=c['scales']
    return Scenario(ambient_k=c['hot_K'],current_a=c['current_A'],material_model=c['material_model'],
        heat_sink_k_w=0.,detector_bias_w=c['die_load_W'],detector_absorbed_w=0.,
        cavity_pressure_pa=0.,cap_emissivity=0.,window_thermal_emissivity=0.,
        pn_seebeck_scale=a,pn_resistivity_scale=r,pn_thermal_conductivity_scale=k,
        die_attach_conductivity_w_mk=c['attach_k_W_mK'])


def summarize(c,r):
    nodes=list(r['temperatures_k'].values());stages=r['stage_budget'];power=r['module_electrical_power_w'];terminal=r['terminal_electrical_power_w']
    extrema=[s.get('leg_temperature_extrema_k',[min(nodes[:4]),max(nodes[:4])]) for s in stages]
    extension=any(s.get('high_T_assumption_applied',False) for s in stages)
    return {'id':c['id'],'group':c['group'],'hypothesis':c['hypothesis'],'current_A':c['current_A'],
       'hot_K':nodes[0],'die_load_W':c['die_load_W'],'wires_ON':c['wires_ON'],'Tdie_K':r['MCT_die_k'],
       'Tcold_ceramic_K':nodes[3],'cold_lift_K':nodes[0]-nodes[3],'stage_lifts_K':np.array(nodes[:3])-nodes[1:4],
       'Qc_cold_W':stages[2]['qc_w'],'module_voltage_V':r['module_voltage_v'],
       'terminal_voltage_V':r['terminal_voltage_v'],'module_input_W':power,'terminal_input_W':terminal,
       'cooler_COP':stages[2]['qc_w']/power if power>1e-14 else None,
       'die_COP':c['die_load_W']/terminal if terminal>1e-14 else None,
       'local_leg_min_K':min(e[0] for e in extrema),'local_leg_max_K':max(e[1] for e in extrema),
       'assumed_continuation_used':extension,'all_legs_within_measured_domain':not extension if c['material_model']!='g1_constant' else None,
       'module_boundary':'conditional idealized vacuum with prescribed hot ceramic and cold load, no external exchange',
       'material_grade_identified':False}


def oem_comparisons(oem,cases,results,attach_ok):
    rows=[]
    for p in oem['points']:
        for h in HYPOTHESES:
            row={'source_id':p['id'],'panel':p['panel'],'hypothesis':h,'current_A':p['current_a'],
                 'Qc_W':p['load_w'],'field':p['field'],'source_value':p['value'],'source_split_already_examined':p['split'],
                 'chart_reading_bound':p['value_reading_bound'],'measured_grade_match':False,'fresh_blind_holdout':False}
            if p['panel']!='300K_vacuum':
                row.update(status='NOT COMPARABLE',reason='Dry-N2 boundary/exchange not modeled; no gas/radiation campaign')
            else:
                c=next(c for c in cases if c['group']=='OEM_literal' and c['hypothesis']==h and c['current_A']==p['current_a'] and c['die_load_W']==p['load_w'])
                result=results[c['id']]
                if result['status']!='ACCEPTED' or not attach_ok:
                    row.update(status='NOT COMPARABLE',reason='Reduced point rejected/NOT RUN or auxiliary attach invariance failed',case_id=c['id'])
                else:
                    s=result['summary'];value=s['cold_lift_K'] if p['field']=='delta_t_k' else s['module_voltage_V']
                    diff=value-p['value']
                    row.update(status='CONDITIONAL BOUNDARY-MATCHED PLAUSIBILITY',case_id=c['id'],literal_hot_K=300.15,
                        model_value=value,signed_difference=diff,absolute_difference=abs(diff),
                        signed_relative_difference=diff/p['value'] if p['value']!=0 else None,
                        absolute_relative_difference=abs(diff/p['value']) if p['value']!=0 else None,
                        strict_measured_source_comparison='NOT COMPARABLE: 300.15 K exceeds measured 300 K endpoint',
                        assumed_continuation_used=s['assumed_continuation_used'],
                        unknown_conditions='Actual grade, internal geometry, contact/mount losses, vacuum pressure and radiative parasitics not identified')
            rows.append(row)
    return rows


def run(out,total_seconds=600.):
    out=Path(out).resolve()
    if out.exists():raise ValueError('Use absent output directory; never overwrite evidence')
    out.mkdir(parents=True);start=time.monotonic();oem=read(ROOT/'data/g2c/oem2019_curves_v1.json')
    hashes={p:sha(ROOT/p) for p in SOURCES};g=geometry();cases=registered_cases(oem)
    registration={'UTC':datetime.now(timezone.utc).isoformat(),'baseline':'c24dd2535f52c813bb92c06190c2fd0a371f8955',
         'registration':NOTE.read_text().split('## Results')[0],'hypotheses':HYPOTHESES,'cases':cases,
         'input_sha256':hashes,'study_code_sha256':sha(__file__),'per_case_seconds':8.,'total_case_budget_seconds':total_seconds,
         'source_material_id':graded_tec.source().metadata['id'],'fitted_parameters':False,'new_3D_solves':0}
    if registration['source_material_id']!='zhang2025_he_digitized_40_300_v2r1':raise ValueError('Incorrect source/erratum version')
    write(out/'registration.json',registration);write(out/'properties.json',characterization())
    transport=independent_transport_checks(g);write(out/'transport_verification.json',transport)
    if not transport['passed']:raise ValueError('Independent scaled transport verification failed; stop before scenarios')
    results={}
    def timeout(signum,frame):raise TimeoutError('Registered 8 s reduced-point budget exceeded')
    previous=signal.signal(signal.SIGALRM,timeout)
    try:
        for c in cases:
            if time.monotonic()-start>total_seconds:
                results[c['id']]={'status':'NOT RUN','reason':'Registered total case budget exhausted'};continue
            t=time.monotonic();s=scenario(c);geo=deepcopy(g)
            if not c['wires_ON']:geo['wires']=[]
            signal.setitimer(signal.ITIMER_REAL,min(8.,max(.01,total_seconds-(time.monotonic()-start))))
            try:
                r=solve(s,geo,transport_intervals=32)
                results[c['id']]={'status':'ACCEPTED','summary':summarize(c,r),'result':r,'seconds':time.monotonic()-t}
            except (ValueError,RuntimeError,TimeoutError,FloatingPointError) as error:
                diag=getattr(error,'diagnostics',None)
                results[c['id']]={'status':'REJECTED','reason':str(error),'diagnostics':diag or failure_diagnostics(s,error=str(error)),
                                 'classification':'runtime_budget' if isinstance(error,TimeoutError) else 'existing_model_failure',
                                 'seconds':time.monotonic()-t}
            finally:signal.setitimer(signal.ITIMER_REAL,0.)
            write(out/'cases.json',results)
    finally:signal.signal(signal.SIGALRM,previous)
    write(out/'cases.json',results)
    module=[c for c in cases if c['group']=='OEM_literal' and c['hypothesis']=='nominal' and c['current_A']==.2 and c['die_load_W']==.1][0]
    checks=[results[c['id']] for c in cases if c['group']=='attach_invariance']+[results[module['id']]]
    attach_ok=all(r['status']=='ACCEPTED' for r in checks)
    attach_diffs=None
    if attach_ok:
        attach_diffs={key:float(np.ptp([r['summary'][key] for r in checks])) for key in ('Tcold_ceramic_K','module_voltage_V','Qc_cold_W')}
        attach_ok=attach_diffs['Tcold_ceramic_K']<1e-6 and attach_diffs['module_voltage_V']<1e-7 and attach_diffs['Qc_cold_W']<1e-8
    comparisons=oem_comparisons(oem,cases,results,attach_ok)
    write(out/'oem_comparison.json',{'rows':comparisons,'attach_invariance_passed':attach_ok,'attach_spans':attach_diffs,
           'Qmax':'NOT RUN','DeltaTmax':'NOT RUN','historical_G2d_residual_current_validation':False,
           'identifiability_note':'Historical rank 8/9; no new fit, fresh blindness or commercial grade identification'})
    counts={group:{status:sum(c['group']==group and results[c['id']]['status']==status for c in cases) for status in ('ACCEPTED','REJECTED','NOT RUN')} for group in sorted({c['group'] for c in cases})}
    target={}
    for h in HYPOTHESES:
        for wires in (False,True):
            subset=[r['summary'] for c in cases if c['group']=='core' and c['hypothesis']==h and c['wires_ON']==wires and (r:=results[c['id']])['status']=='ACCEPTED']
            best=min(subset,key=lambda r:r['Tdie_K']) if subset else None
            hits=[r for r in subset if r['Tdie_K']<=200.]
            target[h+('_wires_ON' if wires else '_wires_OFF')]={'minimum_accepted_sample':best,'target_hit_case_ids':[r['id'] for r in hits],
                 'target_demonstrated_in_registered_reduced_assumptions':bool(hits),
                 'strict_measured_domain_target_ids':[r['id'] for r in hits if r['all_legs_within_measured_domain']],
                 'meaning':'Discrete admitted reduced-model result only; not actual assembly feasibility or an unrestricted optimum'}
    for p,h in hashes.items():
        if sha(ROOT/p)!=h:raise ValueError('Frozen source changed during study: '+p)
    report={'scope':'Material-law hypotheses and conditional module-boundary plausibility; no OEM fit or new FEM',
         'counts':counts,'targets':target,'total_seconds':time.monotonic()-start,
         'cases':len(cases),'accepted':sum(r['status']=='ACCEPTED' for r in results.values()),
         'rejected':sum(r['status']=='REJECTED' for r in results.values()),'not_run':sum(r['status']=='NOT RUN' for r in results.values()),
         'Rev3_modified':False,'optional_nonlocal_scenario':'NOT RUN; prior 7.277% side-port gate remains failed'}
    write(out/'summary.json',report)
    print(json.dumps({'counts':counts,'seconds':report['total_seconds'],'targets':{k:{'minimum_K':v['minimum_accepted_sample']['Tdie_K'] if v['minimum_accepted_sample'] else None,'hit_ids':v['target_hit_case_ids']} for k,v in target.items()}}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();run(args.out)
