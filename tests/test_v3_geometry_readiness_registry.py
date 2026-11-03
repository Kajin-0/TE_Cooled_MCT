"""No-solve checks for the frozen V3 R1 physical-to-analysis geometry registry."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/v3_geometry_readiness_20261103"
SOURCE = ROOT / "data/synthetic_v3_assembly_20261102/source_final/design.json"
STEP = ROOT / "data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step"
SI = ROOT / "data/synthetic_v3_assembly_20261102/cad_02/si_reader.json"
REV3 = ROOT / "reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf"


def load():
    return json.loads((ART / "domain_interface_registry.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_every_824_step_body_is_linked_once_and_si_identity_is_frozen():
    r = load()
    source = json.loads(SOURCE.read_text())
    si = json.loads(SI.read_text())
    assert r["body_count"] == 824 == source["body_count"] == len(si["records"])
    assert len(r["parts"]) == 824
    assert r["input_sha256"][str(STEP.relative_to(ROOT))] == sha(STEP)
    assert r["input_sha256"][str(SOURCE.relative_to(ROOT))] == sha(SOURCE)
    assert {d["name"] for d in r["parts"]} == {b["name"] for b in source["bodies"]}
    assert {d["imported_STEP_tag"] for d in r["parts"]} == {x["tag"] for x in si["records"]}
    assert all(d["interface_laws_status"] == "NOT COMPUTATIONALLY QUALIFIED" for d in r["parts"])


def test_source_contact_witnesses_resolve_to_existing_solids():
    r = load()
    contacts = r["source_interface_witnesses"]
    assert len(contacts) == r["explicit_source_contact_count"] == 378
    names = {d["name"] for d in r["parts"]}
    assert {c["id"] for c in contacts} == set(range(378))
    assert all(c["component_a"] in names and c["component_b"] in names and
               c["source_contact_area_m2"] > 0 for c in contacts)
    assert all("NOT" in c["status"] or "geometry" in c["status"] for c in contacts)


def test_canonical_ports_and_unrepresented_gas_are_explicit():
    r = load()
    ports = {p["id"] for p in r["thermal_ports"]}
    assert {"CERAMIC0", "CERAMIC1", "CERAMIC2", "CERAMIC3",
            "HEADER", "TEC_PIN1", "TEC_PIN9", "DET_PIN7", "DET_PIN8",
            "CASE", "WINDOW", "GAS", "OPTICAL"} <= ports
    assert "NOT PRESENT" in r["proposed_analysis_representations"]["cavity"]
    assert r["electrical_terminal_assignments"]["PIN5"] == "VACANT"
    assert r["electrical_terminal_assignments"]["PIN6"] == "VACANT"


def test_tab_bend_radius_is_a_hypothesis_not_new_geometry_acceptance():
    r = load()
    variants = r["bend_radius_hypotheses"]
    assert variants[0]["neutral_radius_mm"] == .075
    assert abs(variants[0]["elementary_strain_proxy"] - .20) < 1e-12
    assert abs(variants[-1]["elementary_strain_proxy"] - .075) < 1e-12
    assert all(v["geometric_rebuild_and_fit"] == "NOT RUN" for v in variants)
    assert len(r["tab_nominal"]) == 3


def test_height_tolerance_remains_tight_and_original_pdf_is_protected():
    r = load()
    h = r["height_margin"]
    assert h["current_range_mm"] == [3.664, 3.944]
    assert abs(h["upper_reserve_mm"] - .006) < 1e-12
    assert r["input_sha256"][str(REV3.relative_to(ROOT))] == sha(REV3)
    assert r["old_electrical_Gate_B"].startswith("STOP")


def test_csv_can_be_used_for_non_solver_exploration():
    r = load()
    with (ART / "domains.csv").open() as f:
        domains = list(csv.DictReader(f))
    with (ART / "interfaces.csv").open() as f:
        contacts = list(csv.DictReader(f))
    assert len(domains) == 824 and len(contacts) == 378
    assert {int(x["source_id"]) for x in domains} == set(range(824))


def test_negative_missing_port_and_source_mapping_are_rejected_by_required_invariants():
    r = load()
    names = {d["name"] for d in r["parts"]}
    assert "pin9" in names and "pin1" in names
    altered = names - {"pin9"}
    assert altered != {b["name"] for b in json.loads(SOURCE.read_text())["bodies"]}
    ports = {p["id"] for p in r["thermal_ports"]}
    altered_ports = ports - {"CERAMIC3"}
    assert not {"CERAMIC0", "CERAMIC1", "CERAMIC2", "CERAMIC3"} <= altered_ports
