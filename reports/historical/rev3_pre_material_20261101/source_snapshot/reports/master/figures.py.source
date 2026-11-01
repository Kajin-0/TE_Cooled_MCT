"""Scientific figures and numerical tables for the single Rev3 master.

Original field figures are recomputed by their inspected, unchanged generator.
New plots use saved numerical evidence; no physics solve is performed here.
"""
import argparse
import json
from pathlib import Path
import shutil

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

from reports.rev3_review.build import figures as solid_figures,ROOT,read,sha,write
from reports.rev3_review.latest_study import supplement

DATA=ROOT/'data/nonlinear_exchange_20261030'


def generate(out):
    solid_figures(out)
    supplement(out)
    fd=out/'figures';inputs=[];generated=[]
    def get(path):
        inputs.append(path);return read(path)
    def save(fig,name):
        for suffix in ('pdf','png'):
            path=fd/(name+'.'+suffix)
            fig.savefig(path,dpi=400,bbox_inches='tight',pad_inches=.07,
                **({'metadata':{'CreationDate':None,'ModDate':None,'Author':'','Creator':'Engineering assessment'}} if suffix=='pdf' else {}))
            generated.append(path)
        plt.close(fig)
    # Redraw the same two immutable owner-gradient arrays with a case-specific
    # title; the old supplement's historical "Latest bath" label is ambiguous
    # once later transverse evidence is part of the master.
    from matplotlib.colors import Normalize,SymLogNorm
    archive=ROOT/'fem/results/cold_bath_rev3_20261030'
    fig,axs=plt.subplots(1,2,figsize=(6.35,2.8),layout='constrained')
    for ax,label,title in zip(axs,('cold1','bath3'),('Cold normal:\nCeramic trace','Bath normal 2:\nSigned outward flux')):
        mesh=archive/'meshes'/label/'mesh.npz';inputs.append(mesh);p=np.load(mesh)['points']
        path=archive/('cold1_audit/cold/face_4_302.npz' if label=='cold1' else 'bath3_audit/bath/face_data.npz')
        inputs.append(path);d=np.load(path)
        value=-d['power_outward_w'][:,0]/d['areas_m2'] if label=='cold1' else d['outward_density_W_m2']
        norm=Normalize(1700,2200) if label=='cold1' else SymLogNorm(linthresh=1,vmin=-2e4,vmax=2e4)
        coll=PolyCollection(p[d['faces']][:,:,:2]*1000,array=value,norm=norm,
            cmap='viridis' if label=='cold1' else 'coolwarm',edgecolors='none',rasterized=True)
        ax.add_collection(coll);ax.set(xlim=(-.5,.5) if label=='cold1' else (-16,16),
            ylim=(-.5,.5) if label=='cold1' else (-9,9),xlabel='$x$ (mm)',ylabel='$y$ (mm)',title=title)
        ax.set_aspect('equal');fig.colorbar(coll,ax=ax,shrink=.65,label='$q$ (W m$^{-2}$)',
            ticks=None if label=='cold1' else [-1e4,-1e2,0,1e2,1e4])
    save(fig,'latest_raw_flux')
    report=get(DATA/'enclosed_scenarios/summary.json');nominal=report['cases']['nominal_krypton_I0.15']
    transport=get(DATA/'transport/comparison.json');exchange=get(DATA/'exchange/summary.json')
    operator=get(DATA/'exchange/operator_65536.json')
    source=get(ROOT/'data/g2c/zhang2025_he_40_300_v2.json')
    from tecooledmct.graded_tec import props
    fig,axs=plt.subplots(1,3,figsize=(6.5,2.65),layout='constrained')
    for pol,color in [('P','#a04940'),('N','#286687')]:
        for k,label,scale,ax in zip(('S','rho','k'),('$S$ ($\\mu$V K$^{-1}$)','$\\rho$ ($\\mu\\Omega$ m)','$k$ (W m$^{-1}$ K$^{-1}$)'),(1e6,1e6,1),axs):
            for start,end,style in ((180.,300.,'-'),(300.,390.,'--')):
                t=np.linspace(start,end,181)
                ax.plot(t,props(pol,t)[k]*scale,style,color=color,label=pol if start==180 else None)
            ax.axvspan(300,390,color='#ece9dc');ax.set(xlim=(180,390),xlabel='$T$ (K)',ylabel=label);ax.grid(alpha=.2)
    axs[0].legend();save(fig,'material_laws')
    # Native candidate cap/window tetrahedral cut alongside the reduced core.
    from tecooledmct.exchange_geometry import read_msh
    from reports.field_geometry import plane_section
    fixture=ROOT/'fem/results/corrected_enclosure_geometry_20261030'
    inputs.extend([fixture/'cap_window_only.msh',fixture/'corrected_cap_window.step',fixture/'geometry_audit.json'])
    nodes,tets,_=read_msh(fixture/'cap_window_only.msh');ids=sorted(nodes);index={v:i for i,v in enumerate(ids)}
    cp=np.array([nodes[i] for i in ids]);cc=np.array([[index[v] for v in row] for _,row in tets]);cb=np.array([b for b,_ in tets])
    cut=plane_section(cp,cc,axis=1,coordinate=.00015)
    fig,axs=plt.subplots(1,2,figsize=(6.5,4),layout='constrained')
    palette={7301:'#85949c',7302:'#85949c',7303:'#8baebe'}
    axs[0].add_collection(PolyCollection(cut['xyz'][:,:,[0,2]]*1000,
        facecolors=[palette[int(v)] for v in cb[cut['cells']]],edgecolors='none',rasterized=True))
    s=np.load(out/'section.npz');tri=s['xyz_m'][:,:,[0,2]]*1000
    axs[0].add_collection(PolyCollection(tri,facecolors='#c3bda8',edgecolors='none',rasterized=True))
    axs[0].set_title('Native candidate-solid section')
    spec=operator['specification'];r=spec['radius_m']*1000;z0=spec['floor_z_m']*1000;zr=spec['roof_z_m']*1000
    axs[1].plot([-r,-r,r,r], [z0,zr,zr,z0],color='#546b78');axs[1].plot([-r,r],[z0,z0],color='#546b78')
    for i,level in enumerate(spec['levels']):
        bottom=spec['floor_z_m'] if i==0 else spec['levels'][i-1]['top_z_m']
        width=level['side_m']*1000
        axs[1].add_patch(plt.Rectangle((-width/2,bottom*1000),width,(level['top_z_m']-bottom)*1000,
                                      facecolor='#b9afc7',edgecolor='white',linewidth=.7))
    axs[1].set_title('Filled-core exchange proxy')
    for ax in axs:
        ax.set(xlim=(-8.2,8.2),ylim=(1.1,10.5),xlabel='$x$ (mm)',ylabel='$z$ (mm)');ax.set_aspect('equal');ax.grid(alpha=.15)
    save(fig,'candidate_enclosure')
    fig,axs=plt.subplots(1,2,figsize=(6.5,3.1),layout='constrained')
    for name,label,color in [('vacuum_low_parasitic','Low parasitic, vacuum','#286687'),('nominal_krypton','Nominal Kr','#a46a26'),('nitrogen_high_parasitic','High parasitic, N$_2$','#54815a')]:
        for key,ax,ylab in [('MCT_die_k',axs[0],'Die temperature (K)'),('terminal_electrical_power_w',axs[1],'Terminal electrical power (W)')]:
            current=np.arange(21)/20;values=[]
            for value in current:
                case=report['cases'][f'{name}_I{value:.2f}'];values.append(case.get(key,np.nan))
            ax.plot(current,values,'o-',ms=2.5,label=label,color=color);ax.set(xlabel='Series current (A)',ylabel=ylab);ax.grid(alpha=.2)
    axs[0].legend(fontsize=8);save(fig,'operating_sweep')
    measured=[row for row in transport['rows'] if row.get('comparison_scope')=='measured-domain numerical check']
    fig,ax=plt.subplots(figsize=(6.5,2.9),layout='constrained');x=np.arange(len(measured))
    affine=[100*r['affine_errors']['voltage_v']/abs(r['reference64']['voltage_v']) for r in measured]
    nonlinear=[100*r['newton_levels'][1]['errors_against_reference64']['voltage_v']['relative_abs'] for r in measured]
    ax.bar(x-.18,affine,.36,label='Affine temperature');ax.bar(x+.18,nonlinear,.36,label='Nonlinear, 32 intervals')
    ax.set_yscale('log');ax.set(ylabel='Absolute relative voltage error (%)',xlabel='Stage; boundary temperatures (K); current (A)')
    ax.set_xticks(x,[f"{r['stage_index']+1}; {r['hot_k']:.0f}/{r['cold_k']:.0f}\n{r['current_a']:.2f} A" for r in measured],fontsize=7)
    ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2);save(fig,'transport_accuracy')
    sensitivity=report['one_factor_sensitivity'];fig,ax=plt.subplots(figsize=(6.5,3.6),layout='constrained')
    labels={'pn_thermal_conductivity_scale':'P/N thermal conductivity, 0.8–1.2 ×','pn_seebeck_scale':'Seebeck coefficient, 0.9–1.1 ×','pn_resistivity_scale':'P/N resistivity, 0.8–1.2 ×','detector_bias_w':'Bias heat, 0.5–5 mW','cavity_pressure_pa':'Kr pressure, vacuum–101 kPa','gas_area_factor':'Gas-network scale, 0.5–1.5 ×','heat_sink_k_w':'Sink resistance, 0.5–5 K/W','cap_emissivity':'Cap emissivity, 0.08–0.65','au_wire_conductance_scale':'Au conductance, 0.75–1.25 ×','die_attach_conductivity_w_mk':'Attach conductivity, 0.5–3 W/(m K)'}
    rows=list(reversed(sensitivity));ax.barh(np.arange(len(rows)),[r['endpoint_span_abs_k'] for r in rows],color='#286687')
    ax.set_yticks(np.arange(len(rows)),[labels[r['field']] for r in rows],fontsize=8)
    ax.set(xlabel='Absolute endpoint temperature difference (K)');ax.grid(axis='x',alpha=.2);save(fig,'sensitivity')
    fig,axs=plt.subplots(1,2,figsize=(6.5,2.8),layout='constrained')
    rays=[r['rays'] for r in exchange['rows']]
    axs[0].semilogx(rays,[r['ray_audit']['max_absolute_view_factor_correction'] for r in exchange['rows']],'o-')
    axs[0].set(xlabel='Rays per surface',ylabel='Maximum absolute $F$ correction')
    for key,label in [('gas_nodes_w','Gas chord network'),('radiation_nodes_w','Gray radiation')]:
        axs[1].semilogx(rays,[r['exchange'][key][4]*1000 for r in exchange['rows']],'o-',label=label)
    axs[1].set(xlabel='Rays per surface',ylabel='Heat into die (mW)');axs[1].legend(fontsize=8)
    for ax in axs:ax.grid(alpha=.2)
    save(fig,'ray_refinement')
    paths=nominal['heat_paths_w'];fig,ax=plt.subplots(figsize=(6.5,2.65),layout='constrained')
    x=np.arange(4);bottom=np.zeros(4)
    for key,label,color in [('gas_w','Gas','#6d9ba9'),('radiation_w','Radiation','#c28b43')]:
        v=np.array(paths[key])*1000;ax.bar(x,v,bottom=bottom,label=label,color=color);bottom+=v
    au=np.array([0,0,0,paths['Au_wires_into_die_w']*1000]);ax.bar(x,au,bottom=bottom,label='Au conduction',color='#96774d');bottom+=au
    internal=np.array([0,0,0,.002*1000]);ax.bar(x,internal,bottom=bottom,label='Imposed die heat',color='#8b759c')
    ax.set_xticks(x,['Intermediate 1','Intermediate 2','Cold ceramic','Die']);ax.set(ylabel='Heat input (mW)');ax.legend(ncol=2,fontsize=8);ax.grid(axis='y',alpha=.2);save(fig,'reduced_heat_budget')
    # Data-driven tables; all extra digits are numerical audit identifiers.
    tex=[]
    def macro(name,value):tex.append('\\newcommand{\\'+name+'}{'+str(value)+'}')
    rows=[]
    for name,label in [('vacuum_low_parasitic','Low-parasitic vacuum'),('nominal_krypton','Nominal Kr'),('nitrogen_high_parasitic','High-parasitic nitrogen')]:
        c=report['cases'][name+'_I0.15']
        rows.append(f"{label} & {c['MCT_die_k']:.3f} & {c['terminal_voltage_v']:.5f} & {c['terminal_electrical_power_w']*1000:.3f} & {c['bath_rejected_power_w']*1000:.3f}"+r' \\')
    macro('OperatingRows','\n'.join(rows))
    macro('ReducedDie',f"{nominal['MCT_die_k']:.3f}");macro('ReducedVoltage',f"{nominal['terminal_voltage_v']:.5f}")
    rows=[]
    for i,s in enumerate(nominal['stage_budget']):
        rows.append(f"{i+1} & {s['qc_w']*1000:.3f} & {s['qh_w']*1000:.3f} & {s['voltage_v']:.5f} & {s['joule_w']*1000:.3f}"+r' \\')
    macro('ReducedStageRows','\n'.join(rows))
    reservoir=-sum(paths['enclosure_reservoir_into_w'])
    pin=paths['Cu_conduction_into_hot_w']-.5*paths['Cu_total_joule_w']
    budget=[('Terminal electrical input',nominal['terminal_electrical_power_w']),('Imposed die heat',.002),('Net header/cap/window heat into device',reservoir),('Au warm-end conduction into die',paths['Au_wires_into_die_w']),('Cu pin-end thermal input (signed)',pin),('Heat rejected at effective sink',nominal['bath_rejected_power_w'])]
    macro('BudgetRows','\n'.join(label+f' & {value*1000:+.6f}'+r' \\' for label,value in budget))
    spatial=get(ROOT/'fem/results/bath_spatial_device_20261030/device_summary.json')
    rows=[]
    for label,c in zip(('Transverse volume 1','Transverse volume 2'),spatial['cases']):
        metrics=get(ROOT/'fem/results/bath_spatial_device_20261030/cases'/c['case']/'metrics.json')
        rows.append(f"{label} & {c['tetrahedra']:,} & {metrics['die_mean_k']:.6f} & {metrics['voltage_v']:.9f} & {c['bath_relative_error']*100:+.4f}"+r' \\')
    macro('SpatialRows','\n'.join(rows))
    (out/'master_numerics.tex').write_text('\n'.join(tex)+'\n')
    d=read(out/'report_inputs.json');d['edition_kind']='CONTINUOUS REV3 MASTER';d['review_draft']=False
    d['old_report_unchanged']=True;d['original_rev3_historical_snapshot_preserved']=True
    for path in inputs:d['inputs'][str(path.relative_to(ROOT))]=sha(path)
    for path in generated:d['figures'][path.name]=sha(path)
    d['master_scope']={'nonlinear_leg_intervals':32,'accepted_proxy_cases':len(report['summary_rows']),
        'total_proxy_cases':len(report['cases']),'full_native_cavity_visibility':False,
        'new_enclosed_3D_field':False,'ray_max_absolute_correction':exchange['rows'][-1]['ray_audit']['max_absolute_view_factor_correction']}
    d['figure_generators']={name:sha(ROOT/name) for name in (
        'reports/master/figures.py','reports/rev3_review/build.py',
        'reports/rev3_review/latest_study.py','reports/field_geometry.py',
        'tecooledmct/graded_tec.py','tecooledmct/material_profiles.py')}
    write(out/'report_inputs.json',d)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.out)
