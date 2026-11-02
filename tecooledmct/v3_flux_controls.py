"""Preregistered electrical RT0 controls, not a thermal or device campaign."""
import json,time
from pathlib import Path
import numpy as np
from .v3_et_fem import Operator,structured,control_faces,PROPS,LAYERS,SCENARIOS
from .v3_flux_rt0 import FluxSpace,cg_solution

CASES = ('bar','series','parallel','laminate_normal','laminate_sheet',
         'layers_normal','layers_sheet','harmonic')


def setup(name,n):
    axis = 2 if name.endswith('normal') else 0
    layer = name.startswith('layers_')
    dims = [.0004,.0003,sum(t for m,t in LAYERS)] if 'laminate' in name or layer else [.001,.0003,.0002]
    if name == 'harmonic':
        dims = [.001]*3
    axes = [np.linspace(0,d,n+1) for d in dims]
    if layer:
        z = [0.]
        for m,t in LAYERS:
            z.extend(z[-1]+t*np.arange(1,n+1)/n)
        axes[2] = np.array(z)
        region = lambda i,j,k:k//n
        tensors = [np.eye(3)/(PROPS[m][0]*(2 if m=='Cu' else 1)) for m,t in LAYERS]
        mats = [m for m,t in LAYERS]
        contact = SCENARIOS['NOM']['plated_re']
    elif name in ('series','parallel'):
        region = (lambda i,j,k:int(i>=n//2)) if name == 'series' else (lambda i,j,k:int(j>=n//2))
        mats = ['Cu','BiSn']
        tensors = [np.eye(3)/PROPS[m][0] for m in mats]
        contact = SCENARIOS['NOM']['re']
    else:
        region = lambda i,j,k:0
        mats = ['Cu']
        tensors = [np.eye(3)/PROPS['Cu'][0]]
        contact = SCENARIOS['NOM']['re']
    # Independent explicit series/parallel arithmetic, not laminate().
    total = sum(t for m,t in LAYERS)
    rho = [PROPS[m][0]*(2 if m=='Cu' else 1) for m,t in LAYERS]
    parallel = sum(t/r for (m,t),r in zip(LAYERS,rho))/total
    normal = total/(sum(r*t for (m,t),r in zip(LAYERS,rho))+4*SCENARIOS['NOM']['plated_re'])
    if name.startswith('laminate'):
        tensors = [np.diag([parallel,parallel,normal])]
    p,t,r = structured(axes,region)
    tr,ids,faces = control_faces(p,t,r,axis)
    groups = [dict(name='control_'+str(i),material=m) for i,m in enumerate(mats)]
    op = Operator(p,t,r,tr,ids,dict(groups=groups,faces=faces),np.array(tensors),contact)
    area = np.prod([d for i,d in enumerate(dims) if i!=axis])
    if name == 'series':
        R = (dims[0]/2*(PROPS['Cu'][0]+PROPS['BiSn'][0])+contact)/area
    elif name == 'parallel':
        R = dims[0]/(area/2*(1/PROPS['Cu'][0]+1/PROPS['BiSn'][0]))
    elif 'normal' in name:
        R = dims[2]/(normal*area)
    elif 'sheet' in name:
        R = dims[0]/(parallel*area)
    else:
        R = dims[0]*PROPS['Cu'][0]/area
    exact = np.zeros((len(t),3))
    if name in ('parallel','layers_sheet'):
        exact[:,axis] = -np.array(tensors)[r,axis,axis]/dims[axis]
    else:
        exact[:,axis] = -1/R/area
    return op,contact,exact,R,axis,dims


def phi(x):
    x = x/.001
    return x[:,0]+.2*(x[:,1]**2-x[:,2]**2)


def exact_harmonic_J(x):
    y = x/.001
    return -np.stack([np.ones(y.shape[:-1]),.4*y[...,1],-.4*y[...,2]],axis=-1)/(.001*PROPS['Cu'][0])


def run_case(name,n):
    then = time.monotonic()
    op,re,exact,R,axis,dims = setup(name,n)
    harmonic = name == 'harmonic'
    cg,u,J = cg_solution(op,phi if harmonic else None)
    space = FluxSpace(op,re,harmonic,phi if harmonic else None)
    qmix,pmix = space.mixed()
    qrec,prec = space.recover(u,J,None if harmonic else cg['unit_potential_current_A'])
    modes = {}
    for method,q in [('recovered',qrec),('mixed',qmix)]:
        a = space.evaluate(q)
        target = exact_harmonic_J(a['locations']) if harmonic else exact[:,None,:]
        denom = np.sum(op.volume*np.mean(np.sum(target**2,axis=-1),axis=1))
        err = np.sqrt(np.sum(op.volume*np.mean(np.sum((a['J_quadrature']-target)**2,axis=-1),axis=1))/denom)
        b = {k:v for k,v in a.items() if k not in ('J_quadrature','locations','interface_power_faces')}
        b['relative_flux_L2_error'] = float(err)
        b['R_relative_error'] = None if harmonic else float(abs(1/a['input_A']/R-1))
        b['IV_loss_relative_error'] = None if harmonic else float(abs(a['total_W']/a['input_A']-1))
        if method == 'mixed':
            bounds = (-.2,1.2) if harmonic else (0.,1.)
            b['voltage_min'] = float(pmix.min());b['voltage_max'] = float(pmix.max())
            b['bounded'] = bool(pmix.min()>=bounds[0]-1e-8 and pmix.max()<=bounds[1]+1e-8)
            jumps = space.contact_jump(qmix,pmix)
            b['contact_law_jump_defect_V'] = float(abs(jumps[:,0]-jumps[:,1]).max()) if len(jumps) else 0.
            if name in ('series','layers_normal'):
                expected = re/(R*np.prod([d for i,d in enumerate(dims) if i!=axis]))
                b['analytic_jump_relative_error'] = float(np.max(abs(abs(jumps[:,0])/expected-1)))
        modes[method] = b
    # Independent raw P1 accuracy against the same analytical field, not cuts.
    target = exact_harmonic_J(space.c) if harmonic else exact
    # Exact integral for a linear manufactured J includes its cell covariance.
    points = space.evaluate(qmix)['locations']
    target4 = exact_harmonic_J(points) if harmonic else exact[:,None,:]
    cgerr = np.sqrt(np.sum(op.volume*np.mean(np.sum((J[:,None,:]-target4)**2,axis=-1),axis=1))/
                    np.sum(op.volume*np.mean(np.sum(target4**2,axis=-1),axis=1)))
    modes['P1_raw'] = dict(relative_flux_L2_error=float(cgerr),
        R_relative_error=None if harmonic else float(abs(cg['R_coupon_ohm']/R-1)),
        IV_loss_relative_error=None if harmonic else cg['loss_relative_error'])
    ok = all(v['relative_flux_L2_error']<1e-7 and v['R_relative_error']<1e-7 and v['IV_loss_relative_error']<1e-7 for v in modes.values()) if not harmonic else True
    ok = ok and modes['mixed']['bounded'] and modes['mixed']['contact_law_jump_defect_V']<1e-7
    ok = ok and all(modes[m]['max_cell_imbalance_relative']<1e-9 for m in ('mixed','recovered'))
    if 'analytic_jump_relative_error' in modes['mixed']:
        ok = ok and modes['mixed']['analytic_jump_relative_error']<1e-7
    return dict(case=name,n=n,tets=len(op.t),seconds=time.monotonic()-then,methods=modes,
                gate=bool(ok),analytic_R_ohm=None if harmonic else R,
                recovery_current='P1 weak terminal current fixed; not independent current proof',
                mixed_current='Independent RT0/P0 potential-driven solve; no CG current input')


def campaign(out):
    out.mkdir(exist_ok=False,parents=True);then=time.monotonic();records=[]
    op,*_=setup('bar',2)
    rejected=[]
    for value in (0.,-1.,float('nan')):
        try:FluxSpace(op,value)
        except ValueError:rejected.append(str(value))
        else:raise ValueError('Invalid contact negative control was admitted')
    original=op.tensor.copy();op.tensor=-op.tensor
    try:FluxSpace(op,1e-11)
    except ValueError:rejected.append('negative conductivity')
    else:raise ValueError('Nonpassive conductivity admitted')
    op.tensor=original
    for f in op.meta.values():f['electrical_port']=-1
    try:FluxSpace(op,1e-11)
    except ValueError:rejected.append('missing terminals')
    else:raise ValueError('Missing terminals admitted')
    (out/'negative_controls.json').write_text(json.dumps(dict(status='PASS',rejected=rejected),indent=2)+'\n')
    for name in CASES:
        for n in ((4,8) if name=='harmonic' else (2,4)):
            q = run_case(name,n);records.append(q)
            (out/'cases.json').write_text(json.dumps(records,indent=2)+'\n')
            if not q['gate']:
                (out/'gate.json').write_text(json.dumps(dict(status='FAIL/STOP',failed_case=name,n=n,
                    seconds=time.monotonic()-then,geometry='NOT RUN',coupon='NOT RUN',C='NOT RUN',D='NOT RUN'),indent=2)+'\n')
                return
    a,b = records[-2:];ratios={}
    for method in ('P1_raw','recovered','mixed'):
        e0=a['methods'][method]['relative_flux_L2_error'];e1=b['methods'][method]['relative_flux_L2_error']
        ratios[method]=e0/e1
    ok=all(b['methods'][m]['relative_flux_L2_error']<=.05 and ratios[m]>=1.5 for m in ratios)
    (out/'gate.json').write_text(json.dumps(dict(status='PASS' if ok else 'FAIL/STOP',
        harmonic_error_reduction=ratios,seconds=time.monotonic()-then,
        geometry='ELIGIBLE only if PASS',coupon='NOT RUN',C='NOT RUN',D='NOT RUN'),indent=2)+'\n')
