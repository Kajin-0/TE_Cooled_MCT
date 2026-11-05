#!/usr/bin/env python3
"""R3.9 exact-R3.8 read-only edge-star quality feasibility census."""
import json,hashlib,time,resource
from pathlib import Path
import numpy as np
W=Path('/r38'); OUT=Path('/r39')
t0=time.monotonic()
r=json.loads((W/'independent_audit.json').read_text())
assert r['status']=='PASS GEOMETRIC 3D GATES; QUALITY/PHYSICS UNQUALIFIED'
name=W/'work/R38_430_domains.1.ele'
h=hashlib.sha256(name.read_bytes()).hexdigest()
assert h==r['tetgen_output_sha256'][name.name]
e=np.loadtxt(name,dtype=np.int32,skiprows=1)
assert len(e)==1043314 and len(e[0])==6
t=np.ascontiguousarray(e[:,1:5])
reg=e[:,5]
quality=np.loadtxt(W/'work/R38_430_domains.1.node',dtype=np.float64,skiprows=1)
xyz=quality[:,1:4]; quality=None
v=xyz[t-1]
v0=v[:,1]-v[:,0];v1=v[:,2]-v[:,0];v2=v[:,3]-v[:,0]
vol=np.einsum('ij,ij->i',v0,np.cross(v1,v2))/6
ss=np.zeros(len(t))
for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
 d=v[:,i]-v[:,j];ss+=np.einsum('ij,ij->i',d,d)
q=12*np.power(3*vol,2/3)/ss
del v,v0,v1,v2,vol,ss
assert np.all(np.isfinite(q))
ids=np.arange(len(t),dtype=np.int32)
edge=[]
for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
 a=np.minimum(t[:,i],t[:,j]);b=np.maximum(t[:,i],t[:,j])
 edge.append(np.column_stack((a,b,ids)))
edges=np.concatenate(edge)
print('all_edge_incidence_records',len(edges),'RSS_MiB',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,flush=True)
del edge
order=np.lexsort((edges[:,1],edges[:,0]))
edges=edges[order];del order
st=np.r_[0,np.flatnonzero(np.any(edges[1:,:2]!=edges[:-1,:2],axis=1))+1]
ct=np.diff(np.r_[st,len(edges)])
s3=st[ct==3]
triplets=edges[s3[:,None]+np.arange(3),2]
same=(reg[triplets[:,0]]==reg[triplets[:,1]])&(reg[triplets[:,0]]==reg[triplets[:,2]])
bad=(q[triplets]<.05).sum(axis=1)
report={
 'source_ele_sha256':h,'tetrahedra':len(t),'node_count':len(xyz),
 'edge_incidence_records':len(edges),'unique_mesh_edges':len(st),
 'edge_incidence_distribution':{str(k):int(v) for k,v in zip(*np.unique(ct,return_counts=True))},
 'exact_three_incident_edges':len(s3),
 'same_material_three_tet_edges':int(same.sum()),
 'same_material_three_tet_edges_with_at_least_one_bad_cell':int((same&(bad>0)).sum()),
 'same_material_three_tet_edges_with_two_or_more_bad_cells':int((same&(bad>=2)).sum()),
 'bad_cell_quality_threshold':.05,'global_bad_cells':int((q<.05).sum()),
 'source_material_domain_attribute_count':len(set(reg)),
 'read_only':True,'full_global_mesh_remeshing':False,'PDE':False,
 'seconds':round(time.monotonic()-t0,2),
 'RSS_peak_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'edge_feasibility.json').write_text(json.dumps(report,indent=2)+'\n')
print('R39_FEASIBILITY',json.dumps(report),flush=True)
