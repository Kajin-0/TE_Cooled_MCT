"""Build figures and machine summary from two independently accepted results only."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_coupling_20261110';rows=[]
for name in ('nominal','custom_060'):
 p=D/name;r=json.loads((p/'result.json').read_text());a=json.loads((p/'independent_audit.json').read_text());g=json.loads((p/'gas_crosscheck.json').read_text())
 assert a['status'].startswith('PASS') and g['status'].startswith('PASS') and r['variant']==name
 sha=hashlib.sha256((p/'result.json').read_bytes()).hexdigest();assert sha==a['result_sha256']==g['source_result_sha256']
 n=r['source_full_temperature_nodes_K'];legs=r['source_individual_leg_flux_and_electric_results'];st=r['source_stage_thermoelectric_budget']
 rows.append({'case':name,'height_mm':r['leg_length_m']*1000,'I_A':r['operating_current_A'],'V_V':r['terminal_voltage_V'],'P_W':r['electrical_power_W'],
  'die_K':r['calculated_detector_temperature_K'],'top_ceramic_K':n['carrier'],'hot_ceramic_K':n['stage0_hot'],
  'cold_leg_Qc_W':st[2]['qc_w'],'bath_W':r['bath_heat_rejected_W'],'stage_budgets':st,'gas_interstage_W':r['internal_interstage_gas_heat_hot_to_cold_W'],
  'external_gas_W':sum(r['cavity_gas_heat_into_three_ceramics_and_die_W']),'external_radiation_W':sum(r['gray_radiation_heat_into_three_ceramics_and_die_W']),
  'lead_conduction_W':r['source_tec_power_leads']['conduction_into_ceramic_W'],'lead_joule_W':r['source_tec_power_leads']['joule_W'],
  'copper_heat_into_stage_W':r['Cu_form_tab_heat_into_ceramic_by_stage_W'],'copper_joule_W':r['Cu_form_tab_electrical_Joule_W'],
  'joint_joule_W':r['source_joint_additional_electrical_Joule_W'],'leg_min_K':min(x['leg_min_K'] for x in legs),'leg_max_K':max(x['leg_max_K'] for x in legs),'assumed_above300_legs':sum(x['assumed_above_300K'] for x in legs),
  'outer_iterations':r['outer_iterations'],'seconds':r['solve_time_s'],'outer_update_K':r['max_last_spatial_temperature_update_K'],
  'global_balance_W':a['global_energy_residual_W'],'max_stage_boundary_balance_W':max(abs(x) for x in a['stage_boundary_residual_W']),'max_leg_residual_W':a['max_leg_residual_W'],'result_sha256':sha})
assert abs(rows[0]['P_W']-rows[1]['P_W'])<1e-8
result={'status':'TWO CONDITIONAL MATCHED-POWER 88-LEG/TRANSLATED CERAMIC SOLVES; gas and metal proxy physical accuracy unqualified','cases':rows,
 'candidate_minus_nominal_die_K':rows[1]['die_K']-rows[0]['die_K'],'candidate_minus_nominal_top_K':rows[1]['top_ceramic_K']-rows[0]['top_ceramic_K'],
 'matched_power_W':.5956680349614825,'full_system_solves':2,'independent_audits':2,'native_gas_and_full_3D_metal':'NOT SOLVED',
 'cavity_warning':'External 3mm fixed reservoir proxy and additional interstage channels are hypothetical and may share true cavity volume; no native gas closure or statistical uncertainty.'}
out=D/'summary.json'
if out.exists():assert json.loads(out.read_text())==result
else:out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'axes.titlesize':10});fig,ax=plt.subplots(1,2,figsize=(8.6,3.8),constrained_layout=True);x=np.arange(2);colors=['#376b93','#be7443']
for i,z in enumerate(rows):
 ax[0].scatter(z['die_K'],i+.12,s=55,color=colors[i],marker='o');ax[0].scatter(z['top_ceramic_K'],i-.12,s=55,color=colors[i],marker='s')
 ax[0].text(z['die_K']+.08,i+.12,f"{z['die_K']:.3f}",va='center',fontsize=8)
 ax[0].text(z['top_ceramic_K']+.08,i-.12,f"{z['top_ceramic_K']:.3f}",va='center',fontsize=8)
ax[0].set_xlim(min(z['top_ceramic_K'] for z in rows)-.30,max(z['die_K'] for z in rows)+.75);ax[0].set_yticks(x,['0.50 mm','0.60 mm']);ax[0].invert_yaxis();ax[0].set_xlabel('Temperature (K)');ax[0].set_title('Matched-input solved temperatures');ax[0].grid(axis='x',alpha=.2)
from matplotlib.lines import Line2D
ax[0].legend(handles=[Line2D([],[],color='#555',marker='o',ls='',label='Die mount'),Line2D([],[],color='#555',marker='s',ls='',label='Top ceramic')],loc='lower right',fontsize=8)
xx=np.arange(3);w=.36
for i,z in enumerate(rows):
 v=np.array(z['gas_interstage_W'])*1000;bars=ax[1].bar(xx+(i-.5)*w,v,w,label=f"{z['height_mm']:.2f} mm",color=colors[i]);ax[1].bar_label(bars,fmt='%.2f',padding=2,fontsize=8)
ax[1].set_xticks(xx,['Hot stage','Middle','Cold stage']);ax[1].set_ylabel('Hot-to-cold gas heat (mW)');ax[1].set_title('Interstage gas-channel proxy');ax[1].set_ylim(0,max(max(z['gas_interstage_W']) for z in rows)*1250);ax[1].legend(fontsize=8,loc='upper right');ax[1].grid(axis='y',alpha=.2)
for ext in ('pdf','png'):fig.savefig(R/f'reports/current/figures/v320_height_matched.{ext}',dpi=190)
print(json.dumps(result,indent=2))
