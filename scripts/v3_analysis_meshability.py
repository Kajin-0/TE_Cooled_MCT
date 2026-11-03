"""Mesh only small patches of the actual derived V3 BREP. No PDE solves."""
import argparse, json, time
from pathlib import Path
import gmsh
import numpy as np

def main(brep, registry, out, fixture):
    if out.exists(): raise ValueError("output exists")
    out.mkdir(parents=True)
    receipt={"status":"INCOMPLETE", "fixture":fixture}
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal",0)
    gmsh.option.setString("Geometry.OCCTargetUnit","MM")
    gmsh.option.setNumber("General.NumThreads",4)
    start=time.monotonic()
    try:
        occ=gmsh.model.occ
        occ.importShapes(str(brep))
        occ.synchronize()
        names=json.loads(registry.read_text())["source_to_analysis_volume"]
        if fixture=="tec":
            selected=["ceramic0","ceramic1","leg0_N","solder0_hot",
                      "solder0_cold","net0_plane0.500_Cu","net1_plane1.100_Cu"]
            tags=[names[n] for n in selected]
            occ.remove([(3,t) for _,t in gmsh.model.getEntities(3) if t not in tags],recursive=True)
        else:
            selected=["local_gas_patch"]
            gas=names["CAVITY_GAS"]
            occ.remove([(3,t) for _,t in gmsh.model.getEntities(3) if t!=gas],recursive=True)
            box=occ.addBox(2.9,-.65,1.65,1.4,1.30,1.20)
            solids,_=occ.intersect([(3,gas)],[(3,box)],removeObject=True,removeTool=True)
            tags=[t for d,t in solids if d==3]
            if len(tags)!=1: raise ValueError("unexpected gas patch topology")
        occ.synchronize()
        for j,(name,tag) in enumerate(zip(selected,tags),1):
            gmsh.model.addPhysicalGroup(3,[tag],j)
            gmsh.model.setPhysicalName(3,j,name)
        gmsh.option.setNumber("Mesh.MeshSizeMin",.015 if fixture=="tec" else .08)
        gmsh.option.setNumber("Mesh.MeshSizeMax",.28 if fixture=="tec" else .40)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints",0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary",0)
        gmsh.option.setNumber("Mesh.Algorithm3D",1)
        print("MESH BEGIN",fixture,flush=True)
        gmsh.model.mesh.generate(3)
        node_ids, coords, _=gmsh.model.mesh.getNodes()
        xyz=np.asarray(coords).reshape(-1,3)
        lookup={int(v):i for i,v in enumerate(node_ids)}
        total=0
        domains={}
        for name,tag in zip(selected,tags):
            kinds,_,elem=gmsh.model.mesh.getElements(3,tag)
            if 4 not in kinds:raise ValueError("not tetrahedra")
            ids=np.asarray(elem[list(kinds).index(4)],dtype=np.int64).reshape(-1,4)
            tet=xyz[np.array([[lookup[int(j)] for j in row] for row in ids])]
            v=np.abs(np.linalg.det(tet[:,1:]-tet[:,:1]))/6
            if not np.all(v>1e-18):raise ValueError("degenerate tetrahedron")
            cad=occ.getMass(3,tag)
            domains[name]={"tets":len(ids),"CAD_volume_mm3":cad,
                "mesh_volume_mm3":float(v.sum()),
                "volume_error_relative":float(abs(v.sum()/cad-1))}
            total+=len(ids)
        if total>150000:raise ValueError("mesh exceeds local 150k cap")
        surface_types,_,surface_nodes=gmsh.model.mesh.getElements(2)
        tri=np.zeros((0,3),dtype=np.int64)
        if 2 in surface_types:
            q=list(surface_types).index(2)
            tri=np.asarray(surface_nodes[q],dtype=np.int64).reshape(-1,3)
            tri=np.array([[lookup[int(j)] for j in row] for row in tri],dtype=np.int64)
        if not len(tri): raise ValueError("No boundary triangles available")
        np.savez_compressed(out/"surface_mesh.npz", points_mm=xyz,
                            triangles=tri, bounds_mm=np.array([xyz.min(0),xyz.max(0)]))
        msh=out/("local_tec.msh" if fixture=="tec" else "local_gas.msh")
        gmsh.write(str(msh))
        # Gmsh ASCII writer appends spaces after element connectivity.
        # Strip only line-ending whitespace; preserve every token and element ID.
        raw=msh.read_bytes()
        msh.write_bytes(b"\n".join(line.rstrip(b" \t\r") for line in raw.split(b"\n")))
        receipt.update(status="PASS LOCAL 3D MESH; NO PDE",tets=total,
                       nodes=len(xyz),surface_triangles=len(tri),domains=domains,
                       seconds=time.monotonic()-start)
        print("MESH PASS",fixture,total,flush=True)
    except Exception as exc:
        receipt.update(status="FAIL",error=repr(exc))
        raise
    finally:
        (out/"meshability.json").write_text(json.dumps(receipt,indent=2)+"\n")
        gmsh.finalize()

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--brep",type=Path,required=True)
    parser.add_argument("--face",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--fixture",choices=("tec","gas"),required=True)
    args=parser.parse_args()
    main(args.brep,args.face,args.out,args.fixture)
