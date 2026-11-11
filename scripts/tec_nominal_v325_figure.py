"""Original saved P1 field samples and conditional partial-cavity link heats."""
from pathlib import Path
import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_p1_20261111';o=json.loads((D/'p1_operator.json').read_text());a=json.loads((D/'coupled_attempt01/independent_audit.json').read_text());assert a['status'].startswith('PASS');pairs=o['pairs'];q=o['saved_field_results']['0.8']['pair_heat_hot_to_cold_W'];idx=[i for i,p in enumerate(pairs) if p['stage']==0];poly=[pairs[i]['polygon_xy_mm'] for i in idx];values=np.array([q[i]*1000/pairs[i]['area_mm2'] for i in idx]);fig,axes=plt.subplots(1,2,figsize=(8.5,3.3),constrained_layout=True)
c=PolyCollection(poly,array=values,cmap='viridis',edgecolors='none');axes[0].add_collection(c);axes[0].autoscale_view();axes[0].set_aspect('equal');axes[0].set(xlabel='x (mm)',ylabel='y (mm)',title='C0–C1 selected patches: saved field');fig.colorbar(c,ax=axes[0],label='Local heat flux (mW/mm²)',shrink=.8)
st=np.arange(3);old=np.array(o['saved_field_results']['0.8']['stage_heat_hot_to_cold_W'])*1000;new=np.array(a['gas_links_W'])*1000;axes[1].bar(st-.19,old,width=.36,label='Saved-field P1');axes[1].bar(st+.19,new,width=.36,label='Partial-cavity coupled');axes[1].set(xticks=st,xticklabels=['C0–C1','C1–C2','C2–C3'],ylabel='Hot-to-cold gas heat (mW)',title='Selected gas subset; α = 0.8');axes[1].grid(axis='y',alpha=.2);axes[1].legend(fontsize=8)
for e in ('png','pdf'):fig.savefig(R/f'reports/current/figures/v325_nominal_p1_gas.{e}',dpi=190,**({'metadata':{'CreationDate':None,'ModDate':None}} if e=='pdf' else {}))
