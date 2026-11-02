"""Versioned curvature-mesh producer; unchanged frozen coupon BREP and ports.
Derived from sealed v3_et_geometry.mesh; only curvature discretization changes.
"""
import time
from pathlib import Path
import numpy as np
from .v3_et_geometry import read,write,sha,qualify_faces,PORTS

def mesh(out,geometry,h):
    import gmsh
    if out.exists():raise ValueError('Preserve mesh')
    out.mkdir(parents=True);start=time.monotonic();geo=read(geometry/'geometry.json')
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',1);gmsh.option.setString('Geometry.OCCTargetUnit','MM');gmsh.option.setNumber('General.NumThreads',4)
    try:
        occ=gmsh.model.occ;tags=occ.importShapes(str(geometry/'coupon_mm.brep'));occ.synchronize();available={t for dim,t in tags if dim==3};g=geo['groups'];vols={};cache={t:(occ.getMass(3,t),occ.getBoundingBox(3,t)) for t in available}
        for i,q in enumerate(g):
            hit=[t for t in available if abs(cache[t][0]*1e-9/q['volume_m3']-1)<1e-7 and max(abs(a-b) for a,b in zip(cache[t][1],q['bbox_mm']))<.00021]
            # Native loose BRep boxes are stable undersamekernel roundtrip.
            if len(hit)!=1:raise ValueError('Fixture identity '+q['name']+' '+str(hit))
            vols[hit[0]]=i;available.remove(hit[0])
        registry=[]
        for _,f in gmsh.model.getEntities(2):
            up,_=gmsh.model.getAdjacencies(2,f);own=sorted(vols[int(t)] for t in up if int(t) in vols)
            if not own:continue
            bb=occ.getBoundingBox(2,f);area=occ.getMass(2,f)*1e-6
            hit=[q for q in geo['faces'] if q['owners']==own and abs(area/q['area_m2']-1)<1e-7 and max(abs(a-b) for a,b in zip(bb,q['bbox_mm']))<.00021]
            if len(hit)!=1:raise ValueError('Face reimportidentity')
            registry.append(dict(hit[0],tag=f))
        qualify_faces(g,registry)
        gmsh.option.setNumber('Mesh.MeshSizeMin',.001);gmsh.option.setNumber('Mesh.MeshSizeMax',h);gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',64 if h>.03 else 80);gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0);gmsh.option.setNumber('Mesh.Algorithm3D',1);gmsh.option.setNumber('Mesh.MinimumCirclePoints',128 if h>.03 else 160);gmsh.option.setNumber('Mesh.ElementOrder',1)
        gmsh.model.mesh.generate(3)
        nt,coords,_=gmsh.model.mesh.getNodes();nt=np.asarray(nt,dtype=np.int64);points=np.asarray(coords).reshape(-1,3)*.001;mapper=np.full(int(nt.max())+1,-1,np.int64);mapper[nt]=np.arange(len(nt));cells=[];regions=[]
        for tag,i in vols.items():
            kinds,_,arrays=gmsh.model.mesh.getElements(3,tag)
            if list(kinds)!=[4]:raise ValueError('NonP1tets')
            tet=mapper[np.asarray(arrays[0],dtype=np.int64).reshape(-1,4)];cells.append(tet);regions.extend([i]*len(tet))
        cells=np.concatenate(cells);regions=np.asarray(regions)
        if len(cells)>250000:raise ValueError('250ktethardcap;no solve; actual='+str(len(cells)))
        used=np.unique(cells);re=np.full(len(points),-1,np.int64);re[used]=np.arange(len(used));points=points[used];cells=re[cells]
        det=np.linalg.det(points[cells[:,1:]]-points[cells[:,:1]]);neg=det<0;cells[neg,1],cells[neg,2]=cells[neg,2].copy(),cells[neg,1].copy();det=abs(det)
        if np.any(det<=1e-30):raise ValueError('Nonpositive/degenerate tets')
        tris=[];faceids=[]
        for q in registry:
            kinds,_,arrays=gmsh.model.mesh.getElements(2,q['tag'])
            if list(kinds)!=[2]:raise ValueError('Unsupported boundary faces')
            tr=re[mapper[np.asarray(arrays[0],dtype=np.int64).reshape(-1,3)]];tris.append(tr);faceids.extend([q['tag']]*len(tr))
        tris=np.concatenate(tris);faceids=np.asarray(faceids)
        gmsh.write(str(out/'coupon.msh'));np.savez_compressed(out/'mesh.npz',points=points,cells=cells,regions=regions,triangles=tris,faceids=faceids)
        write(out/'registry.json',dict(groups=g,faces=registry,ports=PORTS));write(out/'mesh_audit.json',dict(status='PASS positiveP1mesh;fieldgatespending',nodes=len(points),tets=len(cells),h_mm=h,minimum_volume_m3=float(det.min()/6),CAD_volume_m3=sum(q['volume_m3'] for q in g),mesh_volume_m3=float(det.sum()/6),seconds=time.monotonic()-start,mesh_sha256=sha(out/'mesh.npz')))
        print('LOCALMESH',len(points),len(cells))
    except Exception as e:write(out/'failure.json',dict(error=repr(e),seconds=time.monotonic()-start));raise
    finally:gmsh.finalize()
