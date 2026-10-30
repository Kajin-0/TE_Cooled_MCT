"""Scientific mesh, solved-temperature, one-sided-face-flux and convergence figures."""
import argparse,json
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .cold_convergence_summary import RAW,CONFIG,read


def render(out,study_path=None):
    import meshio,matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import Normalize
    from reports.field_geometry import plane_section,section_values,node_map
    out.mkdir(parents=True,exist_ok=False);provenance={}
    plt.rcParams.update({'font.size':10,'axes.labelsize':10,'axes.titlesize':11,'savefig.bbox':'tight'})
    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=350);fig.savefig(out/(name+'.pdf'));plt.close(fig)
    study_path=study_path or RAW/'study.json'
    study=read(study_path);completed=[r for r in CONFIG if r[0] in [v['level'] for v in study['cases']]]
    selected=(completed[0],completed[-1])
    fig,axs=plt.subplots(2,2,figsize=(11,7.2),layout='constrained');caseinfo=[]
    for label,mesh,case,diag,stat in selected:
        d=np.load(mesh/'mesh.npz');p,c,b=(d[k] for k in ('points','cells','bodies'))
        field=meshio.read(case/'derived.vtu');ix,_=node_map(p,field.points);t=field.point_data['Temperature_K'].ravel()[ix]
        section=plane_section(p,c,axis=1,coordinate=.00015);xyz=section['xyz'][:,:,[0,2]]*1e3;tv=section_values(section,c,t)
        select=(xyz[:,:,0].min(1)>-.8)&(xyz[:,:,0].max(1)<.8)&(xyz[:,:,1].min(1)>5.10)
        xyz=xyz[select];tv=tv[select];ids=section['cells'][select]
        np.savez_compressed(out/(label+'_section.npz'),xyz_mm=xyz,temperature_vertices_k=tv,source_tetra=ids,body_ids=b[ids])
        caseinfo.append((label,xyz,tv,b[ids]));provenance[label]={'mesh_sha256':sha(mesh/'mesh.npz'),'derived_sha256':sha(case/'derived.vtu'),
             'raw_field_sha256':read(case/'execution.json')['vtu_sha256'],'diagnosis_sha256':sha(diag/'diagnosis.json')}
    norm=Normalize(min(v[2].min() for v in caseinfo),max(v[2].max() for v in caseinfo))
    for col,(label,xyz,tv,body) in enumerate(caseinfo):
        coll=PolyCollection(xyz,array=body.astype(float),cmap='tab20',edgecolors='black',linewidths=.12,rasterized=True)
        axs[0,col].add_collection(coll);axs[0,col].set_title(label+' — actual tetrahedron section')
        thermal=PolyCollection(xyz,array=tv.mean(1),cmap='viridis',norm=norm,edgecolors='none',rasterized=True)
        axs[1,col].add_collection(thermal);axs[1,col].set_title(label+' — actual solved temperature')
        for ax in axs[:,col]:
            ax.set(xlim=(-.70,.70),ylim=(5.10,5.60),xlabel='x (mm)',ylabel='z (mm)');ax.set_aspect('equal')
            ax.plot([-.65,-.45],[5.12,5.12],color='black',lw=3);ax.text(-.55,5.135,'0.2 mm',ha='center',fontsize=8)
            for z,txt in [(5.35,'ceramic / attach'),(5.38,'attach / die')]:ax.axhline(z,color='white',lw=.5,alpha=.8)
        for z,txt in [(5.23,'alumina 220 µm'),(5.365,'attach 30 µm'),(5.49,'MCT 200 µm')]:axs[0,col].text(.68,z,txt,ha='right',fontsize=8,bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
    fig.colorbar(thermal,ax=axs[1,:],label='Temperature (K)',shrink=.8)
    fig.suptitle('Actual y = 0.15 mm cold-interface FEM sections; conformal contacts, voids unfilled')
    save(fig,'actual_mesh_temperature')
    # Four actual owner-side flux maps per mesh, with a common physical down-positive scale.
    maps=[];vmin=0.;vmax=0.
    for label,mesh,case,diag,stat in selected:
        p=np.load(mesh/'mesh.npz')['points'];values=[]
        for pair in ('4_302','302_303'):
            a=np.load(diag/('face_'+pair+'.npz'));power=a['power_outward_w'];density=power/a['areas_m2'][:,None]
            down=density*np.array([-1.,1.]);vmin=min(vmin,float(down.min()));vmax=max(vmax,float(down.max()))
            values.extend([(p[a['faces']][:,:,:2]*1e3,down[:,s]) for s in (0,1)])
        maps.append((label,values))
    fig,axs=plt.subplots(2,4,figsize=(13,6.6),layout='constrained');fnorm=Normalize(vmin,vmax)
    names=('ceramic side','attach bottom side','attach top side','MCT bottom side')
    for row,(label,values) in enumerate(maps):
        for col,(xyz,density) in enumerate(values):
            coll=PolyCollection(xyz,array=density,cmap='coolwarm',norm=fnorm,edgecolors='none',rasterized=True)
            axs[row,col].add_collection(coll);axs[row,col].set(xlim=(-.5,.5),ylim=(-.5,.5),xlabel='x (mm)',ylabel='y (mm)',title=label+'\n'+names[col]);axs[row,col].set_aspect('equal')
    fig.colorbar(coll,ax=axs,label='Raw one-sided downward Fourier flux (W/m²)',shrink=.8)
    fig.suptitle('True interface triangles and owner gradients; common scale; no reaction/recovered flux substitution')
    save(fig,'actual_one_sided_flux_maps')
    rows=study['cases'];h=np.array([r['regions']['fixed_cold_ROI']['h_eff_m'] for r in rows])*1e6
    fig,axs=plt.subplots(2,2,figsize=(11,7.5),layout='constrained')
    for i,name in enumerate(('ceramic / attach','attach / MCT')):
        axs[0,0].plot(h,[abs(r['interfaces'][i]['mismatch'])*100 for r in rows],'o-',label=name)
    axs[0,0].axhline(5,color='black',ls='--',label='unchanged 5% gate');axs[0,0].set(ylabel='Raw interface mismatch (%)');axs[0,0].legend(fontsize=8)
    axs[0,1].plot(h,[r['direct_bath_relative_error']*100 for r in rows],'o-',color='tab:red');axs[0,1].axhline(-1,color='black',ls='--');axs[0,1].axhline(1,color='black',ls='--');axs[0,1].set(ylabel='Signed raw bath error (%)',title='Bath sizing held fixed; bath convergence untested')
    axs[1,0].plot(h,[(r['die_mean_k']-rows[0]['die_mean_k'])*1e3 for r in rows],'o-');axs[1,0].set(ylabel='Die mean change from original (mK)',title=f'{len(rows)} actual solved meshes; no full-device GCI')
    for ax in axs.flat[:3]:ax.set(xlabel='Actual fixed cold-ROI h_eff (µm)');ax.invert_xaxis();ax.grid(alpha=.25)
    b=read(RAW/'benchmark/summary.json')['cases'];source=[r for r in b if r['kind']=='distributed_MCT_source'];hb=np.array([r['h_m'] for r in source])*1e6
    axs[1,1].loglog(hb,[r['interface_relative_errors'][1]*100 for r in source],'o-',label='source-layer face error (%)')
    axs[1,1].loglog(hb,[abs(r['MCT_mean_error_k'])*1e3 for r in source],'s-',label='die mean error (mK)')
    axs[1,1].set(xlabel='Manufactured benchmark h_eff (µm)',ylabel='Analytic-reference error',title='Independent 3D HeatSolver: flux p≈1, mean T p≈2');axs[1,1].invert_xaxis();axs[1,1].grid(alpha=.25);axs[1,1].legend(fontsize=8)
    save(fig,'actual_convergence')
    write(out/'provenance.json',{'source_sha256':sha(Path(__file__)),'study_sha256':sha(study_path),'cases':provenance,
          'scope':'actual3D meshes and actual solved fields only; all failures plotted without gate changes'})
    print('Actual mesh/temperature/face-flux/convergence figures generated',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--study',type=Path);a=p.parse_args();render(a.out.resolve(),a.study.resolve() if a.study else None)
