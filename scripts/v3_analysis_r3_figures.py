"""Actual saved-mesh jacket views and measured area-error plots, never fields."""
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


def figures(mesh, registry, gate, out):
    if out.exists():
        raise ValueError('Preserve actual-mesh visual evidence')
    out.mkdir(parents=True)
    r, g = read(registry), read(gate)
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    try:
        gmsh.open(str(mesh))
        ids, xyz, _ = gmsh.model.mesh.getNodes()
        p = np.asarray(xyz).reshape(-1, 3)
        lookup = np.full(int(max(ids))+1, -1, np.int64)
        lookup[np.asarray(ids, np.int64)] = np.arange(len(ids))
        fig = plt.figure(figsize=(12, 5.8))
        counts = {}
        for pos, lead in enumerate((1, 9)):
            ax = fig.add_subplot(1, 2, pos+1, projection='3d')
            wire, poly = 'TEC_lead'+str(lead), 'lead'+str(lead)+'_insulation'
            local = []
            count = 0
            for key, q in r['face_registry'].items():
                owners = set(q['owners'])
                if not ({wire, poly} & owners):
                    continue
                if owners == {wire, poly}:
                    # Hide buried inner interface, retain the actual external
                    # jacket and exposed Cu triangulations in this view.
                    continue
                kinds, _, arrays = gmsh.model.mesh.getElements(2, int(key))
                assert list(kinds) == [2]
                tri = lookup[np.asarray(arrays[0], np.int64).reshape(-1, 3)]
                v = p[tri]
                local.append(v.reshape(-1, 3))
                count += len(v)
                color = '#39966c' if poly in owners else '#be6b26'
                coll = Poly3DCollection(v, facecolor=color, edgecolor='none', alpha=.85)
                ax.add_collection3d(coll)
            points = np.concatenate(local)
            lo, hi = points.min(axis=0), points.max(axis=0)
            span = max(hi-lo)
            center = (hi+lo)/2
            ax.set_xlim(center[0]-span/2, center[0]+span/2)
            ax.set_ylim(center[1]-span/2, center[1]+span/2)
            ax.set_zlim(center[2]-span/2, center[2]+span/2)
            ax.set_box_aspect((1, 1, 1))
            ax.view_init(22, -58)
            ax.set(xlabel='x (mm)', ylabel='y (mm)', zlabel='z (mm)',
                   title=f'Lead {lead}: actual Cu / 15 µm jacket mesh')
            counts[str(lead)] = count
        fig.legend(handles=[Patch(color='#be6b26', label='Exposed copper'),
                            Patch(color='#39966c', label='Explicit source polymer boundary')],
                   loc='lower center', ncol=2, frameon=False)
        fig.suptitle('R3 geometry-only surface candidate — not a solved field')
        fig.subplots_adjust(left=.03, right=.98, top=.86, bottom=.15, wspace=.08)
        fig.savefig(out/'actual_jacket_mesh.png', dpi=180)
        plt.close(fig)
        rows = list(g['rows'].values())
        errors = np.array([abs(q['relative_error'])*100 for q in rows])
        ntri = np.array([q['triangles'] for q in rows])
        fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
        axes[0].hist(np.maximum(errors, 1e-6), bins=np.geomspace(1e-6, max(2, errors.max()*1.05), 45))
        axes[0].set(xscale='log', xlabel='Absolute CAD area error (%)', ylabel='Native faces')
        axes[0].axvline(1, color='crimson', ls='--', label='Strict 1% gate')
        axes[0].legend(fontsize=8)
        order = np.argsort(errors)[-12:]
        axes[1].barh(range(len(order)), errors[order], color='#516b8a')
        axes[1].set_yticks(range(len(order)), [str(rows[i]['face']) for i in order])
        axes[1].axvline(1, color='crimson', ls='--')
        axes[1].set(xlabel='Absolute CAD area error (%)', ylabel='Native face identity')
        axes[2].bar(['Accepted R2\nreference', 'R3\ncandidate'],
                    [1416664/1e6, g['triangles']/1e6], color=['#9ca8b8', '#516b8a'])
        axes[2].set(ylabel='Surface triangles (million)')
        axes[2].set_title(f"{len(g['failed_faces'])}/{len(rows)} faces fail 1%")
        fig.suptitle('Measured mesh efficiency and geometric fidelity; no accuracy waiver')
        fig.tight_layout(rect=(0, 0, 1, .94))
        fig.savefig(out/'area_error_and_cost.png', dpi=180)
        plt.close(fig)
        save(out/'provenance.json', dict(mesh_sha256=sha(mesh), registry_sha256=sha(registry),
             gate_sha256=sha(gate), displayed_triangles=counts, decimation=False,
             no_PDE=True, status='Actual saved surface mesh; gate status '+g['status']))
    finally:
        gmsh.finalize()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for k in ('mesh', 'registry', 'gate', 'out'):
        p.add_argument('--'+k, type=Path, required=True)
    a = p.parse_args()
    figures(a.mesh, a.registry, a.gate, a.out)
