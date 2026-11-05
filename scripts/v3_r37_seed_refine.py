#!/usr/bin/env python3
"""R3.7b region-seed clearance refinement; preserve PLC nodes/facets byte-identically."""
from pathlib import Path
import hashlib,json,math,time
import gmsh,numpy as np

ROOT=Path("/work")
SRC=ROOT/"data/v3_r32_global_surface_20261103/source_metadata.json"
R=ROOT/"data/v3_r37_plc_preflight_20261105/attempt01"
OUT=ROOT/"data/v3_r37_plc_preflight_20261105/seed_refined_01"
if OUT.exists():raise RuntimeError("Existing seed refinement: no overwrite")
OUT.mkdir(parents=True)
source=json.loads(SRC.read_text())
old=json.loads((R/"region_seeds.json").read_text())
clear=json.loads((R/"seed_clearances.json").read_text())
critical=[k for k,v in clear.items() if v["nearest_CAD_face_distance_mm"] < .0005]
assert len(critical)==6,critical
start=time.monotonic()
gmsh.initialize()
gmsh.option.setNumber("General.Terminal",0)
gmsh.option.setString("Geometry.OCCTargetUnit","MM")
gmsh.model.occ.importShapes(str(ROOT/"data/v3_analysis_r3_20261103/geometry_restored/R3_conformal_mm.brep"))
gmsh.model.occ.synchronize()
owners={}
bbox={}
for name,tag in source["domain_id_map"].items():
 tag=int(tag)
 owners[tag]=[int(k) for k,q in source["faces"].items() if tag in q["owner_volume_ids"]]
 bbox[tag]=gmsh.model.getBoundingBox(3,tag)
def inside_unique(p,tag):
 p=p.tolist()
 if not gmsh.model.isInside(3,tag,p,False):return False
 for other,b in bbox.items():
  if other==tag:continue
  if any(p[i]<b[i]-1e-7 or p[i]>b[i+3]+1e-7 for i in range(3)):continue
  if gmsh.model.isInside(3,other,p,False):return False
 return True
def measure(p,tag):
 m=math.inf;face=-1
 for f in owners[tag]:
  closest,_=gmsh.model.getClosestPoint(2,f,p.tolist())
  a=np.asarray(closest,dtype=float).reshape(-1,3)[0]
  d=float(np.linalg.norm(p-a))
  if d<m:m=d;face=f
 return m,face
report={}
new={k:dict(v) for k,v in old.items()}
for name in critical:
 tag=old[name]["volume_id"];p=np.asarray(old[name]["xyz_mm"],float)
 dist,nearface=measure(p,tag)
 closest,_=gmsh.model.getClosestPoint(2,nearface,p.tolist())
 closest=np.asarray(closest,float).reshape(-1,3)[0]
 direction=p-closest;norm=np.linalg.norm(direction)
 direction=direction/norm
 best=(dist,p,nearface)
 for length in (.0002,.00035,.0005,.0007,.001,.0015,.002,.003,.004,.006,.008,.012,.02,.03,.05,.08):
  candidate=closest+direction*length
  if not inside_unique(candidate,tag):continue
  actual,face=measure(candidate,tag)
  if actual>best[0]:best=(actual,candidate.copy(),face)
  if actual>=.0005:break
 if best[0]<.0005:
  for scale in (.0005,.001,.002,.004,.008,.015,.03):
   for axis in range(3):
    for sign in (-1,1):
     candidate=p.copy();candidate[axis]+=sign*scale
     if not inside_unique(candidate,tag):continue
     actual,face=measure(candidate,tag)
     if actual>best[0]:best=(actual,candidate.copy(),face)
     if actual>=.0005:break
    if best[0]>=.0005:break
   if best[0]>=.0005:break
 report[name]={"original_clearance_mm":dist,"refined_clearance_mm":best[0],
  "original_xyz_mm":p.tolist(),"refined_xyz_mm":best[1].tolist(),
  "closest_CAD_face":best[2],"threshold_pass":best[0]>=.0005}
 new[name]["xyz_mm"]=best[1].tolist()
 new[name]["method"]="clearance_refined_inside_unique_CAD"
 print(name,round(dist,8),"->",round(best[0],8),"PASS",best[0]>=.0005,flush=True)

# Output derivation only, never modifying original 19 MB PLC.
original=R/"R37_430_domains_surface.poly"
target=OUT/"R37_430_domains_surface_seed_refined.poly"
with original.open() as src,target.open("w") as dest:
 header=src.readline();n=int(header.split()[0]);dest.write(header)
 for i in range(n):dest.write(src.readline())
 facetheader=src.readline();f=int(facetheader.split()[0]);dest.write(facetheader)
 assert f==320522
 for i in range(f*2):dest.write(src.readline())
 holes=src.readline();assert holes.strip()=="0";dest.write(holes)
 seedheader=src.readline();assert int(seedheader)==430;dest.write(seedheader)
 mapping={int(v["volume_id"]):v for v in new.values()}
 for i in range(430):
  line=src.readline().split()
  vol=int(line[0])
  v=mapping[vol];x,y,z=v["xyz_mm"]
  dest.write(f"{vol} {x:.17g} {y:.17g} {z:.17g} {vol} -1\n")
 assert not src.read().strip()
assert target.stat().st_size>0
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={"status":"PASS SIX REGION SEEDS CLEARANCE" if all(x["threshold_pass"] for x in report.values()) else "STOP: SOME SEEDS BELOW 0.5 UM CLEARANCE",
  "source_SHA256":digest(original),"output_SHA256":digest(target),
  "source_node_facets_unchanged":True,
  "region_seeds":430,"refined":report,"threshold_clearance_mm":.0005,
  "no_meshing":True,"PDE":False,"elapsed_seconds":time.monotonic()-start}
(OUT/"region_seeds.json").write_text(json.dumps(new,indent=2)+"\n")
(OUT/"result.json").write_text(json.dumps(result,indent=2)+"\n")
print("FINAL",result["status"],"seconds",round(result["elapsed_seconds"],3),flush=True)
gmsh.finalize()
