"""Independent saved-record V3 derived geometry integrity checks; no CAD/mesh/PDE."""
from collections import Counter
import math

EXPECTED_TERMINALS={
    "ELECTRICAL_TERMINAL_PIN1","ELECTRICAL_TERMINAL_PIN9",
    "ELECTRICAL_TERMINAL_PIN7","ELECTRICAL_TERMINAL_PIN8",
}

def _req(cond, message):
    if not cond: raise ValueError(message)

def validate(source, registry, conformal, design, tec, gas):
    names={x["name"]:x for x in source["bodies"]}
    _req(source["body_count"]==824 and len(names)==824,"frozen physical source incomplete")
    _req(len(source["legs"])==88,"incorrect leg count")
    edges=[(x["hot_node"],x["cold_node"]) for x in source["legs"]]
    degrees=Counter(n for a,b in edges for n in (a,b))
    _req(set(degrees)==set(range(89)) and degrees[0]==degrees[88]==1 and
         all(degrees[k]==2 for k in range(1,88)),"88-leg net chain failed")
    _req([x["polarity"] for x in source["legs"]]==
         ["N" if k%2==0 else "P" for k in range(88)],"leg polarity invalid")
    _req(registry["volume_count"]==438 and len(registry["domain_metadata"])==438,
         "analysis volume mismatch")
    _req(len(registry["source_body_names"])==824 and
         set(registry["source_body_names"])==set(names),"source correspondence failed")
    _req(len(registry["removed_to_retained"])==824,"reduction loses source identities")
    material_ids=set(names)
    groups=registry["domain_metadata"]
    ids=[x["tag"] for x in groups.values()]
    _req(set(ids)==set(range(1,439)),"domain IDs not bijective")
    for name,info in groups.items():
        if name=="CAVITY_GAS": continue
        _req(info["source_names"] and all(n in material_ids for n in info["source_names"]),
             "domain material origins missing")
        _req(set(info["source_materials"])=={names[n]["material"] for n in info["source_names"]},
             "material identity mismatch")
        composite=len(info["source_names"])>1
        if composite:
            _req(info["material"]=="COMPOSITE_MULTILAYER" and
                 info["constitutive_assignment"]=="REQUIRES_EFFECTIVE_TENSOR_AND_INTERFACE_LAW" and
                 {x["material"] for x in info["layer_stack"]}==set(info["source_materials"]),
                 "composite silently classified as a homogeneous material")
            _req(info["retained_source_material"]==names[name]["material"],
                 "retained composite physical-source material mismatch")
        else:
            _req(info["material"]==names[name]["material"] and
                 info["constitutive_assignment"]=="SOURCE_MATERIAL_UNQUALIFIED" and
                 info["layer_stack"] is None,"single material classification mismatch")
        if info["material"] in ("P","N"):
            idx=int(name[3:].split("_")[0]) if name.startswith("leg") else -1
            _req(0<=idx<88 and info["stage"]==source["legs"][idx]["stage"] and
                 name==f"leg{idx}_{source['legs'][idx]['polarity']}",
                 "thermoelectric stage fallback or material misclassification")
        else:
            _req(info["stage"] is None,"unexpected TE stage classification")
    _req(registry["stage_leg_counts"]=={"0":58,"1":22,"2":8},
         "3-stage topology altered")
    faces=registry["interface_records"]
    _req(len(faces)==registry["face_count"]==2456,"unowned analysis faces")
    ids=[q["face_tag"] for q in faces]
    _req(len(ids)==len(set(ids)) and min(ids)>=1,"duplicate face identity")
    counts=Counter()
    gasfaces=0
    contacts=set()
    terminals=Counter()
    external=0
    for f in faces:
        owner=f["owners"]
        _req(len(owner) in (1,2) and len({i["volume_tag"] for i in owner})==len(owner),
             "contradictory domain ownership")
        _req(all(i["source_name"] in groups and
                 i["volume_tag"]==groups[i["source_name"]]["tag"] for i in owner),
             "incorrect volume-source mapping")
        _req(math.isfinite(f["area_m2"]) and f["area_m2"]>0,"face area vanished")
        _req(f["port_id"]!="UNMAPPED","unmapped thermal port")
        _req(f.get("electrical_material_category") not in (None,""),
             "missing electrical material category")
        _req(f.get("structural_condition") not in (None,""),
             "missing structural boundary classification")
        names_of_face={i["source_name"] for i in owner}
        if len(owner)==2:
            _req(sum(i["signed_outward"] for i in owner)==0,
                 "paired face normals not opposing")
            if "CAVITY_GAS" in names_of_face:
                _req(f["interface_class"]=="GAS_SOLID","gas domain interface incorrectly classified")
                gasfaces+=1
            else:
                _req(f["interface_class"]=="SOLID_SOLID","solid interface incorrectly classified")
                a,b=[names[z] for z in names_of_face]
                g,h=a.get("group"),b.get("group")
                _req(not(isinstance(g,int) and isinstance(h,int) and g!=h),
                     "unintended cross-net metallic short")
                _req(not ((str(g).startswith("DET") and isinstance(h,int)) or
                          (str(h).startswith("DET") and isinstance(g,int))),
                     "detector/TEC direct short")
                contacts.add(tuple(sorted(names_of_face)))
        else:
            _req(f["interface_class"]=="EXTERIOR","external port misclassified")
            external+=1
        if f["electrical_condition"].startswith("ELECTRICAL_TERMINAL_"):
            _req(len(owner)==1 and owner[0]["source_name"] in
                 ("pin1","pin7","pin8","pin9"),"terminal bound to wrong solid")
            terminals[f["electrical_condition"]]+=1
        counts[f["interface_class"]]+=1
    _req(counts==Counter({"GAS_SOLID":1848,"SOLID_SOLID":565,"EXTERIOR":43}),
         "face classification coverage changed")
    _req(gasfaces==1848 and external==43 and
         registry["gas_faces_without_solid_owner"]==0,
         "gas boundary leak or missing boundary")
    _req(set(terminals)==EXPECTED_TERMINALS and all(v==1 for v in terminals.values()),
         "incorrect terminal count or pin assignment")
    _req(registry["gas_connected_component_count"]==1 and
         1200<registry["gas_volume_mm3"]<1250,
         "gas topology/volume invalid")
    _req(len(registry["contact_sources"])==378 and
         not registry["missing_declared_contacts"],"source contacts missing")
    for q in registry["contact_sources"]:
        _req(q.get("retained_pair") is not None and
             tuple(sorted(q["retained_pair"])) in contacts,
             "declared contact not verified by finite-area shared face")
        _req(q["shared_area_m2"]>0 and q["source_witness_area_m2"]>0,
             "contact area not positive")
        _req(abs(q["shared_area_m2"]/q["source_witness_area_m2"]-1)<1e-6,
             "finite source contact area not preserved")
    _req(conformal["final_volume_count"]==438 and
         conformal["final_face_count"]==2456 and
         conformal["nonmanifold_face_count"]==0 and
         conformal["preservation_max_relative_volume_error"]<1e-6,
         "conformalized STEP source volume identity failed")
    _req(design["reduced_solid_count"]==437 and design["gas_component_count"]==1,
         "reduced source geometry not complete")
    _req(len(design["reductions"])>=95,"thin material reduction missing")
    for f in ("tec","gas"):
        r=tec if f=="tec" else gas
        _req(r["status"].startswith("PASS LOCAL 3D MESH") and
             0<r["tets"]<150000 and all(v["volume_error_relative"]<.01 for v in r["domains"].values()),
             "bounded 3D mesh control failed")
    return {"status":"PASS PHYSICAL/DERIVED GEOMETRY INTEGRITY; PDE NOT RUN",
            "analysis_volumes":438,"analysis_faces":2456,
            "native_gas_connected":1,"gas_interface_faces":1848,
            "declared_contacts":378,"electrical_pins":sorted(terminals),
            "tec_mesh_tets":tec["tets"],"gas_patch_tets":gas["tets"],
            "physical_solids":824,"original_electrical_Gate_B":"STOP",
            "physics_laws":"NOT QUALIFIED"}
