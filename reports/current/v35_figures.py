"""V3.5 source-resolved, conditionally accepted TEC power-lead/contact figures.

All plotted operating temperatures originate in archived full-system results.
The separate contact curve is explicitly fixed-field only, NOT another PDE run.
"""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'data/v3_5_power_lead_and_copper_sensitivity_20261108'
V34=ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json'
FIG=HERE/'figures'
def read(p):return json.loads(p.read_text())
def save(fig,name):
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',
        metadata={'Creator':'Source-based HgCdTe engineering report','CreationDate':None,'ModDate':None})
    fig.savefig(FIG/(name+'.png'),dpi=220,bbox_inches='tight')
    plt.close(fig)
def make():
    old=read(V34)
    names=('copper_native_pad','nickel_native_pad','high_interstage_contact_R')
    r={name:read(BASE/name/'result.json') for name in names}
    for name in names:
        independent=read(BASE/name/'independent_energy_audit.json')
        assert independent['verdict'].startswith('PASS')
        assert independent['result_sha256']==hashlib.sha256((BASE/name/'result.json').read_bytes()).hexdigest()
        assert r[name]['max_last_spatial_temperature_update_K']<3e-7
    screen=read(BASE/'fixed_source_field_screen.json')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
       'axes.spines.top':False,'axes.spines.right':False,
       'pdf.fonttype':42,'savefig.facecolor':'white'})
    titles=['V3.4: combined lead approximation','V3.5: separate copper leads',
       'V3.5: separate nickel-like leads','V3.5: high interstage contact R']
    values=[old['calculated_detector_temperature_K']]+[r[x]['calculated_detector_temperature_K'] for x in names]
    fig,ax=plt.subplots(figsize=(9.5,4.4),layout='constrained')
    yy=np.arange(4)
    colors=['#8894a2','#406e8e','#63928d','#b27347']
    ax.scatter(values,yy,s=110,c=colors,zorder=4)
    for j,v in enumerate(values):
        ax.plot([values[1],v],[j,j],linewidth=2,color=colors[j],alpha=.65,zorder=3)
    ax.axvline(values[1],linestyle='--',linewidth=1.0,color='#7690a0',alpha=.8)
    ax.set_yticks(yy,titles);ax.invert_yaxis()
    ax.set_xlim(210.7,221)
    ax.set_xlabel('Calculated HgCdTe temperature at 0.4 A (K)')
    ax.set_title('Whole-device response to terminal leads and copper joints',
                 fontsize=13,fontweight='bold')
    ax.grid(axis='x',alpha=.2)
    ax.set_axisbelow(True)
    for i,v in enumerate(values):
        ax.text(v+.17,i,f'{v:.3f} K',va='center',fontsize=10,weight='bold')
    ax.text(.01,.02,'Synthetic selected material/contact laws; not a measured prediction',
            transform=ax.transAxes,fontsize=8,color='#545b65')
    save(fig,'v35_full_system_scenario_temperature')
    # Plot lead heat at original separate pads, using ONLY the saved source-field screen.
    labels=['Copper','Nickel proxy','FeCrAl screen']
    rows=[next(x for x in screen['lead_screen'] if x['alloy']==mode and
               x['internal_wire_routing_length_factor']==1.)
          for mode in ('copper','nickel_proxy','fecral_screen')]
    x=np.arange(3);w=.3
    heat1=np.array([v['separate_native_pad_heat_W']['8']*1e3 for v in rows])
    heat9=np.array([v['separate_native_pad_heat_W']['36']*1e3 for v in rows])
    fig,ax=plt.subplots(figsize=(8.8,4.5),layout='constrained')
    ax.bar(x-w/2,heat1,width=w,label='Pin 1 / original face 8',color='#527c99')
    ax.bar(x+w/2,heat9,width=w,label='Pin 9 / original face 36',color='#b16d44')
    ax.axhline(0,color='#4a5055',lw=1)
    ax.set_xticks(x,labels)
    ax.set_ylabel('Heat into original ceramic pad (mW)')
    ax.set_title('Separate lead terminals: heat can flow in opposite directions',fontsize=12,weight='bold')
    ax.legend(frameon=False)
    ax.grid(axis='y',alpha=.2)
    ax.set_axisbelow(True)
    ax.text(.02,.03,'V3.4 fixed source pad temperatures, not re-solved detector temperatures',
            transform=ax.transAxes,color='#545b65',fontsize=8)
    save(fig,'v35_fixed_field_lead_heat_screen')
    # Interstage contact resistance sweep is also fixed-field and is not
    # a nonlinear case series. The severe high-R scenario separately gets a
    # full nonlinear solve in the first figure.
    sweep=[d for d in screen['interstage_Cu_contact_screen'] if d['r_thermal_contact_area_m2K_W']>0]
    a=np.array([d['r_thermal_contact_area_m2K_W'] for d in sweep])
    b=np.array([d['original_source_Cu_heat_into_stage_mW'][2] for d in sweep])
    fig,ax=plt.subplots(figsize=(7.7,4.1),layout='constrained')
    ax.semilogx(a,b,'o-',color='#496e8b',linewidth=2.2,markersize=8)
    ax.axvline(1e-6,color='#b27347',ls='--',lw=1.2,label='V3.5 nominal contact hypothesis')
    ax.set_xlabel('Assumed effective Cu-foil contact areal thermal resistance (m² K/W)')
    ax.set_ylabel('Cu heat entering upper ceramic (mW)')
    ax.set_title('Copper interface impedance dominates the heat-bypass screen',
                 fontsize=12,fontweight='bold')
    ax.grid(alpha=.25,which='both')
    ax.legend(frameon=False,fontsize=9)
    ax.text(.03,.03,'Fixed V3.4 pad temperature field; not a self-consistent Tdetector sweep',
            transform=ax.transAxes,color='#545b65',fontsize=8)
    save(fig,'v35_fixed_field_interstage_contact_screen')
    # Genuine accepted V3.5 spatial FEM on the SAME frozen tetrahedral meshes,
    # not an invented interpolated temperature gradient or V3.3 surrogate.
    import matplotlib.tri as mtri
    from matplotlib.ticker import FormatStrFormatter
    conn=np.load(ROOT/'reports/current/inputs/v33_ceramic_connectivity.npz',allow_pickle=False)
    with np.load(BASE/'copper_native_pad/source_native_ceramics_V3_5.npz',allow_pickle=False) as v35field:
        fig,axs=plt.subplots(2,2,figsize=(8.4,6.5),layout='constrained')
        expected=[4936,4085,1986,784]
        for i,ax in enumerate(axs.flat):
            xyz=v35field[f'ceramic{i}_xyz_mm']
            temp=v35field[f'ceramic{i}_temperature_K']
            tet=conn[f'ceramic{i}_tetrahedra_local']
            assert len(tet)==expected[i]
            faces=np.concatenate([tet[:,[0,1,2]],tet[:,[0,1,3]],tet[:,[0,2,3]],tet[:,[1,2,3]]])
            top=faces[np.all(np.isclose(xyz[faces,2],xyz[:,2].max(),atol=1e-9),axis=1)]
            assert len(top)>0 and top.max()<len(xyz)
            im=ax.tripcolor(mtri.Triangulation(xyz[:,0],xyz[:,1],top),temp,
                shading='gouraud',cmap='viridis')
            cb=fig.colorbar(im,ax=ax,shrink=.83,label='Temperature (K)',
                format=FormatStrFormatter('%.3f' if i==3 else '%.2f'))
            cb.ax.tick_params(labelsize=7)
            ax.set(title=f'Ceramic {i}: {expected[i]:,} TET4',xlabel='x (mm)',ylabel='y (mm)')
            ax.set_aspect('equal')
    save(fig,'v35_original_spatial_ceramic_fields')
    summary={'full_system':{n:{'Tdie_K':d['calculated_detector_temperature_K'],
         'Vterminal_V':d['terminal_voltage_V'],'Pel_W':d['electrical_power_W'],
         'bath_W':d['bath_heat_rejected_W'],'outer_iterations':d['outer_iterations']}
         for n,d in r.items()},
       'old_V3_4_Tdie_K':old['calculated_detector_temperature_K'],
       'baseline_delta_from_V3_4_K':values[1]-values[0],
       'nickel_delta_from_corrected_copper_K':values[2]-values[1],
       'high_contact_delta_from_corrected_copper_K':values[3]-values[1],
       'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in [V34,BASE/'fixed_source_field_screen.json']+
           [BASE/n/'result.json' for n in names]}}
    (HERE/'v35_figure_provenance.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('V3.5 figures built',json.dumps(summary['full_system'],indent=2))
if __name__=='__main__':make()
