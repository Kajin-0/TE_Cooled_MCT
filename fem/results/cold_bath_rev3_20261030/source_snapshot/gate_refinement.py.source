"""Exact conformal normal-edge refinement with explicit independent region locks."""
import argparse,json,shutil,time
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .fem_g2a import mesh_adjacency
from .geometry_complete import audit
from .cold_roi_mesh import metrics
from .cold20_bath_mesh import EDGES,TRIEDGES
from .fem_g1_run import execute
from .fem_g2c_mesh import verify_elmer_tetra_mapping

PLAN=ROOT/'data/gate_refinement/plan.json'


def refine_edges(p,c,b,f,tags,marked):
    marked={tuple(sorted(map(int,e))) for e in marked};ts={e:set() for e in marked};fs={e:set() for e in marked}
    cells=c.tolist();bodies=b.tolist();faces=f.tolist();labels=tags.tolist();active=[True]*len(cells);fa=[True]*len(faces);points=p.tolist()
    def update(row,i,stars,edges,add):
        for a,z in edges:
            e=tuple(sorted((row[a],row[z])))
            if e in stars:
                if add:stars[e].add(i)
                else:stars[e].discard(i)
    for i,row in enumerate(cells):update(row,i,ts,EDGES,True)
    for i,row in enumerate(faces):update(row,i,fs,TRIEDGES,True)
    for a,z in sorted(marked):
        mid=len(points);points.append(((p[a]+p[z])/2).tolist())
        for i in list(ts[(a,z)]):
            row=cells[i];active[i]=False;update(row,i,ts,EDGES,False);left=row.copy();right=row.copy();left[left.index(z)]=mid;right[right.index(a)]=mid
            for child in (left,right):
                n=len(cells);cells.append(child);bodies.append(bodies[i]);active.append(True);update(child,n,ts,EDGES,True)
        for i in list(fs[(a,z)]):
            row=faces[i];fa[i]=False;update(row,i,fs,TRIEDGES,False);left=row.copy();right=row.copy();left[left.index(z)]=mid;right[right.index(a)]=mid
            for child in (left,right):
                n=len(faces);faces.append(child);labels.append(labels[i]);fa.append(True);update(child,n,fs,TRIEDGES,True)
    active=np.array(active);fa=np.array(fa)
    return np.array(points),np.array(cells)[active],np.array(bodies)[active],np.array(faces)[fa],np.array(labels)[fa]


def normal_edges(c,b,faces,adj):
    marked=set()
    for face in faces:
        for owner in adj[tuple(sorted(face))]:
            apex=list(set(map(int,c[owner]))-set(map(int,face)))
            if len(apex)!=1:raise ValueError('Invalid face owner')
            marked.update(tuple(sorted((int(node),apex[0]))) for node in face)
    return marked


def build(parent,out,track):
    import gmsh
    if out.exists():raise ValueError('Choose a new mesh output label')
    out.mkdir(parents=True);start=time.monotonic();d=np.load(parent/'mesh.npz');m=json.loads((parent/'manifest.json').read_text());plan=json.loads(PLAN.read_text())
    op,oc,ob,of,ot=(d[k] for k in ('points','cells','bodies','faces','boundaries'));adj=mesh_adjacency(oc)
    if track=='cold':
        selected_tags=[next(x['boundary_id'] for x in m['contacts'] if x['bodies']==pair) for pair in ([4,302],[302,303])]
        allowed={4,302,303}
    else:selected_tags=[101];allowed={300,*range(401,410)}
    selected=of[np.isin(ot,selected_tags)];marked=normal_edges(oc,ob,selected,adj);del adj
    p,c,b,f,t=refine_edges(op,oc,ob,of,ot,marked)
    if len(c)>plan['tetrahedron_cap']:raise ValueError('Registered1M tet bound exceeded')
    changed=[int(bid) for bid in np.unique(b) if not np.array_equal(c[b==bid],oc[ob==bid])]
    if not set(changed)<=allowed or not np.array_equal(p[:len(op)],op):raise ValueError('Independent region-lock proof failed')
    if not np.array_equal(f[np.isin(t,selected_tags)],selected):raise ValueError('Normal refinement unexpectedly changed target interface triangles')
    for name in ('manifest.json','wire_routes.json'):shutil.copy2(parent/name,out/name)
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('source_exact_normal_refinement');ids=sorted(np.unique(b));first=int(ids[0]);gmsh.model.addDiscreteEntity(3,first)
        gmsh.model.mesh.addNodes(3,first,np.arange(1,len(p)+1),p.ravel());elem=1;q=np.empty(len(c))
        for bid in ids:
            bid=int(bid)
            if bid!=first:gmsh.model.addDiscreteEntity(3,bid)
            mask=b==bid;cc=c[mask];els=np.arange(elem,elem+len(cc));elem+=len(cc)
            gmsh.model.mesh.addElementsByType(bid,4,els,(cc+1).ravel());gmsh.model.addPhysicalGroup(3,[bid],bid);q[mask]=gmsh.model.mesh.getElementQualities(els,'minSICN')
        for tag in np.unique(t):
            tag=int(tag);gmsh.model.addDiscreteEntity(2,tag);ff=f[t==tag];els=np.arange(elem,elem+len(ff));elem+=len(ff)
            gmsh.model.mesh.addElementsByType(tag,2,els,(ff+1).ravel());gmsh.model.addPhysicalGroup(2,[tag],tag)
        gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.write(str(out/'connected.msh'))
    finally:gmsh.finalize()
    if q.min()<plan['minimum_SICN']:raise ValueError('Mesh SICN below0.01')
    np.savez_compressed(out/'mesh.npz',points=p,cells=c,bodies=b,faces=f,boundaries=t,quality=q)
    proof=audit(m,p,c,b,f,t,q);proof.update(mesh_sha256=sha(out/'mesh.npz'),manifest_sha256=sha(out/'manifest.json'),
        source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(PLAN.relative_to(ROOT)):sha(PLAN),
                      'tecooledmct/geometry_complete.py':sha(ROOT/'tecooledmct/geometry_complete.py')},
        parent_mesh_sha256=sha(parent/'mesh.npz'),track=track,normal_edge_count=len(marked),changed_bodies=changed,
        independent_region_lock_passed=True,target_interface_triangles_byte_identical=True,parent_points_byte_identical=True,
        geometrically_identical=True,elapsed_s=time.monotonic()-start)
    write(out/'audit.json',proof);metrics(out);execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],out,'grid')
    write(out/'elmer_mapping.json',verify_elmer_tetra_mapping(out));print('Normal refinement PASS',track,len(p),len(c),changed,q.min(),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--track',choices=('cold','bath'),required=True);a=p.parse_args();build(a.parent.resolve(),a.out.resolve(),a.track)
