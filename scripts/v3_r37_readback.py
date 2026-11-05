#!/usr/bin/env python3
"""Read-only independent PLC serialization, CAD seed clearance and budget audit."""
import collections,hashlib,json,math,pathlib,resource,time
import gmsh,numpy as np
ROOT=pathlib.Path('/work')
OUT=pathlib.Path('/work/data/v3_r37_plc_preflight_20261105/attempt01')
source=json.loads((ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json').read_text())
r=json.loads((ROOT/'data/v3_r37_plc_preflight_20261105/attempt01/result.json').read_text())
seeds=json.loads((ROOT/'data/v3_r37_plc_preflight_20261105/attempt01/region_seeds.json').read_text())
poly=ROOT/'data/v3_r37_plc_preflight_20261105/attempt01/R37_430_domains_surface.poly'
beg=time.monotonic()
def stream():
 with poly.open() as fh:
  def tokens():
   while True:
    line=next(fh).split('#',1)[0].split()
    if line:return line
  head=tokens()
  assert len(head)==4 and (int(head[0]),int(head[1]))==(156599,3)
  coords={}
  for _ in range(int(head[0])):
   q=tokens();coords[int(q[0])]=tuple(map(float,q[1:4]))
  assert len(coords)==156599
  header=tokens()
  assert (int(header[0]),int(header[1]))==(320522,1)
  per_face=collections.Counter()
  edge=collections.Counter()
  edges_by_volume=collections.defaultdict(collections.Counter)
  signatures=collections.Counter()
  for i in range(320522):
   h=tokens();p=tokens()
   assert int(h[0])==1 and int(h[1])==0 and len(p)==4 and int(p[0])==3
   face=int(h[2]);v=tuple(sorted(map(int,p[1:4])))
   per_face[face]+=1;signatures[v]+=1
   fowners=source['faces'][str(face)]['owner_volume_ids']
   for x,y in ((v[0],v[1]),(v[1],v[2]),(v[0],v[2])):
    edge[(x,y)]+=1
    for owner in fowners:edges_by_volume[owner][(x,y)]+=1
  assert tokens()==['0'] # no hole seeds
  nregions=tokens();assert int(nregions[0])==430
  regionrows=[tokens() for _ in range(430)]
  assert len({int(z[0]) for z in regionrows})==430
  return coords,per_face,edge,edges_by_volume,signatures,regionrows
coords,count,edges,edges_by_volume,signatures,rows=stream()
assert count==collections.Counter({int(k):v for k,v in r['face_triangle_counts'].items()})
assert set(count)==set(map(int,source['faces']))
assert set(map(int,(z[0] for z in rows)))==set(source['domain_id_map'].values())
assert all(len(t)==6 and int(t[0])==int(t[4]) for t in rows)
duplicate_triangles=sum(x-1 for x in signatures.values())
bad_edges=[(vol,k,v) for vol,ec in edges_by_volume.items() for k,v in ec.items() if v!=2]
assert not duplicate_triangles
# Per-domain closed skins: global shared-interface edges naturally have incidence >2.
assert len(bad_edges)==0, bad_edges[:10]
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
gmsh.model.occ.importShapes(str(ROOT/'data/v3_analysis_r3_20261103/geometry_restored/R3_conformal_mm.brep'))
gmsh.model.occ.synchronize()
owners=collections.defaultdict(list)
for k,f in source['faces'].items():
 for tag in f['owner_volume_ids']:owners[tag].append(int(k))
clearance={}
for i,(name,seed) in enumerate(sorted(seeds.items(),key=lambda p:p[1]['volume_id'])):
 tag=seed['volume_id'];p=np.asarray(seed['xyz_mm'],float)
 best=(math.inf,None)
 for f in owners[tag]:
  near,_=gmsh.model.getClosestPoint(2,f,p.tolist())
  near=np.asarray(near,float).reshape(-1,3)
  dist=float(np.linalg.norm(near[0]-p))
  if dist<best[0]:best=(dist,f)
 clearance[name]={'nearest_CAD_face_distance_mm':best[0],'nearest_face':best[1],
   'method':seed['method'],'material':seed['material']}
 if (i+1)%90==0:print('clearance',i+1,'/',len(seeds),'elapsed',round(time.monotonic()-beg,2),flush=True)
gmsh.finalize()
near=sorted(((v['nearest_CAD_face_distance_mm'],name) for name,v in clearance.items()))
tiny=[(name,float(dist)) for dist,name in near if dist<0.0005]
fallback=[(name,v) for name,v in clearance.items() if v['method']=='inward_verified_boundary_triangle']
# Count budget: only heuristic derived from earlier TetGen fixture, with a wide uncertainty interval.
ratio=15676/7106
estimate=320522*ratio
report={
 'status':'PASS EXACT PLC SERIALIZATION; REGION SEED CLEARANCE REVIEW REQUIRED' if tiny else 'PASS PLC SERIALIZATION AND CAD REGION SEED CLEARANCE',
 'file_sha256':hashlib.sha256(poly.read_bytes()).hexdigest(),
 'input_vertices':len(coords),'facet_count':sum(count.values()),'face_markers':len(count),
 'regions':len(rows),'duplicate_triplets':duplicate_triangles,
 'unique_global_edges':len(edges),'volume_edge_incidence_not_equal_two':len(bad_edges),
 'seed_clearance_min_mm':near[0][0],
 'seed_clearance_p01_mm':near[4][0],
 'seed_clearance_less_than_0p0005mm':tiny,
 'nearest_seed_clearances':near[:30],
 'estimated_tets_from_R35_fixture_ratio':int(estimate),
 'rough_sensitivity_tets_at_1x_2x_4x_fixture_ratio':[int(estimate*m) for m in (1,2,4)],
 'memory_qualification':'NOT MEASURED; TetGen real whole-package peak RSS cannot be inferred from fixture scaling',
 'no_tetra':True,'no_PDE':True,
 'seconds':round(time.monotonic()-beg,2),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
OUT.mkdir(exist_ok=True)
(OUT/'seed_clearances.json').write_text(json.dumps(clearance,indent=2)+'\n')
(OUT/'independent_plc_readback.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','facet_count','regions','duplicate_triplets','volume_edge_incidence_not_equal_two','seed_clearance_min_mm','seed_clearance_less_than_0p0005mm','rough_sensitivity_tets_at_1x_2x_4x_fixture_ratio','seconds')},indent=2),flush=True)
