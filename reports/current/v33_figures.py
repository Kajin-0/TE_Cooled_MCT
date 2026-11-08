"""Revision 3.3 figures exclusively from frozen numerical evidence; no solve."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.ticker import FormatStrFormatter
from tecooledmct.graded_tec import props
from ..master.history import ROOT,sha

BASE='data/v3_3_cavity_package_feedback_20261108/attempt02/'
SOURCES=[BASE+'result.json',BASE+'registration.json',BASE+'independent_read_only_acceptance.json',BASE+'source_native_ceramics_V3_3.npz','data/v3_3_cavity_package_feedback_20261108/manifest.json','reports/current/inputs/v33_ceramic_connectivity.npz','reports/current/inputs/v33_ceramic_connectivity.json','data/synthetic_v3_assembly_20261102/source_final/design.json','data/g2c/zhang2025_he_40_300_v2.json','data/v1_integrated_full_package_20261107/attempt01/result.json','data/v2_integrated_spatial_20261107/attempt02/v2_integrated_result.json','data/v3_integrated_leg_resolved_20261107/attempt01/result.json','data/v3_1_native_pad_feedback_20261107/attempt02/result.json','data/v3_2_joint_loss_feedback_20261107/attempt01/result.json']
def read(name):return json.loads((ROOT/name).read_text())

def generate(out):
    d=read(BASE+'result.json');reg=read(BASE+'registration.json');accept=read(BASE+'independent_read_only_acceptance.json');manifest=read('data/v3_3_cavity_package_feedback_20261108/manifest.json')
    for key,h in manifest['attempt02_evidence_SHA256'].items():assert sha(ROOT/BASE/key)==h,key
    assert accept['numerical_accepted'] and d['outer_iterations']==5 and d['source_individual_leg_count']==88
    assert d['original_ceramic_TET4']==11791 and d['source_stage_couples']==[29,11,4]
    assert d['max_last_spatial_temperature_update_K']<reg['outer_thermal_field_tolerance_K']
    assert abs(d['global_thermoelectric_energy_residual_W'])<reg['global_energy_tolerance_W']
    assert read('reports/current/inputs/v33_ceramic_connectivity.json')['source_mesh_sha256']==reg['original_mesh_SHA256']
    fields=np.load(ROOT/(BASE+'source_native_ceramics_V3_3.npz'));conn=np.load(ROOT/'reports/current/inputs/v33_ceramic_connectivity.npz')
    design=read('data/synthetic_v3_assembly_20261102/source_final/design.json');legs=d['source_individual_leg_flux_and_electric_results'];out=Path(out);fd=out/'figures';fd.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    made=[]
    def save(fig,name):
        for ext in ('pdf','png'):
            p=fd/(name+'.'+ext);kw={'metadata':{'CreationDate':None,'ModDate':None,'Author':'','Creator':'Engineering assessment'}} if ext=='pdf' else {}
            fig.savefig(p,dpi=350,bbox_inches='tight',pad_inches=.07,**kw);made.append(p)
        plt.close(fig)
    # Actual source positions and ceramic footprints, not invented conductors.
    fig,axs=plt.subplots(1,3,figsize=(6.5,2.7),layout='constrained')
    for st,ax in enumerate(axs):
        for width,ls in [(reg['original_CAD_ceramic_halfwidth_mm'][st]*2,'--'),(reg['original_CAD_ceramic_halfwidth_mm'][st+1]*2,'-')]:
            ax.add_patch(plt.Rectangle((-width/2,-width/2),width,width,fill=False,ls=ls,lw=.8,color='#555555'))
        for pol,c,marker in [('P','#a54e43','o'),('N','#28769b','s')]:
            x=np.array([v['center_mm'] for v in design['legs'] if v['stage']==st and v['polarity']==pol]);ax.scatter(x[:,0],x[:,1],s=12,c=c,marker=marker,label=pol)
        ax.set(title=f'Stage {st+1}: {reg["source_stage_couples"][st] if "source_stage_couples" in reg else [29,11,4][st]} couples',xlabel='$x$ (mm)',ylabel='$y$ (mm)');ax.set_aspect('equal');ax.grid(alpha=.15)
    axs[0].legend(loc='lower left');save(fig,'v33_topology')
    # Actual top boundary triangles from saved original tetrahedra; P1 nodal values.
    fig,axs=plt.subplots(2,2,figsize=(6.5,5.4),layout='constrained')
    for i,ax in enumerate(axs.flat):
        xyz=fields[f'ceramic{i}_xyz_mm'];temp=fields[f'ceramic{i}_temperature_K'];t=conn[f'ceramic{i}_tetrahedra_local'];assert len(t)==[4936,4085,1986,784][i]
        faces=np.concatenate([t[:,[0,1,2]],t[:,[0,1,3]],t[:,[0,2,3]],t[:,[1,2,3]]]);mask=np.all(np.isclose(xyz[faces,2],xyz[:,2].max(),atol=1e-9),axis=1);top=faces[mask];assert len(top)>0
        im=ax.tripcolor(mtri.Triangulation(xyz[:,0],xyz[:,1],top),temp,shading='gouraud',cmap='viridis')
        bar=fig.colorbar(im,ax=ax,shrink=.8,label='$T$ (K)',format=FormatStrFormatter('%.3f' if i==3 else '%.2f'));bar.ax.tick_params(labelsize=7)
        ax.set(title=f'Ceramic {i}',xlabel='$x$ (mm)',ylabel='$y$ (mm)');ax.set_aspect('equal')
    save(fig,'v33_ceramic_fields')
    # A single matched current is shown, not an invented IV sweep.
    paths=SOURCES[9:];q=[read(p) for p in paths]
    Ts=[q[0]['predicted_all_five_thermal_nodes_K']['MCT_die'],q[1]['full_detector_die_temperature_K'],q[2]['detector_temperature_K'],q[3]['calculated_detector_temperature_K'],q[4]['calculated_detector_temperature_K'],d['calculated_detector_temperature_K']]
    Vs=[z['terminal_voltage_V'] for z in q]+[d['terminal_voltage_V']];names=['V1','V2','V3','V3.1','V3.2','V3.3'];x=np.arange(6)
    fig,axs=plt.subplots(1,2,figsize=(6.5,2.7),layout='constrained')
    for ax,vals,label in zip(axs,(Ts,Vs),('Detector temperature (K)','Terminal voltage (V)')):
        ax.plot(x,vals,'o-',color='#256888');ax.set_xticks(x,names);ax.set_ylabel(label);ax.grid(alpha=.2)
    save(fig,'v33_versions')
    fig,ax=plt.subplots(figsize=(6.5,2.8),layout='constrained');x=np.arange(4);gas=np.array(d['cavity_gas_heat_into_three_ceramics_and_die_W'])*1e3;rad=np.array(d['gray_radiation_heat_into_three_ceramics_and_die_W'])*1e3
    ax.bar(x-.18,gas,.36,label='Krypton',color='#35758b');ax.bar(x+.18,rad,.36,label='Gray radiation',color='#c17b31');ax.set_xticks(x,['Ceramic 1','Ceramic 2','Ceramic 3','Detector']);ax.set_ylabel('Heat into cold node (mW)');ax.legend(ncol=2);ax.grid(axis='y',alpha=.2);save(fig,'v33_cavity_loads')
    fig,axs=plt.subplots(1,3,figsize=(6.5,2.5),layout='constrained')
    for pol,c in [('P','#a54e43'),('N','#28769b')]:
        for key,ax,label,scale in zip(('S','rho','k'),axs,('$S$ ($\\mu$V K$^{-1}$)','$\\rho$ ($\\mu\\Omega$ m)','$k$ (W m$^{-1}$ K$^{-1}$)'),(1e6,1e6,1)):
            for low,high,ls in ((180,300,'-'),(300,390,'--')):
                x=np.linspace(low,high,121);ax.plot(x,props(pol,x)[key]*scale,ls,c=c,label=pol if low==180 else None)
            ax.axvspan(300,390,color='#f0ead7',zorder=-1);ax.set(xlabel='$T$ (K)',ylabel=label);ax.grid(alpha=.2)
    axs[0].legend();save(fig,'v33_transport')
    fig,axs=plt.subplots(2,1,figsize=(6.5,4.2),sharex=True,layout='constrained');x=np.arange(88)
    colors=['#a54e43' if z['material']=='P' else '#28769b' for z in legs]
    axs[0].scatter(x,[z['Qcold_W']*1000 for z in legs],c=colors,s=11);axs[0].set_ylabel('$Q_c$ (mW leg$^{-1}$)')
    axs[1].scatter(x,[z['terminal_contribution_V']*1000 for z in legs],c=colors,s=11);axs[1].set(ylabel='Leg voltage (mV)',xlabel='Source leg index in series order')
    for ax in axs:
        for boundary in (57.5,79.5):ax.axvline(boundary,color='gray',ls='--',lw=.8)
        ax.grid(alpha=.2)
    save(fig,'v33_leg_budgets')
    history=d['spatial_outer_iteration_history'];fig,axs=plt.subplots(1,2,figsize=(6.5,2.65),layout='constrained')
    axs[0].semilogy([z['outer_iteration'] for z in history],[z['spatial_pad_K_max_change'] for z in history],'o-',color='#256888');axs[0].axhline(reg['outer_thermal_field_tolerance_K'],ls='--',color='#a54e43',label='Registered limit');axs[0].set(xlabel='Outer iteration',ylabel='Maximum pad change (K)');axs[0].legend()
    axs[1].plot([z['outer_iteration'] for z in history],[z['die_K'] for z in history],'o-',color='#a54e43');axs[1].set(xlabel='Outer iteration',ylabel='Detector temperature (K)')
    for ax in axs:ax.set_xticks(range(1,6));ax.grid(alpha=.2)
    save(fig,'v33_iterations')
    rows=[]
    for i,z in enumerate(d['source_stage_thermoelectric_budget']):rows.append(f'{i+1} & {z["nlegs"]} & {z["qc_w"]*1000:.3f} & {z["qh_w"]*1000:.3f} & {z["voltage_v"]:.6f}'+r' \\')
    (out/'v33_numerics.tex').write_text('\\newcommand{\\VThreeStageRows}{'+'\n'.join(rows)+'}\n')
    info=json.loads((out/'report_inputs.json').read_text())
    for name in SOURCES:info['inputs'][name]=sha(ROOT/name)
    for p in made:info['figures'][p.name]=sha(p)
    info['figure_generators']['reports/current/v33_figures.py']=sha(ROOT/'reports/current/v33_figures.py')
    info['v33_scope']={'source_ceramic_tetrahedra':11791,'source_legs':88,'stages':[29,11,4],'outer_iterations':5,'gas_native_PDE':False,'three_dimensional_PN_transport':False,'full_430_domain_coupled_PDE':False,'archived_fields_used':True,'new_solves':0}
    (out/'report_inputs.json').write_text(json.dumps(info,indent=2)+'\n')
    return info['v33_scope']
