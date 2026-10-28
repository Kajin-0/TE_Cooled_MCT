"""Conformal OCC/HXT tetrahedral meshing for explicit contact transition layers."""
from pathlib import Path
import json
import numpy as np
from .fem_g2a import BC_NAMES,audit_boxes,audit_mesh


def generate_transition_mesh(out,size,manifest):
    import gmsh,meshio
    audit_boxes(manifest);out.mkdir(parents=True,exist_ok=True);gmsh.initialize();gmsh.logger.start()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',1)
        gmsh.option.setNumber('Mesh.RandomSeed',20261028);gmsh.option.setNumber('Mesh.Algorithm3D',10)
        gmsh.model.add('explicit_transition_domains')
        originals=[(3,gmsh.model.occ.addBox(*b['box_m'])) for b in manifest['bodies']]
        _,mapping=gmsh.model.occ.fragment(originals[:1],originals[1:]);gmsh.model.occ.synchronize();vb={}
        for body,fragments in zip(manifest['bodies'],mapping):
            volumes=[tag for dim,tag in fragments if dim==3];gmsh.model.addPhysicalGroup(3,volumes,body['id'],body['name']);vb.update({v:body['id'] for v in volumes})
        contacts={tuple(c['bodies']):c for c in manifest['contacts']};surfaces={b:[] for b in BC_NAMES};surfaces.update({c['boundary_id']:[] for c in manifest['contacts']})
        for _,surface in gmsh.model.getEntities(2):
            up,_=gmsh.model.getAdjacencies(2,surface);pair=tuple(sorted({vb[int(v)] for v in up}));center=gmsh.model.occ.getCenterOfMass(2,surface)
            if len(pair)==2:tag=contacts[pair]['boundary_id']
            elif len(pair)==1:
                tag=105
                if abs(center[2]-manifest['hot_z_m'])<1e-11:tag=101
                elif abs(center[2]-manifest['cold_z_m'])<1e-11:tag=102
                else:
                    for bc,plane in manifest['terminal_planes'].items():
                        if pair[0]==plane['body'] and abs(center[plane['axis']]-plane['coordinate_m'])<1e-11:tag=int(bc)
            else:raise ValueError('Invalid OCC interface')
            surfaces[tag].append(surface)
        for tag,ss in surfaces.items():
            if not ss:raise ValueError(f'Missing physical interface {tag}')
            gmsh.model.addPhysicalGroup(2,ss,tag,BC_NAMES.get(tag,f'contact_{tag}'))
        gmsh.option.setNumber('Mesh.MeshSizeMin',size);gmsh.option.setNumber('Mesh.MeshSizeMax',size);gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
        gmsh.model.mesh.generate(3);gmsh.model.mesh.optimize('Netgen')
        _,tt,_=gmsh.model.mesh.getElements(3);quality=np.concatenate([gmsh.model.mesh.getElementQualities(t,'minSICN') for t in tt]);gmsh.write(str(out/'stage.msh'))
        if quality.min()<.01:raise ValueError(f'Contact mesh min SICN {quality.min()} below .01')
    finally:
        (out/'gmsh.log').write_text('\n'.join(gmsh.logger.get())+'\n');gmsh.logger.stop();gmsh.finalize()
    actual=meshio.read(out/'stage.msh');points=actual.points;cells=actual.cells_dict['tetra'];faces=actual.cells_dict['triangle'];bodies=actual.cell_data_dict['gmsh:physical']['tetra'];tags=actual.cell_data_dict['gmsh:physical']['triangle']
    np.savez_compressed(out/'mesh.npz',points=points,cells=cells,bodies=bodies,faces=faces,boundaries=tags)
    audit=audit_mesh(manifest,points,cells,bodies,faces,tags);audit.update(min_tetra_sicn=float(quality.min()),algorithm='OCC BooleanFragments + HXT + Netgen',mesh_size_m=size)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    return audit


def verify_elmer_tetra_mapping(mesh):
    """Check real ElmerGrid node/connectivity/body IDs against original arrays."""
    from scipy.spatial import cKDTree
    d=np.load(mesh/'mesh.npz');rows=np.loadtxt(mesh/'elmer/mesh.nodes');dist,ix=cKDTree(rows[:,2:5]).query(d['points'])
    if dist.max()>1e-12 or len(np.unique(ix))!=len(ix):raise ValueError('ElmerGrid node mapping mismatch')
    ids=rows[ix,0].astype(int);expected={tuple(sorted(ids[c])):int(b) for c,b in zip(d['cells'],d['bodies'])}
    actual={}
    for line in (mesh/'elmer/mesh.elements').read_text().splitlines():
        v=list(map(int,line.split()))
        if v[2]!=504:raise ValueError('ElmerGrid element is not a P1 tetrahedron')
        actual[tuple(sorted(v[3:]))]=v[1]
    if len(actual)!=len(d['cells']) or actual!=expected:raise ValueError('ElmerGrid changed tetrahedron/body material mapping')
    return {'passed':True,'nodes':len(ids),'tetrahedra':len(actual),'body_ids_preserved':True}
