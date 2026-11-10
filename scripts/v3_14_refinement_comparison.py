#!/usr/bin/env python3
"""Read-only V3.14 full 16-cut strict raw-current comparison and plot."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'data/v3_gate_B_original_P2_20261106/attempt01/P2_coupon_result.json'
NEW=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/attempt01/P2_candidate_h035_result.json'
MESH=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/fine35/mesh_audit.json'
AUD=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/attempt01/independent_readback.json'
OUT=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/refinement_comparison.json'
FIG=ROOT/'reports/current/figures/v314_all_raw_current_cuts'
def load(p):return json.loads(p.read_text())
def ident(r):
  return ' / '.join(r['pair']) if 'pair' in r else 'terminal '+str(r['terminal']) if 'terminal' in r else r['interior']
def main():
  old,new,mesh,aud=map(load,(OLD,NEW,MESH,AUD))
  assert len(old['P2_cuts'])==len(new['P2_cuts'])==16
  assert mesh['tets']==47277
  assert 'PASS independently reconstructed' in aud['status']
  assert abs(aud['max_reconstruction_disagreement_rel'])<2e-11
  assert old['status'].startswith('STOP') and new['status'].startswith('STOP')
  assert old['current_gate_limit']==new['current_gate_limit']==.001
  assert old['P2_raw_cuts_failing_count']==new['P2_raw_cuts_failing_count']==11
  assert new['P2_raw_cut_max_relative_error']>new['current_gate_limit']
  a={ident(r):r for r in old['P2_cuts']};b={ident(r):r for r in new['P2_cuts']}
  assert set(a)==set(b)
  rows=[]
  for name,r in b.items():
    rows.append(dict(physical_cut=name,original_P2_relative=a[name]['gate_error'],
     fine_P2_relative=r['gate_error'],delta_percentage_points=100*(r['gate_error']-a[name]['gate_error']),
     new_pass=r['gate_error']<=new['current_gate_limit']))
  improved=sum(r['fine_P2_relative']<r['original_P2_relative'] for r in rows)
  worsened=sum(r['fine_P2_relative']>r['original_P2_relative'] for r in rows)
  rec={
   'result':'FAIL/STOP source-CAD finer P2 local electrical Gate B',
   'project':'TEC/TO physical package; local net88/lead9 coupon only',
   'original_geometric_mesh_h_mm':.045,'new_geometric_mesh_h_mm':.035,
   'original_tetrahedra':28691,'new_tetrahedra':mesh['tets'],
   'original_P2_dofs':58993,'new_P2_dofs':92495,
   'original_reduced_resistance_ohm':old['P2_R_coupon_ohm'],
   'new_reduced_resistance_ohm':new['P2_R_coupon_ohm'],
   'resistance_rel_delta':new['P2_R_coupon_ohm']/old['P2_R_coupon_ohm']-1,
   'original_worst_cut_error_pct':100*old['P2_raw_cut_max_relative_error'],
   'new_worst_cut_error_pct':100*new['P2_raw_cut_max_relative_error'],
   'worst_cut_relative_reduction_pct':100*(1-new['P2_raw_cut_max_relative_error']/old['P2_raw_cut_max_relative_error']),
   'current_cut_acceptance_pct':.1,
   'new_worst_over_limit_factor':new['P2_raw_cut_max_relative_error']/.001,
   'original_failing_cuts':old['P2_raw_cuts_failing_count'],
   'new_failing_cuts':new['P2_raw_cuts_failing_count'],
   'strictly_improved_cut_count':improved,'strictly_worsened_cut_count':worsened,
   'new_voltage_min_V':new['P2_minimum_voltage_V'],
   'voltage_bound_min_allowed_V':-1e-8,
   'voltage_gate_pass':new['P2_minimum_voltage_V']>=-1e-8,
   'new_IV_loss_mismatch_rel':new['P2_IV_minus_losses_relative'],
   'new_algebraic_relative_residual':new['solver']['true_reduced_relative_residual'],
   'source_mesh_volume_vs_CAD_rel':mesh['mesh_volume_m3']/mesh['CAD_volume_m3']-1,
   'new_independent_contact_readback_max_rel':aud['max_reconstruction_disagreement_rel'],
   'interpretation':'Higher spatial resolution reduced some raw interfacial errors but not all. 3D electrical gate still fails; exact cause cannot be attributed solely to mesh refinement. FEM weak energy balance is not raw contact-flux qualification.',
   'new_thermal_FEM_solves':0,'new_spatial_Joule_FEM_solves':0,
   'original_mesh_fields_immutable':True,
   'cutwise_results':rows,
   'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (OLD,NEW,MESH,AUD)},
  }
  plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
  sorted_rows=sorted(rows,key=lambda r:r['fine_P2_relative'],reverse=True)
  names=[r['physical_cut'].replace(' / ',' → ') for r in sorted_rows]
  y=np.arange(len(sorted_rows));fig,ax=plt.subplots(figsize=(10.3,7.2))
  fig.subplots_adjust(left=.28,right=.96,bottom=.16,top=.82)
  old_err=np.array([r['original_P2_relative']*100 for r in sorted_rows]);new_err=np.array([r['fine_P2_relative']*100 for r in sorted_rows])
  # Plot zero and near-zero raw-cut errors on a linear axis to avoid distorting 0.1% threshold.
  ax.barh(y-.18,old_err,height=.34,label='Previous P2 / 28,691 TET4',color='#7892a9')
  ax.barh(y+.18,new_err,height=.34,label='New P2 / 47,277 TET4',color='#b2774a')
  ax.axvline(.1,color='#b34643',lw=1.5,ls='--',label='Required maximum: 0.1%')
  ax.set_yticks(y,names);ax.invert_yaxis();ax.set_xlim(0,9.0)
  ax.set_xlabel('Absolute source-normalized raw-current cut mismatch (%)')
  ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
  fig.text(.035,.965,'Native net88/lead9: same 16 current-flux gates, refined spatial mesh',weight='bold',fontsize=14.5,color='#26374b')
  fig.text(.035,.925,'Original CAD, 12 region properties and P2 contact law unchanged; both coupon runs FAIL electrical Gate B',fontsize=9.8,color='#506277')
  fig.legend(loc='upper left',bbox_to_anchor=(.28,.90),frameon=False,ncol=2,fontsize=8.5)
  fig.text(.03,.058,'Zero-current net88 middle landing is retained. Two interior-foil cut errors are near zero and included in the chart.',color='#56697e',fontsize=8.8)
  fig.text(.03,.027,'Independent source-current audits confirm reported values; this is not an experimentally calibrated current distribution.',color='#56697e',fontsize=8.8)
  fig.savefig(str(FIG)+'.pdf',bbox_inches='tight',metadata={'Creator':'V3.14 source-archived cut audit','CreationDate':None,'ModDate':None})
  fig.savefig(str(FIG)+'.png',dpi=195,bbox_inches='tight')
  plt.close(fig)
  rec['figure_sha256']={str((FIG.with_suffix('.'+suf)).relative_to(ROOT)):hashlib.sha256(FIG.with_suffix('.'+suf).read_bytes()).hexdigest() for suf in ('png','pdf')}
  OUT.write_text(json.dumps(rec,indent=2)+'\n')
  print('CUTS IMPROVED',improved,'WORSENED',worsened,'WORST',rec['new_worst_cut_error_pct'],'READBACK',rec['new_independent_contact_readback_max_rel'])
  print('SOURCE',OUT)
if __name__=='__main__':main()
