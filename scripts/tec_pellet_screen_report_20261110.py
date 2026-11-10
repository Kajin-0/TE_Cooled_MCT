#!/usr/bin/env python3
"""Generate compact tables/figures from sealed fixed-boundary screen; no solve."""
from pathlib import Path
import hashlib,json,datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tecooledmct.graded_tec import props
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/tec_pellet_screen_20261110';FIG=ROOT/'reports/current/figures'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 reg=read(DATA/'registration.json');cases={}
 for z in reg['geometry_cases']:
  cid=z['id'];p=DATA/'cases'/cid/'result.json';d=read(p);a=read(p.parent/'independent_audit.json')
  assert d['status']=='ACCEPTED FROZEN-PAD TRANSPORT ONLY' and a['result_sha256']==sha(p) and a['status'].startswith('PASS')
  cases[cid]=d
 base=cases['baseline'];bqc=base['matched_power']['stage_budgets'][2]['qc_W'];rows=[]
 for z in reg['geometry_cases']:
  d=cases[z['id']];f=d['fixed_current'];m=d['matched_power'];a=read(DATA/'cases'/z['id']/'independent_audit.json')
  rows.append(dict(case=z['id'],width_mm=z['width_mm'],area_mm2=z['width_mm']**2,length_mm=z['length_mm'],g=(z['width_mm']/.4)**2/(z['length_mm']/.5),fixed_current_A=f['current_A'],fixed_current_terminal_V=f['terminal_V'],fixed_current_power_W=f['electrical_power_W'],fixed_current_cold_Qc_W=f['stage_budgets'][2]['qc_W'],matched_current_A=m['current_A'],matched_terminal_V=m['terminal_V'],matched_power_W=m['electrical_power_W'],matched_cold_Qc_W=m['stage_budgets'][2]['qc_W'],matched_cold_Qc_delta_W=m['stage_budgets'][2]['qc_W']-bqc,min_leg_K=m['min_leg_K'],max_leg_K=m['max_leg_K'],assumed_extension_legs=m['legs_using_assumed_above_300K'],independent_audit=a['status'],max_leg_residual_W=a['max_leg_energy_error_W'],max_stage_residual_W=a['max_stage_energy_error_W'],elapsed_seconds=d['elapsed_seconds'],geometry_consistent=z['id']=='baseline'))
 prop={str(T):{pol:{k:float(np.asarray(props(pol,float(T))[k])) for k in ('S','rho','k')} for pol in ('P','N')} for T in (220,260,300)}
 byid={r['case']:r for r in rows};secants={}
 for name,lo,hi in [('height','length_060','length_040'),('width','width_036','width_044')]:
  x,y=byid[lo],byid[hi];slope=(y['matched_cold_Qc_W']-x['matched_cold_Qc_W'])/np.log(y['g']/x['g']);secants[name]=dict(dQc_dlog_g_W=float(slope),normalized_to_baseline_Qc=float(slope/bqc))
 summary=dict(matched_power_geometry_secants=secants,status='FIVE ACCEPTED FROZEN-PAD TRANSPORT SCENARIOS; NO GEOMETRY-CONSISTENT OR FULL-PACKAGE RESULTS',cases=rows,matched_power_target_W=reg['matched_power_reference_W'],source_reference=dict(top_ceramic_K=base['fixed_current']['source_top_ceramic_K_FIXED'],die_K=base['fixed_current']['source_die_K_FIXED'],hot_ceramic_K=base['fixed_current']['source_hot_ceramic_K_FIXED'],auxiliary_R_ohm=base['fixed_current']['auxiliary_series_R_ohm'],current_A=.4),source_material_samples_SI=prop,accepted_case_count=len(rows),independently_audited_count=5,accepted_states=10,full_system_solves=0,source_die_temperature_and_top_held_fixed=True,physical_geometry_variants_qualified=0,max_stage_residual_W=max(z['max_stage_residual_W'] for z in rows),max_leg_residual_W=max(z['max_leg_residual_W'] for z in rows),input_sha256={str((DATA/'cases'/z['id']/'result.json').relative_to(ROOT)):sha(DATA/'cases'/z['id']/'result.json') for z in reg['geometry_cases']})
 (DATA/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
 FIG.mkdir(exist_ok=True);plt.rcParams.update({'font.size':9,'axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 fig,axs=plt.subplots(1,2,figsize=(7,2.9),layout='constrained')
 for ids,col,label,marker in [(['length_040','baseline','length_060'],'#28779b','Vary height','o'),(['width_036','baseline','width_044'],'#a35340','Vary width','s')]:
  z=sorted([next(r for r in rows if r['case']==i) for i in ids],key=lambda r:r['g']);x=[r['g'] for r in z]
  axs[0].plot(x,[r['fixed_current_cold_Qc_W']*1e3 for r in z],marker=marker,ls='--',color=col,alpha=.65,label=label+'; 0.4 A')
  axs[0].plot(x,[r['matched_cold_Qc_W']*1e3 for r in z],marker=marker,ls='-',color=col,label=label+'; fixed power')
  axs[1].plot(x,[r['matched_current_A'] for r in z],marker=marker,color=col,label=label)
 axs[0].axhline(0,color='#555',lw=.8);axs[0].set(xlabel='Relative axial geometry factor $(A/L)/(A_0/L_0)$',ylabel='Cold-stage $Q_c$ (mW)');axs[0].legend(fontsize=6.4,loc='best')
 axs[1].axhline(.4,color='#777',lw=.8,ls=':');axs[1].set(xlabel='Relative axial geometry factor $(A/L)/(A_0/L_0)$',ylabel='Current at 0.595668 W (A)');axs[1].legend()
 for ax in axs:ax.grid(alpha=.2)
 for ext in ('pdf','png'):fig.savefig(FIG/f'v317_pellet_fixed_boundary.{ext}',dpi=300,bbox_inches='tight',**({'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}))
 plt.close(fig)
 fig,axs=plt.subplots(1,3,figsize=(7,3),layout='constrained');labels=['L=.4','Base','L=.6','w=.36','w=.44'];order=['length_040','baseline','length_060','width_036','width_044']
 for stage,ax in enumerate(axs):
  values=[cases[k]['matched_power']['stage_budgets'][stage]['qc_W']*1e3 for k in order];ax.bar(np.arange(5),values,color=['#28779b','#777777','#28779b','#a35340','#a35340']);ax.axhline(0,color='#555',lw=.7);ax.set_title(f'Stage {stage+1}');ax.set_xticks(np.arange(5),labels,rotation=40,ha='right',fontsize=7);ax.set_ylabel('$Q_c$ (mW)');ax.grid(axis='y',alpha=.2)
 for ext in ('pdf','png'):fig.savefig(FIG/f'v317_pellet_stage_budgets.{ext}',dpi=300,bbox_inches='tight',**({'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}))
 plt.close(fig)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
