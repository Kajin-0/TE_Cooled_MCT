"""Summarize only complete independently audited pairs; no hidden interpolation."""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_robustness_20261110';base=R/'data/tec_height_coupling_20261110'
contract=json.loads((D/'contract.json').read_text());
def row(path,variant,source):
 r=json.loads((path/'result.json').read_text());a=json.loads((path/'independent_audit.json').read_text());h=hashlib.sha256((path/'result.json').read_bytes()).hexdigest();assert a['status'].startswith('PASS') and a['result_sha256']==h
 n=r['source_full_temperature_nodes_K'];return {'variant':variant,'die_K':r['calculated_detector_temperature_K'],'top_K':n['carrier'],'hot_K':n['stage0_hot'],'current_A':r['operating_current_A'],'voltage_V':r['terminal_voltage_V'],'power_W':r['electrical_power_W'],'sink_W':r['bath_heat_rejected_W'],'cold_leg_Qc_W':r['source_stage_thermoelectric_budget'][2]['qc_w'],'gas_internal_W':r['internal_interstage_gas_heat_hot_to_cold_W'],'gas_external_W':sum(r['cavity_gas_heat_into_three_ceramics_and_die_W']),'radiation_W':sum(r['gray_radiation_heat_into_three_ceramics_and_die_W']),'Cu_joule_W':r['Cu_form_tab_electrothermal_result']['total_electrical_power_W'],'Cu_heat_by_stage_W':r['Cu_form_tab_electrothermal_result']['heat_into_ceramic_by_stage_W'],'lead_conduction_W':r['source_tec_power_leads']['conduction_into_ceramic_W'],'stage_residual_W':max(abs(x) for x in a['stage_boundary_residual_W' if source=='V3.20' else 'stage_residual_W']),'global_residual_W':a['global_energy_residual_W' if source=='V3.20' else 'global_residual_W'],'outer_iterations':r['outer_iterations'],'solve_time_s':r['solve_time_s'],'result_sha256':h,'source':source}
rows=[]
nom=row(base/'nominal','nominal','V3.20');custom=row(base/'custom_060','custom_060','V3.20');rows.append({'scenario':'v320_control','nominal':nom,'custom_060':custom,'delta_die_K':custom['die_K']-nom['die_K'],'delta_top_K':custom['top_K']-nom['top_K'],'new_solves':0})
missing=[]
for key in contract['attempt_order']:
 folder=D/'cases'/key
 if not all((folder/v/'result.json').exists() and (folder/v/'independent_audit.json').exists() and (folder/v/'ports_crosscheck.json').exists() for v in ('nominal','custom_060')):
  missing.append({'scenario':key,'status':'INCOMPLETE / NOT RUN'});continue
 a=row(folder/'nominal','nominal','V3.21');b=row(folder/'custom_060','custom_060','V3.21')
 for v in ('nominal','custom_060'):
  p=folder/v;port=json.loads((p/'ports_crosscheck.json').read_text());assert port['status'].startswith('PASS') and port['source_result_sha256']==hashlib.sha256((p/'result.json').read_bytes()).hexdigest()
 rows.append({'scenario':key,'nominal':a,'custom_060':b,'delta_die_K':b['die_K']-a['die_K'],'delta_top_K':b['top_K']-a['top_K'],'new_solves':2})
r={'status':'MATCHED-POWER CONDITIONAL PAIRED SAMPLES; no probabilistic interval or native-cavity validation','pairs':rows,'incomplete':missing,'new_full_system_solves_with_audit':sum(x['new_solves'] for x in rows),'new_paired_scenarios':len(rows)-1,
 'min_delta_die_K':min(x['delta_die_K'] for x in rows),'max_delta_die_K':max(x['delta_die_K'] for x in rows),'all_sampled_custom_colder':all(x['delta_die_K']<0 for x in rows),'power_target_W':contract['target_power_W']}
p=D/'summary.json'
if p.exists(): assert json.loads(p.read_text()) == r
else: p.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'axes.titlesize':10});fig,ax=plt.subplots(1,2,figsize=(8.7,3.8),constrained_layout=True)
labels={'v320_control':'V3.20 reference','interstage_off':'Interstage gas off','outer_gap_1p5mm':'Outer gap 1.5 mm','sink_plus5':'Sink +5 K/W'}
ys=list(range(len(rows)));names=[labels[x['scenario']] for x in rows]
for i,z in enumerate(rows):
 ax[0].plot([z['custom_060']['die_K'],z['nominal']['die_K']],[i,i],color='#999',lw=1.3,zorder=1)
 ax[0].scatter([z['nominal']['die_K'],z['custom_060']['die_K']],[i,i],c=['#376b93','#be7443'],s=36,zorder=2)
 ax[1].barh(i,z['delta_die_K'],color='#648caa');ax[1].text(z['delta_die_K']-.05,i,f"{z['delta_die_K']:.3f}",ha='right',va='center',fontsize=8)
ax[0].set_yticks(ys,names);ax[0].invert_yaxis();ax[0].set_xlabel('Detector-mount temperature (K)');ax[0].set_title('Paired solved states');ax[0].grid(axis='x',alpha=.2)
from matplotlib.lines import Line2D
ax[0].legend(handles=[Line2D([],[],marker='o',ls='',color='#376b93',label='0.50 mm'),Line2D([],[],marker='o',ls='',color='#be7443',label='0.60 mm')],fontsize=8,loc='center right',bbox_to_anchor=(.98,.74))
ax[1].set_yticks(ys,names);ax[1].invert_yaxis();ax[1].axvline(0,color='#333',lw=.8);ax[1].set_xlabel('0.60 mm minus 0.50 mm (K)');ax[1].set_title('Conditional paired differences');ax[1].set_xlim(min(x['delta_die_K'] for x in rows)-.65,.2);ax[1].grid(axis='x',alpha=.2)
for ext in ('pdf','png'):fig.savefig(R/f'reports/current/figures/v321_height_robustness.{ext}',dpi=190)
print(json.dumps(r,indent=2))
