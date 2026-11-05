#!/usr/bin/env python3
"""R3.7: save a 430-region TetGen PLC from an immutable R3.3 MSH; NO tetrahedra/PDE."""
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import time

import gmsh
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/v3_r32_global_surface_20261103/source_metadata.json"
GEOM = ROOT / "data/v3_analysis_r3_20261103/geometry_restored/R3_conformal_mm.brep"
MESH = ROOT / "data/v3_r33_surface_20261105/attempt_01/run/global_surface.msh"
ORIGINAL_RESULT = MESH.parent / "result.json"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    arg = parser.parse_args()
    out = arg.out
    if out.exists():
        raise RuntimeError("Refusing to overwrite existing R3.7 output")
    out.mkdir(parents=True)
    begun = time.monotonic()
    source = read(SRC)
    legacy = read(ORIGINAL_RESULT)
    assert legacy["status"] == "FAIL GLOBAL SURFACE GATE; NO RETRY"
    assert len(source["domains"]) == len(source["domain_id_map"]) == 430
    assert len(source["faces"]) == 2440
    assert len(source["source_contacts"]) == 378
    assert len(set(source["domain_id_map"].values())) == 430
    assert sha(MESH) == read(MESH.parent / "mesh_archive_receipt.json")["SHA256"]

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
    try:
        assert gmsh.__version__ == "4.13.1"
        gmsh.model.occ.importShapes(str(GEOM))
        gmsh.model.occ.synchronize()
        assert len(gmsh.model.getEntities(3)) == 430
        assert len(gmsh.model.getEntities(2)) == 2440
        gmsh.merge(str(MESH))
        assert len(gmsh.model.getPhysicalGroups(3)) == 430
        assert len(gmsh.model.getPhysicalGroups(2)) == 2440
        ids, xyz, _ = gmsh.model.mesh.getNodes()
        ids = np.asarray(ids, dtype=np.int64)
        xyz = np.asarray(xyz, dtype=np.float64).reshape(-1, 3)
        assert len(ids) == len(np.unique(ids)) == 156599
        order = np.argsort(ids)
        ids, xyz = ids[order], xyz[order]
        maxid = int(ids.max())
        mesh_to_plc = np.full(maxid + 1, -1, dtype=np.int64)
        mesh_to_plc[ids] = np.arange(1, len(ids) + 1)
        lookup = np.full(maxid + 1, -1, dtype=np.int64)
        lookup[ids] = np.arange(len(ids))

        faces_by_volume = collections.defaultdict(list)
        facets = []
        face_counts = {}
        edge_occurrences = collections.Counter()
        for fid, f in sorted(source["faces"].items(), key=lambda x: int(x[0])):
            tag = int(fid)
            owners = sorted(map(int, gmsh.model.getAdjacencies(2, tag)[0]))
            assert owners == f["owner_volume_ids"], (fid, owners)
            types, _, arrays = gmsh.model.mesh.getElements(2, tag)
            assert list(types) == [2], (fid, types)
            triangles = np.asarray(arrays[0], dtype=np.int64).reshape(-1, 3)
            assert np.all(mesh_to_plc[triangles] > 0)
            mapped = mesh_to_plc[triangles]
            face_counts[fid] = len(mapped)
            assert len(mapped) > 0
            facets.append((tag, mapped))
            for owner in owners:
                faces_by_volume[owner].append((tag, f, triangles))
            edge_occurrences[len(owners)] += len(mapped)
            if tag % 400 == 0:
                print("read_face", tag, "triangles_so_far", sum(face_counts.values()),
                      "elapsed_s", round(time.monotonic()-begun, 2), flush=True)
        total_facets = sum(face_counts.values())
        assert total_facets == 320522 and len(facets) == 2440

        # Canonical sorted-triplet identity detects all coincident elements even
        # if their native winding or surface ownership is different.
        sorted_tri = np.vstack([np.sort(arr, axis=1) for _, arr in facets])
        assert len(np.unique(sorted_tri, axis=0)) == total_facets

        cad_masses = {}
        bounds = {}
        seeds = {}
        seed_methods = collections.Counter()
        fallback_fail = []
        for name, tag in sorted(source["domain_id_map"].items(), key=lambda x: x[1]):
            tag = int(tag)
            mass = float(gmsh.model.occ.getMass(3, tag))
            assert mass > 0 and math.isfinite(mass)
            cad_masses[name] = mass
            bounds[tag] = tuple(gmsh.model.getBoundingBox(3, tag))
            center = list(map(float, gmsh.model.occ.getCenterOfMass(3, tag)))
            b = bounds[tag]
            boxcenter = [(b[i] + b[i+3]) * 0.5 for i in range(3)]
            seed = None
            method = None
            for candidate, meth in ((center, "OCC_center_of_mass"),
                                    (boxcenter, "bbox_midpoint")):
                if gmsh.model.isInside(3, tag, candidate, False):
                    seed, method = candidate, meth
                    break

            if seed is None:
                candidates = sorted(faces_by_volume[tag],
                                    key=lambda x: -x[1]["face_area_mm2"])
                for ftag, face, tri in candidates[:min(80, len(candidates))]:
                    verts = xyz[lookup[tri]]
                    crossed = np.cross(verts[:, 1]-verts[:, 0], verts[:, 2]-verts[:, 0])
                    magnitudes = np.linalg.norm(crossed, axis=1)
                    largest = np.argsort(magnitudes)[-min(12, len(tri)):][::-1]
                    adjacent = [v for v in face["owner_volume_ids"] if v != tag]
                    for idx in largest:
                        if magnitudes[idx] <= 0:
                            continue
                        midpoint = verts[idx].mean(axis=0)
                        unit = crossed[idx] / magnitudes[idx]
                        for epsilon in (.00005, .0001, .0003, .0006, .001,
                                        .002, .003, .004, .006, .01, .015,
                                        .025, .04, .08, .12):
                            for direction in (-1, 1):
                                p = (midpoint + direction*epsilon*unit).tolist()
                                if not gmsh.model.isInside(3, tag, p, False):
                                    continue
                                if any(gmsh.model.isInside(3, other, p, False)
                                       for other in adjacent):
                                    continue
                                # 50 nm from a face is too close to trust for a
                                # numerically robust PLC region seed.
                                if epsilon < .0001:
                                    continue
                                seed = p
                                method = "inward_verified_boundary_triangle"
                                break
                            if seed is not None:
                                break
                        if seed is not None:
                            break
                    if seed is not None:
                        break
            if seed is None:
                fallback_fail.append(name)
                continue
            seeds[name] = {"volume_id": tag, "xyz_mm": seed, "method": method,
                           "material": source["domains"][name]["material"],
                           "CAD_volume_mm3": mass}
            seed_methods[method] += 1
        assert not fallback_fail, ("Could not find inside-region seeds", fallback_fail)
        assert len(seeds) == 430

        # Unique ownership: shortlist overlapping AABBs before strict OCC tests.
        # A seed inside an adjacent second volume indicates a topology/seed error.
        unique_fail = []
        for name, data in seeds.items():
            p = data["xyz_mm"]
            match = []
            for _, tag in source["domain_id_map"].items():
                tag = int(tag)
                b = bounds[tag]
                if any(p[i] < b[i]-1e-7 or p[i] > b[i+3]+1e-7
                       for i in range(3)):
                    continue
                if gmsh.model.isInside(3, tag, p, False):
                    match.append(tag)
            if match != [data["volume_id"]]:
                unique_fail.append((name, match))
        assert not unique_fail, ("Region seed is nonunique", unique_fail[:20])

        contacts_bad = []
        for contact in source["source_contacts"]:
            ff = contact["face_tags"]
            for ftag in ff:
                key = str(ftag)
                if key not in face_counts or face_counts[key] <= 0 or \
                   len(source["faces"][key]["owner_volume_ids"]) != 2:
                    contacts_bad.append((contact["index"], ftag))
        assert not contacts_bad, ("Missing finite contact witness", contacts_bad[:20])

        poly = out / "R37_430_domains_surface.poly"
        with poly.open("w") as f:
            f.write(f"{len(ids)} 3 0 0\n")
            for i, p in enumerate(xyz, 1):
                f.write(f"{i} {p[0]:.17g} {p[1]:.17g} {p[2]:.17g}\n")
            f.write(f"{total_facets} 1\n")
            for tag, triples in facets:
                for t in triples:
                    f.write(f"1 0 {tag}\n3 {t[0]} {t[1]} {t[2]}\n")
            f.write("0\n")
            f.write(f"{len(seeds)}\n")
            for name, data in sorted(seeds.items(), key=lambda x: x[1]["volume_id"]):
                vol = data["volume_id"]
                x, y, z = data["xyz_mm"]
                f.write(f"{vol} {x:.17g} {y:.17g} {z:.17g} {vol} -1\n")

        result = {
            "status": "PASS SOURCE MSH TO 430-REGION PLC PRECONDITIONS; TETRA NOT RUN",
            "source_R33_worker_status": legacy["status"],
            "original_R33_msh_sha256": sha(MESH),
            "CAD_BREP_sha256": sha(GEOM),
            "PLC_sha256": sha(poly),
            "PLC_size_bytes": poly.stat().st_size,
            "CAD_volumes": 430, "native_CAD_faces": 2440,
            "PLC_nodes": len(ids), "PLC_triangular_facets": total_facets,
            "PLC_facets_by_owner_count": dict(edge_occurrences),
            "distinct_face_markers": len(face_counts),
            "source_contact_witnesses": len(source["source_contacts"]),
            "source_contact_errors": contacts_bad,
            "region_seeds": len(seeds), "seed_methods": dict(seed_methods),
            "region_seed_uniqueness_errors": unique_fail,
            "region_names_to_attributes": {n: int(t) for n,t in source["domain_id_map"].items()},
            "face_triangle_counts": face_counts,
            "source_faces_per_volume": {str(k):len(v) for k,v in faces_by_volume.items()},
            "CAD_volume_mm3": cad_masses,
            "no_tetrahedralization": True, "no_PDE": True,
            "quality_gates": "NOT RUN: whole-device tets and conditioning",
            "source_script": "scripts/v3_r37_plc_preflight.py",
            "elapsed_seconds": round(time.monotonic()-begun, 3),
            "peak_RSS_MiB": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, 2)
        }
        (out / "region_seeds.json").write_text(json.dumps(seeds, indent=2)+"\n")
        (out / "result.json").write_text(json.dumps(result, indent=2)+"\n")
        print("RESULT", result["status"], "facets", total_facets,
              "seeds", seed_methods, "seconds", result["elapsed_seconds"],
              "rss", result["peak_RSS_MiB"], flush=True)
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    main()
