"""Plot saved source rectangle areas; bars are not gas conductance."""
from pathlib import Path
import json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/tec_gas_partition_20261110/source_partition.json').read_text())
rows=[x for x in d['designs']['nominal']['faces'] if x['face'] in ('z-','z+')]
fig,ax=plt.subplots(figsize=(8.4,4.1),constrained_layout=True);left=[0.]*len(rows);y=list(range(len(rows)))
for k,label,col in [('solid_contact','Direct solid contact','#9b714d'),('facing_gap_unblocked_at_face','Exposed, projected facing','#4e7b9f'),('outer_unblocked_at_face','Exposed, remaining face','#a5c3d7')]:
 v=[x['partition_mm2'][k] for x in rows];ax.barh(y,v,left=left,label=label,color=col);left=[a+b for a,b in zip(left,v)]
ax.set_yticks(y,[f"{x['ceramic']} {x['face']}" for x in rows]);ax.invert_yaxis();ax.set_xlabel('Source ceramic face area (mm²)');ax.set_title('Face partition: nominal and taller designs have the same areas');ax.grid(axis='x',alpha=.2);ax.legend(loc='lower right',fontsize=8)
for ext in ('png','pdf'):fig.savefig(R/f'reports/current/figures/v322_gas_face_partition.{ext}',dpi=180)
