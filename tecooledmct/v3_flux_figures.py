"""Deterministic figures from the frozen STOP dataset; no solver or mesh."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BASE=Path('data/v3_conservative_flux_20261102')

def main():
    out=BASE/'figures';out.mkdir(exist_ok=False)
    cases=json.loads((BASE/'controls/cases.json').read_text())[-2:]
    audit=json.loads((BASE/'saved_audit.json').read_text())
    raw=json.loads((BASE/'geometry/L1_field/P1_raw.json').read_text())
    plt.rcParams.update({'font.size':10,'svg.hashsalt':'v3_flux_registered_stop'})
    fig,axes=plt.subplots(1,2,figsize=(11,4.7))
    for method,label in [('P1_raw','Raw CG P1'),('recovered','RT0 recovery'),('mixed','Direct mixed RT0/P0')]:
        axes[0].plot([q['n'] for q in cases],[100*q['methods'][method]['relative_flux_L2_error'] for q in cases],'-o',label=label)
    axes[0].axhline(5,color='black',ls='--',lw=1,label='Fine-control limit')
    axes[0].set(xlabel='Subdivisions per cube edge',ylabel='Actual flux L2 error (%)',xticks=[4,8],ylim=(0,5.5),title='Nonuniform analytic 3D control: PASS')
    axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
    vals=[100*raw['loss_relative_error'],100*audit['independent_IV_loss_relative_error']]
    axes[1].bar(['P1 weak loss identity','Recovered-field loss'],vals,color=['#326b94','#b34235'])
    axes[1].axhline(.5,color='black',ls='--',label='Coupon release limit')
    axes[1].set(ylabel='|integrated loss / IV − 1| (%)',ylim=(0,1),title='Actual L1 coupon: FAIL / STOP')
    axes[1].legend(fontsize=8);axes[1].grid(axis='y',alpha=.2)
    fig.text(.08,.02,'Conservative recovered cuts close; actual loss error still fails. Direct mixed coupon flux export was lost.',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,1))
    for ext in ('png','svg'):fig.savefig(out/('accuracy_and_loss.'+ext),dpi=240,metadata={'Date':None} if ext=='svg' else None)
    plt.close(fig)
    old=json.loads((BASE/'original_reproduction.json').read_text())['audits']
    total=[];lead=[]
    for level in ('coarse','fine'):
        groups=old[level]['volume_by_group'];total.append(100*abs(sum(q['tet_volume_m3'] for q in groups)/sum(q['CAD_volume_m3'] for q in groups)-1))
        lead.append(100*abs(next(q['relative_volume_error'] for q in groups if q['group']=='lead9')))
    fine=json.loads((BASE/'geometry/L1/fidelity.json').read_text())
    total.append(100*abs(fine['total_relative_volume_error']))
    lead.append(100*abs(next(q['relative_volume_error'] for q in fine['individual'] if q['name']=='lead9')))
    fig,ax=plt.subplots(figsize=(8,4.6));x=np.arange(3)
    ax.bar(x-.18,total,.36,label='Total volume');ax.bar(x+.18,lead,.36,label='Lead9 volume')
    ax.axhline(.25,color='black',ls='--',label='New total limit 0.25%');ax.axhline(.5,color='gray',ls=':',label='New per-domain limit 0.5%')
    ax.set(xticks=x,xticklabels=['Original coarse','Original fine','New L1'],ylabel='Absolute mesh/CAD volume error (%)',title='Same frozen CAD; geometric fidelity improves',yscale='log',ylim=(.05,10))
    ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
    fig.text(.1,.025,'L1: 207,396 tets. Geometry PASS does not qualify current or loss. L2 NOT RUN.',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,1))
    for ext in ('png','svg'):fig.savefig(out/('geometry_fidelity.'+ext),dpi=240,metadata={'Date':None} if ext=='svg' else None)
    plt.close(fig)

if __name__=='__main__':main()
