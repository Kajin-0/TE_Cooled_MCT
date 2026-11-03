"""One bounded whole R3 tetrahedral attempt on an accepted surface mesh. No PDE."""
from pathlib import Path
import argparse,time,resource
import numpy as np
import gmsh
from scripts.v3_analysis_r3_geometry import read,save,sha

def main(brep,mesh,registry,surface_audit,out,algorithm):
    if out.exists():raise ValueError('Preserve volume attempt')
    if not read(surface_audit)['status'].startswith('PASS'):raise ValueError('Surface audit not accepted')
    out.mkdir(parents=True);reg=read(registry);start=time.monotonic()
    result=dict(status='PENDING',algorithm=algorithm,input_BREP_sha256=sha(brep),input_surface_sha256=sha(mesh),no_PDE=True,solver_ready=False)
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',1);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    gmsh.option.setNumber('General.NumThreads',4);gmsh.option.setNumber('Mesh.MaxNumThreads3D',4)
    gmsh.option.setNumber('Mesh.MeshSizeMin',.0015);gmsh.option.setNumber('Mesh.MeshSizeMax',.60)
    gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',0)
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0);gmsh.option.setNumber('Mesh.MeshOnlyEmpty',1)
    gmsh.option.setNumber('Mesh.Algorithm3D',algorithm);gmsh.option.setNumber('Mesh.ElementOrder',1)
    gmsh.option.setNumber('Mesh.SaveAll',1);gmsh.option.setNumber('Mesh.Binary',1);gmsh.logger.start()
    try:
        gmsh.model.occ.importShapes(str(brep));gmsh.model.occ.synchronize();gmsh.merge(str(mesh))
        if set(reg['domain_id_map'].values())!={t for d,t in gmsh.model.getEntities(3)}:raise ValueError('Volume identity before3D')
        for key,q in reg['face_registry'].items():
            if sorted(map(int,gmsh.model.getAdjacencies(2,int(key))[0]))!=q['owner_volume_ids']:raise ValueError('Boundary ownership before3D')
        gmsh.model.mesh.generate(3)
        kinds,ids,arrays=gmsh.model.mesh.getElements(3)
        if list(kinds)!=[4]:raise ValueError('Non-tetrahedral3D result')
        n=len(ids[0]);result['tetrahedra']=n
        if n>3000000:raise ValueError('3million-tet budget exceeded')
        nodes,xyz,_=gmsh.model.mesh.getNodes();result['nodes']=len(nodes)
        gmsh.write(str(out/'R3_volume.msh'))
        result.update(status='GENERATED GLOBAL TETS; INDEPENDENT AUDIT PENDING',mesh_sha256=sha(out/'R3_volume.msh'))
    except Exception as ex:
        result.update(status='STOP GLOBAL3D MESHER',error=repr(ex));raise
    finally:
        result.update(seconds=time.monotonic()-start,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        save(out/'receipt.json',result);save(out/'gmsh_tail.json',gmsh.logger.get()[-100:]);gmsh.logger.stop();gmsh.finalize()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--brep',type=Path,required=True);p.add_argument('--surface',type=Path,required=True)
    p.add_argument('--registry',type=Path,required=True);p.add_argument('--surface-audit',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--algorithm',type=int,choices=[1,10],default=1)
    a=p.parse_args();main(a.brep,a.surface,a.registry,a.surface_audit,a.out,a.algorithm)
