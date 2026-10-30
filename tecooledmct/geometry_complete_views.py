"""Actual mesh geometry and hybrid wire routes, never fabricated solved fields."""
import argparse,json
from pathlib import Path
import numpy as np
from .geometry_rebaseline import sha,write


def render(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    d=np.load(out/'mesh.npz');p=d['points']*1000;c=d['cells'];b=d['bodies']
    m=json.loads((out/'manifest.json').read_text());w=json.loads((out/'wire_routes.json').read_text())
    fig=plt.figure(figsize=(12,9));ax=fig.add_subplot(projection='3d',computed_zorder=False)
    by={row['id']:row for row in m['bodies']}
    for bid in sorted(np.unique(b),key=lambda k:by[k]['material'] in ('Cu','P','N')):
        if bid==300 or 400<=bid<600:continue
        cc=c[b==bid];f=cc[:,[[1,2,3],[0,3,2],[0,1,3],[0,2,1]]].reshape(-1,3)
        f,count=np.unique(np.sort(f,axis=1),axis=0,return_counts=True);f=f[count==1]
        mat=by[bid]['material'];color={'Cu':'#b76c37','P':'#ad4f52','N':'#3b7fa3','Alumina':'#cdc6b7','Presolder':'#8c8c8c','Au':'#c4a248','MCT':'#36554a','Attach':'#b0b0b0'}[mat]
        ax.add_collection3d(Poly3DCollection(p[f],facecolor=color,edgecolor='none',alpha=.16 if mat=='Alumina' else 1,
                                           zorder=2 if mat=='Alumina' else 3,rasterized=True))
    for row in w['wires']:
        v=np.array(row['polyline_m'])*1000;ax.plot(*v.T,'--',color='#c17a3e' if row['material']=='Cu' else '#a38a2a',lw=1.8,zorder=5)
        ax.scatter(*v[0],color='#2f5d70',s=18,zorder=5);ax.text(*v[0],f'pin{row["pin"]}',fontsize=9,zorder=6)
    ax.plot([-4,-3],[-4,-4],[1.6,1.6],color='black',lw=3,zorder=5);ax.text(-3.5,-4,1.8,'1 mm',zorder=6)
    ax.set(xlim=(-5.8,5.8),ylim=(-5.8,5.8),zlim=(1.4,6.2),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)')
    ax.set_box_aspect((11.6,11.6,4.8));ax.set_proj_type('ortho');ax.view_init(elev=28,azim=-65)
    ax.set_title('Actual88-leg module mesh: P red, N blue, Cu brown; transparent alumina\nDashed wires are reduced1D paths; both TEC pads are on hot ceramic. Header omitted from this zoom.',fontsize=11)
    fig.tight_layout();fig.savefig(out/'actual_stack_mesh.png',dpi=300);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,7))
    for row in m['bodies']:
        if row['id'] not in (184,185,190,191,192):continue
        for box in row['boxes_m']:
            x,y,z,dx,dy,dz=np.array(box)*1000
            ax.add_patch(plt.Rectangle((x,z),dx,dz,fill=row['id']==191,alpha=.35 if row['id']==191 else .8,
                                      edgecolor='#a64e2e' if row['id']==191 else '#777777',facecolor='#c67c42' if row['id']==191 else 'none'))
    for row in m['bodies'][:4]:
        x,y,z,dx,dy,dz=np.array(row['boxes_m'][0])*1000
        ax.add_patch(plt.Rectangle((x,z),dx,dz,fill=False,edgecolor='#39697b'))
    ax.annotate('Stage2 terminal → insulated resolved return',(-1.025,4.39),xytext=(-3.7,5.3),arrowprops={'arrowstyle':'->'},fontsize=9)
    ax.annotate('Both hot-side external pads',(-2.8,1.835),xytext=(-3.7,1.15),arrowprops={'arrowstyle':'->'},fontsize=9)
    ax.plot([2,3],[1.3,1.3],color='black',lw=3);ax.text(2.5,1.43,'1 mm',ha='center')
    ax.set(xlim=(-4,3.5),ylim=(1,5.8),xlabel='x (mm)',ylabel='z (mm)',title='Dimensioned x-z projection of actual registered boxes\nProjection overlaps do not imply electrical contact; exact3D CSG/mesh adjacency is audited')
    ax.set_aspect('equal');fig.tight_layout();fig.savefig(out/'return_route_projection.png',dpi=300);plt.close(fig)
    write(out/'view_provenance.json',{'mesh_sha256':sha(out/'mesh.npz'),'source_sha256':sha(Path(__file__)),
          'actual_stack_mesh':'actual tetrahedron skin, no temperature/current field','return_projection':'registered3D box projection, NOT a true section',
          'wires':'explicit1D hybrid paths, unmeshed in3D'})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);render(parser.parse_args().out.resolve())
