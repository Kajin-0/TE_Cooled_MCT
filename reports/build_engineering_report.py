#!/usr/bin/env python3
"""Rebuild a scientific PDF exclusively from immutable archived FEM evidence.

Host entry point uses only stdlib, the existing FEM image, pdflatex and MuPDF.
--figures-only runs inside the pinned image. No mesh generator or solver is run.
"""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def dump(path,data):path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def scientific_build(out):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    from matplotlib import colors,cm
    from matplotlib.collections import PolyCollection,LineCollection
    from matplotlib.patches import Patch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from mpl_toolkits.mplot3d import proj3d
    from reports.fem_report_data import ROOT,ARCHIVE,BASELINE,CASE,read,sha,load_fields
    from reports.field_geometry import plane_section,section_values,triangle_grid,clip_triangles
    from tecooledmct.fem_g2a import mesh_adjacency
    from tecooledmct.fem_g1 import tetra_geometry
    out.mkdir(parents=True,exist_ok=True);figdir=out/'figures';figdir.mkdir(exist_ok=True);cache=ROOT/'outputs/report_build_cache';d=load_fields(cache)
    p,c,b,f,tags=[d[k] for k in ('points','cells','bodies','faces','tags')];T,V,J,q=[d[k] for k in ('temperature','potential','J','q')];m=d['manifest'];by={x['id']:x for x in m['bodies']};summary=read(ARCHIVE/'charts/summary.json');cases=summary['cases'];reg=read(ROOT/'data/g3b/enclosure_registry.json');rev6=read(ROOT/'geometry/revision6/engineering_assumptions.json')
    plt.rcParams.update({'font.family':'serif','font.serif':['DejaVu Serif'],'font.size':12,'axes.labelsize':12,'axes.titlesize':12,'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':10,'axes.linewidth':.65,'savefig.dpi':600,'figure.dpi':120,'mathtext.fontset':'dejavuserif','pdf.fonttype':42,'ps.fonttype':42})
    generated=[];audit=d['audit'];audit['archive_inputs_only']=True;audit['revision6_reference']='geometry/revision6/engineering_assumptions.json; docs/rev6_cad_audit.md; no CAD images imported'
    def save(fig,name,raster=False):
        path=figdir/(name+('.png' if raster else '.pdf'));fig.savefig(path,dpi=600,bbox_inches='tight',pad_inches=.07,**({} if raster else {'metadata':{'CreationDate':None,'ModDate':None,'Creator':'Engineering Simulation Assessment'}}));plt.close(fig);generated.append(path)
    palette={'P':'#9b4547','N':'#34658b','Cu':'#b98b43','Alumina':'#d8d7cb','Kovar':'#8d969e','Pin':'#ad8552','Glass':'#90b9c7','Steel':'#a5afb4','ZnSe':'#a2cbd0','Mount':'#646f77','Attach':'#747583','MCT':'#543969','Au':'#d1ac43'}
    adj=mesh_adjacency(c);ext=np.flatnonzero(tags<1000);owners=np.array([b[adj[tuple(sorted(row))][0]] for row in f[ext]])
    section=plane_section(p,c,axis=1,coordinate=0);tri=section['xyz'];sc=section['cells'];st=section_values(section,c,T);sv=section_values(section,c,V)
    legs={x['id'] for x in m['bodies'] if x['kind']=='leg'};audit['section']={'axis':'y','coordinate_m':0.,'triangles':len(tri),'intersected_tetrahedra':len(np.unique(sc)),'intersected_leg_domains':len(set(b[sc])&legs),'method':'exact tetrahedron-edge intersections, source-cell P1 weights; positive-side preference at coincident faces; no Delaunay fill'}
    np.savez_compressed(out/'section_data.npz',xyz_m=tri,source_cells=sc,barycentric=section['barycentric'],temperature_k=st,potential_v=sv,body_ids=b[sc],J_cell_mean_a_m2=J[sc],q_cell_mean_w_m2=q[sc])
    def decorate3d(ax,limits):
        for axis in (ax.xaxis,ax.yaxis,ax.zaxis):axis.pane.fill=False;axis._axinfo['grid']['linewidth']=.35
        ax.set(xlabel='$x$ (mm)',ylabel='$y$ (mm)',zlabel='$z$ (mm)',xlim=limits[0],ylim=limits[1],zlim=limits[2]);ax.zaxis.set_rotate_label(False);ax.set_zlabel('$z$ (mm)',rotation=90,labelpad=9);ax.tick_params(labelsize=10,pad=1);ax.view_init(23,-64);ax.set_proj_type('ortho');ax.set_box_aspect([v[1]-v[0] for v in limits],zoom=1.12)
    def callout(ax,body,target,label,position):
        nodes=np.unique(c[b==body]);anchor=p[nodes[np.argmin(np.linalg.norm(p[nodes]-target,axis=1))]]*1e3
        x,y,_=proj3d.proj_transform(*anchor,ax.get_proj())
        ax.annotate(label,(x,y),xycoords='data',xytext=position,textcoords='axes fraction',fontsize=10,ha='left',va='center',bbox={'facecolor':'white','edgecolor':'none','alpha':.93,'pad':2},arrowprops={'arrowstyle':'-','color':'.25','lw':.7},annotation_clip=False)
    def view3d(name,cut=False,tec=False,thermal=False):
        selected=set(range(1,190))|{191,192,193,196,199} if tec else set(by)
        mask=np.isin(owners,list(selected));faces=f[ext[mask]];own=owners[mask]
        # Boundary of the selected solid union, including its real mount underside.
        if tec:
            contact_by_tag={x['boundary_id']:x['bodies'] for x in m['contacts']}
            extra=[];eb=[]
            for i in np.flatnonzero(tags>=1001):
                pair=contact_by_tag[int(tags[i])];inside=[v for v in pair if v in selected]
                if len(inside)==1:extra.append(f[i]);eb.append(inside[0])
            faces=np.concatenate([faces,np.array(extra,dtype=int)]);own=np.r_[own,eb]
        xyz=p[faces];data=np.stack([T[faces],np.repeat(own[:,None],3,axis=1)],axis=-1)
        if cut:
            xyz,data=clip_triangles(xyz,data);s=np.isin(b[sc],list(selected));xyz=np.concatenate([xyz,tri[s]]);closing=np.stack([st[s],np.repeat(b[sc[s],None],3,axis=1)],axis=-1);data=np.concatenate([data,closing])
        material=[by[int(v)]['material'] for v in np.rint(data[:,:,1].mean(1)).astype(int)];fc=[palette[v] for v in material]
        temperature_norm=colors.Normalize(float(T.min()),float(T.max()))
        if thermal:fc=plt.get_cmap('plasma')(temperature_norm(data[:,:,0].mean(1)))
        fig=plt.figure(figsize=(7.6,5.4 if not tec else 5.8));ax=fig.add_subplot(111,projection='3d');ax.add_collection3d(Poly3DCollection(xyz*1e3,facecolors=fc,edgecolors=(.12,.15,.17,.22) if thermal else '#50575b',linewidths=.025 if thermal else .055,alpha=1.,rasterized=True))
        limits=((-3.4,3.4),(0,3.4),(-.28,3.85)) if tec else ((-16,16),(-9,9) if not cut else (0,9),(-3.5,8.5));decorate3d(ax,limits)
        ax.set_xticks([-3,0,3] if tec else [-15,0,15]);ax.set_yticks([0,1.5,3] if tec else ([0,4,8] if cut else [-8,0,8]));ax.set_zticks([0,1,2,3] if tec else [-2,0,4,8])
        names=['Alumina','N','P','Cu','MCT','Attach','Mount'] if tec else ['Kovar','Pin','Glass','Steel','ZnSe']
        if not thermal:ax.legend(handles=[Patch(facecolor=palette[n],edgecolor='.3',label=n) for n in names],loc='upper center',bbox_to_anchor=(.5,1.05),ncol=4 if tec else 5,frameon=False,fontsize=10)
        fig.subplots_adjust(left=.005,right=.83 if thermal else .89,bottom=.10,top=.90)
        if not thermal:
            ax.set(xlabel='',ylabel='',zlabel='')
            fig.text(.40,.075,'$x$ (mm)',ha='center',fontsize=12)
            fig.text(.83,.15,'$y$ (mm)',ha='center',rotation=40,fontsize=12)
            fig.text(.93,.56,'$z$ (mm)',ha='center',rotation=90,fontsize=12)
        if thermal:
            cax=fig.add_axes([.91,.24,.025,.48]);fig.colorbar(cm.ScalarMappable(norm=temperature_norm,cmap='plasma'),cax=cax,label='$T$ (K)')
            callout(ax,193,[0,0,.0038],f"MCT mean {d['metrics']['die_mean_k']:.3f} K",(.02,.98))
            callout(ax,4,[.001,0,.0035],f"Cold ceramic {d['metrics']['cold_ceramic_k']:.3f} K",(.02,.88))
        elif cut and not tec:
            callout(ax,215,[0,0,.008],'Window',(.72,.94))
            callout(ax,214,[.0076,0,.004],'Cap',(.80,.75))
            callout(ax,193,[0,0,.0038],'TEC + detector',(.02,.86))
            callout(ax,190,[.010,0,-.0008],'Header / bath underside',(.40,.04))
        elif tec:
            callout(ax,193,[0,0,.0038],'MCT / attach',(.04,.89))
            callout(ax,191,[0,0,-.0001],'Mount proxy',(.06,.13))
        save(fig,name,True)
    view3d('full_mesh');view3d('package_cutaway',True);view3d('tec_cutaway',True,True);view3d('temperature_3d',True,True,True)
    # True section triangulation in millimetres; actual voids remain white.
    projection=tri[:,:,[0,2]]*1e3;roi=(tri[:,:,0].min(1)>-.0035)&(tri[:,:,0].max(1)<.0035)&(tri[:,:,2].min(1)>-.0003)&(tri[:,:,2].max(1)<.004)
    def axis2(ax):
        ax.set(xlim=(-3.4,3.4),ylim=(-.28,3.86),xlabel='$x$ (mm)',ylabel='$z$ (mm)');ax.set_aspect('equal');ax.spines[['top','right']].set_visible(False)
    def outlines(ax):
        # Every actual cut triangle is retained; light mesh lines disclose sampling.
        ax.add_collection(PolyCollection(projection[roi],facecolors='none',edgecolors=(0,0,0,.18),linewidths=.12))
    fig,ax=plt.subplots(figsize=(7,4.9));ax.add_collection(PolyCollection(projection[roi],facecolors=[palette[by[int(v)]['material']] for v in b[sc[roi]]],edgecolors='#30373b',linewidths=.16));axis2(ax);fig.tight_layout();save(fig,'section_mesh')
    vertices,connections,tval=triangle_grid(tri[roi],st[roi]);grid=mtri.Triangulation(vertices[:,0]*1e3,vertices[:,2]*1e3,connections)
    tgrid=grid
    fig,ax=plt.subplots(figsize=(7,4.9));plot=ax.tricontourf(grid,tval,levels=np.linspace(268,301,67),cmap='plasma',extend='neither');axis2(ax);fig.colorbar(plot,ax=ax,pad=.025,shrink=.88,label='$T$ (K)',ticks=[270,280,290,300]);fig.tight_layout();save(fig,'temperature_section')
    # Local P1 detector section plus independent volume-weighted means from the
    # same solved mesh; no reduced-network temperature is substituted.
    volume,_=tetra_geometry(p,c)
    profile=[]
    for bid,label in [(1,'Hot ceramic'),(2,'Ceramic 1'),(3,'Ceramic 2'),(4,'Cold ceramic'),(193,'MCT')]:
        sel=b==bid;weight=volume[sel];mean=float(weight@T[c[sel]].mean(1)/weight.sum());z=float(weight@p[c[sel],2].mean(1)/weight.sum())
        profile.append({'body_id':bid,'label':label,'volume_mean_k':mean,'centroid_z_mm':z*1e3})
    audit['annotated_results']={'volume_means':profile,'detector_min_k':d['metrics']['die_min_k'],'detector_max_k':d['metrics']['die_max_k'],'die_to_cold_k':d['metrics']['die_to_cold_k']}
    fig,axs=plt.subplots(1,2,figsize=(8.2,4.2),gridspec_kw={'width_ratios':[1.3,1]})
    plot=axs[0].tricontourf(tgrid,tval,levels=np.linspace(267,271,49),cmap='plasma',extend='both')
    axs[0].set(xlim=(-.75,.75),ylim=(3.30,3.84),xlabel='$x$ (mm)',ylabel='$z$ (mm)',title='(a) Detector and attach section');axs[0].set_aspect('equal')
    for text,xy,pos in [('MCT',(0,3.73),(-.68,3.80)),('Attach',(.55,3.62),(.28,3.80)),('Alumina',(.7,3.47),(.1,3.34))]:
        axs[0].annotate(text,xy,xytext=pos,fontsize=10,arrowprops={'arrowstyle':'-','lw':.7},bbox={'facecolor':'white','edgecolor':'none','alpha':.8,'pad':1})
    fig.colorbar(plot,ax=axs[0],orientation='horizontal',pad=.18,shrink=.9,label='$T$ (K)',ticks=[267,268,269,270,271])
    axs[1].plot([v['volume_mean_k'] for v in profile],[v['centroid_z_mm'] for v in profile],'-o',color='#315c75',ms=5,lw=1)
    axs[1].set(xlabel='Volume mean temperature (K)',ylabel='Centroid height (mm)',title='(b) Actual solid volume means',xlim=(265,303),ylim=(-.3,4.2));axs[1].grid(alpha=.2)
    for v in profile:
        if v['label'] in ('Hot ceramic','Ceramic 1','Ceramic 2'):
            axs[1].annotate(v['label'],(v['volume_mean_k'],v['centroid_z_mm']),xytext=(-3,9),textcoords='offset points',ha='right',fontsize=9)
    axs[1].annotate(f"MCT {d['metrics']['die_mean_k']:.3f} K",(profile[-1]['volume_mean_k'],profile[-1]['centroid_z_mm']),xytext=(8,12),textcoords='offset points',fontsize=9)
    for ax in axs:ax.spines[['top','right']].set_visible(False)
    fig.tight_layout(w_pad=1.8);save(fig,'thermal_detail')
    conductor_ids=[x['id'] for x in m['bodies'] if x['material'] in ('P','N','Cu')];active=roi&np.isin(b[sc],conductor_ids)
    vertices,connections,pval=triangle_grid(tri[active],sv[active]*1e3);grid=mtri.Triangulation(vertices[:,0]*1e3,vertices[:,2]*1e3,connections)
    fig,ax=plt.subplots(figsize=(7,4.9));ax.add_collection(PolyCollection(projection[roi],facecolors='#ededE8',edgecolors='none'));plot=ax.tricontourf(grid,pval,levels=np.linspace(0,540,55),cmap='cividis');axis2(ax);fig.colorbar(plot,ax=ax,pad=.025,shrink=.88,label='$\\phi$ (mV)',ticks=[0,100,200,300,400,500]);fig.tight_layout();save(fig,'potential_section')
    for field,name,label,mask,minimum in [(J,'current_section','$|\\mathbf{j}|$ (A m$^{-2}$)',active,1e4),(q,'heat_section','$|\\mathbf{q}|$ (W m$^{-2}$)',roi,1.)]:
        mag=np.linalg.norm(field[sc],axis=1);sel=mask&(mag>minimum);fig,ax=plt.subplots(figsize=(7,4.9));ax.add_collection(PolyCollection(projection[roi],facecolors='#ededE8',edgecolors='none'));norm=colors.LogNorm(minimum,float(mag[sel].max()));plot=PolyCollection(projection[sel],array=mag[sel],norm=norm,cmap='viridis',edgecolors='none');ax.add_collection(plot);axis2(ax);fig.colorbar(plot,ax=ax,pad=.025,shrink=.88,label=label)
        center=projection[sel].mean(1);vec=field[sc[sel]][:,[0,2]];size=np.linalg.norm(vec,axis=1);good=size>minimum;center=center[good];vec=vec[good]/size[good,None];bins=np.floor(center/[.28,.25]).astype(int);_,ix=np.unique(bins,axis=0,return_index=True);ax.quiver(center[ix,0],center[ix,1],vec[ix,0],vec[ix,1],color='#f9f5e6',angles='xy',scale_units='xy',scale=8,width=.0022,headwidth=3.5);fig.tight_layout();save(fig,name)
    fig,axs=plt.subplots(2,2,figsize=(8.3,8.1))
    ax=axs[0,0];ax.add_collection(PolyCollection(projection[roi],facecolors=[palette[by[int(v)]['material']] for v in b[sc[roi]]],edgecolors='#30373b',linewidths=.13));ax.set_title('(a) Exact mesh section')
    ax=axs[0,1];ax.add_collection(PolyCollection(projection[roi],facecolors='#edede8',edgecolors='none'));plot=ax.tricontourf(grid,pval,levels=np.linspace(0,540,55),cmap='cividis');ax.set_title('(b) Conductor potential');fig.colorbar(plot,ax=ax,orientation='horizontal',pad=.19,label='$\\phi$ (mV)',ticks=[0,200,400])
    for ax,field,title,mask,minimum,label in [(axs[1,0],J,'(c) Conductor current',active,1e4,'$|\\mathbf{j}|$ (A m$^{-2}$)'),(axs[1,1],q,'(d) Total solid heat flux',roi,1.,'$|\\mathbf{q}|$ (W m$^{-2}$)')]:
        mag=np.linalg.norm(field[sc],axis=1);sel=mask&(mag>minimum);ax.add_collection(PolyCollection(projection[roi],facecolors='#edede8',edgecolors='none'));plot=PolyCollection(projection[sel],array=mag[sel],norm=colors.LogNorm(minimum,float(mag[sel].max())),cmap='viridis',edgecolors='none');ax.add_collection(plot);ax.set_title(title);fig.colorbar(plot,ax=ax,orientation='horizontal',pad=.19,label=label)
        center=projection[sel].mean(1);vec=field[sc[sel]][:,[0,2]];size=np.linalg.norm(vec,axis=1);good=size>minimum;center=center[good];vec=vec[good]/size[good,None];_,ix=np.unique(np.floor(center/[.45,.4]).astype(int),axis=0,return_index=True);ax.quiver(center[ix,0],center[ix,1],vec[ix,0],vec[ix,1],color='white',angles='xy',scale_units='xy',scale=6,width=.004)
    for ax in axs.flat:axis2(ax);ax.tick_params(labelsize=10)
    fig.tight_layout(h_pad=2.2,w_pad=1.4);save(fig,'field_diagnostics')
    labels=['solid_reference_h0','lead_only_0','vacuum_a0','nitrogen_0','argon_0','krypton_0','window_high_0'];display=['Solids + Au','+ Cu supply leads','Vacuum + radiation','N$_2$, 100 Pa','Ar, 100 Pa','Kr, 100 Pa','Vacuum, window $\\epsilon=0.8$'];yy=np.arange(len(labels))[::-1];fig,ax=plt.subplots(figsize=(7,4.3));ax.plot([cases[x]['die_mean_k'] for x in labels],yy,'o',color='#245879',label='Die mean');ax.plot([cases[x]['cold_ceramic_k'] for x in labels],yy,'s',mfc='white',mec='#9b4547',label='Cold ceramic');ax.set(yticks=yy,yticklabels=display,xlabel='Temperature (K)',xlim=(262,270));ax.grid(axis='x',alpha=.2);ax.spines[['top','right']].set_visible(False);ax.legend(loc='lower right',frameon=False);fig.tight_layout();save(fig,'operating_points')
    ref=cases[CASE];fig,axs=plt.subplots(1,2,figsize=(7,4.2));keys=['TEC IV','Bias','Optical','Cu $I^2R$','Header out'];power=[ref['tec_input_w'],ref['pbias_w'],ref['poptical_thermal_w'],ref['lead_joule_w'],ref['hot_out_reaction_w']];axs[0].barh(np.arange(5)[::-1],np.array(power)*1e3,color=['#3b657c']*4+['#8c594c']);axs[0].set(yticks=np.arange(5)[::-1],yticklabels=keys,xlabel='Power (mW)',xlim=(0,68));
    for i,v in enumerate(power):axs[0].text(v*1e3+.8,4-i,f'{v*1e3:.3f}',va='center',fontsize=8)
    ownerset=['MCT_x029','die_attach','Au_die_pad_0','Au_die_pad_1','ceramic_3'];mechanisms=['radiation','gas','gold','lead_conduction'];vals=[sum(row[k] for name,row in ref['exchange_by_body_w'].items() if name in ownerset)*1e3 for k in mechanisms];axs[1].barh(np.arange(4)[::-1],vals,color=['#997246','#477f91','#ac913a','#606f77']);axs[1].set(yticks=np.arange(4)[::-1],yticklabels=['Radiation','Gas film','Au bonds','Cu conduction'],xlabel='Into cold assembly (mW)');axs[1].axvline(0,color='.3',lw=.6)
    for ax in axs:ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15)
    axs[0].set_title('(a) External budget');axs[1].set_title('(b) Selected internal transfers');fig.tight_layout(w_pad=1.8);save(fig,'heat_budget')
    failures=summary['unaccepted_fine_cases'];fig,ax=plt.subplots(figsize=(7,4));ax.axhline(1,color='#9c3a39',ls='--',lw=1,label='Unchanged 1% gate');ax.scatter([ref['nodes']/1000],[100*ref['direct_bath_relative_error']],s=60,color='#245879',label='Accepted coarse / 907 patches');
    for label,r in failures.items():ax.scatter(r['nodes']/1000,100*r['direct_bath_relative_error'],marker='x',s=65,lw=1.6,color='#a03b3b');ax.annotate(f"{100*r['direct_bath_relative_error']:.3f}%",(r['nodes']/1000,100*r['direct_bath_relative_error']),xytext=(0,8),textcoords='offset points',ha='center',fontsize=9)
    ax.scatter([],[],marker='x',color='#a03b3b',label='Converged fine, UNACCEPTED');ax.set(xlabel='Mesh nodes ($10^3$)',ylabel='Independent bath-gradient error (%)',ylim=(0,1.95));ax.spines[['top','right']].set_visible(False);ax.legend(frameon=False,loc='lower right');ax.grid(alpha=.15);fig.tight_layout();save(fig,'qualification')
    # All text and tables below are derived directly from verified archival records.
    def esc(s):return str(s).replace('\\','\\textbackslash{}').replace('_','\\_').replace('%','\\%').replace('&','\\&')
    def table(rows):return '\n'.join(' & '.join(map(str,row))+r' \\' for row in rows)
    tex=[]
    def macro(name,value):tex.append('\\newcommand{\\'+name+'}{'+str(value)+'}')
    rawsha=audit['fields']['fields_t0001.vtu']['uncompressed_sha256'];derivedsha=audit['fields']['derived.vtu']['uncompressed_sha256'];meshsha=audit['mesh_sha256']
    generator_files=[ROOT/'reports'/x for x in ('build_engineering_report.py','field_geometry.py','fem_report_data.py','verification.py','validate_report.py','report.tex')];generator={str(x.relative_to(ROOT)):sha(x) for x in generator_files};g=hashlib.sha256(json.dumps(generator,sort_keys=True).encode()).hexdigest()
    for name,val in {'NodeCount':f'{len(p):,}','TetCount':f'{len(c):,}','CutTriangles':f"{len(tri):,}",'CutLegs':audit['section']['intersected_leg_domains'],'FieldDie':f"{ref['die_mean_k']:.6f}",'FieldCold':f"{ref['cold_ceramic_k']:.6f}",'FieldVoltage':f"{ref['voltage_v']:.9f}",'FieldBathError':f"{100*ref['direct_bath_relative_error']:.6f}",'HeaderPower':f"{1e3*ref['hot_out_reaction_w']:.9f}",'TECPower':f"{1e3*ref['tec_input_w']:.9f}",'LeadJoule':f"{1e3*ref['lead_joule_w']:.9f}",'EnergyResidual':f"{ref['global_energy_error_w']:.3e}",'JCheckError':f"{audit['derived_vectors_normalized_max_error']['J_A_m2']:.3e}",'QCheckError':f"{audit['derived_vectors_normalized_max_error']['q_W_m2']:.3e}"}.items():macro(name,val)
    tex.append('\\newcommand{\\OperatingRows}{'+table([[display[i].replace('N$_2$','N$_2$'),f"{cases[x]['cold_ceramic_k']:.6f}",f"{cases[x]['die_mean_k']:.6f}",f"{cases[x]['voltage_v']:.9f}",f"{100*cases[x]['direct_bath_relative_error']:+.5f}"] for i,x in enumerate(labels)])+'}')
    fine_labels=['Global refinement','Header-bath refinement','Feedthrough refinement']
    tex.append('\\newcommand{\\FailureRows}{'+table([[label,f"{r['nodes']:,}",f"{r['tetrahedra']:,}",f"{100*r['direct_bath_relative_error']:.6f}"] for label,r in zip(fine_labels,failures.values())])+'}')
    tex.append('\\newcommand{\\PinRows}{'+table([[str(i+1),f'{x*1e3:+.6f}',f'{y*1e3:+.6f}'] for i,(x,y) in enumerate(reg['feedthroughs']['centers_xy_m'])])+'}')
    from reports.verification import verification_matrix
    matrix=verification_matrix(summary,audit,reg['numerical_limits'])
    tex.append('\\newcommand{\\VerificationRows}{'+table([[row[k] for k in ('test','criterion','evidence','status')] for row in matrix])+'}')
    dump(out/'verification_matrix.json',{'rows':matrix,'source_summary_sha256':sha(ARCHIVE/'charts/summary.json'),'full_qualification':False})
    bybody=ref['exchange_by_body_w'];groups={'Die/attach/Au pads':['MCT_x029','die_attach','Au_die_pad_0','Au_die_pad_1'],'Cold ceramic':['ceramic_3'],'Cap/window':['enclosure_cap','ZnSe_window'],'Nine pins':[x for x in bybody if x.startswith('pin_')]};used=sum(groups.values(),[]);groups['Other solids']=[x for x in bybody if x not in used]
    tex.append('\\newcommand{\\BudgetRows}{'+table([[name]+[f"{1e3*sum(bybody.get(x,{}).get(k,0) for x in ids):+.6f}" for k in ('radiation','gas','gold','lead_conduction','lead_joule')] for name,ids in groups.items()])+'}')
    src=ROOT/'fem/results/g3a_20261029/charts/summary.json';ga=read(src)['cases']['loaded_1'];macro('GThreeADie',f"{ga['die_mean_k']:.6f}");macro('GThreeACold',f"{ga['cold_ceramic_k']:.6f}")
    (out/'numerics.tex').write_text('\n'.join(tex)+'\n')
    inputs={str(ARCHIVE.relative_to(ROOT)/'checksums.json'):sha(ARCHIVE/'checksums.json'),str(src.relative_to(ROOT)):sha(src),str((ROOT/'data/g3b/enclosure_registry.json').relative_to(ROOT)):sha(ROOT/'data/g3b/enclosure_registry.json'),'geometry/revision6/engineering_assumptions.json':sha(ROOT/'geometry/revision6/engineering_assumptions.json'),'docs/rev6_cad_audit.md':sha(ROOT/'docs/rev6_cad_audit.md')}
    inputs.update({str(x.relative_to(ROOT)):sha(x) for x in [ARCHIVE/'charts/summary.json',ARCHIVE/'operators/operator_h0p1/mesh.npz',ARCHIVE/'operators/operator_h0p1/manifest.json',ARCHIVE/'cases'/CASE/'metrics.json',ARCHIVE/'cases'/CASE/'execution.json',ROOT/'data/g3b/source_review.json',ROOT/'data/g3b/runtime_lock.json',ROOT/'REPORT_REBUILD_WORK_ORDER.md',ROOT/'REPORT_REVISION2_WORK_ORDER.md']})
    import scipy,meshio
    audit.update(report_revision=2,software_versions={'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'meshio':meshio.__version__},generator_sha256=generator,generator_digest=g,input_sha256=inputs,derived_sha256={name:sha(out/name) for name in ('numerics.tex','verification_matrix.json')},figures={x.name:{'sha256':sha(x),'format':x.suffix[1:],'raster_dpi':600 if x.suffix=='.png' else None} for x in generated},pre_solder_status='physically present per user work order; FEM generic50um k2 W/m/K mount proxy, not identified metallic pre-solder',baseline_evidence_modified=False)
    dump(out/'report_inputs.json',audit);print('PASS: archived fields, mappings, reconstructed J/q and volume means; generated',len(generated),'scientific figures',flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--figures-only',action='store_true');p.add_argument('--out',type=Path,default=ROOT/'reports/generated');p.add_argument('--skip-figures',action='store_true');a=p.parse_args();out=a.out.resolve()
    if not out.is_relative_to(ROOT):raise ValueError('Report output must remain in this project')
    if a.figures_only:scientific_build(out);return
    out.mkdir(parents=True,exist_ok=True)
    if a.skip_figures:
        from reports.validate_report import verify_files
        verify_files(out)
    if not a.skip_figures:subprocess.run([str(ROOT/'fem/run_g2b.sh'),'python','reports/build_engineering_report.py','--figures-only','--out',str(Path('/work')/out.relative_to(ROOT))],cwd=ROOT,check=True)
    wrapper=out/'report.tex';wrapper.write_text('\\def\\reportdata{'+out.as_posix()+'}\n\\input{'+(ROOT/'reports/report.tex').as_posix()+'}\n')
    environment={**os.environ,'SOURCE_DATE_EPOCH':'1793232000','FORCE_SOURCE_DATE':'1'}
    for suffix in ('aux','out','toc'):
        stale=out/('HgCdTe_Engineering_Assessment.'+suffix)
        if stale.exists():stale.unlink()
    for _ in range(3):
        with (out/'latex-build.log').open('w') as log:subprocess.run(['pdflatex','-halt-on-error','-interaction=nonstopmode','-file-line-error','-output-directory',str(out),'-jobname','HgCdTe_Engineering_Assessment',str(wrapper)],cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run([sys.executable,str(ROOT/'reports/validate_report.py'),'--out',str(out)],cwd=ROOT,check=True)
    print('Built and validated',out/'HgCdTe_Engineering_Assessment.pdf')

if __name__=='__main__':main()
