"""Frozen-case analysis and visuals only: no solver, fit or additional scenarios."""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .tec_material_plausibility import ROOT,read,write,sha


def present(folder):
    folder=Path(folder).resolve();reg=read(folder/'registration.json');a=read(folder/'analysis.json');cases=read(folder/'cases.json');plan=reg['design']
    common=set.intersection(*[{(r['I'],r['Q'],r['field']) for r in a['oem_rows'] if r['factor']==g and r['status']=='CONDITIONAL'} for g in (.8,1.,1.2,1.7)])
    errors=[]
    for g in (.8,1.,1.2,1.7):
        for field in ('delta_t_k','voltage_v'):
            rows=[r for r in a['oem_rows'] if r['factor']==g and r['field']==field and r['status']=='CONDITIONAL' and (r['I'],r['Q'],field) in common]
            errors.append({'g':g,'field':field,'common_count':len(rows),'mean_signed':float(np.mean([r['difference'] for r in rows])),
                'MAE':float(np.mean([abs(r['difference']) for r in rows])),'mean_absolute_relative':float(np.mean([abs(r['relative_difference']) for r in rows]))})
    targets=[]
    for g in (.8,1.,1.2,1.7):
        rows=[dict(cases[x['case']]['summary'],case=x['case']) for x in plan['targets'] if x['g']==g and cases[x['case']]['status']=='ACCEPTED']
        hits=[r for r in rows if r['Tdie_K']<=200.]
        targets.append({'g':g,'accepted':len(rows),'rejected':sum(x['g']==g and cases[x['case']]['status']=='REJECTED' for x in plan['targets']),
            'lowest_current_admitted_hit':min(hits,key=lambda r:r['current_A']) if hits else None,
            'minimum_admitted_sample':min(rows,key=lambda r:r['Tdie_K']) if rows else None})
    topology=[]
    for x in plan['topology']:
        if cases[x['case']]['status']!='ACCEPTED':continue
        b=next(r for r in plan['jacobian']['300.15'] if r['I']==x['I'] and r['Q']==x['Q'])['base']
        s=cases[x['case']]['summary'];baseline=cases[b]['summary']
        topology.append({'I':x['I'],'Q':x['Q'],'case':x['case'],'baseline':b,
            'lift_difference_K':s['cold_lift_K']-baseline['cold_lift_K'],'voltage_difference_V':s['module_voltage_V']-baseline['module_voltage_V']})
    record={'common_OEM_errors':errors,'target_samples':targets,'topology_contrasts':topology,
        'primary_omitted_source_samples':sorted({(r['I'],r['Q']) for r in a['oem_rows'] if 'no exact digitized' in r['status']}),
        'no_fit':True,'different_Thot_dry_N2':'NOT COMPARABLE','no_additional_simulations':True}
    write(folder/'presentation.json',record)
    images=[]
    def save(fig,name):
        for suffix in ('pdf','png'):
            p=folder/(name+'.'+suffix)
            fig.savefig(p,dpi=280,bbox_inches='tight',pad_inches=.07,
                **({'metadata':{'CreationDate':None,'ModDate':None,'Author':'','Creator':'Engineering assessment'}} if suffix=='pdf' else {}))
            images.append(p.name)
        plt.close(fig)
    with plt.rc_context({'font.size':10}):
        fig,axs=plt.subplots(1,2,figsize=(10.5,3.4),layout='constrained')
        for hot,style in (('300.15','-'),('295.0','--')):
            for step,marker in (('0.005','o'),('0.0025','s')):
                b=a['jacobians'][hot]['steps'][step]['raw'];v=np.array(b['singular_values'])
                axs[0].semilogy(np.arange(1,5),v/v[0],style,marker=marker,label=f'{hot} K; h={step}')
        axs[0].axhline(1e-5,color='.4',ls=':');axs[0].set(xlabel='Singular-value index',ylabel='Raw singular value / largest',xticks=[1,2,3,4]);axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
        b=a['jacobians']['300.15']['steps']['0.0025'];matrix=np.asarray(b['raw']['matrix'])
        for j,label in enumerate(('Geometry g','Resistivity r','Conductivity k','Seebeck s')):
            axs[1].plot(np.arange(1,len(matrix)+1),matrix[:,j],'o-',ms=3,label=label)
        axs[1].set(xlabel='Stacked normalized output row (lift, V pairs)',ylabel='Derivative per unit log factor');axs[1].legend(fontsize=8);axs[1].grid(alpha=.2)
        save(fig,'identifiability_spectrum')
        colors={.8:'#b45b3f',1.:'#2266a3',1.2:'#7b69a6',1.7:'#2c866a'}
        fig,axs=plt.subplots(2,2,figsize=(10.5,7),layout='constrained')
        for j,field in enumerate(('delta_t_k','voltage_v')):
            ax=axs[0,j]
            for g,color in colors.items():
                rows=sorted([r for r in a['oem_rows'] if r['factor']==g and r['Q']==0 and r['field']==field],key=lambda r:r['I'])
                ax.plot([r['I'] for r in rows],[r.get('model_value',np.nan) for r in rows],'o-',ms=4,color=color,label=f'g={g:g}')
            rows=sorted([r for r in a['oem_rows'] if r['factor']==1 and r['Q']==0 and r['field']==field and 'source_value' in r],key=lambda r:r['I'])
            ax.errorbar([r['I'] for r in rows],[r['source_value'] for r in rows],yerr=[r['reading_bound'] for r in rows],fmt='ks',ms=4,label='Published chart')
            ax.set(xlabel='Current (A)',ylabel='Cold-ceramic lift (K)' if j==0 else 'Module voltage (V)',title='300.15 K, zero load, idealized vacuum');ax.grid(alpha=.2)
        axs[0,0].legend(fontsize=8)
        for g,color in colors.items():
            rows=[x for x in plan['targets'] if x['g']==g]
            for j,key in enumerate(('Tdie_K','terminal_input_W')):
                axs[1,j].plot([r['I'] for r in rows],[cases[r['case']]['summary'][key] if cases[r['case']]['status']=='ACCEPTED' else np.nan for r in rows],
                    'o-',ms=4,color=color,label=f'g={g:g}')
        axs[1,0].axhline(200,color='.4',ls=':')
        for j,label in enumerate(('Die temperature (K)','Terminal electrical input (W)')):
            axs[1,j].set(xlabel='Current (A)',ylabel=label,title='300 K hot ceramic, 2 mW die, wires ON');axs[1,j].grid(alpha=.2)
        save(fig,'geometry_residual_and_target')
        manifest=read(ROOT/'fem/results/geometry_complete_checkpoint_20261030/manifest.json');audits=read(folder/'geometry_audit.json');leg=next(b for b in manifest['bodies'] if b['id']==5)
        x,y,z,w,d,h=leg['boxes_m'][0];cx=x+w/2;cy=y+d/2
        fig,axs=plt.subplots(1,2,figsize=(10.5,3.5),layout='constrained');ax=axs[0]
        owners=audits[0]['face_ownership'][0]['Cu_owners']
        for body in manifest['bodies']:
            if body['id'] not in owners:continue
            for bx,by,bz,bw,bd,bh in body['boxes_m']:
                if min(abs(bz-z),abs(bz+bh-z))<1e-11:
                    ax.add_patch(Rectangle(((bx-cx)*1000,(by-cy)*1000),bw*1000,bd*1000,color='#c5a66b',alpha=.6,label='Actual native Cu footprint'))
        ax.add_patch(Rectangle((-.2,-.2),.4,.4,fill=False,edgecolor='#2266a3',lw=2,label='Original 0.4 mm leg'))
        width=.4*np.sqrt(1.7);ax.add_patch(Rectangle((-width/2,-width/2),width,width,fill=False,edgecolor='#b45b3f',ls='--',lw=2,label='Area ×1.7 hypothesis'))
        ax.set(xlim=(-.4,.4),ylim=(-.4,.4),xlabel='Local x (mm)',ylabel='Local y (mm)',title='First leg hot-end source rectangles');ax.set_aspect('equal');ax.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.2))
        rows=audits[:4];axs[1].bar([str(r['area_factor']) for r in rows],[r['minimum_footprint_coverage']*100 for r in rows],color=[colors[r['area_factor']] for r in rows])
        axs[1].set(xlabel='Area factor (length fixed)',ylabel='Minimum full-face Cu coverage (%)',title='All 176 axial faces audited');axs[1].axhline(100,color='.5',ls=':');axs[1].grid(axis='y',alpha=.2)
        save(fig,'native_pad_constraint')
    write(folder/'figure_provenance.json',{'generator_sha256':sha(__file__),'input_sha256':{str((folder/n).relative_to(ROOT)):sha(folder/n) for n in ('registration.json','analysis.json','cases.json','geometry_audit.json')},
        'figures':{n:sha(folder/n) for n in images},'scope':'Actual saved reduced results and native box rectangles; no invented field, no additional solves or fit'})
    write(folder/'checksums.json',{'artifact_sha256':{str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='checksums.json'},'scope':'Completed identifiability scientific evidence, including preserved postprocessing failure'})
    return record


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args();present(a.data)
