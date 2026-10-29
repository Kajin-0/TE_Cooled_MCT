"""Independent conservative radiosity and rarefied gas-film operators, SI.

These are reduced surface exchange operators, not a gas volume/CFD solution.
"""
import numpy as np
from scipy.linalg import solve
SIGMA=5.670374419e-8
KB=1.380649e-23
GASES={'N2':{'k':[.0183,.0259,.0326],'R':296.803,'gamma':1.4},'Ar':{'k':[.0124,.0177,.0224],'R':208.132,'gamma':5/3},'Kr':{'k':[.0064,.0095,.0122],'R':99.218,'gamma':5/3}}


def gas_properties(name,t,pressure):
    if name not in GASES or not np.isfinite(pressure) or pressure<0:raise ValueError('Unknown gas / negative pressure')
    t=np.asarray(t,dtype=float)
    if np.any(~np.isfinite(t)) or np.any(t<200) or np.any(t>400):raise ValueError('Gas k(T) outside ingested NIST200..400 K')
    r=GASES[name];k=np.interp(t,[200,300,400],r['k']);R=r['R'];cp=r['gamma']/(r['gamma']-1)*R
    # Eucken relation: viscosity is a kinetic closure, not measured viscosity data.
    mu=k/(cp+1.25*R);pr=mu*cp/k;lam=mu/max(pressure,1e-300)*np.sqrt(np.pi*R*t/2)
    return {'k':k,'mu':mu,'cp':cp,'rho':pressure/(R*t),'lambda_m':lam,'Pr':pr,'gamma':r['gamma'],'R':R}


def gas_conductances(w,dist,t,name,pressure,accommodation=.8):
    if not 0<accommodation<=1:raise ValueError('Accommodation in (0,1] required')
    if pressure<0 or not np.isfinite(pressure):raise ValueError('Finite nonnegative pressure required')
    if pressure==0:return np.zeros_like(w)
    tt=(np.asarray(t)[:,None]+np.asarray(t)[None,:])/2;p=gas_properties(name,tt,pressure)
    jump=(2-accommodation)/accommodation*2*p['gamma']/(p['gamma']+1)*p['lambda_m']/p['Pr']
    g=p['k']*w/(dist+2*jump);np.fill_diagonal(g,0)
    if np.any(g<0) or not np.allclose(g,g.T,atol=1e-16,rtol=1e-12):raise ValueError('Nonconservative gas matrix')
    return g


def gas_power(g,t):
    t=np.asarray(t);return g@t-g.sum(axis=1)*t


def radiation_matrix(areas,f,emissivity):
    a=np.asarray(areas);f=np.asarray(f);e=np.broadcast_to(emissivity,a.shape).astype(float)
    if np.any(e<0) or np.any(e>1) or np.any(f<0) or not np.allclose(f.sum(axis=1),1,atol=1e-10):raise ValueError('Invalid gray enclosure')
    if not np.allclose(a[:,None]*f,(a[:,None]*f).T,atol=1e-13,rtol=1e-9):raise ValueError('View-factor reciprocity failure')
    if not np.any(e):return np.zeros_like(f)
    h=solve(np.eye(len(a))-(1-e[:,None])*f,np.diag(e)*SIGMA,assume_a='gen')
    l=a[:,None]*((np.eye(len(a))-f)@h)
    # Reciprocity makes this symmetric; retain only roundoff-level correction.
    if np.max(np.abs(l-l.T))>max(1e-18,np.max(np.abs(l))*1e-8):raise ValueError('Radiosity lost reciprocity')
    l=(l+l.T)/2;np.fill_diagonal(l,0);np.fill_diagonal(l,-l.sum(axis=1));return l


def balanced_view_factors(raw,areas,tolerance=1e-10):
    a=np.asarray(areas);raw=np.asarray(raw)
    if np.any(raw<0) or not np.allclose(raw,raw.T):raise ValueError('Symmetric positive exchange areas required')
    if np.any(raw.sum(axis=1)<=0):raise ValueError('Isolated radiative patch')
    d=np.ones(len(a))
    for iteration in range(20000):
        row=d*(raw@d);ratio=a/row
        if np.max(np.abs(ratio-1))<tolerance:break
        d*=np.sqrt(ratio)
    else:raise ValueError('Reciprocal closure scaling did not converge')
    w=d[:,None]*raw*d[None,:];f=w/a[:,None]
    return f,{'iterations':iteration,'raw_row_min':float((raw.sum(axis=1)/a).min()),'raw_row_max':float((raw.sum(axis=1)/a).max()),'raw_area_weighted_closure_error':float(np.sum(abs(raw.sum(axis=1)-a))/a.sum()),'diagonal_scale_min':float(d.min()),'diagonal_scale_max':float(d.max()),'closure_max_error':float(abs(f.sum(axis=1)-1).max()),'reciprocity_max_m2':float(abs(w-w.T).max()),'visibility_zeros_preserved':bool(np.all(w[raw==0]==0)),'method':'symmetric diagonal area balancing; raw quadrature error and scale corrections reported, no blocked ray restored'}


def ray_box_blocked(start,end,boxes,source_owner=None,target_owner=None):
    """Open segments against exact orthogonal opaque solids, endpoint contacts excluded."""
    start=np.atleast_2d(start);end=np.atleast_2d(end);delta=end-start;blocked=np.zeros(len(start),bool)
    segment_low=np.minimum(start,end);segment_high=np.maximum(start,end)
    for box in boxes:
        low=np.asarray(box[:3]);high=low+box[3:]
        use=np.flatnonzero((~blocked)&np.all(segment_high>=low-1e-12,axis=1)&np.all(segment_low<=high+1e-12,axis=1))
        if not len(use):continue
        ss=start[use];dd=delta[use];parallel=np.abs(dd)<1e-18;safe=np.where(parallel,1.,dd);u=(low-ss)/safe;v=(high-ss)/safe
        lo=np.where(parallel,-np.inf,np.minimum(u,v));hi=np.where(parallel,np.inf,np.maximum(u,v));outside=np.any(parallel&((ss<low-1e-12)|(ss>high+1e-12)),axis=1)
        enter=np.maximum(np.max(lo,axis=1),1e-7);leave=np.minimum(np.min(hi,axis=1),1-1e-7)
        blocked[use] |= (~outside)&(leave>enter+1e-9)
    return blocked


def ray_pin_blocked(start,end,pins,owners,source_owner,target_owner):
    start=np.atleast_2d(start);end=np.atleast_2d(end);d=end-start;out=np.zeros(len(start),bool)
    for pin in pins:
        x,y,r,z0,z1,bid=pin;v=start[:,:2]-[x,y];aa=np.sum(d[:,:2]**2,axis=1);bb=2*np.sum(v*d[:,:2],axis=1);cc=np.sum(v*v,axis=1)-r*r;disc=bb*bb-4*aa*cc
        root=np.sqrt(np.maximum(disc,0));a=np.where(aa>1e-30,(-bb-root)/(2*np.maximum(aa,1e-30)),-np.inf);b=np.where(aa>1e-30,(-bb+root)/(2*np.maximum(aa,1e-30)),np.inf)
        dz=d[:,2];zz=np.where(abs(dz)>1e-20,dz,1.);za=(z0-start[:,2])/zz;zb=(z1-start[:,2])/zz;zl=np.where(abs(dz)>1e-20,np.minimum(za,zb),-np.inf);zh=np.where(abs(dz)>1e-20,np.maximum(za,zb),np.inf)
        valid=(disc>=0)&((aa>1e-30)|(cc<0))&((abs(dz)>1e-20)|((start[:,2]>z0)&(start[:,2]<z1)))
        hit=np.minimum.reduce([b,zh,np.full(len(a),1-1e-7)])>np.maximum.reduce([a,zl,np.full(len(a),1e-7)])+1e-9
        # A convex endpoint cylinder cannot occlude an outward/incident ray.
        out|=valid&hit&(source_owner!=bid)&(target_owner!=bid)
    return out


def rayleigh_screen():
    rows=[]
    for gas in GASES:
        for pressure in (1.,100.,101325.):
            for gap in (.001,.003,.008,.0142):
                p=gas_properties(gas,250.,pressure);rho=float(p['rho']);nu=float(p['mu'])/rho;alpha=float(p['k'])/(rho*p['cp']);ra=9.80665/250*100*gap**3/(nu*alpha)
                rows.append({'gas':gas,'pressure_pa':pressure,'T_k':250,'delta_t_k':100,'gap_m':gap,'Ra':ra,'Kn':float(p['lambda_m'])/gap,'convection_flag':bool(ra>1708),'criterion_note':'1708 is ideal horizontal heated-below onset, not universal cavity threshold; above it requires a dedicated convection assessment'})
    return rows
