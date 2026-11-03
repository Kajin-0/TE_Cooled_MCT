"""Render actual analytic R3 CAD boundaries; deliberately not an analysis mesh."""
from pathlib import Path
import argparse
import numpy as np
import gmsh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scripts.v3_analysis_r3_geometry import read, save, sha


def draw(brep, registry, out):
    if out.exists():
        raise ValueError('Preserve CAD display')
    out.mkdir(parents=True)
    r = read(registry)
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.option.setString('Geometry.OCCTargetUnit', 'MM')
    try:
        gmsh.model.occ.importShapes(str(brep))
        gmsh.model.occ.synchronize()
        fig = plt.figure(figsize=(12, 5.8))
        displayed = {}
        for col, lead in enumerate((1, 9)):
            ax = fig.add_subplot(1, 2, col+1, projection='3d')
            copper, poly = 'TEC_lead'+str(lead), 'lead'+str(lead)+'_insulation'
            points = []
            shown = []
            for key, q in r['face_registry'].items():
                owners = set(q['owners'])
                if owners not in ({copper, 'CAVITY_GAS'}, {poly, 'CAVITY_GAS'}):
                    continue
                f = int(key)
                if gmsh.model.getType(2, f) not in ('Cylinder', 'Torus'):
                    continue  # No fictitious rectangular fill of annular ends.
                lo, hi = gmsh.model.getParametrizationBounds(2, f)
                uu = np.linspace(lo[0], hi[0], 49)
                vv = np.linspace(lo[1], hi[1], 25)
                uv = np.stack(np.meshgrid(uu, vv, indexing='ij'), axis=-1)
                p = np.asarray(gmsh.model.getValue(2, f, uv.ravel())).reshape(49, 25, 3)
                a, b, c, d = p[:-1, :-1], p[1:, :-1], p[1:, 1:], p[:-1, 1:]
                facets = np.stack((a, b, c, d), axis=-2).reshape(-1, 4, 3)
                color = '#39966c' if poly in owners else '#be6b26'
                ax.add_collection3d(Poly3DCollection(facets, facecolor=color,
                                    edgecolor='none', alpha=.95))
                points.append(p.reshape(-1, 3))
                shown.append(f)
            xyz = np.concatenate(points)
            lo, hi = xyz.min(axis=0), xyz.max(axis=0)
            center, span = (lo+hi)/2, max(hi-lo)
            ax.set(xlim=(center[0]-span/2, center[0]+span/2),
                   ylim=(center[1]-span/2, center[1]+span/2),
                   zlim=(center[2]-span/2, center[2]+span/2),
                   xlabel='x (mm)', ylabel='y (mm)', zlabel='z (mm)',
                   title=f'Lead {lead}: exact curved CAD boundaries')
            ax.set_box_aspect((1, 1, 1))
            ax.view_init(23, -55)
            displayed[str(lead)] = shown
        fig.suptitle('Source jacket restoration / exposed Cu — CAD display, not a qualified mesh')
        fig.legend(handles=[Patch(color='#be6b26', label='Bare Cu / gas'),
                            Patch(color='#39966c', label='Polymer / gas')],
                   ncol=2, loc='lower center', frameon=False)
        fig.subplots_adjust(left=.03, right=.97, top=.86, bottom=.15, wspace=.08)
        fig.savefig(out/'actual_CAD_jacket_regions.png', dpi=200)
        plt.close(fig)
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
        for ax, lead in zip(axes, (1, 9)):
            regions = [q for q in r['shell_regions'] if q['physical_Cu'] == 'TEC_lead'+str(lead)]
            covered = [q['exact_covered_mm2'] for q in regions]
            bare = [q['exact_bare_mm2'] for q in regions]
            ax.bar(range(5), covered, label='Cu / source polymer', color='#39966c')
            ax.bar(range(5), bare, bottom=covered, label='Bare Cu / gas complement', color='#be6b26')
            ax.set_xticks(range(5), [str(q['derived_lead_gas_face']) for q in regions])
            ax.set(xlabel='Original R2 native face identity', title=f'Lead {lead}')
            ax.grid(axis='y', alpha=.2)
        axes[0].set_ylim(0, 1.15*max(q['exact_covered_mm2']+q['exact_bare_mm2'] for q in r['shell_regions']))
        axes[0].set_ylabel('Exact analytic CAD area (mm²)')
        axes[1].legend(fontsize=8)
        fig.suptitle('Six full and four partial jacket regions; no whole-face averaging')
        fig.tight_layout(rect=(0, 0, 1, .92))
        fig.savefig(out/'exact_jacket_area_partition.png', dpi=200)
        plt.close(fig)
        save(out/'provenance.json', dict(BREP_sha256=sha(brep), registry_sha256=sha(registry),
             native_faces_displayed=displayed, evaluation='Exact getValue on native Cylinder/Torus UV domains',
             omitted='Annular end planes; buried Cu/polymer interfaces',
             no_analysis_mesh=True, no_PDE=True))
    finally:
        gmsh.finalize()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('brep', 'registry', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    draw(a.brep, a.registry, a.out)
