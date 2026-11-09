"""Physical pinout diagram from original immutable V3 R1 CAD.
Pin geometry is source-derived and looked down toward header:
no inferred positive/negative polarity, no unverified wire routing.
"""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'figures'
D=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
pins={}
for b in D['bodies']:
    if b['name'].startswith('pin') and b['name'][3:].isdigit() and b['material']=='Kovar_pin':
        pins[int(b['name'][3:])]=tuple(b['base'][:2])
assert set(pins)==set(range(1,10))
assert pins[1][0]<0 and pins[9][0]<0 and pins[7][1]>0 and pins[8][1]>0
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                     'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig=plt.figure(figsize=(11.4,5.4),facecolor='white')
ax=fig.add_axes([.080,.21,.40,.57])
ax.set_aspect('equal')
ax.set_xlim(-8.25,8.25);ax.set_ylim(-7.6,8.1)
ax.add_patch(Circle((0,0),6.3,fc='#f4f7f9',ec='#b5c1cb',lw=1.5,ls='--',zorder=0))
for n,(x,y) in sorted(pins.items()):
    col='#2e7195' if n in (1,9) else '#b7774a' if n in (7,8) else '#aab4be'
    ax.add_patch(Circle((x,y),.53,facecolor=col,edgecolor='white',lw=1.2,zorder=3))
    ax.text(x,y,str(n),ha='center',va='center',color='white' if n in (1,7,8,9) else '#27384d',weight='bold',fontsize=11,zorder=4)
ax.set_title('Source-CAD top-view pin centers',loc='left',weight='bold',fontsize=11,color='#20384d',pad=9)
ax.set_xlabel('x (mm)');ax.set_ylabel('y (mm)')
ax.grid(alpha=.12)

side=fig.add_axes([.56,.20,.40,.61]);side.axis('off')
side.text(0,1.025,'Two independent electrical circuits',fontsize=11,fontweight='bold',color='#20384d',transform=side.transAxes)
def panel(y,label,col,lines):
    side.add_patch(FancyBboxPatch((.0,y),.99,.38,boxstyle='round,pad=.025,rounding_size=.03',
         lw=1,edgecolor='#d6dee5',facecolor='#f5f8fa',transform=side.transAxes))
    side.add_patch(Circle((.055,y+.31),.022,facecolor=col,transform=side.transAxes,clip_on=False))
    side.text(.105,y+.295,label,fontweight='bold',color='#293d51',fontsize=10.2,transform=side.transAxes)
    for j,t in enumerate(lines):side.text(.055,y+.22-.073*j,t,color='#475b70',fontsize=9.1,transform=side.transAxes)
panel(.55,'Thermoelectric cooler','#2e7195',[
    'Pin 1  →  88 P/N thermoelectric legs  →  Pin 9',
    'Three stages; 29 / 11 / 4 couples',
    'Terminal current: 0.400 A (nominal model)'])
panel(.03,'HgCdTe photoconductor','#b7774a',[
    'Pin 7  →  detector electrical path  →  Pin 8',
    'Separate from TEC electrical power supply',
    'Detector bias polarity is not specified here'])
fig.text(.055,.95,'Nine-pin TO header: circuit assignments',fontsize=15,fontweight='bold',color='#20384d')
fig.text(.056,.900,'Source-derived pin coordinates  |  Separate TEC and detector electrical paths',fontsize=9.5,color='#57697b')
fig.text(.056,.095,'Dashed circle: location guide only, not the machined flange. Pin polarities and actual lead harness are not asserted.',fontsize=8.7,color='#64758a')
for ext in ('pdf','png'):
    p=OUT/f'cad_package_pinout.{ext}'
    if ext=='pdf':fig.savefig(p,bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
    else:fig.savefig(p,dpi=210,bbox_inches='tight')
    print(p,p.stat().st_size)
plt.close(fig)
