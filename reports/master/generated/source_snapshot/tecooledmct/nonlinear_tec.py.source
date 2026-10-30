"""Direct conservative nonlinear 1D transport; no interpolated surrogate.

Same midpoint control volumes as oem_phase_a.bounded_leg, independent banded
Newton implementation. Temperatures are bounded at every material evaluation.
The 300..390 K law is the explicit graded_tec engineering continuation.
"""
from __future__ import annotations

import time
import numpy as np
from scipy.linalg import solve_banded

from . import graded_tec as analog


class LegFailure(ValueError):
    def __init__(self,message,diagnostics):
        super().__init__(message)
        self.diagnostics=diagnostics


def properties(polarity,t,scales):
    p=analog.props(polarity,t)
    slope_factor=np.where(t>300.,analog.HIGH_T_SLOPE_FACTOR,1.)
    curves=analog.source().curves[polarity]
    result={key:np.asarray(p[key])*scale for key,scale in zip(('S','rho','k'),scales)}
    for key,scale in zip(('S','rho','k'),scales):
        result[key+'_prime']=curves[key].slope(np.minimum(t,300.))*slope_factor*scale
    return result


def leg(polarity,hot,cold,j,length,*,intervals=32,scales=(1.,1.,1.),max_iterations=40):
    """Solve q=S*T*J-k*T', q'=J*(rho*J+S*T') on hot -> cold z.

    The Jacobian is analytic/tridiagonal on each active source segment.
    No clipping of a solved state, rounded cache keys, or affine fallback.
    """
    if (polarity not in ('P','N') or not isinstance(intervals,int) or intervals<8
            or not isinstance(max_iterations,int) or max_iterations<1
            or not np.isfinite((hot,cold,j,length,*scales)).all()
            or length<=0 or min(scales)<=0):
        raise ValueError('Invalid nonlinear leg inputs')
    lo,hi=analog.LOW_K,analog.HIGH_K
    if min(hot,cold)<lo or max(hot,cold)>hi:
        raise ValueError('Nonlinear leg boundary outside active material domain')
    dx=length/intervals
    t=np.linspace(hot,cold,intervals+1)
    last_norm=None

    def fields(temperature):
        mid=(temperature[:-1]+temperature[1:])/2
        p=properties(polarity,mid,scales)
        dt=np.diff(temperature);grad=dt/dx
        q=p['S']*mid*j-p['k']*grad
        v=j*p['rho']*dx+p['S']*dt
        w=j*v
        r=np.diff(q)-.5*(w[1:]+w[:-1])
        # Segment derivatives with respect to left/right nodal temperatures.
        common=.5*j*(p['S']+mid*p['S_prime'])-.5*p['k_prime']*grad
        ql=common+p['k']/dx;qr=common-p['k']/dx
        common_w=j*(.5*j*p['rho_prime']*dx+.5*p['S_prime']*dt)
        wl=common_w-j*p['S'];wr=common_w+j*p['S']
        diagonal=ql[1:]-qr[:-1]-.5*(wl[1:]+wr[:-1])
        lower=-ql[:-1]-.5*wl[:-1]
        upper=qr[1:]-.5*wr[1:]
        ab=np.zeros((3,intervals-1));ab[1]=diagonal
        ab[0,1:]=upper[:-1];ab[2,:-1]=lower[1:]
        return r,ab,q,w,v,p,grad

    for iteration in range(max_iterations):
        r,ab,q,w,v,p,grad=fields(t)
        last_norm=float(np.max(np.abs(r)))
        flux_energy=q[-1]+.5*w[-1]-q[0]+.5*w[0]-j*float(v.sum())
        if last_norm<=1e-4 and abs(flux_energy)<=1e-6:
            break
        change=solve_banded((1,1),ab,-r,check_finite=True)
        alpha=1.
        for bound,mask in ((hi,change>0),(lo,change<0)):
            if np.any(mask):
                alpha=min(alpha,.99*float(np.min((bound-t[1:-1][mask])/change[mask])))
        if alpha<=1e-12:
            break
        for _ in range(24):
            trial=t.copy();trial[1:-1]+=alpha*change
            rr=fields(trial)[0]
            if np.linalg.norm(rr)<=np.linalg.norm(r)*(1-1e-4*alpha):
                t=trial
                break
            alpha*=.5
        else:
            break
    # Independently audit physical residual and both endpoint fluxes.
    r,_,q,w,v,p,grad=fields(t)
    qhot=float(q[0]-.5*w[0]);qcold=float(q[-1]+.5*w[-1])
    voltage=float(v.sum());energy=qcold-qhot-j*voltage
    diagnostic={'polarity':polarity,'intervals':intervals,'iterations':iteration+1,
        'temperatures_k':t.tolist(),'max_balance_residual_w_m2':float(np.max(np.abs(r))),
        'energy_error_w_m2':float(energy),'domain_k':[lo,hi],
        'active_bound':bool(np.min(t)<=lo+1e-4 or np.max(t)>=hi-1e-4)}
    if (not np.isfinite(t).all() or np.min(t)<lo or np.max(t)>hi
            or diagnostic['max_balance_residual_w_m2']>1e-4 or abs(energy)>1e-6):
        raise LegFailure('Nonlinear leg failed residual/domain gate',diagnostic)
    return {**diagnostic,'q_hot_w_m2':qhot,'q_cold_w_m2':qcold,
        'electric_integral_v':voltage,'joule_w_m2':float(j*j*np.sum(p['rho'])*dx),
        'mean_fourier_w_m2':float(np.mean(-p['k']*grad)),
        'assumed_high_T_continuation_used':bool(np.max(t)>300.)}


class Transport:
    """Per-package-solve cache keyed by exact inputs; no persistent stale table."""
    def __init__(self,intervals=32):
        if not isinstance(intervals,int) or intervals<8:raise ValueError('At least eight intervals')
        self.intervals=intervals;self.cache={};self.hits=0;self.calls=0;self.seconds=0.

    def stage(self,geom,th,tc,current,*,alpha_scale=1.,rho_scale=1.,k_scale=1.,bypass_w_k=0.):
        n=geom['couples'];area=geom['leg_area_m2'];length=geom['leg_length_m']
        if (not isinstance(n,int) or n<1 or not np.isfinite((area,length,th,tc,current,
                alpha_scale,rho_scale,k_scale,bypass_w_k)).all() or area<=0 or length<=0
                or min(alpha_scale,rho_scale,k_scale)<=0 or bypass_w_k<0):
            raise ValueError('Invalid nonlinear stage geometry/coefficients')
        key=(n,area,length,th,tc,current,alpha_scale,rho_scale,k_scale,bypass_w_k)
        if key in self.cache:
            self.hits+=1
            return self.cache[key].copy()
        start=time.perf_counter();self.calls+=1
        scales=(alpha_scale,rho_scale,k_scale)
        pn={pol:leg(pol,th,tc,current/area*(1 if pol=='N' else -1),length,
                    intervals=self.intervals,scales=scales) for pol in ('P','N')}
        bypass=bypass_w_k*(th-tc)
        qc=-n*area*sum(v['q_cold_w_m2'] for v in pn.values())-bypass
        qh=-n*area*sum(v['q_hot_w_m2'] for v in pn.values())-bypass
        voltage=n*(pn['N']['electric_integral_v']-pn['P']['electric_integral_v'])
        energy=qh-qc-current*voltage
        if abs(energy)>1e-9:raise LegFailure('Nonlinear stage energy gate failed',{'energy_residual_w':energy})
        result={'qc_w':qc,'qh_w':qh,'voltage_v':voltage,'energy_residual_w':energy,
            'joule_w':n*area*sum(v['joule_w_m2'] for v in pn.values()),
            'conduction_w':n*area*sum(v['mean_fourier_w_m2'] for v in pn.values())+bypass,
            'leg_temperature_extrema_k':[min(min(v['temperatures_k']) for v in pn.values()),
                                         max(max(v['temperatures_k']) for v in pn.values())],
            'max_leg_balance_residual_w_m2':max(v['max_balance_residual_w_m2'] for v in pn.values()),
            'max_leg_iterations':max(v['iterations'] for v in pn.values()),
            'high_T_assumption_applied':any(v['assumed_high_T_continuation_used'] for v in pn.values()),
            'transport_domain_K':[analog.LOW_K,analog.HIGH_K],
            'transport':'direct nonlinear conservative 1D P/N midpoint BVP',
            'intervals':self.intervals,'affine_T_axial_approximation':False}
        self.seconds+=time.perf_counter()-start
        if len(self.cache)>=8192:self.cache.clear()
        self.cache[key]=result
        return result.copy()

    def statistics(self):
        return {'stage_solves':self.calls,'exact_cache_hits':self.hits,'stage_solve_seconds':self.seconds,
                'intervals':self.intervals,'cache':'exact floating inputs, per solve, no rounding/interpolation'}
