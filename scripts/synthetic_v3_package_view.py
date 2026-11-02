"""Clipped full-header view from saved imported-BRep curves, no CAD/mesh rerun."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
B=Path('data/synthetic_v3_assembly_20261102');D=B/'drawings'
by={b['name']:b for b in json.loads((B/'source_final/design.json').read_text())['bodies']}
fig=plt.figure(figsize=(11,7));ax=fig.add_subplot(111,projection='3d')
for row in json.loads((D/'actual_brep_edges.json').read_text()):
    b=by[row['name']];color='#a26b13' if b['material'] in ('Cu','Au') else '#b83f45' if b['material']=='P' else '#295b9b' if b['material']=='N' else '#6c7a89'
    segments=[]
    for curve in row['curves_mm']:
        for a,bb in zip(curve,curve[1:]):
            a=np.array(a);bb=np.array(bb)
            if max(a[2],bb[2])<0:continue
            if a[2]<0:a=a+(bb-a)*(-a[2]/(bb[2]-a[2]))
            if bb[2]<0:bb=bb+(a-bb)*(-bb[2]/(a[2]-bb[2]))
            segments.append([a,bb])
    ax.add_collection3d(Line3DCollection(segments,colors=color,linewidths=.35,alpha=.8))
ax.set(xlim=(-16,16),ylim=(-9,9),zlim=(0,7),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)');ax.set_box_aspect((32,18,9));ax.view_init(28,-60)
ax.set_title('Actual V3 STEP interior — full two-ear header and installed circuits')
for pin in (1,7,8,9):
    b=by['pin'+str(pin)];x,y,_=b['base'];ax.text(x,y,2.4,str(pin),color='black',fontsize=10)
fig.text(.05,.05,'Actual imported BRep edges. Cap/window hidden; exterior pin tails clipped at z=0 for inspection.\nSynthetic assembly; selected process requirements, not a manufactured/qualified device.',fontsize=9)
fig.savefig(D/'package_actual_STEP_corrected.png',dpi=220);fig.savefig(D/'package_actual_STEP_corrected.svg',metadata={'Date':None})
