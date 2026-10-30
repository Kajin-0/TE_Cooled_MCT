"""Integrated plausible-reference TEC/package thermal screening, not a 3D FEM solve.

Geometry and 1D wire coefficients: immutable corrected 88-leg package archive.
Nodal TEC: first-principles constant-law P/N surrogate, energy-conserving cascade.
Cap/window and gas: explicitly *assumed reservoirs/operators*, not meshed fields.
Historical OEM fits and old-geometry G3b enclosure geometry are not imported.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from .fem_g2a import PROPERTIES
from .fem_g3b_exchange import SIGMA, GASES
from .g2d_data import ROOT

GEOMETRY=ROOT/'fem/results/geometry_complete_checkpoint_20261030'
GEOM_FILES=('manifest.json','wire_routes.json')
STAGE_MATERIAL_STATUS='constant first-principles G1 verification proxy (NOT OEM transport grade)'
TEMPERATURE_NODES=('hot_ceramic','stage1','stage2','cold_ceramic','MCT_die')


class OperatingPointFailure(ValueError):
    """Rejected solve with auditable candidates, never an accepted state."""

    def __init__(self,message,diagnostics):
        super().__init__(message)
        self.diagnostics=diagnostics


def failure_diagnostics(s,x=None,residual=None,fit=None,*,error=None):
    """Keep physical W residuals separate from the optimizer's scaled K row."""
    lower,upper=180.+1e-6,390.-1e-6
    finite=x is not None and bool(np.isfinite(x).all())
    temperatures=dict(zip(TEMPERATURE_NODES,map(float,x))) if finite else None
    active={name:('lower' if t-lower<=1e-4 else 'upper' if upper-t<=1e-4 else None)
            for name,t in temperatures.items()} if finite else None
    valid_r=residual is not None and bool(np.isfinite(residual).all())
    r=np.asarray(residual) if valid_r else None
    if fit is None:
        classification='evaluation_or_input_error'
    elif not fit.success:
        classification='optimizer_failure'
    elif active and any(active.values()) and valid_r and np.max(np.abs(r))>1e-8:
        classification='active_bound_residual_failure'
    else:
        classification='residual_or_energy_gate_failure'
    return {
        'classification':classification,
        'scenario':asdict(s),
        'last_candidate_temperatures_k':temperatures,
        'node_balance_residuals_w':dict(zip(TEMPERATURE_NODES[1:],map(float,r[:4]))) if valid_r else None,
        'max_node_balance_residual_w':float(np.max(np.abs(r[:4]))) if valid_r else None,
        'hot_sink_temperature_residual_k':float(2*r[4]) if valid_r else None,
        'optimizer_scaled_residuals':r.tolist() if valid_r else None,
        'max_optimizer_scaled_residual':float(np.max(np.abs(r))) if valid_r else None,
        'optimizer_residual_units':'first four W; last K divided by 2 (optimizer scaling only)',
        'active_temperature_bounds':active,
        'active_temperature_bound_tolerance_k':1e-4,
        'any_active_temperature_bound':bool(any(active.values())) if active else None,
        'physical_domain':{
            'model_temperature_interval_k':[180.,390.],
            'optimizer_temperature_interval_k':[lower,upper],
            'candidate_within_model_domain':bool(min(x)>=180 and max(x)<=390) if finite else None,
            'measured_PN_interval_k':[40.,300.] if s.material_model!='g1_constant' else None,
            'PN_candidate_within_measured_interval':bool(min(x[:4])>=40 and max(x[:4])<=300)
                if finite and s.material_model!='g1_constant' else None,
            'assumed_high_T_continuation_used':bool(max(x[:4])>300)
                if finite and s.material_model!='g1_constant' else None,
            'interpretation':'An active bound does not prove an out-of-domain physical solution or physical infeasibility.'},
        'optimizer':{'success':bool(fit.success) if fit is not None else None,
                     'status':int(fit.status) if fit is not None else None,
                     'message':str(fit.message) if fit is not None else error,
                     'nfev':int(fit.nfev) if fit is not None else None,
                     'active_mask':np.asarray(fit.active_mask,dtype=int).tolist() if fit is not None else None},
        'evaluation_error':error,
        'candidate_is_accepted':False,
    }


@dataclass(frozen=True)
class Scenario:
    ambient_k: float=300.
    current_a: float=.15
    material_model: str='g1_constant'  # opt-in: zhang2025_analog; prior results untouched
    heat_sink_k_w: float=2.
    detector_bias_w: float=.0015
    detector_absorbed_w: float=.0005
    gas: str='Kr'
    cavity_pressure_pa: float=30000.
    gas_gap_m: float=.003
    gas_area_factor: float=1.
    accommodation: float=.8
    cap_emissivity: float=.2
    ceramic_emissivity: float=.8
    window_thermal_emissivity: float=.1
    cap_view_factor: float=.5
    window_die_view_factor: float=.7
    cold_surface_factor: float=1.5
    pn_seebeck_scale: float=1.
    pn_resistivity_scale: float=1.
    pn_thermal_conductivity_scale: float=1.
    die_attach_conductivity_w_mk: float=1.
    au_wire_conductance_scale: float=1.
    cu_wire_conductance_scale: float=1.
    # Unmodeled surface/route bypass: explicit hypothesis per stage.
    stage_bypass_w_k: tuple=(0.,0.,0.)

    def validate(self):
        vals=asdict(self)
        if not all(np.isfinite(v) for k,v in vals.items() if isinstance(v,(int,float))):
            raise ValueError('Nonfinite scenario input')
        if self.gas not in GASES:
            raise ValueError('Unsupported gas species')
        if self.material_model not in ('g1_constant','zhang2025_analog','zhang2025_nonlinear'):
            raise ValueError('Unsupported TEC material model')
        if not (180.<=self.ambient_k<=380.) or not (0.<=self.current_a<=1.):
            raise ValueError('Scenario beyond declared thermal/current screening interval')
        for n in ('heat_sink_k_w','detector_bias_w','detector_absorbed_w','cavity_pressure_pa',
                  'au_wire_conductance_scale','cu_wire_conductance_scale'):
            if getattr(self,n)<0:raise ValueError('Negative '+n)
        for n in ('gas_gap_m','gas_area_factor','pn_seebeck_scale','pn_resistivity_scale',
                  'pn_thermal_conductivity_scale','die_attach_conductivity_w_mk',
                  'cold_surface_factor'):
            if getattr(self,n)<=0:raise ValueError('Nonpositive '+n)
        for n in ('accommodation','cap_emissivity','ceramic_emissivity','window_thermal_emissivity',
                  'cap_view_factor','window_die_view_factor'):
            val=getattr(self,n)
            if not 0<=val<=1 or (n=='accommodation' and val==0):
                raise ValueError('Outside 0..1 '+n)
        if len(self.stage_bypass_w_k)!=3 or any(x<0 or not np.isfinite(x) for x in self.stage_bypass_w_k):
            raise ValueError('Invalid stage bypass values')
        return self


def geometry():
    """Load *corrected* source-registered 3D dimensions, no remeshing."""
    raw={name:(GEOMETRY/name).read_bytes() for name in GEOM_FILES}
    ledger=json.loads((GEOMETRY/'checksums.json').read_text())['artifact_sha256']
    for name,data in raw.items():
        if hashlib.sha256(data).hexdigest()!=ledger[name]:
            raise ValueError('Protected corrected geometry archive hash mismatch: '+name)
    m=json.loads(raw['manifest.json'])
    wires=json.loads(raw['wire_routes.json'])['wires']
    if m['legs']!=88 or m['stage_couples_assumed']!=[28,12,4]:
        raise ValueError('Unexpected corrected TEC stage geometry')
    if len(wires)!=4 or sorted(w['pin'] for w in wires)!=[1,7,8,9]:
        raise ValueError('Incorrect corrected hybrid wire routes')
    ceramic={b['id']:b for b in m['bodies'] if b['kind']=='ceramic'}
    if set(ceramic)!={1,2,3,4}:raise ValueError('Incorrect ceramic stack')
    squares=[float(ceramic[i]['boxes_m'][0][3])**2 for i in (1,2,3,4)]
    attach=next(b['boxes_m'][0] for b in m['bodies'] if b['id']==302)
    die=next(b['boxes_m'][0] for b in m['bodies'] if b['id']==303)
    if abs(attach[3]*attach[4]-die[3]*die[4])>=1e-16:
        raise ValueError('Mismatched detector and attach footprint')
    stages=[]
    legs=[b for b in m['bodies'] if b['kind']=='leg']
    for net in m['stage_nets']:
        stage=int(net['stage']);pair=[b for b in legs if b['stage']==stage]
        p=[b for b in pair if b['material']=='P'];n=[b for b in pair if b['material']=='N']
        if len(p)!=len(n) or len(p)!=net['couples']:raise ValueError('Incorrect corrected stage allocations')
        box=p[0]['boxes_m'][0];a=box[3]*box[4];height=box[5]
        if any(abs(b['boxes_m'][0][5]-height)>1e-12 or abs(b['boxes_m'][0][3]*b['boxes_m'][0][4]-a)>1e-16 for b in pair):
            raise ValueError('Nonuniform leg geometry; resolve geometry individually')
        if abs(height-net['leg_height_m'])>1e-12:raise ValueError('Stage leg length mismatch')
        stages.append({'couples':len(p),'leg_length_m':height,'leg_area_m2':a})
    return {'stages':stages,'ceramic_sides_area_m2':squares,
            'die_area_m2':die[3]*die[4],
            'die_attach_thickness_over_area_m_inverse':attach[5]/(attach[3]*attach[4]),
            'wires':wires,
            'source_archive':'fem/results/geometry_complete_checkpoint_20261030',
            'source_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},
            'material_status':STAGE_MATERIAL_STATUS}


def coefficients(s:Scenario,g):
    s.validate();out=[]
    for st,bypass in zip(g['stages'],s.stage_bypass_w_k):
        n=st['couples'];a=st['leg_area_m2'];h=st['leg_length_m']
        sp=PROPERTIES['P'];sn=PROPERTIES['N']
        alpha=n*(sp[2]-sn[2])*s.pn_seebeck_scale
        r=n*h/a*(1/sp[1]+1/sn[1])*s.pn_resistivity_scale
        k=n*a/h*(sp[0]+sn[0])*s.pn_thermal_conductivity_scale+bypass
        out.append({'alpha_v_k':alpha,'r_ohm':r,'k_w_k':k,'couples':n})
    return out


def gas_transport(s:Scenario,mean_k:float):
    """NIST/G3b 200..400 K tabulations; 180..200 K a DECLARED surrogate."""
    if not 180<=mean_k<=400:raise ValueError('Gas temperature outside bounded180..400K scenario')
    p=GASES[s.gas]
    k=float(np.interp(max(mean_k,200.),[200.,300.,400.],p['k']))
    extrapolated=mean_k<200
    if extrapolated:k*= (mean_k/200.)**.75  # engineering hypothesis, NOT measured NIST data
    R=p['R'];gamma=p['gamma']
    cp=gamma/(gamma-1)*R
    mu=k/(cp+1.25*R)  # Eucken approximation
    Pr=mu*cp/k
    lam=mu/max(s.cavity_pressure_pa,1e-300)*np.sqrt(np.pi*R*mean_k/2)
    jump= (2-s.accommodation)/s.accommodation*2*gamma/(gamma+1)*lam/Pr
    return k, jump, extrapolated


def radiative_load(warm,cold,area,emissivity_warm,emissivity_cold,view):
    if view==0 or area==0 or emissivity_warm==0 or emissivity_cold==0:return 0.
    effective=1/(1/emissivity_warm+1/emissivity_cold-1)
    return view*effective*SIGMA*area*(warm**4-cold**4)


def heat_paths(s:Scenario,g,temperatures):
    """Positive heat INTO each cold stage/die; cap+pins at ambient by hypothesis."""
    hot,t1,t2,t3,die=temperatures;warm=s.ambient_k
    sizes=g['ceramic_sides_area_m2'];diearea=g['die_area_m2']
    exposed=np.array([sizes[1]-sizes[2],sizes[2]-sizes[3],sizes[3]-diearea,diearea])
    if np.any(exposed<=0):raise ValueError('Invalid cold geometry surface areas')
    exposed[:3]*=s.cold_surface_factor
    cold=np.array([t1,t2,t3,die])
    gas=np.zeros(4);rad=np.zeros(4);sub200=False
    for i in range(4):
        avg=.5*(warm+cold[i])
        if s.cavity_pressure_pa:
            k,jump,used=gas_transport(s,avg);sub200|=used
            gas[i]=k*exposed[i]*s.gas_area_factor*(warm-cold[i])/(s.gas_gap_m+2*jump)
        epsilon=s.window_thermal_emissivity if i==3 else s.cap_emissivity
        vf=s.window_die_view_factor if i==3 else s.cap_view_factor
        rad[i]=radiative_load(warm,cold[i],exposed[i],epsilon,s.ceramic_emissivity,vf)
    wire_au=sum(w['G_W_K'] for w in g['wires'] if w['material']=='Au')*s.au_wire_conductance_scale*(warm-die)
    wire_cu=sum(w['G_W_K'] for w in g['wires'] if w['material']=='Cu')*s.cu_wire_conductance_scale*(warm-hot)
    cu_joule=s.current_a**2*sum(w['R_ohm'] for w in g['wires'] if w['material']=='Cu')
    die_heating=s.detector_bias_w+s.detector_absorbed_w
    attach_g=s.die_attach_conductivity_w_mk/g['die_attach_thickness_over_area_m_inverse']
    die_into_cold=attach_g*(die-t3)
    external=gas+rad;external[3]+=wire_au
    return {'gas_w':gas,'radiation_w':rad,'Au_wires_into_die_w':float(wire_au),
            'Cu_conduction_into_hot_w':float(wire_cu),
            'Cu_total_joule_w':float(cu_joule),
            'die_internal_heating_w':float(die_heating),
            'die_attach_into_cold_w':float(die_into_cold),
            'external_into_nodes_w':external,
            'gas_sub200_engineering_extension_used':bool(sub200),
            'warm_reservoir_k':float(warm),
            'gas_window_status':'effective gap and area, not a meshed cavity/optical window'}


def stage_thermoelectric(coeff,th,tc,current):
    alpha,r,k=(coeff[n] for n in ('alpha_v_k','r_ohm','k_w_k'))
    qcond=k*(th-tc)
    qc=alpha*current*tc-.5*current**2*r-qcond
    qh=alpha*current*th+.5*current**2*r-qcond
    voltage=current*r+alpha*(th-tc)
    return {'qc_w':qc,'qh_w':qh,'voltage_v':voltage,'conduction_w':qcond,
            'joule_w':current*current*r,
            'energy_residual_w':qh-qc-current*voltage}


def solve(s:Scenario,g=None,*,transport_intervals=32,exchange=None):
    s.validate()
    if g is None:g=geometry()
    coeff=coefficients(s,g)
    nonlinear=None
    if s.material_model=='zhang2025_nonlinear':
        from .nonlinear_tec import Transport
        nonlinear=Transport(transport_intervals)

    def evaluate(x):
        hot,t1,t2,t3,die=x
        th=(hot,t1,t2);tc=(t1,t2,t3)
        if s.material_model in ('zhang2025_analog','zhang2025_nonlinear'):
            if nonlinear is None:
                from .graded_tec import stage as graded_stage
            else:
                graded_stage=nonlinear.stage
            stages=[graded_stage(g['stages'][i],a,b,s.current_a,
                       alpha_scale=s.pn_seebeck_scale,rho_scale=s.pn_resistivity_scale,
                       k_scale=s.pn_thermal_conductivity_scale,
                       bypass_w_k=s.stage_bypass_w_k[i])
                    for i,(a,b) in enumerate(zip(th,tc))]
        else:
            stages=[stage_thermoelectric(c,a,b,s.current_a) for c,a,b in zip(coeff,th,tc)]
        paths=heat_paths(s,g,x)
        if exchange is not None:
            from .corrected_exchange import evaluate as exchange_evaluate
            transfer=exchange_evaluate(exchange,[*map(float,x),s.ambient_k,s.ambient_k,s.ambient_k],
                pressure_pa=s.cavity_pressure_pa,gas=s.gas,accommodation=s.accommodation,
                cap_emissivity=s.cap_emissivity,window_emissivity=s.window_thermal_emissivity,
                body_emissivity=s.ceramic_emissivity,gas_scale=s.gas_area_factor)
            gas=np.asarray(transfer['gas_nodes_w']);radiation=np.asarray(transfer['radiation_nodes_w'])
            paths['gas_w']=gas[1:5];paths['radiation_w']=radiation[1:5]
            paths['external_into_nodes_w']=gas[1:5]+radiation[1:5]
            paths['external_into_nodes_w'][3]+=paths['Au_wires_into_die_w']
            paths['enclosure_into_hot_w']=float(gas[0]+radiation[0])
            paths['enclosure_reservoir_into_w']=(gas+radiation)[5:].tolist()
            paths['enclosure_conservation_residual_w']=transfer['max_conservation_residual_w']
        e=paths['external_into_nodes_w']
        # Stage 0/1/2 and die conservation, hot-side bath balance.
        residual=np.array([
            stages[0]['qc_w']-stages[1]['qh_w']-e[0],
            stages[1]['qc_w']-stages[2]['qh_w']-e[1],
            stages[2]['qc_w']-e[2]-paths['die_attach_into_cold_w'],
            paths['die_attach_into_cold_w']-e[3]-paths['die_internal_heating_w'],
            hot-s.ambient_k-s.heat_sink_k_w*(stages[0]['qh_w']+
                        paths['Cu_conduction_into_hot_w']+.5*paths['Cu_total_joule_w']+
                        paths.get('enclosure_into_hot_w',0.))
        ])
        # Last row in K, scale it to W using 1/(2 K/W) for optimization.
        residual[4]/=2.
        return stages,paths,residual

    init=np.array([s.ambient_k+.2,s.ambient_k-12,s.ambient_k-22,s.ambient_k-30,s.ambient_k-29.9])
    if s.current_a<.02:init[:]=s.ambient_k
    initialization='default temperature estimate'
    if nonlinear is not None:
        try:
            guess=solve(replace(s,material_model='g1_constant'),g,exchange=exchange)
            init=np.array([guess['temperatures_k'][name] for name in TEMPERATURE_NODES])
            initialization='g1_constant package solve used as initial iterate ONLY'
        except ValueError:
            initialization='constant-law guess failed; default estimate used'
    lower=np.full(5,180.+1e-6);upper=np.full(5,390.-1e-6)
    x0=np.clip(init,lower+1e-4,upper-1e-4)
    last={'x':None,'residual':None}
    def objective(x):
        last['x']=np.array(x,copy=True)
        last['residual']=None
        result=evaluate(x)[2]
        last['residual']=result
        return result
    fit=None
    try:
        fit=least_squares(objective,x0,bounds=(lower,upper),
                          max_nfev=250,ftol=1e-12,xtol=1e-12,gtol=1e-12)
        last['x']=np.array(fit.x,copy=True)
        last['residual']=None
        stages,paths,residual=evaluate(fit.x)
    except (ValueError,RuntimeError,FloatingPointError) as error:
        diagnostics=failure_diagnostics(s,last['x'],last['residual'],fit,error=str(error))
        if hasattr(error,'diagnostics'):diagnostics['transport_failure']=error.diagnostics
        raise OperatingPointFailure(str(error),diagnostics) from error
    maximum=float(np.max(np.abs(residual)))
    if not fit.success or maximum>1e-8 or any(t<180 or t>390 for t in fit.x):
        raise OperatingPointFailure(
            f'Nonconverged/infeasible plausible operating point, residual={maximum:.5g}',
            failure_diagnostics(s,fit.x,residual,fit))
    vtec=sum(st['voltage_v'] for st in stages)
    vwire=s.current_a*sum(w['R_ohm'] for w in g['wires'] if w['material']=='Cu')
    pin_in=paths['Cu_conduction_into_hot_w']-.5*paths['Cu_total_joule_w']
    extcold=float(paths['external_into_nodes_w'].sum())
    hot_exchange=paths.get('enclosure_into_hot_w',0.)
    q_bath=stages[0]['qh_w']+paths['Cu_conduction_into_hot_w']+.5*paths['Cu_total_joule_w']+hot_exchange
    global_error=(vtec+vwire)*s.current_a+paths['die_internal_heating_w']+extcold+pin_in+hot_exchange-q_bath
    if abs(global_error)>1e-8 or any(abs(st['energy_residual_w'])>1e-9 for st in stages):
        diagnostics=failure_diagnostics(s,fit.x,residual,fit)
        diagnostics['global_energy_residual_w']=float(global_error)
        diagnostics['stage_energy_residuals_w']=[st['energy_residual_w'] for st in stages]
        raise OperatingPointFailure('Power bookkeeping failed',diagnostics)
    from .graded_tec import source_evidence
    out={'method':'corrected-geometry, 5-node conservative screening; NOT 3D FEM or OEM-validated',
         'transport_source':source_evidence() if s.material_model!='g1_constant' else
              {'id':'G1 constant verification properties','grade_matched':False},
         'material_model':s.material_model,
         'scenario':asdict(s),'geometry_provenance':g['source_sha256'],
         'temperatures_k':{'hot_ceramic':float(fit.x[0]),'stage1':float(fit.x[1]),
             'stage2':float(fit.x[2]),'cold_ceramic':float(fit.x[3]),'MCT_die':float(fit.x[4])},
         'cold_stage_lift_k':float(fit.x[0]-fit.x[3]),
         'MCT_die_k':float(fit.x[4]),
         'current_a':s.current_a,'module_voltage_v':float(vtec),
         'terminal_voltage_v':float(vtec+vwire),
         'module_electrical_power_w':float(s.current_a*vtec),
         'terminal_electrical_power_w':float(s.current_a*(vtec+vwire)),
         'bath_rejected_power_w':float(q_bath),
         'stage_budget':stages,
         'heat_paths_w':{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in paths.items()},
         'max_node_balance_residual_w':maximum,
         'global_energy_residual_w':float(global_error),
         'numerical_evaluations':int(fit.nfev),
         'qualification':'exploratory plausible reference, no matched-grade identification or 3D cavity field'}
    if nonlinear is not None:
        out['transport_computation']={**nonlinear.statistics(),'initialization':initialization}
    if exchange is not None:
        out['enclosure_operator']={'payload_sha256':exchange['payload_sha256'],
            'scope':exchange['scope'],'inactive_legacy_controls':['gas_gap_m','cold_surface_factor',
                'cap_view_factor','window_die_view_factor']}
    return out


def scenarios():
    """Engineering hypotheses; neither posterior intervals nor measured ranges."""
    nominal=Scenario()
    return {
        'vacuum_low_parasitic':replace(nominal,cavity_pressure_pa=0.,cap_emissivity=.08,
            window_thermal_emissivity=.05,heat_sink_k_w=.5,gas_area_factor=.5,
            au_wire_conductance_scale=.75),
        'nominal_krypton':nominal,
        'nitrogen_high_parasitic':replace(nominal,gas='N2',cavity_pressure_pa=101325.,
            cap_emissivity=.65,window_thermal_emissivity=.6,
            heat_sink_k_w=5.,gas_area_factor=1.5,
            au_wire_conductance_scale=1.25,
            cold_surface_factor=2.),
    }


def sensitivity(g=None, current=.15, material_model='g1_constant',exchange=None):
    """One-factor engineering envelope, not uncertainty quantiles or calibration."""
    if g is None:g=geometry()
    base=replace(Scenario(),current_a=current,material_model=material_model)
    reference=solve(base,g,exchange=exchange)
    trials={
        'Seebeck surrogate scale':('pn_seebeck_scale',.90,1.10),
        'P/N electrical resistivity scale':('pn_resistivity_scale',.80,1.20),
        'P/N thermal conductivity scale':('pn_thermal_conductivity_scale',.80,1.20),
        'hot-side heat-sink K/W':('heat_sink_k_w',.5,5.),
        'cavity pressure Pa':('cavity_pressure_pa',0.,101325.),
        'effective gas area scale':('gas_area_factor',.5,1.5),
        'cap thermal emissivity':('cap_emissivity',.08,.65),
        'Au bond conductance scale':('au_wire_conductance_scale',.75,1.25),
        'die attach conductivity W/(m K)':('die_attach_conductivity_w_mk',.5,3.),
        'detector bias dissipation W':('detector_bias_w',.0005,.005),
    }
    results=[]
    for description,(field,lower,upper) in trials.items():
        endpoints=[]
        for value in (lower,upper):
            result=solve(replace(base,**{field:value}),g,exchange=exchange)
            endpoints.append(result['MCT_die_k'])
        results.append({'factor':description,'field':field,'low_input':lower,'high_input':upper,
                        'low_result_die_k':endpoints[0], 'high_result_die_k':endpoints[1],
                        'baseline_die_k':reference['MCT_die_k'],
                        'endpoint_span_abs_k':abs(endpoints[1]-endpoints[0]),
                        'direction':'warmer_when_increased' if endpoints[1]>endpoints[0] else 'cooler_when_increased'})
    return sorted(results,key=lambda r:r['endpoint_span_abs_k'],reverse=True)


def run(out, material_model='g1_constant',exchange=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if material_model not in ('g1_constant','zhang2025_analog','zhang2025_nonlinear'):
        raise ValueError('Unsupported material model')
    g=geometry()
    cases={};rows=[]
    for name,s in scenarios().items():
        s=replace(s,material_model=material_model)
        for i in (step/20 for step in range(21)): # bounded 0..1 A, 0.05 A grid
            label=f'{name}_I{i:.2f}'
            try:
                result=solve(replace(s,current_a=i),g,exchange=exchange)
                cases[label]=result
                rows.append({'scenario':name,'current_a':i,'detector_k':result['MCT_die_k'],
                             'hot_k':result['temperatures_k']['hot_ceramic'],
                             'terminal_voltage_v':result['terminal_voltage_v'],
                             'terminal_power_w':result['terminal_electrical_power_w'],
                             'bath_w':result['bath_rejected_power_w']})
            except ValueError as error:
                diagnostics=getattr(error,'diagnostics',None)
                if diagnostics is None:
                    diagnostics=failure_diagnostics(replace(s,current_a=i),error=str(error))
                cases[label]={'status':'FAILED CLOSED','reason':str(error),
                              'diagnostics':diagnostics}
    oat=sensitivity(g,material_model=material_model,exchange=exchange)
    grid_best={}
    for name in scenarios():
        subset=[r for r in rows if r['scenario']==name]
        minimum=min(subset,key=lambda r:r['detector_k'])
        rejected=[k for k,v in cases.items() if k.startswith(name+'_') and 'status' in v]
        grid_best[name]={'current_a':minimum['current_a'],'detector_k':minimum['detector_k'],
                         'meaning':'minimum among accepted discretely sampled cases ONLY; not a continuous physical optimum; any rejected current intervals invalidate an unrestricted optimum claim',
                         'failed_case_labels':rejected,
                         'unqualified_optimum_if_failures':bool(rejected)}
    report={'label':'plausible reference-only; not Elmer or product qualification',
            'corrected_geometry':g['source_archive'],'geometry_sha256':g['source_sha256'],
            'temperature_dependent_tec':material_model!='g1_constant',
            'material_model':material_model,
            'source_transport_status':STAGE_MATERIAL_STATUS if material_model=='g1_constant' else 'Zhang2025 P/N research analog with explicit 300..390K engineering extension',
            'hypotheses':{n:asdict(replace(s,material_model=material_model)) for n,s in scenarios().items()},
            'cases':cases,'summary_rows':rows,'grid_best':grid_best,
            'one_factor_sensitivity':oat,
            'sensitivity_warning':'endpoint span across user-defined engineering hypotheses, NOT a statistical uncertainty interval'}
    (out/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    import csv
    for filename,records in (('sweep.csv',rows),('sensitivity.csv',oat)):
        with (out/filename).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n')
            w.writeheader();w.writerows(records)
    print('Plausible scenario operating-point summary:')
    for r in rows:
        if r['current_a'] in (.0,.1,.15,.25):
            print(r['scenario'],r['current_a'],'die',round(r['detector_k'],3),'K','V',round(r['terminal_voltage_v'],5),'P',round(r['terminal_power_w'],4),'W')
    print('accepted',len(rows),'failed',sum('status' in r for r in cases.values()))
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT/'outputs/integrated-reference-20261030'))
    ap.add_argument('--material',choices=('g1_constant','zhang2025_analog','zhang2025_nonlinear'),default='g1_constant')
    ap.add_argument('--exchange',type=Path,help='Optional corrected stepped-core operator JSON')
    args=ap.parse_args()
    if args.exchange:
        from .corrected_exchange import load
        operator=load(args.exchange)
    else:operator=None
    run(args.out,material_model=args.material,exchange=operator)
