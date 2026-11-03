"""Fresh-process native-MSH geometry/topology audit. No PDE or fitted measures."""
from pathlib import Path
import argparse,time,resource
import numpy as np
import gmsh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scripts.v3_analysis_r3_geometry import read,save,sha

def mesh_tables(reg):
    tags,coords,_=gmsh.model.mesh.getNodes();coords=np.asarray(coords).reshape(-1,3)
    tags=np.asarray(tags,dtype=np.int64);lookup=np.full(int(tags.max())+1,-1,np.int64);lookup[tags]=np.arange(len(tags))
    faces={};areas={};expected=[];owner=[]
    for key,q in reg['face_registry'].items():
        f=int(key);types,_,arrays=gmsh.model.mesh.getElements(2,f)
        if list(types)!=[2]:raise ValueError('Missing/nontriangular physical face '+key)
        tri=lookup[np.asarray(arrays[0],np.int64).reshape(-1,3)];v=coords[tri];u=v[:,1]-v[:,0];w=v[:,2]-v[:,0]
        # Gram determinant independent of the producer's vector-cross areas.
        area=.5*np.sqrt(np.maximum(0.,np.einsum('ij,ij->i',u,u)*np.einsum('ij,ij->i',w,w)-np.einsum('ij,ij->i',u,w)**2))
        if np.any(area<=0):raise ValueError('Degenerate mesh triangle')
        error=float(area.sum()/q['face_area_mm2']-1)
        areas[key]=dict(relative_error=error,triangles=len(tri),mesh_area_mm2=float(area.sum()))
        if abs(error)>=.01:raise ValueError('Per-face1% fidelity failure '+key+' '+str(error))
        faces[f]=tri;expected.append(np.sort(tri,axis=1))
        ids=sorted(q['owner_volume_ids']);ids=ids+[-1] if len(ids)==1 else ids
        owner.extend([ids]*len(tri))
        if f not in gmsh.model.getPhysicalGroupsForEntity(2,f):raise ValueError('Missing physical face group')
    for p,children in reg['R2_face_descendants'].items():
        total=sum(areas[str(f)]['mesh_area_mm2'] for f in children)
        exact=sum(reg['face_registry'][str(f)]['face_area_mm2'] for f in children)
        if abs(total/exact-1)>=.01:raise ValueError('Original R2 parent face area gate '+p)
    for name,tag in reg['domain_id_map'].items():
        if tag not in gmsh.model.getPhysicalGroupsForEntity(3,tag):raise ValueError('Missing physical domain group')
    return coords,lookup,faces,areas,np.concatenate(expected),np.asarray(owner,np.int64)

def skin_check(reg,faces):
    counts={}
    for name,tag in reg['domain_id_map'].items():
        tri=np.concatenate([faces[int(f)] for f,q in reg['face_registry'].items() if tag in q['owner_volume_ids']])
        edges=np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1)
        unique,n=np.unique(edges,axis=0,return_counts=True)
        if np.any(n!=2):raise ValueError('Open/nonmanifold volume skin '+name+' edges='+str(int(np.count_nonzero(n!=2))))
        counts[name]=dict(surface_triangles=len(tri),unique_edges=len(unique),open_edges=0)
    return counts

def audit(mesh,registry,geometry,out,volume=False):
    if out.exists():raise ValueError('Preserve independent mesh audit')
    out.mkdir(parents=True);then=time.monotonic();reg=read(registry);geo=read(geometry)
    result=dict(status='PENDING',mesh_sha256=sha(mesh),no_PDE=True,solver_ready=False)
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
    try:
        gmsh.open(str(mesh));p,lookup,faces,area,expected,owner=mesh_tables(reg)
        result.update(surface_faces=len(faces),surface_triangles=sum(v['triangles'] for v in area.values()),
            mesh_nodes=len(p),max_face_area_error=max(abs(v['relative_error']) for v in area.values()),face_areas=area,
            closed_skins=skin_check(reg,faces),bbox_m=[*(p.min(axis=0)*.001),*(p.max(axis=0)*.001)])
        if volume:
            blocks=[];regions=[];volumes={};qualities=[];alltetids=[]
            for name,tag in reg['domain_id_map'].items():
                types,ids,arrays=gmsh.model.mesh.getElements(3,tag)
                if list(types)!=[4]:raise ValueError('Missing/nonlinear tetrahedral domain '+name)
                t=lookup[np.asarray(arrays[0],np.int64).reshape(-1,4)];blocks.append(t);regions.extend([tag]*len(t));alltetids.extend(ids[0])
                edge=p[t[:,1:]]-p[t[:,:1]];det=np.einsum('ei,ei->e',edge[:,0],np.cross(edge[:,1],edge[:,2]))
                if np.any(det<=0):raise ValueError('Nonpositive raw tetrahedron Jacobian '+name)
                v=float(det.sum()/6);target=geo['domains'][name]['area_or_volume'];err=v/target-1
                volumes[name]=dict(tets=len(t),CAD_mm3=target,mesh_mm3=v,relative_error=err,min_jacobian_m3=float(det.min()*1e-9))
                if abs(err)>=.01:raise ValueError('Per-domain volume1% failure '+name+' '+str(err))
            t=np.concatenate(blocks);r=np.asarray(regions,np.int64)
            if len(t)>3000000:raise ValueError('3million-tet cap')
            q=np.asarray(gmsh.model.mesh.getElementQualities(alltetids,'minSICN'))
            if not np.isfinite(q).all() or q.min()<=1e-9:raise ValueError('Positive shape-quality gate')
            face=t[:,[[1,2,3],[0,2,3],[0,1,3],[0,1,2]]].reshape(-1,3);face.sort(axis=1)
            order=np.lexsort((face[:,2],face[:,1],face[:,0]));face=face[order]
            diff=np.r_[True,np.any(face[1:]!=face[:-1],axis=1)];starts=np.flatnonzero(diff);counts=np.diff(np.r_[starts,len(face)])
            if counts.max()>2:raise ValueError('Nonmanifold tetrahedral face incidence')
            rr=np.repeat(r,4)[order];a=rr[starts];b=rr[starts+counts-1]
            physical=(counts==1)|(a!=b);actual=face[starts[physical]];ab=np.sort(np.stack([a[physical],b[physical]],axis=1),axis=1)
            ab[counts[physical]==1,1]=-1
            es=np.lexsort((expected[:,2],expected[:,1],expected[:,0]));expected=expected[es];owner=owner[es]
            if not np.array_equal(actual,expected) or not np.array_equal(ab,owner):raise ValueError('Actual tetra-to-physical-face ownership mismatch')
            element=np.repeat(np.arange(len(t)),4)[order];g=reg['domain_id_map']['CAVITY_GAS']
            used=(counts==2)&(a==g)&(b==g);left=element[starts[used]];right=element[starts[used]+1]
            local=np.full(len(t),-1,np.int64);local[r==g]=np.arange(np.count_nonzero(r==g))
            graph=coo_matrix((np.ones(len(left)),(local[left],local[right])),shape=(np.count_nonzero(r==g),)*2).tocsr()
            components=connected_components(graph,directed=False,return_labels=False)
            if components!=1:raise ValueError('Disconnected actual gas mesh')
            result.update(tetrahedra=len(t),volumes=volumes,min_jacobian_m3=min(v['min_jacobian_m3'] for v in volumes.values()),
              quality=dict(zip(['min','p01','p05','median','p95','max'],map(float,np.quantile(q,[0,.01,.05,.5,.95,1])))),
              conformal_physical_facets=len(actual),gas_components=int(components),max_domain_volume_error=max(abs(v['relative_error']) for v in volumes.values()))
        result['status']='PASS INDEPENDENT VOLUME MESH GATES; NO PDE' if volume else 'PASS INDEPENDENT SURFACE/SKIN GATES; 3D NOT RUN'
        print(result['status'],result.get('tetrahedra'),result['surface_triangles'],flush=True)
    except Exception as ex:result.update(status='STOP INDEPENDENT MESH AUDIT',error=repr(ex));raise
    finally:
        result.update(seconds=time.monotonic()-then,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        save(out/'audit.json',result);gmsh.finalize()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,required=True);p.add_argument('--registry',type=Path,required=True)
    p.add_argument('--geometry',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--volume',action='store_true')
    a=p.parse_args();audit(a.mesh,a.registry,a.geometry,a.out,a.volume)
