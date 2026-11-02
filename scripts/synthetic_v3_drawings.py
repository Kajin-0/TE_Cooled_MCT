"""Actual STEP edge views and dimensioned assembly drawing details; no mesh."""
import argparse,json,math
from pathlib import Path
import gmsh,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from tecooledmct.tec_assembly_v3 import support_planes,tight_bounds

def main(cad,src,out):
    out.mkdir(exist_ok=False);d=json.loads((src/'design.json').read_text());gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    occ=gmsh.model.occ;tags=occ.importShapes(str(cad/'synthetic_v3_mm.step'));occ.synchronize();available={t for dim,t in tags if dim==3};pp=support_planes(occ);bodies=[];all_edges=[]
    cache={t:(occ.getMass(3,t),occ.getBoundingBox(3,t)) for t in available}
    colors={'Al2O3':'#607d8b','P':'#b83f45','N':'#295b9b','Cu':'#a26b13','Au':'#b49016','SnBi57_43':'#606060','In52Sn48':'#737373','pHgCdTe_PC':'#111111','Sapphire':'#329ca4','EP29LPSP':'#7c5d95','Kovar':'#777777','Kovar_pin':'#777777'}
    for b in d['bodies']:
        cand=[t for t in available if abs(cache[t][0]/b['volume_mm3']-1)<1e-7 and max(abs(x-y) for x,y in zip(cache[t][1],b['bbox_mm']))<.2]
        cand=[t for t in cand if max(abs(x-y) for x,y in zip(tight_bounds(occ,t,pp) if b['shape']=='wire' else cache[t][1],b['bbox_mm']))<.00021]
        if len(cand)!=1:raise ValueError(b['name'])
        t=cand[0];available.remove(t)
        if b['material'] not in colors:continue
        faces=gmsh.model.getBoundary([(3,t)],False,False);edges=set(abs(e) for dim,e in gmsh.model.getBoundary(faces,False,False) if dim==1)
        curves=[]
        for e in edges:
            lo,hi=gmsh.model.getParametrizationBounds(1,e);v=gmsh.model.getValue(1,e,np.linspace(lo[0],hi[0],18));curves.append(np.array(v).reshape(-1,3))
        bodies.append((b,curves,colors[b['material']]))
        all_edges.append(dict(name=b['name'],solid=t,curves_mm=[q.tolist() for q in curves]))
    gmsh.finalize();(out/'actual_brep_edges.json').write_text(json.dumps(all_edges,separators=(',',':'))+'\n')
    plt.rcParams.update({'font.size':10,'svg.hashsalt':'synthetic_v3'})
    for name,wide in [('package_actual_STEP',True),('module_actual_STEP',False)]:
        fig=plt.figure(figsize=(10,7.5));ax=fig.add_subplot(111,projection='3d')
        for b,curves,c in bodies:
            if not wide and (b['name'].startswith(('pin','glass','VIGO_reference','header_','hot_mount','lead')) or b['shape']=='header'):continue
            # Cap hidden for inspection; source remains present in exported assembly.
            if b['name'].startswith('cap'):continue
            if wide and b['material']=='Kovar_pin':curves=[q.copy() for q in curves];curves=[q for q in curves if np.max(q[:,2])>0] # only inside-header pin features
            ax.add_collection3d(Line3DCollection(curves,colors=c,linewidths=.4 if wide else .55,alpha=.85))
        lim=8 if wide else 3.6;ax.set(xlim=(-lim,lim),ylim=(-lim,lim),zlim=(0 if wide else 1.5,7),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)')
        ax.set_box_aspect((2*lim,2*lim,7 if wide else 5.5));ax.view_init(25,-55)
        ax.set_title('Actual imported STEP edges — '+('package interior' if wide else '88-leg module and installed bonds'))
        fig.text(.04,.04,'Cap/window hidden; exterior pin tails cropped for inspection. CAD geometry, no solved field.\nCu: ochre; P/N: red/blue; alumina: gray; detector: black. Synthetic, process qualification pending.',fontsize=9)
        fig.savefig(out/(name+'.png'),dpi=220);fig.savefig(out/(name+'.svg'),metadata={'Date':None});plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,6))
    # Cross section of ACTUAL imported tab/foot/riser at x=1.45; BRep projected y-z.
    ax=axs[0]
    for b,curves,c in bodies:
        if b['name'] not in ['formed_tab58','tab_joint0','tab_joint1','ceramic0','ceramic1','fillet0_-1','fillet0_1']:continue
        for q in curves:ax.plot(q[:,1],q[:,2],color=c,lw=.8)
    ax.set(xlim=(2.05,3.2),ylim=(1.95,3.5),xlabel='y (mm)',ylabel='z (mm)',title='Net58: imported tab and real feet')
    ax.text(2.08,3.42,'Foil 0.300 × 0.030 mm\nRneutral 0.075 / Rinner 0.060 mm\nTwo 0.300 × 0.200 × 0.020 mm joints',fontsize=9,va='top')
    ax.annotate('1.100 mm stage rise',xy=(2.68,3.23425),xytext=(2.14,2.6),arrowprops={'arrowstyle':'->'},fontsize=9)
    ax.grid(alpha=.25)
    ax=axs[1];yy=0
    layers=[('Header Ni',.002),('Header Au',.00025),('In52Sn48 mount',.080),('Au/Ni/Cu/TiW/Ti underside',.002),('Hot Al2O3',.500)]
    for j,(n,h) in enumerate(layers):
        # Vertical expansion explicitly stated; label actual thickness.
        hh=.12 if h<.01 else .24 if h<.1 else .65
        ax.add_patch(plt.Rectangle((0,yy),1,hh,color=plt.cm.tab20(j),ec='black',lw=.6));ax.text(1.04,yy+hh/2,f'{n}: {h*1000:g} µm',va='center',fontsize=9);yy+=hh
    ax.set(xlim=(-.02,2.65),ylim=(-.05,yy+.15),title='Hot mount: specified physical stack');ax.axis('off')
    ax.text(0,-.20,'Thicknesses expanded for legibility; nominal bondline 80 ±20 µm.\nFinished surfaces ≤10 µm; mount top datum 1.58425 mm.\nInSn 117 °C family; selected peak 125–132 °C, process pending.',fontsize=9,va='top')
    fig.suptitle('Synthetic V3 joint and mount drawing details (mm unless stated)');fig.tight_layout(rect=(0,.08,1,.95))
    fig.savefig(out/'joint_mount_sections.png',dpi=220);fig.savefig(out/'joint_mount_sections.svg',metadata={'Date':None});plt.close(fig)
    print('Three actual-geometry/dimensioned drawings complete')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cad',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.cad,a.source,a.out)
