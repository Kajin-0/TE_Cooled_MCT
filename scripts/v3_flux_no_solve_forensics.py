"""Read-only saved-field numerics: per-domain loss, interface losses, mixed minimum.

Never calls operator solvers, creates meshes, repairs original producer, or
represents the overwritten direct-mixed flux as observed data.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


BASE = Path("data/v3_conservative_flux_20261102")
DEFS = Path("data/v3_interconnect_et_20261102/operator_definitions.json")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyse():
    d = BASE / "geometry/L1"
    f = BASE / "geometry/L1_field"
    sf = f / "fields.npz"
    mf = d / "mesh.npz"
    saved = np.load(sf)
    mesh = np.load(mf)
    registry = json.loads((d / "registry.json").read_text())
    defs = json.loads(DEFS.read_text())
    if ("mixed_q" in saved.files or "recovered_q" in saved.files or
        "lead9_q" not in saved.files or "lead9_cell_V" not in saved.files):
        raise ValueError("expected exact frozen mislabelled experiment; no guesses")
    p, t, regions = mesh["points"], mesh["cells"], mesh["regions"]
    xyz = p[t]
    edges = xyz[:, 1:] - xyz[:, :1]
    vol = abs(np.einsum("ei,ei->e", edges[:, 0], np.cross(edges[:, 1], edges[:, 2]))) / 6
    if not (vol > 0).all():
        raise ValueError("non-positive tetrahedron")
    c = xyz.mean(axis=1)
    q = saved["lead9_q"]  # RECOVERED only.
    localq = q[saved["cell_faces"]] * saved["cell_signs"]
    # Source-free RT0: cell divergence is the sum of its oriented face currents.
    divergence = localq.sum(axis=1)
    Jcenter = np.einsum("ei,eia->ea", localq, c[:, None, :] - xyz) / (3 * vol[:, None])
    refJ = saved["lead9_J"]
    reconstruction = float(np.linalg.norm(Jcenter - refJ, axis=1).max() /
                           max(np.linalg.norm(refJ, axis=1).max(), 1e-30))
    constants, scenario = defs["material_constants"], defs["scenarios"]["NOM"]
    rho = []
    groups = registry["groups"]
    for g in groups:
        material = g["material"]
        if material in ("laminate", "pin_laminate"):
            layers = defs["film_stack_m" if material == "laminate" else "pin_stack_m"]
            thickness = sum(v for _, v in layers)
            resistance = [constants[mat][0] * (scenario["film_factor"] if mat == "Cu" else 1)
                          for mat, _ in layers]
            parallel = sum(h / r for (_, h), r in zip(layers, resistance)) / thickness
            normal = thickness / (sum(h * r for (_, h), r in zip(layers, resistance)) +
                                  (len(layers) - 1) * scenario["plated_re"])
            rho.append(np.diag([1 / parallel, 1 / parallel, 1 / normal]))
        else:
            rho.append(np.eye(3) * constants[material][0])
    rho = np.asarray(rho)[regions]
    # Independently evaluate RT0 J at degree-2 quadrature; not a new field solve.
    bary = np.full((4, 4), 0.1381966011250105)
    np.fill_diagonal(bary, 0.5854101966249685)
    pos = np.einsum("qi,eia->eqa", bary, xyz)
    J = Jcenter[:, None, :] + (pos - c[:, None, :]) * divergence[:, None, None] / (3 * vol[:, None, None])
    loss_cell = vol * np.einsum("eqa,eab,eqb->eq", J, rho, J).mean(axis=1)
    loss_domains = {}
    for i, g in enumerate(groups):
        z = regions == i
        loss_domains[g["name"]] = dict(bulk_W=float(loss_cell[z].sum()),
                                       cell_count=int(z.sum()),
                                       volume_m3=float(vol[z].sum()))
    face_map = {tuple(int(x) for x in row): i for i, row in enumerate(saved["face_nodes"])}
    tags = {int(row["tag"]): row for row in registry["faces"]}
    contacts = {}
    for tr, tag in zip(mesh["triangles"], mesh["faceids"]):
        record = tags[int(tag)]
        if len(record["owners"]) != 2:
            continue
        fidx = face_map[tuple(sorted(int(x) for x in tr))]
        tri = p[tr]
        area = float(np.linalg.norm(np.cross(tri[1] - tri[0], tri[2] - tri[0])) / 2)
        key = " ↔ ".join(groups[int(j)]["name"] for j in record["owners"])
        item = contacts.setdefault(key, {"loss_W": 0., "area_m2": 0., "face_count": 0})
        item["loss_W"] += scenario["re"] * q[fidx] ** 2 / area
        item["area_m2"] += area
        item["face_count"] += 1
    mixed = saved["lead9_cell_V"]  # Survives overwritten mixed FLUX, no mixed solution reconstruction.
    minidx = int(np.argmin(mixed))
    neighbour_faces = saved["cell_faces"][minidx]
    # Inspect material interfaces and surface proximity from already stored faces.
    face_owners = {}
    for idx, faces in enumerate(saved["cell_faces"]):
        if idx == minidx:
            continue
        for ff in faces:
            if int(ff) in neighbour_faces:
                face_owners.setdefault(int(ff), []).append(idx)
    neighbour_ids = sorted(set(n for xs in face_owners.values() for n in xs))
    # KD-tree of external physical-face centroids (not an exact point-to-surface distance).
    external_tris = []
    for tri, tag in zip(mesh["triangles"], mesh["faceids"]):
        if len(tags[int(tag)]["owners"]) == 1:
            external_tris.append(tri)
    boundary_distance = None
    if external_tris:
        centroids = p[np.asarray(external_tris, dtype=int)].mean(axis=1)
        dist, near = cKDTree(centroids).query(c[minidx])
        boundary_distance = dict(nearest_surface_triangle_centroid_distance_m=float(dist),
                                 nearest_surface_centroid_m=centroids[int(near)].tolist(),
                                 note="Centroid-distance proxy, NOT shortest true geometric distance")
    tri_xyz = np.stack([xyz[:, [1, 2, 3]], xyz[:, [0, 2, 3]], xyz[:, [0, 1, 3]], xyz[:, [0, 1, 2]]], axis=1)
    area = np.linalg.norm(np.cross(tri_xyz[:, :, 1] - tri_xyz[:, :, 0],
                                   tri_xyz[:, :, 2] - tri_xyz[:, :, 0]), axis=2) / 2
    inradius = 3 * vol / area.sum(axis=1)
    pairs = np.stack(np.triu_indices(4, 1), axis=1)
    lengths = np.stack([np.linalg.norm(xyz[:, j] - xyz[:, i], axis=1) for i,j in pairs], axis=1)
    aspect = lengths.max(axis=1) / inradius
    input_A = json.loads((f / "alternative.json").read_text())["lead9"]["input_A"]
    bulk = float(loss_cell.sum())
    inter = float(sum(x["loss_W"] for x in contacts.values()))
    diff = bulk + inter - input_A
    out = {
        "scope": "NO SOLVE: retained recovered RT0 flux plus separately surviving mixed cell means",
        "observed_UTC": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_sha256": {str(x): digest(x) for x in [mf, sf, d / "registry.json", DEFS,
            f / "alternative.json", BASE / "registration.json"]},
        "actual_methods_retained": {"raw_P1": True, "recovered_RT0_flux_as_lead9": True,
                                    "direct_mixed_RT0_flux": False, "mixed_cell_potential_only": True},
        "mixed_voltage_min": {
            "V": float(mixed[minidx]), "tetra_index": minidx,
            "region": groups[int(regions[minidx])]["name"],
            "centroid_m": c[minidx].tolist(), "volume_m3": float(vol[minidx]),
            "aspect_maxedge_over_inradius": float(aspect[minidx]),
            "adjacent_tetra_indices": neighbour_ids,
            "adjacent_material_regions": sorted(set(groups[int(regions[n])]["name"] for n in neighbour_ids)),
            "nearest_external_triangle_centroid": boundary_distance,
            "cells_below_registered_floor": int((mixed < -1e-8).sum()),
            "cells_above_registered_ceiling": int((mixed > 1 + 1e-8).sum())
        },
        "quality_aspect": {
            "all_tets_maxedge_over_inradius_p50": float(np.quantile(aspect, 0.5)),
            "p99": float(np.quantile(aspect, 0.99)),
            "max": float(aspect.max()),
            "mixed_min_tet_percentile": float((aspect <= aspect[minidx]).mean())
        },
        "recovered_loss": {
            "input_I_at_1V_A": float(input_A),
            "bulk_W": bulk, "contact_W": inter, "sum_W": bulk + inter,
            "diss_minus_IV_W": diff, "relative_discrepancy": diff / input_A,
            "by_material_domain": loss_domains, "by_finite_contact": contacts,
            "recovered_J_centroid_reconstruction_relative": reconstruction,
            "comparison_warning": "Recovered field constrained to P1 current. Nonzero recovered dissipation minus P1 IV is NOT alone proof of incorrect mixed solution or constitutive law."
        },
        "limitations": [
            "No new PDE or mesh; all outputs are derivatives of saved incomplete experiment",
            "Missing mixed flux cannot be recovered as an observed method field",
            "No original control fields were archived; cannot independently recompute control L2 norms",
            "Cell-mean mixed voltage need not obey CG maximum principle without additional monotonicity theory",
            "No thermal-port distribution, physical device resistance, current rating, or performance"
        ]
    }
    assert abs(out["recovered_loss"]["relative_discrepancy"] - 0.0076915363179273) < 1e-10
    assert abs(out["mixed_voltage_min"]["V"] + 2.65228085795e-5) < 1e-12
    assert reconstruction < 1e-8
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = analyse()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as out:
        json.dump(value, out, indent=2)
        out.write("\n")
    print("NO-SOLVE forensics completed:", args.out)
    print("worst mixed cell", value["mixed_voltage_min"])
    print("loss breakdown", {k: value["recovered_loss"][k] for k in
                             ["input_I_at_1V_A", "bulk_W", "contact_W", "diss_minus_IV_W",
                              "relative_discrepancy"]})


if __name__ == "__main__":
    main()
