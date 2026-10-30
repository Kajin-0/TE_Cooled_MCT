"""Original figures from actual corrected-mesh solved fields; no report edits."""
import argparse,json
from pathlib import Path
import numpy as np
from .geometry_rebaseline import sha,write


def render(mesh,cases,out):
    import meshio,matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import Normalize
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from reports.field_geometry import plane_section,section_values,triangle_grid,node_map,cell_map
    out.mkdir(parents=True,exist_ok=False);d=np.load(mesh/'mesh.npz');p,c,b=(d[n] for n in ('points','cells','bodies'))
    section=plane_section(p,c,axis=1,coordinate=.00015);provenance={};fig,axs=plt.subplots(len(cases),3,figsize=(13,4.7*len(cases)),squeeze=False)
    for row,case in enumerate(cases):
        label_case={'cu_off':'Cu leads OFF','cu_on':'Cu leads ON'}.get(case.name,case.name)
        field=meshio.read(case/'derived.vtu');ix,_=node_map(p,field.points);inv=np.empty_like(ix);inv[ix]=np.arange(len(ix));ci=cell_map(c,inv[field.get_cells_type('tetra')])
        t=field.point_data['Temperature_K'].ravel()[ix];phi=field.point_data['Potential_V'].ravel()[ix];J=field.cell_data['J_A_m2'][0][ci]
        ts=section_values(section,c,t);ps=section_values(section,c,phi);tri=section['xyz'][:,:,[0,2]]*1000
        scalars=[ts.mean(1),ps.mean(1),np.log10(np.maximum(np.linalg.norm(J[section['cells']],axis=1),1e-20))]
        for col,(values,label,cmap) in enumerate(zip(scalars,('Temperature (K)','Potential (V)','log₁₀ |J| (A/m²)'),('viridis','plasma','magma'))):
            collection=PolyCollection(tri,array=values,cmap=cmap,edgecolors='none',rasterized=True)
            axs[row,col].add_collection(collection);axs[row,col].set(xlim=(-3.4,3.4),ylim=(1.45,5.8),xlabel='x (mm)',ylabel='z (mm)',title=label_case+' — '+label)
            axs[row,col].set_aspect('equal');axs[row,col].plot([-3,-2],[1.55,1.55],color='black',lw=3);axs[row,col].text(-2.5,1.7,'1 mm',ha='center',fontsize=8)
            fig.colorbar(collection,ax=axs[row,col],shrink=.8)
        np.savez_compressed(out/(case.name+'_section.npz'),xyz_m=section['xyz'],source_tetra=section['cells'],barycentric=section['barycentric'],
                            temperature_vertices_k=ts,potential_vertices_v=ps,current_A_m2=J[section['cells']])
        provenance[case.name]={'derived_sha256':sha(case/'derived.vtu'),'raw_field_sha256':json.loads((case/'metrics.json').read_text())['vtu_sha256']}
        # Actual tetrahedron body skins, excluding the header/pins from this zoom.
        f3=plt.figure(figsize=(10,7));ax=f3.add_subplot(projection='3d',computed_zorder=False);norm=Normalize(vmin=float(t.min()),vmax=float(t.max()));cm=plt.get_cmap('viridis')
        meta=json.loads((mesh/'manifest.json').read_text());by={v['id']:v for v in meta['bodies']}
        for bid in sorted(np.unique(b),key=lambda bid:by[bid]['material'] in ('Cu','P','N')):
            if bid==300 or 400<=bid<600:continue
            cc=c[b==bid];f=cc[:,[[1,2,3],[0,3,2],[0,1,3],[0,2,1]]].reshape(-1,3);f,count=np.unique(np.sort(f,axis=1),axis=0,return_counts=True);f=f[count==1]
            alumina=by[bid]['material']=='Alumina';colors=cm(norm(t[f].mean(1)));colors[:,3]=.15 if alumina else 1.
            ax.add_collection3d(Poly3DCollection(p[f]*1000,facecolors=colors,edgecolor='none',zorder=2 if alumina else 3,rasterized=True))
        ax.set(xlim=(-3.4,3.4),ylim=(-3.4,3.4),zlim=(1.45,5.8),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)')
        ax.set_box_aspect((6.8,6.8,4.35));ax.set_proj_type('ortho');ax.view_init(elev=27,azim=-65)
        ax.plot([-3,-2],[-3,-3],[1.55,1.55],color='black',lw=3,zorder=5);ax.text(-2.5,-3,1.8,'1 mm',zorder=6)
        ax.set_title('Actual solved solid temperature — '+label_case+'\nStack zoom; translucent alumina. Header/pins outside this view. No enclosure.',fontsize=11)
        f3.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cm),ax=ax,shrink=.65,label='Temperature (K)');f3.tight_layout();f3.savefig(out/(case.name+'_actual_3D_temperature.png'),dpi=300);plt.close(f3)
    fig.suptitle('Actual y=0.15 mm tetrahedron sections through all three leg stages; gaps preserved',fontsize=12)
    fig.tight_layout();fig.savefig(out/'actual_solved_sections.png',dpi=300);plt.close(fig)
    write(out/'provenance.json',{'source_sha256':sha(Path(__file__)),'mesh_sha256':sha(mesh/'mesh.npz'),'cases':provenance,
        'scope':'actual P1 plane intersections and solved tetrahedron skins; solid-only, no geometric or thermal field imputed in voids'})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mesh',type=Path,required=True);parser.add_argument('--cases',type=Path,nargs='+',required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();render(args.mesh.resolve(),[p.resolve() for p in args.cases],args.out.resolve())
