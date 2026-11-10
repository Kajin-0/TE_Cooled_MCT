"""Plot archived-field source-column subset only; no prediction of whole package."""
from pathlib import Path
import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_coupler_20261110';p=json.loads((D/'source_bare_column_subset.json').read_text());x=json.loads((D/'source_field_subset_exchange.json').read_text())
plt.rcParams.update({'font.size':8,'pdf.fonttype':42});fig,ax=plt.subplots(1,2,figsize=(8.5,3.3),constrained_layout=True);st=np.arange(3);names=['C0–C1','C1–C2','C2–C3'];areas=[z['unobstructed_column_area_mm2'] for z in p['patches']]
ax[0].bar(st,areas,color='#6a91aa');ax[0].set(xticks=st,xticklabels=names,ylabel='Unblocked area (mm²)',title='Selected bare-face columns');ax[0].grid(axis='y',alpha=.2)
for i,a in enumerate(('0.5','0.8','1.0')):ax[1].bar(st+(i-1)*.23,[v*1000 for v in x['summary'][a]['link_W']],width=.22,label='α = '+a)
ax[1].set(xticks=st,xticklabels=names,ylabel='Hot-to-cold gas heat (mW)',title='Saved ceramic fields; no new solve');ax[1].grid(axis='y',alpha=.2);ax[1].legend(fontsize=8)
for e in ('png','pdf'):fig.savefig(R/f'reports/current/figures/v324_nominal_gas_subset.{e}',dpi=190,**({'metadata':{'CreationDate':None,'ModDate':None}} if e=='pdf' else {}))
