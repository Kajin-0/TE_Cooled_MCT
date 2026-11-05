#!/usr/bin/env python3
"""R3.10 one-pass bounded interior-node relocation. Preserves all fixed 156599 nodes."""
import hashlib,json,time,resource
from pathlib import Path
import numpy as np
R38=Path('/r38')
R39=Path('/r39')
W=Path('/r310')
OUT=W/'candidate01'
if OUT.exists():raise RuntimeError('Refuse to overwrite existing candidate')
start=time.monotonic()
baseline=json.loads((R39/'candidate_01/independent_audit.json').read_text())
census=json.loads((W/'free_node_census.json').read_text())
assert baseline['status']=='PASS GEOMETRIC 3D GATES; QUALITY/PHYSICS UNQUALIFIED'
nodefile=R38/'work/R38_430_domains.1.node'
tetfile=R39/'candidate_01/R39_430_domains.1.ele'
facefile=R38/'work/R38_430_domains.1.face'
def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(4<<20),b''):h.update(x)
 return h.hexdigest()
assert hashfile(tetfile)==census['original_R39_element_sha256']
assert hashfile(nodefile)==census['original_R38_node_sha256']
N=np.loadtxt(nodefile,dtype=np.float64,skiprows=1)
E=np.loadtxt(tetfile,dtype=np.int32,skiprows=1)
F=np.loadtxt(facefile,dtype=np.int32,skiprows=1)
coords=N[:,1:4].copy()
tets=np.ascontiguousarray(E[:,1:5])
regions=E[:,5]
boundary=np.unique(F[:,1:4])
interior=np.setdiff1d(np.arange(1,len(coords)+1,dtype=np.int32),boundary)
assert len(interior)==166 and np.all(interior>156599)
sorted_inc=np.argsort(tets.ravel(),kind='stable')
keys=tets.ravel()[sorted_inc]
refs=np.repeat(np.arange(len(tets),dtype=np.int32),4)[sorted_inc]
counts=np.bincount(keys,minlength=len(coords)+1)
offs=np.r_[0,np.cumsum(counts)]
def metric(tindex, p_override=None,nodeid=None):
 tn=tets[tindex]
 v=coords[tn-1].copy()
 if p_override is not None:
  mask=(tn==nodeid)
  v[mask]=p_override
 a=v[:,1]-v[:,0];b=v[:,2]-v[:,0];c=v[:,3]-v[:,0]
 signed=np.einsum('ij,ij->i',a,np.cross(b,c))/6
 denom=np.zeros(len(tindex))
 for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
  d=v[:,i]-v[:,j];denom+=np.einsum('ij,ij->i',d,d)
 q=12*np.power(3*np.abs(signed),2/3)/denom
 return signed,q
all_ids=np.arange(len(tets),dtype=np.int32)
vol0,q0=metric(all_ids)
assert np.all(vol0>0)
base_bad=int(np.count_nonzero(q0<.05))
base_critical=int(np.count_nonzero(q0<.01))
base_min=float(q0.min())
original_region_volume=np.bincount(regions,weights=vol0,minlength=431)
# Test candidates in descending count of quality-poor incident elements,
# with all constraints re-evaluated against current moved node positions.
records=[];moved=[]
candidates=sorted(census['all_interior_nodes'],key=lambda v:(-v['q_lt_0p05'],v['node']))
for rank,entry in enumerate(candidates):
 n=int(entry['node'])
 incident=refs[offs[n]:offs[n+1]]
 before_vol,before_q=metric(incident)
 cur=coords[n-1].copy()
 neighbor=np.unique(tets[incident]);neighbor=neighbor[neighbor!=n]
 targetmean=coords[neighbor-1].mean(axis=0)
 targetmedian=np.median(coords[neighbor-1],axis=0)
 targets=(('neighbor_mean',targetmean),('neighbor_median',targetmedian))
 trials=[]
 old_bad=int(np.count_nonzero(before_q<.05))
 old_critical=int(np.count_nonzero(before_q<.01))
 old_floor=float(before_q.min())
 orig_volume_sum=float(before_vol.sum())
 for name,target in targets:
  for alpha in (.025,.05,.1,.15,.25,.35,.5,.75,1.0):
   new=cur+alpha*(target-cur)
   signed,q=metric(incident,new,n)
   if np.any(signed<=1e-13) or not np.all(np.isfinite(q)):continue
   drift=abs(float(signed.sum())-orig_volume_sum)
   if drift>max(1e-12,orig_volume_sum*1e-9):continue
   bad=int(np.count_nonzero(q<.05))
   critical=int(np.count_nonzero(q<.01))
   floor=float(q.min())
   if critical>old_critical:continue
   if bad>old_bad:continue
   if floor<old_floor-1e-10:continue
   if (bad<old_bad or (floor>old_floor*(1+0.05) and old_bad>0)):
    trials.append((old_bad-bad,old_critical-critical,floor-old_floor,alpha,name,new,signed,q))
 if trials:
  trials.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
  best=trials[0]
  # Allow only actual poor-element count improvement, not a cosmetic floor-only move
  if best[0]>0:
   coords[n-1]=best[5]
   moved.append(n)
   records.append({'node':n,'region':int(entry['region']),'initial_xyz_mm':cur.tolist(),
    'optimized_xyz_mm':best[5].tolist(),'method':best[4],'alpha':best[3],
    'old_q_min':old_floor,'new_q_min':float(best[7].min()),
    'old_bad_below_0p05':old_bad,'new_bad_below_0p05':int(np.count_nonzero(best[7]<.05)),
    'old_below_0p01':old_critical,'new_below_0p01':int(np.count_nonzero(best[7]<.01)),
    'regional_volume_sum_delta_mm3':float(best[6].sum()-orig_volume_sum)})
 if (rank+1)%40==0:
  print('NODE_RELOCATION_PROGRESS',rank+1,'of',len(candidates),'accepted',len(records),
   'elapsed',round(time.monotonic()-start,2),flush=True)
 if time.monotonic()-start>100:raise TimeoutError('R3.10 relocation must finish <100s')
v1,q1=metric(all_ids)
assert np.all(v1>0)
n_bad=int(np.count_nonzero(q1<.05))
n_critical=int(np.count_nonzero(q1<.01))
v1regions=np.bincount(regions,weights=v1,minlength=431)
max_drift=float(np.max(np.abs(v1regions[1:]-original_region_volume[1:])/original_region_volume[1:]))
assert n_bad<=base_bad and n_critical<=base_critical and float(q1.min())>=base_min-1e-10
assert max_drift<1e-8
assert np.array_equal(coords[:156599],N[:156599,1:4])
assert np.array_equal(coords[boundary-1],N[boundary-1,1:4])
OUT.mkdir(parents=True)
new_node=OUT/'R310_430_domains.1.node'
with new_node.open('w') as f:
 f.write(f'{len(coords)} 3 0 0\n')
 for i,p in enumerate(coords,1):
  f.write(f'{i} {p[0]:.17g} {p[1]:.17g} {p[2]:.17g}\n')
note={'status':'CANDIDATE R3.10 INTERIOR-ONLY NODE RELOCATION; INDEPENDENT FULL AUDIT REQUIRED',
 'baseline_tets':len(tets),'boundary_nodes_fixed':len(boundary),'movable_nodes':len(interior),
 'accepted_relocations':len(records),'bad_tets_before':base_bad,'bad_tets_after':n_bad,
 'q_below_0p01_before':base_critical,'q_below_0p01_after':n_critical,
 'q_min_before':base_min,'q_min_after':float(q1.min()),
 'max_region_volume_drift_relative':max_drift,
 'original_source_node_sha256':hashfile(nodefile),'original_source_ele_sha256':hashfile(tetfile),
 'candidate_node_sha256':hashfile(new_node),
 'all_material_interface_nodes_locked':True,'no_tetrahedral_connectivity_change':True,
 'global_intersection_check':'NOT YET RUN','PDE':'NOT RUN',
 'seconds':round(time.monotonic()-start,2),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
(OUT/'result.json').write_text(json.dumps(note,indent=2)+'\n')
(OUT/'accepted_relocations.json').write_text(json.dumps(records,indent=2)+'\n')
print('R310_RESULT',json.dumps(note,indent=2),flush=True)
