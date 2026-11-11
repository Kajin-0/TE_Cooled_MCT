"""Plot actual saved source multiport nodes and conditional 1D foil profiles."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tecooledmct.nominal_cavity_metal_v326 import segment_profile
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_metal_v326_20261111';r=json.loads((R/'data/nominal_gas_p1_20261111/coupled_attempt01/result.json').read_text());I=r['operating_current_A'];nets=r['Cu_form_tab_electrothermal_result']['net_details'];fig,ax=plt.subplots(figsize=(7.6,3.5),layout='constrained')
for net,c in [('58','#0072b2'),('80','#d55e00'),('88','#009e73')]:
 n=nets[net];offset=0
 for j,(L,g,rr) in enumerate(zip(n['segment_length_m'],n['thermal_segment_conductance_W_K'],n['metal_electrical_segment_R_ohm'])):
  us=np.linspace(0,1,100);x=offset+us*L*1e3;y=[segment_profile(u,*n['foil_node_temperature_K'][j:j+2],rr,g,I)[0] for u in us];ax.plot(x,y,color=c,lw=2,label=f'Net {net}' if j==0 else None);offset+=L*1e3
 xs=np.r_[0,np.cumsum(n['segment_length_m'])]*1e3;ax.scatter(xs,n['foil_node_temperature_K'],facecolors='white',edgecolors=c,zorder=3,s=27)
ax.set(xlabel='Distance along foil between joint centers (mm)',ylabel='Conditional foil temperature (K)',title='Original source copper: saved nodes and 1D reconstruction');ax.grid(alpha=.22);ax.legend(frameon=False,ncol=3,loc='upper right');p=R/'reports/current/figures/v326_source_tab_temperature';fig.savefig(str(p)+'.pdf',metadata={'CreationDate':None,'ModDate':None});fig.savefig(str(p)+'.png',dpi=190,metadata={'Software':'Matplotlib'});plt.close(fig)
