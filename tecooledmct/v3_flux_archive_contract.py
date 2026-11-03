"""Prospective, no-solve scientific-field archive validator, revision 3.

Operates on PRECOMPUTED bytes. Does not produce meshes, PDE solutions,
recover fields, or modify the frozen V3 historical archives.
Validation certifies format/lineage and independently recomputable analytic
norms, NOT physical accuracy or correctness of a solver.
"""
import hashlib
import io
import json
from pathlib import Path

import numpy as np

from . import v3_flux_infrastructure_v2 as writer

METHODS = ("p1", "recovered_rt0", "mixed_rt0")
UNITS = {
    "length": "m",
    "potential": "V",
    "current": "A",
    "current_density": "A/m^2",
    "conductivity": "S/m",
    "resistivity": "ohm*m",
    "quadrature_weight": "m^3",
    "loss": "W",
}
NPZ_KEYS = {
    "mesh": {"points_m", "cells", "regions", "face_nodes", "cell_faces", "cell_face_signs"},
    "potential": {"values_V", "sample_points_m", "mesh_node_indices", "execution_id", "method_id"},
    "flux": {"J_A_m2", "sample_points_m", "sample_cells", "face_currents_A",
             "execution_id", "method_id"},
    "material_map": {"region_ids", "conductivity_S_m", "resistivity_ohm_m"},
    "residual": {"cell_balance_A", "execution_id", "method_id"},
    "analytical_reference": {"available", "potential_V", "J_A_m2",
                             "potential_weights", "flux_weights_m3"},
}


def _require(ok, reason):
    if not ok:
        raise ValueError(reason)


def _arrays(blob, kind):
    try:
        with np.load(io.BytesIO(blob), allow_pickle=False) as opened:
            _require(set(opened.files) == NPZ_KEYS[kind], f"{kind}: invalid array keys")
            arrays = {k: opened[k] for k in opened.files}
    except (ValueError, OSError, EOFError, KeyError) as exc:
        raise ValueError(f"{kind}: invalid NPZ or unsafe array") from exc
    for key, arr in arrays.items():
        _require(arr.dtype.kind != "O", f"{kind}.{key}: object arrays prohibited")
    return arrays


def _number(arr, shape, label, integer=False):
    _require(arr.shape == shape, f"{label}: wrong shape {arr.shape} != {shape}")
    _require(arr.dtype.kind in ("i", "u") if integer else arr.dtype == np.dtype("float64"),
             f"{label}: wrong dtype {arr.dtype}")
    _require(bool(np.all(np.isfinite(arr))), f"{label}: nonfinite values")


def _identity(value, expected, label):
    _require(value.shape == () and value.dtype.kind == "U" and str(value.item()) == expected,
             f"{label}: identity mismatch")


def _error(values, reference, weights):
    _number(weights, (len(values),), "reference weights")
    _require(bool((weights > 0).all()), "reference weights must be positive")
    _require(len(values) > 0, "empty analytic reference")
    diff = values - reference
    num = float(np.sum(weights[:, None] * diff**2)) if values.ndim == 2 else float(np.sum(weights * diff**2))
    den = float(np.sum(weights[:, None] * reference**2)) if reference.ndim == 2 else float(np.sum(weights * reference**2))
    return float(np.sqrt(num / den)) if den > 0 else float(np.sqrt(num / float(weights.sum())))


def validate_scientific_payloads(manifest, payloads):
    """Validate all three methods before ANY output directory is created.

    Requires identical exact mesh bytes, independently reported reference norms,
    SI units, positive elements and conductivity, correct DOF/field provenance.
    """
    writer.validate_manifest(manifest)
    _require(set(payloads) == set(METHODS), "missing method payload")
    data = {}
    for method in METHODS:
        _require(set(payloads[method]) == writer.REQUIRED, "missing field payload")
        _require(all(isinstance(b, bytes) for b in payloads[method].values()), "payload must be bytes")
        blobs = payloads[method]
        record = {k: _arrays(blobs[k], k) for k in NPZ_KEYS}
        try:
            meta = json.loads(blobs["metadata"].decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ValueError("invalid JSON metadata") from exc
        _require(isinstance(meta, dict), "metadata not object")
        _require(meta.get("method") == method, "method metadata mismatch")
        _require(meta.get("units") == UNITS, "units incompatible with SI contract")
        _require(meta.get("kind") in ("analytic_control", "coupon"), "invalid experiment kind")
        _require(meta.get("run_id") and isinstance(meta["run_id"], str), "missing run identity")
        for key in ("source_sha256", "operator_sha256", "mesh_sha256"):
            v = meta.get(key)
            _require(isinstance(v, str) and len(v) == 64 and
                     all(c in "0123456789abcdef" for c in v), "invalid " + key)
        _require(meta["mesh_sha256"] == hashlib.sha256(blobs["mesh"]).hexdigest(),
                 "mesh checksum mismatch")
        for key in ("potential_execution_id", "flux_execution_id"):
            _require(isinstance(meta.get(key), str) and bool(meta[key]), "missing " + key)
        mesh = record["mesh"]
        points, cells, regions, faces = (mesh[k] for k in
                                           ("points_m", "cells", "regions", "face_nodes"))
        _number(points, (len(points), 3), "mesh points")
        _number(cells, (len(cells), 4), "mesh tetra", integer=True)
        _number(regions, (len(cells),), "mesh regions", integer=True)
        _number(faces, (len(faces), 3), "mesh faces", integer=True)
        _require(len(points) >= 4 and len(cells) > 0 and len(faces) >= 4, "empty mesh")
        _require(bool(np.all(cells < len(points)) and np.all(faces < len(points))),
                 "mesh node index out of bounds")
        _require(bool(np.all(cells >= 0) and np.all(faces >= 0)), "negative mesh node")
        _require(bool((regions >= 0).all()), "negative region index")
        _require(bool(np.all(np.sort(cells, axis=1)[:, 1:] != np.sort(cells, axis=1)[:, :-1])),
                 "duplicate tetra node")
        txyz = points[cells]
        vol = abs(np.linalg.det(txyz[:, 1:] - txyz[:, :1])) / 6
        _require(bool((vol > 0).all()), "degenerate mesh")
        _require(np.unique(np.sort(faces, axis=1), axis=0).shape[0] == len(faces),
                 "duplicate face geometry")
        cellfaces, cellsigns = mesh["cell_faces"], mesh["cell_face_signs"]
        _number(cellfaces, (len(cells), 4), "cell face indices", integer=True)
        _number(cellsigns, (len(cells), 4), "cell face outward signs")
        _require(bool(np.all((cellfaces >= 0) & (cellfaces < len(faces)))),
                 "invalid cell face index")
        _require(bool(np.all(np.abs(cellsigns) == 1)), "face signs not ±1")
        face_by_nodes = {tuple(sorted(row.tolist())): idx for idx, row in enumerate(faces)}
        incidence = np.zeros(len(faces), dtype=np.int64)
        sign_sum = np.zeros(len(faces), dtype=np.int64)
        for cell_idx, row in enumerate(cells):
            for local_idx in range(4):
                tri_nodes = np.delete(row, local_idx)
                actual = face_by_nodes.get(tuple(sorted(tri_nodes.tolist())))
                _require(actual is not None and int(cellfaces[cell_idx, local_idx]) == actual,
                         "cell to face incidence mismatch")
                oriented = points[faces[actual]]
                n = np.cross(oriented[1] - oriented[0], oriented[2] - oriented[0])
                opposite = points[row[local_idx]]
                face_center = oriented.mean(axis=0)
                direction = float(np.dot(n, opposite - face_center))
                _require(direction != 0, "degenerate tetra face orientation")
                expected = -1 if direction > 0 else 1
                _require(cellsigns[cell_idx, local_idx] == expected,
                         "cell face flux orientation mismatch")
                incidence[actual] += 1
                sign_sum[actual] += expected
        _require(bool(np.all((incidence >= 1) & (incidence <= 2))),
                 "missing or nonmanifold faces")
        _require(bool(np.all(sign_sum[incidence == 2] == 0)),
                 "shared faces not oppositely oriented")
        refbbox = np.asarray(meta.get("bbox_m"))
        _number(refbbox, (2, 3), "source expected bbox")
        _require(bool(np.allclose(np.vstack((points.min(axis=0), points.max(axis=0))),
                                     refbbox, rtol=0, atol=1e-10)),
                 "mesh/source SI bounding box inconsistent")
        materials = record["material_map"]
        mids = materials["region_ids"]
        _number(mids, (len(mids),), "material region ids", integer=True)
        _require(np.array_equal(mids, np.unique(regions)), "material region coverage mismatch")
        for prop in ("conductivity_S_m", "resistivity_ohm_m"):
            mat = materials[prop]
            _number(mat, (len(mids), 3, 3), prop)
            _require(bool((np.linalg.eigvalsh(mat) > 0).all()), prop + ": not positive definite")
            _require(bool(np.allclose(mat, mat.transpose(0, 2, 1), rtol=1e-10, atol=0)),
                     prop + ": not symmetric")
        _require(bool(np.allclose(materials["conductivity_S_m"] @ materials["resistivity_ohm_m"],
                                     np.eye(3), rtol=1e-8, atol=1e-8)),
                 "material conductivity/resistivity inconsistent")
        pot, flux, res = (record[x] for x in ("potential", "flux", "residual"))
        values = pot["values_V"]
        pxyz = pot["sample_points_m"]
        nodeindices = pot["mesh_node_indices"]
        _number(values, (len(values),), "potential V")
        _number(pxyz, (len(values), 3), "potential sample positions")
        _number(nodeindices, (len(nodeindices),), "potential node indices", integer=True)
        _identity(pot["execution_id"], meta["potential_execution_id"], "potential execution")
        _identity(pot["method_id"], method, "potential method")
        _identity(flux["execution_id"], meta["flux_execution_id"], "flux execution")
        _identity(flux["method_id"], method, "flux method")
        _identity(res["execution_id"], meta["flux_execution_id"], "residual execution")
        _identity(res["method_id"], method, "residual method")
        if method == "mixed_rt0":
            _require(len(values) == len(cells) and len(nodeindices) == 0,
                     "mixed potential DOFs must be cell means")
            _require(bool(np.allclose(pxyz, txyz.mean(axis=1), rtol=0, atol=1e-12)),
                     "mixed potentials not at cell centroids")
            _require(meta["potential_execution_id"] == meta["flux_execution_id"],
                     "direct mixed potential/flux not same execution")
        else:
            _require(len(nodeindices) == len(values) and len(nodeindices) >= len(points),
                     "CG trace DOF mapping incomplete")
            _require(bool((nodeindices >= 0).all() and (nodeindices < len(points)).all()),
                     "CG DOF mesh index invalid")
            _require(bool(np.allclose(pxyz, points[nodeindices], atol=1e-12, rtol=0)),
                     "CG potential DOF positions inconsistent")
            if method == "p1":
                _require(meta["potential_execution_id"] == meta["flux_execution_id"],
                         "P1 potential/flux from distinct executions")
        J, fxyz, cellid, facecurr = (flux[k] for k in
                                    ("J_A_m2", "sample_points_m", "sample_cells", "face_currents_A"))
        _number(J, (len(J), 3), "flux J")
        _number(fxyz, (len(J), 3), "flux sample positions")
        _number(cellid, (len(J),), "flux sample cells", integer=True)
        _number(facecurr, (len(facecurr),), "face currents")
        _require(len(J) > 0 and bool((cellid >= 0).all() and (cellid < len(cells)).all()),
                 "flux sample geometry index invalid")
        owner_points = txyz[cellid]
        _require(bool(np.all(fxyz >= owner_points.min(axis=1) - 1e-12) and
                      np.all(fxyz <= owner_points.max(axis=1) + 1e-12)),
                 "flux samples outside assigned cells")
        _require(len(facecurr) == (0 if method == "p1" else len(faces)),
                 "RT0 face-current DOF mismatch")
        if method != "p1":
            qlocal = facecurr[cellfaces] * cellsigns
            implied_balance = qlocal.sum(axis=1)
            _require(np.allclose(implied_balance, res["cell_balance_A"],
                                    rtol=1e-8, atol=1e-12),
                     "RT0 residual inconsistent with archived face currents")
            # Independently reconstruct the RT0 vector at every archived point.
            xlocal = txyz[cellid]
            qsample = qlocal[cellid]
            vlocal = vol[cellid]
            reconstructed = np.einsum('si,sia->sa', qsample,
                                      fxyz[:, None, :] - xlocal) / (3 * vlocal[:, None])
            tolerance = 1e-8 * max(1.0, float(np.max(np.abs(reconstructed))))
            _require(bool(np.max(np.abs(reconstructed - J)) <= tolerance),
                     "RT0 flux samples inconsistent with face-current DOFs")
        balance = res["cell_balance_A"]
        _number(balance, (len(cells),), "cell conservation residual")
        ref = record["analytical_reference"]
        available = ref["available"]
        _require(available.shape == () and available.dtype == np.dtype("bool"),
                 "invalid analytical-reference availability")
        _require(bool(available) == (meta["kind"] == "analytic_control"),
                 "analytic data availability disagrees with experiment kind")
        if bool(available):
            _number(ref["potential_V"], values.shape, "reference potential")
            _number(ref["J_A_m2"], J.shape, "reference flux")
            error_v = _error(values, ref["potential_V"], ref["potential_weights"])
            error_j = _error(J, ref["J_A_m2"], ref["flux_weights_m3"])
            e = meta.get("reported_analytic_errors")
            _require(isinstance(e, dict) and set(e) == {"potential_l2", "flux_l2"},
                     "missing independently reproducible analytical error")
            _require(np.isclose(e["potential_l2"], error_v, rtol=1e-8, atol=1e-12) and
                     np.isclose(e["flux_l2"], error_j, rtol=1e-8, atol=1e-12),
                     "analytical L2 errors inconsistent with archived fields")
        else:
            _require(all(ref[k].size == 0 for k in
                         ("potential_V", "J_A_m2", "potential_weights", "flux_weights_m3")),
                     "coupon must not include fabricated analytic reference")
            _require(meta.get("reported_analytic_errors") is None,
                     "unavailable analytical accuracy cannot be claimed")
        data[method] = (record, meta, error_v if bool(available) else None,
                        error_j if bool(available) else None)
    _require(len({payloads[m]["mesh"] for m in METHODS}) == 1,
             "methods use different mesh bytes")
    _require(len({data[m][1]["run_id"] for m in METHODS}) == 1,
             "methods not from same experiment")
    _require(len({data[m][1]["source_sha256"] for m in METHODS}) == 1 and
             len({data[m][1]["operator_sha256"] for m in METHODS}) == 1,
             "methods have different frozen sources/operators")
    p1pot, p1meta = data["p1"][0]["potential"], data["p1"][1]
    recpot, recmeta = data["recovered_rt0"][0]["potential"], data["recovered_rt0"][1]
    _require(recmeta["potential_execution_id"] == p1meta["potential_execution_id"] and
             recmeta["flux_execution_id"] != p1meta["flux_execution_id"] and
             np.array_equal(recpot["values_V"], p1pot["values_V"]) and
             np.array_equal(recpot["mesh_node_indices"], p1pot["mesh_node_indices"]),
             "recovered RT0 potential does not derive from archived P1 solve")
    _require(data["mixed_rt0"][1]["flux_execution_id"] not in
             (p1meta["flux_execution_id"], recmeta["flux_execution_id"]),
             "mixed solution cannot reuse P1/recovered execution identity")
    return {m: {"analytic_potential_l2": data[m][2], "analytic_flux_l2": data[m][3]}
            for m in METHODS}


def publish_validated(root, manifest, payloads):
    """Validate contents *before* calling legacy exclusive, fail-closed writer."""
    results = validate_scientific_payloads(manifest, payloads)
    writer.publish_prepared(root, manifest, payloads)
    return results


def verify_archive(root):
    """Reject partial/corrupted archives, then independently recheck contents."""
    root = Path(root)
    _require(root.is_dir() and not (root / "INCOMPLETE").exists(),
             "incomplete or missing output archive")
    mf = root / "manifest.json"
    _require(mf.is_file(), "archive lacks final manifest")
    info = json.loads(mf.read_text())
    manifest = writer.default_manifest()
    _require(info.get("schema") == 1 and isinstance(info.get("sha256"), dict),
             "invalid archive manifest")
    expected_paths = {p for m in manifest.values() for p in m.values()}
    _require(set(info["sha256"]) == expected_paths,
             "archive is missing or has additional files")
    discovered = set()
    for actual in root.rglob("*"):
        _require(not actual.is_symlink(), "symlink in archive prohibited")
        if actual.is_file():
            discovered.add(actual.relative_to(root).as_posix())
    _require(discovered == expected_paths | {"manifest.json"},
             "archive contains unexpected files or missing data")
    payloads = {}
    for method, entries in manifest.items():
        payloads[method] = {}
        for kind, relpath in entries.items():
            blob = (root / relpath).read_bytes()
            _require(hashlib.sha256(blob).hexdigest() == info["sha256"][relpath],
                     "archive SHA256 mismatch")
            payloads[method][kind] = blob
    return validate_scientific_payloads(manifest, payloads)
