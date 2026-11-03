"""V3 derived computational BREP: direct OCC transformations of frozen STEP solids.

Source/STEP immutable. Analysis conductor laminates are collapsed geometrically
but layer composition and finite interfacial laws remain explicit registry tasks.
Gas cavity is constructed by OCC occupied-volume subtraction, never a visual prop.
NO PDE, NO electrical or thermal field solve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHYSICAL = ROOT / "data/synthetic_v3_assembly_20261102"
SOURCE = PHYSICAL / "source_final/design.json"
STEP = PHYSICAL / "cad_02/synthetic_v3_mm.step"
SI = PHYSICAL / "cad_02/si_reader.json"
REV3 = ROOT / "reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf"
LAYERS = (("Ti", .000075), ("TiW", .000050), ("Cu", .013625), ("Ni", .001), ("Au", .000250))
OUTER = (("Ti", .000075), ("TiW", .000050), ("Cu", .000625), ("Ni", .001), ("Au", .000250))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def layer_group(b):
    n, mat = b["name"], b["material"]
    if n.startswith("net") and mat in ("Ti", "TiW", "Ni", "Au", "Cu"):
        return n.rsplit("_", 1)[0], mat
    if n.startswith(("underside_", "cold_finish_")) and mat in ("Ti", "TiW", "Ni", "Au", "Cu"):
        return n.rsplit("_", 1)[0], mat
    if n.startswith(("det7_", "det8_")) and mat in ("Au_ohmic", "Ni", "Au"):
        return n.split("_",1)[0], mat
    if n.startswith("header_finish_"):
        return "header_finish", mat
    return None, None


def source_plan():
    src = json.loads(SOURCE.read_text())
    rdr = json.loads(SI.read_text())
    assert sha(STEP) == rdr["STEP_sha256"]
    assert sha(SOURCE) == rdr["source_design_sha256"]
    assert len(src["bodies"]) == len(rdr["records"]) == 824
    rmap = {x["name"]: x for x in rdr["records"]}
    assert len(rmap) == 824
    tags = {}
    for b in src["bodies"]:
        assert b["name"] in rmap
        tags[b["name"]] = rmap[b["name"]]["tag"]
    merged = defaultdict(list)
    for b in src["bodies"]:
        key, mat = layer_group(b)
        if key:
            merged[key].append(b)
    remove, enlarge, replacements = set(), {}, {}
    for key, group in merged.items():
        matmap = {x["material"]: x for x in group}
        if key.startswith("net"):
            assert set(matmap) == {k for k, _ in LAYERS}, (key, matmap)
            keep = matmap["Cu"]["name"]
            low = min(x["bbox_mm"][2] for x in group)
            high = max(x["bbox_mm"][5] for x in group)
            enlarge[keep] = dict(target_zlow_mm=low, target_zhigh_mm=high, kind="five-film patterned laminate")
        elif key in ("underside", "cold_finish"):
            # Keep the actual patterned finish footprint as one composite thin solid.
            assert set(matmap) == {k for k, _ in OUTER}
            keep=matmap["Au"]["name"]
            enlarge[keep]=dict(target_zlow_mm=min(x["bbox_mm"][2] for x in group),
                               target_zhigh_mm=max(x["bbox_mm"][5] for x in group),
                               kind="full-footprint outer coating multilayer")
        elif key in ("det7", "det8"):
            # Group only the ohmic/finish pad, keep its real wedge foot separately.
            assert set(matmap) == {"Au_ohmic", "Ni", "Au"}
            keep = matmap["Au"]["name"]
            enlarge[keep] = dict(target_zlow_mm=min(x["bbox_mm"][2] for x in group),
                                 target_zhigh_mm=max(x["bbox_mm"][5] for x in group),
                                 kind="detector contact multilayer")
        elif key.startswith("pin"):
            assert set(matmap) == {"Ni", "Au"}
            keep = None
        elif key == "header_finish":
            assert set(matmap) == {"Ni", "Au"}
            keep=matmap["Ni"]["name"]
            enlarge[keep]=dict(target_zlow_mm=min(x["bbox_mm"][2] for x in group),
                               target_zhigh_mm=max(x["bbox_mm"][5] for x in group),
                               kind="full-footprint header finish multilayer")
        else:
            raise AssertionError(key)
        for b in group:
            if b["name"] != keep:
                remove.add(b["name"])
        replacements[key] = dict(physical_sources=[x["name"] for x in group],
                                 retained_name=keep,
                                 source_total_volume_mm3=sum(x["volume_mm3"] for x in group),
                                 layers=[dict(material=x["material"], thickness_mm=x["bbox_mm"][5]-x["bbox_mm"][2])
                                         for x in sorted(group, key=lambda x:x["bbox_mm"][2])],
                                 electrical_law="anisotropic in-plane parallel sheet; transverse series + finite contact",
                                 thermal_law="in-plane parallel and transverse series thermal laminate with interface thermal resistance",
                                 equivalence="ANALYTIC LAW ONLY; no field equivalence qualified")
    # Keep actual coating footprints separate from mount and ceramic bodies.
    # No expansion of adjacent physical material footprint is permitted.
    for n, value in enlarge.items():
        b = next(x for x in src["bodies"] if x["name"] == n)
        zlo, zhi = b["bbox_mm"][2], b["bbox_mm"][5]
        assert value["target_zhigh_mm"] > value["target_zlow_mm"]
        value["original_z_mm"] = [zlo, zhi]
        value["scale"] = (value["target_zhigh_mm"]-value["target_zlow_mm"])/(zhi-zlo)
    retained = [b for b in src["bodies"] if b["name"] not in remove]
    return src, tags, retained, remove, enlarge, replacements


def build(out, gas=True):
    import gmsh
    if out.exists():
        raise ValueError("refuse overwrite")
    out.mkdir(parents=True)
    start = time.monotonic()
    src, tags, retained, remove, enlarge, replacements = source_plan()
    info = dict(
        state="INCOMPLETE", execution_UTC=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        immutable_input_sha256={str(p.relative_to(ROOT)): sha(p) for p in (SOURCE, STEP, SI, REV3)},
        imported_824=True, original_solids=824,
        removed_physical_thin_solids=len(remove), retained_domains=len(retained),
        changed_geometric_envelope=enlarge, reductions=replacements,
        source_to_analysis={x["name"]: tags[x["name"]] for x in retained},
        no_physics_solve=True,
        caveats=[
            "Composite conductor requires independent anisotropic tensor/interface material equivalence tests",
            "Finite solder, P/N and tab contacts remain physical separate solids",
            "Final STEP-face ownership is not implied by source body identities",
            "Gas boolean must preserve actual solids and produce provable disjoint occupied region",
            "Hermeticity, cap/window and header sealing are idealized closure conditions",
            "Original electrical numerical Gate B remains STOP, thermal C/D not run",
        ])
    save(out / "design_plan.json", info)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
    gmsh.option.setNumber("General.NumThreads", 4)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", 4)
    try:
        occ = gmsh.model.occ
        imported = occ.importShapes(str(STEP))
        occ.synchronize()
        assert len(imported) == 824
        for name in sorted(remove):
            occ.remove([(3, tags[name])], recursive=False)
        for name, q in enlarge.items():
            tag = tags[name]
            zlo, zhi = q["original_z_mm"]
            # Scale only Z, anchored at the physical original solid's lower boundary.
            occ.dilate([(3, tag)], 0, 0, zlo, 1, 1, q["scale"])
            occ.translate([(3, tag)], 0, 0, q["target_zlow_mm"] - zlo)
        occ.synchronize()
        existing = [t for _,t in gmsh.model.getEntities(3)]
        assert len(existing) == len(retained), (len(existing), len(retained))
        mass_errors = {}
        srcby = {b["name"]: b for b in src["bodies"]}
        for b in retained:
            name = b["name"]
            mass = occ.getMass(3, tags[name])
            expect = b["volume_mm3"] * enlarge[name]["scale"] if name in enlarge else b["volume_mm3"]
            err = abs(mass / expect - 1)
            if err > 2e-7:
                mass_errors[name] = err
        if mass_errors:
            raise ValueError("Imported CAD mass discrepancies: " + str(sorted(mass_errors.items(), key=lambda x:-x[1])[:10]))
        gmsh.write(str(out / "analysis_solids_mm.brep"))
        info["reduced_solid_count"] = len(existing)
        info["reductions_validated_volume"] = True
        info["analysis_solids_sha256"] = sha(out / "analysis_solids_mm.brep")
        print("REDUCED SOLIDS",len(existing),"seconds",round(time.monotonic()-start,3),flush=True)
        if not gas:
            info["gas_status"] = "NOT RUN"
            info["state"] = "PARTIAL - no cavity"
            return
        # A closed synthetic inner cavity: inside cap bore and below roof/window,
        # above header top. This is an IDEALIZED full closure, not a sealed OEM.
        gasid = occ.addCylinder(0, 0, 1.5, 0, 0, 8.15, 7.1)
        occ.synchronize()
        source_gas_volume = occ.getMass(3, gasid)
        # Cut actual occupied solids, keeping original independent solid domains.
        # The cap itself meets the cylinder at its radial boundary.
        cuttools = [(3,t) for t in existing if t not in
                    [tags["cap_shell"],tags["cap_roof"],tags["window"]]]
        print("GAS BOOLEAN CUT BEGIN",len(cuttools),"source",source_gas_volume,flush=True)
        t0 = time.monotonic()
        gas_entities, cutmap = occ.cut([(3,gasid)], cuttools,
                                       removeObject=True, removeTool=False)
        occ.synchronize()
        gas_tags = [t for dim,t in gas_entities if dim==3]
        if not gas_tags:
            raise ValueError("No interior gas remaining")
        gas_volumes = [occ.getMass(3,t) for t in gas_tags]
        gas_volume = sum(gas_volumes)
        if not (0 < gas_volume < source_gas_volume):
            raise ValueError("Gas subtraction physically invalid")
        info["gas_status"] = "CAD BOOLEAN CUT, NOT MESHED"
        info["gas_entities"] = gas_tags
        info["gas_component_count"] = len(gas_tags)
        info["gas_component_volumes_mm3"] = gas_volumes
        info["gas_volume_mm3"] = gas_volume
        info["cavity_unoccupied_fraction"] = gas_volume/source_gas_volume
        info["boolean_seconds"] = time.monotonic()-t0
        gmsh.write(str(out / "analysis_with_gas_mm.brep"))
        info["analysis_with_gas_sha256"] = sha(out / "analysis_with_gas_mm.brep")
        info["state"] = "SOLIDS+CAVITY CREATED; FACE OWNERSHIP UNQUALIFIED"
        print("GAS RESULT",len(gas_tags),gas_volume,"s",round(time.monotonic()-t0,1),flush=True)
    except Exception as exc:
        info["state"] = "FAIL"
        info["error"] = repr(exc)
        raise
    finally:
        info["elapsed_seconds"] = time.monotonic()-start
        save(out / "design_plan.json",info)
        gmsh.finalize()


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--no-gas",action="store_true")
    q=p.parse_args()
    build(q.out, gas=not q.no_gas)
