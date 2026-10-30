"""Preliminary corrected-source gray radiation / gas chord-network operator.

Visibility is solved in a closed STEPPED-CORE PROXY, not between every native
88-leg face. Gas uses geometric chords as a conservative engineering network,
not a diffusion/CFD or validated rarefied-gas solution. All units are SI.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from .exchange_geometry import specification,surfaces,emit,first_hit,verify_sources
from .fem_g3b_exchange import (balanced_view_factors,radiation_matrix,gas_properties,
                              gas_power,GASES)

NODES=('hot_ceramic','stage1','stage2','cold_ceramic','MCT_die','header','cap','window')


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate(data):
    a=np.asarray([s['area_m2'] for s in data['surfaces']]);f=np.asarray(data['view_factors'])
    distances=np.asarray(data['chord_distance_m']);mapping=np.asarray([s['weights'] for s in data['surfaces']])
    if (f.shape!=(len(a),len(a)) or distances.shape!=f.shape or mapping.shape!=(len(a),8)
            or not np.isfinite([f,distances]).all() or not np.isfinite(a).all()
            or np.any(a<=0) or np.any(f<0) or np.any(distances<0)
            or not np.allclose(f.sum(axis=1),1,rtol=0,atol=2e-10)
            or not np.allclose(a[:,None]*f,(a[:,None]*f).T,rtol=1e-10,atol=1e-16)
            or not np.allclose(distances,distances.T,rtol=0,atol=1e-14)
            or np.any((f>0)&(distances<=0))
            or not np.isfinite(mapping).all() or np.any(mapping<0)
            or not np.allclose(mapping.sum(axis=1),1,rtol=0,atol=1e-14)):
        raise ValueError('Invalid corrected exchange operator')
    upward=[0,2,4,6,8,10]
    if (np.any(f[np.ix_(upward,upward)]>1e-14)
            or np.any(f[np.ix_([12,13],[12,13])]>1e-14)
            or any(f[i,i]>1e-14 for i in range(len(a)) if i!=11)):
        raise ValueError('Analytically blocked proxy view restored')
    return data


def build(rays=1024,seed=20261030):
    if not isinstance(rays,int) or rays<128 or rays&(rays-1):
        raise ValueError('Use a power-of-two ray count >=128 per surface')
    spec=specification();ss=surfaces(spec);n=len(ss)
    a=np.array([s['area_m2'] for s in ss]);counts=np.zeros((n,n));lengths=np.zeros_like(counts)
    for i,s in enumerate(ss):
        start,direction=emit(s,spec,rays,seed+i)
        target,distance=first_hit(start,direction,spec)
        counts[i]=np.bincount(target,minlength=n)
        lengths[i]=np.bincount(target,weights=distance,minlength=n)
    raw_f=counts/rays;raw_direct=a[:,None]*raw_f
    raw=.5*(raw_direct+raw_direct.T)
    f,correction=balanced_view_factors(raw,a)
    weighted_length=a[:,None]*lengths/rays
    dist=np.divide(weighted_length+weighted_length.T,2*raw,out=np.zeros_like(raw),where=raw>0)
    result={'schema':'corrected-stepped-cavity-exchange-v1','specification':spec,
        'surfaces':ss,'node_order':list(NODES),'view_factors':f.tolist(),
        'raw_view_factors':raw_f.tolist(),'chord_distance_m':dist.tolist(),
        'ray_audit':{'rays_per_surface':rays,'seed':seed,'unclosed_rays':0,
            'raw_row_closure_error':float(abs(raw_f.sum(axis=1)-1).max()),
            'raw_reciprocity_max_m2':float(abs(raw_direct-raw_direct.T).max()),
            'max_absolute_view_factor_correction':float(abs(f-raw_f).max()),
            'balancing':correction,'blocked_or_unsampled_pairs_not_restored':True},
        'scope':'PRELIMINARY reduced operator; corrected cap + stepped filled-core proxy, no full-native-face visibility, gas CFD, optical transmission or 3D thermal field',
        'gas_model':'NIST-registered N2/Ar/Kr k(T) 200..400K, explicit T^0.75 engineering extension 180..200K; Eucken jump closure, line-of-sight chord network; model-form accuracy unqualified'}
    validate(result)
    result['payload_sha256']=fingerprint(result)
    return result


def load(path):
    result=json.loads(Path(path).read_text());expected=result.pop('payload_sha256')
    if fingerprint(result)!=expected:raise ValueError('Exchange payload checksum mismatch')
    result['payload_sha256']=expected
    if result['specification']['source_sha256']!=verify_sources():
        raise ValueError('Exchange geometry source identity mismatch')
    return validate(result)


def evaluate(data,temperatures,*,pressure_pa=30000.,gas='Kr',accommodation=.8,
             cap_emissivity=.2,window_emissivity=.1,body_emissivity=.8,gas_scale=1.):
    validate(data)
    t=np.asarray(temperatures,dtype=float)
    if t.shape!=(8,) or not np.isfinite(t).all() or np.any(t<=0):raise ValueError('Eight finite positive temperatures')
    if (gas not in GASES or not np.isfinite((pressure_pa,accommodation,gas_scale)).all()
            or pressure_pa<0 or not 0<accommodation<=1 or gas_scale<0):
        raise ValueError('Invalid gas scenario')
    emissivity=np.array([body_emissivity]*10+[cap_emissivity]*3+[window_emissivity])
    if not np.isfinite(emissivity).all() or np.any(emissivity<0) or np.any(emissivity>1):
        raise ValueError('Invalid emissivity')
    a=np.array([s['area_m2'] for s in data['surfaces']]);f=np.array(data['view_factors'])
    mapping=np.array([s['weights'] for s in data['surfaces']]);ts=mapping@t
    radiation_into=-(radiation_matrix(a,f,emissivity)@(ts**4))
    conductance=np.zeros_like(f)
    sub200=False
    if pressure_pa and gas_scale:
        mean=.5*(ts[:,None]+ts[None,:])
        if np.any(mean<180) or np.any(mean>400):raise ValueError('Gas scenario outside180..400K')
        p=gas_properties(gas,np.maximum(mean,200.),pressure_pa)
        factor=np.where(mean<200.,(mean/200.)**.75,1.)
        p['k']=p['k']*factor
        p['mu']=p['k']/(p['cp']+1.25*p['R'])
        p['lambda_m']=p['mu']/pressure_pa*np.sqrt(np.pi*p['R']*mean/2)
        sub200=bool(np.any((mean<200)&(f>0)))
        jump=(2-accommodation)/accommodation*2*p['gamma']/(p['gamma']+1)*p['lambda_m']/p['Pr']
        w=a[:,None]*f;distance=np.array(data['chord_distance_m'])
        conductance=np.divide(p['k']*w*gas_scale,distance+2*jump,
            out=np.zeros_like(w),where=w>0)
        np.fill_diagonal(conductance,0)
        if not np.allclose(conductance,conductance.T,rtol=1e-10,atol=1e-14):
            raise ValueError('Gas reciprocity failed')
    gas_into=gas_power(conductance,ts)
    radiation_nodes=mapping.T@radiation_into;gas_nodes=mapping.T@gas_into
    balance=max(abs(radiation_into.sum()),abs(gas_into.sum()),abs(radiation_nodes.sum()),abs(gas_nodes.sum()))
    if balance>1e-10:raise ValueError('Exchange heat balance failure')
    return {'radiation_nodes_w':radiation_nodes.tolist(),'gas_nodes_w':gas_nodes.tolist(),
        'radiation_surfaces_w':radiation_into.tolist(),'gas_surfaces_w':gas_into.tolist(),
        'surface_temperatures_k':ts.tolist(),'max_conservation_residual_w':float(balance),
        'gas_sub200_assumption_used':sub200,
        'gas_conductance_w_k':conductance.tolist(),'node_order':list(NODES)}


def study(out):
    out=Path(out)
    if out.exists():raise ValueError('Choose a new exchange output directory')
    out.mkdir(parents=True)
    rows=[];temperature=[300.,270.,240.,220.,221.,300.,300.,300.]
    for rays in (4096,16384,65536):
        data=build(rays);result=evaluate(data,temperature)
        (out/('operator_'+str(rays)+'.json')).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
        rows.append({'rays':rays,'ray_audit':data['ray_audit'],'fixed_temperatures_k':temperature,
                     'exchange':result})
    summary={'scope':'Conservative proxy operator refinement, not full native-cavity accuracy.',
             'rows':rows,'pressure_sweep':[]}
    for pressure in (0.,1.,100.,30000.,101325.):
        summary['pressure_sweep'].append({'pressure_pa':pressure,**evaluate(data,temperature,pressure_pa=pressure)})
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print('Completed corrected proxy exchange audit and three bounded ray levels',flush=True)
    return data


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();study(args.out)
