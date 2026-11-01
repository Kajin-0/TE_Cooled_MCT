"""Solver-free diagrams and comparison of the frozen separate design candidate."""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .tec_candidate_study import DATA,metrics
from .tec_material_plausibility import ROOT,read,write,sha
from . import graded_tec


def present(folder=DATA,output=None):
    folder=Path(folder);out=Path(output) if output is not None else folder/'presentation'
    if (output is None and (folder/'checksums.json').exists()) or (output is not None and out.exists()):
        raise ValueError('Sealed checkpoint or existing output; choose an absent --out directory')
    out.mkdir(parents=True,exist_ok=True)
    study=folder/'study';a=read(study/'analysis.json');cases=read(study/'cases.json');d=read(folder/'geometry/design.json')
    old=read(ROOT/'data/tec_material_plausibility_20261101/oem_comparison.json')['rows'];rows=[]
    for r in old:
        if r['panel']!='300K_vacuum' or r['hypothesis']!='nominal':continue
        x=dict(source_id=r['source_id'],field=r['field'],status='REJECTED',reason=r.get('reason'))
        if 'model_value' in r:x.update(status='ACCEPTED',absolute_difference=r['absolute_difference'],signed_difference=r['signed_difference'],relative_difference=r['signed_relative_difference'])
        rows.append(x)
    selected=a['rows'];source={r['source_id']:r for r in selected}
    def row(Q,field):return next(r for r in selected if r['current_A']==1 and r['load_W']==Q and r['field']==field)
    source_secant=(row(0,'delta_t_k')['source_value']-row(.41,'delta_t_k')['source_value'])/.41
    model_secant=(row(0,'delta_t_k')['model']-row(.41,'delta_t_k')['model'])/.41
    nofit=read(study/'no_fit_comparison.json')['rows']
    common=set(r['source_id'] for r in rows if r['status']=='ACCEPTED') & set(r['source_id'] for r in nofit if r['status']=='ACCEPTED')
    # Post-hoc omission audit ONLY: geometry was frozen before any curve result.
    # These 1D estimates are not a new coupled model, observed heat or fit targets.
    rho_cu=1.72e-8;conductors=[]
    for node,points in d['Cu_routes_mm'].items():
        length=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum())*.001
        conductors.append(dict(node=node,length_m=length,area_m2=.1e-3*.03e-3,
            R_ohm_estimate=rho_cu*length/(.1e-3*.03e-3)))
    pair_R=85*rho_cu*.58e-3/(.44e-3*.03e-3)
    tails_R=2*rho_cu*1.5e-3/(np.pi*(.1e-3)**2)
    Cu_R=sum(x['R_ohm_estimate'] for x in conductors)+pair_R+tails_R
    pn={p:graded_tec.props(p,300.) for p in ('P','N')}
    bulk_R=44*.5e-3/.16e-6*(pn['P']['rho']+pn['N']['rho'])
    data=dict(original_reference_metrics=metrics(rows),no_fit_metrics=a['no_fit_metrics'],calibration_selected_metrics=a['all20_metrics'],
        evaluation_metrics=a['evaluation16_metrics'],source_lift_load_secant_K_W=source_secant,
        candidate_lift_load_secant_K_W=model_secant,relative_secant_excess=model_secant/source_secant-1,
        interpretation='Fixed-current finite-load secants; not passive thermal resistance or identification of k/contact cause.',
        common_support_observables=len(common),common_support_original=metrics([r for r in rows if r['source_id'] in common]),
        common_support_no_fit=metrics([r for r in nofit if r['source_id'] in common]),
        common_support_selected=metrics([r for r in selected if r['source_id'] in common]),
        post_hoc_Cu_omission_audit=dict(routes=conductors,ordinary85_pair_links_R_ohm_estimate=pair_R,
            lead_tails_R_ohm_estimate=tails_R,total_Cu_R_ohm_estimate=Cu_R,Joule_W_at_1A_estimate=Cu_R,
            nominal_uniform300K_bulk_R_ohm=float(bulk_R),calibrated_uniform300K_effective_R_ohm=float(bulk_R*a['selected_scales_S_rho_k'][1]),
            Cu_rho_proxy_ohm_m=rho_cu,provenance='Original frozen wire-route bulk proxy; not measured candidate Cu',
            limitations='1D centerline estimates omit spreading/corner/stub/contact changes. Not coupled into any reported curve. Fitted effective rho may absorb omissions; adding Cu afterward risks double counting.'),
        output_disposition='STOP full alignment; geometry PASS; no qualified datasheet-aligned release or actual package prediction',
        input_sha256={str(p.relative_to(ROOT)):sha(p) for p in (study/'analysis.json',study/'cases.json',folder/'geometry/design.json')})
    for key in ('common_support_original','common_support_no_fit','common_support_selected'):
        data[key]['thresholds_on_common_subset_only']=data[key].pop('alignment_PASS')
        data[key]['full_candidate_qualification']=False
    write(out/'comparison.json',data)
    colors={'N':'#3b6c96','P':'#b77b3b','Al2O3':'#b5bac0','Cu':'#b64d3c','SnSb':'#dbcb98','Attach':'#887b98','MCT':'#34645a'}
    fig=plt.figure(figsize=(11,5.6),layout='constrained');ax=fig.add_subplot(121,projection='3d');section=fig.add_subplot(122)
    fig.set_constrained_layout_pads(w_pad=.15,h_pad=.06,wspace=.16)
    for body in d['bodies']:
        for box in body['boxes_mm']:
            x,y,z,w,h,t=box
            vertices=np.array([[x,y,z],[x+w,y,z],[x+w,y+h,z],[x,y+h,z],[x,y,z+t],[x+w,y,z+t],[x+w,y+h,z+t],[x,y+h,z+t]])
            faces=[vertices[ix] for ix in ([0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7])]
            ax.add_collection3d(Poly3DCollection(faces,facecolor=colors[body['kind']],edgecolor='none',alpha=.18 if body['kind']=='Al2O3' else .85))
            if y-1e-9<=-.29<=y+h+1e-9:section.add_patch(Rectangle((x,z),w,t,facecolor=colors[body['kind']],edgecolor='none'))
    ax.set(xlim=(-3.4,3.4),ylim=(-3.6,3.3),zlim=(0,4.1),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)')
    ax.set_box_aspect((1,1,.7));ax.view_init(elev=25,azim=-55)
    ax.text2D(0.,1.01,'Blue N / brown P / red Cu / gray alumina',transform=ax.transAxes,fontsize=8)
    for tail in d['lead_tails']:
        phi=np.linspace(0,2*np.pi,24);Y,phi=np.meshgrid([tail['y_start_mm'],tail['y_end_mm']],phi)
        ax.plot_surface(tail['x_mm']+.1*np.cos(phi),Y,.7+.1*np.sin(phi),color=colors['Cu'],linewidth=0)
    ax.set_ylim(-5.2,3.3)
    section.set(xlim=(-3.4,3.4),ylim=(-.1,4.15),xlabel='x (mm)',ylabel='z (mm)',title='Actual primitive section, y = −0.29 mm')
    section.set_aspect('equal');section.grid(alpha=.15)
    fig.suptitle('Separate 29/11/4 candidate: 88 legs and geometric Cu routing\nExact CSG primitives matching STEP volumes; no thermal field or package-pin integration',fontsize=10)
    fig.savefig(out/'candidate_geometry.png',dpi=200);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    Igrid=[.1,.2,.4,.6,.8,1.]
    for Q,color in zip((0,.1,.2),('#315d85','#ab6c25','#3b7853')):
        for field,ax in zip(('delta_t_k','voltage_v'),axes[0]):
            rr=[next((r for r in selected if r['current_A']==I and r['load_W']==Q and r['field']==field),None) for I in Igrid]
            ax.plot(Igrid,[r.get('model',np.nan) if r else np.nan for r in rr],color=color,label=f'Candidate Q={Q:g} W')
            good=[r for r in rr if r]
            ax.errorbar([r['current_A'] for r in good],[r['source_value'] for r in good],yerr=[r['digitization_bound'] for r in good],fmt='o',ms=3,color=color,capsize=2,ls='none')
    for field,ax in zip(('delta_t_k','voltage_v'),axes[1]):
        Qs=[0,.1,.2,.31,.41];sel=[next(r for r in selected if r['current_A']==1 and r['load_W']==Q and r['field']==field) for Q in Qs]
        orig=[next(r for r in nofit if r['current_A']==1 and r['load_W']==Q and r['field']==field) for Q in Qs]
        ax.plot(Qs,[r['source_value'] for r in sel],'ko--',label='Manufacturer digitization',ms=4)
        ax.plot(Qs,[r['model'] for r in sel],'-o',color='#315d85',label='Calibration-selected',ms=3)
        ax.plot(Qs,[r.get('model',np.nan) for r in orig],'-s',color='#ab6c25',label='No-fit; rejected gap retained',ms=3)
        ax.set_xlabel('Cold heat load Qc (W), at I = 1 A')
    for ax in axes.flat:ax.grid(alpha=.2)
    axes[0,0].set_ylabel('Cold-ceramic lift (K)');axes[1,0].set_ylabel('Cold-ceramic lift (K)')
    axes[0,1].set_ylabel('Module voltage (V)');axes[1,1].set_ylabel('Module voltage (V)')
    for ax in axes[0]:ax.set_xlabel('Current (A)')
    axes[0,0].legend(fontsize=8);axes[1,1].legend(fontsize=8)
    axes[0,1].plot([],[],'ko',ms=3,label='Dots / bars: digitized source');axes[0,1].legend(fontsize=8,loc='upper left')
    fig.suptitle('300.15 K, module alone, ideal vacuum surrogate; assumed >300 K transport\nPreviously seen source points; full alignment FAIL (maximum lift error 25.11 K)',fontsize=10)
    fig.savefig(out/'matched_curves.png',dpi=210);plt.close(fig)
    print(data)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=DATA);p.add_argument('--out',type=Path)
    args=p.parse_args();present(args.folder,args.out)
