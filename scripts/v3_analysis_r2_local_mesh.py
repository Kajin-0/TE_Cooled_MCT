"""Bounded lead/contact meshability fixture from actual R2 BREP. NO PDE."""
import argparse,hashlib,json,time
from pathlib import Path
import gmsh,numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def run(brep,registry,out):
 if out.exists():raise ValueError('Refuse overwrite')
 out.mkdir(parents=True)
 a=json.loads(registry.read_text());names=a['domain_id_map']
 requested=['pin1','TEC_lead1','lead1_pin_joint','lead1_land_joint']
 tags={names[n]:n for n in requested}
 report={'status':'INCOMPLETE','input_brep_sha256':sha(brep),'source_registry_sha256':sha(registry),
  'selected_domains':requested,'no_pde':True}
 save(out/'meshability.json',report)
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
 gmsh.option.setNumber('General.NumThreads',4);gmsh.option.setNumber('Mesh.MaxNumThreads3D',4)
 start=time.monotonic()
 try:
  occ=gmsh.model.occ;occ.importShapes(str(brep));occ.synchronize()
  occ.remove([(3,t) for _,t in gmsh.model.getEntities(3) if t not in tags],recursive=True)
  occ.synchronize()
  if {t for _,t in gmsh.model.getEntities(3)}!=set(tags):raise ValueError('fixture source identity mismatch')
  for t,name in tags.items():gmsh.model.addPhysicalGroup(3,[t],t);gmsh.model.setPhysicalName(3,t,name)
  gmsh.option.setNumber('Mesh.MeshSizeMin',.01)
  gmsh.option.setNumber('Mesh.MeshSizeMax',.27)
  gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0)
  gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
  gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',30)
  gmsh.option.setNumber('Mesh.MinimumCirclePoints',32)
  gmsh.option.setNumber('Mesh.MinimumCurvePoints',16)
  gmsh.option.setNumber('Mesh.Algorithm3D',1)
  gmsh.model.mesh.generate(3)
  nids,coords,_=gmsh.model.mesh.getNodes();pts=np.asarray(coords).reshape(-1,3)
  lookup={int(n):i for i,n in enumerate(nids)};n=0;volumes={}
  for tag,name in tags.items():
   k,_,elements=gmsh.model.mesh.getElements(3,tag)
   if 4 not in k:raise ValueError('no linear tetrahedra '+name)
   ids=np.asarray(elements[list(k).index(4)],dtype=np.int64).reshape(-1,4)
   v=np.asarray([[lookup[int(j)] for j in row] for row in ids],dtype=int)
   p=pts[v];det=np.linalg.det(p[:,1:]-p[:,:1]);ifbad=np.abs(det)<1e-15
   if np.any(ifbad):raise ValueError('degenerate tetrahedron '+name)
   cv=occ.getMass(3,tag);mv=float(np.abs(det).sum()/6)
   if abs(mv/cv-1)>.01:raise ValueError('mesh CAD volume mismatch '+name)
   volumes[name]={'tets':len(ids),'cad_mm3':cv,'mesh_mm3':mv,'relative_volume_error':abs(mv/cv-1)}
   n+=len(ids)
  if n>350000:raise ValueError('local tet count exceeds 350k')
  gmsh.option.setNumber('Mesh.Binary',1)
  gmsh.write(str(out/'r2_lead_pin_local.msh'))
  report.update(status='PASS LOCAL R2 LEAD/PIN 3D MESH ONLY; GLOBAL/PDE NOT QUALIFIED',
    domain_count=len(tags),tetrahedra=n,nodes=len(nids),volumes=volumes,
    mesh_sha256=sha(out/'r2_lead_pin_local.msh'),elapsed_seconds=time.monotonic()-start)
  print('LOCAL R2 LEAD PASS',n,'tets',len(nids),'nodes',flush=True)
 except Exception as exc:
  report.update(status='STOP LOCAL R2 LEAD/PIN MESH',error=repr(exc),elapsed_seconds=time.monotonic()-start)
  raise
 finally:
  save(out/'meshability.json',report);gmsh.finalize()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--brep',type=Path,required=True)
 p.add_argument('--registry',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();run(a.brep,a.registry,a.out)
