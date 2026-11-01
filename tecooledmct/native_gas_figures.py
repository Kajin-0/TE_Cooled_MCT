"""Actual mesh-section field and failed raw/reaction budget comparison."""
import argparse
from pathlib import Path

import numpy as np

from .native_gas_audit import ROOT, read, write, sha


def run(folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from reports.field_geometry import plane_section, section_values, triangle_grid
    folder=Path(folder).resolve();c=folder/'phase_C';m=np.load(c/'mesh.npz');f=np.load(c/'audited_field.npz');r=read(c/'result.json')
    output=folder/'native_gas_control.png'
    if output.exists():raise ValueError('Never overwrite figure evidence')
    sec=plane_section(m['points'],m['cells'],axis=1,coordinate=-.000825)
    values=section_values(sec,m['cells'],f['temperature_K']);p,t,v=triangle_grid(sec['xyz'],values)
    fig,axes=plt.subplots(1,3,figsize=(15.5,6.2),gridspec_kw={'width_ratios':[1.15,1.1,1.25]})
    for i,ax in enumerate(axes[:2]):
        artist=ax.tripcolor(p[:,0]*1e3,p[:,2]*1e3,t,v,shading='gouraud',cmap='viridis',vmin=250,vmax=300)
        ax.set_aspect('equal');ax.set_xlabel('x (mm)');ax.set_ylabel('z (mm)')
        if i==0:
            ax.set_title('Actual gas mesh section, y = −0.825 mm',fontsize=10)
            ax.set(xlim=(-7.3,7.3),ylim=(1.35,9.8))
        else:
            ax.set_title('Interleg voids: white regions are solids',fontsize=10)
            ax.set(xlim=(-2.45,2.45),ylim=(1.45,4.5))
            collection=PolyCollection(sec['xyz'][:,:,[0,2]]*1e3,facecolors='none',edgecolors='k',linewidths=.12,alpha=.3)
            ax.add_collection(collection)
    colorbar=fig.colorbar(artist,cax=fig.add_axes([.20,.14,.30,.025]),orientation='horizontal')
    colorbar.set_label('Solved gas-control temperature (K)',fontsize=9)
    ids=[1,2,3,4,303,300,7301,7302,7303]
    budget={b['body']:b for b in r['bodies']};labels=['Hot ceramic','Stage 1 ceramic','Stage 2 ceramic','Cold ceramic','Die','Header','Cap shell','Cap roof','Window']
    raw=[1e3*budget[b]['raw_out_of_gas_W'] for b in ids];react=[1e3*budget[b]['allocated_reaction_into_solid_W'] for b in ids]
    y=np.arange(len(ids));ax=axes[2];ax.barh(y-.17,raw,.32,label='Raw one-sided gradient',color='#b55d44')
    ax.barh(y+.17,react,.32,label='Area-allocated nodal reaction',color='#3a7d88')
    ax.set(yticks=y,yticklabels=labels,xlabel='Heat into solid (mW; negative = supplies gas)')
    ax.invert_yaxis();ax.axvline(0,color='.3',lw=.7);ax.grid(axis='x',alpha=.2)
    ax.set_title('Unqualified surface powers: raw balance FAIL',fontsize=10)
    ax.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.20))
    fig.suptitle('Native gas-only Laplace control — 228,710 tets; raw global mismatch 32.63% > 1%',fontsize=12)
    fig.text(.04,.025,'Analytic walls 250–300 K; N₂, constant k=0.0259 W/(m K), 101325 Pa; buoyancy suppressed. No device-temperature prediction.',fontsize=9)
    fig.subplots_adjust(left=.045,right=.985,bottom=.30,top=.86,wspace=.65)
    fig.savefig(output,dpi=220);plt.close(fig)
    write(folder/'figure_provenance.json',{'source_sha256':sha(__file__),'figure_sha256':sha(output),
        'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (c/'mesh.npz',c/'audited_field.npz',c/'result.json')},
        'section_y_m':-.000825,'kind':'Actual tetrahedral P1 gas field, exact plane intersections; failed raw numerical gate explicitly shown',
        'registered_raw_gate_passed':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);args=p.parse_args();run(args.data)
