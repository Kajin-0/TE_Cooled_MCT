#!/usr/bin/env python3
"""R3.13 independent reconstructed nested-centroid mesh topology and quality audit.
Never modifies original source R39 and R38; no PDE.
"""
from pathlib import Path
import json,time,resource
import numpy as np
P=Path('/input');O=Path('/out')
t0=time.monotonic()
node=np.loadtxt(P/'R38_430_domains.1.node',skiprows=1)
element=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
fac=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
metadata=json.loads((P/'source_metadata.json').read_text())
tglobal=element[element[:,5]==420,1:5]
nglobal=np.unique(tglobal)
node_lookup=np.full(len(node)+1,-1,dtype=np.int32)
node_lookup[nglobal]=np.arange(len(nglobal))
t=node_lookup[tglobal]
v=node[nglobal-1,1:4].copy()
tags=[int(k) for k,x in metadata['faces'].items() if 420 in x['owner_volume_ids']]
registered=np.sort(node_lookup[fac[np.isin(fac[:,4],tags),1:4]],axis=1)
kdt=np.dtype([('a',np.int32),('b',np.int32),('c',np.int32)])
def keys(a):return np.ascontiguousarray(a,dtype=np.int32).view(kdt).reshape(-1)
registered_keys=np.sort(keys(registered))
assert len(registered_keys)==13540 and len(np.unique(registered_keys))==len(registered_keys)
res=[]
for level in range(3):
 p=v[t]
 J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
 det=np.linalg.det(J)
 nonpositive=int(np.count_nonzero(det<=0))
 assert nonpositive==0,('bad_oriented',level,nonpositive)
 volume=det/6
 ff=np.concatenate([t[:,[1,2,3]],t[:,[0,2,3]],t[:,[0,1,3]],t[:,[0,1,2]]])
 ff.sort(axis=1)
 ordered=np.sort(keys(ff))
 starts=np.r_[0,np.flatnonzero(ordered[1:]!=ordered[:-1])+1]
 counts=np.diff(np.r_[starts,len(ordered)])
 assert np.max(counts)<=2
 bound=ordered[starts[counts==1]]
 assert len(bound)==len(registered_keys)
 assert np.array_equal(bound,registered_keys),('boundary_facets_drift',level)
 assert len(np.unique(bound))==len(registered_keys)
 edgesq=np.zeros(len(t))
 for i,j in [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]:
  d=p[:,i]-p[:,j]
  edgesq+=np.einsum('ti,ti->t',d,d)
 q=12*np.power(3*volume,2/3)/edgesq
 measure={'level':level,'nodes':len(v),'tetrahedra':len(t),
          'boundary_TRI3':len(bound),'exact_native_boundary_match':True,
          'nonmanifold_faces_over_two':0,'nonpositive_tetrahedra':nonpositive,
          'total_region_volume_mm3':float(volume.sum()),
          'minimum_normalized_quality':float(q.min()),
          'q_below_0p05':int(np.count_nonzero(q<.05)),
          'q_below_0p01':int(np.count_nonzero(q<.01)),
          'elapsed_seconds':round(time.monotonic()-t0,2)}
 res.append(measure)
 print('R313_TOPOLOGY',json.dumps(measure),flush=True)
 if level<2:
  new=v[t].mean(axis=1)
  n=len(v)
  newid=np.arange(n,n+len(t),dtype=np.int32)
  t=np.concatenate((
   np.column_stack((t[:,2],t[:,1],t[:,3],newid)),
   np.column_stack((t[:,3],t[:,0],t[:,2],newid)),
   np.column_stack((t[:,1],t[:,0],t[:,3],newid)),
   np.column_stack((t[:,2],t[:,0],t[:,1],newid))
  ))
  v=np.vstack((v,new))
assert all(abs(x['total_region_volume_mm3']/res[0]['total_region_volume_mm3']-1)<1e-9 for x in res)
report={'status':'PASS ALL THREE EXACT CONSTRAINED NATIVE SURFACE FACET AND VOLUME SKIN GATES',
        'source':'R3.9 saved region420 tetrahedra + R3.8 preserved original face set',
        'output_levels':res,'no_source_mutation':True,'full_device_PDE':'NOT RUN',
        'elapsed_seconds':round(time.monotonic()-t0,2),
        'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2)}
(O/'independent_refinement_topology.json').write_text(json.dumps(report,indent=2)+'\n')
print('R313_TOPOLOGY_PASS',report['elapsed_seconds'],flush=True)
