"""True OCC surface-mesh 3D overview of selected derived BREP physical bodies."""
import argparse,json,time
from pathlib import Path
import gmsh,numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def main(brep,registry,out):
    if out.exists():raise ValueError("output already exists")
    out.mkdir(parents=True)
    start=time.monotonic()
    r=json.loads(registry.read_text())
    lookup=r["source_to_analysis_volume"]
    groups={}
    for name,vid in lookup.items():
        if name.startswith("ceramic"):family="Alumina"
        elif name.startswith("leg") and name.endswith("_P"):family="P legs"
        elif name.startswith("leg") and name.endswith("_N"):family="N legs"
        elif name.startswith("formed_tab"):family="Formed Cu tabs"
        elif name.startswith("TEC_lead"):family="TEC leads"
        elif name=="VIGO_reference_header":family="Kovar header"
        elif name.startswith("pin") and name[3:].isdigit():family="Pins"
        elif name.startswith(("p_HgCdTe","sapphire_carrier","die_attach","carrier_attach")):family="Detector and carrier"
        else:continue
        groups[int(vid)]=family
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal",0)
    gmsh.option.setString("Geometry.OCCTargetUnit","MM")
    gmsh.option.setNumber("General.NumThreads",4)
    try:
        occ=gmsh.model.occ
        occ.importShapes(str(brep));occ.synchronize()
        occ.remove([(3,t) for _,t in gmsh.model.getEntities(3) if t not in groups],recursive=True)
        occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin",.07)
        gmsh.option.setNumber("Mesh.MeshSizeMax",.40)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints",0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary",0)
        gmsh.model.mesh.generate(2)
        nodeids,pts,_=gmsh.model.mesh.getNodes()
        xyz=np.asarray(pts).reshape(-1,3)
        ids={int(t):i for i,t in enumerate(nodeids)}
        samples={}
        ntri=0
        for volume,cat in groups.items():
            fs=gmsh.model.getBoundary([(3,volume)],combined=False,oriented=False,recursive=False)
            for _,f in fs:
                kinds,_,arr=gmsh.model.mesh.getElements(2,f)
                if 2 not in kinds:continue
                tr=np.asarray(arr[list(kinds).index(2)],dtype=np.int64).reshape(-1,3)
                tri=np.array([[ids[int(k)] for k in row] for row in tr],dtype=np.int64)
                samples.setdefault(cat,[]).append(tri)
                ntri+=len(tri)
        colors={"Alumina":"#e0e8f0","P legs":"#d56e3b","N legs":"#2b6798",
                "Formed Cu tabs":"#f0a832","TEC leads":"#d2a05e",
                "Kovar header":"#7891a0","Pins":"#acb6c0",
                "Detector and carrier":"#7952a5"}
        fig=plt.figure(figsize=(12,10),dpi=155)
        ax=fig.add_subplot(111,projection="3d",computed_zorder=False)
        for cat,parts in samples.items():
            faces=np.concatenate(parts)
            if len(faces)>14000:
                faces=faces[np.linspace(0,len(faces)-1,14000,dtype=int)]
            coll=Poly3DCollection(xyz[faces],linewidths=.025,
                                  edgecolors=(.12,.18,.21,.12),alpha=.86)
            coll.set_facecolor(colors[cat])
            ax.add_collection3d(coll)
        bounds=np.array([xyz.min(axis=0),xyz.max(axis=0)])
        ax.set_xlim(-8,8);ax.set_ylim(-8,8);ax.set_zlim(-13,10)
        ax.set_box_aspect((16,16,23))
        ax.view_init(elev=23,azim=-68)
        ax.set(xlabel="X (mm)",ylabel="Y (mm)",zlabel="Z (mm)",
               title="V3 analysis BREP — physical source-derived cutaway")
        fig.text(.07,.07,"Cutaway intentionally omits cap and gas surfaces; exact CAD-derived surface tessellation",fontsize=10)
        fig.tight_layout()
        fig.savefig(out/"analysis_overview.png",bbox_inches="tight")
        plt.close(fig)
        (out/"overview.json").write_text(json.dumps({"status":"PASS OCC-BASED SURFACE MESH",
          "selected_source_volumes":len(groups),"triangles":ntri,
          "categories":{k:sum(len(x) for x in v) for k,v in samples.items()},
          "seconds":time.monotonic()-start,"note":"not global tetrahedral mesh or PDE"},indent=2)+"\n")
        print("OVERVIEW",len(groups),"bodies",ntri,"tris",flush=True)
    finally:gmsh.finalize()

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--brep",type=Path,required=True)
 p.add_argument("--face",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();main(a.brep,a.face,a.out)
