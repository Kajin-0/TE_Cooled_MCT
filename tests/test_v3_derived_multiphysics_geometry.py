"""Strict no-PDE acceptance and negative tests for actual derived V3 BREP."""
import copy,json,math
from pathlib import Path
import pytest
from tecooledmct.v3_analysis_geometry_integrity import validate

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/v3_derived_multiphysics_20261103"
SOURCE=ROOT/"data/synthetic_v3_assembly_20261102/source_final/design.json"

def load():
    return (
      json.loads(SOURCE.read_text()),
      json.loads((DATA/"face_ownership.json").read_text()),
      json.loads((DATA/"conformal_audit.json").read_text()),
      json.loads((DATA/"design_plan.json").read_text()),
      json.loads((DATA/"meshes/tec_meshability.json").read_text()),
      json.loads((DATA/"meshes/gas_meshability.json").read_text()),
    )

def test_geometry_acceptance_no_pde():
    assert validate(*load())["status"].startswith("PASS PHYSICAL")

@pytest.mark.parametrize("failure",[
    "drop_face","duplicate_face","open_gas","cross_net","wrong_pin",
    "missing_contact","wrong_stage","bad_material","failed_mesh","bad_volume",
    "composite_material_fallback","contact_area_drift",
])
def test_corrupted_geometry_registries_fail(failure):
    values=list(load())
    src,registry,conformal,plan,tec,gas=values
    if failure=="drop_face":
        registry["interface_records"].pop()
    elif failure=="duplicate_face":
        registry["interface_records"][1]["face_tag"]=registry["interface_records"][0]["face_tag"]
    elif failure=="open_gas":
        q=next(q for q in registry["interface_records"] if q["interface_class"]=="GAS_SOLID")
        q["owners"]=q["owners"][:1]
    elif failure=="cross_net":
        q=next(q for q in registry["interface_records"] if q["interface_class"]=="SOLID_SOLID")
        # Deliberate different-net face corruption: independent ownership must reject it.
        q["owners"]=[{"volume_tag":registry["domain_metadata"]["net0_plane0.500_Cu"]["tag"],
                      "source_name":"net0_plane0.500_Cu","signed_outward":1},
                     {"volume_tag":registry["domain_metadata"]["net88_plane0.500_Cu"]["tag"],
                      "source_name":"net88_plane0.500_Cu","signed_outward":-1}]
    elif failure=="wrong_pin":
        q=next(q for q in registry["interface_records"]
               if q["electrical_condition"]=="ELECTRICAL_TERMINAL_PIN9")
        q["electrical_condition"]="ELECTRICAL_TERMINAL_PIN1"
    elif failure=="missing_contact":
        registry["contact_sources"].pop()
    elif failure=="wrong_stage":
        registry["domain_metadata"]["leg0_N"]["stage"]=2
    elif failure=="bad_material":
        registry["domain_metadata"]["leg0_N"]["source_materials"]=["Cu"]
    elif failure=="composite_material_fallback":
        registry["domain_metadata"]["net0_plane0.500_Cu"]["material"]="Cu"
    elif failure=="contact_area_drift":
        registry["contact_sources"][0]["shared_area_m2"]*=1.01
    elif failure=="failed_mesh":
        gas["status"]="FAIL"
    elif failure=="bad_volume":
        conformal["preservation_max_relative_volume_error"]=.015
    with pytest.raises(ValueError):
        validate(*values)

def test_effective_film_preserves_original_stack_areas_and_thickness():
    src,_,_,plan,_,_=load()
    original={x["name"]:x for x in src["bodies"]}
    netgroups={k:v for k,v in plan["reductions"].items() if k.startswith("net")}
    assert len(netgroups)>80
    for key,item in netgroups.items():
        thickness=sum(row["thickness_mm"] for row in item["layers"])
        assert math.isclose(thickness,.015,abs_tol=1e-9)
        original_volume=sum(original[n]["volume_mm3"] for n in item["physical_sources"])
        kept=original[item["retained_name"]]["volume_mm3"]
        scale=plan["changed_geometric_envelope"][item["retained_name"]]["scale"]
        assert abs(kept*scale/original_volume-1)<1e-5
        assert {x["material"] for x in item["layers"]}=={"Ti","TiW","Cu","Ni","Au"}
    assert set(plan["reductions"]) >= {"underside","cold_finish","header_finish"}

def test_analytic_thin_stack_equivalence_control():
    # Deliberately synthetic coefficients test algebra; not device material claims.
    t=[75e-9,50e-9,13.625e-6,1e-6,.25e-6]
    sigma=[2e6,1e6,5e7,1e7,3e7]
    L,w=1e-3,.30e-3
    sheet=sum(a*b for a,b in zip(t,sigma))
    ideal_R=L/(w*sheet)
    by_strips=1/sum(w*a*b/L for a,b in zip(t,sigma))
    assert math.isclose(ideal_R,by_strips,rel_tol=1e-13)
    normal_specific=sum(a/b for a,b in zip(t,sigma))
    area=w*L
    through_R=normal_specific/area
    series_R=sum(a/(b*area) for a,b in zip(t,sigma))
    assert math.isclose(through_R,series_R,rel_tol=1e-13)
    assert through_R>0

def test_immutable_original_step_rev3_hashes():
    import hashlib
    _,_,_,plan,_,_=load()
    for path,expected in plan["immutable_input_sha256"].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected
