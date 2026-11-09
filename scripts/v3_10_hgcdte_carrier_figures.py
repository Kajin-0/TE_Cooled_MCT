"""V3.10 semiconductor composition vs real coupled TEC: source-registry plots."""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_10_hgcdte_carrier_20261109'
OUT=ROOT/'reports/current/figures'
CASES=('lw_x020','x022','x024','mw_x029')
def accept(case):
 p=D/case
 d=json.loads((p/'result.json').read_text())
 aud=json.loads((p/'independent_energy_audit.json').read_text())
 assert aud['verdict'].startswith('PASS V3.10')
 assert aud['result_sha256']==hashlib.sha256((p/'result.json').read_bytes()).hexdigest()
 return d,d['source_HgCdTe_electrothermal_at_T']
def main():
 r=[accept(n) for n in CASES]
 x=np.array([h['composition_x'] for _,h in r])
 R=np.array([h['dark_resistance_ohm'] for _,h in r])
 temp=np.array([d['calculated_detector_temperature_K'] for d,_ in r])
 power=np.array([h['detector_bias_Joule_W']*1000 for _,h in r])
 cut=np.array([h['idealized_Eg_cutoff_um'] for _,h in r])
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,
     'axes.spines.top':False,'axes.spines.right':False})
 fig=plt.figure(figsize=(11.6,5.3),facecolor='white')
 a=fig.add_axes([.08,.245,.38,.54])
 b=fig.add_axes([.59,.245,.34,.54])
 a.plot(x,R,'o-',color='#275f7d',lw=2,ms=7)
 a.set_yscale('log');a.set_xlabel('Cd composition x');a.set_ylabel('Bulk channel dark resistance (Ω)')
 a.set_xticks(x);a.grid(axis='y',alpha=.2)
 a.set_title('Composition changes dark resistance',loc='left',fontsize=11,weight='bold')
 for xi,ri in zip(x,R):
  a.annotate(f'{ri:,.0f} Ω',(xi,ri),xytext=(0,10),textcoords='offset points',ha='center',fontsize=8.7)
 b.plot(x,power,'o-',color='#aa7044',lw=2,ms=7,label='Joule power')
 b.set_xticks(x);b.set_xlabel('Cd composition x');b.set_ylabel('HgCdTe Joule heating (mW)')
 b.grid(axis='y',alpha=.2)
 b.set_title('Same applied 0.35 V detector bias',loc='left',fontsize=11,weight='bold')
 for xi,pi in zip(x,power):
  b.annotate(f'{pi:.3f}',(xi,pi),xytext=(0,11),textcoords='offset points',ha='center',fontsize=8.8,color='#91562f')
 fig.text(.075,.955,'HgCdTe composition changes electrical heat load on the TEC',fontsize=15.2,weight='bold',color='#243e51')
 fig.text(.075,.898,'Unmeasured 400 × 100 × 10 µm bulk channel; acceptors 10¹⁶ cm⁻³, μₑ/μₕ = 100',fontsize=9.6,color='#566a7b')
 fig.text(.075,.092,'μₕ assumptions: 450 / 450 / 400 / 220 cm²/(V·s) for x = 0.20 / 0.22 / 0.24 / 0.29.',fontsize=8.7,color='#677789')
 fig.text(.075,.058,'No measured grade, contacts, field-dependent mobility, photoresponse, surface shunts or validated detectivity.',fontsize=8.7,color='#677789')
 for ext in ('png','pdf'):
  path=OUT/f'v310_composition_resistance_and_joule.{ext}'
  fig.savefig(path,bbox_inches='tight',**({'dpi':205} if ext=='png' else {'metadata':{'CreationDate':None,'ModDate':None}}))
  print(path)
 plt.close(fig)
 fig=plt.figure(figsize=(10.7,5.0),facecolor='white')
 a=fig.add_axes([.105,.245,.70,.56])
 a.plot(x,temp,'o-',lw=2,color='#2b657f',ms=7)
 for xi,ti in zip(x,temp):
  a.annotate(f'{ti:.3f} K',(xi,ti),xytext=(0,11),textcoords='offset points',ha='center',fontsize=9)
 a.set_xlabel('Cd composition x');a.set_ylabel('Fully coupled detector temperature (K)')
 a.set_xticks(x);a.grid(axis='y',alpha=.2)
 fig.text(.10,.95,'Detector self-heating feeds back into the complete TEC',fontsize=15.3,weight='bold',color='#243e51')
 fig.text(.10,.89,'Fixed 0.400 A TEC / 300 K sink / 100 Pa krypton; 0.35 V photoconductor bias',fontsize=9.7,color='#566a7b')
 fig.text(.10,.09,'Compared alloy compositions also use different assumed mobilities. This is not an isolated x-only material experiment.',fontsize=8.8,color='#677789')
 for ext in ('png','pdf'):
  path=OUT/f'v310_coupled_detector_temperature.{ext}'
  fig.savefig(path,bbox_inches='tight',**({'dpi':205} if ext=='png' else {'metadata':{'CreationDate':None,'ModDate':None}}))
  print(path)
 plt.close(fig)
 allnames=('off_x020',*CASES,'lw_x020_highbias','lw_x020_lowdoping')
 summary={'science_status':'HYPOTHESIS composition-aware equilibrium carrier model, uncalibrated HgCdTe channel; source TEC numerical results independently energy-audited','cases':[]}
 for name in allnames:
  d,h=accept(name)
  summary['cases'].append({'case':name,'composition_x':h['composition_x'],'Eg_eV':h['bandgap_eV'],
    'idealized_Eg_cutoff_um':h['idealized_Eg_cutoff_um'],'net_ionized_acceptors_cm3':h['net_ionized_acceptors_cm3'],
    'mu_h_cm2_Vs':h['hole_mobility_cm2_Vs'],'intrinsic_cm3':h['intrinsic_carriers_cm3'],
    'dark_resistance_ohm':h['dark_resistance_ohm'],'detector_current_A':h['detector_dark_current_A'],
    'Joule_W':h['detector_bias_Joule_W'],'Tdie_K':d['calculated_detector_temperature_K'],
    'TEC_electrical_input_W':d['electrical_power_W'],'johnson_voltage_V_sqrtHz':h['johnson_voltage_V_sqrtHz'],
    'source_sha256':d['solver_source_sha256'],
    'result_sha256':hashlib.sha256((D/name/'result.json').read_bytes()).hexdigest()})
 (D/'accepted_carrier_results_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print('Seven accepted carrier-state summaries saved')
if __name__=='__main__':main()
