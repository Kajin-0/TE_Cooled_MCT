"""Solid-filled inspection views of the frozen synthetic V3 replacement TEC.
Source: exact body primitives and analytical formed-tab curves in the 824-body
design.json. Source CAD is not modified; plates/legs/foils are never displaced.
The source shapes are tessellated only for visualization, no FEM is performed.
"""
from pathlib import Path
import json, math, hashlib, argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch,Rectangle
from matplotlib import patheffects

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
OUT=Path(__file__).resolve().parent/'figures'
OUT.mkdir(parents=True,exist_ok=True)
D=json.loads(SRC.read_text())
B=D['bodies']
assert len(B)==824 and len(D['legs'])==88
COLORS={'Al2O3':'#dbe5e9','P':'#d97376','N':'#467eaa',
        'SnSb':'#a6adb0','Cu':'#d9a34d','Au':'#e2c077','Ni':'#a8acb4',
        'Ti':'#9b9da8','TiW':'#a3a4aa','SnBi57_43':'#cdb3ad',
        'Sapphire':'#77c1bc','EP29LPSP':'#545b66','pHgCdTe_PC':'#684a70'}
SPECIAL={'formed_tab58':'#e86b25','formed_tab80':'#e86b25',
        'formed_tab88':'#ef8139'}
def box_polys(q):
    x,y,z,dx,dy,dz=map(float,q)
    v=np.array([[x,y,z],[x+dx,y,z],[x+dx,y+dy,z],[x,y+dy,z],
                [x,y,z+dz],[x+dx,y,z+dz],[x+dx,y+dy,z+dz],[x,y+dy,z+dz]])
    return [v[j] for j in ([0,1,2,3],[4,5,6,7],[0,1,5,4],
                          [3,2,6,7],[0,3,7,4],[1,2,6,5])]
def norm3(a):
    m=np.linalg.norm(a)
    return a/m if m>1e-12 else a
def shade(poly,color):
    p=np.asarray(poly)
    normal=norm3(np.cross(p[1]-p[0],p[2]-p[0]))
    # Soften the light depending on each face orientation (two-sided shading)
    light=norm3(np.array([-0.42,-0.58,0.70]))
    illum=.70+.27*abs(np.dot(normal,light))
    return tuple(np.clip(np.array(to_rgb(color))*illum+.035,0,1))
def xy_point_for_arc(p,n=10):
    a=np.asarray(p['a'],float);b=np.asarray(p['b'],float)
    if p['type']=='line':
        return np.vstack([a,b])
    c=np.asarray(p['c'],float)
    t0=math.atan2(a[1]-c[1],a[0]-c[0])
    t1=math.atan2(b[1]-c[1],b[0]-c[0])
    # Gmsh uses signed arc direction; the shortest quarter-circle matches source.
    delta=(t1-t0+math.pi)%(2*math.pi)-math.pi
    ts=t0+np.linspace(0,delta,n+1)
    return c+float(p['r'])*np.stack([np.cos(ts),np.sin(ts)],axis=1)
def centers(parts):
    pts=[]
    for p in parts:
        pp=xy_point_for_arc(p)
        if pts:pp=pp[1:]
        pts.extend(pp)
    return np.asarray(pts)
def foil_polys(body):
    # Exact source centerline including nominal source bend radius; t=0.030mm,
    # extruded x width 0.300mm. The two faces are offset along local 2D normal.
    path=centers(body['parts'])
    tang=np.gradient(path,axis=0)
    tang=tang/np.linalg.norm(tang,axis=1)[:,None]
    n=np.stack([-tang[:,1],tang[:,0]],axis=1)
    upper=path+n*(body['thickness']/2)
    lower=path-n*(body['thickness']/2)
    x0=body['x']-body['width']/2
    x1=body['x']+body['width']/2
    out=[]
    for i in range(len(path)-1):
        v0=np.array([[x0,*upper[i]],[x1,*upper[i]],
                     [x1,*lower[i]],[x0,*lower[i]]])
        v1=np.array([[x0,*upper[i+1]],[x1,*upper[i+1]],
                     [x1,*lower[i+1]],[x0,*lower[i+1]]])
        out.extend([np.asarray([v0[j],v0[(j+1)%4],v1[(j+1)%4],v1[j]]) for j in range(4)])
    out += [np.array([[x0,*upper[0]],[x1,*upper[0]],[x1,*lower[0]],[x0,*lower[0]]]),
            np.array([[x0,*upper[-1]],[x1,*upper[-1]],[x1,*lower[-1]],[x0,*lower[-1]]])]
    return out
def visible(body, mode='full'):
    name=body['name'];m=body['material']
    if name.startswith('ceramic'):return True
    if name.startswith('leg') and m in ('P','N'):return True
    if name.startswith('formed_tab'):return True
    if name.startswith('tab_joint'):return True
    if name.startswith('fillet'):return False  # micron-scale, immaterial at this zoom
    # Actual electrolytic solder pads: keep for fidelity, but do not use in isolated foil scene
    if mode=='full':
        if name.startswith('solder') and m=='SnSb':return True
        # Keep the Cu/visible gold on the same original contact nets; hide submicron underlayers
        if name.startswith('net') and m in ('Au','Cu'):return True
        if name.startswith('sapphire_carrier') or name.startswith('p_HgCdTe'):return True
        if name.startswith('die_attach') or name.startswith('carrier_attach'):return True
    if mode=='tabs':
        if name.startswith('net') and m in ('Au','Cu') and body.get('group') in (58,80,88):return True
    return False
def face_geometry(mode='full'):
    faces=[];colors=[];counts={}
    for b in B:
        if not visible(b,mode):continue
        if b['shape']=='boxes':
            patches=[face for q in b['boxes_mm'] for face in box_polys(q)]
        elif b['shape']=='tab':patches=foil_polys(b)
        else:continue
        col=SPECIAL.get(b['name'],COLORS.get(b['material'],'#777777'))
        # for plated net traces, material name as classified by original CAD
        if b['material']=='Cu' and b['name'].startswith('net'):col='#c49a58'
        faces.extend(patches)
        colors.extend([shade(q,col) for q in patches])
        counts[b['material']]=counts.get(b['material'],0)+1
    return faces,colors,counts
def setup(ax, elev, azim):
    ax.view_init(elev=elev,azim=azim,roll=0,vertical_axis='z')
    ax.set_xlim(-3.55,3.55);ax.set_ylim(-3.55,3.55);ax.set_zlim(1.44,6.03)
    ax.set_box_aspect((7.1,7.1,5.6),zoom=1.12)
    ax.set_axis_off()
    ax.set_facecolor('#fbfcfd')
def render_pair(output):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':'#fbfcfd'})
    fig=plt.figure(figsize=(15.5,8.5),facecolor='#fbfcfd')
    # Manual panels for precise layout independent of mpl constrained_layout
    a=fig.add_axes([.015,.17,.475,.74],projection='3d',computed_zorder=True)
    b=fig.add_axes([.51,.17,.475,.74],projection='3d',computed_zorder=True)
    faces,colors,counts=face_geometry()
    for ax,elev,azim in ((a,27,115),(b,28,-60)):
        coll=Poly3DCollection(faces,facecolors=colors,edgecolors='none',
                             zsort='average',linewidths=0,antialiased=True)
        ax.add_collection3d(coll)
        setup(ax,elev,azim)
    fig.text(.05,.935,'Replacement TEC: solid model inspection',fontsize=20,fontweight='bold',color='#21334b')
    fig.text(.05,.900,'Actual V3 R1 source CAD body geometry  |  no wireframe  |  outer enclosure hidden for inspection',
             color='#506477',fontsize=11)
    fig.text(.04,.155,'VIEW A · POSITIVE-Y FACE',fontsize=12,color='#243d51',fontweight='bold')
    fig.text(.53,.155,'VIEW B · OPPOSITE FACE',fontsize=12,color='#243d51',fontweight='bold')
    legend=[('Alumina ceramics',COLORS['Al2O3']),('P-type legs',COLORS['P']),
            ('N-type legs',COLORS['N']),('Metallization / joint',COLORS['Cu']),
            ('Formed Cu foil tabs',SPECIAL['formed_tab58']),('HgCdTe die',COLORS['pHgCdTe_PC'])]
    for i,(txt,c) in enumerate(legend):
        x=.035+(i%3)*.30;y=.105-(i//3)*.043
        fig.patches.append(Rectangle((x,y),.016,.020,transform=fig.transFigure,color=c,ec='#a4a9ae',lw=.4))
        fig.text(x+.022,y+.002,txt,color='#344457',fontsize=9.2)
    fig.text(.04,.012,'Source: frozen 824-body V3 replacement design.json; actual formed-tab arc paths tessellated for display. Some sub-micron layers, leads and the package are hidden.',
             fontsize=8.3,color='#647184')
    fig.savefig(output,dpi=210,facecolor=fig.get_facecolor(),bbox_inches='tight',pad_inches=.12)
    plt.close(fig)
    print('Rendering',output,'bodies',counts,'polygons',len(faces))
def render_tab_paths(output):
    import matplotlib.patheffects as pe
    fig,axs=plt.subplots(1,3,figsize=(15,5.1),facecolor='#fbfcfd')
    names=('formed_tab58','formed_tab80','formed_tab88')
    bmap={b['name']:b for b in B}
    # Show source Y/Z without shifting or aligning artificial exploded geometry
    for ax,name in zip(axs,names):
        bd=bmap[name]
        ymin=min(v['a'][0] for v in bd['parts'])-.35
        ymax=max(v['a'][0] for v in bd['parts'])+.35
        for idx,z in enumerate([1.58425,2.68425,3.78425,4.88425]):
            if z>4.6:continue
            width=[6.4,5.2,3.8][idx]/2
            # only actual ceramic zone on this y-vertical section
            left=max(ymin,-width);right=min(ymax,width)
            if right>left:
                ax.add_patch(Rectangle((left,z),right-left,.5,ec='#9aabb8',facecolor='#e2ebef',lw=.9,alpha=.56))
        path=centers(bd['parts'])
        tang=np.gradient(path,axis=0)
        tang=tang/np.linalg.norm(tang,axis=1)[:,None]
        n=np.stack([-tang[:,1],tang[:,0]],axis=1)
        up=path+n*bd['thickness']/2;lo=path-n*bd['thickness']/2
        outline=np.vstack([up,lo[::-1]])
        ax.fill(outline[:,0],outline[:,1],facecolor='#ea852e',edgecolor='#9d4a13',lw=1.0,zorder=5)
        # precise contact foot locations only, no exploded coordinates
        for i,z in enumerate([2.10925,3.20925,4.30925]):
            if abs(z-path[:,1].min())>.25 and abs(z-path[:,1].max())>.25 and name!='formed_tab88':continue
        ax.plot(path[:,0],path[:,1],color='#a73e1e',lw=.7,ls='--',alpha=.5,zorder=7)
        ax.grid(alpha=.13,zorder=0)
        ax.set_xlim(ymin,ymax);ax.set_ylim(1.96,4.48);ax.set_aspect('equal')
        ax.set_xlabel('Actual Y (mm)');ax.set_ylabel('Actual Z (mm)')
        ax.set_title(f'NET {name[-2:]}'+(' · STEPPED RETURN' if name.endswith('88') else ' · INTERSTAGE TAB'),color='#22394f',fontsize=12,fontweight='bold')
    fig.suptitle('Formed copper connections: actual section profiles',fontsize=18,fontweight='bold',color='#22394f')
    fig.text(.02,.008,'Derived from actual source analytic bend arcs and original stage coordinates. Ceramic sections shown in pale blue; 30 µm foil drawn at true scale (not exaggerated).',
             fontsize=9,color='#52677b')
    fig.savefig(output,dpi=210,bbox_inches='tight',pad_inches=.17)
    plt.close(fig)
    print('Saved section',output)
if __name__=='__main__':
    out=OUT/'tec_solid_inspection.png'
    render_pair(out)
    render_tab_paths(OUT/'tec_formed_tab_sections.png')
    h=hashlib.sha256(SRC.read_bytes()).hexdigest()
    (OUT/'tec_render_source.json').write_text(json.dumps({
        'source':'data/synthetic_v3_assembly_20261102/source_final/design.json',
        'source_sha256':h,'source_bodies':len(B),
        'geometry':'actual source boxes plus arc-tessellated analytic formed-foil body paths',
        'omissions':'outer package, external leads, submicron hidden coating layers, small fillet body edges',
        'new_solver_runs':0},indent=2)+'\n')
    print('Source SHA',h)
