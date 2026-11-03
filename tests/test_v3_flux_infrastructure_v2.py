"""No-solve output hygiene and collision tests."""
import json
from pathlib import Path
import pytest
from tecooledmct.v3_flux_infrastructure_v2 import (
    default_manifest, publish_prepared, validate_manifest, METHODS, REQUIRED)


def data():
    return {m: {k: (m + k).encode() for k in REQUIRED} for m in METHODS}


def test_success(tmp_path):
    dest = tmp_path / "out"
    hashes = publish_prepared(dest, default_manifest(), data())
    assert len(hashes) == 3 * len(REQUIRED)
    assert len(json.loads((dest / "manifest.json").read_text())["sha256"]) == 3 * len(REQUIRED)


def test_duplicate_path_is_rejected_before_write(tmp_path):
    paths = default_manifest()
    paths["mixed_rt0"]["flux"] = paths["recovered_rt0"]["flux"]
    dest = tmp_path / "out"
    with pytest.raises(ValueError, match="namespace|duplicate"):
        publish_prepared(dest, paths, data())
    assert not dest.exists()


def test_mislabelled_method_is_rejected(tmp_path):
    paths = default_manifest()
    paths["mixed_rt0"]["flux"] = "lead9/flux.bin"
    with pytest.raises(ValueError, match="namespace"):
        publish_prepared(tmp_path / "out", paths, data())
    assert not (tmp_path / "out").exists()


def test_existing_archive_never_overwritten(tmp_path):
    dest = tmp_path / "out"
    publish_prepared(dest, default_manifest(), data())
    f = dest / "mixed_rt0" / "flux.bin"
    before = f.read_bytes()
    with pytest.raises(FileExistsError):
        publish_prepared(dest, default_manifest(), data())
    assert f.read_bytes() == before


def test_incomplete_fields_fail_before_write(tmp_path):
    payload = data()
    del payload["mixed_rt0"]["potential"]
    with pytest.raises(ValueError):
        publish_prepared(tmp_path / "out", default_manifest(), payload)
    assert not (tmp_path / "out").exists()
