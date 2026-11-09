"""Source-provenance V3.7 HgCdTe bias heat and assumed resistance slope."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tecooledmct.hgcdte_bias_proxy import photoconductor_at_T
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_7_hgcdte_electrothermal_20261109'
OUT=ROOT/'reports/current/figures'
NAMES=('zero_bias','reference_match','bias_1p2V','bias_1p5V')
def load(n):
 p=D/n;d=json.loads((p/'result.json').read_text());a=json.loads((p/'independent_energy_audit.json').read_text())
 assert a['verdict'].startswith('PASS V3.7')
 assert a['result_sha256']==hashlib.sha256((p/'result.json').read_bytes()).hexdigest()
 return d
dat=[load(s) for s in NAMES]
x=np.array([r['source_HgCdTe_electrothermal_at_T']['voltage_V'] for r in dat])
T=np.array([r['calculated_detector_temperature_K'] for r in dat])
P=np.array([1000*r['source_HgCdTe_bias_heat_W'] for r in dat])
R=np.array([r['source_HgCdTe_electrothermal_at_T']['dark_resistance_ohm'] for r in dat])
assert np.all(np.diff(x)>0) and np.all(np.diff(T)>0)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(11.5,5.2),facecolor='white')
ax=fig.add_axes([.075,.23,.40,.56])
ax2=fig.add_axes([.60,.23,.36,.56])
ax.plot(x,T,'o-',color='#245d7d',ms=7,lw=1.9)
ax.set_xlim(-.12,1.66);ax.set_ylim(T.min()-.23,T.max()+.33)
ax.set_xticks(x);ax.set_xlabel('Applied HgCdTe detector bias (V)')
ax.set_ylabel('Coupled detector temperature (K)')
ax.grid(axis='y',alpha=.22)
ax.set_title('Detector operating temperature',loc='left',weight='bold')
for a,b in zip(x,T):ax.annotate(f'{b:.3f} K',(a,b),xytext=(0,11),textcoords='offset points',ha='center',fontsize=8.6,color='#234a61')
ax2.plot(x,P,'o-',color='#ae7144',ms=7,lw=1.9)
ax2.set_xlim(-.12,1.66);ax2.set_ylim(-.25,P.max()+.8)
ax2.set_xticks(x);ax2.set_xlabel('Applied HgCdTe detector bias (V)')
ax2.set_ylabel('Calculated detector Joule heating (mW)')
ax2.grid(axis='y',alpha=.22)
ax2.set_title('Temperature-dependent bias power',loc='left',weight='bold')
for a,b in zip(x,P):ax2.annotate(f'{b:.3f}',(a,b),xytext=(0,11),textcoords='offset points',ha='center',fontsize=8.6,color='#86502c')
fig.text(.075,.955,'HgCdTe bias heating coupled to the three-stage TEC',fontsize=16.4,fontweight='bold',color='#21384d')
fig.text(.075,.895,'0.400 A TEC  |  300 K mounting reservoir  |  100 Pa krypton  |  absorbed optical heat = 0.50 mW',fontsize=9.6,color='#52687b')
fig.text(.075,.087,'Electrical proxy: R(218.90 K) = 500 Ω; effective activation 30 meV. These are unmeasured design assumptions.',fontsize=8.6,color='#60758a')
fig.text(.075,.055,'Each point is a nonlinear, separately audited whole-device solution; no responsivity, noise or measured detector I–V.',fontsize=8.6,color='#60758a')
for ext in ('pdf','png'):
 p=OUT/f'v37_hgcdte_bias_temperature.{ext}'
 if ext=='pdf':fig.savefig(p,bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
 else:fig.savefig(p,bbox_inches='tight',dpi=205)
 print(p.relative_to(ROOT),p.stat().st_size)
plt.close(fig)
fig=plt.figure(figsize=(9.8,4.75),facecolor='white')
ax=fig.add_axes([.095,.24,.78,.57])
t=np.linspace(200,240,160)
for E,c in ((.03,'#245d7d'),(.06,'#ab7043')):
    z=np.array([photoconductor_at_T(float(v),1.2,.0005,500,218.90002402868413,E)['dark_resistance_ohm'] for v in t])
    ax.plot(t,z,lw=2.0,color=c,label=f'Effective E = {E*1e3:.0f} meV')
ax.scatter([218.90002402868413],[500],s=54,color='#26374b',zorder=4)
ax.set_xlabel('Detector temperature (K)');ax.set_ylabel('Assumed dark resistance (Ω)')
ax.grid(alpha=.2);ax.legend(frameon=False)
fig.text(.094,.955,'Unmeasured resistance-law hypotheses',fontsize=15.7,fontweight='bold',color='#21384d')
fig.text(.094,.899,'Reference 500 Ω at 218.900 K; activated slope is not HgCdTe bandgap or validated detector transport.',fontsize=9.4,color='#52687b')
fig.text(.095,.095,'These curves illustrate parameter sensitivity only. Real HgCdTe R(T) depends on alloy composition, doping, mobility and contacts.',fontsize=8.8,color='#60758a')
for ext in ('pdf','png'):
 p=OUT/f'v37_detector_resistance_hypotheses.{ext}'
 if ext=='pdf':fig.savefig(p,bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
 else:fig.savefig(p,bbox_inches='tight',dpi=205)
 print(p.relative_to(ROOT),p.stat().st_size)
plt.close(fig)
summary={'source':'registered unmeasured detector R(T) design assumptions coupled into frozen V3.6 TEC physical model',
'input_conditions':{'TEC_current_A':.4,'ambient_K':300.,'gas_Pa':100.,'absorbed_optical_W':.0005,'Rref_ohm':500.,'Tref_K':218.90002402868413,'Eeff_eV':.03},
'cases':[]}
for n in (*NAMES,'bias_1p2V_high_activation'):
 d=load(n);z=d['source_HgCdTe_electrothermal_at_T']
 summary['cases'].append({'name':n,'voltage_V':z['voltage_V'],'activation_eV':z['effective_activation_eV'],
 'temperature_K':d['calculated_detector_temperature_K'],'R_ohm':z['dark_resistance_ohm'],
 'detector_dark_current_A':z['detector_dark_current_A'],
 'detector_Joule_W':z['detector_bias_Joule_W'],'Pabsorbed_W':z['absorbed_optical_heat_W'],
 'Pdet_total_W':z['total_applied_detector_heat_W'],'TEC_input_W':d['electrical_power_W'],
 'small_gain_311K_per_W_proxy':d['source_HgCdTe_electrothermal_small_gain_proxy'],
 'result_sha256':hashlib.sha256((D/n/'result.json').read_bytes()).hexdigest(),
 'solver_source_sha256':d['solver_source_sha256']})
(D/'accepted_biased_operating_points.json').write_text(json.dumps(summary,indent=2)+'\n')
print('SUMMARY 5 cases saved')
