"""Supplemental ACTUAL tetra-face connectivity proof, including inside each body.

Aggregating by material tag alone could hide disconnected fragments with one ID.
This audit proves that no such fragment exists and that both conductor/thermal
assemblies are face-connected; point/edge-only contact cannot satisfy it.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from .fem_g2a import mesh_adjacency


def connectivity(cells, bodies, conductor_ids):
    count=len(cells)
    same=np.arange(count);electric=np.arange(count);thermal=np.arange(count)
    def root(parent,x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=int(parent[x])
        return x
    def union(parent,a,b):
        ra,rb=root(parent,a),root(parent,b)
        if ra!=rb:parent[rb]=ra
    conductor=np.isin(bodies,list(conductor_ids))
    for adjacent in mesh_adjacency(cells).values():
        if len(adjacent)>2:raise ValueError("Nonmanifold tetra face")
        if len(adjacent)!=2:continue
        a,b=adjacent
        union(thermal,a,b)
        if bodies[a]==bodies[b]:union(same,a,b)
        if conductor[a] and conductor[b]:union(electric,a,b)
    fragments={str(int(bid)):len({root(same,int(i)) for i in np.flatnonzero(bodies==bid)}) for bid in np.unique(bodies)}
    if any(n!=1 for n in fragments.values()):raise ValueError("A physical body contains disconnected tetra fragments")
    electrical=len({root(electric,int(i)) for i in np.flatnonzero(conductor)})
    heat=len({root(thermal,i) for i in range(count)})
    if electrical!=1:raise ValueError("Actual conductor tetrahedra are disconnected")
    if heat!=1:raise ValueError("Actual solid thermal assembly is disconnected")
    return {"passed":True,"conductor_tetra_components":electrical,"thermal_tetra_components":heat,
            "per_body_tetra_components":fragments,"point_edge_only_connections_accepted":False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",type=Path,default=Path("outputs/fem-g2b-two-terminal"))
    args=p.parse_args();out=args.run.resolve()
    report=json.loads((out/"summary.json").read_text())
    proofs=[]
    for result in report["convergence"]:
        mesh=Path(result["mesh_path"])
        m=json.loads((mesh/"manifest.json").read_text());data=np.load(mesh/"mesh.npz")
        cid={b["id"] for b in m["bodies"] if b["material"]!="Alumina"}
        proof=connectivity(data["cells"],data["bodies"],cid)
        proof["mesh_path"]=str(mesh);proof["mesh_npz_sha256"]=hashlib.sha256((mesh/"mesh.npz").read_bytes()).hexdigest()
        proofs.append(proof)
        (mesh/"tetra_connectivity.json").write_text(json.dumps(proof,indent=2)+"\n")
    report["actual_tetra_connectivity"]=proofs
    report["verification"]["checks"]["every_material_domain_face_connected"]=all(r["passed"] for r in proofs)
    report["verification"]["checks"]["actual_conductor_and_thermal_tetra_components_one"]=all(r["conductor_tetra_components"]==r["thermal_tetra_components"]==1 for r in proofs)
    report["verification"]["passed"]=all(report["verification"]["checks"].values())
    root=Path(__file__).resolve().parents[1]
    report["supplemental_verification_source_sha256"]={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in (Path(__file__).resolve(),root/"tests/test_fem_g2b_connectivity.py")}
    (out/"summary.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(f"Actual tetra-face proof passed on {len(proofs)} meshes: each domain connected, one conductor and thermal component")


if __name__=="__main__":main()
