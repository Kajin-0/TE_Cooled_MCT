#!/usr/bin/env python3
"""R3.8 independent saved TetGen 3D audit; source PLC and historical CAD read only."""
import collections,hashlib,json,math,resource,time
from pathlib import Path
import numpy as np

ROOT=Path("/work")
RUN=Path("/trial")
WORK=RUN/"work"
SOURCE=ROOT/"data/v3_r37_plc_preflight_20261105/seed_refined_01"
EXPECTED=SOURCE/"R37_430_domains_surface_seed_refined.poly"
ORIGINAL=RUN/"work/R38_430_domains.poly"
FACE=WORK/"R38_430_domains.1.face"
NODE=WORK/"R38_430_domains.1.node"
ELE=WORK/"R38_430_domains.1.ele"
RESULT=RUN/"independent_audit.json"
CAD=json.loads((ROOT/"data/v3_r32_global_surface_20261103/source_metadata.json").read_text())
PREFLIGHT=json.loads((ROOT/"data/v3_r37_plc_preflight_20261105/seed_refined_01/independent_plc_readback.json").read_text())
RECORD=json.loads((ROOT/"data/v3_r37_plc_preflight_20261105/attempt01/result.json").read_text())
start=time.monotonic()
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(4<<20),b""):h.update(block)
 return h.hexdigest()
def save(obj):
 tmp=RESULT.with_suffix(".json.tmp")
 tmp.write_text(json.dumps(obj,indent=2)+"\n")
 tmp.replace(RESULT)
def stage(msg):
 print("AUDIT",msg,"seconds",round(time.monotonic()-start,2),flush=True)
assert sha(EXPECTED)==sha(ORIGINAL)==PREFLIGHT["file_sha256"],"input hash drift"
assert sha(NODE) and sha(ELE) and sha(FACE)
stage("loading node and element records")
node=np.loadtxt(NODE,dtype=np.float64,skiprows=1)
ele=np.loadtxt(ELE,dtype=np.int64,skiprows=1)
fac=np.loadtxt(FACE,dtype=np.int64,skiprows=1)
assert node.shape[1]==4 and ele.shape[1]==6 and fac.shape[1]==5
assert len(node)==int(NODE.open().readline().split()[0])
assert len(ele)==int(ELE.open().readline().split()[0])
assert len(fac)==int(FACE.open().readline().split()[0])
assert len(node)==156765 and len(ele)==1043314 and len(fac)==320522
assert np.array_equal(node[:,0].astype(np.int64),np.arange(1,len(node)+1))
assert np.array_equal(ele[:,0],np.arange(1,len(ele)+1))
assert len(set(fac[:,0]))==len(fac)
xyz=np.asarray(node[:,1:4],dtype=np.float64)
tets=np.asarray(ele[:,1:5],np.int32)
region=np.asarray(ele[:,5],np.int32)
assert tets.min()>=1 and tets.max()<=len(node)
assert set(map(int,np.unique(region)))==set(CAD["domain_id_map"].values())
stage("loading source PLC for exact node, triangle and marker comparisons")
# Parse exactly one known header / all node records / all simplex facets / 430 regions.
with ORIGINAL.open() as f:
 head=list(map(int,f.readline().split()))
 assert (head[0],head[1])==(156599,3)
 orig=np.fromiter((float(v) for _ in range(head[0]) for v in f.readline().split()[:4]),dtype=float,count=4*head[0]).reshape(-1,4)
 assert np.array_equal(orig[:,0].astype(np.int64),np.arange(1,head[0]+1))
 assert np.array_equal(orig,node[:len(orig)]), "Moved or renumbered input node"
 h=list(map(int,f.readline().split()))
 assert (h[0],h[1])==(320522,1)
 known=np.empty((h[0],4),dtype=np.int32)
 for i in range(h[0]):
  marker=f.readline().split()
  tri=f.readline().split()
  assert int(marker[0])==1 and int(marker[1])==0 and len(tri)==4 and tri[0]=='3'
  known[i,0]=int(marker[2]);known[i,1:]=list(map(int,tri[1:4]))
 assert f.readline().strip()=="0"
 assert f.readline().strip()=="430"
 attr_from_plc={}
 for _ in range(430):
  a=f.readline().split()
  assert len(a)==6
  attr_from_plc[int(a[0])]=int(a[4])
 assert not f.read().strip()
def canon(m):
 a=np.ascontiguousarray(m.copy())
 a[:,1:]=np.sort(a[:,1:],axis=1)
 ix=np.lexsort((a[:,3],a[:,2],a[:,1],a[:,0]))
 return a[ix]
canonical_known=canon(known)
actual_faces=np.column_stack((fac[:,4],fac[:,1:4])).astype(np.int32)
canonical_actual=canon(actual_faces)
flag_exact=np.array_equal(canonical_known,canonical_actual)
assert flag_exact,"TetGen did not preserve native face tags and node triplets exactly"
input_tags=set(range(1,156600))
new_nodes=set(map(int,node[156599:,0]))
boundary_nodes=set(map(int,fac[:,1:4].ravel()))
assert not new_nodes&boundary_nodes, "Steiner node on constrained surface"
stage("signed 3D volumes and shape metrics on every saved tetrahedron")
v=xyz[tets-1]
a=v[:,1]-v[:,0];b=v[:,2]-v[:,0];c=v[:,3]-v[:,0]
cross=np.cross(b,c)
vol=np.einsum("ij,ij->i",a,cross)/6
nonpos=int(np.count_nonzero(vol<=0))
assert np.all(np.isfinite(vol)),"nonfinite signed tetrahedron volume"
lens=np.zeros(len(tets),dtype=np.float64)
for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
 d=v[:,i]-v[:,j]
 lens+=np.einsum("ij,ij->i",d,d)
q=12*np.power(3*np.abs(vol),2/3)/lens
assert np.all(np.isfinite(q)),"nonfinite quality"
quality={"min":float(q.min()),"p01":float(np.quantile(q,.01)),
 "p05":float(np.quantile(q,.05)),"median":float(np.median(q)),
 "below_0p01":int(np.count_nonzero(q<.01)),
 "below_0p05":int(np.count_nonzero(q<.05)),
 "below_0p1":int(np.count_nonzero(q<.1)),
 "nonpositive_signed":nonpos}
region_volume={}
volume_errors={}
region_counts={}
for name,tag in CAD["domain_id_map"].items():
 idx=region==tag
 region_counts[name]=int(idx.sum())
 measured=float(vol[idx].sum())
 expected=RECORD["CAD_volume_mm3"][name]
 region_volume[name]=measured
 volume_errors[name]=(measured/expected)-1
maxvol=max((abs(v),k,v) for k,v in volume_errors.items())
missing_regions=[k for k,n in region_counts.items() if n==0]
stage("building tetrahedral face complex and checking global manifold/interface ownership")
# Facet multiset: 4 oriented (here sorted) faces per tet. A conformal 3D mesh
# must use each facet once (exterior) or twice (interior), never >2.
ff=np.concatenate((tets[:,[1,2,3]],tets[:,[0,2,3]],tets[:,[0,1,3]],tets[:,[0,1,2]]),axis=0)
ff.sort(axis=1)  # in-place sort; prior call discarded sorted return
rr=np.tile(region,4)
order=np.lexsort((ff[:,2],ff[:,1],ff[:,0]))
ff=ff[order]
rr=rr[order]
new=np.empty(len(ff),dtype=bool)
new[0]=True
new[1:]=np.any(ff[1:]!=ff[:-1],axis=1)
beg=np.flatnonzero(new)
count=np.diff(np.r_[beg,len(ff)])
nonmanifold=int(np.count_nonzero(count>2))
assert nonmanifold==0,"Tetrahedral faces with >2 incident tetrahedra"
types=np.full(len(beg),0,np.int8)
types[count==1]=1
types[(count==2)&(rr[beg]!=rr[np.minimum(beg+1,len(rr)-1)])]=2
interface_positions=np.flatnonzero(types>0)
boundary_complex=np.ascontiguousarray(ff[beg[interface_positions]])
boundary_types=types[interface_positions]
boundary_first=rr[beg[interface_positions]]
boundary_second=rr[np.minimum(beg[interface_positions]+1,len(rr)-1)]
expected_triangles=np.sort(np.ascontiguousarray(fac[:,1:4],np.int32),axis=1)
# Construct one structured face-key vocabulary and resolve every saved .face
keytype=np.dtype([('a','<i4'),('b','<i4'),('c','<i4')])
def keys(x):return np.ascontiguousarray(x).view(keytype).reshape(-1)
bk=keys(boundary_complex)
fk=keys(expected_triangles)
bindex=np.argsort(bk)
found_sorted=bk[bindex]
found=np.searchsorted(found_sorted,fk)
valid=(found<len(found_sorted))
valid[valid]=found_sorted[found[valid]]==fk[valid]
missing_count=int(np.count_nonzero(~valid))
extra_count=int(len(boundary_complex)-len(fac)+missing_count)
assert missing_count==0 and extra_count==0,("Input facet/tet boundary disagreement",missing_count,extra_count)
matched=bindex[found]
observed_n=boundary_types[matched]
a1=boundary_first[matched]
a2=boundary_second[matched]
owner_count=np.array([len(CAD["faces"][str(k)]["owner_volume_ids"]) for k in fac[:,4]],dtype=np.int8)
native_owner1=np.array([CAD["faces"][str(k)]["owner_volume_ids"][0] for k in fac[:,4]],dtype=np.int32)
native_owner2=np.array([CAD["faces"][str(k)]["owner_volume_ids"][-1] for k in fac[:,4]],dtype=np.int32)
# Owner identity verified against the actual tetrahedra on each constrained face.
exterior=(owner_count==1)
owner_mismatches=int(
 np.count_nonzero(owner_count!=observed_n)+
 np.count_nonzero(a1[exterior]!=native_owner1[exterior])+
 np.count_nonzero((np.minimum(a1[~exterior],a2[~exterior])!=native_owner1[~exterior])|
                  (np.maximum(a1[~exterior],a2[~exterior])!=native_owner2[~exterior])))
# Material owners verified by real tet incidence, including 378 finite witness faces.
bad_contacts=[]
face_id_set=set(map(int,fac[:,4]))
for item in CAD["source_contacts"]:
 for face in item["face_tags"]:
  if face not in face_id_set:
   bad_contacts.append(item["index"])
# Compute per region stats and budgets.
estimated_tet_budget=3000000
overall_pass=(flag_exact and nonpos==0 and not missing_regions and
 not nonmanifold and missing_count==0 and extra_count==0 and
 owner_mismatches==0 and not bad_contacts and
 len(tets)<=estimated_tet_budget and maxvol[0]<.01)
status="PASS GEOMETRIC 3D GATES; QUALITY/PHYSICS UNQUALIFIED" if overall_pass else "FAIL ONE OR MORE GLOBAL 3D GEOMETRIC GATES"
report={
 "status":status,"source_input_sha256":sha(EXPECTED),
 "tetgen_output_sha256":{p.name:sha(p) for p in (NODE,ELE,FACE)},
 "surface_original_node_positions_unchanged":True,
 "added_nonboundary_nodes":len(new_nodes),"nodes":len(node),
 "tetrahedra":len(ele),"PLC_regions":430,"nonempty_tet_regions":len(region_counts)-len(missing_regions),
 "missing_region_names":missing_regions,
 "original_native_facet_triplets_and_face_markers_unchanged":flag_exact,
 "constrained_facets":len(fac),
 "tet_faces_with_nonmanifold_incidence":nonmanifold,
 "original_facets_missing_from_tet_boundary_or_interfaces":missing_count,
 "unregistered_tet_boundary_or_material_interface_facets":extra_count,
 "tet_to_CAD_interface_owner_mismatches":owner_mismatches,
 "missing_finite_contact_witnesses":bad_contacts,
 "volume_error_max_absolute":maxvol[0],"volume_error_worst_region":maxvol[1],
 "volume_error_worst_signed":maxvol[2],
 "volume_error_regions_above_1pct":{k:v for k,v in volume_errors.items() if abs(v)>=.01},
 "volume_error_all":volume_errors,"region_tet_counts":region_counts,
 "quality_mean_ratio":quality,"tetrahedron_budget_3million":len(tets)<=estimated_tet_budget,
 "global_facet_self_intersections":"NOT INDEPENDENTLY RECHECKED POST TET",
 "solver_conditioning":"NOT RUN","PDE":"NOT RUN",
 "elapsed_seconds":round(time.monotonic()-start,2),
 "peak_RSS_MiB":round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2)
}
save(report)
print("FINAL_STATUS",status,flush=True)
for k in ("tetrahedra","nodes","added_nonboundary_nodes","constrained_facets",
          "nonempty_tet_regions","tet_faces_with_nonmanifold_incidence",
          "original_facets_missing_from_tet_boundary_or_interfaces",
          "unregistered_tet_boundary_or_material_interface_facets",
          "tet_to_CAD_interface_owner_mismatches","volume_error_max_absolute",
          "volume_error_worst_region","volume_error_regions_above_1pct",
          "quality_mean_ratio","elapsed_seconds","peak_RSS_MiB"):
 print(k,":",report[k] if k!="volume_error_regions_above_1pct" else list(report[k].items())[:10],flush=True)
