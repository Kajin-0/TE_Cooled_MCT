"""Prospective bounded 1D thermoelectric screening; not OEM-grade validation.

Finite-volume midpoint constitutive laws, with nodal heat balance and bounded
nonlinear temperatures. Unlike an unconstrained BVP iterate, every material
evaluation lies in the *measured* property interval. Historical G2d code and
Elmer archives are unchanged. This model has ideal contacts and isothermal
stage interfaces, and does not replace 3D package FEM.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import diags

from .g2d_network import constant, geometry
from .material_profiles import load_profile, DATA as MATERIAL_DATA
from .g2d_data import ROOT


def bounded_leg(profile, polarity, hot, cold, current_density, length, *, intervals=32):
    """Solve q = S*T*J-k*dT/dz, dq/dz = J*(rho*J+S*dT/dz).

    Segment midpoint work is shared equally between the two adjacent flux
    control volumes, yielding a conservative second-order 1D discretization.
    Temperatures are bounded at *all* optimizer evaluations; no extrapolation
    or property clamping is used.
    """
    lo, hi = profile.interval
    if not isinstance(intervals, int) or intervals < 8:
        raise ValueError("At least eight integer intervals are required")
    if not all(np.isfinite(v) for v in (hot, cold, current_density, length)):
        raise ValueError("Nonfinite leg inputs")
    if length <= 0 or min(hot, cold) < lo or max(hot, cold) > hi:
        raise ValueError("Leg geometry or boundary temperature outside source domain")
    dx = length / intervals
    initial = np.linspace(hot, cold, intervals + 1)
    n = intervals - 1
    low = np.full(n, lo + 1e-9)
    high = np.full(n, hi - 1e-9)
    x0 = np.maximum(low + 1e-6, np.minimum(high - 1e-6, initial[1:-1]))
    jac = diags([np.ones(n-1), np.ones(n), np.ones(n-1)], [-1, 0, 1], shape=(n,n), format='csr')

    def fields(x):
        t = np.r_[hot, x, cold]
        mid = (t[:-1] + t[1:]) / 2
        p = profile.properties(polarity, mid)
        grad = np.diff(t) / dx
        flux = p['S'] * mid * current_density - p['k'] * grad
        segment_voltage = current_density * p['rho'] * dx + p['S'] * np.diff(t)
        work = current_density * segment_voltage
        return t, flux, work, segment_voltage

    # Residual has native flux units; normalize for optimizer but audit the
    # unscaled physical residual independently at the accepted solution.
    def residual(x):
        _, q, w, _ = fields(x)
        return (np.diff(q) - .5 * (w[1:] + w[:-1])) / 1e4

    solution = least_squares(residual, x0, bounds=(low,high),
                             jac_sparsity=jac, method='trf', max_nfev=400,
                             tr_options={'atol':1e-14,'btol':1e-14,'maxiter':1000},
                             ftol=1e-12, xtol=1e-12, gtol=1e-12)
    t, q, w, v = fields(solution.x)
    max_residual = float(np.max(np.abs(residual(solution.x))) * 1e4)
    voltage = float(np.sum(v))
    q_hot = float(q[0] - .5 * w[0])
    q_cold = float(q[-1] + .5 * w[-1])
    mismatch = q_cold - q_hot - current_density * voltage
    if (not solution.success or max_residual > 2e-3 or
            abs(mismatch) > 2e-3 or not np.isfinite(t).all()):
        raise ValueError(f"Bounded leg did not converge: residual {max_residual:.4g} W/m2")
    if np.min(t) < lo - 1e-12 or np.max(t) > hi + 1e-12:
        raise ValueError("Accepted leg field outside source temperature coverage")
    return {
        'q_hot_w_m2': q_hot, 'q_cold_w_m2': q_cold,
        'electric_integral_v': voltage, 'energy_error_w_m2': float(mismatch),
        'min_k': float(t.min()), 'max_k': float(t.max()),
        'max_balance_residual_w_m2': max_residual, 'intervals': intervals,
        'evaluations': int(solution.nfev),
        'temperatures_k': t.tolist(),
    }


def bounded_cascade(profile, current, load, hot=300., *, counts=(28,12,4), intervals=32):
    """Bounded three-stage reduced model at a stated hot-plate temperature."""
    if len(counts) != 3 or sum(counts) != 44 or any(type(n) is not int or n <= 0 for n in counts):
        raise ValueError("Expected positive integer 44-couple allocation")
    lo, hi = profile.interval
    if not (lo <= hot <= hi) or not all(np.isfinite(v) for v in (current,load,hot)):
        raise ValueError("Hot-side operating point outside source interval")
    g = geometry()
    a = g['area_m2']
    heights = g['heights_m']
    cache = {}

    def evaluate(x):
        key = tuple(x)
        if key in cache:
            return cache[key]
        temp = [hot, *x]
        budgets = []
        for i, n in enumerate(counts):
            th, tc = temp[i:i+2]
            legs = {
                p: bounded_leg(profile, p, th, tc,
                               current/a * (1 if p == 'N' else -1),
                               heights[i], intervals=intervals)
                for p in ('N','P')
            }
            qc = -n*a*sum(legs[p]['q_cold_w_m2'] for p in ('N','P'))
            qh = -n*a*sum(legs[p]['q_hot_w_m2'] for p in ('N','P'))
            rcu = g['local_cu_r_ohm'][i]
            route = g['route_k_w_k'][i] * (th - tc)
            v = n*(legs['N']['electric_integral_v'] - legs['P']['electric_integral_v']) + current*rcu
            budgets.append({'qc_w':qc-.5*current*current*rcu-route,
                            'qh_w':qh+.5*current*current*rcu-route,
                            'voltage_v':v,
                            'max_leg_balance_residual_w_m2':max(p['max_balance_residual_w_m2'] for p in legs.values()),
                            'leg_temperature_extrema_k':[min(p['min_k'] for p in legs.values()),
                                                         max(p['max_k'] for p in legs.values())]})
        cache[key] = budgets
        return budgets

    def residual(x):
        q = evaluate(x)
        return np.array([q[0]['qc_w']-q[1]['qh_w'],
                         q[1]['qc_w']-q[2]['qh_w'],
                         q[2]['qc_w']-load]) / .01

    start = np.asarray(constant(current,load,hot)['plate_temperatures_k'][1:])
    lower = np.full(3, lo + 1e-7)
    upper = np.full(3, hi - 1e-7)
    start = np.clip(start, lower + .1, upper - .1)
    fit = least_squares(residual,start,bounds=(lower,upper),max_nfev=120,
                        ftol=1e-11,xtol=1e-11,gtol=1e-11)
    q = evaluate(fit.x)
    cascade = float(np.max(np.abs(residual(fit.x)))*.01)
    v = float(sum(b['voltage_v'] for b in q))
    conservation = max(abs(b['qh_w']-b['qc_w']-current*b['voltage_v']) for b in q)
    if not fit.success or cascade > 1e-6 or conservation > 1e-6:
        raise ValueError(f"Bounded cascade failed closed: cascade {cascade:.3g} W; energy {conservation:.3g} W")
    return {'method':'bounded source-backed 1D screening, NOT FEM or OEM validation',
            'profile_id':profile.metadata['id'],'grade_matched':False,
            'hot_k':float(hot),'current_a':float(current),'load_w':float(load),
            'ambient':'vacuum','counts':list(counts),'intervals':intervals,
            'plate_temperatures_k':[float(hot),*map(float,fit.x)],
            'delta_t_k':float(hot-fit.x[-1]),'voltage_v':v,
            'max_cascade_residual_w':cascade,'max_stage_energy_error_w':float(conservation),
            'min_leg_temperature_k':min(b['leg_temperature_extrema_k'][0] for b in q),
            'max_leg_temperature_k':max(b['leg_temperature_extrema_k'][1] for b in q),
            'stages':q,'evaluations':int(fit.nfev),
            'limitations':'Different literature specimens, not OEM grade; inferred 28/12/4 geometry and simplified routing, ideal contacts, no package or detector electronics'}


def run(out):
    """One transparent local numerical screening; never overwrite archived G2d."""
    p=load_profile(MATERIAL_DATA/'zhang2025_he_40_300_v2.json')
    results=[]
    for hot, current in ((295.,.1),(300.,.1),(300.,.2)):
        runs=[]
        for n in (16,32):
            try:
                runs.append(bounded_cascade(p,current,0.,hot,intervals=n))
            except ValueError as e:
                runs.append({'intervals':n,'status':'FAILED CLOSED','reason':str(e)})
        results.append({'hot_k':hot,'current_a':current,'mesh_levels':runs,
                        'oem_comparison_permitted':False})
    report={'status':'PHYSICAL VALIDATION NOT ESTABLISHED',
            'source_profile':p.metadata['id'],
            'source_domain_k':list(p.interval),
            'independent_oem_grade_match':False,
            'note':'Matching the hot temperature does not establish OEM-grade material/geometry equivalence. No parameter fitting or holdout comparison is made here.',
            'results':results}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
    for row in results:
        print('case',row['hot_k'],row['current_a'],
              [(r.get('intervals'),r.get('delta_t_k'),r.get('voltage_v'),r.get('status','OK')) for r in row['mesh_levels']])
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default=str(ROOT/'outputs/oem-phase-a'))
    args=parser.parse_args()
    run(args.out)
