"""Bounded local evidence priorities; unchanged physical model, no fitting/3D."""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import signal
import time

import numpy as np

from .integrated_reference import Scenario, geometry, solve, failure_diagnostics, TEMPERATURE_NODES
from .finite_sink_study import wire_coefficients
from .tec_material_plausibility import ROOT, read, write, sha

BASELINE = '84e1b4f90e090604739f65c3ba1e2d5c3c4a2a39'
NOTE = ROOT/'docs/PHYSICAL_INPUT_QUALIFICATION_20261101.md'
OLD = ROOT/'data/finite_sink_20261101'
FACTORS = ('pn_seebeck_scale', 'pn_resistivity_scale', 'pn_thermal_conductivity_scale',
           'au_wire_conductance_scale', 'die_attach_conductivity_w_mk')
STEPS = (.01, .005)
TOL = .0001


def scenario(current, factor=None, multiplier=1.):
    s = Scenario(ambient_k=300., current_a=current, material_model='zhang2025_nonlinear',
        heat_sink_k_w=2., detector_bias_w=.002, detector_absorbed_w=0., cavity_pressure_pa=0.,
        cap_emissivity=0., window_thermal_emissivity=0.)
    if factor is not None:
        if factor not in FACTORS or not np.isfinite(multiplier) or not .99 <= multiplier <= 1.01:
            raise ValueError('Outside registered one-factor input')
        s = replace(s, **{factor: multiplier})
    if not .25 <= current <= .35:
        raise ValueError('Outside registered local current branch')
    return s.validate()


def balance(s, g, r):
    """Independent signed balance: Au scale belongs in G, not a posterior correction."""
    t = np.array([r['temperatures_k'][n] for n in TEMPERATURE_NODES])
    st = r['stage_budget']; I = s.current_a
    Gcu, Gau, Rcu = wire_coefficients(g)
    au = Gau*s.au_wire_conductance_scale*(s.ambient_k-t[4])
    cu = Gcu*s.cu_wire_conductance_scale*(s.ambient_k-t[0]); J = I*I*Rcu
    attach = s.die_attach_conductivity_w_mk/g['die_attach_thickness_over_area_m_inverse']*(t[4]-t[3])
    V = sum(q['voltage_v'] for q in st)+I*Rcu; P = I*V
    sink = st[0]['qh_w']+cu+.5*J; Q = s.detector_bias_w+s.detector_absorbed_w
    nodes = [st[0]['qc_w']-st[1]['qh_w'], st[1]['qc_w']-st[2]['qh_w'], st[2]['qc_w']-attach, attach-Q-au]
    stages = [q['qh_w']-q['qc_w']-I*q['voltage_v'] for q in st]
    global_error = P+Q+au+cu-.5*J-sink
    hot_error = t[0]-s.ambient_k-s.heat_sink_k_w*sink
    ext = [q['leg_temperature_extrema_k'] for q in st]
    diffs = [sink-r['bath_rejected_power_w'], P-r['terminal_electrical_power_w'],
             V-r['terminal_voltage_v'], au-r['heat_paths_w']['Au_wires_into_die_w'],
             cu-r['heat_paths_w']['Cu_conduction_into_hot_w'], J-r['heat_paths_w']['Cu_total_joule_w']]
    if (not np.isfinite([*t,*nodes,*stages,global_error,hot_error,*diffs,*np.ravel(ext)]).all()
            or max(abs(x) for x in stages)>=1e-9 or max(abs(x) for x in nodes)>=1e-8
            or abs(global_error)>=1e-8 or abs(hot_error)>=2e-8 or max(abs(x) for x in diffs)>=1e-10
            or min(t)<180 or max(t)>390 or min(x[0] for x in ext)<180 or max(x[1] for x in ext)>390
            or np.any(r['heat_paths_w']['gas_w']) or np.any(r['heat_paths_w']['radiation_w'])):
        raise AssertionError('Independent physical balance/domain check failed; STOP')
    return dict(Tdie_K=float(t[4]),hot_K=float(t[0]),cold_ceramic_K=float(t[3]),
        terminal_W=P,terminal_V=V,sink_W=sink,Qc_cold_W=st[2]['qc_w'],
        Au_into_die_W=au,Cu_into_hot_W=cu,Cu_joule_W=J,attach_W=attach,
        node_errors_W=nodes,stage_errors_W=stages,global_error_W=global_error,hot_error_K=hot_error,
        leg_extrema_K=ext,assumed_continuation=bool(max(x[1] for x in ext)>300),
        net_ambient_rejection_W=sink-au-cu+.5*J,die_COP=Q/P)


def partial(minus, plus, h):
    return {key:(plus[key]-minus[key])/(2*h) for key in ('Tdie_K','terminal_W')}


def stable(a,b):
    return all(abs(a[k]-b[k])<=.02*max(abs(b[k]),floor)
               for k,floor in (('Tdie_K',.01),('terminal_W',1e-4)))


def implicit(Tp,Pp,TI,PI,P):
    if not np.isfinite([Tp,Pp,TI,PI,P]).all() or TI>=0 or P<=0:
        raise ValueError('No admitted falling local target derivative')
    shift = -Tp/TI
    derivative = Pp+PI*shift
    return {'current_A_per_log_factor':shift,'power_W_per_log_factor':derivative,
            'power_elasticity':derivative/P}


def valid_bracket(lo,hi):
    return (lo['status']==hi['status']=='ACCEPTED'
            and lo['case']['current_A']<hi['case']['current_A']
            and lo['audit']['Tdie_K']>200>=hi['audit']['Tdie_K'])


def target(lo,hi,slots,call):
    ids=[]
    if not valid_bracket(lo,hi):
        return {'status':'STOP','reason':'No accepted falling bracket; no expansion or gap bridge','attempts':ids}
    initial=[lo['case']['id'],hi['case']['id']]
    for slot in slots:
        if 0<=200-hi['audit']['Tdie_K']<=TOL:break
        row=call(dict(slot,current_A=.5*(lo['case']['current_A']+hi['case']['current_A'])))
        ids.append(row['case']['id'])
        if row['status']!='ACCEPTED':
            return {'status':'STOP','reason':'Rejected/unattempted midpoint; no gap bridged','attempts':ids,'initial_bracket':initial}
        if not hi['audit']['Tdie_K']-1e-5<=row['audit']['Tdie_K']<=lo['audit']['Tdie_K']+1e-5:
            return {'status':'STOP','reason':'Nonmonotone/branch-incompatible midpoint','attempts':ids,'initial_bracket':initial}
        if row['audit']['Tdie_K']>200:lo=row
        else:hi=row
    return {'status':'PASS' if 0<=200-hi['audit']['Tdie_K']<=TOL else 'STOP',
        'reason':'Actual cold-side target' if 0<=200-hi['audit']['Tdie_K']<=TOL else 'Midpoint budget exhausted',
        'initial_bracket':initial,'final_bracket':[lo['case']['id'],hi['case']['id']],
        'cold_side_case':hi['case']['id'],'attempts':ids}


def run(out):
    out=Path(out)
    if out.exists():raise ValueError('Absent output directory required; no overwrite/retry')
    out.mkdir(parents=True)
    old=read(OLD/'cases.json');cross=read(OLD/'target_crossings.json')['2.0']
    ref=old[cross['cold_side_case']];Iref=ref['case']['current_A'];g=geometry()
    base_inputs=read(OLD/'registration.json')['input_sha256']
    paths=(*base_inputs,'tecooledmct/finite_sink_study.py','data/finite_sink_20261101/cases.json',
        'data/finite_sink_20261101/checksums.json','data/tec_identifiability_20261101/analysis.json',
        'data/native_gas_flux_forensics_20261101/checksums.json',
        'data/isolated_cap_native_gas_20261101/phase_A/cap_window_mm_derivative.step',
        'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf')
    inputs={p:sha(ROOT/p) for p in paths}
    registration={'observed_UTC':datetime.now(timezone.utc).isoformat(),'baseline':BASELINE,
        'protocol':NOTE.read_text().split('## Results')[0],'producer_sha256':sha(__file__),
        'input_sha256':inputs,'reference_case':cross['cold_side_case'],'reference_current_A':Iref,
        'factors':FACTORS,'fractional_steps':STEPS,'maximum_calls':150,'seconds_limit':600.,
        'individual_seconds_limit':8.,'nominal_target_slots':7,'endpoint_target_slots':10,
        'original_geometry':g,'source_measured_K':[40,300],'active_K':[180,390],
        'actual_device_feasibility':'unresolved','new_3D_calls':0}
    write(out/'registration.json',registration)
    (out/'producer.py.source').write_bytes(Path(__file__).read_bytes())
    rows={};targets={};derivatives={};start=time.monotonic()
    def timeout(*_):raise TimeoutError('Registered reduced deadline')
    previous=signal.signal(signal.SIGALRM,timeout)
    def call(c):
        remain=600-(time.monotonic()-start)
        if len(rows)>=150:raise AssertionError('Call cap; STOP')
        t=time.monotonic();row={'case':c,'status':'NOT RUN','reason':'Total time budget exhausted'}
        s=scenario(c['current_A'],c.get('factor'),c.get('multiplier',1.))
        if remain>0:
            signal.setitimer(signal.ITIMER_REAL,min(8.,remain))
            try:
                r=solve(s,g,transport_intervals=32)
                row={'case':c,'status':'ACCEPTED','result':r,'audit':balance(s,g,r)}
            except AssertionError as error:
                rows[c['id']]={'case':c,'status':'REJECTED','reason':str(error)};write(out/'cases.json',rows);raise
            except (ValueError,RuntimeError,TimeoutError,FloatingPointError) as error:
                row={'case':c,'status':'REJECTED','reason':str(error),
                     'diagnostics':getattr(error,'diagnostics',failure_diagnostics(s,error=str(error)))}
            finally:signal.setitimer(signal.ITIMER_REAL,0.)
        row['seconds']=time.monotonic()-t;rows[c['id']]=row;write(out/'cases.json',rows)
        return row
    def spec(id,family,**kw):return dict(id=id,family=family,**kw)
    try:
        replay=call(spec('baseline','baseline',current_A=Iref))
        if replay['status']!='ACCEPTED':raise AssertionError('Baseline unavailable; STOP')
        replay_error={'Tdie_K':abs(replay['audit']['Tdie_K']-ref['audit']['Tdie_K']),
                      'terminal_V':abs(replay['audit']['terminal_V']-ref['audit']['terminal_V'])}
        if replay_error['Tdie_K']>1e-6 or replay_error['terminal_V']>1e-7:
            raise AssertionError('Frozen baseline replay failed; STOP')
        for f in FACTORS:
            for h in STEPS:
                for sign in (-1,1):
                    call(spec(f'{f}_h{h:g}_{sign:+d}','factor',current_A=Iref,factor=f,multiplier=1+sign*h,h=h,sign=sign))
        cm=call(spec('current_minus','current',current_A=Iref-.001))
        cp=call(spec('current_plus','current',current_A=Iref+.001))
        if cm['status']!=cp['status'] or cm['status']!='ACCEPTED':raise AssertionError('Current derivative unavailable; STOP')
        current=partial(cm['audit'],cp['audit'],.001)
        lo,hi=[old[k] for k in cross['final_bracket']]
        archived_secant=partial(lo['audit'],hi['audit'],.5*(hi['case']['current_A']-lo['case']['current_A']))
        if not stable(current,archived_secant):raise AssertionError('Current derivative disagrees with archived branch; STOP')
        nominal=target(lo,hi,[spec(f'nominal_step{j}','target') for j in range(7)],call)
        targets['nominal']=nominal
        if nominal['status']!='PASS':raise AssertionError('Nominal fine target unavailable; STOP')
        nom=rows.get(nominal['cold_side_case'],old.get(nominal['cold_side_case']))
        for f in FACTORS:
            pairs=[]
            for h in STEPS:
                pair=[rows[f'{f}_h{h:g}_{sign:+d}'] for sign in (-1,1)]
                if any(r['status']!='ACCEPTED' for r in pair):break
                pairs.append(partial(pair[0]['audit'],pair[1]['audit'],h))
            if len(pairs)!=2 or not stable(*pairs):
                derivatives[f]={'status':'STOP','reason':'Finite-difference failure or step instability'};continue
            local=implicit(pairs[1]['Tdie_K'],pairs[1]['terminal_W'],current['Tdie_K'],current['terminal_W'],nom['audit']['terminal_W'])
            derivatives[f]={'status':'PASS','h01':pairs[0],'h005':pairs[1],**local}
            for sign in (-1,1):
                key=f'{f}_{sign:+d}';shift=local['current_A_per_log_factor']*sign*.01
                center=nom['case']['current_A']+shift;width=max(5e-6,.05*abs(shift))
                if not .25<=center-width<center+width<=.35:
                    targets[key]={'status':'NOT RUN','reason':'Predicted bracket outside registered current interval'};continue
                ends=[call(spec(f'{key}_end{j}','target_endpoint',current_A=center+sgn*width,
                          factor=f,multiplier=1+sign*.01)) for j,sgn in enumerate((-1,1))]
                slots=[spec(f'{key}_step{j}','target',factor=f,multiplier=1+sign*.01) for j in range(10)]
                targets[key]=target(*ends,slots,call)
            write(out/'targets.json',targets);write(out/'derivatives.json',derivatives)
    except Exception as error:
        write(out/'STOP.json',{'observed_UTC':datetime.now(timezone.utc).isoformat(),'reason':str(error)})
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0.);signal.signal(signal.SIGALRM,previous)
        write(out/'cases.json',rows);write(out/'targets.json',targets);write(out/'derivatives.json',derivatives)
        write(out/'execution.json',{'observed_end_UTC':datetime.now(timezone.utc).isoformat(),
            'seconds':time.monotonic()-start,'recorded_calls':len(rows),'maximum_calls':150,
            'unused_maximum_slots_NOT_RUN':150-len(rows),
            'counts':{s:sum(r['status']==s for r in rows.values()) for s in ('ACCEPTED','REJECTED','NOT RUN')}})
    for p,h in inputs.items():
        if sha(ROOT/p)!=h:raise AssertionError('Frozen input changed: '+p)
    good=[r['audit'] for r in rows.values() if r['status']=='ACCEPTED']
    write(out/'controls.json',{'baseline_replay_error':replay_error,'current_partial':current,
        'archived_current_secant':archived_secant,'max_stage_W':max(abs(x) for a in good for x in a['stage_errors_W']),
        'max_node_W':max(abs(x) for a in good for x in a['node_errors_W']),
        'max_global_W':max(abs(a['global_error_W']) for a in good),
        'max_hot_K':max(abs(a['hot_error_K']) for a in good)})
    print(read(out/'execution.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out)
