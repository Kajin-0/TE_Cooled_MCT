"""Prospective no-solve output protocol for independently retained flux methods.

This module is NOT imported by the frozen experimental producer.
"""
import hashlib
import json
import os
from pathlib import Path

METHODS = frozenset({"p1", "recovered_rt0", "mixed_rt0"})
REQUIRED = frozenset({"mesh", "potential", "flux", "material_map",
                      "residual", "analytical_reference", "metadata"})


def validate_manifest(manifest):
    if set(manifest) != METHODS:
        raise ValueError("exact three method identifiers required")
    all_paths = set()
    for method, files in manifest.items():
        if set(files) != REQUIRED:
            raise ValueError("missing/extra control-field archive: " + method)
        for kind, path in files.items():
            if not isinstance(path, str) or not path or Path(path).is_absolute():
                raise ValueError("invalid output path")
            parts = Path(path).parts
            if ".." in parts or parts[0] != method:
                raise ValueError("wrong method namespace")
            if path in all_paths:
                raise ValueError("duplicate destination")
            all_paths.add(path)
    return True


def publish_prepared(root, manifest, payloads):
    """All-or-nothing preflight, exclusive writes; refuses overwrite.

    root MUST be a new directory. Validation is done before creating root.
    No PDE solve, no field reconstruction and no deserialization of arbitrary pickle.
    """
    root = Path(root)
    validate_manifest(manifest)
    if set(payloads) != METHODS:
        raise ValueError("missing method payload")
    for method, files in manifest.items():
        if set(payloads[method]) != REQUIRED:
            raise ValueError("missing archive field")
        for kind in REQUIRED:
            if not isinstance(payloads[method][kind], bytes):
                raise TypeError("archive values must be bytes")
    # A new root provides fail-before-overwrite semantics; pathlib mkdir is exclusive.
    root.mkdir(parents=False, exist_ok=False)
    hashes = {}
    try:
        for method, files in manifest.items():
            for kind, relative in files.items():
                dest = root / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                with os.fdopen(os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "wb") as fp:
                    fp.write(payloads[method][kind])
                hashes[relative] = hashlib.sha256(payloads[method][kind]).hexdigest()
        (root / "manifest.json").write_text(json.dumps({"schema": 1, "sha256": hashes}, indent=2) + "\n")
    except BaseException:
        # Do not delete partial artifacts; preserve failure for forensics.
        (root / "INCOMPLETE").write_text("STOP: partial archive retained; do not reuse this output directory\n")
        raise
    return hashes


def default_manifest():
    return {method: {kind: method + "/" + kind + ".bin" for kind in sorted(REQUIRED)}
            for method in sorted(METHODS)}
