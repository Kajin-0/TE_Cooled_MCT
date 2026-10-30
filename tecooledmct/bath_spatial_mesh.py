"""Registered full owner-star transverse/volume pair, exact source geometry."""
import argparse,json,shutil,time
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .cold20_bath_mesh import refine_stars
from .gate_refinement import refine_edges,normal_edges
from .fem_g2a import mesh_adjacency
from .geometry_complete import audit
from .cold_roi_mesh import metrics
from .fem_g1_run import execute
from .fem_g2c_mesh import verify_elmer_tetra_mapping
from .bath_spatial_audit import gradients
PLAN=ROOT/'data/bath_spatial/refinement_plan.json'

def build(parent,out,level=1,combined=False):
    import gmsh
    if out.exists():raise ValueError('New mesh label required')
    out.mkdir(parents=True);start=time.monotonic();plan=json.loads(PLAN.read_text());d=np.load(parent/'mesh.npz');m=json.loads((parent/'manifest.json').read_text())
    op,oc,ob,of,ot=[d[k] for k in ['points','cells','bodies','faces','boundaries']];adj=mesh_adjacency(oc)
    if combined:
        tags=[next(x['boundary_id'] for x in m['contacts'] if x['bodies']==pair) for pair in [[4,302],[302,303]]]
        selected=of[np.isin(ot,tags)];marked=normal_edges(oc,ob,selected,adj);del adj
        p,c,b,f,t=refine_edges(op,oc,ob,of,ot,marked);count=len(marked);allowed={4,302,303}
    else:
        selected=of[ot==101]
        if level==2:selected=selected[np.linalg.norm(op[selected,:2].mean(1),axis=1)<=plan['central_radius_m']]
        owners=np.array([adj[tuple(sorted(face))][0] for face in selected]);del adj
        if not np.all(ob[owners]==300):raise ValueError('Non-Kovar bath owners')
        p,c,b,f,t,count=refine_stars(op,oc,ob,of,ot,np.unique(owners));allowed=set(plan['allowed_changed_bodies'])
    cap=plan['combined_tetrahedron_cap' if combined else 'independent_tetrahedron_cap']
    write(out/'preflight.json',{'points':len(p),'tetrahedra':len(c),'cap':cap,'combined':combined,'level':level,'selected_faces':len(selected),'marked_edges':count,'solver_executed':False})
    if len(c)>cap:raise ValueError('Registered mesh resource bound exceeded; no solver run')
    fixed={str(bid):np.array_equal(c[b==bid],oc[ob==bid]) for bid in np.unique(ob) if bid not in allowed}
    if not all(fixed.values()) or not np.array_equal(p[:len(op)],op):raise ValueError('Fixed region or original point changed')
    changed=[int(x) for x in np.unique(b) if not np.array_equal(c[b==x],oc[ob==x])]
    v,_=gradients(p,c,np.zeros(len(p)));ov,_=gradients(op,oc,np.zeros(len(op)))
    volume_errors={str(bid):float(v[b==bid].sum()/ov[ob==bid].sum()-1) for bid in np.unique(b)}
    if max(abs(x) for x in volume_errors.values())>1e-10:raise ValueError('Exact material volumes changed')
    def areas(points,faces,labels):
        xyz=points[faces];a=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
        return {int(tag):float(a[labels==tag].sum()) for tag in np.unique(labels)}
    oldarea=areas(op,of,ot);newarea=areas(p,f,t);area_errors={str(tag):newarea[tag]/oldarea[tag]-1 for tag in oldarea}
    if max(abs(x) for x in area_errors.values())>1e-10:raise ValueError('Physical contact/exterior areas changed')
    for name in ['manifest.json','wire_routes.json']:shutil.copy2(parent/name,out/name)
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('source_exact_transverse_volume_refinement');ids=sorted(np.unique(b));first=int(ids[0]);gmsh.model.addDiscreteEntity(3,first);gmsh.model.mesh.addNodes(3,first,np.arange(1,len(p)+1),p.ravel());elem=1;q=np.empty(len(c))
        for bid in ids:
            bid=int(bid)
            if bid!=first:gmsh.model.addDiscreteEntity(3,bid)
            mask=b==bid;els=np.arange(elem,elem+mask.sum());elem+=mask.sum();gmsh.model.mesh.addElementsByType(bid,4,els,(c[mask]+1).ravel());gmsh.model.addPhysicalGroup(3,[bid],bid);q[mask]=gmsh.model.mesh.getElementQualities(els,'minSICN')
        for tag in np.unique(t):
            tag=int(tag);gmsh.model.addDiscreteEntity(2,tag);ff=f[t==tag];els=np.arange(elem,elem+len(ff));elem+=len(ff);gmsh.model.mesh.addElementsByType(tag,2,els,(ff+1).ravel());gmsh.model.addPhysicalGroup(2,[tag],tag)
        gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.write(str(out/'connected.msh'))
    finally:gmsh.finalize()
    if q.min()<plan['minimum_SICN']:raise ValueError('Actual minimum SICN below original0.01 bound')
    np.savez_compressed(out/'mesh.npz',points=p,cells=c,bodies=b,faces=f,boundaries=t,quality=q)
    proof=audit(m,p,c,b,f,t,q);proof.update(mesh_sha256=sha(out/'mesh.npz'),manifest_sha256=sha(out/'manifest.json'),
       source_sha256={str(x.relative_to(ROOT)):sha(x) for x in [Path(__file__),PLAN,ROOT/'tecooledmct/cold20_bath_mesh.py',ROOT/'tecooledmct/gate_refinement.py',ROOT/'tecooledmct/geometry_complete.py',ROOT/'tecooledmct/bath_spatial_audit.py']},
       parent_mesh_sha256=sha(parent/'mesh.npz'),combined=combined,level=level,changed_bodies=changed,fixed_cell_sets_byte_identical=fixed,
       parent_points_byte_identical=True,material_volume_relative_errors=volume_errors,physical_area_relative_errors=area_errors,
       bath_area_m2=newarea[101],geometrically_identical=True,selected_faces=len(selected),marked_edges=count,elapsed_s=time.monotonic()-start)
    write(out/'audit.json',proof);metrics(out);execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],out,'grid');write(out/'elmer_mapping.json',verify_elmer_tetra_mapping(out))
    print('Transverse volume mesh PASS',len(p),len(c),'minSICN',q.min(),'changed',changed,'combined',combined,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--level',type=int,choices=[1,2],default=1);p.add_argument('--combined',action='store_true');a=p.parse_args();build(a.parent.resolve(),a.out.resolve(),a.level,a.combined)
