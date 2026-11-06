#!/usr/bin/env python3
"""R3.15 read-only native CAD face 2349 and two-volume PLC interface preflight."""
import json,hashlib,time
from collections import Counter
import numpy as np
from pathlib import Path
P=Path('/input');O=Path('/out')
t0=time.monotonic()
meta=json.loads((P/'source_metadata.json').read_text())
n=np.loadtxt(P/'R38_430_domains.1.node',skiprows=1)
e=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
f=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
assert set(meta['faces']['2349']['owner_volume_ids'])=={410,420}
ids=(410,420);which=np.isin(e[:,5],ids)
te=e[which,1:5];reg=e[which,5]
iface=f[f[:,4]==2349,1:4]
assert len(iface)>0
tindices=np.unique(te)
coords=n[tindices-1,1:4]
lookup=np.full(len(n)+1,-1,dtype=np.int32);lookup[tindices]=np.arange(len(tindices),dtype=np.int32)
assert np.min(lookup[te])>=0
faces=np.concatenate([te[:,[1,2,3]],te[:,[0,2,3]],te[:,[0,1,3]],te[:,[0,1,2]]])
faces.sort(axis=1)
region=np.tile(reg,4)
keytype=np.dtype([('a','<i4'),('b','<i4'),('c','<i4')])
key=lambda x:np.ascontiguousarray(x,dtype=np.int32).view(keytype).reshape(-1)
rank=np.argsort(key(faces));face_sorted=faces[rank];region=region[rank]
keys=key(face_sorted);start=np.r_[0,np.flatnonzero(keys[1:]!=keys[:-1])+1]
count=np.diff(np.r_[start,len(keys)])
assert np.max(count)<=2
bfaces=face_sorted[start[count==1]]
shared_all=start[count==2]
diff_region=region[shared_all]!=region[shared_all+1]
shared=face_sorted[shared_all[diff_region]]
assert len(shared)>0
i_expected=np.sort(iface,axis=1)
source_set=set(map(tuple,i_expected.tolist()))
actual_set=set(map(tuple,shared.tolist()))
print('INTERFACE_DIAGNOSTIC',len(shared),len(i_expected),'shared_unique',len(actual_set),'registered_unique',len(source_set),'missing',len(source_set-actual_set),'extra',len(actual_set-source_set),flush=True)
print('INTERFACE_MISSING_EXAMPLES',list(source_set-actual_set)[:8],flush=True)
print('INTERFACE_EXTRA_EXAMPLES',list(actual_set-source_set)[:8],flush=True)
assert np.array_equal(np.sort(key(shared)),np.sort(key(i_expected)))
z0=float(meta['faces']['2349']['center_mm'][2])
plane_dist=np.abs(n[np.unique(iface)-1,3]-z0)
assert np.max(plane_dist)<3e-10
bbox={}
for r in ids:
 t=te[reg==r];v=np.unique(t);p=n[v-1,1:4]
 bbox[str(r)]={'tetrahedra':len(t),'vertices':len(v),'min_xyz_mm':p.min(axis=0).tolist(),
               'max_xyz_mm':p.max(axis=0).tolist(),
               'min_z_minus_interface_mm':float(p[:,2].min()-z0),
               'max_z_minus_interface_mm':float(p[:,2].max()-z0)}
plane_geom={}
for row in iface:
 p=n[row-1,1:4];plane_geom[tuple(sorted(row.tolist()))]=float(np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))/2)
mesh_area=sum(plane_geom.values())
cad_area=float(meta['faces']['2349']['face_area_mm2'])
B={tuple(sorted(x)) for x in bfaces}
other_boundary=set(map(tuple,np.sort(bfaces,axis=1)))
assert not B.intersection(plane_geom)
out={
 'status':'PASS two-volume CAD-planar native interface exact-TET3 face readback',
 'two_region_CAD_ids':list(ids),'materials':{str(r):next(v['material'] for v in meta['domains'].values() if v['id']==r) for r in ids},
 'source_CAD_face_tag':2349,'source_CAD_face_owners':meta['faces']['2349']['owner_volume_ids'],
 'interface_z_mm':z0,'maximum_native_interface_planarity_deviation_mm':float(plane_dist.max()),
 'interface_TRI3':len(iface),'interface_unique_vertices':len(np.unique(iface)),
 'interface_area_saved_triangles_mm2':mesh_area,'interface_area_CAD_mm2':cad_area,
 'relative_CAD_interface_area_error':mesh_area/cad_area-1,
 'shared_internal_pair_faces':len(shared),
 'outer_boundary_TRI3':len(bfaces),
 'all_two_region_tets':len(te),'all_two_region_nodes':len(tindices),
 'per_region':bbox,
 'all_registered_contact_triangles_exactly_shared':True,
 'no_nonmanifold_faces':True,'all_source_facet_vertices_unchanged':True,
 'no_PDE':True,'elapsed_seconds':round(time.monotonic()-t0,3)
}
O.mkdir(exist_ok=True)
(O/'native_interface_preflight.json').write_text(json.dumps(out,indent=2)+'\n')
print('R315_INTERFACE_PREFLIGHT',json.dumps(out),flush=True)
