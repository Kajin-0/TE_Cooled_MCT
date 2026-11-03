"""No-PDE scientific archive integrity tests with synthetic array fixtures.

These deliberately fabricated arrays are data-integrity controls, not solver
benchmark results or evidence that the physical V3 mixed field exists.
"""
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pytest

from tecooledmct import v3_flux_archive_contract as c
from tecooledmct import v3_flux_infrastructure_v2 as w


POINTS = np.array([[0, 0, 0], [0.001, 0, 0],
                   [0, 0.001, 0], [0, 0, 0.001]], dtype=np.float64)
CELLS = np.array([[0, 1, 2, 3]], dtype=np.int64)
FACES = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.int64)
CENTROID = POINTS[CELLS].mean(axis=1)


def pack(**arrays):
    with io.BytesIO() as buf:
        np.savez_compressed(buf, **arrays)
        return buf.getvalue()


def repack(blob, **changes):
    with np.load(io.BytesIO(blob), allow_pickle=False) as f:
        data = {k: f[k] for k in f.files}
    data.update(changes)
    return pack(**data)


def fixture():
    m = pack(points_m=POINTS, cells=CELLS, regions=np.array([0], dtype=np.int64),
             face_nodes=FACES,
             cell_faces=np.array([[3, 2, 1, 0]], dtype=np.int64),
             cell_face_signs=np.array([[1., -1., 1., -1.]], dtype=np.float64))
    sha = hashlib.sha256(m).hexdigest()
    tensor = np.eye(3, dtype=np.float64)[None, :, :]
    identity = "a" * 64
    operator = "b" * 64
    out = {}
    for method in c.METHODS:
        ismixed = method == "mixed_rt0"
        values = np.array([0, 1, 0, 0], dtype=np.float64)
        if ismixed:
            values = np.array([0.25], dtype=np.float64)
        dofs = np.array([], dtype=np.int64) if ismixed else np.arange(4, dtype=np.int64)
        positions = CENTROID if ismixed else POINTS
        jid = ("mixed-solve" if ismixed else
               "recovery-solve" if method == "recovered_rt0" else "p1-solve")
        potential_execution_id = "mixed-solve" if ismixed else "p1-solve"
        flux_execution_id = jid
        expected = {
            "mesh": m,
            "potential": pack(values_V=values, sample_points_m=positions,
                              mesh_node_indices=dofs,
                              execution_id=np.asarray(potential_execution_id),
                              method_id=np.asarray(method)),
            "flux": pack(J_A_m2=np.zeros((1, 3), dtype=np.float64),
                         sample_points_m=CENTROID.copy(),
                         sample_cells=np.array([0], dtype=np.int64),
                         face_currents_A=np.zeros(4 if method != "p1" else 0, dtype=np.float64),
                         execution_id=np.asarray(flux_execution_id),
                         method_id=np.asarray(method)),
            "material_map": pack(region_ids=np.array([0], dtype=np.int64),
                                 conductivity_S_m=tensor, resistivity_ohm_m=tensor),
            "residual": pack(cell_balance_A=np.zeros(1),
                             execution_id=np.asarray(flux_execution_id),
                             method_id=np.asarray(method)),
        }
        expected["analytical_reference"] = pack(
            available=np.asarray(True), potential_V=values.copy(),
            J_A_m2=np.zeros((1, 3), dtype=np.float64),
            potential_weights=np.ones(len(values), dtype=np.float64),
            flux_weights_m3=np.ones(1, dtype=np.float64))
        meta = {
            "method": method, "units": c.UNITS, "kind": "analytic_control",
            "run_id": "synthetic-no-solve", "source_sha256": identity,
            "operator_sha256": operator, "mesh_sha256": sha,
            "potential_execution_id": potential_execution_id,
            "flux_execution_id": flux_execution_id,
            "bbox_m": np.vstack((POINTS.min(axis=0), POINTS.max(axis=0))).tolist(),
            "reported_analytic_errors": {"potential_l2": 0., "flux_l2": 0.},
        }
        expected["metadata"] = json.dumps(meta, sort_keys=True).encode()
        out[method] = expected
    return out


def amend(payload, method, kind, **changes):
    payload[method][kind] = repack(payload[method][kind], **changes)


def metadata(payload, method, **changes):
    meta = json.loads(payload[method]["metadata"])
    meta.update(changes)
    payload[method]["metadata"] = json.dumps(meta, sort_keys=True).encode()


def test_typed_scientific_archive_passes_no_solve(tmp_path):
    payload = fixture()
    refs = c.validate_scientific_payloads(w.default_manifest(), payload)
    assert refs["mixed_rt0"]["analytic_flux_l2"] == 0
    dest = tmp_path / "valid"
    c.publish_validated(dest, w.default_manifest(), payload)
    assert c.verify_archive(dest) == refs


@pytest.mark.parametrize("bad,method,kind,key,value", [
    ("wrong dimensionality", "mixed_rt0", "flux", "J_A_m2", np.zeros(3)),
    ("wrong dtype", "p1", "potential", "values_V", np.zeros(4, dtype=np.float32)),
    ("wrong DOFs", "mixed_rt0", "potential", "values_V", np.zeros(4)),
    ("nonfinite", "p1", "flux", "J_A_m2", np.array([[np.nan, 0., 0.]])),
    ("wrong method", "mixed_rt0", "flux", "method_id", np.asarray("recovered_rt0")),
    ("wrong execution", "p1", "flux", "execution_id", np.asarray("other-solve")),
    ("wrong analytic norm", "p1", "analytical_reference", "J_A_m2", np.ones((1, 3))),
    ("incorrect material", "mixed_rt0", "material_map", "conductivity_S_m",
     np.array([[[-1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]])),
])
def test_wrong_field_content_rejected_before_write(tmp_path, bad, method, kind, key, value):
    payload = fixture()
    amend(payload, method, kind, **{key: value})
    dest = tmp_path / "bad"
    with pytest.raises(ValueError):
        c.publish_validated(dest, w.default_manifest(), payload)
    assert not dest.exists(), bad


def test_unit_mismatch_rejected(tmp_path):
    payload = fixture()
    units = dict(c.UNITS)
    units["length"] = "mm"
    metadata(payload, "p1", units=units)
    with pytest.raises(ValueError, match="units"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)
    assert not (tmp_path / "out").exists()


def test_mesh_scale_and_cross_method_mismatch_rejected(tmp_path):
    payload = fixture()
    scaled = POINTS * 1000.
    newmesh = repack(payload["mixed_rt0"]["mesh"], points_m=scaled)
    payload["mixed_rt0"]["mesh"] = newmesh
    metadata(payload, "mixed_rt0", mesh_sha256=hashlib.sha256(newmesh).hexdigest())
    with pytest.raises(ValueError):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_lineage_mismatch_rejected(tmp_path):
    payload = fixture()
    metadata(payload, "mixed_rt0", run_id="different-run")
    with pytest.raises(ValueError, match="same experiment"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_analytical_error_recomputed_from_archived_arrays(tmp_path):
    payload = fixture()
    payload["p1"]["analytical_reference"] = repack(
        payload["p1"]["analytical_reference"],
        potential_V=np.ones(4, dtype=np.float64))
    with pytest.raises(ValueError, match="L2 errors"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_no_claim_of_missing_analytic_references(tmp_path):
    payload = fixture()
    metadata(payload, "p1", kind="coupon", reported_analytic_errors=None)
    with pytest.raises(ValueError, match="availability"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_tampering_rejected_after_archive_completion(tmp_path):
    payload = fixture()
    dest = tmp_path / "out"
    c.publish_validated(dest, w.default_manifest(), payload)
    file = dest / "mixed_rt0/flux.bin"
    file.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        c.verify_archive(dest)


def test_interrupted_write_preserves_incomplete_and_refuses_read(tmp_path, monkeypatch):
    payload = fixture()
    dest = tmp_path / "out"
    original_open = w.os.open
    count = 0

    def fail_second_write(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("injected interruption")
        return original_open(*args, **kwargs)

    monkeypatch.setattr(w.os, "open", fail_second_write)
    with pytest.raises(OSError, match="injected interruption"):
        c.publish_validated(dest, w.default_manifest(), payload)
    assert (dest / "INCOMPLETE").is_file()
    with pytest.raises(ValueError, match="incomplete"):
        c.verify_archive(dest)
    with pytest.raises(FileExistsError):
        c.publish_validated(dest, w.default_manifest(), payload)


def test_no_pickle_array_payload_accepted(tmp_path):
    payload = fixture()
    amend(payload, "mixed_rt0", "potential",
          values_V=np.array([{"undocumented": "field"}], dtype=object))
    with pytest.raises(ValueError, match="unsafe|object"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_rt0_face_orientation_and_cell_balance_rejected(tmp_path):
    payload = fixture()
    amend(payload, "mixed_rt0", "mesh",
          cell_face_signs=np.array([[-1., -1., 1., -1.]]))
    # Update the self-reported SHA to demonstrate independent orientation checks.
    for method in c.METHODS:
        payload[method]["mesh"] = payload["mixed_rt0"]["mesh"]
        metadata(payload, method, mesh_sha256=hashlib.sha256(payload[method]["mesh"]).hexdigest())
    with pytest.raises(ValueError, match="orientation"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_rt0_residual_consistency_rejected(tmp_path):
    payload = fixture()
    amend(payload, "mixed_rt0", "flux", face_currents_A=np.array([0., 0., 0., 1.]))
    with pytest.raises(ValueError, match="residual"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_rt0_vector_field_consistency_rejected(tmp_path):
    payload = fixture()
    amend(payload, "mixed_rt0", "flux",
          J_A_m2=np.array([[1., 2., 3.]]))
    with pytest.raises(ValueError, match="flux samples inconsistent"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_mesh_to_cell_face_mapping_rejected(tmp_path):
    payload = fixture()
    malformed = repack(payload["p1"]["mesh"], cell_faces=np.array([[3, 2, 0, 1]], dtype=np.int64))
    for method in c.METHODS:
        payload[method]["mesh"] = malformed
        metadata(payload, method, mesh_sha256=hashlib.sha256(malformed).hexdigest())
    with pytest.raises(ValueError, match="incidence"):
        c.publish_validated(tmp_path / "out", w.default_manifest(), payload)


def test_unexpected_file_in_completed_archive_rejected(tmp_path):
    payload = fixture()
    dest = tmp_path / "out"
    c.publish_validated(dest, w.default_manifest(), payload)
    (dest / "unspecified_result.vtu").write_bytes(b"unreviewed")
    with pytest.raises(ValueError, match="unexpected files"):
        c.verify_archive(dest)
