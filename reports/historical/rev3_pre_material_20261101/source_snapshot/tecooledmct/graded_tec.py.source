"""Bounded temperature-dependent P/N analog stage using a linear axial T ansatz.

Source: Zhang et al. 2025 P/N specimen curves, 40-300 K. Not a matched
commercial grade. Above 300 K, an openly assumed 25% terminal-tangent
continuation is allowed to 390 K. Not measured data.

A conservative weighted-integral solution reproduces constant S,rho,k
exactly for affine T(x), and enforces Qh-Qc=I V for varying S(T).
It is an explicitly approximate thermoelectric finite-volume reduction,
NOT a solved 1D/3D temperature profile or a validated Thomson distribution.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import hashlib
import numpy as np

from .material_profiles import load_profile, DATA

SOURCE = DATA / 'zhang2025_he_40_300_v2.json'
LOW_K = 180.0
HIGH_K = 390.0
PUBLISHED_HIGH_K = 300.0
HIGH_T_SLOPE_FACTOR = .25
GAUSS_N = 2  # exact for degree<=3 on each piecewise-linear source segment


@lru_cache(maxsize=1)
def source():
    profile = load_profile(SOURCE)
    if profile.interval != (40, 300):
        raise ValueError('Unreviewed source temperature coverage')
    return profile


def source_evidence():
    p=source()
    return {'source_id':p.metadata['id'],
            'source_doi':p.metadata['doi'],
            'file_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'measured_K':[40.,300.],
            'analog_model_K':[LOW_K,HIGH_K],
            'commercial_grade_matched':False,
            'high_T_extension':'ENGINEERING HYPOTHESIS: beyond 300K, use 0.25 x slope of final 280..300K measured segment, through 390K; P/N grades are not matched'}


def props(polarity, temp):
    """Evaluate the active law, including its reciprocal and derivative.

    Interior source knots use the source's right derivative. At 300 K use
    the measured LEFT derivative; strictly above it use the assumed tangent.
    At 390 K use the continuation's LEFT derivative (no law beyond 390 K).
    """
    values=np.asarray(temp,dtype=float)
    if not np.all(np.isfinite(values)) or np.any(values<LOW_K) or np.any(values>HIGH_K):
        raise ValueError('Analog property evaluation outside 180..390 K')
    p=source()
    x=np.minimum(values,300.)
    result=p.properties(polarity,x)
    above=np.maximum(values-300.,0.)
    for key,curve in (('S','S'),('rho','rho'),('k','k')):
        base=np.asarray(result[key],dtype=float)
        slope=float(p.curves[polarity][curve].slope(300.))
        result[key]=base+above*(HIGH_T_SLOPE_FACTOR*slope)
    if (any(not np.all(np.isfinite(result[key])) for key in ('rho','k','S'))
            or np.any(result['rho']<=0) or np.any(result['k']<=0)):
        raise ValueError('Analog continuation violates passivity')
    if np.any(result['S']*(1 if polarity=='P' else -1)<=0):
        raise ValueError('Analog continuation violates P/N thermopower sign')
    slope_s=np.where(values>PUBLISHED_HIGH_K,
                     HIGH_T_SLOPE_FACTOR*p.curves[polarity]['S'].slope(PUBLISHED_HIGH_K),
                     p.curves[polarity]['S'].slope(x))
    result['sigma']=1/result['rho']
    result['thomson_v_k']=values*slope_s
    return result


def stage(geom, th, tc, current, *, alpha_scale=1.,rho_scale=1.,k_scale=1.,
          bypass_w_k=0.,gauss_n=GAUSS_N):
    """Return energy-conservative Qc,Qh,V with variable transport (SI).

    With affine T(s)=Tc+(Th-Tc)s, 0<=s<=1 (cold -> hot):
        q_avg = I integral(alpha(T)*T ds) - dT integral(K(T) ds)
        V     = I integral(R(T) ds) + dT integral(alpha(T) ds)
        Qc    = q_avg - integral[(1-s)*(I^2*R+I*alpha*dT)]ds
        Qh    = Qc + I*V
    Variable-alpha Thomson effects are represented through this weighted
    axial energy identity under the affine-T assumption. The full nonlinear
    temperature field, contact physics and Thomson distribution are NOT solved.
    """
    values=(th,tc,current,alpha_scale,rho_scale,k_scale,bypass_w_k)
    if not np.isfinite(values).all() or min(th,tc)<LOW_K or max(th,tc)>HIGH_K:
        raise ValueError('Stage temperatures outside analog source/assumed domain')
    if min(alpha_scale,rho_scale,k_scale)<=0 or bypass_w_k<0:
        raise ValueError('Invalid analog coefficients')
    n=int(geom['couples']);a=float(geom['leg_area_m2']);length=float(geom['leg_length_m'])
    if n<1 or a<=0 or length<=0:
        raise ValueError('Invalid stage geometry')
    if not isinstance(gauss_n,int) or gauss_n<2:
        raise ValueError('At least two Gauss nodes per source interval required')
    dt=th-tc
    # Split at every source-table breakpoint. On each interval S, rho and k
    # are affine in temperature; the weighted integrands are degree <=2.
    # Thus 2-point Gaussian quadrature is exact to floating-point precision
    # under the expressly assumed affine axial temperature profile.
    segment_knots={0.,1.}
    if dt!=0.:
        psource=source()
        for curves in psource.curves.values():
            for curve in curves.values():
                for knot in curve.temperature_k:
                    u=(knot-tc)/dt
                    if 0.<u<1.:segment_knots.add(float(u))
        upper_knot=(PUBLISHED_HIGH_K-tc)/dt
        if 0.<upper_knot<1.:segment_knots.add(float(upper_knot))
    sorted_knots=np.asarray(sorted(segment_knots))
    left=sorted_knots[:-1];right=sorted_knots[1:]
    roots,w=np.polynomial.legendre.leggauss(gauss_n)
    x=(.5*(left+right)[:,None]+.5*(right-left)[:,None]*roots[None,:]).ravel()
    weights=(.5*(right-left)[:,None]*w[None,:]).ravel()
    t=tc+dt*x
    pp=props('P',t); pn=props('N',t)
    alpha=n*(pp['S']-pn['S'])*alpha_scale
    r=n*length/a*(pp['rho']+pn['rho'])*rho_scale
    k=n*a/length*(pp['k']+pn['k'])*k_scale
    voltage=float(np.dot(weights,current*r+alpha*dt))
    qavg=float(np.dot(weights,alpha*t*current-k*dt))
    work=float(np.dot(weights*(1-x),current**2*r+current*alpha*dt))
    qc=qavg-work-bypass_w_k*dt
    qh=qc+current*voltage
    return {
        'qc_w':qc,'qh_w':qh,'voltage_v':voltage,
        'conduction_w':float(np.dot(weights,k)*dt+bypass_w_k*dt),
        'joule_w':float(np.dot(weights,r)*current**2),
        'energy_residual_w':float(qh-qc-current*voltage),
        'transport':'Zhang2025 dissimilar research specimen P/N, affine-T integrated analog',
        'high_T_assumption_applied':bool(max(th,tc)>PUBLISHED_HIGH_K),
        'transport_domain_K':[LOW_K,HIGH_K],
        'affine_T_axial_approximation':True,
        'mean_effective_alpha_v_k':float(np.dot(weights,alpha)),
        'mean_effective_resistance_ohm':float(np.dot(weights,r)),
        'mean_effective_k_w_k':float(np.dot(weights,k)+bypass_w_k),
    }
