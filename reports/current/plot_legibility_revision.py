#!/usr/bin/env python3
"""Re-typeset five accepted report figures from frozen source data.

No simulation, mesh generation, physical recalculation, or modification of
archived figures. Outputs are separate *_legible files for the cumulative PDF.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = HERE / 'figures'
INPUTS = []
OUTPUTS = []

def load(path):
    path = Path(path)
    INPUTS.append(path)
    return json.loads(path.read_text())

def save(fig, name):
    pdf = FIG / f'{name}.pdf'
    png = FIG / f'{name}.png'
    fig.savefig(pdf, bbox_inches='tight', pad_inches=.10,
                metadata={'Creator':'TEC/TO plot-legibility revision',
                          'CreationDate': None, 'ModDate': None})
    fig.savefig(png, dpi=220, bbox_inches='tight', pad_inches=.10)
    OUTPUTS.extend([pdf, png])
    plt.close(fig)

def verify_result(case, prefix):
    root=ROOT / prefix / case
    dat=load(root/'result.json')
    a=load(root/'independent_energy_audit.json')
    assert a['verdict'].startswith('PASS'), (case,a.get('verdict'))
    assert hashlib.sha256((root/'result.json').read_bytes()).hexdigest() == a['result_sha256']
    return dat

plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
    'pdf.fonttype':42, 'axes.spines.top':False,
    'axes.spines.right':False, 'savefig.facecolor':'white'})

# 1: V3.3 native P/N physical centers. A single figure-footer legend does
# not cover any real leg position; preserve both source-CAD ceramic outlines.
base = 'data/v3_3_cavity_package_feedback_20261108/attempt02'
reg = load(ROOT/base/'registration.json')
design = load(ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json')
assert len(design['legs']) == 88
fig=plt.figure(figsize=(8.35,3.15),facecolor='white')
axes=[fig.add_axes([.075+i*.315,.245,.250,.60]) for i in range(3)]
for st,ax in enumerate(axes):
    for halfwidth,style in [(reg['original_CAD_ceramic_halfwidth_mm'][st],'--'),
                            (reg['original_CAD_ceramic_halfwidth_mm'][st+1],'-')]:
        w=2*halfwidth
        ax.add_patch(plt.Rectangle((-w/2,-w/2),w,w,fill=False,ls=style,lw=.9,color='#555555'))
    for polarity,color,marker in [('P','#a54e43','o'),('N','#28769b','s')]:
        xy=np.array([v['center_mm'] for v in design['legs'] if v['stage']==st and v['polarity']==polarity])
        assert len(xy) == [29,11,4][st]
        ax.scatter(xy[:,0],xy[:,1],s=17,c=color,marker=marker,zorder=3)
    ax.set_title(f'Stage {st+1}: {[29,11,4][st]} couples',fontsize=11,pad=7)
    ax.set_xlabel('x (mm)',fontsize=10)
    ax.set_ylabel('y (mm)',fontsize=10)
    ax.set_aspect('equal')
    ax.grid(alpha=.15,zorder=0)
handles=[Line2D([0],[0],marker='o',color='none',markerfacecolor='#a54e43',
                markeredgecolor='#a54e43',markersize=6,label='P-type legs'),
         Line2D([0],[0],marker='s',color='none',markerfacecolor='#28769b',
                markeredgecolor='#28769b',markersize=6,label='N-type legs')]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.025),ncol=2,
           frameon=False,fontsize=9.5,columnspacing=2.5)
save(fig,'v33_topology_legible')

# 2/3: V3.5 fixed-field hypotheses. Footnotes are placed OUTSIDE the axes.
screen=load(ROOT/'data/v3_5_power_lead_and_copper_sensitivity_20261108/fixed_source_field_screen.json')
rows=[next(x for x in screen['lead_screen'] if x['alloy']==mode and
           x['internal_wire_routing_length_factor']==1.)
      for mode in ('copper','nickel_proxy','fecral_screen')]
xx=np.arange(3)
h1=np.array([x['separate_native_pad_heat_W']['8']*1e3 for x in rows])
h9=np.array([x['separate_native_pad_heat_W']['36']*1e3 for x in rows])
fig=plt.figure(figsize=(8.8,4.9),facecolor='white')
ax=fig.add_axes([.115,.245,.855,.63])
ax.bar(xx-.15,h1,width=.30,label='Pin 1 / original face 8',color='#527c99')
ax.bar(xx+.15,h9,width=.30,label='Pin 9 / original face 36',color='#b16d44')
ax.axhline(0,color='#4a5055',lw=1)
ax.set_xticks(xx,['Copper','Nickel proxy','FeCrAl screen'])
ax.set_ylim(min(h1.min(),h9.min())-2,max(h1.max(),h9.max())+2)
ax.set_ylabel('Heat into original ceramic pad (mW)')
ax.set_title('Separate supply leads: signed heat at individual ceramic pads',fontsize=12.2,pad=9,fontweight='bold')
ax.legend(frameon=False,loc='upper left',fontsize=9)
ax.grid(axis='y',alpha=.2)
ax.set_axisbelow(True)
fig.text(.115,.06,'Fixed V3.4 pad-temperature field; NOT re-solved device temperatures.',
         color='#536579',fontsize=9)
save(fig,'v35_fixed_field_lead_heat_screen_legible')

sweep=[d for d in screen['interstage_Cu_contact_screen'] if d['r_thermal_contact_area_m2K_W']>0]
a=np.array([d['r_thermal_contact_area_m2K_W'] for d in sweep])
b=np.array([d['original_source_Cu_heat_into_stage_mW'][2] for d in sweep])
fig=plt.figure(figsize=(8.5,4.75),facecolor='white')
ax=fig.add_axes([.135,.260,.835,.61])
ax.semilogx(a,b,'o-',color='#496e8b',linewidth=2.3,markersize=8)
ax.axvline(1e-6,color='#b27347',ls='--',lw=1.35,label='Nominal V3.5 contact hypothesis')
ax.set_ylim(min(b)-4,max(b)+6)
ax.set_xlabel('Effective Cu-foil contact areal thermal resistance (m² K/W)')
ax.set_ylabel('Cu heat entering upper ceramic (mW)')
ax.set_title('Interstage Cu contact resistance: fixed-field thermal screen',fontsize=12.2,fontweight='bold',pad=9)
ax.grid(alpha=.22,which='both')
ax.legend(frameon=False,loc='upper right',fontsize=9)
fig.text(.135,.065,'Source V3.4 pad temperatures held fixed; this is NOT a coupled Tdetector sweep.',
         color='#536579',fontsize=9)
save(fig,'v35_fixed_field_interstage_contact_screen_legible')

# 4: V3.6 full current envelope. Avoid on-line numeric labels: values are
# retained in the report's exact source-derived operating-point table.
current_cases=['I025_Q002_corrected','I040_Q002','I055_Q002_corrected','I060_Q002_corrected']
dats=[verify_result(name,'data/v3_6_operating_envelope_20261109') for name in current_cases]
I=np.array([d['operating_current_A'] for d in dats]);T=np.array([d['calculated_detector_temperature_K'] for d in dats]);P=np.array([d['electrical_power_W'] for d in dats])
assert np.all(np.diff(I)>0) and len(I)==4
fig=plt.figure(figsize=(10.8,5.25),facecolor='white')
left=fig.add_axes([.075,.255,.39,.565]);right=fig.add_axes([.585,.255,.355,.565])
for ax,y,color,ylabel,title,yspan in [
    (left,T,'#326480','Calculated HgCdTe temperature (K)','Detector cooling',(-5,5)),
    (right,P,'#b16d44','TEC electrical input (W)','Electrical power cost',(-.14,.16))]:
    ax.plot(I,y,'o-',lw=2.0,ms=7.2,color=color)
    ax.set_xlim(.21,.63)
    ax.set_xticks(I)
    ax.set_xlabel('TEC drive current (A)')
    ax.set_ylabel(ylabel)
    ax.set_title(title,loc='left',fontsize=11.2,fontweight='bold')
    ax.grid(axis='y',color='#dfe6eb',lw=.75)
left.set_ylim(T.min()-6,T.max()+5)
right.set_ylim(0,P.max()*1.15)
# Exact point values remain in the source-derived table adjacent to this plot.
# Avoid plotting a second numeric row beneath the current-axis labels.
fig.text(.074,.946,'TEC operating envelope: cooling versus electrical input',
         fontsize=15.3,fontweight='bold',color='#233a50')
fig.text(.074,.895,'300 K sink  |  2.00 mW imposed die heat  |  100 Pa Kr  |  fixed V3.5 architecture',
         fontsize=9.8,color='#526779')
fig.text(.075,.060,'Four independently solved source cases; exact T and P values are tabulated in the report. Lines only guide the eye.',
         fontsize=8.7,color='#60758a')
save(fig,'v36_current_temperature_power_legible')

# 5: V3.11 pressure curve. Relocate the vacuum value away from the rising
# segment; no interpolation of points or modification of effective-gap law.
s=load(ROOT/'data/v3_11_rev3_backfill_source_20261109/accepted_gas_pressure_source_summary.json')
lookup={d['case']:d for d in s['cases']}
order=['vacuum_I040','Kr100_I040','Kr30k_I040','Kr101k_I040']
y=np.array([lookup[n]['detector_mount_K'] for n in order])
x=np.arange(len(y))
fig=plt.figure(figsize=(8.6,4.6),facecolor='white')
ax=fig.add_axes([.11,.22,.79,.63])
ax.plot(x,y,'o-',color='#2b6c83',lw=2.1,ms=7.6)
ax.set_xticks(x,['Vacuum','100 Pa','30 kPa','101 kPa'])
ax.set_ylim(218.38,219.01)
ax.set_xlim(-.18,3.2)
ax.set_ylabel('Detector mounting temperature (K)')
ax.grid(axis='y',alpha=.17)
for i,val in enumerate(y):
    if i==0:
        continue  # Vacuum numeric value appears in the figure footer and source table.
    dx,dy,ha=(0,12,'center')
    ax.annotate(f'{val:.3f} K',(i,val),xytext=(dx,dy),textcoords='offset points',
                ha=ha,fontsize=9.2,color='#1f3545',
                bbox=dict(facecolor='white',edgecolor='none',alpha=.88,pad=.75))
fig.text(.095,.954,'Krypton backfill: discrete modeled operating states',
         fontsize=15.0,weight='bold',color='#213b4e')
fig.text(.095,.895,'Fixed TEC 0.400 A; source solid paths and imposed die heat unchanged',
         fontsize=9.4,color='#526779')
fig.text(.095,.085,'Vacuum: 218.437 K. All four points are independently accepted source-geometry cases.',
         fontsize=8.7,color='#60758a')
fig.text(.095,.048,'Pressure response is conditional on the assumed 3 mm effective gas gap.',
         fontsize=8.7,color='#60758a')
save(fig,'v311_krypton_pressure_sensitivity_legible')

# Complete independent provenance: the frozen files stay untouched.
provenance={'purpose':'Figure-text collision correction, no physics reruns',
            'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(set(INPUTS))},
            'outputs_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in OUTPUTS}}
(HERE/'plot_legibility_manifest.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('PLOT_QA_OUTPUTS',len(OUTPUTS),'INPUTS',len(provenance['input_sha256']))
for file in OUTPUTS:
    print(file.relative_to(ROOT),file.stat().st_size)
