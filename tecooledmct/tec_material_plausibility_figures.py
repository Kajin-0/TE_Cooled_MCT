"""Evidence-derived material, operating-grid and conditional datasheet panels."""
import argparse
import csv
from pathlib import Path

import numpy as np

from .tec_material_plausibility import ROOT,read,write,sha,HYPOTHESES,CURRENTS,material_properties
from .integrated_reference import geometry


def analyze(folder):
    reg=read(folder/'registration.json');results=read(folder/'cases.json');oem=read(folder/'oem_comparison.json')
    accepted=[dict(r['summary'],label=c['label']) for c in reg['cases'] if (r:=results[c['id']])['status']=='ACCEPTED']
    base=next(r for r in accepted if r['group']=='core' and r['hypothesis']=='nominal' and not r['wires_ON'] and r['current_A']==.25)
    pairs={'S':('S_0.9','S_1.1'),'rho':('rho_0.8','rho_1.2'),'k':('k_0.8','k_1.2'),
           'hot_K':('hot_290.0','hot_310.0'),'load_W':('load_0.0','load_0.005'),'attach_k':('attach_0.5','attach_3.0')}
    oat=[]
    for name,labels in pairs.items():
        points=[next((r for r in accepted if r['group']=='OAT' and r['label']==label),None) for label in labels]
        oat.append({'factor':name,'case_ids':[r['id'] if r else None for r in points],
             'low_Tdie_K':points[0]['Tdie_K'] if points[0] else None,'high_Tdie_K':points[1]['Tdie_K'] if points[1] else None,
             'endpoint_span_K':abs(points[1]['Tdie_K']-points[0]['Tdie_K']) if all(points) else None})
    oat.sort(key=lambda r:-(r['endpoint_span_K'] if r['endpoint_span_K'] is not None else -1))
    wire=next(r for r in accepted if r['group']=='core' and r['hypothesis']=='nominal' and r['wires_ON'] and r['current_A']==.25)
    matched=[r for r in oem['rows'] if r['status'].startswith('CONDITIONAL')]
    sets={h:{r['source_id'] for r in matched if r['hypothesis']==h} for h in HYPOTHESES};common=set.intersection(*sets.values())
    metrics=[]
    for scope in ('all_admitted','common_admitted'):
        for h in HYPOTHESES:
            for field in ('delta_t_k','voltage_v'):
                rows=[r for r in matched if r['hypothesis']==h and r['field']==field and (scope=='all_admitted' or r['source_id'] in common)]
                metrics.append({'scope':scope,'hypothesis':h,'field':field,'count':len(rows),
                     'mean_signed_difference':float(np.mean([r['signed_difference'] for r in rows])) if rows else None,
                     'MAE':float(np.mean([r['absolute_difference'] for r in rows])) if rows else None,
                     'max_abs':max((r['absolute_difference'] for r in rows),default=None),
                     'mean_abs_relative':float(np.mean([r['absolute_relative_difference'] for r in rows])) if rows else None})
    hot_offsets=[]
    for reference in [r for r in accepted if r['group']=='OEM_300K_reference']:
        literal=next((r for r in accepted if r['group']=='OEM_literal' and r['hypothesis']=='nominal' and r['die_load_W']==0. and r['current_A']==reference['current_A']),None)
        if literal:hot_offsets.append({'current_A':reference['current_A'],'literal_minus_300K_lift_K':literal['cold_lift_K']-reference['cold_lift_K'],
                                       'literal_minus_300K_voltage_V':literal['module_voltage_V']-reference['module_voltage_V']})
    g=geometry();isothermal={}
    for h,scales in HYPOTHESES.items():
        pn={p:material_properties(p,np.array([200.,300.]),scales) for p in ('P','N')}
        rho_sum=pn['P']['rho']+pn['N']['rho'];alpha=pn['P']['S']-pn['N']['S'];k_sum=pn['P']['k']+pn['N']['k']
        isothermal[h]={'temperature_K':[200.,300.],'R_PN_ohm':rho_sum*sum(s['couples']*s['leg_length_m']/s['leg_area_m2'] for s in g['stages']),
                       'couple_ZT':alpha**2*np.array([200.,300.])/(rho_sum*k_sum)}
    report={'OAT_baseline':base,'one_factor_endpoint_rankings':oat,'isothermal_PN_reference':isothermal,
            'wire_ON_minus_OFF_at_nominal_025A_K':wire['Tdie_K']-base['Tdie_K'],
            'OEM_error_metrics':metrics,'OEM_common_admitted_scalar_points':len(common),
            'hot_reference_offset_effect':hot_offsets,
            'source_domain_counts':{'accepted_nonlinear':sum(r['group']!='G1_control' for r in accepted),
                'measured_domain_only':sum(r['all_legs_within_measured_domain'] is True for r in accepted),
                'assumed_continuation':sum(r['assumed_continuation_used'] for r in accepted)},
            'max_global_residual_W':max(abs(r['result']['global_energy_residual_w']) for r in results.values() if r['status']=='ACCEPTED'),
            'max_stage_residual_W':max(abs(s['energy_residual_w']) for r in results.values() if r['status']=='ACCEPTED' for s in r['result']['stage_budget']),
            'interpretation':'Engineering conditional sensitivities; unequal admitted coverage is not a fair grade ranking; common-point metrics are descriptive, no fit'}
    write(folder/'analysis.json',report)
    # Human-readable scalar table; structured per-stage arrays remain in JSON.
    with (folder/'accepted_sweep.csv').open('w',newline='') as f:
        fields=['id','group','hypothesis','current_A','hot_K','die_load_W','wires_ON','Tdie_K','Tcold_ceramic_K','cold_lift_K','Qc_cold_W','module_voltage_V','terminal_voltage_V','module_input_W','terminal_input_W','cooler_COP','die_COP','assumed_continuation_used']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in accepted:w.writerow({k:r[k] for k in fields})
    return reg,results,oem,report


def run(folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder=Path(folder).resolve()
    if (folder/'figure_provenance.json').exists():raise ValueError('Do not overwrite figure evidence')
    reg,results,oem,analysis=analyze(folder);colors={'nominal':'#2266a3','lower':'#b45b3f','higher':'#2c866a'}
    images=[]
    fig,axes=plt.subplots(2,2,figsize=(11.5,7.4));t=np.linspace(180,390,421)
    for h,scales in HYPOTHESES.items():
        p=material_properties('P',t,scales);n=material_properties('N',t,scales)
        data=[(p['S']*1e6,n['S']*1e6),(p['rho']*1e6,n['rho']*1e6),(p['k'],n['k']),((p['S']-n['S'])**2*t/((p['rho']+n['rho'])*(p['k']+n['k'])),None)]
        for ax,(pp,nn) in zip(axes.ravel(),data):
            ax.plot(t,pp,color=colors[h],label=h+' hypothesis')
            if nn is not None:ax.plot(t,nn,color=colors[h],ls='--',lw=1.1)
    for ax,y in zip(axes.ravel(),['S (µV/K): P solid, N dashed','ρ (µΩ m): P solid, N dashed','k (W/(m K)): P solid, N dashed','Equal-area couple ZT (dimensionless)']):
        ax.axvspan(300,390,color='.7',alpha=.25);ax.axvline(300,color='.4',lw=.8);ax.set(xlabel='Temperature (K)',ylabel=y);ax.grid(alpha=.2)
    axes[1,1].legend(fontsize=9);fig.suptitle('Dissimilar Zhang specimens and scaled engineering hypotheses — not measured module grades')
    fig.text(.05,.015,'180–300 K source interpolation; shaded 300–390 K is the ASSUMED quarter-tangent continuation. No grade fitting.',fontsize=9)
    fig.tight_layout(rect=(0,.045,1,.95));name='transport_hypotheses.png';fig.savefig(folder/name,dpi=220);plt.close(fig);images.append(name)
    fig,axes=plt.subplots(1,2,figsize=(12,5.1))
    for h in HYPOTHESES:
        for wire in (False,True):
            rows=[]
            for I in CURRENTS:
                c=next(c for c in reg['cases'] if c['group']=='core' and c['hypothesis']==h and c['wires_ON']==wire and c['current_A']==I)
                r=results[c['id']];rows.append(r['summary'] if r['status']=='ACCEPTED' else None)
            for ax,key in zip(axes,('Tdie_K','module_voltage_V')):
                ax.plot(CURRENTS,[r[key] if r else np.nan for r in rows],color=colors[h],ls='--' if wire else '-',marker='o' if wire else '.',ms=4,label=h+(' / wires ON' if wire else ' / wires OFF'))
    g1=[results[c['id']]['summary'] for c in reg['cases'] if c['group']=='G1_control' and results[c['id']]['status']=='ACCEPTED']
    axes[0].plot([r['current_A'] for r in g1],[r['Tdie_K'] for r in g1],color='.5',ls=':',label='G1 constant / OFF')
    axes[0].axhline(200,color='.3',lw=.8);axes[0].set(ylabel='Reduced die temperature (K)');axes[1].set(ylabel='Module voltage (V)')
    for ax in axes:ax.set(xlabel='Current (A)');ax.grid(alpha=.2)
    axes[0].legend(fontsize=8);fig.suptitle('Fixed hot ceramic 300 K, die load 2 mW; gas and radiation OFF')
    fig.text(.04,.015,'Gaps are rejected cases, never interpolated. Conditional reduced estimates; no actual assembly feasibility or global optimum is claimed.',fontsize=8.5)
    fig.tight_layout(rect=(0,.045,1,.94));name='operating_grid.png';fig.savefig(folder/name,dpi=220);plt.close(fig);images.append(name)
    source=read(ROOT/'data/g2c/oem2019_curves_v1.json');fig,axes=plt.subplots(2,2,figsize=(11.5,7.2))
    for ir,load in enumerate((0.,.1)):
        for ic,field in enumerate(('delta_t_k','voltage_v')):
            ax=axes[ir,ic];points=sorted([p for p in source['points'] if p['panel']=='300K_vacuum' and p['load_w']==load and p['field']==field],key=lambda p:p['current_a'])
            ax.errorbar([p['current_a'] for p in points],[p['value'] for p in points],xerr=[p['current_reading_bound_a'] for p in points],yerr=[p['value_reading_bound'] for p in points],fmt='ks',ms=3,capsize=2,label='Published chart readings')
            for h in HYPOTHESES:
                rows=[next(r for r in oem['rows'] if r['source_id']==p['id'] and r['hypothesis']==h) for p in points]
                ax.plot([p['current_a'] for p in points],[r.get('model_value',np.nan) for r in rows],color=colors[h],marker='.',label=h+' hypothesis')
            ax.set(xlabel='Current (A)',ylabel='Cold-ceramic lift (K)' if ic==0 else 'Module voltage (V)',title=f'Qc={load:g} W; literal hot side 300.15 K');ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=8);fig.suptitle('Conditional idealized vacuum module boundaries — not OEM validation')
    fig.text(.04,.015,'All model points require assumed >300 K continuation. Reading bars are digitization bounds, not measurement uncertainty; prior splits already examined.',fontsize=8)
    fig.tight_layout(rect=(0,.045,1,.95));name='datasheet_plausibility.png';fig.savefig(folder/name,dpi=220);plt.close(fig);images.append(name)
    write(folder/'figure_provenance.json',{'source_sha256':sha(__file__),
        'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (folder/'registration.json',folder/'cases.json',folder/'oem_comparison.json',ROOT/'data/g2c/oem2019_curves_v1.json')},
        'figures':{n:sha(folder/n) for n in images},'data_scope':'Actual admitted reduced scenarios and original digitized charts; no FEM fields or invented observations'})
    return analysis


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);args=p.parse_args();run(args.data)
