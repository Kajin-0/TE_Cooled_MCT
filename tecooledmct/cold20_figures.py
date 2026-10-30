"""Measured solver phase costs and actual independently recovered bath fields."""
import argparse,json,re
from pathlib import Path
import numpy as np
from .geometry_rebaseline import sha,write
from .cold20_analysis import RAW,read


def render(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import Normalize
    out.mkdir(parents=True,exist_ok=False)
    def save(fig,name):fig.savefig(out/(name+'.png'),dpi=350,bbox_inches='tight');fig.savefig(out/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
    coarse=read(RAW/'bench_direct/timings.json')['iterations'];fine=read(RAW/'loaded20_direct_P1/timings.json')['iterations']
    labels=['Cold30 Picard','Cold20 Picard','Cold20 Newton'];sets=[coarse,fine[:2],fine[2:]]
    a=[np.mean([r['assembly_cpu_s'] for r in rows]) for rows in sets];l=[np.mean([r['linear_cpu_s'] for r in rows]) for rows in sets]
    fig,axs=plt.subplots(1,2,figsize=(11,4.5),layout='constrained');x=np.arange(3)
    axs[0].bar(x,a,label='Assembly');axs[0].bar(x,l,bottom=a,label='Linear solve');axs[0].set_xticks(x,labels,rotation=15);axs[0].set(ylabel='Mean measured CPU seconds / iteration',title='Pinned runtime; unchanged physical assembly');axs[0].legend()
    text=(RAW/'lu_profile30/solver.log').read_text();sym=[float(v) for v in re.findall(r'COLD20_UMF symbolic wall=[^ ]+ cpu=([^ ]+)',text)];num=[float(v) for v in re.findall(r'COLD20_UMF numeric wall=[^ ]+ cpu=([^ ]+)',text)]
    axs[1].bar(['Symbolic','Numeric'],[np.mean(sym),np.mean(num)],color=['tab:gray','tab:red']);axs[1].set(ylabel='Mean measured CPU seconds / factorization',title='Cold30 pass-through UMFPACK profile')
    save(fig,'measured_solver_phases')
    provenance={'source_sha256':sha(Path(__file__)),'timings_sha256':{n:sha(RAW/n/'timings.json') for n in ('bench_direct','loaded20_direct_P1')},'LU_log_sha256':sha(RAW/'lu_profile30/solver.log')}
    if (RAW/'bath_refined/audit.json').exists():
        registry=read(RAW/'configuration_registry.json');parent=Path(registry['primary_case']);configs=[('Cold20 parent',RAW.parent/'cold-convergence/mesh20',RAW/'bath_parent'),('Bath volume refined',RAW/'bath_mesh',RAW/'bath_refined')]
        arrays=[];lo=0.;hi=0.
        for label,mesh,diag in configs:
            p=np.load(mesh/'mesh.npz')['points'];d=np.load(diag/'face_data.npz');values=d['outward_density_W_m2'];tri=p[d['faces']][:,:,:2]*1e3
            arrays.append((label,tri,values,read(diag/'audit.json')));lo=min(lo,float(values.min()));hi=max(hi,float(values.max()))
        fig,axs=plt.subplots(2,1,figsize=(11,8.5),layout='constrained');norm=Normalize(lo,hi)
        for ax,(label,tri,values,audit) in zip(axs,arrays):
            coll=PolyCollection(tri,array=values,cmap='viridis',norm=norm,edgecolors='black',linewidths=.05,rasterized=True);ax.add_collection(coll)
            low=tri.min((0,1));high=tri.max((0,1));pad=(high-low)*.03
            ax.set(xlim=(low[0]-pad[0],high[0]+pad[0]),ylim=(low[1]-pad[1],high[1]+pad[1]),xlabel='x (mm)',ylabel='y (mm)',title=f"{label}: independent raw bath error {audit['raw_relative_error']*100:+.4f}%");ax.set_aspect('equal')
        fig.colorbar(coll,ax=axs,label='Actual one-sided outward Fourier flux (W/m²)',shrink=.8)
        fig.suptitle('True Kovar underside triangles; source-traced two-ear geometry and holes preserved\nCold tetrahedra exactly unchanged; no weak/recovered-flux substitution',fontsize=11)
        save(fig,'actual_bath_fields')
        provenance['bath_audit_sha256']={str(diag):sha(diag/'audit.json') for _,_,diag in configs}
    write(out/'provenance.json',provenance);print('Actual timing/bath figures generated',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();render(a.out.resolve())
