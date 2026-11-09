"""A scientifically labeled thermal architecture illustration for the cover.
Dimensions in the original CAD are documented elsewhere; schematic explicitly
not to scale and no new physics or interpolated temperatures are introduced.
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
ROOT=Path(__file__).resolve().parents[2]
r=json.loads((ROOT/'data/v3_5_power_lead_and_copper_sensitivity_20261108/copper_native_pad/result.json').read_text())
n=r['source_full_temperature_nodes_K']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(11.4,4.7),facecolor='white')
fig.subplots_adjust(left=.04,right=.96,top=.91,bottom=.19)
ax.set_xlim(0,11.4);ax.set_ylim(0,4.5);ax.axis('off')
# Three rectangles mark stage heat-to-warm-sink direction, not a CAD projection.
levels=[('HgCdTe detector',n['die'],'#426c93',3.5),
        ('Upper TEC stage',n['stage2_hot'],'#7b9bb0',2.6),
        ('Middle TEC stage',n['stage1_hot'],'#b4a17a',1.7),
        ('Hot-side TEC ceramic',n['stage0_hot'],'#b97f56',.8)]
for label,temp,color,y in levels:
    ax.add_patch(Rectangle((.5,y),5.7,.55,facecolor=color,edgecolor='white',linewidth=1.2))
    ax.text(.7,y+.28,label,va='center',fontsize=11.3,fontweight='bold',color='white' if color in ('#426c93','#b97f56') else '#24384c')
    ax.text(6.60,y+.28,f'{temp:.2f} K',va='center',ha='left',fontsize=12.0,fontweight='bold',color='#24384c')
# Arrows on the left depict heat pumping toward the sink and are not quantitative.
for y in (3.34,2.44,1.54):
    ax.add_patch(FancyArrowPatch((1.1,y),(1.1,y-.2),arrowstyle='-|>',mutation_scale=17,lw=1.4,color='#506b80'))
ax.text(7.9,3.74,'Matched synthetic operating case',fontsize=11.1,fontweight='bold',color='#243b52')
for i,t in enumerate(('TEC drive: 0.400 A','Ambient reservoir: 300 K','Detector heat load: 2.00 mW','Krypton fill: 100 Pa')):
    ax.text(8.0,3.27-.44*i,t,fontsize=10.1,color='#465e74')
ax.text(8.0,1.08,'Calculated detector cooling',fontsize=10.5,color='#456278')
ax.text(8.0,.65,f'{300-n["die"]:.2f} K below reservoir',fontsize=14.0,color='#243b52',fontweight='bold')
fig.text(.06,.975,'THERMAL ARCHITECTURE  |  3-STAGE TEC + HgCdTe',fontsize=15.4,color='#24384d',weight='bold',va='top')
fig.text(.06,.083,'Schematic not to scale; stage temperatures are saved V3.5 source-model values, not measured hardware data.',fontsize=8.7,color='#61758a')
out=ROOT/'reports/current/figures'
for ext in ('pdf','png'):
    path=out/f'cover_thermal_architecture.{ext}'
    if ext=='pdf':fig.savefig(path,bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
    else:fig.savefig(path,dpi=210,bbox_inches='tight')
    print(path,path.stat().st_size)
plt.close(fig)
