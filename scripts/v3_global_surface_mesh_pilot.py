"""One bounded, geometry-only Gmsh surface pilot on immutable V3 conformal BREP.

Physical labels are exported independently from volume and face identities.
NO PDE, NO physical material parameter assignment, NO re-meshing loop.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main(brep:Path, registry:Path, output:Path, max_triangles:int, volume:bool=False, facet_overlap_angle:float|None=None):
    if output.exists():
        raise ValueError('Refuse to overwrite pilot outputs')
    output.mkdir(parents=True)
    receipt={'status':'INCOMPLETE', 'scope':'single global 3D meshing attempt; no PDE' if volume else 'global conformal surface pilot only; no PDE/no 3D volume mesh',
             'brep_sha256':sha(brep),'registry_sha256':sha(registry)}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0)
        gmsh.option.setString('Geometry.OCCTargetUnit','MM')
        gmsh.option.setNumber('General.NumThreads',4)
        gmsh.option.setNumber('Mesh.MaxNumThreads2D',4)
        gmsh.option.setNumber('Mesh.MeshSizeMin',0.01)
        gmsh.option.setNumber('Mesh.MeshSizeMax',0.45)
        gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0)
        gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
        gmsh.option.setNumber('Mesh.Algorithm',6)
        if facet_overlap_angle is not None:
            assert 0<facet_overlap_angle<=0.1
            gmsh.option.setNumber('Mesh.AngleToleranceFacetOverlap',facet_overlap_angle)
            receipt['facet_overlap_tolerance_degrees']=facet_overlap_angle
        gmsh.logger.start()
        t=time.monotonic()
        gmsh.model.occ.importShapes(str(brep));gmsh.model.occ.synchronize()
        reg=json.loads(registry.read_text())
        vols={t for dim,t in gmsh.model.getEntities(3)}
        faces={t for dim,t in gmsh.model.getEntities(2)}
        assert len(vols)==438 and len(faces)==2456
        assert vols=={v['tag'] for v in reg['domain_metadata'].values()}
        assert faces=={v['face_tag'] for v in reg['interface_records']}
        for name,d in sorted(reg['domain_metadata'].items(),key=lambda z:z[1]['tag']):
            gmsh.model.addPhysicalGroup(3,[d['tag']],d['tag'])
            gmsh.model.setPhysicalName(3,d['tag'],name)
            if d['material']=='COMPOSITE_MULTILAYER':
                assert d['constitutive_assignment']=='REQUIRES_EFFECTIVE_TENSOR_AND_INTERFACE_LAW'
        ownership=[]
        for f in reg['interface_records']:
            tag=f['face_tag']
            adjacent=sorted(map(int,gmsh.model.getAdjacencies(2,tag)[0]))
            required=sorted(x['volume_tag'] for x in f['owners'])
            assert adjacent==required,(tag,adjacent,required)
            gmsh.model.addPhysicalGroup(2,[tag],tag)
            gmsh.model.setPhysicalName(2,tag,'face_'+str(tag)+'_'+f['interface_class'])
            ownership.append((tag,tuple(required),f['interface_class']))
        receipt['cad_preflight']={'volumes':len(vols),'faces':len(faces),'face_groups':len(ownership),
            'volume_groups':len(vols),'unassigned_faces':0,'import_seconds':time.monotonic()-t}
        (output/'face_volume_physical_groups.json').write_text(json.dumps({
            'source_brep_sha256':sha(brep),'source_registry_sha256':sha(registry),
            'volume_groups':{k:{'id':v['tag'],'material':v['material'],'constitutive_assignment':v.get('constitutive_assignment', 'GAS_PROPERTIES_NOT_QUALIFIED')} for k,v in reg['domain_metadata'].items()},
            'face_groups':{str(f['face_tag']):{'id':f['face_tag'],'owners':f['owners'],
              'class':f['interface_class'],'thermal':f['thermal_condition'],
              'electrical':f['electrical_condition'],'structural':f['structural_condition'],
              'radiation':f['radiation_condition'],'optical':f['optical_condition']}
              for f in reg['interface_records']},
            'solver_ready':False,
            'reason':'Missing physical constitutive tensors, contact laws and validated boundary values; no solver may silently inherit bulk properties for composites'
        },indent=2)+'\n')
        print('GLOBAL FACE GROUPS READY',len(ownership),'elapsed',round(time.monotonic()-t,2),flush=True)
        receipt['status']='SURFACE MESH ATTEMPT STARTED'
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        gmsh.model.mesh.generate(2)
        kinds,ids,nodes=gmsh.model.mesh.getElements(2)
        tris=sum(len(arr) for k,arr in zip(kinds,ids) if k in (2,9,21))
        receipt['surface_triangles']=tris
        receipt['surface_nodes']=len(gmsh.model.mesh.getNodes()[0])
        if not 0<tris<=max_triangles:
            raise ValueError('global triangle budget exceeded: '+str(tris))
        result=output/'v3_global_surface.msh'
        gmsh.write(str(result))
        receipt.update(status='PASS GLOBAL SURFACE ONLY; 3D VOLUME MESH NOT RUN',mesh_sha256=sha(result),
            seconds=time.monotonic()-t)
        print('GLOBAL SURFACE PASS',tris,'nodes',receipt['surface_nodes'],flush=True)
        if volume:
            receipt['status']='GLOBAL VOLUME MESH IN PROGRESS'
            (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
            gmsh.option.setNumber('Mesh.Algorithm3D',1)
            gmsh.model.mesh.generate(3)
            import numpy as np
            telements=0
            volume_evidence={}
            node_ids,coords,_=gmsh.model.mesh.getNodes()
            pts=np.asarray(coords,dtype=float).reshape(-1,3)
            lookup={int(v):i for i,v in enumerate(node_ids)}
            for name,d in sorted(reg['domain_metadata'].items(),key=lambda z:z[1]['tag']):
                tag=d['tag']
                kinds,_,conn=gmsh.model.mesh.getElements(3,tag)
                if 4 not in kinds:raise ValueError('no linear tetrahedra on '+name)
                idx=list(kinds).index(4)
                tetra=np.asarray(conn[idx],dtype=np.int64).reshape(-1,4)
                if not len(tetra):raise ValueError('unmeshed solid '+name)
                # Independent signed-volume sum checks volume vs native BREP.
                elem=np.array([[lookup[int(v)] for v in row] for row in tetra],dtype=np.int64)
                tets=pts[elem]
                six=np.linalg.det(tets[:,1:]-tets[:,:1])
                if np.any(np.abs(six)<1e-15):raise ValueError('degenerate tetrahedron: '+name)
                mesh_volume=float(np.sum(np.abs(six))/6)
                cad_volume=gmsh.model.occ.getMass(3,tag)
                err=abs(mesh_volume/cad_volume-1)
                volume_evidence[name]={'tets':len(tetra),'mesh_mm3':mesh_volume,'cad_mm3':cad_volume,'volume_error_relative':err}
                telements+=len(tetra)
            if telements>1500000:raise ValueError('global tetrahedral budget exceeded')
            if max(v['volume_error_relative'] for v in volume_evidence.values())>0.005:
                raise ValueError('global tetrahedral volume difference exceeds 0.5%')
            final=output/'v3_global_volume.msh'
            gmsh.write(str(final))
            receipt.update(status='PASS SINGLE GLOBAL 3D MESH; CONVERGENCE AND PHYSICS NOT QUALIFIED',
                volume_tets=telements,volume_nodes=len(node_ids),volume_mesh_sha256=sha(final),
                max_domain_volume_error=max(v['volume_error_relative'] for v in volume_evidence.values()),
                mesh_domains=len(volume_evidence))
            (output/'volume_evidence.json').write_text(json.dumps(volume_evidence,indent=2)+'\n')
            print('GLOBAL VOLUME PASS',telements,'tets',len(node_ids),'nodes',flush=True)

    except Exception as exc:
        receipt.update(status='STOP GLOBAL 3D MESH' if volume and 'surface_triangles' in receipt else 'STOP GLOBAL SURFACE MESH',error=repr(exc))
        raise
    finally:
        try: (output/'gmsh_tail.json').write_text(json.dumps(gmsh.logger.get()[-80:],indent=2)+'\n')
        finally:
            gmsh.logger.stop();gmsh.finalize()
            (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--brep',type=Path,required=True)
    p.add_argument('--registry',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--max-triangles',type=int,default=500000)
    p.add_argument('--volume',action='store_true')
    p.add_argument('--facet-overlap-angle',type=float,default=None)
    a=p.parse_args();main(a.brep,a.registry,a.out,a.max_triangles,a.volume,a.facet_overlap_angle)
