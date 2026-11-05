#!/usr/bin/env python3
"""R3.9: one-pass strictly conservative R3.8 local 3-to-2 quality optimization.
Preserves all node coordinates, registered facets, and region volumes.
Output is a separately versioned .ele candidate; original R3.8 files are READ-ONLY.
"""
import collections,hashlib,json,time,resource
from pathlib import Path
import numpy as np
R38=Path('/r38')
R39=Path('/r39')
OUT=R39/'candidate_01'
if OUT.exists():raise RuntimeError('Refuse to overwrite candidate')
t0=time.monotonic()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
source=json.loads((R38/'independent_audit.json').read_text())
nodefile=R38/'work/R38_430_domains.1.node'
elefile=R38/'work/R38_430_domains.1.ele'
facfile=R38/'work/R38_430_domains.1.face'
assert sha(elefile)==source['tetgen_output_sha256'][elefile.name]
assert source['status'].startswith('PASS GEOMETRIC 3D')
node=np.loadtxt(nodefile,skiprows=1)
xyz=np.ascontiguousarray(node[:,1:4])
ele=np.loadtxt(elefile,dtype=np.int32,skiprows=1)
tets=np.ascontiguousarray(ele[:,1:5])
regions=np.ascontiguousarray(ele[:,5])
assert len(tets)==1043314 and len(xyz)==156765
def vector_metrics(ids):
 p=xyz[ids-1]
 d0=p[:,1]-p[:,0];d1=p[:,2]-p[:,0];d2=p[:,3]-p[:,0]
 signed=np.einsum('ij,ij->i',d0,np.cross(d1,d2))/6
 ed=np.zeros(len(ids),dtype=float)
 for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
  d=p[:,i]-p[:,j];ed+=np.einsum('ij,ij->i',d,d)
 q=12*np.power(3*np.abs(signed),2/3)/ed
 return signed,q
signed,q=vector_metrics(tets)
assert np.all(signed>0)
start_stats={
 'n_tets':len(tets),'q_min':float(q.min()),
 'q_lt_0p01':int(np.count_nonzero(q<.01)),'q_lt_0p05':int(np.count_nonzero(q<.05)),
 'q_p01':float(np.quantile(q,.01))}
print('R39_BASELINE',start_stats,'s',round(time.monotonic()-t0,2),flush=True)
# Build exact edge-star incidence: consider only edges with precisely three incident cells.
ids=np.arange(len(tets),dtype=np.int32)
blocks=[]
for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
 blocks.append(np.column_stack((np.minimum(tets[:,i],tets[:,j]),
                                np.maximum(tets[:,i],tets[:,j]),ids)))
edges=np.concatenate(blocks);del blocks
order=np.lexsort((edges[:,1],edges[:,0]));edges=edges[order];del order
beg=np.r_[0,np.flatnonzero(np.any(edges[1:,:2]!=edges[:-1,:2],axis=1))+1]
inc=np.diff(np.r_[beg,len(edges)])
s3=beg[inc==3]
trip=edges[s3[:,None]+np.arange(3),2]
same=(regions[trip[:,0]]==regions[trip[:,1]])&(regions[trip[:,0]]==regions[trip[:,2]])
bad=np.sum(q[trip]<.05,axis=1)
candidate_rows=np.flatnonzero(same&(bad>0))
print('R39_SCREENING_START',len(candidate_rows),'s',round(time.monotonic()-t0,2),flush=True)
del beg,inc,same,bad,ids
def calc_one(ns):
 p=xyz[np.asarray(ns,np.int32)-1]
 a=p[1]-p[0];b=p[2]-p[0];c=p[3]-p[0]
 vol=float(np.dot(a,np.cross(b,c))/6)
 edge_sq=sum(float(np.dot(p[i]-p[j],p[i]-p[j]))
             for i in range(4) for j in range(i))
 return vol,12*(3*abs(vol))**(2/3)/edge_sq
def orient(ns):
 n=list(ns)
 if calc_one(n)[0]<0:n[0],n[1]=n[1],n[0]
 return tuple(n)
FACES=((1,2,3),(0,2,3),(0,1,3),(0,1,2))
def skin(cells):
 counts=collections.Counter()
 for cell in cells:
  for face in FACES:
   counts[tuple(sorted(cell[j] for j in face))]+=1
 return tuple(sorted(f for f,n in counts.items() if n==1))
# Note: local conservation check compares each five-node cavity's boundary, not the global outer boundary alone.
candidates=[];stats=collections.Counter()
for z,index in enumerate(candidate_rows):
 i,j,k=(int(x) for x in trip[index])
 star=(i,j,k);old=[tuple(map(int,tets[a])) for a in star]
 pair=tuple(map(int,edges[s3[index],:2]))
 uniq=set(old[0])|set(old[1])|set(old[2])
 if len(uniq)!=5 or not set(pair).issubset(uniq):stats['bad_star_topology']+=1;continue
 ring=tuple(sorted(uniq-set(pair)))
 if len(ring)!=3:continue
 # Three ring triangle pair combinations must appear once, guaranteeing a legitimate edge star.
 sides=collections.Counter(tuple(sorted(set(n)-set(pair))) for n in old)
 if set(sides)!={(ring[0],ring[1]),(ring[0],ring[2]),(ring[1],ring[2])} or any(v!=1 for v in sides.values()):
  stats['bad_ring_topology']+=1;continue
 replacement=[orient((*ring,pair[0])),orient((*ring,pair[1]))]
 after=[calc_one(ns) for ns in replacement]
 if any(v<=1e-13 or not np.isfinite(qu) for v,qu in after):stats['bad_new_volume']+=1;continue
 oldv=float(signed[i]+signed[j]+signed[k])
 newv=sum(v for v,qu in after)
 if abs(newv-oldv)>max(1e-13,1e-9*oldv):
  stats['nonconservative']+=1;continue
 if skin(old)!=skin(replacement):
  stats['cavity_skin_change']+=1;continue
 before_q=[float(q[i]),float(q[j]),float(q[k])]
 after_q=[qu for v,qu in after]
 before_bad=sum(z<.05 for z in before_q);after_bad=sum(z<.05 for z in after_q)
 if after_bad>=before_bad:
  stats['no_bad_cell_count_gain']+=1;continue
 if min(after_q)<=min(before_q)+1e-8:
  stats['no_floor_gain']+=1;continue
 if sum(z<.01 for z in after_q)>sum(z<.01 for z in before_q):
  stats['increased_critical_count']+=1;continue
 candidates.append({
  'star':star,'old_edge':pair,'new_nodes':replacement,
  'region':int(regions[i]),'bad_removed':before_bad-after_bad,
  'min_quality_gain':min(after_q)-min(before_q),
  'new_quality':after_q})
 if len(candidates)%250==0:
  print('R39_VALID',len(candidates),'seen',z+1,'elapsed',round(time.monotonic()-t0,1),flush=True)
 if time.monotonic()-t0>160:raise TimeoutError('Screening budget 160 seconds exceeded')
print('R39_GEOMETRIC_CANDIDATES',len(candidates),'elapsed',round(time.monotonic()-t0,1),flush=True)
# Maximal disjoint batch; deterministic tie breaks.
candidates.sort(key=lambda a:(-a['bad_removed'],-a['min_quality_gain'],a['star']))
used=np.zeros(len(tets),dtype=bool)
selected=[]
for c in candidates:
 if any(used[i] for i in c['star']):continue
 for i in c['star']:used[i]=True
 selected.append(c)
print('R39_DISJOINT_ACCEPTED',len(selected),'removed',3*len(selected),'added',2*len(selected),'elapsed',round(time.monotonic()-t0,1),flush=True)
if not selected:
 OUT.mkdir(parents=True)
 (OUT/'result.json').write_text(json.dumps({'status':'STOP ZERO ACCEPTED FLIPS','screening':dict(stats)},indent=2)+'\n')
 raise SystemExit(0)
keep=~used
newt=np.asarray([n for c in selected for n in c['new_nodes']],np.int32)
newr=np.asarray([c['region'] for c in selected for _ in c['new_nodes']],np.int32)
candidate_tets=np.concatenate((tets[keep],newt))
candidate_reg=np.concatenate((regions[keep],newr))
assert len(candidate_tets)==len(tets)-len(selected)
new_signed,new_q=vector_metrics(candidate_tets)
assert np.all(new_signed>0) and np.all(np.isfinite(new_q))
oldvol=np.bincount(regions,weights=signed,minlength=431)
newvol=np.bincount(candidate_reg,weights=new_signed,minlength=431)
reldrift=np.max(np.abs(newvol[1:]-oldvol[1:])/oldvol[1:])
assert reldrift<1e-8,('material volume drift',reldrift)
result_stats={'n_tets':len(candidate_tets),'q_min':float(new_q.min()),
 'q_lt_0p01':int(np.count_nonzero(new_q<.01)),
 'q_lt_0p05':int(np.count_nonzero(new_q<.05)),
 'q_p01':float(np.quantile(new_q,.01))}
assert result_stats['q_lt_0p05']<start_stats['q_lt_0p05']
assert result_stats['q_lt_0p01']<=start_stats['q_lt_0p01']
assert result_stats['q_min']>=start_stats['q_min']-1e-10
OUT.mkdir(parents=True)
# Derived .ele in TetGen 1-based numbering; node and face records stay in original R3.8 archive.
derived=OUT/'R39_430_domains.1.ele'
with derived.open('w') as f:
 f.write(f'{len(candidate_tets)} 4 1\n')
 for i,(tet,attr) in enumerate(zip(candidate_tets,candidate_reg),1):
  f.write(f'{i} {tet[0]} {tet[1]} {tet[2]} {tet[3]} {attr}\n')
report={'status':'CANDIDATE LOCAL QUALITY IMPROVEMENT; INDEPENDENT GLOBAL 3D AUDIT REQUIRED',
 'baseline':start_stats,'candidate':result_stats,'accepted_3_to_2_flips':len(selected),
 'candidate_edges_scanned':len(candidate_rows),'valid_candidates':len(candidates),
 'rejects':dict(stats),'CAD_region_volume_max_relative_drift':float(reldrift),
 'source_ele_sha256':sha(elefile),'derived_ele_sha256':sha(derived),
 'original_fixed_boundary_facets_unchanged_by_local_skin_check':True,
 'global_facet_validation':'PENDING INDEPENDENT AUDIT',
 'PDE':'NOT RUN','seconds':round(time.monotonic()-t0,2),
 'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
(OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'selected_flips.json').write_text(json.dumps(selected,indent=2)+'\n')
print('R39_RESULT',json.dumps(report),flush=True)
