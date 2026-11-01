"""Report-only projection of frozen material scenarios: no transport/physics calls."""
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/tec_material_plausibility_20261101'
COLORS={'nominal':'#2266a3','lower':'#b45b3f','higher':'#2c866a'}


def evidence():
    """Check frozen scientific bytes before deriving any report quantity."""
    from .history import sha
    ledger=json.loads((DATA/'checksums.json').read_text())['artifact_sha256']
    for name,digest in ledger.items():
        if sha(DATA/name)!=digest:raise ValueError('Changed screening evidence: '+name)
    names=('registration','cases','summary','analysis','properties','oem_comparison',
           'figure_provenance','transport_verification')
    d={name:json.loads((DATA/(name+'.json')).read_text()) for name in names}
    for name,digest in d['figure_provenance']['input_sha256'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Changed screening source: '+name)
    return d


def generate(out,save):
    """Regenerate two professional panels and typeset tables from saved JSON only."""
    d=evidence();reg=d['registration'];cases=d['cases'];summary=d['summary'];a=d['analysis']
    oem=d['oem_comparison'];tex=[]
    def macro(name,value):tex.append('\\newcommand{\\'+name+'}{'+str(value)+'}')
    gas_path=ROOT/'data/isolated_cap_native_gas_20261101/phase_C/result.json'
    gas=json.loads(gas_path.read_text())
    if gas['registered_numerical_gates_passed'] or gas['physical_device_validation']:
        raise ValueError('Original standalone gas failure must remain explicit')
    macro('GasRawMismatch',f"{gas['raw_global_relative_mismatch']*100:.4f}")
    labels={'nominal':'Nominal','lower':'Lower','higher':'Higher'}
    rows=[]
    for h in COLORS:
        p=d['properties']['hypotheses'][h];scales=p['scales_S_rho_k']
        z=a['isothermal_PN_reference'][h]['couple_ZT']
        rows.append(f"{labels[h]} & ({scales[0]:g}, {scales[1]:g}, {scales[2]:g}) & {z[0]:.3f} / {z[1]:.3f}"+r' \\')
    macro('HypothesisRows','\n'.join(rows))
    rows=[];selected={}
    for h in COLORS:
        c=summary['targets'][h+'_wires_ON']['minimum_accepted_sample'];selected[h]=c['id']
        rows.append(f"{labels[h]} & {c['current_A']:g} & {c['Tdie_K']:.3f} & {c['terminal_voltage_V']:.6f} & {c['terminal_input_W']:.6f} & {c['Qc_cold_W']*1000:.6f}"+r' \\')
    macro('MaterialOperatingRows','\n'.join(rows))
    nominal=summary['targets']['nominal_wires_ON']['minimum_accepted_sample']
    for name,key,fmt in [('ScreenDie','Tdie_K','.3f'),('ScreenVoltage','terminal_voltage_V','.6f'),
                         ('ScreenPower','terminal_input_W','.6f'),('ScreenCOP','die_COP','.6f')]:
        macro(name,format(nominal[key],fmt))
    macro('ScreenQc',f"{nominal['Qc_cold_W']*1000:.6f}")
    coverage=[('Material and wire grid','core'),('Constant-property controls','G1_control'),
              ('Hot-side/load controls','hot_load'),('One-factor endpoints','OAT'),
              ('Literal manufacturer conditions','OEM_literal'),('300 K reference controls','OEM_300K_reference'),
              ('Attach invariance','attach_invariance')]
    macro('CoverageRows','\n'.join(f"{label} & {summary['counts'][key]['ACCEPTED']} & {summary['counts'][key]['REJECTED']}"+r' \\' for label,key in coverage))
    names={'k':r'$k$ scale 0.8--1.2','S':r'$S$ scale 0.9--1.1',
           'hot_K':r'Hot ceramic 290--310 K','rho':r'$\rho$ scale 0.8--1.2',
           'load_W':r'Die heat 0--5 mW','attach_k':r'Attach $k$ 0.5--3 W/(m K)'}
    macro('ScreenSensitivityRows','\n'.join(names[r['factor']]+f" & {r['endpoint_span_K']:.6f}"+r' \\' for r in a['one_factor_endpoint_rankings']))
    macro('ScreenBaselineDie',f"{a['OAT_baseline']['Tdie_K']:.6f}")
    comparisons=[r for r in oem['rows'] if r['hypothesis']=='nominal' and r['Qc_W']==0
                 and r['current_A']==.2 and r['status']=='CONDITIONAL BOUNDARY-MATCHED PLAUSIBILITY']
    if {r['field'] for r in comparisons}!={'delta_t_k','voltage_v'} or len(comparisons)!=2:
        raise ValueError('Expected exactly two admitted literal-vacuum comparison scalars')
    macro('ManufacturerRows','\n'.join(
        (r'Cold-ceramic lift (K)' if r['field']=='delta_t_k' else 'Module voltage (V)')+
        f" & {r['model_value']:.6f} & {r['source_value']:.6f} & {r['signed_difference']:+.6f} & {r['signed_relative_difference']*100:+.2f}"+r' \\'
        for r in comparisons))
    common=[r for r in a['OEM_error_metrics'] if r['scope']=='common_admitted' and r['hypothesis']=='nominal']
    for r in common:macro('LiftMAE' if r['field']=='delta_t_k' else 'VoltageMAE',f"{r['MAE']:.6f}")
    # Plot exact registered currents; rejected points remain NaN gaps.
    currents=sorted({c['current_A'] for c in reg['cases'] if c['group']=='core'})
    with plt.rc_context({'font.size':9,'axes.labelsize':9,'legend.fontsize':7}):
        fig,axs=plt.subplots(1,2,figsize=(6.5,2.95),layout='constrained')
        for h,color in COLORS.items():
            for wires in (False,True):
                samples=[]
                for current in currents:
                    c=next(c for c in reg['cases'] if c['group']=='core' and c['hypothesis']==h and c['wires_ON']==wires and c['current_A']==current)
                    r=cases[c['id']];samples.append(r['summary'] if r['status']=='ACCEPTED' else None)
                for ax,key in zip(axs,('Tdie_K','module_voltage_V')):
                    ax.plot(currents,[r[key] if r else np.nan for r in samples],color=color,
                            ls='--' if wires else '-',marker='o' if wires else '.',ms=3,
                            label=labels[h]+(' / ON' if wires else ' / OFF'))
        control=[cases[c['id']]['summary'] for c in reg['cases'] if c['group']=='G1_control' and cases[c['id']]['status']=='ACCEPTED']
        axs[0].plot([r['current_A'] for r in control],[r['Tdie_K'] for r in control],':',color='.45',label='Constant / OFF')
        axs[0].axhline(200,color='.5',lw=.7);axs[0].set(ylabel='Die temperature (K)');axs[0].legend(loc='upper right')
        axs[1].set(ylabel='Module voltage (V)')
        for ax in axs:ax.set(xlabel='Current (A)');ax.grid(alpha=.2)
        save(fig,'material_operating_grid')
        source=json.loads((ROOT/'data/g2c/oem2019_curves_v1.json').read_text())
        fig,axs=plt.subplots(2,2,figsize=(6.5,4.35),layout='constrained')
        for ir,load in enumerate((0.,.1)):
            for ic,field in enumerate(('delta_t_k','voltage_v')):
                ax=axs[ir,ic]
                points=sorted([p for p in source['points'] if p['panel']=='300K_vacuum' and p['load_w']==load and p['field']==field],key=lambda p:p['current_a'])
                ax.errorbar([p['current_a'] for p in points],[p['value'] for p in points],
                    xerr=[p['current_reading_bound_a'] for p in points],yerr=[p['value_reading_bound'] for p in points],
                    fmt='ks',ms=3,capsize=2,label='Published chart')
                for h,color in COLORS.items():
                    rows=[next(r for r in oem['rows'] if r['source_id']==p['id'] and r['hypothesis']==h) for p in points]
                    ax.plot([p['current_a'] for p in points],[r.get('model_value',np.nan) for r in rows],color=color,marker='.',label=labels[h])
                ax.set(xlabel='Current (A)',ylabel='Cold-ceramic lift (K)' if ic==0 else 'Module voltage (V)',title=f'$Q_c={load:g}$ W');ax.grid(alpha=.2)
        axs[0,0].legend();save(fig,'manufacturer_plausibility')
    (out/'screening_numerics.tex').write_text('\n'.join(tex)+'\n')
    record={'scope':'Report-only projection of frozen reduced data; no solver or property-law calls',
        'selected_case_ids':selected,'cases':summary['cases'],'accepted':summary['accepted'],'rejected':summary['rejected'],
        'source_domain_counts':a['source_domain_counts'],'new_physics_runs':0,'no_parameter_fit':True,
        'manufacturer_assumed_continuation_required':True,'actual_device_feasibility':'unresolved',
        'frozen_scientific_checksums':json.loads((DATA/'checksums.json').read_text())}
    (out/'material_screening.json').write_text(json.dumps(record,indent=2)+'\n')
    return [DATA/(name+'.json') for name in (*d.keys(),'checksums')]+[ROOT/'data/g2c/oem2019_curves_v1.json',gas_path]
