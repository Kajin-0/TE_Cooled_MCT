"""V3.8 hardware-material and mounting-sink figures, frozen accepted source solves only."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_8_rev3_transport_and_sink_20261109'
OUT=ROOT/'reports/current/figures'
MATERIALS=[('Seebeck ±10%','S090_I040','S110_I040'),
           ('P/N resistivity ±20%','rho080_I040','rho120_I040'),
           ('P/N thermal k ±20%','k080_I040','k120_I040')]
SINK40=['base_I040','sink_plus05_I040','sink_plus10_I040']
SINK55=['sink_plus05_I055','sink_plus10_I055']
def get(n):
 p=D/n
 d=json.loads((p/'result.json').read_text())
 a=json.loads((p/'independent_energy_audit.json').read_text())
 assert a['verdict'].startswith('PASS V3.8')
 assert hashlib.sha256((p/'result.json').read_bytes()).hexdigest()==a['result_sha256']
 assert abs(a['global_energy_residual_W'])<2e-9
 return d
def save(fig,name):
 for ext in ('pdf','png'):
  p=OUT/f'{name}.{ext}'
  fig.savefig(p,dpi=205,bbox_inches='tight',
              **({'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}))
  print(p.relative_to(ROOT))
 plt.close(fig)
def plot():
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,
                      'axes.spines.top':False,'axes.spines.right':False})
 base=get('base_I040');baseT=base['calculated_detector_temperature_K'];baseP=base['electrical_power_W']
 fig=plt.figure(figsize=(10.8,5.0),facecolor='white')
 ax=fig.add_axes([.26,.24,.68,.57])
 y=np.arange(3)
 for i,(label,low,high) in enumerate(MATERIALS):
  a=get(low);b=get(high)
  dx=np.array([a['calculated_detector_temperature_K']-baseT,b['calculated_detector_temperature_K']-baseT])
  ax.plot(dx,[i,i],lw=2,color='#b0bfcb',zorder=1)
  for x,c,mark in zip(dx,['#286a88','#b87342'],['o','D']):
   ax.scatter([x],[i],s=71,marker=mark,color=c,zorder=3)
   ax.annotate(f'{x:+.2f} K',(x,i),textcoords='offset points',xytext=(0,10),
               ha='center',fontsize=8.7,color='#31495e')
 ax.axvline(0,ls='--',lw=1.2,color='#506b7d')
 ax.set_yticks(y,[a[0] for a in MATERIALS])
 ax.invert_yaxis();ax.set_xlim(-14,15)
 ax.set_xticks([-12,-8,-4,0,4,8,12])
 ax.set_xlabel('Detector temperature change from nominal V3.7 (K)')
 ax.grid(axis='x',alpha=.16)
 fig.text(.055,.955,'Rev3 material sensitivity repeated on the source-geometry TEC',fontsize=15.2,fontweight='bold',color='#21394e')
 fig.text(.055,.903,'Unchanged V3.7 detector bias, package geometry, copper multiport and original ceramic 3D meshes',fontsize=9.9,color='#56697a')
 fig.text(.26,.12,'Blue circle: lower material scale   •   Orange diamond: upper material scale',fontsize=9.1,color='#435a6b')
 fig.text(.055,.067,'Independent complete nonlinear 88-leg / four-ceramic solutions. Endpoint spans depend on chosen hypothesis widths.',fontsize=8.9,color='#607184')
 save(fig,'v38_source_material_response')
 val40=[get(n) for n in SINK40]
 val55=[get(n) for n in SINK55]
 fig=plt.figure(figsize=(10.2,5.1),facecolor='white')
 ax=fig.add_axes([.13,.23,.76,.59])
 extra=[0,5,10]
 ax.plot(extra,[v['calculated_detector_temperature_K'] for v in val40],
         '-o',color='#276384',lw=2,ms=7,label='TEC current 0.40 A')
 ax.plot([5,10],[v['calculated_detector_temperature_K'] for v in val55],
         '-s',color='#b37346',lw=2,ms=7,label='TEC current 0.55 A')
 for i,z in zip(extra,val40):
  ax.annotate(f'{z["calculated_detector_temperature_K"]:.2f} K',(i,z['calculated_detector_temperature_K']),
              textcoords='offset points',xytext=(0,11),ha='center',fontsize=9,color='#215b78')
 for i,z in zip((5,10),val55):
  ax.annotate(f'{z["calculated_detector_temperature_K"]:.2f} K',(i,z['calculated_detector_temperature_K']),
              textcoords='offset points',xytext=(0,11),ha='center',fontsize=9,color='#96532f')
 ax.set_xticks(extra);ax.set_xlabel('Additional mounting thermal resistance (K/W)')
 ax.set_ylabel('Full-system detector operating temperature (K)')
 ax.grid(alpha=.20);ax.legend(loc='center left',frameon=False)
 fig.text(.10,.945,'Worse mounting path raises the HgCdTe operating temperature',fontsize=14.6,fontweight='bold',color='#21394e')
 fig.text(.10,.893,'Existing 4.833 K/W source package resistance retained; x-axis is extra mounting resistance only',fontsize=9.8,color='#56697a')
 fig.text(.10,.075,'All points include 0.866 V detector self-heating, 0.5 mW absorbed heat, 100 Pa Kr and original 3D ceramic solves.',fontsize=8.7,color='#607184')
 save(fig,'v38_package_sink_temperature')
 summary={'source':'V3.8 complete original source geometry, 88 nonlinear P/N legs, full 3D ceramic FEM and detector bias feedback',
          'base_external_sink_R_K_W':base['base_external_sink_R_K_W'],
          'base_Tdie_K':baseT,'base_TEC_input_W':baseP,
          'material_endpoints':[],'mounting_cases':[]}
 for label,a,b in MATERIALS:
  low=get(a);high=get(b)
  summary['material_endpoints'].append({'name':label,'low_case':a,'high_case':b,
       'low_T_K':low['calculated_detector_temperature_K'],'high_T_K':high['calculated_detector_temperature_K'],
       'low_T_delta_K':low['calculated_detector_temperature_K']-baseT,
       'high_T_delta_K':high['calculated_detector_temperature_K']-baseT,
       'endpoint_T_span_K':abs(low['calculated_detector_temperature_K']-high['calculated_detector_temperature_K']),
       'low_P_W':low['electrical_power_W'],'high_P_W':high['electrical_power_W']})
 for case in [*SINK40,*SINK55]:
  d=get(case)
  summary['mounting_cases'].append({'case':case,'TEC_current_A':d['operating_current_A'],
       'added_sink_R_K_W':d['additional_external_sink_R_K_W'],'total_sink_R_K_W':d['total_external_sink_R_K_W'],
       'Tdie_K':d['calculated_detector_temperature_K'],'P_TEC_W':d['electrical_power_W']})
 (D/'accepted_source_material_and_mounting_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print('Summary saved.')
if __name__=='__main__':plot()
