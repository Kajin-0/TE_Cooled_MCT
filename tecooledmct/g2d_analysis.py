"""Calibration-only reduced-network screening, frozen fit, then held-out scoring."""
from pathlib import Path
import json,csv
import numpy as np
from scipy.optimize import least_squares
from .g2d_data import ROOT,DATA,sha,dump,points,residual,preserve
from .g2d_network import baseline,constant,geometry,temperature_dependent
from .material_profiles import DATA as MATERIAL_DATA,load_profile


def predict(rows,p,counts):
    cache={}
    result=[]
    for row in rows:
        key=(row['current_a'],row['load_w'])
        if key not in cache:cache[key]=constant(*key,parameters=p,counts=counts)
        result.append(cache[key][row['field']])
    return np.asarray(result)


def jacobian(rows,p,counts=(28,12,4),step=1e-3):
    registry=json.loads((DATA/'parameters.json').read_text())['parameters'];y=predict(rows,p,counts)
    scales=np.array([max(abs(v),1. if row['field']=='delta_t_k' else .01) for row,v in zip(rows,y)])
    columns=[];methods=[]
    for r in registry:
        delta=step*r['scale'];lo,hi=r['bounds'];a=dict(p);b=dict(p)
        a[r['id']]=max(lo,p[r['id']]-delta);b[r['id']]=min(hi,p[r['id']]+delta)
        columns.append((predict(rows,b,counts)-predict(rows,a,counts))/(b[r['id']]-a[r['id']])*r['scale']/scales)
        methods.append('central' if a[r['id']]<p[r['id']]<b[r['id']] else 'one-sided at physical bound')
    j=np.column_stack(columns);u,s,v=np.linalg.svd(j,full_matrices=False);rank=int(np.sum(s>s[0]*1e-7))
    return {'parameter_names':[r['id'] for r in registry],'matrix':j.tolist(),'observable_ids':[r['id'] for r in rows],
        'normalization':'d(y/max(abs(y0), 1 K or .01 V))/d(p/reference_scale); not a statistical Fisher confidence model',
        'step':step,'difference_methods':methods,'singular_values':s.tolist(),'relative_rank_threshold':1e-7,'rank':rank,
        'columns':len(registry),'condition_number':None if rank<len(registry) else float(s[0]/s[-1]),
        'null_right_vectors':v[rank:].tolist(),'rank_deficient':rank<len(registry)}


def main():
    out=ROOT/'outputs/g2d-analysis';out.mkdir(parents=True,exist_ok=True);protected=preserve()
    files=[Path(__file__).resolve(),ROOT/'tecooledmct/g2d_network.py',ROOT/'tecooledmct/g2d_data.py',*DATA.glob('*.json')]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
    cal=points('calibration_reserved');base=baseline();y0=predict(cal,base,(28,12,4));matrix=jacobian(cal,base)
    # Three effective diagnostic coefficient scales; geometry/contact/environment
    # are not freely co-fitted. Bounds are inside the preregistered hypothesis box.
    names=['rho_scale','seebeck_scale','k_scale'];lower=[.7,.85,.75];upper=[1.6,1.25,1.25]
    obs=np.array([r['value'] for r in cal]);bounds=np.array([r['value_reading_bound'] for r in cal])
    fits=[]
    topologies=[(28,12,4),(26,12,6),(24,12,8),(30,10,4)]
    for counts in topologies:
        def fun(x):
            p={**base,**dict(zip(names,x))};return (predict(cal,p,counts)-obs)/bounds
        fit=least_squares(fun,[1,1,1],bounds=(lower,upper),max_nfev=200,ftol=1e-10,gtol=1e-10,xtol=1e-10)
        p={**base,**dict(zip(names,fit.x))};fits.append({'counts':list(counts),'parameters':p,'score':float(np.dot(fun(fit.x),fun(fit.x))),
            'optimizer_success':bool(fit.success),'evaluations':fit.nfev,'at_fit_boundary':bool(np.any(np.isclose(fit.x,lower,atol=1e-4)) or np.any(np.isclose(fit.x,upper,atol=1e-4))),
            'calibration_predictions':predict(cal,p,counts).tolist()})
    best=min(fits,key=lambda r:r['score']);p=best['parameters'];equivalent={**p,'leg_aspect':p['leg_aspect']*1.02,'rho_scale':p['rho_scale']/1.02,'k_scale':p['k_scale']*1.02}
    equivalent_error=float(np.max(np.abs(predict(cal,equivalent,tuple(best['counts']))-predict(cal,p,tuple(best['counts'])))))
    frozen={'method':'reduced network diagnostic ONLY, not FEM/OEM qualification','selection':'minimum preregistered CALIBRATION-only score across four inferred integer allocations',
        'calibration_source_sha256':sha(DATA/'calibration_reserved.json'),'registration_sha256':sha(DATA/'preregistration.json'),
        'fits':fits,'selected':best,'distinct_equivalent_parameters':equivalent,'maximum_calibration_prediction_difference':equivalent_error,
        'no_holdout_used_in_fit':True,'source_sha256':hashes,'fit_parameters':names,'fit_bounds':[lower,upper],
        'objective_weights':'calibration vertical reading bounds ONLY; no neighbour/holdout-derived slopes in fitting',
        'preliminary_attempt':'discarded before acceptance: used full-curve horizontal-error slopes in weights; kept under preliminary_unaccepted, no model/bounds/direction changes based on holdout residuals'}
    dump(out/'frozen_fit.json',frozen);freeze_sha=sha(out/'frozen_fit.json')
    # This is the first access to held-out numeric values in the fit runner.
    hold=points('validation_holdout');residuals=[]
    for split,rows in [('calibration_reserved',cal),('validation_holdout',hold)]:
        for model,pp,counts in [('baseline',base,(28,12,4)),('frozen_diagnostic_fit',p,tuple(best['counts']))]:
            for row,value in zip(rows,predict(rows,pp,counts)):
                pred={'hot_k':300,'ambient':'vacuum','current_a':row['current_a'],'load_w':row['load_w'],row['field']:float(value)}
                residuals.append({'model':model,'method':'reduced network, NOT FEM',**residual(row,pred)})
    equivalent_hold=float(np.max(np.abs(predict(hold,equivalent,tuple(best['counts']))-predict(hold,p,tuple(best['counts'])))))
    oat=[]
    for reg in json.loads((DATA/'parameters.json').read_text())['parameters']:
        for value in reg['bounds']:
            pp={**base,reg['id']:value}
            r=constant(.2,0,parameters=pp);oat.append({'parameter':reg['id'],'value':value,'delta_t_k':r['delta_t_k'],'voltage_v':r['voltage_v'],'point':'300 K vacuum .2 A zero load; network screening'})
    td=[];profile=load_profile(MATERIAL_DATA/'zhang2025_he_40_300_v2.json')
    for current in (.05,.1):
        try:td.append(temperature_dependent(profile,current,0.,295.))
        except (ValueError,RuntimeError) as exc:td.append({'current_a':current,'hot_k':295,'status':'FAILED CLOSED','reason':str(exc)})
    checks={'frozen_fit_exists_before_holdout_scoring':freeze_sha==sha(out/'frozen_fit.json'),
        'exact_distinct_parameter_degeneracy':equivalent_error<1e-8 and equivalent_hold<1e-8,
        'jacobian_rank_deficient':matrix['rank_deficient'],
        'constant_network_energy_conservation':all(abs(constant(i,q)['global_energy_error_w'])<1e-9 for i,q in ((.1,0),(.2,.1),(.6,.2),(1.,.41))),
        'calibration_only_optimizer_success':all(f['optimizer_success'] for f in fits),
        'sources_unchanged':all(sha(ROOT/n)==h for n,h in hashes.items())}
    result={'passed':all(checks.values()),'checks':checks,'source_sha256':hashes,'protected_integrity':protected,'frozen_fit_sha256':freeze_sha,'fit':frozen,
        'jacobian':matrix,'residuals':residuals,'one_at_a_time':oat,'local_T_network':td,'equivalent_holdout_prediction_difference':equivalent_hold,
        'geometry_screening_assumptions':geometry(),'qualification_verdict':'FAILED / NOT ESTABLISHED: reduced diagnostic fits do not identify OEM grade/geometry; no source-backed matched 300 K family established'}
    dump(out/'summary.json',result)
    for filename,rows in [('residuals.csv',residuals),('one_at_a_time.csv',oat)]:
        with (out/filename).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({'checks':checks,'rank':matrix['rank'],'columns':matrix['columns'],'best_score':best['score'],'best_counts':best['counts'],'equivalent_error':equivalent_error},indent=2),flush=True)
    if not result['passed']:raise SystemExit('Screening verification failed')

if __name__=='__main__':main()
