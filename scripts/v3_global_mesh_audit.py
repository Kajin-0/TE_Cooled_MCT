"""Independent from-saved-MSH geometric surface-area audit; no remeshing/PDE."""
import argparse,hashlib,json
from pathlib import Path
from tecooledmct.v3_global_mesh_audit import validate_face_area_records

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run(mesh,registry,out):
    if out.exists():raise ValueError('Refuse overwrite')
    out.mkdir(parents=True)
    import gmsh,numpy as np
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0)
        gmsh.open(str(mesh))
        faces=json.loads(registry.read_text())['interface_records']
        physical2={p for dim,p in gmsh.model.getPhysicalGroups(2)}
        physical3={p for dim,p in gmsh.model.getPhysicalGroups(3)}
        if physical2!={int(f['face_tag']) for f in faces}:
            raise ValueError('surface group registry incomplete')
        if len(physical3)!=438:
            raise ValueError('3D physical group registry incomplete')
        node_ids,coords,_=gmsh.model.mesh.getNodes()
        points=np.asarray(coords,dtype=float).reshape(-1,3)
        lookup={int(x):i for i,x in enumerate(node_ids)}
        actual={}
        for f in faces:
            tag=int(f['face_tag'])
            kinds,_,conn=gmsh.model.mesh.getElements(2,tag)
            if 2 not in kinds: raise ValueError('face has no linear triangles '+str(tag))
            triangle_ids=np.asarray(conn[list(kinds).index(2)],dtype=np.int64).reshape(-1,3)
            vertices=points[np.array([[lookup[int(v)] for v in row] for row in triangle_ids],dtype=np.int64)]
            areas=np.linalg.norm(np.cross(vertices[:,1]-vertices[:,0],vertices[:,2]-vertices[:,0]),axis=1)*.5
            if not np.all(areas>1e-15):raise ValueError('degenerate triangle '+str(tag))
            actual[tag]={'triangles':len(triangle_ids),'mesh_area_mm2':float(areas.sum())}
        result=validate_face_area_records(faces,actual)
        result.update(input_mesh_sha256=sha(mesh),input_registry_sha256=sha(registry),
                      node_count=len(node_ids),physical_2d_groups=len(physical2),physical_3d_groups=len(physical3))
        (out/'face_area_audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print('AREA AUDIT:',result['status'],'bad',result['fail_count'],'of',result['face_count'],
              'max error',result['max_absolute_error_relative'],flush=True)
        return result
    finally:gmsh.finalize()

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--mesh',required=True,type=Path);p.add_argument('--registry',required=True,type=Path)
 p.add_argument('--out',required=True,type=Path);a=p.parse_args();run(a.mesh,a.registry,a.out)
