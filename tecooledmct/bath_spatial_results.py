"""Collect the controlled coupled pair without mistaking a plateau for release."""
import argparse,json
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
RAW=ROOT/'outputs/bath-spatial'
def read(p):return json.loads(p.read_text())
def collect():
    baseline=read(ROOT/'fem/results/cold20_completion_20261030/cases/bath_coupled/metrics.json');cases=[]
    for label in ['transverse1','transverse2']:
        a=read(RAW/(label+'_audit')/'summary.json');g=a['gates'];e=read(RAW/(label+'_case')/'execution.json');metrics=read(RAW/(label+'_case')/'metrics.json')
        if not g['genuine_completed_coupled'] or not g['all_nonraw_gates_passed'] or a['field_sha256']!=e['vtu_sha256']:raise ValueError('Incomplete or mismatched actual field')
        faces=np.load(RAW/(label+'_audit')/'bath_faces.npz');q=lambda x:np.quantile(x,[0,.25,.5,.75,1]).tolist()
        cases.append({'case':label,'mesh_sha256':a['mesh_sha256'],'field_sha256':a['field_sha256'],'tetrahedra':g['tetrahedra'],'nodes':g['nodes'],
            'die_mean_K':g['die_mean_K'],'voltage_V':g['voltage_V'],'cold_mismatches':g['cold_mismatches'],'bath_relative_error':g['bath_relative_error'],
            'bath_raw_1percent_passed':abs(g['bath_relative_error'])<.01,'all_nonraw_gates_passed':True,'solver_status':e['solver_status'],
            'known_input_W':metrics['external_total_power_w'],'signed_powers':a['signed_bath_powers'],'identity':a['identity'],
            'normal_height_um_quantiles':q(faces['normal_height_m']*1e6),'transverse_face_edge_um_quantiles':q(faces['tangential_face_max_edge_m']*1e6),
            'apex_offset_over_height_quantiles':q(np.linalg.norm(faces['apex_offset_xy_m'],axis=1)/faces['normal_height_m']),
            'die_change_from_parent_K':g['die_mean_K']-baseline['die_mean_k'],'voltage_change_from_parent_V':g['voltage_V']-baseline['voltage_v']})
    pass_both=all(x['bath_raw_1percent_passed'] for x in cases);monotone=abs(cases[1]['bath_relative_error'])<abs(cases[0]['bath_relative_error'])<abs(baseline['direct_bath_relative_error'])
    permitted=cases[-1]['bath_raw_1percent_passed'] and monotone
    result={'cases':cases,'independent_bath_pair_passed':pass_both,'decreasing_abs_error':monotone,'combined_case_permitted':permitted,
       'combined_status':'NOT RUN: independent bath1%/stable-trend prerequisite unmet' if not permitted else 'conditional pending original checks',
       'qualified_comparator_status':'NOT RUN','full_numerical_release':False,'OEM_validated':False,'whole_device_GCI':False,
       'pair_die_change_K':cases[1]['die_mean_K']-cases[0]['die_mean_K'],'pair_voltage_change_V':cases[1]['voltage_V']-cases[0]['voltage_V'],
       'original_raw_gates':{'bath':.01,'cold':.05},'source_sha256':sha(Path(__file__)),'approved_report_changed':False}
    write(RAW/'device_summary.json',result);return result
def figures(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import SymLogNorm
    if out.exists():raise ValueError('New figure output required')
    out.mkdir(parents=True);s=read(RAW/'device_summary.json');plt.rcParams.update({'font.family':'serif','font.size':10,'axes.titlesize':10,'pdf.fonttype':42});generated=[]
    fig,axs=plt.subplots(1,2,figsize=(7,3.4),layout='constrained')
    for ax,c in zip(axs,s['cases']):
        d=np.load(RAW/(c['case']+'_audit')/'bath_faces.npz');coll=PolyCollection(d['xyz_m'][:,:,:2]*1e3,array=d['density_W_m2'],norm=SymLogNorm(linthresh=1,vmin=-2e4,vmax=2e4),cmap='coolwarm',rasterized=True);ax.add_collection(coll);ax.set(xlim=(-16,16),ylim=(-9,9),xlabel='$x$ (mm)',ylabel='$y$ (mm)',title=f"{c['tetrahedra']:,} tetrahedra\nRaw bath error {c['bath_relative_error']*100:+.4f}%");ax.set_aspect('equal')
    fig.colorbar(coll,ax=axs.tolist(),label='$q_{out}$ (W m$^{-2}$)',shrink=.7,ticks=[-1e4,-1e2,0,1e2,1e4]);generated.append(('coupled_signed_bath',fig))
    fig,axs=plt.subplots(1,2,figsize=(7,3.2),layout='constrained');x=[675496]+[c['tetrahedra'] for c in s['cases']];r=read(ROOT/'fem/results/cold20_completion_20261030/cases/bath_coupled/metrics.json')
    axs[0].plot(np.array(x)/1000,[abs(r['direct_bath_relative_error'])*100]+[abs(c['bath_relative_error'])*100 for c in s['cases']],'o-');axs[0].axhline(1,color='#993333',ls='--',label='Unchanged 1% gate');axs[0].set(xlabel='Tetrahedra ($10^3$)',ylabel='Absolute raw bath error (%)',ylim=(.9,1.4));axs[0].legend(frameon=False,fontsize=9)
    mode=read(RAW/'polynomial_modes.json');z=[c for c in mode['cases'] if c['case'] in ['previous675496','transverse1','transverse2']]
    axs[1].plot(np.array(x)/1000,[abs(c['relative_interpolant_error'])*100 for c in z],'s-',color='#507d61');axs[1].set(xlabel='Tetrahedra ($10^3$)',ylabel='Polynomial-interpolant error (%)',title='Geometry-only diagnostic\nNot a solved device field')
    for ax in axs:ax.grid(alpha=.2)
    generated.append(('coupled_plateau_and_sampling',fig))
    for name,fig in generated:
        for ext in ['pdf','png']:fig.savefig(out/(name+'.'+ext),dpi=600,bbox_inches='tight',**({'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}))
        plt.close(fig)
    write(out/'provenance.json',{'source_sha256':sha(Path(__file__)),'summary_sha256':sha(RAW/'device_summary.json'),'polynomial_diagnostic_sha256':sha(RAW/'polynomial_modes.json'),'files':{p.name:sha(p) for p in out.iterdir() if p.suffix in ['.pdf','.png']}})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--figures',type=Path);a=p.parse_args();collect();figures(a.figures.resolve()) if a.figures else None
