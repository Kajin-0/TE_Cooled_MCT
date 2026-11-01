"""Registered finite-sink controls; unchanged five-node transport, no fitting."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import signal
import time

import numpy as np
from scipy.optimize import least_squares

from .integrated_reference import (Scenario,geometry,solve,coefficients,
    TEMPERATURE_NODES,OperatingPointFailure,failure_diagnostics)
from .nonlinear_tec import Transport
from . import graded_tec
from .tec_material_plausibility import ROOT,SOURCES,HYPOTHESES,read,write,sha

BASELINE='641bf5df70d5c585cb9027efd5d1420e604c2e59'
NOTE=ROOT/'docs/FINITE_SINK_MATCHED_TARGET_20261101.md'
SINKS=(0.,.5,1.,2.,5.,10.)
CURRENTS=tuple(i/1000 for i in (0,100,150,200,250,275,300,325,350,375,400,450,500,600,800,1000))
SEEDS=((301.,270.,240.,210.,210.1),(310.,260.,220.,195.,195.1))
TARGET_K=200.
TARGET_TOL_K=.005


def scenario(c):
    a,r,k=HYPOTHESES[c['hypothesis']]
    return Scenario(ambient_k=300.,current_a=c['current_A'],material_model=c.get('material','zhang2025_nonlinear'),
        heat_sink_k_w=c['sink_K_W'],detector_bias_w=.002,detector_absorbed_w=0.,
        cavity_pressure_pa=0.,cap_emissivity=0.,window_thermal_emissivity=0.,
        pn_seebeck_scale=a,pn_resistivity_scale=r,pn_thermal_conductivity_scale=k).validate()


def design():
    grid=[{'id':f'grid_{h}_R{r:g}_I{i:g}','family':'grid','hypothesis':h,'sink_K_W':r,'current_A':i}
          for h in HYPOTHESES for r in SINKS for i in CURRENTS]
    controls=[{'id':f'constant_R{r:g}_I{i:g}','family':'constant','hypothesis':'nominal',
               'sink_K_W':r,'current_A':i,'material':'g1_constant'} for r in (0.,2.,10.) for i in (0.,.3,.8)]
    branches=[{'id':f'branch_R{r:g}_seed{j}','family':'branch','hypothesis':'nominal','sink_K_W':r,
               'current_A':.3,'seed_K':list(seed)} for r in (2.,10.) for j,seed in enumerate(SEEDS)]
    slots=[{'id':f'target_R{r:g}_step{j}','family':'target','hypothesis':'nominal','sink_K_W':r,
            'midpoint_rule':'first admitted falling 200 K bracket; at most ten real midpoint solves'}
           for r in SINKS for j in range(10)]
    return {'grid':grid,'constant':controls,'branch':branches,'target_slots':slots,
            'maximum_top_level_calls':361,'total_seconds':600.,'per_call_seconds':8.}


def wire_coefficients(g):
    return tuple(sum(w[key] for w in g['wires'] if w['material']==mat)
                 for mat,key in (('Cu','G_W_K'),('Au','G_W_K'),('Cu','R_ohm')))


def constant_exact(s,g):
    """Independent exact linear equations at fixed current, not optimizer residuals."""
    s.validate()
    if s.material_model!='g1_constant':raise ValueError('Analytic control requires constant properties')
    p=coefficients(s,g);I=s.current_a;Rth=s.heat_sink_k_w;Ta=s.ambient_k
    alpha=np.array([c['alpha_v_k'] for c in p]);R=np.array([c['r_ohm'] for c in p]);K=np.array([c['k_w_k'] for c in p])
    Gcu,Gau,Rcu=wire_coefficients(g);Ga=s.die_attach_conductivity_w_mk/g['die_attach_thickness_over_area_m_inverse']
    M=np.zeros((5,5));b=np.zeros(5)
    for j in (0,1):
        M[j,j]=-K[j];M[j,j+1]=(alpha[j]-alpha[j+1])*I+K[j]+K[j+1];M[j,j+2]=-K[j+1]
        b[j]=.5*I*I*(R[j]+R[j+1])
    M[2,2]=-K[2];M[2,3]=alpha[2]*I+K[2]+Ga;M[2,4]=-Ga;b[2]=.5*I*I*R[2]
    M[3,3]=-Ga;M[3,4]=Ga+Gau;b[3]=s.detector_bias_w+s.detector_absorbed_w+Gau*Ta
    M[4,0]=1-Rth*(alpha[0]*I-K[0]-Gcu);M[4,1]=-Rth*K[0]
    b[4]=Ta+Rth*(Gcu*Ta+.5*I*I*(R[0]+Rcu))
    t=np.linalg.solve(M,b)
    V=float(np.sum(I*R+alpha*(t[:3]-t[1:4]))+I*Rcu)
    sink=float(alpha[0]*I*t[0]+.5*I*I*R[0]-K[0]*(t[0]-t[1])+Gcu*(Ta-t[0])+.5*I*I*Rcu)
    return {'temperatures_K':t,'terminal_V':V,'sink_W':sink,'linear_residual':M@t-b}


def zero_current_exact(s,g):
    """Independent resistor-series/parallel limit with both physical wire routes."""
    if s.current_a!=0 or s.material_model!='g1_constant':raise ValueError('Zero-current constant control required')
    K=[c['k_w_k'] for c in coefficients(s,g)];Gcu,Gau,_=wire_coefficients(g)
    reff=s.heat_sink_k_w/(1+s.heat_sink_k_w*Gcu)
    rseries=sum(1/k for k in K)+g['die_attach_thickness_over_area_m_inverse']/s.die_attach_conductivity_w_mk+reff
    rise=(s.detector_bias_w+s.detector_absorbed_w)/(Gau+1/rseries)
    qchain=rise/rseries
    return {'die_K':s.ambient_k+rise,'hot_K':s.ambient_k+reff*qchain,
            'sink_W':qchain/(1+s.heat_sink_k_w*Gcu)}


def audit(s,g,r):
    """Reconstruct signed paths/units and every physical balance independently."""
    t=np.array([r['temperatures_k'][n] for n in TEMPERATURE_NODES]);st=r['stage_budget']
    Gcu,Gau,Rcu=wire_coefficients(g);I=s.current_a;Q=s.detector_bias_w+s.detector_absorbed_w
    au=Gau*(s.ambient_k-t[4]);cu=Gcu*(s.ambient_k-t[0]);J=I*I*Rcu
    attach=s.die_attach_conductivity_w_mk/g['die_attach_thickness_over_area_m_inverse']*(t[4]-t[3])
    voltage=sum(v['voltage_v'] for v in st)+I*Rcu;P=I*voltage;sink=st[0]['qh_w']+cu+.5*J
    node=np.array([st[0]['qc_w']-st[1]['qh_w'],st[1]['qc_w']-st[2]['qh_w'],st[2]['qc_w']-attach,attach-Q-au])
    stage=[v['qh_w']-v['qc_w']-I*v['voltage_v'] for v in st]
    energy=P+Q+au+cu-.5*J-sink;hot=t[0]-s.ambient_k-s.heat_sink_k_w*sink
    extrema=[v.get('leg_temperature_extrema_k',[min(t[:4]),max(t[:4])]) for v in st]
    comparison=[abs(sink-r['bath_rejected_power_w']),abs(P-r['terminal_electrical_power_w']),
                abs(voltage-r['terminal_voltage_v']),abs(au-r['heat_paths_w']['Au_wires_into_die_w']),
                abs(cu-r['heat_paths_w']['Cu_conduction_into_hot_w']),abs(J-r['heat_paths_w']['Cu_total_joule_w'])]
    finite=np.isfinite([*t,voltage,P,sink,au,cu,J,*node,*stage,energy,hot,*comparison,*np.ravel(extrema)]).all()
    if (not finite or max(abs(node))>=1e-8 or abs(energy)>=1e-8 or max(abs(v) for v in stage)>=1e-9
            or abs(hot)>=2e-8 or max(comparison)>1e-10 or min(t)<180 or max(t)>390
            or min(x[0] for x in extrema)<180 or max(x[1] for x in extrema)>390
            or np.any(r['heat_paths_w']['gas_w']) or np.any(r['heat_paths_w']['radiation_w'])):
        raise AssertionError('Independent finite-sink control/balance failed; STOP')
    return {'Tdie_K':t[4],'hot_K':t[0],'cold_ceramic_K':t[3],'stage_lifts_K':t[:3]-t[1:4],
        'stage_leg_extrema_K':extrema,'leg_min_K':min(x[0] for x in extrema),'leg_max_K':max(x[1] for x in extrema),
        'assumed_continuation':s.material_model!='g1_constant' and max(x[1] for x in extrema)>300.,
        'terminal_V':voltage,'terminal_W':P,'module_W':r['module_electrical_power_w'],
        'sink_W':sink,'Qc_cold_W':st[2]['qc_w'],'Qdie_W':Q,'Au_into_die_W':au,'Cu_into_hot_W':cu,
        'Cu_joule_W':J,'direct_pin_input_W':cu-.5*J,'sink_minus_terminal_W':sink-P,
        'net_total_ambient_rejection_W':sink-au-cu+.5*J,'die_COP':Q/P if P>1e-14 else None,
        'cooler_COP':st[2]['qc_w']/r['module_electrical_power_w'] if r['module_electrical_power_w']>1e-14 else None,
        'independent_node_residuals_W':node,'independent_global_error_W':energy,'hot_sink_error_K':hot,
        'independent_stage_errors_W':stage,'max_reported_path_difference':max(comparison)}


def independent_branch(s,g,seed):
    """Independent package residual/initialization; original nonlinear legs unchanged."""
    transport=Transport(32);Gcu,Gau,Rcu=wire_coefficients(g);I=s.current_a
    Ga=s.die_attach_conductivity_w_mk/g['die_attach_thickness_over_area_m_inverse']
    def fields(t):
        stages=[transport.stage(b,th,tc,I,alpha_scale=s.pn_seebeck_scale,rho_scale=s.pn_resistivity_scale,
            k_scale=s.pn_thermal_conductivity_scale) for b,th,tc in zip(g['stages'],t[:3],t[1:4])]
        au=Gau*(s.ambient_k-t[4]);cu=Gcu*(s.ambient_k-t[0]);joule=I*I*Rcu
        sink=stages[0]['qh_w']+cu+.5*joule;attach=Ga*(t[4]-t[3]);Q=s.detector_bias_w+s.detector_absorbed_w
        res=np.array([stages[0]['qc_w']-stages[1]['qh_w'],stages[1]['qc_w']-stages[2]['qh_w'],
            stages[2]['qc_w']-attach,attach-Q-au,(t[0]-s.ambient_k-s.heat_sink_k_w*sink)/2])
        return stages,au,cu,joule,sink,res
    fit=least_squares(lambda t:fields(t)[-1],seed,bounds=(np.full(5,180.+1e-6),np.full(5,390.-1e-6)),
        max_nfev=120,ftol=1e-12,xtol=1e-12,gtol=1e-12)
    stages,au,cu,J,sink,res=fields(fit.x)
    if not fit.success or np.max(abs(res))>1e-8:
        raise OperatingPointFailure('Independent branch residual/optimizer failure',failure_diagnostics(s,fit.x,res,fit))
    V=sum(st['voltage_v'] for st in stages)
    return {'temperatures_k':dict(zip(TEMPERATURE_NODES,map(float,fit.x))),'stage_budget':stages,
        'heat_paths_w':{'Au_wires_into_die_w':au,'Cu_conduction_into_hot_w':cu,'Cu_total_joule_w':J,
                        'gas_w':[0.]*4,'radiation_w':[0.]*4},
        'module_voltage_v':V,'module_electrical_power_w':I*V,'terminal_voltage_v':V+I*Rcu,
        'terminal_electrical_power_w':I*(V+I*Rcu),'bath_rejected_power_w':sink,
        'independent_initial_seed_K':seed,'optimizer_success':bool(fit.success),'optimizer_message':str(fit.message),
        'nfev':int(fit.nfev),'residuals_W_and_scaled_K':res,'transport_computation':transport.statistics()}


def falling_brackets(rows):
    """Adjacent registered points only; failed gaps cannot form a bracket."""
    return [(a['case']['id'],b['case']['id']) for a,b in zip(rows,rows[1:])
        if a['status']==b['status']=='ACCEPTED' and a['audit']['Tdie_K']>TARGET_K>=b['audit']['Tdie_K']]


def nondominated(rows):
    good=[r for r in rows if r['status']=='ACCEPTED' and r['audit']['Tdie_K']<=TARGET_K]
    return [r['case']['id'] for r in good if not any(q['audit']['Tdie_K']<=r['audit']['Tdie_K']
        and q['audit']['terminal_W']<=r['audit']['terminal_W'] and
        (q['audit']['Tdie_K']<r['audit']['Tdie_K'] or q['audit']['terminal_W']<r['audit']['terminal_W']) for q in good)]


def analyze(plan,results,crossings):
    tables=[];response=[];replays=[];old=read(ROOT/'data/tec_material_plausibility_20261101/cases.json')
    oldplan=read(ROOT/'data/tec_material_plausibility_20261101/registration.json')['cases']
    for h in HYPOTHESES:
        for sink in SINKS:
            rows=[results[c['id']] for c in plan['grid'] if c['hypothesis']==h and c['sink_K_W']==sink]
            accepted=[r for r in rows if r['status']=='ACCEPTED'];hits=[r for r in accepted if r['audit']['Tdie_K']<=TARGET_K]
            tables.append({'hypothesis':h,'sink_K_W':sink,'accepted':len(accepted),
                'rejected':sum(r['status']=='REJECTED' for r in rows),'not_run':sum(r['status']=='NOT RUN' for r in rows),
                'minimum_grid_die_case':min(accepted,key=lambda r:r['audit']['Tdie_K'])['case']['id'] if accepted else None,
                'minimum_power_grid_target_case':min(hits,key=lambda r:r['audit']['terminal_W'])['case']['id'] if hits else None,
                'target_nondominated_grid_cases':nondominated(rows)})
        for I in CURRENTS:
            for left,right in zip(SINKS,SINKS[1:]):
                a=results[f'grid_{h}_R{left:g}_I{I:g}'];b=results[f'grid_{h}_R{right:g}_I{I:g}']
                if a['status']==b['status']=='ACCEPTED':
                    response.append({'hypothesis':h,'current_A':I,'left_sink':left,'right_sink':right,
                        'delta_hot_K':b['audit']['hot_K']-a['audit']['hot_K'],
                        'delta_die_K':b['audit']['Tdie_K']-a['audit']['Tdie_K'],
                        'delta_terminal_W':b['audit']['terminal_W']-a['audit']['terminal_W']})
    for c in plan['grid']:
        if c['sink_K_W']!=0:continue
        previous=next((p for p in oldplan if p['group']=='core' and p['hypothesis']==c['hypothesis']
                       and p['current_A']==c['current_A'] and p['wires_ON']),None)
        if previous:
            prior=old[previous['id']]
            new=results[c['id']];row={'case':c['id'],'previous_status':prior['status'],'new_status':new['status']}
            if new['status']!='NOT RUN' and new['status']!=prior['status']:raise AssertionError('Frozen replay acceptance changed; STOP')
            if prior['status']==new['status']=='ACCEPTED':
                row.update(die_error_K=abs(prior['summary']['Tdie_K']-new['audit']['Tdie_K']),
                    voltage_error_V=abs(prior['summary']['terminal_voltage_V']-new['audit']['terminal_V']))
                if row['die_error_K']>1e-6 or row['voltage_error_V']>1e-7:raise AssertionError('Frozen R=0 replay failed; STOP')
            elif prior['status']==new['status']=='REJECTED':
                row['previous_classification']=prior['diagnostics']['classification'];row['new_classification']=new['diagnostics']['classification']
                if row['previous_classification']!=row['new_classification']:raise AssertionError('Frozen rejection classification changed; STOP')
            replays.append(row)
    good=[r for r in results.values() if r['status']=='ACCEPTED']
    return {'tables':tables,'paired_sink_responses':response,'baseline_replays':replays,'target_crossings':crossings,
        'coverage_by_family':{f:{s:sum(r['case']['family']==f and r['status']==s for r in results.values())
            for s in ('ACCEPTED','REJECTED','NOT RUN')} for f in ('grid','constant','branch','target')},
        'primary_source_coverage':{'measured_domain':sum(r['case']['family']=='grid' and not r['audit']['assumed_continuation'] for r in good),
            'assumed_continuation':sum(r['case']['family']=='grid' and r['audit']['assumed_continuation'] for r in good)},
        'max_global_error_W':max(abs(r['audit']['independent_global_error_W']) for r in good),
        'max_physical_node_error_W':max(max(abs(v) for v in r['audit']['independent_node_residuals_W']) for r in good),
        'max_stage_error_W':max(abs(v) for r in good for v in r['audit']['independent_stage_errors_W']),
        'max_hot_sink_error_K':max(abs(r['audit']['hot_sink_error_K']) for r in good),
        'sink_load_scaling_controls':[{'sink_K_W':r,'sink_load_W':q,'hot_rise_K':r*q} for r in SINKS for q in (.5,1.,2.,3.)],
        'no_OEM_fit':True,'new_3D_runs':0,'real_device_feasibility':'unresolved','g1p7_and_fitted_triples':'NOT RUN'}


def run(out):
    out=Path(out).resolve()
    if out.exists():raise ValueError('Choose absent output directory; preserve all prior attempts')
    out.mkdir(parents=True);plan=design();g=geometry()
    extra=('fem/results/geometry_complete_checkpoint_20261030/checksums.json',
        'fem/results/geometry_complete_checkpoint_20261030/mesh.npz',
        'fem/results/geometry_complete_checkpoint_20261030/reference.step.gz',
        'data/tec_material_plausibility_20261101/cases.json','data/tec_material_plausibility_20261101/checksums.json',
        'data/tec_material_plausibility_20261101/registration.json',
        'data/tec_identifiability_20261101/checksums.json')
    inputs={p:sha(ROOT/p) for p in (*SOURCES,*extra)}
    write(out/'registration.json',{'observed_UTC':datetime.now(timezone.utc).isoformat(),'baseline':BASELINE,
        'protocol':NOTE.read_text().split('## Results')[0],'producer_sha256':sha(__file__),'design':plan,'input_sha256':inputs,
        'baseline_live_Rev3_sha256':sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'),
        'original_geometry':g,'no_fitting_or_new_3D':True})
    (out/'producer.py.source').write_bytes(Path(__file__).read_bytes())
    invalid=[]
    for changes in ({'heat_sink_k_w':-1.},{'heat_sink_k_w':float('nan')},{'current_a':1.01},{'pn_resistivity_scale':0.}):
        try:Scenario(**changes).validate()
        except ValueError:invalid.append({'input':{k:str(v) for k,v in changes.items()},'rejected':True})
        else:raise AssertionError('Invalid input accepted; STOP')
    for T in (179.999,390.001):
        try:graded_tec.props('P',T)
        except ValueError:invalid.append({'property_temperature_K':T,'rejected':True})
        else:raise AssertionError('Invalid material domain accepted; STOP')
    write(out/'input_controls.json',invalid)
    start=time.monotonic();results={};crossings={}
    def timeout(*_):raise TimeoutError('Registered per-call/total reduced deadline')
    previous=signal.signal(signal.SIGALRM,timeout)
    def call(c):
        remaining=600-(time.monotonic()-start);t=time.monotonic()
        row={'case':c,'status':'NOT RUN','reason':'Registered 600-second budget exhausted'}
        if remaining>0:
            s=scenario(c);r=None;signal.setitimer(signal.ITIMER_REAL,min(8.,remaining))
            try:
                r=independent_branch(s,g,c['seed_K']) if c['family']=='branch' else solve(s,g,transport_intervals=32)
                row={'case':c,'status':'ACCEPTED','result':r,'audit':audit(s,g,r)}
            except AssertionError as error:
                results[c['id']]={'case':c,'status':'REJECTED','reason':str(error),'result':r}
                write(out/'cases.json',results);raise
            except (ValueError,RuntimeError,TimeoutError,FloatingPointError) as error:
                row={'case':c,'status':'REJECTED','reason':str(error),
                    'diagnostics':getattr(error,'diagnostics',failure_diagnostics(s,error=str(error)))}
            finally:signal.setitimer(signal.ITIMER_REAL,0.)
        row['seconds']=time.monotonic()-t;results[c['id']]=row;write(out/'cases.json',results);return row
    try:
        controls=[]
        for c in plan['constant']:
            row=call(c)
            if row['status']!='ACCEPTED':raise AssertionError('Constant control did not complete; STOP')
            exact=constant_exact(scenario(c),g);s=row['audit'];t=list(row['result']['temperatures_k'].values())
            check={'case':c['id'],'max_temperature_error_K':float(np.max(abs(np.array(t)-exact['temperatures_K']))),
                'voltage_error_V':abs(s['terminal_V']-exact['terminal_V']),'sink_error_W':abs(s['sink_W']-exact['sink_W'])}
            if c['current_A']==0:
                zero=zero_current_exact(scenario(c),g);check['zero_current_error']=max(abs(s['Tdie_K']-zero['die_K']),abs(s['hot_K']-zero['hot_K']),abs(s['sink_W']-zero['sink_W']))
            check['passed']=check['max_temperature_error_K']<1e-6 and check['voltage_error_V']<1e-7 and check['sink_error_W']<1e-8 and check.get('zero_current_error',0)<1e-6
            controls.append(check);write(out/'controls.json',controls)
            if not check['passed']:raise AssertionError('Independent exact constant sink control failed; STOP')
        for c in plan['grid']:call(c)
        branches=[]
        for c in plan['branch']:
            ref=results[f"grid_nominal_R{c['sink_K_W']:g}_I0.3"]
            if ref['status']!='ACCEPTED':
                results[c['id']]={'case':c,'status':'NOT RUN','reason':'Primary reference rejected/unattempted'};continue
            row=call(c)
            if row['status']!='ACCEPTED':raise AssertionError('Independent branch check did not complete; STOP')
            difference=max(abs(row['result']['temperatures_k'][n]-ref['result']['temperatures_k'][n]) for n in TEMPERATURE_NODES)
            dV=abs(row['audit']['terminal_V']-ref['audit']['terminal_V']);dP=abs(row['audit']['terminal_W']-ref['audit']['terminal_W'])
            dQ=max(abs(l[k]-r[k]) for l,r in zip(row['result']['stage_budget'],ref['result']['stage_budget']) for k in ('qc_w','qh_w'))
            dSink=abs(row['audit']['sink_W']-ref['audit']['sink_W'])
            branches.append({'case':c['id'],'temperature_difference_K':difference,'V_difference':dV,'P_difference_W':dP,
                'stage_heat_difference_W':dQ,'sink_difference_W':dSink})
            write(out/'branch_checks.json',branches)
            if difference>1e-5 or dV>1e-7 or max(dP,dQ,dSink)>1e-8:raise AssertionError('Different admitted branch/control; STOP')
        for R in SINKS:
            rows=[results[c['id']] for c in plan['grid'] if c['hypothesis']=='nominal' and c['sink_K_W']==R]
            brackets=falling_brackets(rows);cross={'registered_falling_grid_brackets':brackets,'attempts':[],'status':'NOT RUN: no adjacent admitted falling bracket'}
            if brackets:
                lo,hi=[results[k] for k in brackets[0]];cross['status']='UNRESOLVED: ten-midpoint limit'
                for slot in [c for c in plan['target_slots'] if c['sink_K_W']==R]:
                    if 0<=TARGET_K-hi['audit']['Tdie_K']<=TARGET_TOL_K:cross['status']='PASS';break
                    c=dict(slot,current_A=.5*(lo['case']['current_A']+hi['case']['current_A']));row=call(c);cross['attempts'].append(c['id'])
                    if row['status']!='ACCEPTED':cross['status']='STOP: rejected/unattempted midpoint; no gap bridged';break
                    if not hi['audit']['Tdie_K']-1e-5<=row['audit']['Tdie_K']<=lo['audit']['Tdie_K']+1e-5:
                        cross['status']='STOP: nonmonotone midpoint/possible branch change';break
                    if row['audit']['Tdie_K']>TARGET_K:lo=row
                    else:hi=row
                if 0<=TARGET_K-hi['audit']['Tdie_K']<=TARGET_TOL_K and not cross['status'].startswith('STOP'):cross['status']='PASS'
                cross.update(final_bracket=[lo['case']['id'],hi['case']['id']],cold_side_case=hi['case']['id'])
            crossings[str(R)]=cross
            for slot in [c for c in plan['target_slots'] if c['sink_K_W']==R and c['id'] not in results]:
                results[slot['id']]={'case':slot,'status':'NOT RUN','reason':'Unused bounded target slot: '+cross['status']}
            write(out/'cases.json',results);write(out/'target_crossings.json',crossings)
    except Exception as error:
        write(out/'STOP.json',{'observed_UTC':datetime.now(timezone.utc).isoformat(),'reason':str(error),'elapsed_seconds':time.monotonic()-start})
        write(out/'cases.json',results);raise
    finally:signal.setitimer(signal.ITIMER_REAL,0.);signal.signal(signal.SIGALRM,previous)
    for p,h in inputs.items():
        if sha(ROOT/p)!=h:raise AssertionError('Frozen scientific input changed; STOP: '+p)
    analysis=analyze(plan,results,crossings);analysis['elapsed_reduced_seconds']=time.monotonic()-start
    write(out/'analysis.json',analysis);print(analysis['coverage_by_family'],analysis['elapsed_reduced_seconds'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.out)
