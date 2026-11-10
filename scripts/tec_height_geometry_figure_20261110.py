"""Plot measured source coordinates and unqualified analytic height proposal."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/tec_height_geometry_20261110/analytic_coordinate_proposal.json').read_text())
plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'axes.titlesize':10})
fig,axs=plt.subplots(1,2,figsize=(8.3,4.8),sharey=True,constrained_layout=True)
for ax,key,title in zip(axs,['0.5','0.6'],['Source 0.50 mm legs','Proposed 0.60 mm legs']):
 c=d['cases'][key]
 for p in c['plate_rows']:
  w=p['width_mm'];z=p['candidate_z0_mm'];ax.add_patch(Rectangle((-w/2,z),w,.5,facecolor='#d4e0e8',edgecolor='#31556b',lw=.9))
  ax.text(0,z+.25,f"C{p['index']}",ha='center',va='center',fontsize=8)
 for s in range(3):
  leg=next(l for l in c['legs'] if l['stage']==s);z=leg['leg_z0_mm']
  for x in (-.6,.2):ax.add_patch(Rectangle((x,z),.4,c['height_mm'],facecolor='#bb7557',edgecolor='#7d4028',lw=.7))
  ax.text(1.6,z+c['height_mm']/2,f"{c['height_mm']:.2f} mm",va='center',fontsize=8)
 ax.axhline(c['die_top_mm'],color='#a14242',lw=1,ls='--');ax.text(-3.2,c['die_top_mm']+.06,'die top',fontsize=8,color='#8e3333')
 ax.set(xlim=(-3.5,3.5),ylim=(1.4,6.35),xlabel='Schematic lateral position (mm)',title=title);ax.grid(alpha=.18)
axs[0].set_ylabel('Height above header datum (mm)')
fig.suptitle('Source-coordinate stack translation; schematic legs, not CAD solids',fontsize=10)
for ext in ('pdf','png'):fig.savefig(R/f'reports/current/figures/v318_height_stack.{ext}',dpi=190)
