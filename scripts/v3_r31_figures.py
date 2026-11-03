"""Actual saved local meshes and measured comparisons, with failures visible."""
from pathlib import Path
import hashlib
import json
import gmsh
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r31_local_mesh_20261103'


def load(path):
    return json.loads(path.read_text())


def mesh_face(path, face):
    gmsh.clear()
    gmsh.open(str(path))
    ids, xyz, _ = gmsh.model.mesh.getNodes()
    ids = np.asarray(ids, np.int64)
    xyz = np.asarray(xyz).reshape(-1, 3)
    lookup = np.full(int(ids.max())+1, -1, np.int64)
    lookup[ids] = np.arange(len(ids))
    types, _, arrays = gmsh.model.mesh.getElements(2, face)
    assert list(types) == [2]
    raw = np.asarray(arrays[0], np.int64).reshape(-1, 3)
    used, inverse = np.unique(raw, return_inverse=True)
    return xyz[lookup[used]], inverse.reshape(-1, 3)


def main():
    out = DATA/'figures'
    out.mkdir(exist_ok=False)
    summary = load(DATA/'summary.json')
    inv = load(DATA/'inventory.json')
    order = ['A_callback_all__leads_jackets', 'B_native_all__leads_jackets',
             'B_native_selective__leads_jackets', 'A_callback_all__detector_bonds',
             'B_native_all__detector_bonds', 'B_native_selective__detector_bonds',
             'C_directional__detector_bonds', 'C_directional_corrected__detector_bonds',
             'A_callback_all__pin_planes_contacts', 'B_native_all__pin_planes_contacts',
             'B_native_selective__pin_planes_contacts', 'C_directional__pin_planes_contacts']
    labels = ['Leads — A callback', 'Leads — B native/all', 'Leads — B native/selective',
              'Bonds — A timeout', 'Bonds — B native/all FAIL', 'Bonds — B selective FAIL',
              'Bonds — C original STOP', 'Bonds — C corrected PASS',
              'Pin/planes — A', 'Pin/planes — B all', 'Pin/planes — B selective', 'Pin/planes — C']
    fig, axes = plt.subplots(1, 3, figsize=(14, 7.5), sharey=True)
    for i, key in enumerate(order):
        q = summary['cases'][key]
        color = '#386b8c' if q['worker_status'].startswith('PASS') else '#b44c4b'
        axes[0].barh(i, q['wall_seconds'], color=color, alpha=.85)
        axes[0].text(q['wall_seconds']*1.08, i, '>180' if q['timeout'] else f"{q['wall_seconds']:.2f}", va='center', fontsize=8)
        if q.get('triangles'):
            axes[1].barh(i, q['triangles'], color=color, alpha=.85)
            axes[1].text(q['triangles']*1.05, i, f"{q['triangles']:,}", va='center', fontsize=8)
            axes[2].barh(i, q['max_area_error']*100, color=color, alpha=.85)
        else:
            axes[1].text(.03, i, 'NOT AVAILABLE', transform=axes[1].get_yaxis_transform(), va='center', fontsize=8)
            axes[2].text(.03, i, 'NOT AVAILABLE', transform=axes[2].get_yaxis_transform(), va='center', fontsize=8)
    axes[0].set_yticks(range(len(order)), labels)
    axes[0].invert_yaxis()
    axes[0].set(xscale='log', xlim=(.7, 600), xlabel='End-to-end worker seconds (log)')
    axes[1].set(xscale='log', xlim=(3000, 4e6), xlabel='Actual surface triangles (log)')
    axes[2].set(xlim=(0, 4.6), xlabel='Worst native-face area error (%)')
    axes[2].axvline(1, color='black', ls='--', lw=1)
    for ax in axes:
        ax.grid(axis='x', alpha=.2)
    fig.suptitle('R3.1 actual local runs — blue PASS, red FAIL / STOP; no global estimate')
    fig.text(.5, .015, 'One run per strategy/fixture; one registered correction. A timeout is censored. No mesh or area inferred for unfinished attempts.',
             ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .05, 1, .95))
    fig.savefig(out/'measured_cost_accuracy.png', dpi=180)
    plt.close(fig)
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.option.setString('Geometry.OCCTargetUnit', 'MM')
    try:
        fig, axes = plt.subplots(2, 1, figsize=(11, 6.8), sharex=True, sharey=True)
        face = 2387
        source = inv['faces'][str(face)]
        lo, hi = np.asarray(source['parameter_bounds'])
        radius = 1/max(abs(k) for pair in source['principal_curvatures_per_mm'] for k in pair)
        mesh_sources = []
        for ax, case, label in zip(axes,
            ['B_native_all__detector_bonds', 'C_directional_corrected__detector_bonds'],
            ['Native isotropic mesh (straight face passes; full fixture FAILS at elbows)',
             'Source-boundary directional mesh (all14 faces PASS)']):
            path = DATA/'cases'/case/'worker/local_surface.msh'
            points, triangles = mesh_face(path, face)
            gmsh.clear()
            gmsh.model.occ.importShapes(str(ROOT/'data/v3_analysis_r3_20261103/geometry_restored/R3_conformal_mm.brep'))
            gmsh.model.occ.synchronize()
            uv = np.asarray(gmsh.model.getParametrization(2, face, points.ravel())).reshape(-1, 2)
            xy = np.c_[uv[:, 1]-lo[1], (uv[:, 0]-lo[0])*radius*1000]
            v = xy[triangles]
            center = (hi[1]-lo[1])/2
            # Exclude seam-spanning UV triangles; crop is explicit, not remeshed.
            keep = (np.ptp(v[:, :, 1], axis=1) < radius*1000*np.pi) & (abs(v[:, :, 0].mean(axis=1)-center)<.16)
            v = v[keep]
            segments = np.concatenate((v[:, [0, 1]], v[:, [1, 2]], v[:, [2, 0]]))
            ax.add_collection(LineCollection(segments, colors='#284d67', linewidths=.3))
            ax.set(xlim=(center-.125, center+.125), ylim=(10, 45), ylabel='Circumferential arc (µm)', title=label)
            ax.grid(alpha=.15)
            mesh_sources.append(dict(case=case, face=face, mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                     display='Native source UV unwrapping of actual vertex/triangle connectivity; cropped'))
        axes[-1].set_xlabel('Axial distance on actual5.0023mm straight face (mm)')
        fig.suptitle('Actual9µm-radius bond mesh, same0.25mm axial window; no field or smoothing')
        fig.tight_layout(rect=(0, 0, 1, .94))
        fig.savefig(out/'actual_bond_mesh_detail.png', dpi=200)
        plt.close(fig)
    finally:
        gmsh.finalize()
    (out/'provenance.json').write_text(json.dumps(dict(
        summary_sha256=hashlib.sha256((DATA/'summary.json').read_bytes()).hexdigest(),
        source_registry_sha256=hashlib.sha256((DATA/'inventory.json').read_bytes()).hexdigest(),
        actual_mesh_sources=mesh_sources, no_mesh_generation=True, no_PDE=True,
        failures_visible=True, source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2)+'\n')


if __name__ == '__main__':
    main()
