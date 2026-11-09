"""V3.9 source-traceable conditional high-temperature continuation figures."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tecooledmct.nonlinear_tec_v39 import properties
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_9_highT_source_qualification_20261109'
O=ROOT/'reports/current/figures'
def get(sink,f):
 n=f'sink{sink:02}_factor{f:03}'
 p=D/n
 result=json.loads((p/'result.json').read_text())
 audit=json.loads((p/'independent_energy_audit.json').read_text())
 assert audit['verdict'].startswith('PASS V3.9') and audit['result_sha256']==hashlib.sha256((p/'result.json').read_bytes()).hexdigest()
 return result
def main():
 f=[0,25,100];data={sink:[get(sink,i) for i in f] for sink in (0,10)}
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.4,'pdf.fonttype':42,'axes.spines.right':False,'axes.spines.top':False})
 fig=plt.figure(figsize=(11.5,5.3),facecolor='white')
 a=fig.add_axes([.09,.24,.39,.55]);b=fig.add_axes([.60,.24,.34,.55])
 for sink,color,mark in ((0,'#255f7e','o'),(10,'#b37749','s')):
  d=data[sink]
  x=np.array(f,dtype=float)
  T=np.array([z['calculated_detector_temperature_K'] for z in d])
  P=np.array([1000*z['electrical_power_W'] for z in d])
  a.plot(x,T,'-'+mark,color=color,markersize=7,lw=2,label=f'+{sink} K/W external mounting')
  b.plot(x,P,'-'+mark,color=color,markersize=7,lw=2)
 a.set_xlabel('Assumed >300 K terminal-slope multiplier (%)')
 b.set_xlabel('Assumed >300 K terminal-slope multiplier (%)')
 a.set_ylabel('Coupled HgCdTe temperature (K)')
 b.set_ylabel('TEC terminal electrical power (mW)')
 a.set_xticks(f);b.set_xticks(f)
 a.grid(alpha=.2);b.grid(alpha=.2)
 a.legend(frameon=False,loc='best',fontsize=9)
 fig.text(.075,.949,'How much does unmeasured TEC behavior above 300 K affect the detector?',fontweight='bold',fontsize=15,color='#233e50')
 fig.text(.075,.887,'Published source curve unchanged to 300 K; only the tangent continuation beyond 300 K varies.',color='#566b7b',fontsize=9.8)
 fig.text(.075,.083,'0.400 A TEC, 300 K reservoir, 0.866 V HgCdTe bias, 0.5 mW absorbed heat and 100 Pa krypton',color='#637588',fontsize=8.9)
 fig.text(.075,.051,'Hypothesis sensitivity only; not an extrapolation confidence interval, measured grade or calibrated device prediction.',color='#637588',fontsize=8.8)
 for ext in ('png','pdf'):
  path=O/f'v39_high_temperature_source_extrapolation.{ext}'
  fig.savefig(path,bbox_inches='tight',**({'dpi':205} if ext=='png' else {'metadata':{'CreationDate':None,'ModDate':None}}))
  print(path)
 plt.close(fig)
 out={'source':'High-T tangent sensitivity, unchanged source 40-300 K curves; grade unqualified','cases':[]}
 for sink in (0,10):
  for factor,result in zip(f,data[sink]):
   out['cases'].append({'extra_sink_K_W':sink,'continuation_terminal_tangent_percent':factor,
    'Tdie_K':result['calculated_detector_temperature_K'],'TEC_terminal_W':result['electrical_power_W'],
    'TEC_terminal_V':result['terminal_voltage_V'],'stage0_hot_K':result['source_full_temperature_nodes_K']['stage0_hot'],
    'leg_hot_boundary_above_300K_count':result['source_legs_with_hot_boundary_above_300K'],
    'axial_grid_nodes_above_300K_sum':result['source_axial_nodes_above_300K_sum']})
 (D/'source_upper_T_extrapolation_summary.json').write_text(json.dumps(out,indent=2)+'\n')
 print('Study summary recorded')
if __name__=='__main__':main()
