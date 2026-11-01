"""Publication projection of registered finite-sink data; no physical solves."""
import json
import numpy as np
import matplotlib.pyplot as plt

from .history import ROOT,sha

DATA=ROOT/'data/finite_sink_20261101'
COLORS=('#2166ac','#4393c3','#7b68a6','#d18a30','#b44e42','#267a62')


def generate(out,save):
    ledger=json.loads((DATA/'checksums.json').read_text())['artifact_sha256']
    for name,h in ledger.items():
        if sha(DATA/name)!=h:raise ValueError('Changed finite-sink evidence: '+name)
    a=json.loads((DATA/'analysis.json').read_text());p=json.loads((DATA/'presentation.json').read_text())
    cases=json.loads((DATA/'cases.json').read_text());reg=json.loads((DATA/'registration.json').read_text())
    targets=p['nominal_matched_targets'];tex=[]
    if len(targets)!=6 or not all(r['status']=='PASS' and 199.995<=r['Tdie_K']<=200 for r in targets):
        raise ValueError('Unresolved finite-sink target; cannot publish target table')
    def macro(name,value):tex.append('\\newcommand{\\'+name+'}{'+str(value)+'}')
    macro('SinkTargetRows','\n'.join(f"{r['sink_K_W']:g} & {r['current_A']:.6f} & {r['hot_K']:.3f} & {r['terminal_V']:.6f} & {r['terminal_W']:.6f} & {r['sink_W']:.6f} & {r['terminal_power_fraction_from_R0']*100:.2f}"+r' \\' for r in targets))
    for name,key in (('SinkIdealPower','terminal_W'),('SinkFinalPower','terminal_W'),('SinkFinalHeat','sink_W'),('SinkFinalHot','hot_K')):
        r=targets[0] if name=='SinkIdealPower' else targets[-1];macro(name,f'{r[key]:.6f}')
    macro('SinkPowerPercent',f"{targets[-1]['terminal_power_fraction_from_R0']*100:.4f}")
    with plt.rc_context({'font.size':8,'legend.fontsize':6}):
        fig=plt.figure(figsize=(6.5,3.35),layout='constrained');gs=fig.add_gridspec(2,2,height_ratios=[4,1])
        left=fig.add_subplot(gs[0,0]);status=fig.add_subplot(gs[1,0],sharex=left);right=fig.add_subplot(gs[:,1])
        for j,(target,color) in enumerate(zip(targets,COLORS)):
            R=target['sink_K_W'];rows=[cases[c['id']] for c in reg['design']['grid'] if c['hypothesis']=='nominal' and c['sink_K_W']==R]
            left.plot([r['case']['current_A'] for r in rows],[r['audit']['Tdie_K'] if r['status']=='ACCEPTED' else np.nan for r in rows],color=color,lw=1,label=f'{R:g} K/W')
            for r in rows:
                if r['status']=='ACCEPTED':
                    x=r['audit'];left.plot(r['case']['current_A'],x['Tdie_K'],'o',ms=2.5,mec=color,mfc='white' if x['assumed_continuation'] else color)
                    right.plot(x['Tdie_K'],x['terminal_W'],'o',ms=3,color=color)
                else:status.plot(r['case']['current_A'],j,'x',ms=3,color=color)
            right.plot(target['Tdie_K'],target['terminal_W'],'D',ms=4,mec=color,mfc='white')
        left.axhline(200,color='.5',ls=':',lw=.8);left.set(ylabel='Die temperature (K)',title='Nominal current grid');left.legend(ncol=2,loc='upper right');left.grid(alpha=.15);left.tick_params(labelbottom=False)
        status.set(xlabel='Current (A)',ylabel='Rejected\nR (K/W)',yticks=range(6),yticklabels=[f"{r['sink_K_W']:g}" for r in targets],ylim=(-.7,5.7));status.tick_params(labelsize=5.5)
        right.axvline(200,color='.5',ls=':',lw=.8);right.set(xlim=(195,207),ylim=(.45,.75),xlabel='Attained die temperature (K)',ylabel='Terminal input (W)',title='Target neighborhood');right.grid(alpha=.15)
        save(fig,'finite_sink_operating')
        fig,axs=plt.subplots(1,2,figsize=(6.5,2.7),layout='constrained')
        for target,color in zip(targets,COLORS):
            R=target['sink_K_W'];q=np.array([.5,3.]);axs[0].plot(q,R*q,'--',color=color,lw=.8,label=f'{R:g} K/W')
            rows=[r for r in cases.values() if r['case']['family']=='grid' and r['case']['hypothesis']=='nominal' and r['case']['sink_K_W']==R and r['status']=='ACCEPTED']
            axs[0].scatter([r['audit']['sink_W'] for r in rows],[r['audit']['hot_K']-300 for r in rows],s=7,color=color)
        axs[0].set(xlabel='Actual sink rejection (W)',ylabel='Hot rise above ambient (K)');axs[0].legend(ncol=2,loc='upper left');axs[0].grid(alpha=.15)
        x=np.arange(6);positive=np.zeros(6);negative=np.zeros(6)
        for name,scale,label,color in (('Qdie_W',1.,'Die heat','#aa9379'),('Au_into_die_W',1.,'Au from ambient','#d7aa50'),('Cu_into_hot_W',1.,'Cu into hot pad','#4293ae'),('Cu_joule_W',-.5,'Cu Joule to pins','#8a71a2')):
            value=np.array([r[name]*scale*1000 for r in targets]);axs[1].bar(x,value,bottom=np.where(value>=0,positive,negative),color=color,label=label)
            positive+=np.maximum(value,0);negative+=np.minimum(value,0)
        axs[1].plot(x,[r['sink_minus_terminal_W']*1000 for r in targets],'kD',ms=3,label='Sink minus input')
        axs[1].set(ylim=(negative.min()-3,positive.max()+4),xticks=x,xticklabels=[f"{r['sink_K_W']:g}" for r in targets],xlabel='Sink resistance (K/W)',ylabel='Sink minus input (mW)');axs[1].axhline(0,color='.5',lw=.6);axs[1].legend(fontsize=5.5,loc='lower left')
        save(fig,'finite_sink_heat')
    (out/'finite_sink_numerics.tex').write_text('\n'.join(tex)+'\n')
    return [DATA/p for p in ('registration.json','cases.json','analysis.json','presentation.json','controls.json','branch_checks.json','target_crossings.json','checksums.json')]
