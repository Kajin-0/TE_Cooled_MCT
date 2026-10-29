"""Independent three-stage SCREENING network, never FEM or device validation.

Constant laws use exact linear cascade algebra. Source-dependent legs solve
one-dimensional local-T constitutive BVPs (including implicit Thomson terms).
Contacts/routing in this network are approximations, not meshed interfaces.
"""
from functools import lru_cache
from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_bvp,simpson
from scipy.optimize import root
from .g2d_data import ROOT,DATA,sha
from .fem_g2a import PROPERTIES

@lru_cache(None)
def geometry():
    m=json.loads((ROOT/'fem/results/g2b_two_terminal_20261028/meshes/mesh_2/manifest.json').read_text())
    heights=[s['leg_height_m'] for s in m['stage_nets']]
    leg=next(b for b in m['bodies'] if b['kind']=='leg');area=leg['box_m'][3]*leg['box_m'][4]
    copper=[]
    for stage in range(3):
        r=0.
        for b in m['bodies']:
            if b.get('stage')==stage and b['kind']=='bridge':
                axis=b['cut_axis'];length=b['box_m'][axis+3]-leg['box_m'][3]
                r+=length/(PROPERTIES['Cu'][1]*leg['box_m'][3]*b['box_m'][5])
        copper.append(r)
    shunts=[]
    for idx in range(2):
        link=next(b for b in m['bodies'] if b['name']==f'buried_interstage_link_{idx}')
        resistance=0.
        for box in link['boxes_m']:
            dims=np.array(box[3:]);axis=int(dims.argmax());resistance+=dims[axis]/(400*np.prod(np.delete(dims,axis)))
        rib=next(b for b in m['bodies'] if b['name']==f'routing_rib_{idx}');box=max(rib['boxes_m'],key=lambda b:b[5]);cross=box[3]*box[4]-3.6e-9
        shunts.append(1/resistance+30*cross/box[5])
    return {'heights_m':heights,'area_m2':area,'local_cu_r_ohm':copper,'route_k_w_k':[*shunts,0.],
        'manifest_sha256':sha(ROOT/'fem/results/g2b_two_terminal_20261028/meshes/mesh_2/manifest.json'),
        'assumption':'isothermal stages; 1D local Cu R and Manhattan series Cu / parallel rib shunts; no ceramic spreading/plate drops or external leads'}


def baseline():return {r['id']:r['baseline'] for r in json.loads((DATA/'parameters.json').read_text())['parameters']}

def validate(parameters,counts):
    registry=json.loads((DATA/'parameters.json').read_text())
    if len(counts)!=3 or sum(counts)!=44 or any(not isinstance(n,int) or n<=0 for n in counts):raise ValueError('Topology must contain three positive integer counts summing to 44')
    for r in registry['parameters']:
        value=parameters[r['id']]
        if not np.isfinite(value) or not r['bounds'][0]<=value<=r['bounds'][1]:raise ValueError('Parameter outside preregistered bounds: '+r['id'])


def coefficients(parameters,counts):
    g=geometry();a=g['area_m2']/parameters['leg_aspect'];k=parameters['k_scale'];r=parameters['rho_scale'];s=parameters['seebeck_scale'];out=[]
    for idx,n in enumerate(counts):
        h=g['heights_m'][idx];alpha=n*s*(PROPERTIES['P'][2]-PROPERTIES['N'][2])
        resistance=n*h/a*r*(1/PROPERTIES['P'][1]+1/PROPERTIES['N'][1])+4*n*parameters['re_area']/a+g['local_cu_r_ohm'][idx]
        conductance=sum(n/(h/(PROPERTIES[p][0]*k*a)+2*parameters['rth_area']/a) for p in ('P','N'))+parameters['route_scale']*g['route_k_w_k'][idx]
        out.append((alpha,resistance,conductance))
    return out


def constant(current,load,hot=300.,parameters=None,counts=(28,12,4)):
    p=baseline() if parameters is None else dict(parameters);validate(p,counts)
    c=coefficients(p,counts)
    def stages(t):
        return [{'qc_w':s*current*t[i+1]-.5*current**2*r-k*(t[i]-t[i+1]),
                 'qh_w':s*current*t[i]+.5*current**2*r-k*(t[i]-t[i+1]),
                 'voltage_v':current*r+s*(t[i]-t[i+1])} for i,(s,r,k) in enumerate(c)]
    def residual(t):
        q=stages(t)
        return np.array([t[0]-hot-p['bath_r']*q[0]['qh_w'],q[0]['qc_w']-q[1]['qh_w'],q[1]['qc_w']-q[2]['qh_w'],q[2]['qc_w']-load-p['q_extra_w']])
    b=residual(np.zeros(4));matrix=np.column_stack([residual(np.eye(4)[i])-b for i in range(4)])
    t=np.linalg.solve(matrix,-b)
    if not np.isfinite(t).all() or t.min()<=0 or t.max()>1500:raise ValueError('Nonphysical / out-of-diagnostic-range network root')
    budgets=stages(t);voltage=sum(q['voltage_v'] for q in budgets)
    errors=[q['qh_w']-q['qc_w']-current*q['voltage_v'] for q in budgets]
    return {'method':'reduced constant-law screening network, NOT FEM','current_a':current,'load_w':load,'hot_k':hot,'ambient':'vacuum',
        'plate_temperatures_k':t.tolist(),'delta_t_k':hot-t[-1],'voltage_v':voltage,'power_w':current*voltage,'stages':budgets,
        'max_stage_energy_error_w':max(abs(e) for e in errors),'global_energy_error_w':budgets[0]['qh_w']-load-p['q_extra_w']-current*voltage,
        'max_cascade_residual_w':float(np.abs(residual(t)[1:]).max()),'coefficient_validity':'mathematical constant law only; not a measured wide-temperature grade'}


def local_leg(profile,polarity,hot,cold,current_density,length):
    """Independent local constitutive 1D BVP; q'=J.E, no stage-average laws."""
    profile.properties(polarity,np.array([hot,cold]));z=np.linspace(0,length,25);guess=hot+(cold-hot)*z/length
    props=profile.properties(polarity,guess);q=-props['k']*(cold-hot)/length+props['S']*guess*current_density
    def ode(x,y):
        pp=profile.properties(polarity,y[0]);grad=(pp['S']*y[0]*current_density-y[1])/pp['k']
        return np.vstack([grad,current_density*(current_density*pp['rho']+pp['S']*grad)])
    sol=solve_bvp(ode,lambda a,b:np.array([a[0]-hot,b[0]-cold]),z,np.vstack([guess,q]),tol=1e-5,max_nodes=1000)
    if not sol.success:raise ValueError('Local-T network leg BVP did not converge')
    x=np.linspace(0,length,201);y=sol.sol(x);pp=profile.properties(polarity,y[0]);grad=ode(x,y)[0]
    electric_integral=float(simpson(current_density*pp['rho']+pp['S']*grad,x=x))
    return {'q_hot_w_m2':float(sol.y[1,0]),'q_cold_w_m2':float(sol.y[1,-1]),'electric_integral_v':electric_integral,
        'energy_error_w_m2':float(sol.y[1,-1]-sol.y[1,0]-current_density*electric_integral),'min_k':float(y[0].min()),'max_k':float(y[0].max())}


def temperature_dependent(profile,current,load,hot=295.,counts=(28,12,4)):
    g=geometry();a=g['area_m2'];cache={}
    def evaluate(t):
        key=tuple(t)
        if key in cache:return cache[key]
        all_t=[hot,*t];budgets=[]
        for i,n in enumerate(counts):
            th,tc=all_t[i:i+2];legs={p:local_leg(profile,p,th,tc,current/a*(1 if p=='N' else -1),g['heights_m'][i]) for p in ('P','N')}
            qc=-n*a*sum(r['q_cold_w_m2'] for r in legs.values());qh=-n*a*sum(r['q_hot_w_m2'] for r in legs.values())
            voltage=n*(legs['N']['electric_integral_v']-legs['P']['electric_integral_v'])+current*g['local_cu_r_ohm'][i]
            # Symmetric local copper Joule split and passive route bypass.
            qc-=.5*current**2*g['local_cu_r_ohm'][i]+g['route_k_w_k'][i]*(th-tc)
            qh+=.5*current**2*g['local_cu_r_ohm'][i]-g['route_k_w_k'][i]*(th-tc)
            budgets.append({'qc_w':qc,'qh_w':qh,'voltage_v':voltage,'legs':legs})
        cache[key]=budgets;return budgets
    def fun(t):
        q=evaluate(t);return [q[0]['qc_w']-q[1]['qh_w'],q[1]['qc_w']-q[2]['qh_w'],q[2]['qc_w']-load]
    start=constant(current,load,hot)['plate_temperatures_k'][1:]
    solution=root(fun,start,tol=1e-7)
    if not solution.success or np.max(np.abs(fun(solution.x)))>1e-6:raise ValueError('TD cascade root failed')
    q=evaluate(solution.x);v=sum(b['voltage_v'] for b in q)
    return {'method':'independent reduced 1D local-T cascade, NOT FEM','profile_id':profile.metadata['id'],'current_a':current,'load_w':load,'hot_k':hot,'ambient':'vacuum',
        'plate_temperatures_k':[hot,*solution.x.tolist()],'delta_t_k':hot-solution.x[-1],'voltage_v':v,'stages':q,
        'max_stage_energy_error_w':max(abs(b['qh_w']-b['qc_w']-current*b['voltage_v']) for b in q),'global_energy_error_w':q[0]['qh_w']-load-current*v,
        'limitations':'isothermal stages, approximate Cu/rib routing, ideal interfaces; no plate spreading, no package/environment'}
