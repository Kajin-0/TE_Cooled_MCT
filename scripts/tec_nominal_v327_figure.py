"""Actual source TRI3 common-projection patches and conservative blocker bboxes."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle,Patch
from matplotlib.collections import PatchCollection
R=Path(__file__).resolve().parents[1];v=json.loads((R/'data/nominal_gas_visibility_v327_20261111/die_window_visibility.json').read_text());fig,ax=plt.subplots(figsize=(5.8,4.3),layout='constrained');ax.add_patch(Rectangle((-.5,-.5),1,1,facecolor='#f4f4f4',edgecolor='#333333',lw=1))
patches=[Polygon(p['polygon_xy_mm'],closed=True) for p in v['patches']];ax.add_collection(PatchCollection(patches,facecolor='#2a9d8f',edgecolor='none',alpha=.85))
for b in v['source_candidates_crossing_gap']:
 if 'projected_bbox_xy_mm' not in b:continue
 x,y,X,Y=b['projected_bbox_xy_mm'];ax.add_patch(Rectangle((x,y),X-x,Y-y,fill=False,edgecolor='#c94d3f',lw=.65,alpha=.7))
ax.set(xlim=(-.53,.53),ylim=(-.53,.53),xlabel='x (mm)',ylabel='y (mm)',title='Original die → window: source-checked open columns');ax.set_aspect('equal');ax.legend(handles=[Patch(facecolor='#2a9d8f',label='Accepted projected patches'),Patch(facecolor='none',edgecolor='#c94d3f',label='Solid bounding-box exclusions')],loc='upper center',bbox_to_anchor=(.5,-.16),frameon=False,ncol=2,fontsize=8);p=R/'reports/current/figures/v327_die_window_visibility';fig.savefig(str(p)+'.pdf',metadata={'CreationDate':None,'ModDate':None});fig.savefig(str(p)+'.png',dpi=180,metadata={'Software':'Matplotlib'});plt.close(fig)
