#!/usr/bin/env python3
"""R3.10 fixed-R3.9 interior-node conditioning feasibility audit. READ ONLY."""
import collections,hashlib,json,resource,time
from pathlib import Path
import numpy as np
R38=Path('/r38')
R39=Path('/r39')
OUT=Path('/r310')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(4<<20),b''):h.update(x)
 return h.hexdigest()
t0=time.monotonic()
parent=json.loads((R39/'candidate_01/independent_audit.json').read_text())
nodepath=R38/'work/R38_430_domains.1.node'
facpath=R38/'work/R38_430_domains.1.face'
elepath=R39/'candidate_01/R39_430_domains.1.ele'
assert parent['status']=='PASS GEOMETRIC 3D GATES; QUALITY/PHYSICS UNQUALIFIED'
assert sha(elepath)==json.loads((R39/'candidate_01/result.json').read_text())['derived_ele_sha256']
node=np.loadtxt(nodepath,dtype=np.float64,skiprows=1)
tetrows=np.loadtxt(elepath,dtype=np.int32,skiprows=1)
facrows=np.loadtxt(facpath,dtype=np.int32,skiprows=1)
coords=node[:,1:4];tets=tetrows[:,1:5];regions=tetrows[:,5]
nnode=len(coords);norig=156599
assert nnode==156765 and len(tets)==1010119
boundary=np.unique(facrows[:,1:4])
inner_ids=np.setdiff1d(np.arange(1,nnode+1,dtype=np.int32),boundary)
assert len(inner_ids)==166,(len(inner_ids),inner_ids[:9])
assert inner_ids.min()>=norig+1
# Efficient node incidences via sparse adjacency; count and actual incident region
flat=tets.ravel()
qidx=np.arange(len(tets),dtype=np.int32).repeat(4)
order=np.argsort(flat,kind='stable')
ordered_nodes=flat[order]
ordered_tets=qidx[order]
inc_counts=np.bincount(flat,minlength=nnode+1)
offsets=np.r_[0,np.cumsum(inc_counts)]
v=coords[tets-1]
d0=v[:,1]-v[:,0];d1=v[:,2]-v[:,0];d2=v[:,3]-v[:,0]
vol=np.einsum('ij,ij->i',d0,np.cross(d1,d2))/6
ss=np.zeros(len(tets),np.float64)
for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
 e=v[:,i]-v[:,j];ss+=np.einsum('ij,ij->i',e,e)
q=12*np.power(3*np.abs(vol),2/3)/ss
assert np.all(vol>0)
out=[]
for k in inner_ids:
 pos=ordered_tets[offsets[k]:offsets[k+1]]
 reg,counts=np.unique(regions[pos],return_counts=True)
 assert len(reg)==1,('nonunique_region',int(k),list(reg))
 x=q[pos]
 star=tets[pos]
 other=np.unique(star)
 other=other[other!=k]
 bcount=int(np.count_nonzero(x<.05))
 out.append({'node':int(k),'incident_tets':len(pos),'region':int(reg[0]),'neighbor_nodes':len(other),
             'q_min':float(x.min()),'q_mean':float(x.mean()),'q_lt_0p05':bcount,
             'q_lt_0p01':int(np.count_nonzero(x<.01)),'q_p10':float(np.quantile(x,.10)),
             'node_xyz_mm':list(map(float,coords[k-1])),
             'centroid_of_neighbors_mm':list(map(float,coords[other-1].mean(axis=0)))})
removable_bad=np.zeros(len(tets),dtype=bool)
for k in inner_ids:
 removable_bad[ordered_tets[offsets[k]:offsets[k+1]]]=True
report={
 'status':'R3.10 READ ONLY 166 FREE-NODE ADJACENCY AND BAD-ELEMENT COVERAGE',
 'base_nodes':nnode,'base_tetrahedra':len(tets),
 'boundary_locked_nodes':len(boundary),'interior_nodes':len(inner_ids),
 'interior_node_region_count':len(set(x['region'] for x in out)),
 'interior_node_valence':{'min':int(min(x['incident_tets'] for x in out)),'median':float(np.median([x['incident_tets'] for x in out])),'max':int(max(x['incident_tets'] for x in out))},
 'global_bad_q_lt_0p05':int(np.count_nonzero(q<.05)),
 'bad_cells_adjacent_to_any_free_node':int(np.count_nonzero(removable_bad&(q<.05))),
 'bad_cells_without_free_node':int(np.count_nonzero(~removable_bad&(q<.05))),
 'globally_bad_below_0p01':int(np.count_nonzero(q<.01)),
 'bad_below_0p01_with_free_node':int(np.count_nonzero(removable_bad&(q<.01))),
 'free_nodes_in_bad_stars':int(sum(x['q_lt_0p05']>0 for x in out)),
 'worst_interior_node_stars':sorted(out,key=lambda x:x['q_min'])[:25],
 'highest_bad_count_stars':sorted(out,key=lambda x:-x['q_lt_0p05'])[:25],
 'all_interior_nodes':out,
 'original_R39_element_sha256':sha(elepath),
 'original_R38_node_sha256':sha(nodepath),
 'no_mesh_mutation':True,'PDE':'NOT RUN',
 'elapsed_seconds':round(time.monotonic()-t0,2),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
OUT.mkdir(exist_ok=True)
(OUT/'free_node_census.json').write_text(json.dumps(report,indent=2)+'\n')
print('R310_FREE_NODE_CENSUS',json.dumps({k:report[k] for k in ('status','interior_nodes','interior_node_region_count','interior_node_valence','global_bad_q_lt_0p05','bad_cells_adjacent_to_any_free_node','bad_cells_without_free_node','bad_below_0p01_with_free_node','free_nodes_in_bad_stars','elapsed_seconds','peak_RSS_MiB')},indent=2),flush=True)
print('WORST_NODE_STARS',json.dumps(report['worst_interior_node_stars'][:6],indent=2),flush=True)
