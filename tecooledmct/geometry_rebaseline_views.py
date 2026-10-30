"""Dimensioned actual-mesh views and explicitly unconnected routing preview."""
import argparse
import json
from pathlib import Path
import numpy as np
from .geometry_registry import load, value, pins
from .geometry_rebaseline import sha, write


def views(directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    data=load(directory/'registry_snapshot.json'); mesh=np.load(directory/'mesh.npz')
    xyz=mesh['points']*1000; cells=mesh['cells']; bodies=mesh['bodies']
    h=value(data,'header_thickness'); joint=value(data,'presolder_thickness')
    c=value(data,'ceramic_thickness'); height=value(data,'tec_height')
    routes=[]
    for row, sign in ((pins(data)[0],-1),(pins(data)[8],1)):
        start=np.r_[row['xy_mm'],h+value(data,'pin_stub')]
        end=np.array([value(data,'hot_pad_x'),sign*value(data,'hot_pad_y'),h+joint+c])
        t=np.linspace(0,1,257); points=(1-t[:,None])*start+t[:,None]*end
        points[:,2]+=4*value(data,'lead_bow_height')*t*(1-t)
        L=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum())
        routes.append({'pin':row['pin'],'function':row['function'],'pin_endpoint_mm':start.tolist(),
                       'hot_ceramic_pad_preview_mm':end.tolist(),'sampled_arc_length_mm':L,
                       'straight_endpoint_distance_mm':float(np.linalg.norm(end-start)),
                       'full_88leg_route_connected':False,'status':'geometry preview; NO electrical or thermal coupling',
                       'points_mm':points.tolist()})
    fig=plt.figure(figsize=(11,8)); ax=fig.add_subplot(projection='3d',computed_zorder=False)
    for body in np.unique(bodies):
        tets=cells[bodies==body]; faces=tets[:,[[1,2,3],[0,3,2],[0,1,3],[0,2,1]]].reshape(-1,3)
        uniq,count=np.unique(np.sort(faces,axis=1),axis=0,return_counts=True); f=uniq[count==1]
        # Display actual surface triangles; transparent glasses show insulating annuli.
        color='#b5a174' if body==1 else '#c7e0e7' if 11<=body<=19 else '#9b9c9e' if 21<=body<=29 else '#ae6c3d' if body==30 else '#ece6d7'
        ax.add_collection3d(Poly3DCollection(xyz[f],facecolor=color,edgecolor='none',alpha=.5 if 11<=body<=19 else 1.,rasterized=True,
                                           zorder=2 if body==1 else 1 if 21<=body<=29 else 4))
    phi=np.linspace(0,2*np.pi,180); radius=value(data,'cap_od')/2; roof=value(data,'case_top_from_underside')
    for z in (h,roof):ax.plot(radius*np.cos(phi),radius*np.sin(phi),z,color='#2f6c87',ls='--',lw=.8,zorder=3)
    for angle in np.arange(0,2*np.pi,np.pi/2):ax.plot([radius*np.cos(angle)]*2,[radius*np.sin(angle)]*2,[h,roof],color='#2f6c87',ls='--',lw=.8,zorder=3)
    for route in routes:
        points=np.array(route['points_mm']);ax.plot(*points.T,color='#ad4b39',lw=2,zorder=6)
        ax.text(*route['pin_endpoint_mm'],str(route['pin']),fontsize=9,color='#8a2929',zorder=7)
    ax.plot([12,13],[-7,-7],[2,2],color='black',lw=3,zorder=6);ax.text(12,-7,3,'1 mm',fontsize=8,zorder=7)
    ax.set(xlim=(-16,16),ylim=(-9,9),zlim=(-13,14),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)')
    ax.set_box_aspect((32,18,27));ax.view_init(elev=25,azim=-58,vertical_axis='z')
    ax.set_proj_type('ortho');ax.set_title('Actual new header/feedthrough/ceramic mesh\nDashed case envelope and red lead previews are unmeshed; TEC interior absent',fontsize=11)
    fig.tight_layout();fig.savefig(directory/'actual_mesh_orthographic.png',dpi=300);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,6))
    for body in (1,15,25,30,31,32):
        # True y=0 section of actual tetrahedra, computed independently of CAD rectangles.
        tets=cells[bodies==body]; q=xyz[tets]; selected=(q[:,:,1].min(1)<=0)&(q[:,:,1].max(1)>=0); polygons=[]
        for tet in q[selected]:
            cross=[]
            for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
                if tet[i,1]*tet[j,1]<0:
                    t=-tet[i,1]/(tet[j,1]-tet[i,1]);cross.append((tet[i]+t*(tet[j]-tet[i]))[[0,2]])
                elif abs(tet[i,1])<1e-12:cross.append(tet[i,[0,2]])
                elif abs(tet[j,1])<1e-12:cross.append(tet[j,[0,2]])
            if len(cross)<3:continue
            p=np.unique(np.round(cross,10),axis=0)
            if len(p)<3:continue
            center=p.mean(0);angle=np.arctan2(p[:,1]-center[1],p[:,0]-center[0]);polygons.append(p[np.argsort(angle)])
        color='#b5a174' if body==1 else '#c7e0e7' if body==15 else '#9b9c9e' if body==25 else '#ae6c3d' if body==30 else '#ece6d7'
        ax.add_collection(PolyCollection(polygons,facecolors=color,edgecolors='none',rasterized=True))
    w=value(data,'tec_hot_width'); cold=value(data,'tec_cold_width'); top=h+joint+height
    for sign in (-1,1):
        ax.plot([sign*w/2,sign*cold/2],[h+joint,top],'--',color='#977b46')
        ax.plot([sign*radius]*2,[h,roof],'--',color='#2f6c87')
    ax.plot([-radius,radius],[roof,roof],'--',color='#2f6c87')
    ax.text(8.2,roof,'13.5 ±0.3 mm\ncase top datum',va='top',fontsize=9)
    ax.text(-15,3,'1.5 mm header\n50 µm joint hypothesis',fontsize=9)
    ax.text(-3,6,'TEC envelope3.8 ±0.15 mm\nNo internal legs meshed',fontsize=9)
    ax.plot([-11,-10],[-2,-2],lw=3,color='black');ax.text(-10.5,-1.4,'1 mm',ha='center',fontsize=9)
    ax.set(xlim=(-16,16),ylim=(-13,15),xlabel='x (mm)',ylabel='z (mm)',title='Actual y=0 mesh section; equal axis scales\nDashed enclosure/TEC extents are source envelope previews, not resolved solids')
    ax.set_aspect('equal');fig.tight_layout();fig.savefig(directory/'actual_mesh_section.png',dpi=300);plt.close(fig)
    write(directory/'routing_preview.json',{'routes':routes,'scope':'hot-side coordinate intent only; neither corrected full series route nor coupled physics exists',
          'renderer_sha256':sha(Path(__file__)),'mesh_sha256':sha(directory/'mesh.npz')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,required=True)
    views(parser.parse_args().directory.resolve())
