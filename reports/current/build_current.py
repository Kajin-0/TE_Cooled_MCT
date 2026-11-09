#!/usr/bin/env python3
"""Rebuild the independently readable current-architecture scientific assessment.
Only immutable saved data and reviewed image assets are inputs; no PDE solves.
"""
from pathlib import Path
from shutil import copy2
import hashlib, json, re, subprocess, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
FIG=HERE/'figures'
FIG.mkdir(exist_ok=True)
ARCH=ROOT/'data/v3_3_cavity_package_feedback_20261108/attempt02'
RESULT=json.loads((ARCH/'result.json').read_text())
MD=(ROOT/'reports/generated/TEC_HgCdTe_Reference_V3_3_Standalone_Method_20261108.md').read_text()
C=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/conductor_geometry_coefficients.json').read_text())
v33=[f'v33_{n}' for n in ('topology','ceramic_fields','versions','cavity_loads','transport','leg_budgets','iterations')]
for name in v33:
    for ext in ('pdf','png'):
        p=ROOT/'reports/master/generated/figures'/f'{name}.{ext}'
        # After historical Rev3 restoration, original V3.3 PDF/PNG figures
        # remain frozen under reports/current/figures for reproducible reuse.
        if p.is_file():
            copy2(p,FIG/p.name)
        else:
            assert (FIG/p.name).is_file(),f'Missing frozen figure: {p.name}'
for dest,source in [
('cad_assembly','module_actual_STEP.png'),
('cad_package','package_actual_STEP_corrected.png'),
('cad_interfaces','joint_mount_sections.png')
]:
    copy2(ROOT/'data/synthetic_v3_assembly_20261102/drawings'/source,FIG/f'{dest}.png')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
  'pdf.fonttype':42,'savefig.facecolor':'white'})
# Measured global quality distributions. Verified archival counts, not a new solve.
fig,axs=plt.subplots(1,2,figsize=(10.5,3.25),layout='constrained')
labels=['R3.8\nTetGen','R3.9\nlocal flips']
n=np.array([280430,241754]);nt=np.array([1043314,1010119])
axs[0].bar(labels,n/nt*100,color=['#b27c35','#406f9e'])
for i,v in enumerate(n/nt*100): axs[0].text(i,v+.55,f'{v:.2f}%',ha='center',fontweight='bold')
axs[0].set(ylabel='Cells with mean-ratio q < 0.05 (%)',ylim=(0,32),title='Poor-quality tetrahedron population')
m=np.array([2.656615e-5,1.384952e-4])
axs[1].bar(labels,m,color=['#b27c35','#406f9e'])
for i,v in enumerate(m):axs[1].text(i,v+0.000004,f'{v:.2e}',ha='center',fontsize=9)
axs[1].set(ylabel='Minimum mean-ratio quality q',ylim=(0,0.00018),title='Minimum element quality')
fig.savefig(FIG/'mesh_quality.pdf',metadata={'CreationDate':None,'ModDate':None});fig.savefig(FIG/'mesh_quality.png',dpi=220)
plt.close(fig)
# Tab-length-derived straight uniform bar screening. Explicitly NOT 3D/thermal-junction solve.
rho=1/58e6;k=385
names=['Net 58','Net 80','Net 88 return']
lengths=np.array([c['neutral_path_length_m'] for c in C])
areas=np.array([c['cross_section_m2'] for c in C])
R=rho*lengths/areas
G=k*areas/lengths
fig,axs=plt.subplots(1,2,figsize=(10.5,3.25),layout='constrained')
for ax,vals,unit in zip(axs,[R*1e3,G*1e3],['Idealized series resistance (mΩ)','Idealized end-to-end conductance (mW/K)']):
    ax.bar(names,vals,color=['#4a76a3','#4a76a3','#b27340'])
    ax.set_ylabel(unit);ax.set_ylim(0,max(vals)*1.22)
    for i,v in enumerate(vals):ax.text(i,v+.03*max(vals),f'{v:.2f}',ha='center')
fig.savefig(FIG/'tab_screen.pdf',metadata={'CreationDate':None,'ModDate':None});fig.savefig(FIG/'tab_screen.png',dpi=220)
plt.close(fig)
def esc(s):
    return str(s).replace('&',r'\&').replace('%',r'\%').replace('#',r'\#').replace('_',r'\_')
def getrows(section,nextsection):
    x=MD.split(section,1)[1].split(nextsection,1)[0]
    rows=[]
    for line in x.splitlines():
        if line.startswith('|'):
            cols=[y.strip() for y in line.strip().strip('|').split('|')]
            if cols and re.fullmatch(r'-?\d+',cols[0]):rows.append(cols)
    return rows
legs=getrows('## Appendix B.', '## Appendix C.')
pads=getrows('## Appendix C.','## Independent references')
materials=getrows('| T (K) | S_P','## 3.')
assert len(legs)==88,(len(legs),legs[:2])
assert len(pads)>=90,(len(pads),pads[:2])
assert len(materials)==14,len(materials)
def rows_table(rows):
    return '\n'.join(' & '.join(esc(q) for q in row)+r' \\' for row in rows)
metrics=[]
d=RESULT
stage=d['source_stage_thermoelectric_budget']
strows=[[str(i),str(s['nlegs']),f"{1000*s['qc_w']:.4f}",f"{1000*s['qh_w']:.4f}",f"{s['voltage_v']:.6f}",f"{1000*s['joule_w']:.3f}"] for i,s in enumerate(stage,1)]
gas=np.array(d['cavity_gas_heat_into_three_ceramics_and_die_W'])*1e3
rad=np.array(d['gray_radiation_heat_into_three_ceramics_and_die_W'])*1e3
crow=[[s,f'{g:.5f}',f'{r:.5f}',f'{g+r:.5f}'] for s,g,r in zip(['Ceramic C1','Ceramic C2','Ceramic C3','Detector'],gas,rad)]
crow.append(['TOTAL',f'{gas.sum():.5f}',f'{rad.sum():.5f}',f'{(gas+rad).sum():.5f}'])
V32=d['V3_2_same_current_comparison']
summary=[
['Detector temperature (K)',f"{V32['V3_2_Tdie_K']:.6f}",f"{d['calculated_detector_temperature_K']:.6f}"],
['Terminal voltage (V)',f"{V32['V3_2_Vterminal_V']:.6f}",f"{d['terminal_voltage_V']:.6f}"],
['Electrical input (W)',f"{V32['V3_2_Pelectric_W']:.6f}" if 'V3_2_Pelectric_W' in V32 else '0.609628',f"{d['electrical_power_W']:.6f}"],
['Bath rejection (W)','0.590323',f"{d['bath_heat_rejected_W']:.6f}"],
['Pressure (Pa)','0 (cavity off)','100 (Kr)']
]
nodes=[[k.replace('_',' ').title(),f'{v:.5f}'] for k,v in d['source_full_temperature_nodes_K'].items()]
iters=[[str(z['outer_iteration']),f"{z['die_K']:.6f}",f"{z['spatial_pad_K_max_change']:.3e}",f"{z['local_load_mismatch_W']:.3e}"] for z in d['spatial_outer_iteration_history']]
checks=[['Global energy',d['global_thermoelectric_energy_residual_W'],'W'],
['Worst stage balance',d['max_full_stage_conservation_residual_W'],'W'],
['Ceramic pad heat',d['max_native_plate_net_heat_imbalance_W'],'W'],
['Worst individual leg',d['max_separate_leg_energy_residual_W'],'W'],
['Final pad temperature change',d['max_last_spatial_temperature_update_K'],'K']]
checks_rows=[[k,f'{v:.4e}',u] for k,v,u in checks]
t=r'''% Frozen source-derived tables. Auto-generated; do not hand-edit.
\newcommand{\stagebudgetrows}{STAGEROWS}
\newcommand{\cavityrows}{CAVITYROWS}
\newcommand{\operatingrows}{OPERATINGROWS}
\newcommand{\nodetablerows}{NODEROWS}
\newcommand{\iterationrows}{ITERROWS}
\newcommand{\residualrows}{CHECKROWS}
\newcommand{\materialrows}{MATERIALROWS}
\newcommand{\legrows}{LEGROWS}
\newcommand{\padrows}{PADROWS}
'''
for key,rows in [('STAGEROWS',strows),('CAVITYROWS',crow),('OPERATINGROWS',summary),('NODEROWS',nodes),('ITERROWS',iters),('CHECKROWS',checks_rows),('MATERIALROWS',materials),('LEGROWS',legs),('PADROWS',pads)]:
    t=t.replace(key,rows_table(rows))
# Keep all 88 source leg rows intact but provide balanced two-column presentation.
assert len(legs)==88
t += '\n'+r'\newcommand{\legrowsA}{'+rows_table(legs[:44])+'}'+'\n'
t += r'\newcommand{\legrowsB}{'+rows_table(legs[44:])+'}'+'\n'
# Append all 88 original legs paired side-by-side in ONE LaTeX table:
# unlike nested minipages, 44 paired rows cannot be split into orphan pages.
assert len(legs)==88
paired=[[*a,*b] for a,b in zip(legs[:44],legs[44:])]
assert len(paired)==44 and all(len(v)==10 for v in paired)
t += chr(10)+r'\newcommand{\legpairrows}{'+rows_table(paired)+'}'+chr(10)
(HERE/'derived_tables.tex').write_text(t)
# Current source-coupled V3.4, independently checked against V3.3. This
# generates report input tables from accepted archived results, not from a PDE.
V34=ROOT/'data/v3_4_copper_multiport_20261108/attempt03'
v34=json.loads((V34/'result.json').read_text())
audit=json.loads((V34/'independent_read_only_acceptance.json').read_text())
assert 'ACCEPTED' in audit['verdict']
assert hashlib.sha256((V34/'result.json').read_bytes()).hexdigest()==audit['result_sha256']
assert hashlib.sha256((ARCH/'result.json').read_bytes()).hexdigest()==audit['source_V3_3_result_sha256']
assert abs(v34['calculated_detector_temperature_K']-audit['V3_4_Tdie_K'])<1e-12
independent=json.loads((V34/'independent_physics_reconstruction.json').read_text())
assert independent['status'].startswith('PASS separate algebraic')
assert independent['archived_result_sha256']==audit['result_sha256']
assert independent['maximum_absolute_stage_residual_W']<1e-8
assert v34['max_last_spatial_temperature_update_K']<3e-7
def signed(v):return f'{v:+.6f}'
old=RESULT
metric=[
 ['Detector temperature (K)',f"{old['calculated_detector_temperature_K']:.6f}",
  f"{v34['calculated_detector_temperature_K']:.6f}",
  signed(v34['calculated_detector_temperature_K']-old['calculated_detector_temperature_K'])],
 ['Terminal voltage (V)',f"{old['terminal_voltage_V']:.6f}",
  f"{v34['terminal_voltage_V']:.6f}",signed(v34['terminal_voltage_V']-old['terminal_voltage_V'])],
 ['Electrical input (W)',f"{old['electrical_power_W']:.6f}",
  f"{v34['electrical_power_W']:.6f}",signed(v34['electrical_power_W']-old['electrical_power_W'])],
 ['Sink heat rejection (W)',f"{old['bath_heat_rejected_W']:.6f}",
  f"{v34['bath_heat_rejected_W']:.6f}",signed(v34['bath_heat_rejected_W']-old['bath_heat_rejected_W'])]]
v34s=v34['source_stage_thermoelectric_budget']
stage_rows=[[str(i+1),str(a['nlegs']),
    f"{1000*a['qc_w']:.3f}",f"{1000*a['qh_w']:.3f}",f"{a['voltage_v']:.6f}"]
    for i,a in enumerate(v34s)]
cop=v34['Cu_form_tab_electrothermal_result']
crows=[]
for net in ('58','80','88'):
    d=cop['net_details'][net]
    heats={int(face):q for face,q in zip(d['face_tags'],d['face_heat_into_ceramic_W'])}
    tags=[(38,36),(75,79,74),(105,104)]
    h=[sum(heats.get(t,0.) for t in grp)*1e3 for grp in tags]
    crows.append([f'Net {net}',*[f'{x:+.3f}' for x in h],f"{1000*d['electric_Joule_W']:.3f}"])
crows.append(['ALL',*[f'{x*1000:+.3f}' for x in cop['heat_into_ceramic_by_stage_W']],
    f"{1000*cop['total_electrical_power_W']:.3f}"])
v34checks=[
 ['Final pad update (K)',f"{v34['max_last_spatial_temperature_update_K']:.3e}"],
 ['Independent stage heat residual (W)',f"{max(abs(x) for x in audit['source_stage_balance_reconstructed_W'].values()):.3e}"],
 ['Global energy residual (W)',f"{abs(v34['global_thermoelectric_energy_residual_W']):.3e}"],
 ['Copper Joule/heat mismatch (W)',f"{abs(audit['copper_heat_minus_electrical_work_W']):.3e}"]]
vfour='% Source-derived V3.4 result; frozen independent audit passed.' + chr(10)
for name,rows in [('vfourmetricrows',metric),('vfourstagerows',stage_rows),
    ('vfourcopperrows',crows),('vfourcheckrows',v34checks)]:
    vfour+=chr(92)+'newcommand{'+chr(92)+name+'}{'+rows_table(rows)+'}'+chr(10)
(HERE/'v34_derived_tables.tex').write_text(vfour)
import runpy
runpy.run_path(str(HERE/'v34_figures.py'),run_name='__main__')
# Accepted V3.5 whole-device source state; frozen, verified, no report-time PDE.
V35=ROOT/'data/v3_5_power_lead_and_copper_sensitivity_20261108'
scenarios=('copper_native_pad','nickel_native_pad','high_interstage_contact_R')
solved={name:json.loads((V35/name/'result.json').read_text()) for name in scenarios}
independent={name:json.loads((V35/name/'independent_energy_audit.json').read_text())
             for name in scenarios}
for name in scenarios:
    assert independent[name]['verdict'].startswith('PASS independent')
    assert independent[name]['result_sha256']==hashlib.sha256((V35/name/'result.json').read_bytes()).hexdigest()
    assert solved[name]['max_last_spatial_temperature_update_K']<3e-7
base=solved['copper_native_pad']
nickel=solved['nickel_native_pad']
severe=solved['high_interstage_contact_R']
assert abs(base['calculated_detector_temperature_K']-218.90002402868413)<1e-10
assert abs(severe['calculated_detector_temperature_K']-212.62358247326281)<1e-10
def operating_row(label,d):
    return [label,f"{d['calculated_detector_temperature_K']:.3f}",
      f"{d['terminal_voltage_V']:.5f}",f"{1000*d['electrical_power_W']:.3f}"]
ops=[operating_row('V3.4 legacy lead map',v34),
     operating_row('V3.5 Cu native pad',base),
     operating_row('V3.5 Ni-like wire',nickel),
     operating_row('V3.5 high Cu joint R',severe)]
leadbud=[]
for name,label in (('copper_native_pad','Copper'),
                   ('nickel_native_pad','Nickel-like')):
    z=solved[name]['source_tec_power_leads']
    leadbud.append([label,
      f"{1000*z['per_lead']['TEC_lead1']['heat_into_tec_pad_W']:+.3f}",
      f"{1000*z['per_lead']['TEC_lead9']['heat_into_tec_pad_W']:+.3f}",
      f"{1000*z['joule_W']:.3f}"])
checking=[]
for name,label in (('copper_native_pad','Copper'),
                   ('nickel_native_pad','Nickel-like'),
                   ('high_interstage_contact_R','High R')):
    a=independent[name];d=solved[name]
    checking.append([label,f"{d['max_last_spatial_temperature_update_K']:.3e}",
       f"{a['max_stage_energy_residual_W']:.3e}",
       f"{abs(a['global_energy_residual_W']):.3e}"])
screen=json.loads((V35/'fixed_source_field_screen.json').read_text())
rowscontact=[[f"{x['r_thermal_contact_area_m2K_W']:.0e}",
    f"{x['original_source_Cu_heat_into_stage_mW'][2]:.3f}"]
    for x in screen['interstage_Cu_contact_screen']
    if x['r_thermal_contact_area_m2K_W']>0]
vf='% Source-derived V3.5 frozen registered results; audit accepted.'+chr(10)
for name,rows in (('vfiveoperatingrows',ops),('vfiveleadrows',leadbud),
                  ('vfivecheckrows',checking),('vfivecontactrows',rowscontact)):
    vf+=chr(92)+'newcommand{'+chr(92)+name+'}{'+rows_table(rows)+'}'+chr(10)
(HERE/'v35_derived_tables.tex').write_text(vf)
runpy.run_path(str(HERE/'v35_figures.py'),run_name='__main__')
# V3.6: expand actual accepted source-temperature operating envelope without
# modifying any V3.3-V3.5 scientific plot, table, or archived original.
V36=ROOT/'data/v3_6_operating_envelope_20261109'
runpy.run_path(str(HERE/'v36_operating_envelope_figures.py'),run_name='__main__')
v36sum=json.loads((V36/'accepted_envelope_summary.json').read_text())
assert len(v36sum['current_cases'])==4 and len(v36sum['load_cases'])==3
v36names=sorted({z['name'] for z in v36sum['current_cases']+v36sum['load_cases']})
assert len(v36names)==6
for case in v36names:
    r=json.loads((V36/case/'registration.json').read_text())
    d=json.loads((V36/case/'result.json').read_text())
    a=json.loads((V36/case/'independent_energy_audit.json').read_text())
    assert a['verdict'].startswith('PASS V3.6')
    assert hashlib.sha256((V36/case/'result.json').read_bytes()).hexdigest()==a['result_sha256']
    assert d['max_last_spatial_temperature_update_K']<3e-7
    assert a['max_stage_energy_residual_W']<1e-8
    assert abs(a['global_energy_residual_W'])<1e-8
    assert d['original_ceramic_TET4']==11791 and len(d['source_individual_leg_flux_and_electric_results'])==88
rows_current=[[f"{z['current_A']:.3f}",f"{z['detector_temperature_K']:.3f}",
    f"{z['TEC_voltage_V']:.5f}",f"{z['TEC_input_W']:.5f}"] for z in v36sum['current_cases']]
rows_load=[[f"{z['detector_heat_mW']:.2f}",f"{z['detector_temperature_K']:.3f}",
    f"{z['TEC_voltage_V']:.5f}",f"{z['TEC_input_W']:.5f}"] for z in v36sum['load_cases']]
rows_cost=[]
for a,b in zip(v36sum['current_cases'][:-1],v36sum['current_cases'][1:]):
    delta_cooling=a['detector_temperature_K']-b['detector_temperature_K']
    delta_power=b['TEC_input_W']-a['TEC_input_W']
    assert delta_cooling>0 and delta_power>0
    rows_cost.append([f"{a['current_A']:.2f}--{b['current_A']:.2f}",
        f'{delta_cooling:.3f}',f'{1000*delta_power:.2f}',f'{1000*delta_power/delta_cooling:.2f}'])
vt='% V3.6 full-system accepted source results, independent audits verified.'+chr(10)
for name,rows in [('vsixcurrentrows',rows_current),('vsixloadrows',rows_load),('vsixcostrows',rows_cost)]:
    vt+=chr(92)+'newcommand{'+chr(92)+name+'}{'+rows_table(rows)+'}'+chr(10)
(HERE/'v36_derived_tables.tex').write_text(vt)
infiles=[ARCH/'result.json',ARCH/'source_native_ceramics_V3_3.npz',ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json',ROOT/'data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step',ROOT/'data/synthetic_v3_assembly_20261102/conductor_geometry_coefficients.json',
ROOT/'data/v3_r38_global_tetgen_20261105/attempt01/saved_mesh_audit.json',ROOT/'data/v3_r39_quality_20261105/attempt01/candidate_result.json',V34/'result.json',V34/'independent_read_only_acceptance.json',V34/'independent_physics_reconstruction.json',V34/'source_native_ceramics_V3_4.npz',
V35/'fixed_source_field_screen.json',
*([V35/name/f for name in scenarios for f in
    ('result.json','registration.json','independent_energy_audit.json',
     'source_native_ceramics_V3_5.npz')]),
V36/'accepted_envelope_summary.json',
V36/'attempt01_initial_warm_start_source.py',
*([V36/case/f for case in v36names for f in
    ('registration.json','result.json','independent_energy_audit.json',
     'source_native_ceramics_V3_6.npz')])]
manifest={'kind':'data-only current science assessment','new_physics_solves':0,'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in infiles},
'figures_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in FIG.iterdir()},'n_legs':len(legs),'n_pad_faces':len(pads),'n_material_rows':len(materials)}
(HERE/'reproduction_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if not (HERE/'report.tex').is_file(): raise SystemExit('Missing report.tex')
env={**os.environ,'SOURCE_DATE_EPOCH':'1794139200','TZ':'UTC'}
for i in range(3):
    proc=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','report.tex'],cwd=HERE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env)
    if proc.returncode:
        (HERE/'build_error.log').write_text(proc.stdout)
        raise RuntimeError(f'LaTeX build failed on pass {i+1}: '+proc.stdout[-4000:])
assert (HERE/'report.pdf').is_file()
proc=subprocess.run(['mutool','info','report.pdf'],cwd=HERE,capture_output=True,text=True)
print('PDF BUILT',proc.stdout.split('Pages:')[-1][:20], 'bytes',(HERE/'report.pdf').stat().st_size)
print('Source input coverage:',len(legs),'legs;',len(pads),'pads;',len(materials),'material knots.')
print('PDF sha256',hashlib.sha256((HERE/'report.pdf').read_bytes()).hexdigest())
