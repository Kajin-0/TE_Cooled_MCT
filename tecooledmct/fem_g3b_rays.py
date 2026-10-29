"""Deterministic cosine first-hit rays on audited CSG; closed reciprocal surface operator."""
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix,save_npz
from scipy.spatial import cKDTree
from scipy.stats import qmc
from .g2d_data import ROOT,sha,dump
from .fem_g3b_data import preserve
from .fem_g3b_exchange import balanced_view_factors
from .fem_g2a import mesh_adjacency
from .fem_g1_run import execute
from .fem_g2c_mesh import verify_elmer_tetra_mapping


def first_hits(origin,direction,m,source_owner):
    """Analytic first opaque CSG hit. Cap/floor close every ray; no escape filler."""
    n=len(origin);best=np.full(n,np.inf);owner=np.full(n,-1);normal=np.zeros((n,3));eps=1e-9;cav=m['cavity'];xy=m['package_registry']['feedthroughs']['centers_xy_m'];ri=m['package_registry']['feedthroughs']['pin_radius_m']
    def update(t,bid,nn,valid=None):
        use=(t>eps)&(t<best)
        if valid is not None:use &=valid
        best[use]=t[use];owner[use]=bid if np.isscalar(bid) else bid[use];normal[use]=nn if np.shape(nn)==(3,) else nn[use]
    dz=direction[:,2];safe=np.where(abs(dz)>1e-20,dz,1.)
    t=(cav['ceiling_z_m']-origin[:,2])/safe;hit=origin+direction*t[:,None];bid=np.where(np.linalg.norm(hit[:,:2],axis=1)<m['package_registry']['cap']['window_radius_m'],cav['window_body'],cav['cap_body']);update(t,bid,[0,0,-1],dz>1e-20)
    t=(cav['floor_z_m']-origin[:,2])/safe;hit=origin+direction*t[:,None];bid=np.full(n,cav['header_body'])
    for x in m['pin_tops']:
        glass=next(b['id'] for b in m['bodies'] if b['name']=='glass_'+str(m['pin_tops'].index(x)))
        dist=np.linalg.norm(hit[:,:2]-x['center_xy_m'],axis=1);bid[dist<m['package_registry']['feedthroughs']['glass_radius_m']]=glass
    update(t,bid,[0,0,1],dz< -1e-20)
    aa=np.sum(direction[:,:2]**2,axis=1);bb=2*np.sum(origin[:,:2]*direction[:,:2],axis=1);cc=np.sum(origin[:,:2]**2,axis=1)-cav['radius_m']**2;disc=np.maximum(bb*bb-4*aa*cc,0);t=(-bb+np.sqrt(disc))/(2*np.maximum(aa,1e-30));hit=origin+direction*t[:,None];nn=np.column_stack([-hit[:,:2]/cav['radius_m'],np.zeros(n)]);update(t,cav['cap_body'],nn,aa>1e-24)
    for body in m['bodies']:
        for box in body.get('boxes_m',[body['box_m']] if 'box_m' in body else []):
            lo=np.array(box[:3]);hi=lo+box[3:];parallel=abs(direction)<1e-20;safe=np.where(parallel,1.,direction);a=(lo-origin)/safe;b=(hi-origin)/safe;entry=np.where(parallel,-np.inf,np.minimum(a,b));leave=np.where(parallel,np.inf,np.maximum(a,b));t=entry.max(axis=1);valid=(leave.min(axis=1)>np.maximum(t,eps))&(~np.any(parallel&((origin<lo-1e-12)|(origin>hi+1e-12)),axis=1));axis=entry.argmax(axis=1);nn=np.zeros((n,3));nn[np.arange(n),axis]=-np.sign(direction[np.arange(n),axis]);update(t,body['id'],nn,valid)
    for pin in m['pin_tops']:
        v=origin[:,:2]-pin['center_xy_m'];aa=np.sum(direction[:,:2]**2,axis=1);bb=2*np.sum(v*direction[:,:2],axis=1);cc=np.sum(v*v,axis=1)-ri*ri;disc=bb*bb-4*aa*cc;t=(-bb-np.sqrt(np.maximum(disc,0)))/(2*np.maximum(aa,1e-30));hit=origin+direction*t[:,None];nn=np.column_stack([(hit[:,:2]-pin['center_xy_m'])/ri,np.zeros(n)]);valid=(disc>=0)&(aa>1e-24)&(hit[:,2]>=cav['floor_z_m'])&(hit[:,2]<=pin['z_m'])&(source_owner!=pin['body']);update(t,pin['body'],nn,valid)
        t=(pin['z_m']-origin[:,2])/np.where(abs(dz)>1e-20,dz,1.);hit=origin+direction*t[:,None];valid=(dz< -1e-20)&(np.linalg.norm(hit[:,:2]-pin['center_xy_m'],axis=1)<ri)&(source_owner!=pin['body']);update(t,pin['body'],[0,0,1],valid)
    if np.any(owner<0) or np.any(~np.isfinite(best)):raise ValueError('A ray escaped the declared closed cavity')
    return origin+best[:,None]*direction,owner,normal


def build(mesh,out,level=0):
    import meshio
    preserve();out.mkdir(parents=True,exist_ok=True);m=json.loads((mesh/'manifest.json').read_text());d=np.load(mesh/'mesh.npz');p,c,b,f,bt=(d[k] for k in ('points','cells','bodies','faces','boundaries'));adj=mesh_adjacency(c);ex=np.flatnonzero(bt<1000);ff=f[ex];fc=np.array([adj[tuple(sorted(t))][0] for t in ff]);owner=b[fc];xyz=p[ff];av=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2;area=np.linalg.norm(av,axis=1);norm=av/area[:,None];center=xyz.mean(axis=1);norm[np.einsum('ij,ij->i',norm,center-p[c[fc]].mean(axis=1))<0]*=-1;cav=m['cavity'];mask=(center[:,2]>=cav['floor_z_m']-1e-10)&(center[:,2]<=cav['ceiling_z_m']+1e-10)&(np.linalg.norm(center[:,:2],axis=1)<=cav['radius_m']+1e-10)
    ex,ff,owner,xyz,area,norm,center=(v[mask] for v in (ex,ff,owner,xyz,area,norm,center));aliases=bt[ex];edges={}
    for tri in ff:
        for i,j in ((0,1),(1,2),(2,0)):
            e=tuple(sorted((int(tri[i]),int(tri[j]))));edges[e]=edges.get(e,0)+1
    if any(v!=2 for v in edges.values()):raise ValueError('Open cavity skin')
    volume=-float(np.sum(area*np.einsum('ij,ij->i',norm,center))/3);expected=math.pi*cav['radius_m']**2*(cav['ceiling_z_m']-cav['floor_z_m'])
    for body in m['bodies']:
        if body['id']<=m['original_TEC_domains'] or body['kind'] in ('hot_mount','die_attach','die','bond_pad'):expected-=body['expected_volume_m3']
        if body['kind']=='pin':expected-=math.pi*m['package_registry']['feedthroughs']['pin_radius_m']**2*m['package_registry']['feedthroughs']['pin_above_header_m']
    if abs(volume/expected-1)>.01:raise ValueError('Closed skin volume mismatch')
    by={x['id']:x for x in m['bodies']};groups={};origins={int(i):center[owner==i].min(axis=0)-1e-12 for i in np.unique(owner)}
    for k,(bid,tag,point,nn) in enumerate(zip(owner,aliases,center,norm)):
        body=by[int(bid)];kind=body['kind'];local=point-origins[int(bid)]
        if kind in ('leg','bridge','terminal','routing_insulator','interstage_link','pin'):spatial=(int(local[2]/(.001 if level==0 else .0005)),)
        elif kind=='cap':spatial=(int((math.atan2(point[1],point[0])+math.pi)/(2*math.pi)*(4 if level==0 else 8)),int(local[2]/(.004 if level==0 else .002)),int(abs(nn[2])>.7))
        else:
            size=(.003 if level==0 else .0015) if kind in ('header','window','glass') else (.001 if level==0 else .0005);spatial=tuple(np.floor(local/size).astype(int))
        key=(int(bid),int(tag),*spatial);groups.setdefault(key,[]).append(k)
    patches=[];pi=np.full(len(f),-1,dtype=int);rows=[];cols=[];data=[];patch_ids=[]
    for index,(key,ids) in enumerate(groups.items()):
        ids=np.array(ids);A=float(area[ids].sum());weighted=area[ids]/A;cent=weighted@center[ids];normal=weighted@norm[ids];normal/=max(np.linalg.norm(normal),1e-30);nw=np.zeros(len(p));np.add.at(nw,ff[ids].ravel(),np.repeat(area[ids]/3,3));nodes=np.flatnonzero(nw);rows.extend([index]*len(nodes));cols.extend(nodes.tolist());data.extend((nw[nodes]/A).tolist());pi[ex[ids]]=index;patch_ids.append(ids)
        patches.append({'index':index,'solver_boundary':20000+index,'owner':key[0],'owner_name':by[key[0]]['name'],'kind':by[key[0]]['kind'],'material':by[key[0]]['material'],'original_boundary':key[1],'area_m2':A,'center_m':cent.tolist(),'normal_into_gas':normal.tolist(),'triangle_indices':ex[ids].tolist()})
    N=len(patches);a=np.array([x['area_m2'] for x in patches]);cent=np.array([x['center_m'] for x in patches]);weights=coo_matrix((data,(rows,cols)),shape=(N,len(p))).tocsr();save_npz(out/'weights.npz',weights);rayf=np.zeros((N,N));inverse_gap=np.zeros((N,N));ray_counts=[];mapping_errors=[];trees={};major=np.argmax(abs(norm),axis=1);direction_sign=np.sign(norm[np.arange(len(norm)),major]).astype(int)
    for bid in np.unique(owner):
        for axis in (0,1,2):
            for sign in (-1,1):
                ids=np.flatnonzero((owner==bid)&(major==axis)&(direction_sign==sign))
                if len(ids):trees[(int(bid),axis,sign)]=(cKDTree(center[ids]),ids)
    for i,ids in enumerate(patch_ids):
        count=2**int(np.ceil(np.log2(max(256 if level==0 else 512,a[i]/2e-8*8))));ray_counts.append(count);u=qmc.Sobol(5,scramble=False).random_base2(int(math.log2(count)));u=(u+.5/count)%1;choice=ids[np.minimum(np.searchsorted(np.cumsum(area[ids]/a[i]),u[:,0]),len(ids)-1)];r=np.sqrt(u[:,1]);triweight=np.column_stack([1-r,r*(1-u[:,2]),r*u[:,2]]);origin=np.einsum('ij,ijk->ik',triweight,xyz[choice]);nn=norm[choice];basis=np.cross(nn,np.where((abs(nn[:,2])<.9)[:,None],[0.,0.,1.],[1.,0.,0.]));basis/=np.linalg.norm(basis,axis=1)[:,None];other=np.cross(nn,basis);rr=np.sqrt(u[:,3]);theta=2*np.pi*u[:,4];direction=rr[:,None]*(np.cos(theta)[:,None]*basis+np.sin(theta)[:,None]*other)+np.sqrt(1-u[:,3])[:,None]*nn;origin+=nn*1e-10
        hit,bid,hn=first_hits(origin,direction,m,np.full(count,patches[i]['owner']));dest=np.full(count,-1,dtype=int);axis=np.argmax(abs(hn),axis=1);sign=np.sign(hn[np.arange(count),axis]).astype(int)
        for key in set(zip(bid.tolist(),axis.tolist(),sign.tolist())):
            sel=np.flatnonzero((bid==key[0])&(axis==key[1])&(sign==key[2]));entry=trees.get(key)
            if entry is None:
                available=np.flatnonzero(owner==key[0])
                if not len(available):raise ValueError('Ray hit has no audited cavity facets')
                entry=(cKDTree(center[available]),available)
            tree,ids2=entry;dist,ix=tree.query(hit[sel]);dest[sel]=pi[ex[ids2[ix]]];mapping_errors.extend(dist.tolist())
        if np.any(dest<0):raise ValueError('Unmapped first ray hit')
        rayf[i]=np.bincount(dest,minlength=N)/count
        flight=np.linalg.norm(hit-origin,axis=1);projected=flight*.5*(np.maximum(0,np.einsum('ij,ij->i',direction,nn))+np.maximum(0,-np.einsum('ij,ij->i',direction,hn)))
        inverse_gap[i]=np.bincount(dest,weights=1/np.maximum(projected,1e-10),minlength=N)/count
        if i%100==0:print('Cosine first-hit cavity patches',i,'/',N,flush=True)
    raw=.5*(a[:,None]*rayf+(a[:,None]*rayf).T);fview,closure=balanced_view_factors(raw,a);exchange=a[:,None]*fview;moment=.5*(a[:,None]*inverse_gap+(a[:,None]*inverse_gap).T);dist=np.divide(raw,moment,out=np.ones_like(raw),where=moment>0);np.fill_diagonal(dist,1.)
    solverbt=bt.copy();solverbt[pi>=0]=20000+pi[pi>=0];np.savez_compressed(out/'mesh.npz',points=p,cells=c,bodies=b,faces=f,boundaries=bt,solver_boundaries=solverbt,patch_index=pi);dump(out/'manifest.json',m);dump(out/'patches.json',patches);np.savez_compressed(out/'operators.npz',areas=a,centers=cent,raw_ray_view_factors=rayf,view_factors=fview,exchange_m2=exchange,distance_m=dist)
    meshio.write(out/'connected.msh',meshio.Mesh(p,[('triangle',f),('tetra',c)],cell_data={'gmsh:physical':[solverbt,b],'gmsh:geometrical':[solverbt,b]}),file_format='gmsh22',binary=False);execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],out,'grid');mapping=verify_elmer_tetra_mapping(out);er=np.loadtxt(out/'elmer/mesh.nodes');dd,ix=cKDTree(er[:,2:5]).query(p);nodeids=er[ix,0].astype(int);expected_faces={tuple(sorted(nodeids[tri])):int(tag) for tri,tag in zip(f,solverbt)};actual={}
    for line in (out/'elmer/mesh.boundary').read_text().splitlines():
        v=list(map(int,line.split()));actual[tuple(sorted(v[5:]))]=v[1]
    if actual!=expected_faces:raise ValueError('Actual boundary patch mapping failed')
    audit={'passed':True,'patches':N,'rays':sum(ray_counts),'ray_count_per_patch':ray_counts,'raw_ray_row_max_error':float(abs(rayf.sum(axis=1)-1).max()),'raw_ray_area_reciprocity_l1':float(np.abs(a[:,None]*rayf-(a[:,None]*rayf).T).sum()/a.sum()),'closure':closure,'closed_skin_all_edge_incidence_two':True,'cavity_volume_skin_m3':volume,'cavity_volume_analytical_m3':expected,'skin_triangles':len(ff),'hit_to_actual_face_center_p95_m':float(np.quantile(mapping_errors,.95)),'hit_to_actual_face_center_max_m':float(max(mapping_errors)),'gas_gap_method':'harmonic normal-projected first-hit flight gap; exact parallel-plane spacing, reduced arbitrary-cavity gas-film approximation', 'method':'deterministic cosine area rays, first hit in exact orthogonal opaque union/cylinder enclosure; hit assigned to audited same-owner/orientation cavity facets; symmetric area balancing; self-view only from actual returned rays','elmer_mapping':mapping,'actual_boundary_mapping_verified':True,'level':level,'source_mesh_sha256':sha(mesh/'mesh.npz'),'mesh_sha256':sha(out/'mesh.npz'),'source_sha256':{str(x.relative_to(ROOT)):sha(x) for x in (Path(__file__),ROOT/'tecooledmct/fem_g3b_exchange.py')}};dump(out/'audit.json',audit);print(json.dumps({k:v for k,v in audit.items() if k!='ray_count_per_patch'},indent=2),flush=True);return audit

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,default=Path('outputs/fem-g3b/mesh_0'));p.add_argument('--out',type=Path,default=Path('outputs/fem-g3b/operator_0'));p.add_argument('--level',type=int,default=0);a=p.parse_args();build(a.mesh.resolve(),a.out.resolve(),a.level)
