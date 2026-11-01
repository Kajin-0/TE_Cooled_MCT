"""Actual frozen-surface diagnostic; no interpolated field across solid holes."""
import argparse
from pathlib import Path

import numpy as np

from .native_gas_flux_forensics import ROOT,FROZEN,read,write,sha


def run(folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder=Path(folder).resolve();output=folder/'flux_jump_decomposition.png'
    if output.exists():raise ValueError('Do not overwrite forensic figure evidence')
    r=read(folder/'audit.json');d=np.load(folder/'diagnostic_arrays.npz');m=np.load(FROZEN/'phase_C/mesh.npz')
    groups={g['body']:g for g in r['groups']};ids=[1,2,3,4,303,300,7301,7302,7303]
    fields=['jump_contribution_W','shared_node_redistribution_W','difference_W']
    data=np.array([[groups[i][key] for key in fields] for i in ids]+[[sum(g[key] for g in r['groups'] if g['body'] not in ids) for key in fields]])*1e3
    labels=['Hot ceramic','Stage 1 ceramic','Stage 2 ceramic','Cold ceramic','MCT die','Header','Cap shell','Cap roof','Window','All other surfaces']
    fig,axes=plt.subplots(1,2,figsize=(12.8,6.0),gridspec_kw={'width_ratios':[1.3,1.]})
    y=np.arange(len(labels));ax=axes[0]
    ax.barh(y,data[:,0],height=.64,color='#3e7f8e',label='Area-weighted interior-jump term')
    ax.barh(y,data[:,1],left=data[:,0],height=.64,color='#d3994d',label='Shared-node redistribution')
    ax.plot(data[:,2],y,'k.',ms=6,label='Allocated reaction minus raw')
    ax.set(yticks=y,yticklabels=labels,xlabel='Algebraic difference (mW); positive into solid',
           xlim=(min(0.,data.min())-.35,max(0.,data.max())+.35))
    ax.invert_yaxis();ax.axvline(0,lw=.7,color='.3');ax.grid(axis='x',alpha=.2)
    ax.set_title('Identical disjoint native physical groups',fontsize=10)
    ax.legend(loc='upper left',bbox_to_anchor=(0.,-.14),fontsize=8,frameon=False)
    p,f=m['points'],m['faces'];cold=m['solid_bodies']==4;z=p[f[cold],2].max()
    selected=cold&np.all(abs(p[f,2]-z)<1e-12,axis=1);tri=f[selected]
    diagnostic=(d['allocated_boundary_W']-d['raw_boundary_W'])[selected]/d['boundary_area_m2'][selected]
    limit=float(max(abs(diagnostic).max(),1e-12));ax=axes[1]
    artist=ax.tripcolor(p[:,0]*1e3,p[:,1]*1e3,tri,facecolors=diagnostic,shading='flat',cmap='coolwarm',vmin=-limit,vmax=limit,edgecolors='.45',linewidth=.12)
    bounds=p[np.unique(tri),:2]*1e3
    ax.set(xlim=(bounds[:,0].min()-.1,bounds[:,0].max()+.1),ylim=(bounds[:,1].min()-.1,bounds[:,1].max()+.1),xlabel='x (mm)',ylabel='y (mm)')
    ax.set_aspect('equal');ax.set_title('Actual cold-ceramic top triangles; attach footprint blank',fontsize=10)
    cb=fig.colorbar(artist,cax=fig.add_axes([.67,.165,.27,.025]),orientation='horizontal')
    cb.set_label('(Allocated reaction − raw) / area (W/m²)',fontsize=9)
    fig.suptitle('Frozen gas-field forensics — original 32.6274% raw-flux FAIL remains',fontsize=12)
    fig.text(.035,.025,'Boundary −11.347300 mW + interior jumps +11.347300 mW = roundoff. Allocation is diagnostic, not physical pointwise heat flux. No new solve.',fontsize=8.5)
    fig.subplots_adjust(left=.125,right=.98,bottom=.29,top=.86,wspace=.4)
    fig.savefig(output,dpi=220);plt.close(fig)
    # Localization uses the same independently reconstructed triangle powers.
    # It is accounting on this frozen field, never a local flux correction.
    delta=d['allocated_boundary_W']-d['raw_boundary_W'];area=d['boundary_area_m2']
    xyz=p[f];vectors=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2
    parent_centers=p[m['cells'][d['boundary_parent']]].mean(1)
    vectors[np.einsum('ij,ij->i',vectors,xyz.mean(1)-parent_centers)<0]*=-1
    plane=np.argmax(abs(vectors),axis=1)
    patches=[]
    for body in (2,3,4):
        # Normals point OUT OF GAS INTO SOLID: a solid's top points down.
        for label,mask in [('top',vectors[:,2]<0),('bottom',vectors[:,2]>0),('sides',plane!=2)]:
            sel=(m['solid_bodies']==body)&mask
            if label!='sides':sel&=plane==2
            patches.append({'body':body,'patch':label,'triangles':int(sel.sum()),
                            'raw_W':float(d['raw_boundary_W'][sel].sum()),'allocated_minus_raw_W':float(delta[sel].sum())})
    centers=xyz.mean(1);halfside=max(abs(bounds).ravel())*.001
    strip=selected&(np.max(abs(centers[:,:2]),axis=1)>=halfside-.00015)
    write(folder/'localization.json',{'source':'Independently reconstructed frozen boundary powers; no solve or flux recovery',
        'normal_gradient_abs_quantiles_K_m':np.quantile(abs(d['raw_boundary_W']/area/.0259),[.5,.9,.99,1.]),
        'ceramic_patches':patches,'cold_top_triangles':int(selected.sum()),
        'cold_top_allocated_minus_raw_W':float(delta[selected].sum()),
        'cold_top_outer_150um_strip':{'triangles':int(strip.sum()),'area_fraction':float(area[strip].sum()/area[selected].sum()),
           'allocated_minus_raw_W':float(delta[strip].sum()),'fraction_of_cold_top_difference':float(delta[strip].sum()/delta[selected].sum())},
        'caution':'Patch differences include nodal allocation; they are not pointwise physical heat flux or an error estimator'})
    write(folder/'figure_provenance.json',{'source_sha256':sha(__file__),'figure_sha256':sha(output),
         'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (folder/'audit.json',folder/'diagnostic_arrays.npz',FROZEN/'phase_C/mesh.npz')},
         'actual_surface_body':4,'surface_z_m':float(z),'triangles':len(tri),
         'plotted_diagnostic_min_max_W_m2':[float(diagnostic.min()),float(diagnostic.max())],
         'kind':'Exact frozen boundary triangles and algebraic group decomposition; not a recovered or qualified heat field'})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);args=p.parse_args();run(args.data)
