"""Parameter sweeps, uncertainty propagation, and first-order cooldown dynamics."""
from dataclasses import asdict, replace
import numpy as np
from scipy.integrate import solve_ivp
from .model import Scenario, solve, heat_breakdown, stage_transport, _fractions


def compare_gases(s:Scenario):
    """Single-species and 50/50 mixture comparison at identical stated conditions."""
    inputs = {'N2':(1.,0.,0.), 'Ar':(0.,1.,0.), 'Kr':(0.,0.,1.),
              'N2/Ar 50:50':(.5,.5,0.), 'Ar/Kr 50:50':(0.,.5,.5),
              'N2/Kr 50:50':(.5,0.,.5)}
    rows=[]
    for label,fracs in inputs.items():
        sp=replace(s,gas='mixture',gas_mole_fractions=fracs)
        p=solve(sp); rows.append({'gas':label,'fractions':fracs,'detector_k':p['detector_k'],
                'gas_heat_top_mw':p['loads_w']['gas_w'][2]*1000,
                'radiation_top_mw':p['loads_w']['radiation_w'][2]*1000,
                'rayleigh_top':p['loads_w']['rayleigh'][2]})
    return sorted(rows,key=lambda x:x['detector_k'])


def sweep(s:Scenario, field:str, values):
    rows=[]
    for value in values:
        sp=replace(s,**{field:float(value)})
        try:
            p=solve(sp)
            rows.append({'input':float(value),'detector_k':p['detector_k'],
                  'bottom_k':p['stage_k'][0],'middle_k':p['stage_k'][1],
                  'hot_k':p['hot_k'],'power_w':p['electrical_power_w'],
                  'load_mw':p['loads_w']['total_w'][2]*1000,'status':'converged'})
        except RuntimeError:
            rows.append({'input':float(value),'status':'infeasible'})
    return rows


def monte_carlo(s:Scenario, n:int=100, seed:int=20261028):
    """Exploratory uncertain geometry/material parameters; not a validated CI.

    Uniform inputs: gas effective area multiplier +/-35%, wire diameter +/-20%,
    emissivity +/-0.15 absolute, thermal path resistance +/-30%, detector R +/-25%.
    These ranges are ANALYST PRIORS; NOT empirical tolerance data.
    """
    rng=np.random.default_rng(seed)
    samples=[]
    for _ in range(n):
        sp=replace(s,
            gas_geometry_factor=s.gas_geometry_factor*rng.uniform(.65,1.35),
            wire_diameter_um=s.wire_diameter_um*rng.uniform(.8,1.2),
            surface_emissivity=np.clip(s.surface_emissivity+rng.uniform(-.15,.15),.05,.95),
            hot_to_ambient_k_per_w=s.hot_to_ambient_k_per_w*rng.uniform(.7,1.3),
            detector_resistance_ohm=s.detector_resistance_ohm*rng.uniform(.75,1.25))
        try: samples.append(solve(sp)['detector_k'])
        except RuntimeError: pass
    if not samples: raise RuntimeError('no converged samples')
    return {'n_attempted':n,'n_converged':len(samples),'mean_k':float(np.mean(samples)),
         'p05_k':float(np.quantile(samples,.05)),'p50_k':float(np.median(samples)),
         'p95_k':float(np.quantile(samples,.95)),
         'interpretation':'Prior-driven sensitivity interval, NOT a statistical confidence interval'}


def simulate_transient(s:Scenario,duration_s:float=120.,points:int=241):
    """Simple 4-node thermal capacitance demonstration. C are unmeasured priors.

    Initial condition all parts at ambient. Stage capacitances in J/K are
    estimates including ceramic / legs / mounts, NOT inferred from OEM transient.
    """
    s.validate()
    capacities=np.array([0.012,0.0045,0.0018,1.5],float) # J/K
    def rhs(t,x):
        t1,t2,t3,th=x
        loads=heat_breakdown(s,[t1,t2,t3],th)['total_w']
        st=[stage_transport(0,s.current_a,t1,th),stage_transport(1,s.current_a,t2,t1),stage_transport(2,s.current_a,t3,t2)]
        qdot=np.array([st[1]['qh_w']+loads[0]-st[0]['qc_w'],
              st[2]['qh_w']+loads[1]-st[1]['qc_w'],
              loads[2]-st[2]['qc_w'],
              st[0]['qh_w']-(th-s.ambient_k)/max(s.hot_to_ambient_k_per_w,1e-8)])
        if s.hot_to_ambient_k_per_w==0:qdot[3]=0
        return qdot/capacities
    t=np.linspace(0,duration_s,points)
    x0=np.full(4,s.ambient_k)
    sol=solve_ivp(rhs,(0.,duration_s),x0,t_eval=t,method='BDF',rtol=2e-7,atol=1e-8)
    if not sol.success:raise RuntimeError(sol.message)
    return {'time_s':t.tolist(),'bottom_k':sol.y[0].tolist(),'middle_k':sol.y[1].tolist(),
            'detector_k':sol.y[2].tolist(),'hot_k':sol.y[3].tolist(),
            'capacitances_j_per_k':capacities.tolist(),
            'warning':'Cooldown is illustrative: heat capacities and dynamics unvalidated'}
