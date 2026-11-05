import collections,hashlib,json,math,pathlib,resource,time
import gmsh,numpy as np
root=pathlib.Path('/fixture');start=time.monotonic()
gmsh.initialize()
gmsh.option.setNumber('General.Terminal',0)
gmsh.model.add('R35_coaxial_Cu_15um_PI_gas')
shapes=[gmsh.model.occ.addCylinder(0,0,0,0,0,.4,r) for r in (.10,.115,.22)]
gmsh.model.occ.fragment([(3,k) for k in shapes],[])
gmsh.model.occ.synchronize()
seeds={'copper_core':(.05,0,.2),'polyimide_15um':(.108,0,.2),'gas':(.18,0,.2)}
attributes={name:i+1 for i,name in enumerate(seeds)}
owners={};cad_vol={}
for name,point in seeds.items():
 matches=[int(t) for _,t in gmsh.model.getEntities(3) if gmsh.model.isInside(3,t,list(point),False)]
 assert len(matches)==1,(name,matches)
 tag=matches[0]
 owners[name]=tag
 cad_vol[name]=float(gmsh.model.occ.getMass(3,tag))
assert len(set(owners.values()))==3
gmsh.option.setNumber('Mesh.MeshSizeMin',.007)
gmsh.option.setNumber('Mesh.MeshSizeMax',.022)
gmsh.model.mesh.generate(2)
nids,xyz,_=gmsh.model.mesh.getNodes()
nids=np.asarray(nids,dtype=np.int64)
xyz=np.asarray(xyz,dtype=float).reshape(-1,3)
assert len(nids)==len(set(nids))
nid_map={int(k):i+1 for i,k in enumerate(nids)}
points={i+1:tuple(float(x) for x in xyz[i]) for i in range(len(nids))}
faces=[];face_owner={};tag_types=collections.Counter()
for _,f in gmsh.model.getEntities(2):
 f=int(f)
 dims,elems,cells=gmsh.model.mesh.getElements(2,f)
 assert list(dims)==[2],(f,dims)
 triangles=np.asarray(cells[0],dtype=np.int64).reshape(-1,3)
 owners_for_face=[int(v) for v in gmsh.model.getAdjacencies(2,f)[0]]
 assert 1<=len(owners_for_face)<=2
 face_owner[str(f)]=owners_for_face
 tag_types[len(owners_for_face)]+=len(triangles)
 for tr in triangles:
  idx=tuple(nid_map[int(v)] for v in tr)
  faces.append((f,idx))
assert len(faces)>1000 and len(gmsh.model.getEntities(3))==3
assert len({tuple(sorted(tr)) for _,tr in faces})==len(faces)
p=root/'coaxial_15um.poly'
with p.open('w') as out:
 out.write(f'{len(points)} 3 0 0\n')
 for k,xyz in points.items():out.write(f'{k} {xyz[0]:.17g} {xyz[1]:.17g} {xyz[2]:.17g}\n')
 out.write(f'{len(faces)} 1\n')
 for f,tr in faces:
  out.write(f'1 0 {f}\n3 {tr[0]} {tr[1]} {tr[2]}\n')
 out.write('0\n')
 out.write(f'{len(seeds)}\n')
 for name,point in seeds.items():
  out.write(f'{attributes[name]} {point[0]} {point[1]} {point[2]} {attributes[name]} -1\n')
data=dict(status='PLC INPUT CREATED; NOT TETRA QUALIFIED',
  model='concentric cylindrical copper core r=0.1mm / 15um polyimide annulus to r=0.115mm / gas to r=0.22mm, L=0.4mm',
  nodes={str(k):list(v) for k,v in points.items()},
  facets=[[f,*tr] for f,tr in faces],
  CAD_face_owners=face_owner,CAD_volume_tags=owners,CAD_volume_mm3=cad_vol,
  region_attributes=attributes,regions={name:list(point) for name,point in seeds.items()},
  face_counts={str(k):int(v) for k,v in tag_types.items()},
  surface_triangles=len(faces),input_nodes=len(points),single_surface_facet_per_interface=True,
  gmsh_version=gmsh.__version__,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
  seconds=time.monotonic()-start,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
(root/'fixture_reference.json').write_text(json.dumps(data,indent=2)+'\n')
print('INPUT',{'surface_faces':len(face_owner),'facets':len(faces),'nodes':len(points),'face_owners':dict(tag_types),'CADvol':cad_vol,'sha256':data['source_sha256'],'elapsed':round(time.monotonic()-start,2)},flush=True)
gmsh.finalize()
