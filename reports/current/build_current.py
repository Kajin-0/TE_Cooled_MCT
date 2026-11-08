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
(HERE/'derived_tables.tex').write_text(t)
infiles=[ARCH/'result.json',ARCH/'source_native_ceramics_V3_3.npz',ROOT/'data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step',ROOT/'data/synthetic_v3_assembly_20261102/conductor_geometry_coefficients.json',
ROOT/'data/v3_r38_global_tetgen_20261105/attempt01/saved_mesh_audit.json',ROOT/'data/v3_r39_quality_20261105/attempt01/candidate_result.json']
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
