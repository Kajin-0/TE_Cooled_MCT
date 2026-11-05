from pathlib import Path
import json,numpy as np,resource,time,hashlib
p=Path('/fixture');started=time.monotonic()
t=time.monotonic()
nodes={}
with (p/'coaxial_15um.1.node').open() as fh:
 n=int(next(fh).split()[0])
 for s in fh:
  q=s.split('#',1)[0].split()
  if q:nodes[int(q[0])]=[float(x) for x in q[1:4]]
tets=[];attr=[]
with (p/'coaxial_15um.1.ele').open() as fh:
 m=int(next(fh).split()[0])
 for s in fh:
  q=s.split('#',1)[0].split()
  if q:tets.append([int(x) for x in q[1:5]]);attr.append(int(q[5]))
a=np.array([nodes[k] for k in sorted(nodes)])
mapping={k:i for i,k in enumerate(sorted(nodes))}
t=np.asarray([[mapping[v] for v in tet] for tet in tets],int)
xyz=a[t]
edge=np.array([xyz[:,i]-xyz[:,j] for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))])
edge_sq=np.sum(edge**2,axis=2)
v=np.abs(np.linalg.det(np.stack((xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0],xyz[:,3]-xyz[:,0]),axis=1)))/6
q=12*(3*v)**(2/3)/np.sum(edge_sq,axis=0)
assert np.all(np.isfinite(q)) and (q>0).all()
by={str(i):{'tetrahedra':int(np.sum(np.asarray(attr)==i)),
             'quality_min':float(q[np.asarray(attr)==i].min()),
             'quality_median':float(np.median(q[np.asarray(attr)==i]))} for i in sorted(set(attr))}
result={'status':'PASS FINITE POSITIVE TET SHAPE QUALITY; DISTRIBUTION REPORTED',
'metric':'mean-ratio quality 12*(3V)^(2/3)/sum_six_edges_squared; regular tet=1',
'min':float(q.min()),'p01':float(np.quantile(q,.01)),
'p05':float(np.quantile(q,.05)),'median':float(np.median(q)),
'p95':float(np.quantile(q,.95)),'max':float(q.max()),
'quality_below_0p01':int((q<.01).sum()),
'quality_below_0p05':int((q<.05).sum()),
'quality_below_0p1':int((q<.1).sum()),
'per_region':by,'wall_seconds':time.monotonic()-started}
(p/'quality_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
