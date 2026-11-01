"""Isolated, explicitly calibration-authorized candidate; no baseline mutation."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import signal
import time
import numpy as np
from scipy.optimize import least_squares

from .integrated_reference import Scenario,solve,failure_diagnostics
from .physical_input_qualification import balance
from .finite_sink_study import constant_exact,audit as constant_balance
from .tec_material_plausibility import ROOT,read,write,sha,ScaledMeasuredProfile
from .nonlinear_tec import Transport
from .oem_phase_a import bounded_leg
from .tec_candidate_geometry import ID,COUNTS,WIDTHS

DATA=ROOT/'data/tec_candidate_29114_20261101'
CALIBRATION=((.2,0.),(.2,.1),(.6,0.),(.6,.1))


def geometry(folder=DATA):
    if read(folder/'geometry/analytic_audit.json')['status']!='PASS' or read(folder/'geometry/si_reader.json')['status']!='PASS':
        raise ValueError('Unqualified candidate geometry; STOP')
    return dict(stages=[dict(couples=n,leg_area_m2=.16e-6,leg_length_m=.5e-3) for n in COUNTS],
        ceramic_sides_area_m2=[(w*.001)**2 for w in WIDTHS],die_area_m2=1e-6,
        die_attach_thickness_over_area_m_inverse=30.,wires=[],source_archive=str(folder.relative_to(ROOT)),
        source_sha256={'candidate_design':sha(folder/'geometry/design.json'),'candidate_STEP':sha(folder/'geometry/candidate_mm.step')},
        material_status='distinct source specimens; candidate calibration separate, no manufactured grade identification')


def scenario(I,Q,hot=300.15,S=1.,rho=1.,attach=1.,material='zhang2025_nonlinear'):
    if not (.9<=S<=1.1 and .8<=rho<=1.2):raise ValueError('Calibration beyond registered bounds')
    return Scenario(current_a=I,ambient_k=hot,heat_sink_k_w=0.,material_model=material,
        detector_bias_w=Q,detector_absorbed_w=0.,cavity_pressure_pa=0.,cap_emissivity=0.,window_thermal_emissivity=0.,
        pn_seebeck_scale=S,pn_resistivity_scale=rho,pn_thermal_conductivity_scale=1.,die_attach_conductivity_w_mk=attach).validate()


def summary(r):
    t=r['temperatures_k'];st=r['stage_budget'];ext=[s.get('leg_temperature_extrema_k',[min(t.values()),max(t.values())]) for s in st]
    return dict(cold_K=t['cold_ceramic'],die_K=t['MCT_die'],lift_K=t['hot_ceramic']-t['cold_ceramic'],
        V=r['module_voltage_v'],P_W=r['module_electrical_power_w'],Qc_W=st[2]['qc_w'],
        sink_W=r['bath_rejected_power_w'],stage_lifts_K=[t[a]-t[b] for a,b in zip(('hot_ceramic','stage1','stage2'),('stage1','stage2','cold_ceramic'))],
        leg_min_K=min(x[0] for x in ext),leg_max_K=max(x[1] for x in ext),assumed_continuation=bool(r['material_model']!='g1_constant' and max(x[1] for x in ext)>300.))


def compare(points,rows):
    out=[]
    for p in points:
        key=(p['current_a'],p['load_w']);row=rows[key]
        r=dict(source_id=p['id'],current_A=key[0],load_W=key[1],field=p['field'],source_value=p['value'],
            digitization_bound=p['value_reading_bound'],source_current_bound_A=p['current_reading_bound_a'],
            partition='CALIBRATION previously seen' if key in CALIBRATION else 'EVALUATION previously seen',
            independent_validation=False,case=row['id'],status=row['status'])
        if row['status']=='ACCEPTED':
            value=row['summary']['lift_K' if p['field']=='delta_t_k' else 'V'];delta=value-p['value']
            r.update(model=value,signed_difference=delta,absolute_difference=abs(delta),
                relative_difference=delta/p['value'],assumed_continuation=row['summary']['assumed_continuation'])
        out.append(r)
    return out


def metrics(rows):
    good=[x for x in rows if x['status']=='ACCEPTED'];T=[x for x in good if x['field']=='delta_t_k'];V=[x for x in good if x['field']=='voltage_v']
    if not T or not V:return dict(alignment_PASS=False,accepted_observables=len(good),total_observables=len(rows))
    tmae=float(np.mean([x['absolute_difference'] for x in T]));trmax=max(x['absolute_difference'] for x in T)
    vrms=float(np.sqrt(np.mean([x['relative_difference']**2 for x in V])));vrmax=max(abs(x['relative_difference']) for x in V)
    return dict(alignment_PASS=bool(len(good)==len(rows) and tmae<=8 and vrms<=.15 and trmax<=15 and vrmax<=.25),
        accepted_observables=len(good),total_observables=len(rows),lift_MAE_K=tmae,lift_signed_mean_K=float(np.mean([x['signed_difference'] for x in T])),
        max_absolute_lift_K=trmax,V_relative_RMS=vrms,V_MAE=float(np.mean([x['absolute_difference'] for x in V])),
        V_signed_mean=float(np.mean([x['signed_difference'] for x in V])),max_absolute_relative_V=vrmax)


def independent_checks(g):
    checks=[]
    for index,hot,cold,I in ((0,295.,250.,.15),(2,260.,210.,.3)):
        geom=g['stages'][index];A=geom['leg_area_m2'];n=geom['couples']
        direct=Transport(32).stage(geom,hot,cold,I)
        pn={p:bounded_leg(ScaledMeasuredProfile((1.,1.,1.)),p,hot,cold,I/A*(1 if p=='N' else -1),geom['leg_length_m'],intervals=32) for p in ('P','N')}
        qc=-n*A*sum(v['q_cold_w_m2'] for v in pn.values());V=n*(pn['N']['electric_integral_v']-pn['P']['electric_integral_v'])
        check=dict(stage=index,Qc_error_W=abs(direct['qc_w']-qc),V_error=abs(direct['voltage_v']-V),
            source_min_K=min(v['min_k'] for v in pn.values()),source_max_K=max(v['max_k'] for v in pn.values()))
        check['PASS']=check['Qc_error_W']<3e-8 and check['V_error']<3e-7 and 180<check['source_min_K']<=check['source_max_K']<300
        checks.append(check)
    if not all(c['PASS'] for c in checks):raise AssertionError('Independent candidate BVP gate failed')
    return checks


def run(folder):
    folder=Path(folder).resolve();out=folder/'study'
    if out.exists():raise ValueError('Absent study directory required; no rerun/overwrite')
    g=geometry(folder);out.mkdir();oem=read(ROOT/'data/g2c/oem2019_curves_v1.json')
    points=[p for p in oem['points'] if p['panel']=='300K_vacuum'];conditions=sorted({(p['current_a'],p['load_w']) for p in points})
    reg=read(folder/'registration.json')
    for p,h in reg['input_sha256'].items():
        if sha(ROOT/p)!=h:raise ValueError('Frozen original changed')
    source=ROOT/'tecooledmct/tec_candidate_study.py';(out/'producer.py.source').write_bytes(source.read_bytes())
    write(out/'registration.json',dict(observed_UTC=datetime.now(timezone.utc).isoformat(),protocol=reg['protocol'],
        source_sha256=sha(source),candidate_geometry=g,conditions=conditions,calibration=CALIBRATION,
        S_bounds=[.9,1.1],rho_bounds=[.8,1.2],k_scale=1.,maximum_calls=240,total_seconds=600.,per_call_seconds=8.,
        jacobian_fractional_step=.001,max_refinement_nfev=8,
        dependency_sha256={p:sha(ROOT/p) for p in ('tecooledmct/physical_input_qualification.py','tecooledmct/tec_material_plausibility.py','tecooledmct/tec_candidate_geometry.py')}))
    results={};cache={};start=time.monotonic()
    def timeout(*_):raise TimeoutError('Registered candidate runtime limit')
    previous=signal.signal(signal.SIGALRM,timeout)
    def call(I,Q,S=1.,rho=1.,hot=300.15,attach=1.,use='primary',material='zhang2025_nonlinear'):
        key=(I,Q,S,rho,hot,attach,material)
        if key in cache:
            r=results[cache[key]]
            if use not in r['uses']:r['uses'].append(use)
            return r
        if len(results)>=240:raise RuntimeError('Registered240-call cap; STOP')
        id=f'{len(results):03d}';s=scenario(I,Q,hot,S,rho,attach,material);remaining=600-(time.monotonic()-start);t=time.monotonic()
        row=dict(id=id,current_A=I,load_W=Q,S_scale=S,rho_scale=rho,hot_K=hot,attach_k=attach,material=material,uses=[use],status='NOT RUN',reason='600-second budget exhausted')
        if remaining>0:
            signal.setitimer(signal.ITIMER_REAL,min(8.,remaining))
            try:
                r=solve(s,g,transport_intervals=32)
                row.update(status='ACCEPTED',result=r,summary=summary(r),audit=(constant_balance if material=='g1_constant' else balance)(s,g,r))
                row.pop('reason',None)
            except AssertionError as error:
                row.update(status='REJECTED',reason=str(error),result=r);results[id]=row;write(out/'cases.json',results);raise
            except (ValueError,RuntimeError,TimeoutError,FloatingPointError) as error:
                row.update(status='REJECTED',reason=str(error),diagnostics=getattr(error,'diagnostics',failure_diagnostics(s,error=str(error))))
            finally:signal.setitimer(signal.ITIMER_REAL,0.)
        row['seconds']=time.monotonic()-t;results[id]=row;cache[key]=id;write(out/'cases.json',results);return row
    def rows_for(S,rho,use,conds=conditions):return {(I,Q):call(I,Q,S,rho,use=use) for I,Q in conds}
    fit=dict(status='NOT RUN',reason='No-fit alignment gate not yet evaluated');trials=[]
    try:
        controls=[]
        for I in (0.,.1,.3):
            row=call(I,.002,hot=300.,material='g1_constant',use='constant_control')
            if row['status']!='ACCEPTED':raise AssertionError('Candidate constant control rejected')
            exact=constant_exact(scenario(I,.002,hot=300.,material='g1_constant'),g)
            dt=max(abs(x-y) for x,y in zip(row['result']['temperatures_k'].values(),exact['temperatures_K']))
            check=dict(case=row['id'],temperature_error_K=dt,voltage_error=abs(row['summary']['V']-exact['terminal_V']),sink_error_W=abs(row['summary']['sink_W']-exact['sink_W']))
            if dt>1e-6 or check['voltage_error']>1e-7 or check['sink_error_W']>1e-8:raise AssertionError('Analytic candidate control failed')
            controls.append(check)
        write(out/'constant_controls.json',controls)
        signal.setitimer(signal.ITIMER_REAL,30.)
        checks=independent_checks(g);signal.setitimer(signal.ITIMER_REAL,0.);write(out/'independent_BVP.json',checks)
        nofit=rows_for(1.,1.,'no_fit');no_compare=compare(points,nofit);no_metrics=metrics(no_compare)
        write(out/'no_fit_comparison.json',dict(metrics=no_metrics,rows=no_compare))
        for I in (.1,.2,.4,.6,.8,1.):call(I,0.,hot=300.,use='300K_control')
        for k in (.5,3.):call(.2,.1,attach=k,use='auxiliary_attach_control')
        chosen=(1.,1.)
        if no_metrics['alignment_PASS']:
            fit=dict(status='NOT RUN',reason='No-fit candidate already meets preregistered approximate gate')
        else:
            def objective(x,refinement=False):
                rows=rows_for(*map(float,x),use='calibration_refinement' if refinement else 'calibration_grid',conds=CALIBRATION)
                trial=dict(S=float(x[0]),rho=float(x[1]),cases=[r['id'] for r in rows.values()],accepted=all(r['status']=='ACCEPTED' for r in rows.values()))
                if trial['accepted']:
                    c=compare([p for p in points if (p['current_a'],p['load_w']) in CALIBRATION],rows)
                    residual=np.array([r['signed_difference']/(5. if r['field']=='delta_t_k' else .1) for r in c]);trial['objective']=float(np.mean(residual**2))
                trials.append(trial);write(out/'calibration_trials.json',trials)
                if not trial['accepted']:raise ValueError('Calibration trial rejected; no fabricated penalty observation')
                return residual
            for S in (.9,1.,1.1):
                for rho in (.8,1.,1.2):
                    try:objective((S,rho))
                    except ValueError:pass # Rejected grid vertices retained, not numerical observations.
            good=[r for r in trials if r['accepted']]
            if not good:fit=dict(status='STOP',reason='No admitted calibration vertex')
            else:
                best=min(good,key=lambda r:r['objective']);seed=(best['S'],best['rho'])
                try:
                    opt=least_squares(lambda x:objective(x,True),seed,bounds=([.9,.8],[1.1,1.2]),
                        max_nfev=8,diff_step=.001,ftol=1e-7,xtol=1e-7,gtol=1e-7)
                    fit=dict(status='EXECUTED',optimizer_success=bool(opt.success),optimizer_status=int(opt.status),
                        optimizer_message=str(opt.message),nfev=int(opt.nfev),jacobian=opt.jac.tolist(),
                        optimizer_parameters=opt.x.tolist(),fresh_blind_validation=False)
                except (ValueError,RuntimeError) as e:fit=dict(status='STOP refinement',reason=str(e),fresh_blind_validation=False)
                best=min((r for r in trials if r['accepted']),key=lambda r:r['objective']);chosen=(best['S'],best['rho'])
                fit.update(selected_ACTUALLY_evaluated_parameters=list(chosen),selected_objective=best['objective'],
                    meaning='Calibration-selected effective intrinsic transport factors, not measured commercial grade; no global optimum claim')
        final=rows_for(*chosen,use='selected_evaluation');comparison=compare(points,final)
        evaluation=[r for r in comparison if r['partition'].startswith('EVALUATION')]
        attach=[r for r in results.values() if 'auxiliary_attach_control' in r['uses']]+[nofit[(.2,.1)]]
        attach_PASS=all(r['status']=='ACCEPTED' for r in attach) and np.ptp([r['summary']['cold_K'] for r in attach])<1e-6 and np.ptp([r['summary']['V'] for r in attach])<1e-7
        if not attach_PASS:raise AssertionError('Candidate auxiliary attach invariance failed; STOP')
        good=[r for r in results.values() if r['status']=='ACCEPTED']
        analysis=dict(no_fit_metrics=no_metrics,calibration=fit,selected_scales_S_rho_k=[*chosen,1.],
            all20_metrics=metrics(comparison),evaluation16_metrics=metrics(evaluation),rows=comparison,attach_invariance_PASS=bool(attach_PASS),
            source_coverage=dict(measured=sum(r['material']!='g1_constant' and not r['summary']['assumed_continuation'] for r in good),assumed=sum(r['summary']['assumed_continuation'] for r in good),constant_controls=3),
            counts={s:sum(r['status']==s for r in results.values()) for s in ('ACCEPTED','REJECTED','NOT RUN')},
            actual_calls=len(results),unused_maximum_slots_NOT_RUN=240-len(results),elapsed_seconds=time.monotonic()-start,
            max_stage_error_W=max(abs(x) for r in good if r['material']!='g1_constant' for x in r['audit']['stage_errors_W']),
            max_global_error_W=max(abs(r['audit']['global_error_W']) for r in good if r['material']!='g1_constant'),
            Qmax='NOT RUN',DeltaTmax='NOT RUN',higher_hot_dry_N2='NOT COMPARABLE; NOT RUN',
            physical_qualification=False,original_reference_unchanged=True,
            geometry_feasibility='PASS geometric gates; mechanical and complete thermal behavior NOT QUALIFIED')
        write(out/'analysis.json',analysis);write(out/'selected_cases.json',{f'{I:g}_{Q:g}':r['id'] for (I,Q),r in final.items()})
    except Exception as error:
        write(out/'STOP.json',dict(observed_UTC=datetime.now(timezone.utc).isoformat(),reason=str(error),calls=len(results),seconds=time.monotonic()-start));raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0.);signal.signal(signal.SIGALRM,previous)
        write(out/'cases.json',results)
    for p,h in reg['input_sha256'].items():
        if sha(ROOT/p)!=h:raise AssertionError('Frozen original changed after study')
    print({k:analysis[k] for k in ('counts','actual_calls','elapsed_seconds','no_fit_metrics','all20_metrics','selected_scales_S_rho_k')})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=DATA);run(p.parse_args().folder)
