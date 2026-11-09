"""V3.11 numerical Rev3 backfill replication figures, source-verified."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_11_rev3_backfill_source_20261109'
OUT=ROOT/'reports/current/figures'
CASES=('vacuum_I040','Kr100_I040','Kr30k_I040','Kr101k_I040','Ar30k_I040','N2_30k_I040','N2_101k_I040','Kr30k_I055')
def get(c):
 p=D/c
 d=json.loads((p/'result.json').read_text())
 a=json.loads((p/'independent_energy_audit.json').read_text())
 assert a['verdict'].startswith('PASS V3.11')
 assert a['result_sha256']==hashlib.sha256((p/'result.json').read_bytes()).hexdigest()
 return d
def save(fig,name):
 for ext in ('png','pdf'):
  p=OUT/f'{name}.{ext}'
  fig.savefig(p,bbox_inches='tight',**({'dpi':205} if ext=='png' else {'metadata':{'CreationDate':None,'ModDate':None}}))
  print(p.relative_to(ROOT))
 plt.close(fig)
def main():
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.2,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
 d={n:get(n) for n in CASES}
 b=d['Kr100_I040']
 fig=plt.figure(figsize=(10.8,5.6),facecolor='white')
 ax=fig.add_axes([.11,.24,.74,.54])
 names=['Vacuum','Kr · 100 Pa','Kr · 30 kPa','Kr · 101 kPa','Ar · 30 kPa','N₂ · 30 kPa','N₂ · 101 kPa']
 cases=['vacuum_I040','Kr100_I040','Kr30k_I040','Kr101k_I040','Ar30k_I040','N2_30k_I040','N2_101k_I040']
 T=np.array([d[n]['calculated_detector_temperature_K'] for n in cases])
 dy=T-b['calculated_detector_temperature_K']
 cols=['#326c83' if x<-.001 else '#bd8657' if x>.001 else '#757d85' for x in dy]
 y=np.arange(len(T))
 ax.barh(y,dy,color=cols,height=.6)
 ax.set_yticks(y,names);ax.invert_yaxis()
 ax.axvline(0,color='#34495b',lw=1)
 ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
 ax.set_xlabel('Detector mounting temperature change relative to 100 Pa Kr (K)')
 ax.set_xlim(min(dy)-.22,max(dy)+.25)
 for i,(x,t) in enumerate(zip(dy,T)):
  if x < -.001:
   ax.text(x/2,i,f'{x:+.3f} K',va='center',ha='center',fontsize=8.8,color='white',weight='bold')
  else:
   ax.annotate(f'{x:+.3f} K  |  {t:.3f} K',(x,i),xytext=(7,0),
    textcoords='offset points',va='center',ha='left',fontsize=8.7)
 fig.text(.08,.952,'Gas backfill changes the cooled device temperature',weight='bold',fontsize=15.3,color='#213b4e')
 fig.text(.08,.900,'Same source TEC and TO package  |  0.400 A TEC  |  2.0 mW fixed die heat  |  300 K reservoir',fontsize=9.6,color='#596e7e')
 fig.text(.08,.080,'Cavity treatment: four effective gas-surface branches, 3 mm gap and 0.8 accommodation; NOT native gas CFD.',fontsize=8.7,color='#65788b')
 fig.text(.08,.048,'Old Rev3 geometry/results excluded; all plotted points re-solved with the physical 29/11/4-source cooler.',fontsize=8.7,color='#65788b')
 save(fig,'v311_backfill_species_pressure_cold_temperature')
 fig=plt.figure(figsize=(10.1,5.3),facecolor='white')
 a=fig.add_axes([.12,.24,.75,.56])
 pressures=np.array([0,100,30000,101325],dtype=float)
 t=np.array([d[c]['calculated_detector_temperature_K'] for c in ('vacuum_I040','Kr100_I040','Kr30k_I040','Kr101k_I040')])
 gs=np.array([1000*sum(d[c]['cavity_gas_heat_into_three_ceramics_and_die_W']) for c in ('vacuum_I040','Kr100_I040','Kr30k_I040','Kr101k_I040')])
 a.plot(np.arange(4),t,'o-',color='#286880',ms=7,lw=2)
 a.set_xticks(np.arange(4),['Vacuum','100 Pa','30 kPa','101 kPa'])
 a.set_ylabel('Detector-mounting temperature (K)')
 a.grid(axis='y',alpha=.2)
 for i,x in enumerate(t):a.annotate(f'{x:.3f} K',(i,x),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9)
 fig.text(.105,.952,'Krypton pressure response is strongly nonlinear',weight='bold',fontsize=15.3,color='#213b4e')
 fig.text(.105,.896,'Fixed 0.400 A TEC; solid-body heat paths and detector thermal load unchanged',fontsize=9.8,color='#596e7e')
 fig.text(.105,.086,'Even a nominal 100 Pa can yield substantial gas leakage with this assumed gap and accommodation model.',fontsize=8.9,color='#66798c')
 fig.text(.105,.054,'The shape is model-form dependent: actual TO cavity, inter-pellet gaps and line-of-sight paths unresolved.',fontsize=8.9,color='#66798c')
 save(fig,'v311_krypton_pressure_sensitivity')
 summary={'science_status':'Conditional NIST Eucken Fourier-to-free-molecular gas model, current full source TEC; NO native cavity PDE', 'baseline_reference_case':'Kr100_I040','cases':[]}
 for n in CASES:
  x=d[n];summary['cases'].append({'case':n,'gas':x['cavity_gas_species'],'pressure_Pa':x['cavity_pressure_Pa'],
   'current_A':x['operating_current_A'],'detector_mount_K':x['calculated_detector_temperature_K'],
   'cold_ceramic_K':x['source_full_temperature_nodes_K']['stage2_cold'],
   'hot_ceramic_K':x['source_full_temperature_nodes_K']['stage0_hot'],
   'TEC_voltage_V':x['terminal_voltage_V'],'TEC_power_W':x['electrical_power_W'],
   'gas_heat_into_cold_source_W':sum(x['cavity_gas_heat_into_three_ceramics_and_die_W']),
   'rad_heat_into_cold_source_W':sum(x['gray_radiation_heat_into_three_ceramics_and_die_W']),
   'sink_Q_W':x['bath_heat_rejected_W']})
 (D/'accepted_gas_pressure_source_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print('Saved eight independently audited source operating states')
if __name__=='__main__':main()
