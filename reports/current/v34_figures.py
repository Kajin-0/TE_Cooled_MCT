"""Physics-derived publication figures for V3.4 copper multiport.
Only completed saved V3.3 and V3.4 results are consumed; zero PDE solves.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
FIG=HERE/'figures'
OLD=ROOT/'data/v3_3_cavity_package_feedback_20261108/attempt02/result.json'
NEW=ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json'
def load(p):return json.loads(p.read_text())
def save(fig,name):
    fig.savefig(FIG/f'{name}.pdf',bbox_inches='tight',metadata={'Creator':'Synthetic device engineering report; archived sources','CreationDate':None,'ModDate':None})
    fig.savefig(FIG/f'{name}.png',dpi=210,bbox_inches='tight')
    plt.close(fig)
    print('Saved',name)
def plots():
    assert OLD.exists() and NEW.exists()
    d0=load(OLD);d1=load(NEW)
    assert 'V3.4 PROVISIONAL' in d1['status']
    plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans',
        'axes.spines.top':False,'axes.spines.right':False,
        'pdf.fonttype':42,'savefig.facecolor':'white'})
    keys=['stage0_hot','stage0_cold','stage1_hot','stage1_cold',
          'stage2_hot','stage2_cold','carrier','die']
    labels=['S1 hot','S1 cold','S2 hot','S2 cold','S3 hot','S3 cold','Carrier','HgCdTe']
    x=np.arange(len(keys))
    a=np.array([d0['source_full_temperature_nodes_K'][k] for k in keys])
    b=np.array([d1['source_full_temperature_nodes_K'][k] for k in keys])
    fig,ax=plt.subplots(figsize=(10.7,4.25),layout='constrained')
    ax.plot(x,a,'o-',color='#527b9a',lw=2,label='V3.3: interstage Cu not coupled')
    ax.plot(x,b,'s-',color='#b86b38',lw=2,label='V3.4: source Cu multiport coupled')
    ax.set_xticks(x,labels,rotation=28,ha='right')
    ax.set_ylabel('Calculated local temperature (K)')
    ax.grid(axis='y',alpha=.25)
    ax.legend(loc='upper right',frameon=False)
    ax.set_title('Interstage copper heat transfer changes the whole cooler',fontsize=13,fontweight='bold')
    ax.annotate(f'ΔTdetector = {b[-1]-a[-1]:+.2f} K',
      xy=(7,b[-1]),xytext=(5.3,b[-1]+16),
      arrowprops={'arrowstyle':'->','color':'#9b492d'},color='#9b492d',fontweight='bold')
    save(fig,'v34_copper_stage_temperature_comparison')
    nets=['58','80','88']
    c=d1['Cu_form_tab_electrothermal_result']['net_details']
    stage=np.zeros((3,3))
    for i,net in enumerate(nets):
        z=c[net]
        for f,q in zip(z['face_tags'],z['face_heat_into_ceramic_W']):
            target=0 if int(f) in (38,36) else 1 if int(f) in (75,79,74) else 2
            stage[i,target]+=q*1e3
    fig,ax=plt.subplots(figsize=(9.5,4.8),layout='constrained')
    xx=np.arange(3);bw=.24
    for i,(net,color) in enumerate(zip(nets,['#5282a0','#b66d3c','#6c719c'])):
        ax.bar(xx+(i-1)*bw,stage[i],width=bw,label=f'Net {net}',color=color)
    ax.axhline(0,color='#27394e',lw=1.1)
    ax.set_xticks(xx,['Hot ceramic','Intermediate ceramic','Upper ceramic'])
    ax.set_ylabel('Heat into ceramic (mW); negative = heat removed')
    ax.set_title('Heat redistributed by actual formed-Cu interstage contacts',fontsize=13,fontweight='bold')
    ax.grid(axis='y',alpha=.2)
    ax.legend(frameon=False)
    save(fig,'v34_copper_face_heat_budget')
    return {'v3_3_die_K':float(a[-1]),'v3_4_die_K':float(b[-1]),
      'temperature_delta_K':float(b[-1]-a[-1]),
      'stage_heat_by_net_mW':{n:stage[i].tolist() for i,n in enumerate(nets)},
      'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (OLD,NEW)}}
if __name__=='__main__':
    m=plots()
    (HERE/'v34_figure_provenance.json').write_text(json.dumps(m,indent=2)+'\n')
    print(json.dumps(m,indent=2))
