"""Source-centerline thermal reconstruction of original formed Cu tabs.

The profile solves a 1D, constant-k, uniform-Joule segment with the saved
multiport foil-node endpoint temperatures. It is conditional on the existing
lumped contact and constant-cross-section assumptions; no gas heat is added.
"""
import math

def _wrap(x):
    return (x + math.pi) % (2*math.pi) - math.pi

def project_yz(parts, point):
    """Closest source line/arc in the tab's y-z plane; return distance and arclength."""
    if len(point)!=2 or not all(math.isfinite(float(x)) for x in point):
        raise ValueError('invalid point')
    best=None; s=0.0
    for part in parts:
        a=part['a']; b=part['b']; length=part['length']
        if not math.isfinite(length) or length<=0: raise ValueError('bad path length')
        if part['type']=='line':
            v=[b[k]-a[k] for k in range(2)]; vv=sum(x*x for x in v)
            if vv<=0 or abs(math.sqrt(vv)-length)>1e-8: raise ValueError('line length mismatch')
            u=max(0.,min(1.,sum((point[k]-a[k])*v[k] for k in range(2))/vv)); q=[a[k]+u*v[k] for k in range(2)]
        elif part['type']=='arc':
            c=part['c']; radius=part['r']; aa=math.atan2(a[1]-c[1],a[0]-c[0]); bb=math.atan2(b[1]-c[1],b[0]-c[0]); sweep=_wrap(bb-aa)
            if radius<=0 or abs(abs(sweep)*radius-length)>1e-8: raise ValueError('arc length mismatch')
            angle=math.atan2(point[1]-c[1],point[0]-c[0]); delta=_wrap(angle-aa)
            candidates=[0.,1.]
            u=delta/sweep
            if 0<=u<=1: candidates.append(u)
            def xy(t):return [c[0]+radius*math.cos(aa+t*sweep),c[1]+radius*math.sin(aa+t*sweep)]
            u=min(candidates,key=lambda t:sum((xy(t)[k]-point[k])**2 for k in range(2)));q=xy(u)
        else: raise ValueError('unknown path part')
        dist=math.dist(point,q); cand=(dist,s+u*length)
        if best is None or cand[0]<best[0]:best=cand
        s+=length
    if best is None: raise ValueError('empty path')
    return best

def segment_profile(u, t0, t1, resistance_ohm, conductance_W_K, current_A):
    """Temperature and heat rates into the segment at its two ports."""
    vals=(u,t0,t1,resistance_ohm,conductance_W_K,current_A)
    if not all(math.isfinite(float(x)) for x in vals) or not 0<=u<=1 or min(t0,t1)<=0 or resistance_ohm<0 or conductance_W_K<=0 or current_A<0:
        raise ValueError('invalid segment')
    P=current_A**2*resistance_ohm
    T=(1-u)*t0+u*t1 + P/(2*conductance_W_K)*u*(1-u)
    # Positive is heat flowing from the endpoint into the conductor.
    q0=conductance_W_K*(t0-t1)-P/2
    q1=conductance_W_K*(t1-t0)-P/2
    return T,q0,q1

def segment_with_uniform_bath(u,t0,t1,resistance_ohm,conductance_W_K,current_A,bath_K,gas_G_W_K):
    """Exact constant-property segment with uniformly distributed bath exchange.

    gas_G is the whole-segment exchange conductance, NOT a geometry-derived
    coefficient. Return T, endpoint heat into conductor, gas heat out. The
    latter balances the two endpoint reactions plus electrical dissipation.
    """
    segment_profile(u,t0,t1,resistance_ohm,conductance_W_K,current_A)
    if not math.isfinite(bath_K) or bath_K<=0 or not math.isfinite(gas_G_W_K) or gas_G_W_K<0:
        raise ValueError('invalid bath')
    if gas_G_W_K==0:
        T,q0,q1=segment_profile(u,t0,t1,resistance_ohm,conductance_W_K,current_A)
        return T,q0,q1,0.
    G=conductance_W_K; H=gas_G_W_K; m=math.sqrt(H/G);P=current_A**2*resistance_ohm
    if m>50:raise ValueError('outside bounded analytic regime')
    if m<1e-5:
        # Stable asymptotic factors through O(m²); source shape through O(m²).
        w0=(1-u)*(1+m*m*(u*u-2*u)/6)
        w1=u*(1+m*m*(u*u-1)/6)
        source_shape=.5*u*(1-u)*(1-m*m*(1+u-u*u)/12)
        T=bath_K+w0*(t0-bath_K)+w1*(t1-bath_K)+P/G*source_shape
        mcoth=1+m*m/3;mcsch=1-m*m/6;mtanhhalf=m*m/2-m**4/24
    else:
        sh=math.sinh(m);w0=math.sinh(m*(1-u))/sh;w1=math.sinh(m*u)/sh
        shape=2*math.sinh(m*u/2)*math.sinh(m*(1-u)/2)/math.cosh(m/2)
        T=bath_K+w0*(t0-bath_K)+w1*(t1-bath_K)+P/H*shape
        mcoth=m*math.cosh(m)/sh;mcsch=m/sh;mtanhhalf=m*math.tanh(m/2)
    qsource=P*mtanhhalf/(m*m)
    q0=G*(mcoth*(t0-bath_K)-mcsch*(t1-bath_K))-qsource
    q1=G*(mcoth*(t1-bath_K)-mcsch*(t0-bath_K))-qsource
    qgas=P+q0+q1
    return T,q0,q1,qgas
