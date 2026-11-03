"""Targeted directional surface mesh with exact face-area feedback; no PDE."""
from pathlib import Path
import argparse,gzip,hashlib,json,math,time,resource,collections
import numpy as np
import gmsh
from scripts.v3_analysis_r3_geometry import read,save,sha,R2

def triangles():
    ids,xyz,_=gmsh.model.mesh.getNodes();p=np.asarray(xyz).reshape(-1,3)
    ids=np.asarray(ids,dtype=np.int64);lookup=np.full(int(ids.max())+1,-1,np.int64);lookup[ids]=np.arange(len(ids))
    return p,lookup

def areas(registry):
    p,lookup=triangles();records={};count=0
    for key,face in registry.items():
        f=int(key);kinds,tags,el=gmsh.model.mesh.getElements(2,f)
        if list(kinds)!=[2]:raise ValueError('Missing/nontriangular surface '+key)
        tri=lookup[np.asarray(el[0],dtype=np.int64).reshape(-1,3)];v=p[tri]
        av=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0])/2;a=np.linalg.norm(av,axis=1)
        if np.any(a<=1e-16):raise ValueError('Nonpositive surface triangle')
        exact=face['face_area_mm2'];n=len(tri);count+=n
        records[key]=dict(face=f,triangles=n,CAD_mm2=exact,mesh_mm2=float(a.sum()),relative_error=float(a.sum()/exact-1))
    return records,count,len(p)

def reference(out):
    if out.exists():raise ValueError('Preserve reference replay')
    out.mkdir(parents=True);start=time.monotonic()
    source=R2/'global_surface_area_pass_VOLUME_UNQUALIFIED.msh.gz';manifest=read(R2/'release_manifest.json')
    raw=out/'reference.msh'
    with gzip.open(source,'rb') as src,raw.open('wb') as dst:
        h=hashlib.sha256()
        while piece:=src.read(1<<20):h.update(piece);dst.write(piece)
    if h.hexdigest()!=manifest['decompressed_surface_mesh_sha256']:raise ValueError('R2 reference mesh hash changed')
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
    try:
        gmsh.open(str(raw));reg=read(R2/'physical_to_analysis_registry.json')['face_registry']
        rows,ntri,nnodes=areas(reg)
        failures=[k for k,v in rows.items() if abs(v['relative_error'])>=.01]
        if failures or ntri!=1416664 or nnodes!=701952:raise ValueError('Accepted reference replay failed')
        save(out/'reference.json',dict(status='PASS independent accepted-MSH replay',triangles=ntri,nodes=nnodes,faces=rows,
            max_error=max(abs(v['relative_error']) for v in rows.values()),mesh_sha256=h.hexdigest(),
            seconds=time.monotonic()-start,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
    finally:gmsh.finalize()

def vertices(curve):return [abs(t) for d,t in gmsh.model.getBoundary([(1,curve)],combined=False,oriented=True)]

def configure(reg,reference_data,feedback,previous_plan=None):
    oc=gmsh.model.occ;rows=reg['face_registry'];edge_faces=collections.defaultdict(set);fedges={};quads={};sizes={};counts={}
    ancestry=collections.defaultdict(list)
    for parent,children in reg['R2_face_descendants'].items():
        for f in children:ancestry[int(f)].append(parent)
    for key,q in rows.items():
        f=int(key);edges=list(dict.fromkeys(abs(t) for d,t in gmsh.model.getBoundary([(2,f)],combined=False,oriented=True)))
        fedges[f]=edges
        for e in edges:edge_faces[e].add(f)
        typ=gmsh.model.getType(2,f);lo,hi=gmsh.model.getParametrizationBounds(2,f)
        kk=0.
        if typ!='Plane':
            uv=[(1-a)*lo+a*hi for a in (.25,.5,.75)]
            for v in uv:
                try:
                    k1,k2,d1,d2=gmsh.model.getPrincipalCurvatures(f,v)
                    kk=max(kk,abs(float(k1[0])),abs(float(k2[0])))
                except Exception:raise ValueError('Unmeasured face curvature '+key)
        h=min(.30,.20/kk) if kk>1e-7 else .30
        old=[reference_data['faces'][p] for p in ancestry[f]]
        if old and kk>1e-7:
            # Measured reference error/area sets a candidate isotropic scale;
            # directional transfinite faces independently avoid axial oversizing.
            h_error=min(math.sqrt(2*v['CAD_mm2']/max(v['triangles'],1))*math.sqrt(.004/max(abs(v['relative_error']),1e-6)) for v in old)
            h=min(h,h_error)
        previous=feedback.get(key)
        factor=max(1.,math.sqrt(abs(previous['relative_error'])/.004)) if previous and abs(previous['relative_error'])>=.01 else 1.
        if previous_plan:h=min(h,previous_plan['face_h_mm'][str(f)])
        sizes[f]=max(.0015,h/factor)
        # Only genuine four-edge/four-corner curved faces are structured.
        vv={v for e in edges for v in vertices(e)}
        if kk>1e-7 and len(edges)==4 and len(vv)==4:
            adjacency=collections.defaultdict(list)
            for e in edges:
                ends=vertices(e)
                if len(ends)!=2 or ends[0]==ends[1]:break
                for v in ends:adjacency[v].append(e)
            else:
                if all(len(a)==2 for a in adjacency.values()):
                    v=next(iter(adjacency));corners=[];walk=[];prev=None
                    for _ in range(4):
                        corners.append(v);e=next(e for e in adjacency[v] if e!=prev);walk.append(e)
                        ends=vertices(e);v=ends[0] if ends[1]==v else ends[1];prev=e
                    if len(set(walk))==4:quads[f]=(corners,walk,factor)
    for d,e in gmsh.model.getEntities(1):
        length=oc.getMass(1,e);lo,hi=gmsh.model.getParametrizationBounds(1,e)
        samples=np.linspace(float(lo[0]),float(hi[0]),9)
        k=np.asarray(gmsh.model.getCurvature(1,e,samples));kmax=float(abs(k).max())
        if not np.isfinite(kmax):raise ValueError('Nonfinite edge curvature')
        critical=any(any(n.startswith(('TEC_lead','lead1_insulation','lead9_insulation','detector_bond')) for n in rows[str(f)]['owners']) for f in edge_faces[e])
        h=.08 if critical else .30
        n=max(1,math.ceil(length/h),math.ceil(length*kmax/(math.pi/24)))
        factor=max([quads[f][2] for f in edge_faces[e] if f in quads]+[1.])
        if previous_plan:n=max(n,previous_plan['shared_edge_counts'][str(e)])
        counts[e]=max(1,math.ceil(n*factor))
    # Union opposing-edge count constraints; shared edges have one global DOF.
    parent={e:e for e in counts}
    def find(e):
        while parent[e]!=e:parent[e]=parent[parent[e]];e=parent[e]
        return e
    for corners,es,factor in quads.values():
        for a,b in ((es[0],es[2]),(es[1],es[3])):parent[find(a)]=find(b)
    maximal={}
    for e,n in counts.items():maximal[find(e)]=max(maximal.get(find(e),0),n)
    for e in counts:counts[e]=maximal[find(e)];gmsh.model.mesh.setTransfiniteCurve(e,counts[e]+1)
    for f,(corners,es,factor) in quads.items():gmsh.model.mesh.setTransfiniteSurface(f,'AlternateLeft',corners)
    def callback(dim,tag,x,y,z,lc):
        if dim==2:return min(lc,sizes.get(tag,.30))
        return lc
    gmsh.model.mesh.setSizeCallback(callback)
    return dict(curved_quad_faces=len(quads),shared_edge_counts={str(k):v for k,v in counts.items()},face_h_mm={str(k):v for k,v in sizes.items()},quad_face_tags=sorted(quads))

def mesh(brep,registry,ref,out):
    if out.exists():raise ValueError('Preserve surface attempt')
    out.mkdir(parents=True);start=time.monotonic();reg=read(registry);rd=read(ref)
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4)
    gmsh.option.setNumber('Mesh.MaxNumThreads2D',4);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    gmsh.option.setNumber('Mesh.MeshSizeMin',.0015);gmsh.option.setNumber('Mesh.MeshSizeMax',.30)
    gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',0)
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0);gmsh.option.setNumber('Mesh.MinimumCirclePoints',12)
    gmsh.option.setNumber('Mesh.Algorithm',6);gmsh.logger.start()
    gmsh.option.setNumber('Mesh.SaveAll',1)
    try:
        gmsh.model.occ.importShapes(str(brep));gmsh.model.occ.synchronize()
        if set(reg['domain_id_map'].values())!={t for d,t in gmsh.model.getEntities(3)}:raise ValueError('CAD domain ID mismatch')
        for name,t in reg['domain_id_map'].items():gmsh.model.addPhysicalGroup(3,[t],t);gmsh.model.setPhysicalName(3,t,name)
        for key,q in reg['face_registry'].items():
            f=int(key)
            if sorted(map(int,gmsh.model.getAdjacencies(2,f)[0]))!=q['owner_volume_ids']:raise ValueError('Face owner mismatch')
            gmsh.model.addPhysicalGroup(2,[f],f);gmsh.model.setPhysicalName(2,f,'R3_face_'+key)
        feedback={};previous_plan=None
        for attempt in range(3):
            if attempt:gmsh.model.mesh.clear()
            attemptdir=out/('surface_'+str(attempt));attemptdir.mkdir()
            plan=configure(reg,rd,feedback,previous_plan);save(attemptdir/'size_plan.json',plan)
            then=time.monotonic();gmsh.model.mesh.generate(2)
            rows,n,nodes=areas(reg['face_registry'])
            bad=[k for k,v in rows.items() if abs(v['relative_error'])>=.01]
            parents={}
            for p,children in reg['R2_face_descendants'].items():
                exact=sum(rows[str(f)]['CAD_mm2'] for f in children);actual=sum(rows[str(f)]['mesh_mm2'] for f in children)
                parents[p]=dict(CAD_mm2=exact,mesh_mm2=actual,relative_error=actual/exact-1)
            pb=[p for p,v in parents.items() if abs(v['relative_error'])>=.01]
            gate=dict(status='PASS' if not bad and not pb and n<=800000 else 'FAIL',triangles=n,nodes=nodes,
                failed_faces=bad,failed_R2_parents=pb,face_count=len(rows),R2_parent_count=len(parents),
                max_face_relative_error=max(abs(v['relative_error']) for v in rows.values()),
                rows=rows,R2_parents=parents,seconds=time.monotonic()-then,
                peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                reference_triangle_reduction=1416664/n,triangle_budget=800000,no_PDE=True)
            gmsh.write(str(attemptdir/'surface.msh'));gate['mesh_sha256']=sha(attemptdir/'surface.msh')
            save(attemptdir/'gate.json',gate);print('SURFACE',attempt,gate['status'],n,'triangles',len(bad),'face fails','RSS',gate['peak_RSS_MiB'],flush=True)
            if gate['status']=='PASS':save(out/'gate.json',dict(status='PASS',accepted=str(attemptdir),seconds=time.monotonic()-start));return
            if n>800000:save(out/'gate.json',dict(status='STOP SURFACE BUDGET',last=str(attemptdir)));return
            feedback=rows;previous_plan=plan
        save(out/'gate.json',dict(status='STOP SURFACE AREA GATE',last=str(attemptdir),no_3D=True))
    finally:
        save(out/'gmsh_tail.json',gmsh.logger.get()[-80:]);gmsh.logger.stop();gmsh.finalize()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('role',choices=['reference','mesh']);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--brep',type=Path);p.add_argument('--registry',type=Path);p.add_argument('--reference',type=Path)
    a=p.parse_args();reference(a.out) if a.role=='reference' else mesh(a.brep,a.registry,a.reference,a.out)
