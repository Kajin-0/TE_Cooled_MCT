"""Build a source-to-STEP V3 multiphysics *geometry* readiness registry.

No Gmsh, meshing, PDE, property fitting, or CAD writes. The V3 R1 STEP is immutable.
The derived analysis representation is a proposed domain/port mapping, NOT
a validated multiphysics finite-element model.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "data/synthetic_v3_assembly_20261102"
SOURCE = V3 / "source_final/design.json"
STEP = V3 / "cad_02/synthetic_v3_mm.step"
SI = V3 / "cad_02/si_reader.json"
CONTACT = V3 / "source_final/contact_graph_final.json"
SPEC = ROOT / "docs/SYNTHETIC_V3_ASSEMBLY_CAD_20261102.md"
REV3 = ROOT / "reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf"


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(body):
    n, mat, shape = body["name"], body["material"], body["shape"]
    if n.startswith("ceramic"):
        return ("TEC ceramic reservoir", "thermal solid; electrical insulator; elastic support",
                "bulk 3D", n.upper())
    if mat in ("P", "N"):
        return ("thermoelectric leg", "coupled electric/thermal + Seebeck/Peltier/Thomson where qualified",
                "bulk 3D", "TE_STAGE" + str(next(
                    (i for i, b in enumerate((0, 1, 2)) if abs(body["bbox_mm"][2] - (2.13425 + 1.1 * b)) < .03), 0)))
    if n.startswith("solder") or mat in ("SnSb", "SnBi57_43", "In52Sn48"):
        return ("solder / finite contact", "electric and thermal conduction; joint/contact law unknown",
                "3D solder or equivalent interface requiring independent slab equivalence", None)
    if n.startswith("net") and mat in ("Ti", "TiW", "Cu", "Ni", "Au"):
        return ("patterned TEC conductor", "electric and thermal conduction; finite barrier/contact",
                "anisotropic multilayer sheet/interface, validate tangential and transverse", None)
    if n.startswith("formed_tab") or n.startswith("TEC_lead"):
        return ("metal interstage bridge or lead", "electric and thermal conduction; mechanical compliance",
                "resolved curved 3D path / validated reduced wire", None)
    if n.startswith("lead") and n.endswith("insulation"):
        return ("lead insulation", "thermal/dielectric and mechanical",
                "thin insulator shell or electrical clearance boundary", None)
    if n.startswith("pin") and ("_Au" in n or "_Ni" in n):
        return ("package pin finish", "electrical and thermal laminate/contact",
                "effective layer/film with physical thickness", None)
    if n.startswith("pin") and mat == "Kovar_pin":
        return ("hermetic header lead", "electric, thermal and mechanical",
                "3D shaft or 1D beam if transverse gradients pass verification", "PIN" + n[3:])
    if n.startswith("glass"):
        return ("glass feedthrough", "insulator/thermal/mechanical, hermeticity unqualified",
                "3D annular support", None)
    if n.startswith("header") or n.startswith("VIGO_reference_header"):
        return ("header heat sink substrate", "thermal/mechanical; package reference",
                "bulk 3D", "HEADER")
    if n.startswith("hot_mount") or n.startswith("underside") or n.startswith("header_finish"):
        return ("TEC/header interface", "thermal and mechanical conduction; electrical isolation must be confirmed",
                "thin-layer/contact operator plus bonded contact geometry", "HEADER")
    if n.startswith("cold_finish"):
        return ("cold-side ceramic coating", "thermal/optical/mechanical, electrical isolation",
                "multilayer coating/sheet", "CERAMIC3")
    if "HgCdTe" in n:
        return ("HgCdTe photoconductive detector", "electric/thermal/optical response; measured transport pending",
                "3D semiconductor domain", "DETECTOR")
    if n.startswith("det") or n.startswith("detector_bond"):
        return ("detector contact / wire", "electric/thermal/mechanical", "film interface or beam", None)
    if n.startswith("carrier") or n.startswith("sapphire") or n.startswith("die_attach"):
        return ("detector carrier and attachments", "thermal/mechanical; electrical insulator",
                "bulk 3D plus thin bonded interface", "DETECTOR")
    if n.startswith("cap") or n == "window":
        return ("enclosure / optical access", "thermal/mechanical; gas/radiation/optics",
                "boundary shell + optical window, native gas void NOT PRESENT", "ENCLOSURE")
    if mat == "Polyimide_candidate":
        return ("lead polymer insulation", "thermal and electric insulation, outgassing unknown",
                "thin annular coating", None)
    if mat in ("Ti", "TiW", "Cu", "Ni", "Au", "Au_ohmic"):
        return ("metal conductor / finish", "electric and thermal; finite contacts",
                "bulk or thin sheet depending on smallest physical thickness", None)
    return ("unclassified", "NOT REVIEWED", "NOT REVIEWED", None)


def thermal_ports():
    return [
        dict(id="CERAMIC0", physical="ceramic0", sign="heat entering model from port positive",
             boundary="ceramic0 exposed/support faces; excludes metal/leg/ceramic bonded interfaces"),
        dict(id="CERAMIC1", physical="ceramic1", sign="heat entering model from port positive",
             boundary="ceramic1 faces; resolve stage-0-to-stage-1 and return tab heat"),
        dict(id="CERAMIC2", physical="ceramic2", sign="heat entering model from port positive",
             boundary="ceramic2 faces; resolve stage-1-to-stage-2 and return tab heat"),
        dict(id="CERAMIC3", physical="ceramic3", sign="heat entering model from port positive",
             boundary="ceramic3 faces and cold_finish; detector load must be separately imposed"),
        dict(id="HEADER", physical="VIGO_reference_header, hot_mount_In52Sn48", sign="heat entering model from port positive",
             boundary="header sink/reference, finite thermal resistance, not prescribed infinite bath"),
        dict(id="TEC_PIN1", physical="pin1 external shaft cut", sign="heat entering model from port positive",
             boundary="distinct electrical terminal and external lead thermal reservoir"),
        dict(id="TEC_PIN9", physical="pin9 external shaft cut", sign="heat entering model from port positive",
             boundary="distinct electrical terminal and external lead thermal reservoir"),
        dict(id="DET_PIN7", physical="pin7 external shaft cut", sign="heat entering model from port positive",
             boundary="detector signal lead heat loss separate from TEC electrical return"),
        dict(id="DET_PIN8", physical="pin8 external shaft cut", sign="heat entering model from port positive",
             boundary="detector signal lead heat loss separate from TEC electrical return"),
        dict(id="CASE", physical="cap_shell, cap_roof", sign="heat entering model from port positive",
             boundary="enclosure and header coupling, contact/weld details unknown"),
        dict(id="WINDOW", physical="window", sign="heat entering model from port positive",
             boundary="window spectral transmission/radiative exchange, unqualified"),
        dict(id="GAS", physical="native cavity gas", sign="heat entering model from port positive",
             boundary="NOT AN EXISTING SOLID; future void geometry required for pressure-dependent gas conduction"),
        dict(id="OPTICAL", physical="photoconductor face", sign="absorbed optical power positive into detector",
             boundary="spectral absorbed power; source law and wavelength response not qualified"),
    ]


def main(out):
    if out.exists():
        raise ValueError("Refuse overwrite of geometry-readiness output")
    s, a, g = read(SOURCE), read(SI), read(CONTACT)
    assert a["STEP_sha256"] == digest(STEP)
    assert a["source_design_sha256"] == digest(SOURCE)
    assert len(s["bodies"]) == 824 == len(a["records"]) == a["body_count"]
    assert len(s["legs"]) == 88
    assert g["status"].startswith("PASS")
    index = {b["name"]: b for b in s["bodies"]}
    imported = {b["name"]: b for b in a["records"]}
    assert len(index) == len(imported) == 824 and index.keys() == imported.keys()
    assert {b["id"] for b in s["bodies"]} == set(range(824))
    domain, groupcount, strategies = [], Counter(), Counter()
    for b in s["bodies"]:
        sim = imported[b["name"]]
        role, equations, representation, port = classify(b)
        groupcount[role] += 1
        strategies[representation] += 1
        bbox = b["bbox_mm"]
        unit_bbox = [x / 1000 for x in bbox]
        entry = dict(
            name=b["name"], source_id=b["id"], imported_STEP_tag=sim["tag"],
            source="data/synthetic_v3_assembly_20261102/source_final/design.json",
            source_exact_sha256=digest(SOURCE), STEP_sha256=digest(STEP),
            material=b["material"], material_grade_evidence="synthetic selected; see V3 R1 spec",
            physics_role=role, governing_physics_candidate=equations,
            intended_analysis_representation=representation,
            original_shape=b["shape"], group=b.get("group"),
            volume_m3=b["volume_mm3"] * 1e-9,
            source_bbox_m=unit_bbox,
            imported_relative_volume_error=sim["relative_volume_error"],
            imported_bbox_error_m=sim["bbox_error_m"],
            initial_thermal_port=port,
            interface_laws_status="NOT COMPUTATIONALLY QUALIFIED",
            model_laws="candidate only, not solved",
        )
        domain.append(entry)
    assert len(domain) == 824 and all(d["physics_role"] != "unclassified" for d in domain)
    edges = []
    for i, q in enumerate(s["explicit_contacts"]):
        assert q["a"] in index and q["b"] in index, (i, q)
        assert q["area"] > 0
        edges.append(dict(
            id=i, component_a=q["a"], component_b=q["b"],
            source_contact_scope=q["scope"],
            witness_m=[v / 1000 for v in q["point"]],
            source_contact_area_m2=q["area"] * 1e-6,
            physical_relation="source contact witness, not independently qualified interface constitutive law",
            electric_law="finite contact conductance or galvanic continuous where justified; do not assume ideal",
            thermal_law="finite thermal/contact and interfacial coupling; port heat allocation to validate",
            mechanical_law="bonded or compliant contact subject to mounting/joint process checks",
            ownership="requires unique adjacent pair and outward-normal proof in analysis mesh",
            source="source_final/design.json:explicit_contacts",
            thermal_port="must inherit owning stage/lead boundary; NOT AUTOMATICALLY ASSIGNED",
            status="geometry source witness only, not PDE verification"))
    tab = [b for b in s["bodies"] if b["shape"] == "tab"]
    assert {b["name"] for b in tab} == {"formed_tab58", "formed_tab80", "formed_tab88"}
    tab_nom = {}
    for b in tab:
        thick, radius = b["thickness"], 0.075
        strain = thick / (2 * radius)
        tab_nom[b["name"]] = dict(
            thickness_mm=thick, neutral_radius_mm=radius,
            nominal_outer_fiber_strain_proxy=strain,
            unqualified="not physical plastic strain limit or fatigue prediction")
    radius_variants = []
    for radius in (.075, .10, .125, .15, .20):
        thick = .030
        radius_variants.append(dict(
            neutral_radius_mm=radius, foil_thickness_mm=thick,
            elementary_strain_proxy=thick / (2 * radius),
            inner_radius_mm=radius - thick / 2,
            geometric_rebuild_and_fit="NOT RUN",
            manufacture_fatigue_and_cycling="NOT QUALIFIED"))
    margins = []
    for t in g["tolerances"]:
        margins.append(dict(name=t["check"], worst_case_margin_mm=t.get("lower_bound"),
                            threshold_mm=t.get("requirement"), status=t.get("status"),
                            basis=t.get("units_and_basis")))
    assert len(margins) > 5
    spec_height = dict(
        current_range_mm=[3.664, 3.944], published_envelope_mm=[3.65, 3.95],
        upper_reserve_mm=3.95 - 3.944,
        lower_reserve_mm=3.664 - 3.65,
        hypothetical_tightening_requirements=[
            dict(component_tolerance_reduction_mm=v,
                 hypothetical_upper_reserve_mm=.006 + v,
                 qualification="ONLY ARITHMETIC WHAT-IF, no redefined source spec or CAD")
            for v in (0, .010, .020, .040)],
        proposed_action="do not change 824-solid STEP; investigate tolerance reallocation only after fit audit")
    result = dict(
        scope="no solve; no STEP modification; analysis mappings NOT qualified",
        created_UTC=dt.datetime.now(dt.timezone.utc).isoformat(),
        input_sha256={str(p.relative_to(ROOT)): digest(p) for p in
                      (SOURCE, STEP, SI, CONTACT, SPEC, REV3)},
        anchor_commit="33405a3e27e15b4c8be52c3ffbecae194c4c26e7",
        status="SOURCE/STEP identity PASS; multiphysics-domain completeness CONDITIONAL/NOT REVIEWED",
        body_count=len(domain), explicit_source_contact_count=len(edges),
        body_roles=dict(groupcount), strategy_counts=dict(strategies),
        parts=domain, source_interface_witnesses=edges, thermal_ports=thermal_ports(),
        electrical_terminal_assignments={
            "TEC_PIN1": "net0 / TEC lead1", "TEC_PIN9": "net88 / TEC lead9",
            "DET_PIN7": "photoconductor contact7", "DET_PIN8": "photoconductor contact8",
            "PIN5": "VACANT", "PIN6": "VACANT"
        },
        proposed_analysis_representations={
            "solids": "retain full P/N, ceramic, die, carrier, major lead paths and hot mount",
            "patterned_metal": "anisotropic sheet or two-sided thin-layer interface; preserve both sheet and through-thickness R, k",
            "solder": "thin interface with calibrated film/contact term and finite thermal jump where sourced",
            "foils": "3D curved trace or beam/shell with cross-section conserved, port G and J coupling",
            "detector": "photoconductive semiconductor only; optical/bias law scenario not measured",
            "cavity": "native void and radiation view factors NOT PRESENT; geometry creation required separately",
            "pin_and_header": "solid header/pin cut with finite boundary/lead thermal ports; cannot idealize sink"
        },
        unsolved_couplings=[
            "native gas void, gas pressure/accommodation, cap/window sealing and radiation visibility",
            "finite electrical and thermal contact laws at every physical joint",
            "temperature-dependent BiTe and HgCdTe transport with provenance and validity range",
            "mechanical stress, thermal fatigue, formed-tab bend strain, solder assembly process",
            "thermal port area allocation to exposed/soldered/wetted surface subsets",
            "pin1, pin9, pin7, pin8 independent lead heat exchange and external boundary conditions",
        ],
        tab_nominal=tab_nom, bend_radius_hypotheses=radius_variants,
        tolerance_source_records=margins, height_margin=spec_height,
        validation_requirements=[
            "analysis-domain faces must map injectively to actual STEP faces, no uncovered electrical/thermal boundary",
            "all finite contacts conserve current and heat across both sides, no duplicated flux",
            "represent all 13 declared thermal/optical/gas ports or explicitly document absent/adiabatic",
            "thin-sheet tangential resistance and transverse thermal/electrical impedance checked analytically",
            "curved leads and close tab/ceramic gaps independently checked at chosen analysis resolution",
            "representative parameter sweeps recheck real contact graph and worst-case tolerances",
            "future mesh quality/volume and solver energy cannot qualify this mapping retroactively",
        ],
        old_electrical_Gate_B="STOP; P1 raw81.241662%, recovered loss0.769154%; C/D NOT RUN")
    out.mkdir()
    (out / "domain_interface_registry.json").write_text(json.dumps(result, indent=2) + "\n")
    with (out / "domains.csv").open("w", newline="") as fh:
        cols = ["name", "source_id", "imported_STEP_tag", "material", "physics_role",
                "governing_physics_candidate", "intended_analysis_representation",
                "volume_m3", "initial_thermal_port"]
        writer = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        writer.writeheader()
        for item in domain:
            writer.writerow({k: item[k] for k in cols})
    with (out / "interfaces.csv").open("w", newline="") as fh:
        cols = ["id", "component_a", "component_b", "source_contact_scope",
                "source_contact_area_m2", "electric_law", "thermal_law", "status"]
        writer = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        writer.writeheader()
        for item in edges:
            writer.writerow({k: item[k] for k in cols})
    print(json.dumps({k: result[k] for k in
          ("status", "body_count", "explicit_source_contact_count", "body_roles", "strategy_counts")},
          indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    opts = parser.parse_args()
    main(opts.out)
