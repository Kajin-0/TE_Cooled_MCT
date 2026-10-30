"""Actual signed flux, fixed-patch diagnostics and transverse sampling figures."""
import json
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
def render(audit,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import SymLogNorm
    if out.exists():raise ValueError('New figure label required')
    out.mkdir(parents=True);study=json.loads((audit/'summary.json').read_text());generated=[]
    plt.rcParams.update({'font.family':'serif','font.size':10,'axes.labelsize':10,'axes.titlesize':10,'xtick.labelsize':9,'ytick.labelsize':9,'pdf.fonttype':42})
    names=['Fine baseline','Full owner-star level','Normal depth halved','Normal depth halved again']
    fig,axs=plt.subplots(2,2,figsize=(7,5.4),layout='constrained')
    arrays=[]
    for ax,case,name in zip(axs.ravel(),study['cases'],names):
        d=np.load(audit/case['case']/'bath_faces.npz');arrays.append(d)
        coll=PolyCollection(d['xyz_m'][:,:,:2]*1e3,array=d['density_W_m2'],norm=SymLogNorm(linthresh=1,vmin=-2e4,vmax=2e4),cmap='coolwarm',edgecolors='none',rasterized=True);ax.add_collection(coll);ax.set(xlim=(-16,16),ylim=(-9,9),xlabel='$x$ (mm)',ylabel='$y$ (mm)',title=f"{name}\nRaw error {case['raw_relative_error']*100:+.4f}%");ax.set_aspect('equal')
    fig.colorbar(coll,ax=axs.ravel().tolist(),shrink=.8,label='Signed outward $q$ (W m$^{-2}$)',ticks=[-1e4,-1e2,0,1e2,1e4]);generated.append(('signed_raw_bath',fig))
    fig,axs=plt.subplots(1,2,figsize=(7,3.0),layout='constrained')
    for d,name in zip(arrays,names):
        ratio=np.linalg.norm(d['apex_offset_xy_m'],axis=1)/d['normal_height_m'];order=np.argsort(ratio);weights=d['areas_m2'][order];axs[0].plot(ratio[order],np.cumsum(weights)/weights.sum(),label=name)
        xx=d['tangential_face_max_edge_m']*1e6;order=np.argsort(xx);axs[1].plot(xx[order],np.cumsum(d['areas_m2'][order])/d['areas_m2'].sum(),label=name)
    axs[0].set(xlim=(0,10),xlabel='Transverse apex offset / normal height',ylabel='Cumulative bath area fraction');axs[1].set(xlabel='Maximum face edge ($\\mu$m)',ylabel='Cumulative bath area fraction');axs[1].legend(fontsize=8,frameon=False)
    for ax in axs:ax.grid(alpha=.2)
    generated.append(('owner_sampling',fig))
    a,z=arrays[-2:];lookup={tuple(sorted(face)):i for i,face in enumerate(a['faces'])};ix=np.array([lookup[tuple(sorted(face))] for face in z['faces']])
    if not np.allclose(a['areas_m2'][ix],z['areas_m2'],atol=1e-20,rtol=1e-12):raise ValueError('Matched bath triangles differ')
    delta=z['power_W']-a['power_W'][ix];fig,ax=plt.subplots(figsize=(7,3.2),layout='constrained');coll=PolyCollection(z['xyz_m'][:,:,:2]*1e3,array=delta/z['areas_m2'],cmap='coolwarm',norm=SymLogNorm(linthresh=.1,vmin=-300,vmax=300),rasterized=True);ax.add_collection(coll);ax.set(xlim=(-16,16),ylim=(-9,9),xlabel='$x$ (mm)',ylabel='$y$ (mm)',title='Last normal halving: matched actual-face raw-flux change');ax.set_aspect('equal');fig.colorbar(coll,ax=ax,label='$\\Delta q_{raw}$ (W m$^{-2}$)',ticks=[-100,-1,0,1,100]);generated.append(('matched_face_change',fig))
    for name,fig in generated:
        for ext in ('png','pdf'):fig.savefig(out/(name+'.'+ext),dpi=600,bbox_inches='tight',**({'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}))
        plt.close(fig)
    positive_change=float(z['power_W'][z['power_W']>=0].sum()-a['power_W'][a['power_W']>=0].sum());negative_change=float(z['power_W'][z['power_W']<0].sum()-a['power_W'][a['power_W']<0].sum())
    concentration=[]
    for case in study['cases']:
        d=np.load(audit/case['case']/'support_faces.npz');q=abs(d['weighted_power_W'][d['kind']=='internal']);q=np.sort(q)[::-1]
        concentration.append({'case':case['case'],'internal_abs_W':float(q.sum()),'top1percent_abs_fraction':float(q[:max(1,int(np.ceil(len(q)*.01)))].sum()/q.sum()),'largest_face_abs_fraction':float(q[0]/q.sum())})
    write(out/'comparison.json',{'last_normal_signed_change_W':float(delta.sum()),'positive_contribution_change_W':positive_change,'negative_contribution_change_W':negative_change,
        'same_triangles_verified':True,'continuum_local_error_known':False,'weighted_jump_concentration':concentration,'scope':'matched solved-field change and exact discrete defect distribution; no local continuum reference, reaction substitution or recovered-flux qualification'})
    write(out/'provenance.json',{'source_sha256':sha(Path(__file__)),'audit_summary_sha256':sha(audit/'summary.json'),'figures':{p.name:sha(p) for p in out.iterdir() if p.suffix in ['.png','.pdf']}})
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();render(a.audit.resolve(),a.out.resolve())
