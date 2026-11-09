"""Matched approximately 218.900 K detector target: independent source-solved V3.8 cases."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_8_rev3_transport_and_sink_20261109'
OUT=ROOT/'reports/current/figures'
NAMES=('base_I040','sink_plus05_matched_refined','sink_plus10_matched_refined')
def get(case):
 p=D/case
 d=json.loads((p/'result.json').read_text())
 a=json.loads((p/'independent_energy_audit.json').read_text())
 assert a['verdict'].startswith('PASS V3.8')
 assert a['result_sha256']==hashlib.sha256((p/'result.json').read_bytes()).hexdigest()
 assert abs(a['global_energy_residual_W'])<2e-9
 assert abs(a['independent_sink_T_closure_K'])<4e-7
 return d
def main():
 d=[get(n) for n in NAMES]
 target=d[0]['calculated_detector_temperature_K']
 extra=np.array([x['additional_external_sink_R_K_W'] for x in d])
 T=np.array([x['calculated_detector_temperature_K'] for x in d])
 I=np.array([x['operating_current_A'] for x in d])
 P=np.array([x['electrical_power_W'] for x in d])
 assert np.array_equal(extra,[0,5,10])
 assert np.max(abs(T-target))<.05,('near target insufficiently matched; do not publish matched comparison',T.tolist())
 assert all(np.diff(I)>0) and all(np.diff(P)>0)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.2,'pdf.fonttype':42,
     'axes.spines.top':False,'axes.spines.right':False})
 fig=plt.figure(figsize=(10.8,5.2),facecolor='white')
 a=fig.add_axes([.095,.24,.365,.57])
 b=fig.add_axes([.59,.24,.36,.57])
 a.plot(extra,P,'o-',lw=2,ms=7,color='#aa7048')
 a.set_xlabel('Additional sink resistance (K/W)')
 a.set_ylabel('TEC electrical input (W)')
 a.set_xticks(extra);a.set_xlim(-.6,10.7)
 a.set_ylim(min(P)-.03,max(P)+.045)
 a.grid(axis='y',alpha=.22)
 a.set_title('Electrical cost of maintaining target',loc='left',weight='bold',fontsize=11)
 for x,y in zip(extra,P):
  a.annotate(f'{y:.3f} W',(x,y),textcoords='offset points',xytext=(0,11),ha='center',fontsize=9,color='#86512e')
 b.plot(extra,I,'o-',lw=2,ms=7,color='#2b6686')
 b.set_xlabel('Additional sink resistance (K/W)')
 b.set_ylabel('Required TEC drive current (A)')
 b.set_xticks(extra);b.set_xlim(-.6,10.7)
 b.set_ylim(min(I)-.01,max(I)+.025)
 b.grid(axis='y',alpha=.22)
 b.set_title('TEC current for the same cold temperature',loc='left',weight='bold',fontsize=11)
 for x,y in zip(extra,I):
  b.annotate(f'{y:.4f} A',(x,y),textcoords='offset points',xytext=(0,11),ha='center',fontsize=9,color='#245b77')
 fig.text(.085,.95,'Mounting penalty at a matched detector operating temperature',fontsize=15.5,
          fontweight='bold',color='#243c50')
 fig.text(.085,.892,f'Target Tdet = {target:.3f} K  |  Maximum actual departure = {np.max(abs(T-target)):.3f} K',
          fontsize=9.7,color='#526779')
 fig.text(.085,.09,'Full 88-leg, four-ceramic 3D and copper-coupled solutions; source Rext 4.833 K/W retained plus stated extra.',
          fontsize=8.8,color='#637689')
 fig.text(.085,.055,'Fixed 0.866 V detector bias and assumed optical heat 0.5 mW; provisional P/N and mounting properties.',
          fontsize=8.8,color='#637689')
 for ext in ('png','pdf'):
  p=OUT/f'v38_matched_detector_temperature_power.{ext}'
  kw={'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {'dpi':205}
  fig.savefig(p,bbox_inches='tight',**kw)
  print(p.relative_to(ROOT),p.stat().st_size)
 plt.close(fig)
 summary={'source':'true full-system 3D original ceramic and nonlinear P/N runs, near matched temperature',
 'reference_T_K':target,'maximum_target_error_K':float(np.max(abs(T-target))),
 'cases':[]}
 for name,z in zip(NAMES,d):
  summary['cases'].append({'case':name,'additional_sink_R_K_W':z['additional_external_sink_R_K_W'],
    'total_sink_R_K_W':z['total_external_sink_R_K_W'],
    'TEC_current_A':z['operating_current_A'],'detector_T_K':z['calculated_detector_temperature_K'],
    'target_deviation_K':z['calculated_detector_temperature_K']-target,
    'TEC_input_W':z['electrical_power_W'],
    'relative_TEC_power_increase_percent':100*(z['electrical_power_W']/d[0]['electrical_power_W']-1),
    'result_sha256':hashlib.sha256((D/name/'result.json').read_bytes()).hexdigest()})
 (D/'accepted_matched_temperature_power.json').write_text(json.dumps(summary,indent=2)+'\n')
 print('MATCHED SUMMARY',json.dumps(summary,indent=2))
if __name__=='__main__':main()
