"""Conformalize immutable derived solids and native gas by OCC fragmenting.

No original CAD edits, no mesh, no PDE. Separate trial outputs with stop conditions.
"""
import argparse,hashlib,json,time
from pathlib import Path
import gmsh

def main(src,out):
 if out.exists():raise ValueError("no overwrite")
 out.mkdir(parents=True)
 gmsh.initialize();gmsh.option.setNumber("General.Terminal",0);gmsh.option.setString("Geometry.OCCTargetUnit","MM")
 start=time.monotonic();result={"status":"INCOMPLETE","source_sha256":hashlib.sha256(src.read_bytes()).hexdigest()}
 try:
  occ=gmsh.model.occ;occ.importShapes(str(src));occ.synchronize()
  volumes=[t for _,t in gmsh.model.getEntities(3)]
  gas=[t for t in volumes if occ.getMass(3,t)>1000]
  assert len(gas)==1
  originals=[(3,t) for t in volumes if t not in gas]
  src_masses={t:occ.getMass(3,t) for t in volumes}
  print("FRAGMENT",len(originals),"gas",gas,flush=True)
  produced,mapping=occ.fragment([(3,gas[0])],originals,removeObject=True,removeTool=True)
  occ.synchronize()
  print("FRAGMENT DONE",len(produced),"seconds",time.monotonic()-start,flush=True)
  result["output_map"]=[dict(source=("GAS" if j==0 else originals[j-1][1]),
                             output_tags=[t for d,t in group if d==3]) for j,group in enumerate(mapping)]
  volumes=gmsh.model.getEntities(3)
  bysource={}
  for j,group in enumerate(mapping):
   ids=[t for d,t in group if d==3]
   mass=sum(occ.getMass(3,t) for t in ids)
   orig_tag=gas[0] if j==0 else originals[j-1][1]
   rel=abs(mass-src_masses[orig_tag])/src_masses[orig_tag]
   bysource[str(orig_tag)]={"outputs":ids,"mass_mm3":mass,"relative_volume_error":rel}
  result["preservation_max_relative_volume_error"]=max(q["relative_volume_error"] for q in bysource.values())
  result["source_descendants"]=bysource
  result["final_volume_count"]=len(volumes)
  result["final_face_count"]=len(gmsh.model.getEntities(2))
  result["face_adjacencies"]={}
  for dim,t in gmsh.model.getEntities(2):
   owners=list(map(int,gmsh.model.getAdjacencies(2,t)[0]))
   result["face_adjacencies"][str(t)]=owners
  result["unshared_face_count"]=sum(len(q)==1 for q in result["face_adjacencies"].values())
  result["shared_face_count"]=sum(len(q)==2 for q in result["face_adjacencies"].values())
  result["nonmanifold_face_count"]=sum(len(q)>2 for q in result["face_adjacencies"].values())
  if result["preservation_max_relative_volume_error"]>1e-6 or result["nonmanifold_face_count"]:
   raise ValueError("source volumes or face manifold FAIL")
  gmsh.write(str(out/"analysis_conformal_mm.brep"))
  result["brep_sha256"]=hashlib.sha256((out/"analysis_conformal_mm.brep").read_bytes()).hexdigest()
  result["status"]="FRAGMENT COMPLETE; source volumes PASS; face classification pending"
 except Exception as ex:
  result["status"]="FAIL";result["error"]=repr(ex);raise
 finally:
  result["seconds"]=time.monotonic()-start
  (out/"audit.json").write_text(json.dumps(result,indent=2)+"\n")
  gmsh.finalize()

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--src",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();main(a.src,a.out)
