"""Frozen finite-sink observations/figures only; never calls a solver."""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .tec_material_plausibility import ROOT,read,write,sha

COLORS=('#2166ac','#4393c3','#7b68a6','#d18a30','#b44e42','#267a62')


def present(folder):
    folder=Path(folder).resolve();reg=read(folder/'registration.json');a=read(folder/'analysis.json');cases=read(folder/'cases.json')
    if (folder/'STOP.json').exists():raise ValueError('Stopped study; no comparative publication')
    if sha(folder/'producer.py.source')!=reg['producer_sha256']:raise ValueError('Executed producer changed')
    rows=[];matched=[]
    for row in a['tables']:
        record=dict(row)
        for key in ('minimum_grid_die_case','minimum_power_grid_target_case'):
            cid=row[key];record[key+'_values']=cases[cid]['audit'] if cid else None
            if cid:record[key+'_current_A']=cases[cid]['case']['current_A']
        rows.append(record)
    for R,cross in a['target_crossings'].items():
        record={'sink_K_W':float(R),'status':cross['status'],'attempted_midpoints':len(cross['attempts'])}
        if cross['status']=='PASS':
            r=cases[cross['cold_side_case']];record.update(case=r['case']['id'],current_A=r['case']['current_A'],**r['audit'])
        matched.append(record)
    reference=next((r for r in matched if r['sink_K_W']==0 and r['status']=='PASS'),None)
    if reference:
        for r in matched:
            if r['status']=='PASS':r['terminal_power_change_from_R0_W']=r['terminal_W']-reference['terminal_W'];r['terminal_power_fraction_from_R0']=r['terminal_W']/reference['terminal_W']-1
    out={'grid_tables':rows,'nominal_matched_targets':matched,'counts':a['coverage_by_family'],
         'scope':'Actual frozen reduced outputs; target points within 0.005 K on sampled branch, not physical feasibility or global power optima'}
    write(folder/'presentation.json',out)
    accepted=[]
    for r in cases.values():
        if r['status']=='ACCEPTED':
            c=r['case'];x=r['audit'];accepted.append({**{k:c[k] for k in ('id','family','hypothesis','sink_K_W','current_A')},
                **{k:x[k] for k in ('hot_K','Tdie_K','leg_min_K','leg_max_K','assumed_continuation','terminal_V','terminal_W','sink_W','Qc_cold_W','die_COP','cooler_COP')}})
    with (folder/'accepted.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(accepted[0]),lineterminator='\n');writer.writeheader();writer.writerows(accepted)
    images=[]
    def save(fig,name):
        for suffix in ('pdf','png'):
            p=folder/(name+'.'+suffix);fig.savefig(p,dpi=280,bbox_inches='tight',pad_inches=.07,
                **({'metadata':{'CreationDate':None,'ModDate':None,'Author':'','Creator':'Engineering assessment'}} if suffix=='pdf' else {}))
            images.append(p.name)
        plt.close(fig)
    sinks=sorted({r['sink_K_W'] for r in rows})
    with plt.rc_context({'font.size':10,'legend.fontsize':8}):
        fig,(ax,status)=plt.subplots(2,1,figsize=(8,5.6),sharex=True,gridspec_kw={'height_ratios':[4.5,1]},layout='constrained')
        for j,(R,color) in enumerate(zip(sinks,COLORS)):
            points=[cases[c['id']] for c in reg['design']['grid'] if c['hypothesis']=='nominal' and c['sink_K_W']==R]
            ax.plot([r['case']['current_A'] for r in points],[r['audit']['Tdie_K'] if r['status']=='ACCEPTED' else np.nan for r in points],'-',color=color,label=f'{R:g} K/W')
            for r in points:
                I=r['case']['current_A']
                if r['status']=='ACCEPTED':ax.plot(I,r['audit']['Tdie_K'],'o',ms=4,mec=color,mfc='white' if r['audit']['assumed_continuation'] else color)
                else:status.plot(I,j,'x',ms=5,color=color)
        ax.axhline(200,color='.4',ls=':');ax.set(ylabel='Die temperature (K)',title='Nominal laws; 300 K ambient, 2 mW die, original wires ON; exchange OFF')
        ax.grid(alpha=.2);ax.legend(title='Effective sink resistance',ncol=2,loc='upper right')
        status.set(xlabel='Series current (A)',ylabel='Rejected\nR (K/W)',yticks=range(len(sinks)),yticklabels=[f'{R:g}' for R in sinks],ylim=(-.7,len(sinks)-.3));status.tick_params(labelsize=7);status.grid(alpha=.15)
        status.text(.02,-.75,'Filled circles: measured-domain legs. Open circles: assumed >300 K law. Crosses in lower strip: rejected; no T value.',transform=status.transAxes,fontsize=8)
        save(fig,'sink_current_and_coverage')
        fig,axes=plt.subplots(1,2,figsize=(10.5,4.3),layout='constrained')
        for R,color in zip(sinks,COLORS):
            rset=[r for r in cases.values() if r['case']['family']=='grid' and r['case']['hypothesis']=='nominal' and r['case']['sink_K_W']==R and r['status']=='ACCEPTED']
            ids=next(t for t in a['tables'] if t['hypothesis']=='nominal' and t['sink_K_W']==R)['target_nondominated_grid_cases']
            target=next(x for x in matched if x['sink_K_W']==R)
            for ax in axes:
                ax.scatter([r['audit']['Tdie_K'] for r in rset],[r['audit']['terminal_W'] for r in rset],s=13,color=color,label=f'{R:g} K/W')
                ax.scatter([cases[k]['audit']['Tdie_K'] for k in ids],[cases[k]['audit']['terminal_W'] for k in ids],s=45,marker='*',color=color)
                if target['status']=='PASS':ax.scatter([target['Tdie_K']],[target['terminal_W']],marker='D',s=35,facecolor='white',edgecolor=color)
        for ax in axes:
            ax.axvline(200,color='.4',ls=':');ax.set(xlabel='Actually attained die temperature (K)',ylabel='Terminal electrical input (W)');ax.grid(alpha=.2)
        axes[0].set_title('Nominal grid: discrete trade-offs');axes[0].legend(ncol=2)
        axes[1].set(xlim=(195,207),ylim=(.45,.75),title='Target neighborhood: actual points only')
        fig.text(.5,-.04,'Stars: <=200 K nondominated grid points within each sink scenario. Open diamonds: bounded actual target solves.',ha='center',fontsize=8)
        save(fig,'sink_power_tradeoff')
        fig,axs=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
        for R,color in zip(sinks,COLORS):
            q=np.array([.5,3.]);axs[0].plot(q,R*q,'--',color=color,lw=1,label=f'{R:g} K/W')
            rset=[r for r in cases.values() if r['case']['family']=='grid' and r['case']['hypothesis']=='nominal' and r['case']['sink_K_W']==R and r['status']=='ACCEPTED']
            axs[0].scatter([r['audit']['sink_W'] for r in rset],[r['audit']['hot_K']-300 for r in rset],s=13,color=color)
        axs[0].set(xlabel='Actual sink rejection (W)',ylabel='Hot ceramic minus ambient (K)',title='Dots: solved. Dashed: 0.5–3 W scaling controls.');axs[0].grid(alpha=.2);axs[0].legend(ncol=2)
        target=[r for r in matched if r['status']=='PASS'];x=np.arange(len(target));positive=np.zeros(len(x));negative=np.zeros(len(x))
        for name,scale,label,color in (('Qdie_W',1.,'Imposed die heat','#aa9379'),('Au_into_die_W',1.,'Au heat from ambient','#d7aa50'),
                ('Cu_into_hot_W',1.,'Cu conduction into hot pad','#4293ae'),('Cu_joule_W',-.5,'Cu Joule to pin reservoir','#8a71a2')):
            val=np.array([r[name]*scale*1000 for r in target]);bottom=np.where(val>=0,positive,negative)
            axs[1].bar(x,val,bottom=bottom,color=color,label=label);positive+=np.maximum(val,0);negative+=np.minimum(val,0)
        axs[1].plot(x,[r['sink_minus_terminal_W']*1000 for r in target],'kD',ms=4,label='Sink minus terminal input')
        axs[1].set_ylim(float(negative.min())-3,float(positive.max())+4)
        axs[1].axhline(0,color='.4',lw=.7);axs[1].set(xticks=x,xticklabels=[f"{r['sink_K_W']:g}" for r in target],xlabel='Sink resistance (K/W)',ylabel='Sink minus terminal input (mW)',title='Nominal matched 199.995–200 K: signed budget')
        axs[1].legend(fontsize=7,loc='lower left');axs[1].grid(axis='y',alpha=.2)
        save(fig,'sink_rise_and_signed_budget')
    write(folder/'figure_provenance.json',{'producer_sha256':sha(__file__),
        'inputs':{str((folder/p).relative_to(ROOT)):sha(folder/p) for p in ('registration.json','cases.json','analysis.json','presentation.json')},
        'figures':{p:sha(folder/p) for p in images},'no_new_solves':True})
    write(folder/'checksums.json',{'artifact_sha256':{str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*'))
        if p.is_file() and p.name!='checksums.json' and 'verification' not in p.relative_to(folder).parts},
        'scope':'Frozen finite-sink science, controls, actual target attempts and derived figures; verification records are separate'})
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args();present(a.data)
