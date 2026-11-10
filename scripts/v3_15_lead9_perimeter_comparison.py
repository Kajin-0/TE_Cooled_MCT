#!/usr/bin/env python3
"""One no-PDE signed-bias/radial decomposition, without changing source gates."""
from pathlib import Path
import hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'data/v3_physical_blocker_closure_20261106/attempt01/lead9_contact_operator_audit.json'
NEW=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/v315_perimeter_readback.json'
ORIGINAL_GATE=ROOT/'data/v3_gate_B_original_P2_20261106/attempt01/P2_coupon_result.json'
FINE_GATE=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/attempt01/P2_candidate_h035_result.json'
OUTPUT=ROOT/'data/v3_15_lead9_perimeter_20261110'
OUTPUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old,new,og,ng=[read(x) for x in (OLD,NEW,ORIGINAL_GATE,FINE_GATE)]
 assert new['no_PDE_or_mesh_changes'] and og['P2_raw_cuts_failing_count']==ng['P2_raw_cuts_failing_count']==11
 assert ng['P2_raw_cut_max_relative_error']>.001
 result={'status':'PASS independent numerical decomposition of saved failed P2 fields; electrical Gate B still FAIL/STOP',
 'scope':'two physical lead9 solder joint interfaces only; zero new FEM runs; no current field correction',
 'method':'actual source triangle-centroid radial bins; per-face exact P2 integrated current and weak contact law; frozen fields',
 'gate_B':'FAIL/STOP', 'gate_C_D':'NOT RUN',
 'preregistered_gate_raw_current_relative':.001, 'input_SHA256':{str(p.relative_to(ROOT)):sha(p) for p in (OLD,NEW,ORIGINAL_GATE,FINE_GATE)},'interfaces':{}}
 bars=[]
 for name in ('lead_land','lead_pin'):
  candidate=[]
  for label,data,gate in [('prior P2',old,og),('refined P2',new,ng)]:
   x=data['lead_interfaces'][name];op=x['contact_operator_consistency']
   rim=next(y for y in op['radial_triangle_centroid_bins'] if y['radius_over_CAD_radius_range'][0]==.9)
   inner=[y for y in op['radial_triangle_centroid_bins'] if y['radius_over_CAD_radius_range'][1]<=.9]
   drive=gate['P2_unit_potential_current_A']
   rel_oth=abs(sum(y['signed_other_side_bias_A'] for y in inner))/drive
   rel_lead=abs(sum(y['signed_lead9_bias_A'] for y in inner))/drive
   # Conditional *frozen-field* removal of rim bias, not a new field or bound on another PDE.
   item={'mesh':label,'triangles':x['source_registered_triangles'],
    'contact_area_m2':x['source_interface_area_m2'],
    'P2_raw_current_gate_error_pct':100*x['prospective_P2_gate_error_rel'],
    'lead_side_signed_bias_A':op['raw_lead9_side']['signed_bias_A'],
    'solder_side_signed_bias_A':op['raw_other_material_side']['signed_bias_A'],
    'solder_side_rim_area_share_pct':100*rim['area_fraction'],
    'solder_side_rim_abs_mismatch_share_pct':100*rim['fraction_of_abs_mismatch_on_second_material_side'],
    'lead_side_rim_abs_mismatch_share_pct':100*rim['fraction_of_abs_mismatch_on_lead9_side'],
    'counterfactual_no_rim_signed_solder_bias_pct':100*rel_oth,
    'counterfactual_no_rim_signed_lead_bias_pct':100*rel_lead,
    'counterfactual_no_rim_max_of_sides_pct':100*max(rel_oth,rel_lead),
    'rms_solder_side_rel_weak_flux':op['raw_other_material_side']['RMS_density_error_relative_to_weak_contact_density_RMS'],
    'mesh_adjacent_median_min_q':x['adjacent_worst_tetra_meanratio_quality_min_p01_median_p99'][2]}
   assert abs(item['P2_raw_current_gate_error_pct']-100*x['prospective_P2_gate_error_rel'])<1e-13
   assert item['counterfactual_no_rim_max_of_sides_pct']>.1
   candidate.append(item)
  result['interfaces'][name]=candidate
  bars.extend((name,x['mesh'],x['solder_side_rim_abs_mismatch_share_pct'],x['solder_side_rim_area_share_pct']) for x in candidate)
 result['decision']='STOP: larger source-CAD resolution fails original strict gate; even removing outer rim biases on frozen candidate contact field leaves >0.1% inner-region signed mismatch. Need interface-consistent field and independently bounded original raw-cut criteria, not another generic mesh sweep.'
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 fig,ax=plt.subplots(figsize=(9.6,5.4));fig.subplots_adjust(left=.16,right=.96,top=.70,bottom=.21)
 labels=['Solder land','Solder pin'];vold=[result['interfaces'][s][0]['solder_side_rim_abs_mismatch_share_pct'] for s in ('lead_land','lead_pin')];vnew=[result['interfaces'][s][1]['solder_side_rim_abs_mismatch_share_pct'] for s in ('lead_land','lead_pin')]
 x=np.arange(2);w=.27
 ax.bar(x-w/2,vold,width=w,label='28,691 TET4 P2',color='#7892a9')
 ax.bar(x+w/2,vnew,width=w,label='47,277 TET4 P2',color='#b2774a')
 for i,s in enumerate(('lead_land','lead_pin')):
  for j,v in enumerate((vold[i],vnew[i])):ax.text(i+(j-.5)*w,v+1.3,f'{v:.1f}%',ha='center',va='bottom',fontsize=10,weight='bold')
 ax.set_xticks(x,labels);ax.set_ylim(0,95);ax.set_ylabel('Share of absolute solder-side raw/contact mismatch (%)');ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
 fig.legend(ncol=2,frameon=False,loc='upper left',bbox_to_anchor=(.18,.84),fontsize=10)
 fig.text(.06,.955,'The contact rim still dominates after spatial refinement',weight='bold',fontsize=15,color='#26374b')
 fig.text(.06,.895,'Outer radial band: 0.90–1.05 × registered CAD contact radius',fontsize=10,color='#596b7d')
 fig.text(.06,.075,'This band occupies roughly 19–20% of contact area. Source-native P2 raw electric gate remains FAIL.',fontsize=9,color='#55677a')
 for suffix in ('.png','.pdf'):
  p=OUTPUT/('v315_lead9_rim_mismatch'+suffix)
  args={'dpi':190} if suffix=='.png' else {'metadata':{'Creator':'V3.15 no-solve comparison','CreationDate':None,'ModDate':None}}
  fig.savefig(p,bbox_inches='tight',**args)
 plt.close(fig)
 result['figure_SHA256']={str(p.relative_to(ROOT)):sha(p) for p in (OUTPUT/'v315_lead9_rim_mismatch.png',OUTPUT/'v315_lead9_rim_mismatch.pdf')}
 (OUTPUT/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 for name in result['interfaces']:
  print(name)
  for z in result['interfaces'][name]:
   print(z['mesh'],'rim_abs_share_pct',round(z['solder_side_rim_abs_mismatch_share_pct'],3),'rim_abs_area_pct',round(z['solder_side_rim_area_share_pct'],3),'frozen_no_rim_max_pct',round(z['counterfactual_no_rim_max_of_sides_pct'],3))
if __name__=='__main__':main()
