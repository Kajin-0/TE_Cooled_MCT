"""Build a new review edition from actual immutable corrected FEM archives."""
import argparse, gzip, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
BASE=ROOT/'fem/results/cold20_completion_20261030'
MESH=ROOT/'fem/results/cold_interface_convergence_20261030/device/cold20um_FAILED/mesh'
CASE=BASE/'cases/loaded20_refined_replay'
PUBLIC=ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

def figures(out):
    if (out/'edition_checksums.json').exists():raise ValueError('Published edition is immutable; use a new output directory')
    import numpy as np,meshio,matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib import colors
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from reports.field_geometry import plane_section,section_values,node_map,cell_map
    out.mkdir(parents=True,exist_ok=True);fd=out/'figures';fd.mkdir(exist_ok=True)
    cache=ROOT/'outputs/rev3_cache';cache.mkdir(exist_ok=True)
    source_files=[MESH/'mesh.npz',MESH/'manifest.json',CASE/'metrics.json',CASE/'execution.json',CASE/'uncompressed_sha256.json',BASE/'study.json',BASE/'bath_comparison.json',BASE/'bath_parent/audit.json',BASE/'bath_refined/audit.json',BASE/'diagnosis20_refined/diagnosis.json',ROOT/'data/geometry_complete/reference_v2.json']
    d=np.load(MESH/'mesh.npz');p,c,b,f,tags=[d[k] for k in ('points','cells','bodies','faces','boundaries')]
    e=read(CASE/'execution.json');m=read(CASE/'metrics.json');manifest=read(MESH/'manifest.json');by={x['id']:x for x in manifest['bodies']}
    if sha(MESH/'mesh.npz')!=e['mesh_sha256']:raise ValueError('Mesh does not match archived execution')
    for n in ['fields_t0001.vtu','derived.vtu']:
        z=CASE/(n+'.gz');source_files.append(z);q=cache/n
        expected=read(CASE/'uncompressed_sha256.json')[n]
        if not q.exists() or sha(q)!=expected:q.write_bytes(gzip.decompress(z.read_bytes()))
        if sha(q)!=expected:raise ValueError('Actual archived field checksum differs')
    raw=meshio.read(cache/'fields_t0001.vtu');ix,dist=node_map(p,raw.points);T=raw.point_data['temperature'].ravel()[ix];V=raw.point_data['potential'].ravel()[ix]
    # Audit tetrahedra, not just node positions, including the original Elmer ordering.
    rcell=raw.cells_dict['tetra'];inverse=np.argsort(ix);cell_map(c,inverse[rcell])
    dv=meshio.read(cache/'derived.vtu');di,_=node_map(p,dv.points);dc=cell_map(c,np.argsort(di)[dv.cells_dict['tetra']]);J=dv.cell_data_dict['J_A_m2']['tetra'][dc];Q=dv.cell_data_dict['q_W_m2']['tetra'][dc]
    if len(by)!=216 or sum(x['kind']=='leg' for x in by.values())!=88:raise ValueError('Wrong geometry family')
    plt.rcParams.update({'font.family':'serif','font.size':10,'axes.titlesize':10,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,'pdf.fonttype':42,'savefig.dpi':600,'mathtext.fontset':'dejavuserif'})
    palette={'P':'#ad5551','N':'#3974a2','Cu':'#b88139','Alumina':'#dfded4','Kovar':'#8d969e','Pin':'#a88758','Glass':'#91bec1','Presolder':'#858780','Attach':'#717085','MCT':'#694c83','Au':'#c8a540'}
    generated=[]
    def save(fig,name):
        for ext in ['png','pdf']:
            q=fd/(name+'.'+ext);fig.savefig(q,dpi=600,bbox_inches='tight',pad_inches=.05,**({'metadata':{'CreationDate':None,'ModDate':None,'Author':'','Creator':'Scientific review assessment'}} if ext=='pdf' else {}));generated.append(q)
        plt.close(fig)
    def section(axis,coord):
        s=plane_section(p,c,axis=axis,coordinate=coord);return s,section_values(s,c,T),section_values(s,c,V)
    # An exact horizontal cut reveals the actual two-ear contour and nine holes.
    s,st,sv=section(2,.00075);xy=s['xyz'][:,:,:2]*1e3
    fig,ax=plt.subplots(figsize=(6.35,3.8));ax.add_collection(PolyCollection(xy,facecolors=[palette[by[int(x)]['material']] for x in b[s['cells']]],edgecolors='none'))
    for bid in range(501,510):
        x,y=np.array(by[bid]['center_xy_m'])*1e3;ax.text(x,y,str(bid-500),ha='center',va='center',fontsize=9,bbox={'facecolor':'white','edgecolor':'none','alpha':.8,'pad':.4})
    ax.set(xlim=(-16.4,16.4),ylim=(-9.3,9.3),xlabel='$x$ (mm)',ylabel='$y$ (mm)',title='Actual mesh section through the two-ear header');ax.set_aspect('equal');fig.tight_layout();save(fig,'header_geometry')
    # Full union exterior, as stored by the geometry audit. No invented enclosure.
    ext=f[tags<1000];cent=p[c].mean(1)
    from tecooledmct.fem_g2a import mesh_adjacency
    adj=mesh_adjacency(c);owners=np.array([b[adj[tuple(sorted(x))][0]] for x in ext])
    fig=plt.figure(figsize=(6.35,4.1));ax=fig.add_subplot(111,projection='3d');ax.add_collection3d(Poly3DCollection(p[ext]*1e3,facecolors=[palette[by[int(x)]['material']] for x in owners],edgecolors='none',rasterized=True));ax.view_init(23,-64);ax.set_proj_type('ortho');ax.set(xlim=(-16,16),ylim=(-9,9),zlim=(-13,6),xlabel='$x$ (mm)',ylabel='$y$ (mm)',zlabel='$z$ (mm)');ax.set_box_aspect((32,18,19));ax.set_xticks([-15,0,15]);ax.set_yticks([-8,0,8]);ax.set_zticks([-12,-6,0,6]);ax.zaxis.set_rotate_label(False);ax.set_zlabel('');fig.text(.965,.55,'$z$ (mm)',rotation=90);fig.tight_layout();save(fig,'package_geometry')
    s,st,sv=section(1,.00015);tri=s['xyz'][:,:,[0,2]]*1e3;ci=s['cells'];roi=(tri[:,:,1].min(1)>1.49)&(abs(tri[:,:,0]).max(1)<3.3)
    np.savez_compressed(out/'section.npz',xyz_m=s['xyz'],source_cells=ci,barycentric=s['barycentric'],temperature_K=st,potential_V=sv)
    def axes(ax,zoom=False):
        ax.set(xlim=(-.65,.65) if zoom else (-3.3,3.3),ylim=(5.12,5.60) if zoom else (1.48,5.65),xlabel='$x$ (mm)',ylabel='$z$ (mm)');ax.set_aspect('equal');ax.spines[['top','right']].set_visible(False)
    fig,ax=plt.subplots(figsize=(6.35,4.15));ax.add_collection(PolyCollection(tri[roi],facecolors=[palette[by[int(x)]['material']] for x in b[ci[roi]]],edgecolors=(0,0,0,.22),linewidths=.12));axes(ax);fig.tight_layout();save(fig,'stack_mesh')
    for name,arr,label,cmap,norm,mask in [('temperature',st.mean(1),'$T$ (K)','plasma',colors.Normalize(265.4,300.4),roi),('potential',sv.mean(1)*1e3,'$\\phi$ (mV)','cividis',colors.Normalize(0,552),roi&np.isin(b[ci],[x['id'] for x in by.values() if x['material'] in ['P','N','Cu']])),('current',np.linalg.norm(J[ci],axis=1),'$|\\mathbf{J}|$ (A m$^{-2}$)','viridis',colors.LogNorm(1e4,2e6),roi&np.isin(b[ci],[x['id'] for x in by.values() if x['material'] in ['P','N','Cu']])),('heat',np.linalg.norm(Q[ci],axis=1),'$|\\mathbf{q}|$ (W m$^{-2}$)','viridis',colors.LogNorm(1,2e5),roi)]:
        fig,ax=plt.subplots(figsize=(6.35,4.1));ax.add_collection(PolyCollection(tri[roi],facecolors='#eeeeea',edgecolors='none'));coll=PolyCollection(tri[mask],array=arr[mask],cmap=cmap,norm=norm,edgecolors='none',rasterized=True);ax.add_collection(coll);axes(ax);fig.colorbar(coll,ax=ax,pad=.025,label=label,shrink=.9);fig.tight_layout();save(fig,name)
    fig,ax=plt.subplots(figsize=(6.35,3));coll=PolyCollection(tri[roi],array=st.mean(1)[roi],cmap='plasma',norm=colors.Normalize(265.40,265.80),edgecolors=(0,0,0,.17),linewidths=.15,rasterized=True);ax.add_collection(coll);axes(ax,True);fig.colorbar(coll,ax=ax,label='$T$ (K)',pad=.02,shrink=.85);fig.tight_layout();save(fig,'cold_detail')
    # Separate true one-sided raw face powers. Both fields are independently computed.
    fig,axs=plt.subplots(2,2,figsize=(6.35,5.7),layout='constrained')
    for row,(name,title) in enumerate([('face_4_302.npz','Ceramic / attach'),('face_302_303.npz','Attach / MCT')]):
        path=BASE/'diagnosis20_refined'/name;source_files.append(path);q=np.load(path);xy=p[q['faces']][:,:,:2]*1e3
        for side in range(2):
            ax=axs[row,side];value=q['power_outward_w'][:,side]/q['areas_m2']*(-1 if side==0 else 1);coll=PolyCollection(xy,array=value,norm=colors.Normalize(1700,2200),cmap='viridis',edgecolors='none',rasterized=True);ax.add_collection(coll);ax.set(xlim=(-.5,.5),ylim=(-.5,.5),xlabel='$x$ (mm)',ylabel='$y$ (mm)',title=title+('\nLower-solid trace' if side==0 else '\nUpper-solid trace'));ax.set_aspect('equal')
    fig.colorbar(coll,ax=axs.ravel().tolist(),label='Downward raw Fourier flux (W m$^{-2}$)',shrink=.7);save(fig,'cold_flux')
    fig,axs=plt.subplots(1,2,figsize=(6.35,3.15),layout='constrained')
    for ax,folder,mp,title in zip(axs,['bath_parent','bath_refined'],[MESH,BASE/'bath_mesh'],['Initial bath volume','First bath volume refinement']):
        path=BASE/folder/'face_data.npz';source_files+=[path,mp/'mesh.npz'];q=np.load(path);points=np.load(mp/'mesh.npz')['points'];coll=PolyCollection(points[q['faces']][:,:,:2]*1e3,array=q['outward_density_W_m2'],cmap='coolwarm',norm=colors.SymLogNorm(linthresh=1,vmin=-2e4,vmax=2e4),rasterized=True);ax.add_collection(coll);ax.set(xlim=(-16,16),ylim=(-9,9),xlabel='$x$ (mm)',ylabel='$y$ (mm)',title=title);ax.set_aspect('equal')
    fig.colorbar(coll,ax=axs.tolist(),label='$q_{out}$ (W m$^{-2}$)',shrink=.65,ticks=[-1e4,-1e2,0,1e2,1e4]);save(fig,'bath_flux')
    study=read(BASE/'study.json');cases=study['cases'];fig,axs=plt.subplots(1,2,figsize=(6.35,3.0),layout='constrained');x=[a['tetrahedra']/1000 for a in cases]
    axs[0].plot(x,[(a['die_mean_k']-cases[-1]['die_mean_k'])*1000 for a in cases],'o-',color='#32677c');axs[0].set(xlabel='Tetrahedra ($10^3$)',ylabel='$T_{die}-T_{finest}$ (mK)')
    for j,label in enumerate(['Ceramic / attach','Attach / MCT']):axs[1].plot(x,[abs(a['interfaces'][j]['mismatch'])*100 for a in cases],'o-',label=label)
    axs[1].axhline(5,color='#9f3838',ls='--',label='5% gate');axs[1].set(xlabel='Tetrahedra ($10^3$)',ylabel='Absolute raw mismatch (%)');axs[1].legend(frameon=False,fontsize=8)
    for ax in axs:ax.grid(alpha=.2)
    save(fig,'convergence')
    bench=ROOT/'fem/results/cold_interface_convergence_20261030/benchmark/summary.json';source_files.append(bench);bc=[a for a in read(bench)['cases'] if a['kind']=='distributed_MCT_source'];fig,axs=plt.subplots(1,2,figsize=(6.35,2.8),layout='constrained')
    axs[0].loglog([a['h_m']*1e6 for a in bc],[abs(a['interface_relative_errors'][1])*100 for a in bc],'o-');axs[0].set(xlabel='Effective mesh size ($\\mu$m)',ylabel='Source-face flux error (%)')
    axs[1].loglog([a['h_m']*1e6 for a in bc],[abs(a['MCT_mean_error_k'])*1000 for a in bc],'s-');axs[1].set(xlabel='Effective mesh size ($\\mu$m)',ylabel='Die mean error (mK)')
    for ax in axs:ax.grid(alpha=.2)
    save(fig,'benchmark')
    tex=[]
    def macro(k,v):tex.append('\\newcommand{\\'+k+'}{'+str(v)+'}')
    for k,v in {'Die':f"{m['die_mean_k']:.6f}",'Cold':f"{m['cold_ceramic_k']:.6f}",'Voltage':f"{m['voltage_v']:.9f}",'GlobalResidual':f"{m['global_energy_error_w']*1e6:.6f}",'ThermalResidual':f"{m['free_thermal_residual_L1_w']*1e6:.6f}",'CurrentResidual':f"{m['free_current_residual_L1_a']*1e6:.6f}",'WorstCut':f"{m['worst_raw_cut_relative_error']*100:.6f}",'BathRaw':f"{m['hot_out_raw_gradient_w']*1000:.6f}",'BathWeak':f"{m['hot_out_reaction_w']*1000:.6f}"}.items():macro(k,v)
    rows=[]
    for label,a in zip(['A','B','C'],cases):rows.append(f"{label} & {a['tetrahedra']:,} & {a['die_mean_k']:.6f} & {a['voltage_v']:.9f} & {a['interfaces'][0]['mismatch']*100:+.3f} & {a['interfaces'][1]['mismatch']*100:+.3f}"+r' \\')
    macro('ConvergenceRows','\n'.join(rows));(out/'numerics.tex').write_text('\n'.join(tex)+'\n')
    write(out/'report_inputs.json',{'report_revision':3,'edition_kind':'REVIEW DRAFT','full_qualification':False,'OEM_validated':False,'old_report_unchanged':True,'mesh_nodes':len(p),'tetrahedra':len(c),'solid_domains':len(by),'thermoelectric_legs':88,'mesh_sha256':sha(MESH/'mesh.npz'),'field_sha256':e['vtu_sha256'],'node_bijection_max_distance_m':dist,'tetrahedra_bijection_verified':True,'figure_method':'actual archived corrected tetrahedra, exact plane intersections, P1 cell means; raw owner-side flux maps; no obsolete model images','inputs':{str(x.relative_to(ROOT)):sha(x) for x in set(source_files)},'figures':{x.name:sha(x) for x in generated},'generator':{str(x.relative_to(ROOT)):sha(x) for x in [Path(__file__),Path(__file__).with_name('report.tex'),Path(__file__).with_name('validate.py'),ROOT/'reports/field_geometry.py']}})
    print('Actual corrected-field figures verified',out,flush=True)

def build(out):
    if out.exists():raise ValueError('An edition is immutable: use a new edition directory')
    subprocess.run([str(ROOT/'fem/run.sh'),'python','reports/rev3_review/build.py','--figures-only','--out',str(out.relative_to(ROOT))],cwd=ROOT,check=True)
    subprocess.run([str(ROOT/'fem/run.sh'),'python','-c',"from pathlib import Path; from reports.rev3_review.latest_study import supplement; supplement(Path("+repr(str(out.relative_to(ROOT)))+"))"],cwd=ROOT,check=True)
    shutil.copy2(Path(__file__).with_name('report.tex'),out/'report.tex')
    env=os.environ.copy();env['SOURCE_DATE_EPOCH']='1793318400';env['TZ']='UTC'
    for i in range(3):
        with (out/f'build-{i+1}.log').open('w') as log:subprocess.run(['pdflatex','-halt-on-error','-interaction=nonstopmode','-file-line-error','report.tex'],cwd=out,stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
    from reports.rev3_review.validate import validate
    validate(out)
    print('Candidate built. Inspect rendered pages and record visual_review.json before --publish:',out)

def publish(out):
    from reports.rev3_review.validate import verify_edition
    if (out/'edition_checksums.json').exists():raise ValueError('Published edition is immutable')
    d=read(out/'report_inputs.json');v=read(out/'validation.json');visual=read(out/'visual_review.json')
    if not v['passed'] or visual['pdf_sha256']!=sha(out/'report.pdf') or not visual['all_pages_inspected']:raise ValueError('Missing actual visual review')
    for n,h in d['generator'].items():
        if sha(ROOT/n)!=h:raise ValueError('Changed report generator after build')
        dest=out/'source_snapshot'/(n+'.source');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,dest)
    d['derived']={n:sha(out/n) for n in ['report.tex','numerics.tex','section.npz','latest_cover.tex','latest_study.tex'] if (out/n).exists()};write(out/'report_inputs.json',d)
    write(out/'edition_checksums.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
    verify_edition(out)
    shutil.copy2(out/'report.pdf',PUBLIC)
    write(ROOT/'reports/rev3_review/current.json',{'edition':str(out.relative_to(ROOT)),'pdf_sha256':sha(PUBLIC),'review_draft':True,'full_qualification':False})
    print('Visually inspected REVIEW DRAFT published:',PUBLIC)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--figures-only',action='store_true');a.add_argument('--publish',action='store_true');n=a.parse_args();out=n.out.resolve();publish(out) if n.publish else figures(out) if n.figures_only else build(out)
