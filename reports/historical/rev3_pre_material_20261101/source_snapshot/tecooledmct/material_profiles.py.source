"""Opt-in source-traceable transport curves. No extrapolation or OEM-grade claim."""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np

DATA=Path(__file__).resolve().parents[1]/'data/g2c'

@dataclass(frozen=True)
class Curve:
    temperature_k: tuple
    values: tuple
    unit: str
    positive: bool=False

    def __post_init__(self):
        t,v=np.asarray(self.temperature_k),np.asarray(self.values)
        if len(t)<2 or len(t)!=len(v) or not np.isfinite([t,v]).all() or np.any(np.diff(t)<=0) or t[0]<=0:
            raise ValueError('Ordered finite absolute temperatures and equal-length data required')
        if self.unit not in ('V/K','ohm m','W/(m K)'):raise ValueError('Unrecognized SI unit')
        if self.positive and np.any(v<=0):raise ValueError('Positive transport property required')

    def evaluate(self,temperature):
        t=np.asarray(temperature,dtype=float)
        if not np.isfinite(t).all() or np.any(t<self.temperature_k[0]) or np.any(t>self.temperature_k[-1]):
            raise ValueError(f'Temperature outside measured [{self.temperature_k[0]}, {self.temperature_k[-1]}] K')
        return np.interp(t,self.temperature_k,self.values)

    def slope(self,temperature):
        self.evaluate(temperature)
        i=np.clip(np.searchsorted(self.temperature_k,temperature,side='right')-1,0,len(self.temperature_k)-2)
        return np.diff(self.values)[i]/np.diff(self.temperature_k)[i]

@dataclass(frozen=True)
class Profile:
    metadata: dict
    curves: dict

    def properties(self,polarity,temperature):
        c=self.curves[polarity]
        rho=c['rho'].evaluate(temperature)
        return {'k':c['k'].evaluate(temperature),'sigma':1/rho,'S':c['S'].evaluate(temperature),
                'rho':rho,'thomson_v_k':np.asarray(temperature)*c['S'].slope(temperature)}

    @property
    def interval(self):
        return (max(c.temperature_k[0] for cs in self.curves.values() for c in cs.values()),
                min(c.temperature_k[-1] for cs in self.curves.values() for c in cs.values()))


def load_profile(path=DATA/'zhang2025_he_v1.json'):
    m=json.loads(Path(path).read_text());curves={}
    if m['schema_version']!=1 or m['extrapolation_policy']!='reject':raise ValueError('Unsupported profile policy')
    for polarity in ('P','N'):
        s=m['specimens'][polarity]
        if not s['same_specimen_triple_properties']:raise ValueError('Mixed specimens cannot qualify a triple-property profile')
        curves[polarity]={}
        for name,unit in (('rho','ohm m'),('k','W/(m K)'),('S','V/K')):
            raw=s['curves'][name]
            if raw['unit']!=unit:raise ValueError('Source property units are not SI')
            curve=Curve(tuple(p['temperature_k'] for p in raw['points']),tuple(p['value_si'] for p in raw['points']),unit,name!='S')
            if name=='S' and not np.all(np.sign(curve.values)==(1 if polarity=='P' else -1)):raise ValueError('Invalid P/N thermopower sign')
            curves[polarity][name]=curve
    result=Profile(m,curves)
    if tuple(m['valid_temperature_k'])!=result.interval:raise ValueError('Declared coverage differs from complete property intersection')
    return result


def synthetic_profile(varying=True):
    """Function test only: G1 values at 300 K, documented invented slopes."""
    from .fem_g2a import PROPERTIES
    curves={}
    for p in ('P','N'):
        k,sigma,s=PROPERTIES[p][:3]
        curves[p]={'rho':Curve((200.,300.),((1/sigma)*(.85 if varying else 1),1/sigma),'ohm m',True),
                   'k':Curve((200.,300.),(k*(1.15 if varying else 1),k),'W/(m K)',True),
                   'S':Curve((200.,300.),(s*(.8 if varying else 1),s),'V/K')}
    return Profile({'id':'synthetic_variable_test' if varying else 'g1_constant_regression',
        'status':'SYNTHETIC FUNCTION TEST ONLY','oem_grade_matched':False,'valid_temperature_k':[200,300]},curves)
