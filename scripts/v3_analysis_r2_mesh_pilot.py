"""Single R2 full-geometry surface pilot, with strict CAD/mesh area gate.

No PDE; global 3D mesh is forbidden until every surface passes the area gate.
"""
from pathlib import Path
import argparse,hashlib,json,time
import gmsh,numpy as np
from tecooledmct.v3_global_mesh_audit import validate_face_area_records

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')

def main(brep,registry,out,curvature=False,edge_only=False):
 if out.exists():raise ValueError('Refuse overwrite')
 out.mkdir(parents=True)
 record=json.loads(registry.read_text())
 r={'status':'PENDING','scope':'one full-geometry surface mesh, no PDE/3D if area gate fails',
   'input_BREP_sha256':sha(brep),'input_R2_registry_sha256':sha(registry)}
 save(out/'mesh_receipt.json',r)
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
 gmsh.option.setNumber('General.NumThreads',4);gmsh.option.setNumber('Mesh.MaxNumThreads2D',4)
 gmsh.option.setNumber('Mesh.MeshSizeMin',.008);gmsh.option.setNumber('Mesh.MeshSizeMax',.30)
 gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0);gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
 gmsh.option.setNumber('Mesh.Algorithm',6)
 if curvature and edge_only:raise ValueError('choose curvature or edge-only controls')
 if edge_only:
  gmsh.option.setNumber('Mesh.MinimumCirclePoints',36)
  gmsh.option.setNumber('Mesh.MinimumCurvePoints',22)
  gmsh.option.setNumber('Mesh.MeshSizeMin',.004)
 if curvature:
  gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',36)
  gmsh.option.setNumber('Mesh.MinimumCirclePoints',36)
  gmsh.option.setNumber('Mesh.MinimumCurvePoints',18)
  gmsh.option.setNumber('Mesh.MeshSizeMin',.0015)
 gmsh.logger.start();start=time.monotonic()
 try:
  oc=gmsh.model.occ;oc.importShapes(str(brep));oc.synchronize()
  known=record['domain_id_map'];faces=record['face_registry']
  if len(known)!=428 or len(faces)!=2422:raise ValueError('R2 registry incomplete')
  if {t for d,t in gmsh.model.getEntities(3)}!=set(known.values()):raise ValueError('R2 volume ID mismatch')
  if {t for d,t in gmsh.model.getEntities(2)}!={int(f) for f in faces}:raise ValueError('R2 face ID mismatch')
  for name,t in known.items():
   gmsh.model.addPhysicalGroup(3,[t],t)
   gmsh.model.setPhysicalName(3,t,name)
  for fstr,metadata in faces.items():
   f=int(fstr);owner=sorted(map(int,gmsh.model.getAdjacencies(2,f)[0]))
   if owner!=metadata['owner_volume_ids']:raise ValueError('face ownership mismatch '+fstr)
   gmsh.model.addPhysicalGroup(2,[f],f)
   gmsh.model.setPhysicalName(2,f,'face_'+fstr+'_'+metadata['class'])
  print('R2 groups ready',len(known),'volumes',len(faces),'faces',flush=True)
  gmsh.model.mesh.generate(2)
  nodeids,coordinates,_=gmsh.model.mesh.getNodes()
  pts=np.asarray(coordinates).reshape(-1,3);lookup={int(k):i for i,k in enumerate(nodeids)}
  area_records={};pseudo_faces=[]
  for fstr,info in faces.items():
   f=int(fstr);kinds,_,elems=gmsh.model.mesh.getElements(2,f)
   if 2 not in kinds:raise ValueError('no triangle for '+fstr)
   t=np.asarray(elems[list(kinds).index(2)],dtype=np.int64).reshape(-1,3)
   loc=np.asarray([[lookup[int(j)] for j in line] for line in t],dtype=np.int64)
   vertices=pts[loc];areas=np.linalg.norm(np.cross(vertices[:,1]-vertices[:,0],vertices[:,2]-vertices[:,0]),axis=1)*.5
   if np.any(areas<=1e-15):raise ValueError('degenerated surface '+fstr)
   area_records[f]={'triangles':len(t),'mesh_area_mm2':float(areas.sum())}
   pseudo_faces.append({'face_tag':f,'area_m2':info['face_area_mm2']*1e-6,
    'interface_class':info['class'],'owners':[{'source_name':n} for n in info['owners']]})
  gate=validate_face_area_records(pseudo_faces,area_records,threshold=.01)
  gate.update(mesh_nodes=len(nodeids),curvature_control=curvature,edge_only_control=edge_only,input_R2_brep_sha256=sha(brep),input_R2_registry_sha256=sha(registry))
  msh=out/'r2_global_surface_UNQUALIFIED.msh'
  gmsh.write(str(msh));gate['mesh_sha256']=sha(msh)
  save(out/'area_gate.json',gate)
  r.update(status='PASS FULL SURFACE AREA GATE; 3D NOT RUN' if gate['fail_count']==0 else 'STOP FULL SURFACE AREA GATE; 3D NOT RUN',
   face_count=len(faces),nodes=len(nodeids),triangles=gate['triangle_count'],area_failures=gate['fail_count'],
   max_relative_area_error=gate['max_absolute_error_relative'],mesh_sha256=sha(msh),elapsed_seconds=time.monotonic()-start)
  print('R2 surface:',r['status'],'tets NOT RUN',r['triangles'],'triangles,',r['area_failures'],'failed faces',flush=True)
  if gate['fail_count']:
   print('top 6',[(x['face_tag'],round(x['absolute_error_relative'],5),x['owners']) for x in gate['top_failures'][:6]],flush=True)
 except Exception as ex:
  r.update(status='FAIL R2 SURFACE PILOT',error=repr(ex),elapsed_seconds=time.monotonic()-start)
  raise
 finally:
  save(out/'mesh_receipt.json',r)
  save(out/'gmsh_tail.json',gmsh.logger.get()[-90:]);gmsh.logger.stop();gmsh.finalize()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--brep',type=Path,required=True)
 p.add_argument('--registry',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--curvature',action='store_true')
 p.add_argument('--edge-only',action='store_true')
 a=p.parse_args();main(a.brep,a.registry,a.out,a.curvature,a.edge_only)
