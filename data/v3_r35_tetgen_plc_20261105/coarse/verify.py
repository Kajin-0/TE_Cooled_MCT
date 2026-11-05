import collections,hashlib,json,math,pathlib,time,resource
import numpy as np
root=pathlib.Path('/fixture')
start=time.monotonic()
src=json.loads((root/'fixture_reference.json').read_text())
def read_rows(suffix,cols):
 p=root/('coaxial_15um.1.'+suffix)
 with p.open() as f:
  first=next(f).split()
  rows=[]
  for raw in f:
   t=raw.split('#',1)[0].split()
   if not t:continue
   rows.append(tuple(int(t[j]) if j==0 or suffix in ('ele','face') or (suffix=='node' and j==0) else float(t[j]) for j in range(cols)))
 assert len(rows)==int(first[0]),(suffix,len(rows),first)
 return rows,first
node_rows,node_header=read_rows('node',4)
element_rows,element_header=read_rows('ele',6)
face_rows,face_header=read_rows('face',5)
assert int(element_header[1])==4 and int(element_header[2])==1,element_header
assert int(face_header[1])==1
assert int(node_header[1])==3
pts={int(n[0]):np.asarray(n[1:4],float) for n in node_rows}
original={int(n):np.asarray(v,float) for n,v in src['nodes'].items()}
added=set(pts)-set(original)
removed=set(original)-set(pts)
moved={k:float(np.linalg.norm(pts[k]-original[k])) for k in original.keys()&pts.keys() if np.any(pts[k]!=original[k])}
in_facets=collections.Counter(tuple(sorted(f[1:4])) for f in src['facets'])
out_facets=collections.Counter(tuple(sorted(f[1:4])) for f in face_rows)
missing=in_facets-out_facets;extra=out_facets-in_facets
marker={tuple(sorted(f[1:4])):int(f[0]) for f in src['facets']}
marker_bad=[(f,marker.get(tuple(sorted(f[1:4]))),f[4]) for f in face_rows if marker.get(tuple(sorted(f[1:4])))!=int(f[4])]
tets=np.asarray([row[1:5] for row in element_rows],int)
attrs=np.asarray([row[5] for row in element_rows],int)
assert len(set(row[0] for row in element_rows))==len(element_rows)
ids=sorted(pts);mapping={k:i for i,k in enumerate(ids)}
xyz=np.asarray([pts[k] for k in ids])
idx=np.array([[mapping[int(k)] for k in tet] for tet in tets])
v=xyz[idx]
delta=v[:,1:]-v[:,0:1]
signed=np.einsum('ni,ni->n',delta[:,0],np.cross(delta[:,1],delta[:,2]))/6
abs_vol=np.abs(signed)
quantity={int(a):int(np.sum(attrs==a)) for a in np.unique(attrs)}
volumes={name:float(np.sum(abs_vol[attrs==attr])) for name,attr in src['region_attributes'].items()}
rel={name:float(volumes[name]/src['CAD_volume_mm3'][name]-1) for name in volumes}
# Actual tetrahedral exterior and cross-material interior facets.
allfaces=np.concatenate([tets[:,[1,2,3]],tets[:,[0,2,3]],tets[:,[0,1,3]],tets[:,[0,1,2]]],axis=0)
face_regions=np.tile(attrs,4)
sfaces=np.sort(allfaces,axis=1)
order=np.lexsort((sfaces[:,2],sfaces[:,1],sfaces[:,0]))
sfaces=sfaces[order];face_regions=face_regions[order]
group_start=np.flatnonzero(np.r_[True,np.any(sfaces[1:]!=sfaces[:-1],axis=1)])
group_count=np.diff(np.r_[group_start,len(sfaces)])
max_mult=int(group_count.max())
actual=collections.Counter()
facetype=collections.Counter()
for i,count in zip(group_start,group_count):
 attr=face_regions[i:i+count]
 if count==1 or len(set(attr))==2:
  tri=tuple(int(x) for x in sfaces[i])
  actual[tri]+=1
  facetype[('exterior' if count==1 else 'interface',tuple(sorted(set(map(int,attr)))))] += 1
external_facets=collections.Counter(tuple(sorted(f[1:4])) for f in src['facets'])
interface_bad=(actual!=external_facets)
# Face-owner-to-tet region correspondence
inv_owners={tag:src['region_attributes'][name] for name,tag in src['CAD_volume_tags'].items()}
tet_face_reg={}
for i,count in zip(group_start,group_count):
 if count==1 or len(set(face_regions[i:i+count]))==2:
  tri=tuple(int(x) for x in sfaces[i])
  tet_face_reg[tri]=set(map(int,face_regions[i:i+count]))
ownership_errors=[]
for f in src['facets']:
 tag=int(f[0]);tri=tuple(sorted(f[1:4]))
 expected={inv_owners[v] for v in src['CAD_face_owners'][str(tag)]}
 actualowners=tet_face_reg.get(tri,set())
 if actualowners!=expected:
  ownership_errors.append((tag,tri,sorted(expected),sorted(actualowners)))
q=np.linalg.norm(delta,axis=2)
result={
 'status':'PENDING','input_facets':len(src['facets']),
 'output_facets':len(face_rows),'original_nodes':len(original),'output_nodes':len(pts),
 'added_steiner_nodes':len(added),'removed_original_nodes':len(removed),
 'moved_original_nodes':len(moved),'max_original_displacement_mm':max(moved.values(),default=0),
 'missing_input_facets':sum(missing.values()),'extra_output_facets':sum(extra.values()),
 'duplicate_input_facets':sum(v-1 for v in in_facets.values()),
 'duplicate_output_facets':sum(v-1 for v in out_facets.values()),
 'output_face_marker_errors':len(marker_bad),
 'tetrahedra':len(tets),'tetrahedra_by_attribute':quantity,
 'material_mesh_volume_mm3':volumes,
 'material_CAD_volume_mm3':src['CAD_volume_mm3'],
 'material_relative_volume_error':rel,
 'min_signed_tet_volume_mm3':float(np.min(signed)),
 'max_signed_tet_volume_mm3':float(np.max(signed)),
 'min_absolute_tet_volume_mm3':float(np.min(abs_vol)),
 'nonpositive_signed_tets':int(np.sum(signed<=0)),
 'nonpositive_absolute_tets':int(np.sum(abs_vol<=0)),
 'facets_max_incidence':max_mult,
 'nonmanifold_facets':int(sum(c>2 for c in group_count)),
 'tet_boundary_facets':sum(actual.values()),
 'tet_boundary_identity_errors':sum((actual-external_facets).values())+sum((external_facets-actual).values()),
 'tet_face_region_mismatch':len(ownership_errors),
 'actual_interface_region_pairs':{str(k):v for k,v in facetype.items()},
 'seconds':time.monotonic()-start,'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
}
result['status']='PASS STRICT FACET/OWNERSHIP/JACOBIAN/VOLUME GATES' if (
 len(element_rows)>0 and len(quantity)==3 and all(quantity.values()) and
 not removed and not moved and not missing and not extra and not marker_bad and not interface_bad and
 not ownership_errors and max_mult<=2 and np.all(signed>0) and
 all(abs(v)<.01 for v in rel.values())) else 'FAIL ONE OR MORE STRICT GATES'
(root/'verified_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
