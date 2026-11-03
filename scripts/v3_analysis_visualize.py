"""Generate actual triangulated BREP fixture surface visualizations, not field plots."""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def render(src,out,title):
    saved=np.load(src,allow_pickle=False)
    p=saved["points_mm"];tri=saved["triangles"]
    fig=plt.figure(figsize=(11,8),dpi=170)
    ax=fig.add_subplot(111,projection="3d",computed_zorder=False)
    polys=p[tri]
    poly=Poly3DCollection(polys,alpha=.64,edgecolor=(.2,.25,.32,.38),linewidths=.09)
    poly.set_facecolor((.18,.49,.72,.68))
    ax.add_collection3d(poly)
    mid=(p.max(axis=0)+p.min(axis=0))/2
    span=max(p.max(axis=0)-p.min(axis=0))*1.05
    ax.set_xlim(mid[0]-span/2,mid[0]+span/2)
    ax.set_ylim(mid[1]-span/2,mid[1]+span/2)
    ax.set_zlim(mid[2]-span/2,mid[2]+span/2)
    ax.set_box_aspect((1,1,1))
    ax.view_init(elev=29,azim=-58)
    ax.set(xlabel="X (mm)",ylabel="Y (mm)",zlabel="Z (mm)",title=title)
    fig.text(.04,.03,"Actual triangulation of versioned analysis BREP subset; no physics solve",fontsize=10,color="#425466")
    fig.tight_layout()
    fig.savefig(out,bbox_inches="tight",facecolor="white")
    plt.close(fig)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--src",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True);p.add_argument("--title",required=True)
    a=p.parse_args();render(a.src,a.out,a.title)
