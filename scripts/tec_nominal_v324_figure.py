"""Source-only placement map and explicitly representative original section."""
from pathlib import Path
import json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text());b={x['name']:x for x in d['bodies']}
plt.rcParams.update({'font.size':8,'pdf.fonttype':42});fig=plt.figure(figsize=(9,4.6),constrained_layout=True);g=fig.add_gridspec(2,3,width_ratios=[1.2,1,1]);ax=fig.add_subplot(g[:,0])
for i in range(4):
 q=b[f'ceramic{i}']['boxes_mm'][0];ax.add_patch(Rectangle((q[0],q[2]),q[3],q[5],facecolor='#d4e0e8',edgecolor='#31556b'));ax.text(0,q[2]+q[5]/2,f'C{i}',ha='center',va='center')
for i,c in enumerate((58,22,8)):
 leg=next(x for x in d['legs'] if x['stage']==i);q=b[f'leg{leg["index"]}_{leg["polarity"]}']['boxes_mm'][0]
 for x in (-.6,.2):ax.add_patch(Rectangle((x,q[2]),.4,q[5],facecolor='#bb7557',edgecolor='#7d4028'))
 ax.text(1.2,q[2]+q[5]/2,f'{c} legs',va='center',fontsize=8)
ax.set(xlim=(-3.5,3.5),ylim=(1.4,5.8),xlabel='Representative section (mm)',ylabel='Height above datum (mm)',title='Original 0.50 mm; 2 glyphs/stage');ax.grid(alpha=.15)
for stage,idx in enumerate([(0,1),(0,2),(1,1)]):
 a=fig.add_subplot(g[idx]);q=b[f'ceramic{stage}']['boxes_mm'][0];w=q[3];a.add_patch(Rectangle((-w/2,-w/2),w,w,facecolor='#eff4f7',edgecolor='#31556b'))
 ls=[x for x in d['legs'] if x['stage']==stage]
 for pol,color in [('P','#b85b42'),('N','#386d99')]:
  v=[x for x in ls if x['polarity']==pol];a.scatter([x['center_mm'][0] for x in v],[x['center_mm'][1] for x in v],s=14,c=color,label=pol)
 a.set_aspect('equal');a.set(xlim=(-3.4,3.4),ylim=(-3.4,3.4),title=f'Stage {stage+1}: {len(ls)} legs ({len(ls)//2} pairs)',xlabel='x (mm)',ylabel='y (mm)');a.grid(alpha=.15)
a=fig.add_subplot(g[1,2]);a.axis('off');a.text(.03,.8,'Actual source P/N centers\n0.40 mm square, 0.58 mm pitch\n88 legs in series',va='top',fontsize=9);a.text(.03,.35,'● P-type',color='#b85b42',fontsize=9);a.text(.03,.20,'● N-type',color='#386d99',fontsize=9)
for e in ('png','pdf'):fig.savefig(R/f'reports/current/figures/v324_nominal_stage_geometry.{e}',dpi=190,**({'metadata':{'CreationDate':None,'ModDate':None}} if e=='pdf' else {}))
