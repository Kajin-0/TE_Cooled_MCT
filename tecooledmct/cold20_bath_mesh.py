"""Conformal bath-volume edge-star refinement; the cold mesh remains EXACT."""
import argparse,itertools,json,shutil,time
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .fem_g2a import mesh_adjacency
from .geometry_complete import audit
from .cold_roi_mesh import metrics
from .fem_g1_run import execute
from .fem_g2c_mesh import verify_elmer_tetra_mapping

PLAN=ROOT/'data/cold20/bath_plan.json'
EDGES=list(itertools.combinations(range(4),2));TRIEDGES=[(0,1),(1,2),(2,0)]


def refine_stars(p,c,b,f,tags,selected):
    marked=set(tuple(sorted((int(c[i,a]),int(c[i,z])))) for i in selected for a,z in EDGES)
    tetstars={e:set() for e in marked};facestars={e:set() for e in marked}
    cells=c.tolist();bodies=b.tolist();faces=f.tolist();labels=tags.tolist();active=[True]*len(cells);factive=[True]*len(faces);points=p.tolist()
    def update(row,index,stars,edges,add):
        for a,z in edges:
            edge=tuple(sorted((row[a],row[z])))
            if edge in stars:
                if add:stars[edge].add(index)
                else:stars[edge].discard(index)
    for i,row in enumerate(cells):update(row,i,tetstars,EDGES,True)
    for i,row in enumerate(faces):update(row,i,facestars,TRIEDGES,True)
    for edge in sorted(marked):
        a,z=edge;mid=len(points);points.append(((p[a]+p[z])/2).tolist())
        for i in list(tetstars[edge]):
            row=cells[i];active[i]=False;update(row,i,tetstars,EDGES,False)
            left=row.copy();left[left.index(z)]=mid;right=row.copy();right[right.index(a)]=mid
            for child in (left,right):
                index=len(cells);cells.append(child);bodies.append(bodies[i]);active.append(True);update(child,index,tetstars,EDGES,True)
        for i in list(facestars[edge]):
            row=faces[i];factive[i]=False;update(row,i,facestars,TRIEDGES,False)
            left=row.copy();left[left.index(z)]=mid;right=row.copy();right[right.index(a)]=mid
            for child in (left,right):
                index=len(faces);faces.append(child);labels.append(labels[i]);factive.append(True);update(child,index,facestars,TRIEDGES,True)
    active=np.array(active);factive=np.array(factive)
    return np.array(points),np.array(cells)[active],np.array(bodies)[active],np.array(faces)[factive],np.array(labels)[factive],len(marked)


def build(parent,out):
    import gmsh
    if out.exists():raise ValueError('Choose a new immutable bath mesh label')
    out.mkdir(parents=True);start=time.monotonic();d=np.load(parent/'mesh.npz');m=json.loads((parent/'manifest.json').read_text());plan=json.loads(PLAN.read_text())
    oldp,oldc,oldb,oldf,oldt=(d[k] for k in ('points','cells','bodies','faces','boundaries'))
    adj=mesh_adjacency(oldc);bath=oldf[oldt==101];owners=np.array([adj[tuple(sorted(face))][0] for face in bath]);del adj
    if not np.all(oldb[owners]==300):raise ValueError('Bath ownership is not pure Kovar')
    p,c,b,f,t,nedges=refine_stars(oldp,oldc,oldb,oldf,oldt,np.unique(owners))
    if len(c)>plan['mesh_cap_tetrahedra']:raise ValueError('Registered bath mesh cap exceeded')
    exact={str(bid):np.array_equal(c[b==bid],oldc[oldb==bid]) for bid in (4,302,303,304,305)}
    if not np.array_equal(p[:len(oldp)],oldp) or not all(exact.values()):raise ValueError('Cold mesh changed')
    for name in ('manifest.json','wire_routes.json'):shutil.copy2(parent/name,out/name)
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('exact_parent_polyhedral_bath_volume_subdivision')
        ids=sorted(np.unique(b));first=int(ids[0]);gmsh.model.addDiscreteEntity(3,first);gmsh.model.mesh.addNodes(3,first,np.arange(1,len(p)+1),p.ravel())
        elem=1;all_elements=[]
        for bid in ids:
            bid=int(bid)
            if bid!=first:gmsh.model.addDiscreteEntity(3,bid)
            cc=c[b==bid];els=np.arange(elem,elem+len(cc));elem+=len(cc);all_elements.extend(els)
            gmsh.model.mesh.addElementsByType(bid,4,els,(cc+1).ravel());gmsh.model.addPhysicalGroup(3,[bid],bid)
        for tag in np.unique(t):
            tag=int(tag);gmsh.model.addDiscreteEntity(2,tag);ff=f[t==tag];els=np.arange(elem,elem+len(ff));elem+=len(ff)
            gmsh.model.mesh.addElementsByType(tag,2,els,(ff+1).ravel());gmsh.model.addPhysicalGroup(2,[tag],tag)
        # Element IDs were assigned grouped by body; return SICN to c-array order.
        q=np.empty(len(c));offset=0
        for bid in ids:
            mask=b==bid;count=int(mask.sum());q[mask]=gmsh.model.mesh.getElementQualities(all_elements[offset:offset+count],'minSICN');offset+=count
        gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.write(str(out/'connected.msh'))
    finally:gmsh.finalize()
    if q.min()<plan['minimum_SICN']:raise ValueError('Bath mesh SICN below registered0.01')
    np.savez_compressed(out/'mesh.npz',points=p,cells=c,bodies=b,faces=f,boundaries=t,quality=q)
    proof=audit(m,p,c,b,f,t,q);proof.update(mesh_sha256=sha(out/'mesh.npz'),manifest_sha256=sha(out/'manifest.json'),
        source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(PLAN.relative_to(ROOT)):sha(PLAN),
                       'tecooledmct/geometry_complete.py':sha(ROOT/'tecooledmct/geometry_complete.py')},
        parent_mesh_sha256=sha(parent/'mesh.npz'),parent_points_byte_identical=True,cold_cells_byte_identical=exact,
        geometrically_identical=True,only_bath_edge_stars_changed=True,marked_original_edges=nedges,
        original_bath_face_owners=len(np.unique(owners)),elapsed_s=time.monotonic()-start,
        affected_bodies=[int(bid) for bid in np.unique(b) if not np.array_equal(c[b==bid],oldc[oldb==bid])],
        representation='exact conformal subdivision of source-traced parent FEM geometry; no CAD rebaseline')
    write(out/'audit.json',proof);metrics(out);execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],out,'grid')
    write(out/'elmer_mapping.json',verify_elmer_tetra_mapping(out));print('Independent bath mesh PASS',len(p),len(c),'minSICN',q.min(),'affected',proof['affected_bodies'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.parent.resolve(),a.out.resolve())
