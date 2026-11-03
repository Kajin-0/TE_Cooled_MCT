"""The single R3.2 global SURFACE worker. No Boolean, tet/PDE or retry path."""
from pathlib import Path
import collections
import hashlib
import json
import math
import resource
import time
MODULE_IMPORT_START=time.monotonic()
import gmsh
import numpy as np

from scripts.v3_r31_worker_v2 import Profile, save, constraint_setup, seed_periodic
from scripts.v3_r32_audit import normalize_winding, metrics
from tecooledmct.v3_r32_surface_integrity import DIRECTIONAL_FACES, validate_registration, validate_mesh_evidence
from tecooledmct.v3_r32_intersections import full_intersection_check

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_r32_global_surface_20261103'
R3=ROOT/'data/v3_analysis_r3_20261103'


def read(path):
    return json.loads(Path(path).read_text())


def directional_spec(source):
    curves={};periodic={}
    for f in sorted(DIRECTIONAL_FACES):
        q=source['faces'][str(f)];lo,hi=map(np.asarray,q['parameter_bounds'])
        if q['type'] not in ('Cylinder','Torus'):
            raise ValueError('Unauthorized directional geometry')
        axis=0 if q['type']=='Cylinder' else 1
        if abs(hi[axis]-lo[axis]-2*math.pi)>1e-6:
            raise ValueError('Invalid native periodicity')
        seams=[e for e,n in collections.Counter(q['boundary_with_multiplicity']).items() if n==2]
        if len(seams)!=1:
            raise ValueError('Ambiguous exact source seam')
        periodic[f]=dict(axis=axis,seam=seams[0],lo=lo,hi=hi)
        curves.update({int(e):c for e,c in q['curves'].items()})
    counts={e:max(1,math.ceil(c['length_mm']/.08-1e-8),
                    math.ceil(c['length_mm']*c['max_curvature_per_mm']/(math.pi/24)-1e-8)) for e,c in curves.items()}
    for e,n in counts.items():
        gmsh.model.mesh.setTransfiniteCurve(e,n+1)
    return periodic,counts


def face_mesh_hash(face):
    types,ids,arrays=gmsh.model.mesh.getElements(2,face)
    h=hashlib.sha256()
    h.update(np.asarray(types,np.int64).tobytes())
    for a in [*ids,*arrays]:h.update(np.asarray(a,np.int64).tobytes())
    return h.hexdigest()


def main():
    out=DATA/'run';out.mkdir(exist_ok=False)
    profile=Profile(out)
    registration=read(DATA/'registration.json');source=read(DATA/'source_metadata.json')
    validate_registration(registration,source)
    old_plan=read(R3/'surface/surface_0/size_plan.json')
    result=dict(status='PENDING',directional_face_ids=sorted(DIRECTIONAL_FACES),
        PDE_RUN=False,volume_mesh_RUN=False,solver_ready=False,runs=1,
        python_module_import_seconds=time.monotonic()-MODULE_IMPORT_START,
        intersections=dict(status='NOT RUN',traversal_complete=False,measured_proper_intersections=0))
    gmsh.initialize()
    if gmsh.__version__!='4.13.1':raise ValueError('Wrong pinned Gmsh version')
    gmsh.option.setNumber('General.Terminal',1)
    gmsh.option.setNumber('General.Verbosity',4)
    gmsh.option.setNumber('General.NumThreads',4)
    gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    for key,value in [('Mesh.MaxNumThreads1D',4),('Mesh.MaxNumThreads2D',4),
        ('Mesh.MeshOnlyVisible',0),('Mesh.MeshSizeMin',.0015),('Mesh.MeshSizeMax',.30),
        ('Mesh.MeshSizeFromPoints',0),('Mesh.MeshSizeFromCurvature',0),
        ('Mesh.MeshSizeExtendFromBoundary',0),('Mesh.MinimumCirclePoints',12),
        ('Mesh.Algorithm',6),('Mesh.ElementOrder',1),('Mesh.SaveAll',1),('Mesh.Binary',1)]:
        gmsh.option.setNumber(key,value)
    gmsh.logger.start()
    try:
        with profile.stage('import_and_source_invariants'):
            gmsh.model.occ.importShapes(str(R3/'geometry_restored/R3_conformal_mm.brep'))
            gmsh.model.occ.synchronize()
            if len(gmsh.model.getEntities(3))!=430 or len(gmsh.model.getEntities(2))!=2440:
                raise ValueError('Source domain/face count changed')
            g=read(R3/'geometry_restored/geometry_receipt.json')
            for name,t in source['domain_id_map'].items():
                if abs(gmsh.model.occ.getMass(3,t)/g['domains'][name]['area_or_volume']-1)>=1e-7:
                    raise ValueError('Source volume mass changed '+name)
                gmsh.model.addPhysicalGroup(3,[t],t);gmsh.model.setPhysicalName(3,t,name)
            for key,q in source['faces'].items():
                f=int(key)
                if sorted(map(int,gmsh.model.getAdjacencies(2,f)[0]))!=q['owner_volume_ids'] or abs(gmsh.model.occ.getMass(2,f)/q['face_area_mm2']-1)>=1e-7:
                    raise ValueError('Source native face owner/area changed '+key)
                gmsh.model.addPhysicalGroup(2,[f],f);gmsh.model.setPhysicalName(2,f,'R3_native_face_'+key)
            result['source_invariants_PASS']=True
        with profile.stage('native_sizing_and_shared_constraints'):
            result['native_sizing']=constraint_setup('B_native_selective',list(map(int,source['faces'])),source,old_plan)
            periodic,counts=directional_spec(source)
            result['directional_curve_counts']={str(e):n for e,n in counts.items()}
            if set(periodic)!=DIRECTIONAL_FACES:
                raise ValueError('Exactly ten directional faces required')
        with profile.stage('shared_native_1D'):
            gmsh.model.mesh.generate(1)
        with profile.stage('directional_exact_ten'):
            result['directional_patches']=seed_periodic(periodic,counts)
            populated={f for d,f in gmsh.model.getEntities(2) if any(len(a) for a in gmsh.model.mesh.getElements(2,f)[1])}
            if populated!=DIRECTIONAL_FACES:
                raise ValueError('Directional expansion or missing patch')
            before={f:face_mesh_hash(f) for f in DIRECTIONAL_FACES}
            save(out/'directional_seed_receipt.json',dict(patches=result['directional_patches'],mesh_hashes={str(k):v for k,v in before.items()}))
            gmsh.option.setNumber('Mesh.MeshOnlyEmpty',1)
        with profile.stage('ONE_native_global_2D_fill'):
            gmsh.model.mesh.generate(2)
        with profile.stage('immediate_counts_and_unoriented_archive'):
            for f,h in before.items():
                if face_mesh_hash(f)!=h:
                    raise ValueError('Native fill altered directional seed')
            result['directional_seeds_unchanged']=True
            types,ids,arrays=gmsh.model.mesh.getElements(2)
            if list(types)!=[2]:raise ValueError('Global surface not exclusively TRI3')
            n=sum(len(a) for a in ids)
            save(out/'mesh_counts.json',dict(triangles=n,nodes=len(gmsh.model.mesh.getNodes()[0]),
                tetrahedra=sum(len(a) for a in gmsh.model.mesh.getElements(3)[1]),
                completed_native_faces=sum(any(len(a) for a in gmsh.model.mesh.getElements(2,f)[1]) for d,f in gmsh.model.getEntities(2)),
                triangle_budget_PASS=n<=800000))
            gmsh.write(str(out/'surface_before_winding.msh'))
            save(out/'unoriented_archive.json',dict(complete=True,SHA256=hashlib.sha256((out/'surface_before_winding.msh').read_bytes()).hexdigest()))
        with profile.stage('source_boundary_winding'):
            result['winding_normalization']=normalize_winding(source)
        with profile.stage('canonical_native_MSH_serialization'):
            gmsh.write(str(out/'global_surface.msh'))
            save(out/'mesh_archive_receipt.json',dict(complete=True,SHA256=hashlib.sha256((out/'global_surface.msh').read_bytes()).hexdigest()))
        with profile.stage('all_face_ancestor_topology_quality_normal_validation'):
            points,tri,face_ids,lookup=metrics(source,result,lambda q:save(out/'area_progress.json',q))
            save(out/'geometry_audit_before_intersections.json',result)
        primary=True
        try:validate_mesh_evidence(result,check_intersections=False)
        except ValueError as ex:
            result['primary_gate_failure']=str(ex);primary=False
        if primary:
            with profile.stage('complete_facet_intersection_BVH'):
                result['intersections']=full_intersection_check(points,lookup[tri],face_ids,
                    lambda q:save(out/'intersection_progress.json',q))
        else:
            result['intersections']=dict(status='NOT RUN candidate already fails mandatory gates',
                traversal_complete=False,measured_proper_intersections=0)
        try:
            validate_mesh_evidence(result)
            result['status']='PASS GLOBAL SURFACE GEOMETRY ONLY; VOLUME/PDE NOT RUN'
        except ValueError as ex:
            result.update(status='FAIL GLOBAL SURFACE GATE; NO RETRY',gate_failure=str(ex))
    except Exception as ex:
        result.update(status='STOP GLOBAL WORKER; NO RETRY',error=repr(ex))
    finally:
        result.update(phases=profile.phases,wall_seconds=time.monotonic()-profile.start,
            CPU_seconds=time.process_time(),peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            Gmsh_version=gmsh.__version__,NumPy_version=np.__version__)
        save(out/'result.json',result)
        save(out/'gmsh_tail.json',gmsh.logger.get()[-200:])
        gmsh.logger.stop();gmsh.finalize()
    print('FINAL',result['status'],result.get('triangles'),flush=True)


if __name__=='__main__':
    main()
