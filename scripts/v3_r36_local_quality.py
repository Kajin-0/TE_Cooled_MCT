#!/usr/bin/env python3
"""R3.6 bounded 3-to-2 local quality optimization of R3.5 TetGen fixture."""
import argparse,collections,hashlib,json,math,pathlib,time
P=pathlib.Path
ap=argparse.ArgumentParser()
ap.add_argument('--prefix',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args();start=time.monotonic();prefix=P(a.prefix);out=P(a.out)
if out.exists():raise RuntimeError('Output exists: NO OVERWRITE')
def rows(suf):
 path=P(str(prefix)+suf); lines=[x.split('#')[0].split() for x in path.read_text().splitlines()]
 lines=[x for x in lines if x]
 assert len(lines)-1==int(lines[0][0])
 return lines[1:]
nodes={int(r[0]):tuple(map(float,r[1:4])) for r in rows('.node')}
origface={tuple(sorted(map(int,r[1:4]))):int(r[4]) for r in rows('.face')}
tets=[(tuple(map(int,r[1:5])),int(r[5])) for r in rows('.ele')]
assert (len(nodes),len(origface),len(tets))==(3493,7106,15676)
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def metric(ns):
 x=[nodes[v] for v in ns];v=dot(sub(x[1],x[0]),cross(sub(x[2],x[0]),sub(x[3],x[0])))/6
 ed=sum(dot(sub(x[i],x[j]),sub(x[i],x[j])) for i in range(4) for j in range(i))
 return v,12*(3*abs(v))**(2/3)/ed
def positive(n):
 n=list(n)
 if metric(n)[0]<0:n[0],n[1]=n[1],n[0]
 return tuple(n)
FACE=((1,2,3),(0,2,3),(0,1,3),(0,1,2))
def faces(n):return [tuple(sorted(n[j] for j in ids)) for ids in FACE]
def boundary(ts):
 c=collections.Counter(f for n in ts for f in faces(n))
 return tuple(sorted(f for f,v in c.items() if v==1))
def globalboundary(mesh):
 d=collections.defaultdict(list)
 for ns,region in mesh:
  for f in faces(ns):d[f].append(region)
 assert all(1<=len(v)<=2 for v in d.values())
 return {f:tuple(sorted(v)) for f,v in d.items() if len(v)==1 or len(set(v))==2}
def stats(mesh):
 scores=[];vol={1:0.,2:0.,3:0.};nonpos=0
 for n,r in mesh:
  v,q=metric(n);scores.append(q);vol[r]+=v;nonpos+=(v<=0)
 scores.sort()
 return {'tets':len(mesh),'minimum_quality':scores[0],'p01':scores[int(.01*(len(scores)-1))],
         'median':scores[int(.5*(len(scores)-1))],'below_0p05':sum(q<.05 for q in scores),
         'below_0p01':sum(q<.01 for q in scores),'nonpositive':nonpos,'volumes_mm3':vol}
baseline=stats(tets);reference=globalboundary(tets)
assert len(reference)==7106 and set(reference)==set(origface)
manifest=[];rounds=[]
for iteration in range(1,4):
 edge=collections.defaultdict(list)
 for i,(ns,r) in enumerate(tets):
  for a in range(4):
   for b in range(a):
    edge[tuple(sorted((ns[a],ns[b])))].append(i)
 candidates=[]
 for pair,indexes in edge.items():
  if len(indexes)!=3:continue
  old=[tets[i] for i in indexes]
  if len(set(r for _,r in old))!=1:continue
  uniq=set(n for ns,_ in old for n in ns)
  if len(uniq)!=5:continue
  ring=sorted(uniq-set(pair))
  replacement=[positive((*ring,pair[0])),positive((*ring,pair[1]))]
  if boundary([ns for ns,_ in old])!=boundary(replacement):continue
  b=[metric(ns) for ns,_ in old];c=[metric(ns) for ns in replacement]
  if any(v<1e-13 for v,q in c):continue
  if abs(sum(v for v,q in b)-sum(v for v,q in c))>1e-9*max(1e-12,sum(v for v,q in b)):continue
  nbad=sum(q<.05 for v,q in b)-sum(q<.05 for v,q in c)
  improvement=min(q for v,q in c)-min(q for v,q in b)
  if nbad>0 and improvement>1e-8:
   candidates.append((nbad,improvement,tuple(indexes),replacement,old[0][1],pair))
 candidates.sort(key=lambda c:(-c[0],-c[1],c[2]))
 chosen=[];used=set()
 for c in candidates:
  if not any(i in used for i in c[2]):
   chosen.append(c);used.update(c[2])
 if not chosen:break
 nxt=[t for i,t in enumerate(tets) if i not in used]
 for c in chosen:
  nxt.extend((ns,c[4]) for ns in c[3])
  manifest.append({'round':iteration,'old_indices':list(c[2]),'new_nodes':[list(x) for x in c[3]],'region':c[4],'edge':list(c[5])})
 if globalboundary(nxt)!=reference:raise RuntimeError('Facet ownership/identity changed')
 now=stats(nxt);prev=stats(tets)
 assert now['nonpositive']==0 and now['below_0p05']<prev['below_0p05']
 assert all(abs(now['volumes_mm3'][r]-baseline['volumes_mm3'][r])<1e-9*baseline['volumes_mm3'][r] for r in (1,2,3))
 tets=nxt;rounds.append({'pass':iteration,'accepted_flips':len(chosen),'stats':now})
 assert time.monotonic()-start<110,'Timeout'
final=stats(tets);assert len(tets)==15483 and final['below_0p05']==176 and len(manifest)==193
assert globalboundary(tets)==reference
out.mkdir(parents=True)
for suffix in ('.node','.face'):
 (out/('candidate'+suffix)).write_bytes(P(str(prefix)+suffix).read_bytes())
with (out/'candidate.ele').open('w') as f:
 f.write(f'{len(tets)} 4 1\n')
 for i,(n,r) in enumerate(tets,1):f.write(f'{i} {" ".join(map(str,n))} {r}\n')
report={'status':'PASS LOCAL 3-TO-2 FIXTURE SCREEN; GLOBAL OVERLAP/PDE NOT RUN',
 'source_prefix':str(prefix),'baseline':baseline,'passes':rounds,'final':final,
 'flips':len(manifest),'facets':len(reference),'source_nodes':len(nodes),
 'source_shas':{x:hashlib.sha256(P(str(prefix)+x).read_bytes()).hexdigest() for x in ('.node','.ele','.face')},
 'limitations':['Not a whole 430-domain mesh','Global intersection and FEM convergence not audited','Minimum quality remains poor']}
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'flips.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'result':report['status'],'flips':len(manifest),'initial':baseline,'final':final},indent=2))
