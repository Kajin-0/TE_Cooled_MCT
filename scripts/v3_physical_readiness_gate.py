#!/usr/bin/env python3
"""R3 physical-input and Gate B readiness: strict no-solve, source-backed reconciliation.

This does not qualify, infer or populate any material, interface, boundary,
or thermoelectric coefficient. It explicitly rejects the old 438-domain law
registry as the active 430-domain law table. All readings are immutable.
"""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R3 = ROOT / "data/v3_r32_global_surface_20261103/source_metadata.json"
OLD = ROOT / "data/v3_global_mesh_gate_20261103/physics_law_requirements.json"
B = ROOT / "data/v3_interconnect_et_20261102/B/gate_B.json"
MAT = ROOT / "data/v3_interconnect_et_20261102/operator_definitions.json"
R38 = ROOT / "data/v3_r38_global_tetgen_20261105/attempt01/saved_mesh_audit.json"
R39 = ROOT / "data/v3_r39_quality_20261105/attempt01/manifest.json"
R317 = ROOT / "data/v3_r317_two_contact_network_20261106/attempt01/manifest.json"
SRC_EVIDENCE = ROOT / "data/physical_input_qualification_20261101/evidence_analysis.json"

def digest(p):
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(path.read_text())

def audit():
    geometry = read(R3)
    old = read(OLD)
    gate = read(B)
    material = read(MAT)
    mesh38 = read(R38)
    mesh39 = read(R39)
    network = read(R317)
    evidence = read(SRC_EVIDENCE)

    d = geometry["domains"]
    faces = geometry["faces"]
    contacts = geometry["source_contacts"]
    terminals = geometry["terminal_faces"]
    assert len(d) == 430 and len(faces) == 2440 and len(contacts) == 378
    ids = [v["id"] for v in d.values()]
    assert set(ids) == set(range(1, 431)) and len(ids) == len(set(ids))
    assert all(not x.get("solver_ready", True) for x in d.values())
    status_counts = collections.Counter(v.get("law_status", "MISSING") for v in d.values())
    assert status_counts == {"UNSET": 430}, status_counts
    fstatus = collections.Counter(v.get("law_status", "MISSING") for v in faces.values())
    assert fstatus == {"UNSET": 2440}, fstatus
    material_counts = collections.Counter(v["material"] for v in d.values())
    fclass = collections.Counter(v.get("class_", "MISSING") for v in faces.values())
    assert len(terminals) == 4
    assert set(terminals) == {"pin1", "pin7", "pin8", "pin9"}
    assert all(len(tags) == 1 and int(tags[0]) in range(1,2441) for tags in terminals.values())
    assert old["volume_count"] == 438 and old["face_count"] == 2456
    assert old["solver_ready"] is False
    assert mesh38["status"].startswith("PASS GEOMETRIC 3D GATES")
    assert mesh38["PLC_regions"] == 430 and mesh38["tetrahedra"] == 1043314
    assert mesh39["derived_tetrahedra"] == 1010119
    assert network["original_R38_R39_files_unchanged"]
    assert gate["status"] == "FAIL/STOP"
    expected = {"cuts_0p1pct":False,"power_0p5pct":True,
                "voltage_bounded":False,"R_refinement_1pct":True}
    assert gate["acceptance"] == expected
    assert not evidence["physical_validation"]

    critical = {}
    for label, id_ in (("HgCdTe_active",408),("Detector_composite_contact",410),
                       ("Gold_detector_bond",420),("TEC_Cu_lead9",416)):
        name, obj = next((k,v) for k,v in d.items() if v["id"] == id_)
        critical[label] = {
            "id":id_, "name":name, "material_role":obj["material"],
            "constitutive_requirement":obj["constitutive_requirement"],
            "law_status":obj["law_status"], "solver_ready":obj["solver_ready"],
            "layer_stack":obj.get("layer_stack")
        }
    contact_geometry = {}
    for tag, pair in ((2336,(408,410)),(2349,(410,420))):
        obj = faces[str(tag)]
        assert tuple(obj["owner_volume_ids"]) == pair
        contact_geometry[str(tag)] = {
            "owner_volume_ids":list(pair),
            "CAD_area_mm2":obj["face_area_mm2"],
            "law_status":obj["law_status"],
            "qualification":"GEOMETRY_ONLY; physical contact law UNSET"
        }
    # This inventory is a strict reconciliation of already-registered data,
    # not a release of real transport coefficients.
    gate_raw = gate["worst_fine_cut_relative_error"]
    assert abs(gate_raw - .8562549986750948) < 1e-14
    assert gate_raw > 0.001
    assert gate["fine_power_relative_error"] < .005

    return {
        "status":"STOP PHYSICAL ELECTROTHERMAL READINESS — source-backed no-solve audit",
        "audit_date_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_of_truth":"current R3 430-domain derived CAD and preserved V3 electrical coupon",
        "physical_input_population": {
            "CAD_domains":len(d), "CAD_faces":len(faces), "registered_contacts":len(contacts),
            "volume_law_status":dict(status_counts),
            "face_law_status":dict(fstatus),
            "material_counts":dict(sorted(material_counts.items())),
            "face_class_counts":dict(sorted(fclass.items())),
            "terminal_faces":terminals,
            "source_solver_ready_domains":sum(v["solver_ready"] for v in d.values()),
            "source_solver_ready_faces":sum(v["law_status"] != "UNSET" for v in faces.values()),
            "source_law_values_released":False
        },
        "historical_law_registry": {
            "historical_domains":old["volume_count"],"historical_faces":old["face_count"],
            "active_domains":len(d),"active_faces":len(faces),
            "delta_domains":len(d)-old["volume_count"],
            "delta_faces":len(faces)-old["face_count"],
            "active_law_registry_status":"NOT PORTED; historical 438-domain table is NOT active 430-domain qualified law release",
            "fallback_to_material_defaults":"PROHIBITED"
        },
        "frozen_geometry": {
            "global_R38_tetrahedra":mesh38["tetrahedra"],
            "global_R38_nodes":mesh38["nodes"],
            "R39_derived_tetrahedra":mesh39["derived_tetrahedra"],
            "global_mesh_quality":"NOT QUALIFIED FOR PREDICTIVE FEM",
            "global_nonadjacent_overlap":"NOT RUN",
            "all_430_region_physical_PDE":"NOT RUN"
        },
        "original_gate_B": {
            "status":gate["status"],
            "test_case":"V3 original net88/lead9 local coupon, not full physical TEC",
            "worst_fine_raw_current_cut_relative_error":gate_raw,
            "registered_cut_limit":.001,
            "multiple_of_limit":gate_raw/.001,
            "fine_power_relative_error":gate["fine_power_relative_error"],
            "power_limit":.005,
            "resistance_refinement_error":gate["R_relative_refinement"],
            "resistance_refinement_limit":.01,
            "fine_voltage_boundedness":"FAIL",
            "preregistered_gate_results":gate["acceptance"],
            "gate_status":"FAIL; no re-interpretation based on algebraic contact/reaction conservation",
            "C":"NOT RUN",
            "D":"NOT RUN"
        },
        "critical_r3_volume_roles":critical,
        "physical_contact_faces":contact_geometry,
        "physical_input_evidence":{
            "prior_reduced_model_nominal_temperature_K":evidence["nominal_target"]["Tdie_K"],
            "prior_reduced_model_terminal_power_W":evidence["nominal_target"]["terminal_W"],
            "prior_reduced_model_is_current_V3_430_domain_PDE":False,
            "prior_reduced_model_material_uncertainty_qualified":False,
            "native_gas_nonlocal_contact_matched_target_sensitivity":evidence["native_gas_nonlocal_contact_matched_target_sensitivity"]
        },
        "readiness_decisions":{
            "Gate_B":"STOP",
            "Gates_C_D":"NOT RUN",
            "material_law_release":"STOP",
            "full_430_domain_electrothermal_simulation":"DO NOT LAUNCH",
            "new_synthetic_scalar_benchmarks":"PAUSE",
            "next_action":"Preserve Gate B and commission strictly scoped raw-cut/geometry/trace audit with actual previous coupon, plus evidence-backed 430-domain material and contact-law assignment."
        },
        "source_SHA256":{str(p.relative_to(ROOT)):digest(p)
                         for p in (R3,OLD,B,MAT,R38,R39,R317,SRC_EVIDENCE)}
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,help="Optional JSON receipt destination")
    args=ap.parse_args()
    result=audit()
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        assert not args.out.exists(), "Refuse to overwrite existing science receipt"
        args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "domains":result["physical_input_population"]["CAD_domains"],
        "unreleased_laws":result["physical_input_population"]["volume_law_status"],
        "unreleased_faces":result["physical_input_population"]["face_law_status"],
        "original_gate_B_worst_cut":result["original_gate_B"]["worst_fine_raw_current_cut_relative_error"],
        "next_action":result["readiness_decisions"]["next_action"]},indent=2))

if __name__=="__main__":
    main()
