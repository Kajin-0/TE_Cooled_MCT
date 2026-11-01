"""Publication projection of completed identifiability data; never runs physics."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from .history import ROOT,sha

DATA=ROOT/'data/tec_identifiability_20261101'


def generate(out,save):
    ledger=json.loads((DATA/'checksums.json').read_text())['artifact_sha256']
    for name,digest in ledger.items():
        if sha(DATA/name)!=digest:raise ValueError('Changed identifiability evidence: '+name)
    a=json.loads((DATA/'analysis.json').read_text());p=json.loads((DATA/'presentation.json').read_text())
    geo=json.loads((DATA/'geometry_audit.json').read_text());tex=[]
    def macro(name,value):tex.append('\\newcommand{\\'+name+'}{'+str(value)+'}')
    rows=[]
    for g in (.8,1.,1.2,1.7):
        pair={r['field']:r for r in a['oem_rows'] if r['factor']==g and r['I']==.2 and r['Q']==0 and r['status']=='CONDITIONAL'}
        t=pair['delta_t_k'];v=pair['voltage_v']
        rows.append(f"{g:g} & {t['model_value']:.6f} & {v['model_value']:.6f} & {t['difference']:+.6f} & {v['difference']:+.6f}"+r' \\')
    macro('GeometryResidualRows','\n'.join(rows))
    rows=[]
    for step in ('0.005','0.0025'):
        b=a['jacobians']['300.15']['steps'][step]['raw'];s=b['singular_values']
        rows.append(f"{step} & {s[0]:.6f} & {s[1]:.6f} & {s[2]:.6f} & {s[3]*1e5:.5f} & {b['rank_relative_1e_5']}"+r' \\')
    macro('IdentifiabilitySVDRows','\n'.join(rows))
    target=next(r for r in p['target_samples'] if r['g']==1.7)['lowest_current_admitted_hit']
    macro('GeometryTargetDie',f"{target['Tdie_K']:.3f}");macro('GeometryTargetPower',f"{target['terminal_input_W']:.6f}")
    macro('GeometryFootCoverage',f"{geo[3]['minimum_footprint_coverage']*100:.4f}")
    macro('GeometryShortHeight',f"{geo[6]['repacked_stack_height_m_fixed_other_layers']*1000:.6f}")
    with plt.rc_context({'font.size':9,'legend.fontsize':7}):
        fig,axs=plt.subplots(1,2,figsize=(6.5,2.65),layout='constrained')
        for g,color in ((.8,'#b45b3f'),(1.,'#2266a3'),(1.2,'#7b69a6'),(1.7,'#2c866a')):
            for ax,field in zip(axs,('delta_t_k','voltage_v')):
                rows=sorted([r for r in a['oem_rows'] if r['factor']==g and r['Q']==0 and r['field']==field],key=lambda r:r['I'])
                ax.plot([r['I'] for r in rows],[r.get('model_value',np.nan) for r in rows],'o-',ms=3,color=color,label=f'$g={g:g}$')
        for ax,field,label in zip(axs,('delta_t_k','voltage_v'),('Cold-ceramic lift (K)','Module voltage (V)')):
            rows=sorted([r for r in a['oem_rows'] if r['factor']==1 and r['Q']==0 and r['field']==field and 'source_value' in r],key=lambda r:r['I'])
            ax.errorbar([r['I'] for r in rows],[r['source_value'] for r in rows],yerr=[r['reading_bound'] for r in rows],fmt='ks',ms=3,label='Published chart')
            ax.set(xlabel='Current (A)',ylabel=label);ax.grid(alpha=.2)
        axs[0].legend();save(fig,'geometry_material_comparison')
    (out/'identifiability_numerics.tex').write_text('\n'.join(tex)+'\n')
    return [DATA/n for n in ('registration.json','analysis.json','cases.json','presentation.json','geometry_audit.json','checksums.json','analysis_recovery.json','controls.json')]
