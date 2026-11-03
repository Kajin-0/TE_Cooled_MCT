"""Full boundary-owner and face-interface registry for conformal V3 analysis BREP.

No PDE, no meshing. Converts OCC exact shared faces into named SI interfaces;
fails on missing source body, wrong material/stage, nonmanifold/unpaired face,
duplicate boundary ownership, missing declared contacts, or gas leakage.
"""
import argparse, json, hashlib, math, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import gmsh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v3_analysis_brep_builder import source_plan, ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+"\n")
def name_map(src,ret,remove,reductions):
 m={b["name"]:b["name"] for b in ret}
 for k,q in reductions.items():
  dest=q["retained_name"]
  if dest is None:
   dest=("hot_mount_In52Sn48" if k in ("underside","header_finish") else "ceramic3" if k=="cold_finish" else None)
  if dest is None:raise ValueError("Unknown reduction "+k)
  for n in q["physical_sources"]:
   m[n]=dest
 if len(m)!=824:raise ValueError("source mapping incomplete "+str(len(m)))
 return m

def owner_port(name):
 if name.startswith("pin") and re.fullmatch(r"pin[1-9]",name):
  return "PIN_"+name[3:]
 if name=="VIGO_reference_header" or name=="hot_mount_In52Sn48":
  return "HEADER_ENV"
 if name.startswith("cap"):return "CASE_ENV"
 if name=="window":return "WINDOW_ENV"
 if re.fullmatch(r"glass[1-9]",name):return "FEEDTHROUGH_ENV_"+name[5:]
 return None

def main(brep,conformal,derived,out):
 if out.exists():raise ValueError("immutable output path")
 out.mkdir(parents=True)
 result={"status":"PENDING","source_BREP_sha256":sha(brep)}
 gmsh.initialize();gmsh.option.setNumber("General.Terminal",0);gmsh.option.setString("Geometry.OCCTargetUnit","MM")
 try:
  src,physical_tags,ret,remove,enlarge,reductions=source_plan()
  imported=sorted(ret,key=lambda b:physical_tags[b["name"]])
  audit=json.loads(conformal.read_text())
  assert audit["status"].startswith("FRAGMENT COMPLETE")
  assert audit["brep_sha256"]==sha(brep)
  assert len(imported)==len(ret) and len(imported)>400
  gas_tag=len(imported)+1
  gmsh.model.occ.importShapes(str(brep));gmsh.model.occ.synchronize()
  occ=gmsh.model.occ
  names={i:b["name"] for i,b in enumerate(imported,1)}
  names[gas_tag]="CAVITY_GAS"
  byname={b["name"]:b for b in ret}
  stages={f"leg{x['index']}_{x['polarity']}":x["stage"] for x in src["legs"]}
  assert len(stages)==88 and all(x in (0,1,2) for x in stages.values())
  for b in imported:
   if b["material"] in ("P","N"):
    if b["name"] not in stages:raise ValueError("unknown P/N stage for "+b["name"])
   if b["name"].startswith("leg") and b["name"] not in stages:
    raise ValueError("silently unknown leg "+b["name"])
  for idx,b in enumerate(imported,1):
   v=occ.getMass(3,idx)
   expected=b["volume_mm3"]*(enlarge[b["name"]]["scale"] if b["name"] in enlarge else 1)
   if abs(v/expected-1)>1e-6:raise ValueError("volume ID mismatch "+b["name"])
  gas=occ.getMass(3,gas_tag)
  assert abs(gas-audit["source_descendants"][str(gas_tag)]["mass_mm3"])<1e-6
  ns={b["name"]:b for b in src["bodies"]}
  mapped=name_map(src,ret,remove,reductions)
  named_indices={v:k for k,v in names.items()}
  owners={};signed={}
  for vid in names:
   bb=gmsh.model.getBoundary([(3,vid)],oriented=True,recursive=False)
   seen=set()
   for dim,t in bb:
    assert dim==2
    f=abs(t)
    if f in seen:raise ValueError("duplicate face on one domain")
    seen.add(f)
    owners.setdefault(f,[]).append(vid)
    signed[(vid,f)]=int(math.copysign(1,t))
  faces=set(t for d,t in gmsh.model.getEntities(2))
  if faces!=set(owners):raise ValueError("missing/excess face ownership")
  for f,pair in owners.items():
   if len(pair) not in (1,2):raise ValueError("nonmanifold face "+str(f))
   if len(pair)==2 and signed[(pair[0],f)]+signed[(pair[1],f)]!=0:
    raise ValueError("internal normal orientation disagreement "+str(f))
   adjacency=set(map(int,gmsh.model.getAdjacencies(2,f)[0]))
   if adjacency!=set(pair):raise ValueError("OCC face adjacency mismatch "+str(f))
  facepairs=defaultdict(list)
  for f,pair in owners.items():
   if len(pair)==2:
    facepairs[tuple(sorted(pair))].append(f)
  interface_records=[]
  boundary_records=[]
  ftype=Counter()
  external=Counter()
  shared=Counter()
  anomalies=[]
  for f in sorted(faces):
   pair=owners[f]
   involved=[names[i] for i in pair]
   area=occ.getMass(2,f)
   if not math.isfinite(area) or area<=1e-12:raise ValueError("zero face area "+str(f))
   bbox=occ.getBoundingBox(2,f)
   center=occ.getCenterOfMass(2,f)
   if gas_tag in pair:
    if len(pair)!=2:raise ValueError("gas boundary has no physical closure at "+str(f))
    s=names[next(i for i in pair if i!=gas_tag)]
    condition="GAS_SOLID"
    thermal="GAS_CONDUCTION_PLUS_SEPARATE_RADIATION_POSSIBLE"
    electric="INSULATING_GAS_BOUNDARY"
    radiation="CANDIDATE_RADIATING_SURFACE"
    optical="MCT_ABSORPTION_SOURCE_CANDIDATE" if s=="p_HgCdTe_photoconductor" else ("WINDOW_TRANSMISSION_CANDIDATE" if s=="window" else "NONE")
    port="GAS"
    shared[s]+=1
   elif len(pair)==2:
    condition="SOLID_SOLID"
    s1,s2=involved
    thermal="FINITE_CONTACT_OR_CONTINUOUS_INTERFACE_UNQUALIFIED"
    electric="INTERFACE_LAW_REQUIRED_OR_ELECTRICALLY_INSULATED"
    radiation="NONE"
    optical="NONE"
    port="INTERNAL"
   else:
    condition="EXTERIOR"
    n=involved[0]
    port=owner_port(n)
    if port is None:
     anomalies.append(dict(face=f,owner=n,reason="unmapped external boundary"))
     port="UNMAPPED"
    thermal="EXTERNAL_HEAT_TRANSFER_BC_UNQUALIFIED"
    radiation="EXTERIOR_RADIATION_CANDIDATE" if n.startswith("cap") or n=="window" else "NONE"
    optical="WINDOW_EXTERNAL_ILLUMINATION" if n=="window" else "NONE"
    electric="INSULATED_EXTERIOR"
    if n in ("pin1","pin9","pin7","pin8") and abs(bbox[2]+12.7)<1e-4 and abs(bbox[5]+12.7)<1e-4:
     electric="ELECTRICAL_TERMINAL_"+n.upper()
    external[n]+=1
   ftype[condition]+=1
   solid_bodies=[byname[n] for n in involved if n!="CAVITY_GAS"]
   insulating={"Al2O3","Glass","Sapphire","EP29LPSP","Polyimide_candidate","ZnSe_candidate"}
   if condition=="SOLID_SOLID":
    electrical_category=("DIELECTRIC_INSULATED" if any(b["material"] in insulating for b in solid_bodies)
                         else "CONTACT_OR_CONTINUOUS_CONDUCTIVE_LAW_REQUIRED")
    structural="BONDED_OR_COMPLIANT_INTERFACE_NOT_MECHANICALLY_QUALIFIED"
   elif condition=="GAS_SOLID":
    electrical_category="GAS_ELECTRICAL_INSULATION"
    structural="GAS_PRESSURE_LOAD_SURFACE_UNQUALIFIED"
   else:
    electrical_category="TERMINAL" if electric.startswith("ELECTRICAL_TERMINAL") else "EXPOSED_INSULATED_OR_UNTERMINATED"
    structural="EXTERNAL_TRACTION_OR_HEADER_SUPPORT_CONSTRAINT_NOT_ASSIGNED"
   ceramic_ports=[b["name"].upper() for b in solid_bodies if b["name"] in ("ceramic0","ceramic1","ceramic2","ceramic3")]
   thermo_contact=any(b["material"] in ("P","N") for b in solid_bodies)
   entry=dict(face_tag=f, owners=[dict(volume_tag=i, source_name=names[i], signed_outward=signed[(i,f)]) for i in pair],
              area_m2=area*1e-6, center_m=[v*.001 for v in center],bbox_m=[v*.001 for v in bbox],
              interface_class=condition,
              thermal_condition=thermal, electrical_condition=electric,
              radiation_condition=radiation, optical_condition=optical,
              port_id=port, ceramic_stage_ports=ceramic_ports,
              electrical_material_category=electrical_category,
              structural_condition=structural,
              thermoelectric_interface="P_N_CONTACT_NEEDS_PELTIER_TRANSPORT_LAW" if thermo_contact and condition=="SOLID_SOLID" else "NONE",
              source_cad="frozen V3 R1 physical STEP or explicit synthetic gas closure",
              magnetic_condition="NOT_SPECIFIED",
              material_law_status="NOT QUALIFIED")
   interface_records.append(entry)
   if condition=="EXTERIOR":boundary_records.append(entry)
  if anomalies:raise ValueError("unmapped external boundary "+str(anomalies[:12]))
  contactmap=[]
  missing=[]
  for i,c in enumerate(src["explicit_contacts"]):
   a,b=mapped[c["a"]],mapped[c["b"]]
   if a==b:
    contactmap.append(dict(id=i,source_pair=[c["a"],c["b"]],represented_as="INTERNAL_COLLAPSED_LAYER",source_witness_area_m2=c["area"]*1e-6))
    continue
   v1,v2=named_indices[a],named_indices[b]
   fs=facepairs.get(tuple(sorted((v1,v2))),[])
   if not fs:
    missing.append(dict(id=i,source=[c["a"],c["b"]],retained=[a,b]))
    continue
   physical_area=sum(occ.getMass(2,f) for f in fs)*1e-6
   if physical_area<=0:raise ValueError("contact area vanished")
   contactmap.append(dict(id=i, source_pair=[c["a"],c["b"]], retained_pair=[a,b],
                    source_witness_area_m2=c["area"]*1e-6,
                    shared_face_tags=fs,shared_area_m2=physical_area,
                    representation="FINITE_AREA_SHARED_FACE; CONTACT LAW NOT QUALIFIED"))
  print("FACES",len(faces),"classes",dict(ftype),"missing contacts",len(missing),
        "external",dict(external),flush=True)
  if missing:raise ValueError("missing intended finite contacts "+str(missing[:15]))
  actual_gas=set(f for f,pair in owners.items() if gas_tag in pair)
  if len(actual_gas)<100:raise ValueError("insufficient enclosed gas-solid interfaces")
  for ids,fs in facepairs.items():
   if gas_tag in ids:continue
   aa,bb=names[ids[0]],names[ids[1]]
   ga,gb=byname[aa].get("group"),byname[bb].get("group")
   if isinstance(ga,int) and isinstance(gb,int) and ga!=gb:
    raise ValueError("unintended different electrical net contact "+str((aa,bb)))
   if ((str(ga).startswith("DET") and isinstance(gb,int)) or
       (str(gb).startswith("DET") and isinstance(ga,int))):
    raise ValueError("detector/TEC short "+str((aa,bb)))
  # Identify non-gas exposed electrical terminals, and verify expected four pins.
  terminals=Counter(q["electrical_condition"] for q in interface_records if q["electrical_condition"].startswith("ELECTRICAL_TERMINAL_"))
  if set(terminals)!={"ELECTRICAL_TERMINAL_PIN1","ELECTRICAL_TERMINAL_PIN9","ELECTRICAL_TERMINAL_PIN7","ELECTRICAL_TERMINAL_PIN8"}:
   raise ValueError("missing electrical terminals "+str(terminals))
  known_materials={"Al2O3","P","N","SnSb","SnBi57_43","In52Sn48",
    "Au","Ni","Cu","Ti","TiW","Kovar","Kovar_pin","Glass",
    "EP29LPSP","Sapphire","pHgCdTe_PC","Au_ohmic","Steel",
    "ZnSe_candidate","Polyimide_candidate"}
  if any(b["material"] not in known_materials for b in src["bodies"]):
   raise ValueError("Unknown physical material with no constitutive assignment")
  source_by_name={b["name"]:b for b in src["bodies"]}
  per_domain={}
  for name,tag in named_indices.items():
   if name=="CAVITY_GAS":
    per_domain[name]=dict(tag=tag,material="IDEALIZED_CAVITY_GAS",
       stage=None,source_names=[],role="native connected void; no property law assigned")
    continue
   b=byname[name]
   sources=[n for n,v in mapped.items() if v==name]
   stage=stages[name] if b["material"] in ("P","N") else None
   constituents=sorted({source_by_name[n]["material"] for n in sources})
   composite=len(sources)>1
   stack=next((q for q in reductions.values() if q["retained_name"]==name),None) if composite else None
   if composite and (stack is None or {v["material"] for v in stack["layers"]}!=set(constituents)):
    raise ValueError("composite layer provenance incomplete "+name)
   per_domain[name]=dict(tag=tag,
       material="COMPOSITE_MULTILAYER" if composite else b["material"],
       retained_source_material=b["material"],stage=stage,
       source_names=sources,source_materials=constituents,
       layer_stack=stack["layers"] if composite else None,
       constitutive_assignment="REQUIRES_EFFECTIVE_TENSOR_AND_INTERFACE_LAW" if composite else "SOURCE_MATERIAL_UNQUALIFIED",
       role="effective composite with preserved source material stack" if composite else "single source material",
       physical_reduction="NO FITTED MATERIAL COEFFICIENTS")
  if len(per_domain)!=len(names) or sum(len(v["source_names"]) for v in per_domain.values())!=824:
   raise ValueError("domain-to-physical mapping not exhaustive")
  stage_counts=Counter(stages.values())
  if stage_counts!={0:58,1:22,2:8}:
   raise ValueError("unexpected 3-stage P/N allocation "+str(stage_counts))
  result.update(
   status="PASS CONFORMAL FACE OWNERSHIP / GAS CLOSURE / DECLARED CONTACTS; PDE LAWS NOT QUALIFIED",
   face_count=len(faces),volume_count=len(names),gas_connected_component_count=1,
   gas_volume_mm3=gas,
   gas_face_count=len(actual_gas),gas_faces_without_solid_owner=0,
   classes=dict(ftype), exterior_by_solid=dict(external), electrical_terminals=dict(terminals),
   interface_records=interface_records, contact_sources=contactmap, missing_declared_contacts=missing,
   domain_metadata=per_domain, stage_leg_counts=dict(stage_counts),
   source_to_analysis_volume={name:idx for idx,name in names.items()},
   source_body_names=[b["name"] for b in src["bodies"]],
   removed_to_retained=mapped, negative_checks={"missing":0,"duplicate_face":0,"nonmanifold":0,
   "missing_declared_contact":len(missing),"unknown_thermal_port":len(anomalies)},
   caveats=[
    "Gas closure is idealized: native cylindrical interior and unchanged solids, not a certified welded/hermetic package",
    "Actual manufacturing process, seal, contact coefficients, radiation and gas properties remain unqualified",
    "A mesh will need explicit physical groups; no PDE validation is claimed",
    "Solid-solid faces may include legitimate dielectric interfaces; electrical contact law must be assigned per material",
    "Original numerical electrical Gate B remains STOP; no TE/radiation/gas fields solved",
   ])
  dump(out/"face_ownership.json",result)
 except Exception as ex:
  result["status"]="FAIL";result["error"]=repr(ex)
  dump(out/"failure.json",result)
  raise
 finally:gmsh.finalize()

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--brep",type=Path,required=True);p.add_argument("--conformal",type=Path,required=True);p.add_argument("--derived",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();main(a.brep,a.conformal,a.derived,a.out)
