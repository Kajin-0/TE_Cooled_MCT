"""Professional V3.6 engineering plots from frozen, independently audited full solves.
No interpolation or manufactured error bars; connecting lines only guide reading.
"""
from pathlib import Path
import hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
CASE=ROOT/'data/v3_6_operating_envelope_20261109'
FIG=Path(__file__).resolve().parent/'figures'
CURRENT=['I025_Q002_corrected','I040_Q002','I055_Q002_corrected','I060_Q002_corrected']
LOAD=['I040_Q001','I040_Q002','I040_Q006']

def get(name):
    p=CASE/name
    reg=json.loads((p/'registration.json').read_text())
    data=json.loads((p/'result.json').read_text())
    audit=json.loads((p/'independent_energy_audit.json').read_text())
    assert audit['verdict'].startswith('PASS V3.6'),name
    assert audit['result_sha256']==hashlib.sha256((p/'result.json').read_bytes()).hexdigest(),name
    assert data['max_full_stage_conservation_residual_W']<1e-8,name
    assert data['max_last_spatial_temperature_update_K']<3e-7,name
    assert abs(audit['global_energy_residual_W'])<1e-8,name
    assert data['operating_current_A']==reg['current_A']
    assert data['detector_imposed_heat_W']==reg['detector_heat_W']
    return reg,data,audit

def fsave(fig,key):
    for ext in ('pdf','png'):
        p=FIG/f'{key}.{ext}'
        if ext=='pdf':fig.savefig(p,bbox_inches='tight',metadata={'Creator':'TEC HgCdTe physical engineering V3.6','CreationDate':None,'ModDate':None})
        else:fig.savefig(p,dpi=210,bbox_inches='tight')
        print(p.relative_to(ROOT),p.stat().st_size)
    plt.close(fig)

def plot():
    vals=[get(n) for n in CURRENT]
    currents=np.array([r['current_A'] for r,d,a in vals])
    temperature=np.array([d['calculated_detector_temperature_K'] for r,d,a in vals])
    voltage=np.array([d['terminal_voltage_V'] for r,d,a in vals])
    power=np.array([d['electrical_power_W'] for r,d,a in vals])
    assert all(np.diff(currents)>0) and len(vals)==4
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.1,'pdf.fonttype':42,
         'axes.spines.top':False,'axes.spines.right':False,
         'axes.titlesize':11,'axes.titleweight':'bold'})
    fig=plt.figure(figsize=(10.8,5.2),facecolor='white')
    l=fig.add_axes([.075,.22,.395,.62])
    r=fig.add_axes([.585,.22,.36,.62])
    l.plot(currents,temperature,'o-',lw=1.9,ms=6.4,color='#326480')
    l.set_xlim(.21,.63);l.set_ylim(min(temperature)-4,max(temperature)+5)
    l.set_xticks(currents)
    l.set_xlabel('TEC drive current (A)')
    l.set_ylabel('Calculated HgCdTe temperature (K)')
    l.grid(axis='y',color='#dfe6eb',lw=.7)
    l.set_title('Detector cooling',loc='left')
    for x,y in zip(currents,temperature):
        l.annotate(f'{y:.2f} K',(x,y),xytext=(0,11),textcoords='offset points',ha='center',fontsize=8.9,color='#2d485e')
    r.plot(currents,power,'o-',lw=1.9,ms=6.4,color='#b16d44')
    r.set_xlim(.21,.63);r.set_ylim(0,max(power)*1.15)
    r.set_xticks(currents)
    r.set_xlabel('TEC drive current (A)')
    r.set_ylabel('Electrical input (W)')
    r.grid(axis='y',color='#dfe6eb',lw=.7)
    r.set_title('Electrical power cost',loc='left')
    for x,y in zip(currents,power):
        r.annotate(f'{y:.3f} W',(x,y),xytext=(0,11),textcoords='offset points',ha='center',fontsize=8.9,color='#794a30')
    fig.text(.072,.945,'TEC operating envelope: cooling versus electrical input',
             fontsize=15.5,fontweight='bold',color='#233a50')
    fig.text(.074,.896,'300 K sink  |  2.00 mW imposed detector heat  |  100 Pa krypton  |  unchanged V3.5 physical laws',
             fontsize=9.7,color='#526779')
    fig.text(.075,.083,'Four individually converged synthetic full-system cases; line segments guide the eye. Not a fitted optimum or measured response.',
             fontsize=8.8,color='#60758a')
    fsave(fig,'v36_current_temperature_power')
    vals=[get(n) for n in LOAD]
    Q=np.array([r['detector_heat_W']*1e3 for r,d,a in vals])
    T=np.array([d['calculated_detector_temperature_K'] for r,d,a in vals])
    V=np.array([d['terminal_voltage_V'] for r,d,a in vals])
    assert list(Q)==[1.,2.,6.]
    sensitivity=float((T[-1]-T[0])/(Q[-1]-Q[0]))
    fig=plt.figure(figsize=(8.6,4.45),facecolor='white')
    ax=fig.add_axes([.105,.25,.76,.56])
    ax.plot(Q,T,'o-',color='#326480',lw=2.,ms=7)
    ax.set_xlim(0.5,6.8)
    ax.set_ylim(min(T)-.32,max(T)+.44)
    ax.set_xticks(Q)
    ax.set_xlabel('Applied detector thermal load (mW)')
    ax.set_ylabel('Calculated HgCdTe temperature (K)')
    ax.set_title('Response to detector heat loading',loc='left')
    ax.grid(axis='y',color='#dfe6eb')
    for x,y in zip(Q,T):
        ax.annotate(f'{y:.3f} K',(x,y),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9.0,color='#2a4b64')
    fig.text(.083,.95,'Thermal load sensitivity at fixed 0.400 A',fontweight='bold',fontsize=15.1,color='#253c50')
    fig.text(.085,.89,'300 K sink  |  100 Pa krypton  |  no device electrical or optical response fitted',fontsize=9.1,color='#516477')
    fig.text(.105,.115,f'Secant response across 1–6 mW: {sensitivity:.3f} K/mW ({sensitivity*1e3:.0f} K/W).',
             fontsize=10.5,fontweight='bold',color='#2a4d64')
    fig.text(.105,.075,'Three independently converged synthetic cases; source detector heating is externally specified, not HgCdTe self-heating.',
             fontsize=8.7,color='#64788a')
    fsave(fig,'v36_detector_heat_load_response')
    summary={
       'description':'V3.6 independently accepted operating-envelope scenarios; two corrected-source warm starts at nonreference current',
       'reference':{'I_A':.4,'Qdet_mW':2.0},
       'current_cases':[],
       'load_cases':[],
       'detector_heat_load_secant_K_per_mW':sensitivity,
       'original_V35_model_unchanged':True}
    for name in CURRENT:
        reg,d,a=get(name)
        summary['current_cases'].append({
           'name':name,'current_A':reg['current_A'],'detector_heat_mW':reg['detector_heat_W']*1000,
           'detector_temperature_K':d['calculated_detector_temperature_K'],
           'TEC_voltage_V':d['terminal_voltage_V'],'TEC_input_W':d['electrical_power_W'],
           'bath_Q_W':d['bath_heat_rejected_W'],
           'maximum_independent_stage_balance_W':a['max_stage_energy_residual_W'],
           'result_SHA256':a['result_sha256'],'solver_SHA256':d['solver_source_sha256']})
    for name in LOAD:
        reg,d,a=get(name)
        summary['load_cases'].append({'name':name,'current_A':reg['current_A'],
          'detector_heat_mW':reg['detector_heat_W']*1000,
          'detector_temperature_K':d['calculated_detector_temperature_K'],
          'TEC_voltage_V':d['terminal_voltage_V'],
          'TEC_input_W':d['electrical_power_W'],
          'result_SHA256':a['result_sha256'],'solver_SHA256':d['solver_source_sha256']})
    (CASE/'accepted_envelope_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Completed accepted summary; current T:',temperature.tolist(),'power',power.tolist())
if __name__=='__main__':plot()
