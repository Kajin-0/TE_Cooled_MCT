"""Body-respecting actual tetrahedral P1 starting states; never final FEM fields."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import ROOT,sha,write

BOUNDS=ROOT/'data/cold20/projection_bounds.json'


def transfer_nodes(p,c,b,target,tc,tb,priority=()):
    """Each target node uses a source body incident to that same target node.

    Tiny source/destination curved-skin differences may use a recorded convex
    projection into an actual SAME-body source tetrahedron. No cross-body nearest
    node or scattered triangulation is a fallback. All interpolation weights are
    nonnegative and sum to one, so temperature extrema are preserved.
    """
    N=len(target);sn=np.full((N,4),-1,int);weights=np.zeros((N,4));owner=np.full(N,-1,int);body=np.full(N,-1,int)
    exact=np.zeros(N,bool);displacement=np.zeros(N);bound=json.loads(BOUNDS.read_text());tol=bound['barycentric_tolerance']
    order=sorted(np.unique(tb),key=lambda x:(x not in priority,int(x)))
    def search(bid,ids,project=False):
        indices=np.flatnonzero(b==bid);cells=c[indices];xyz=p[cells];origin=xyz[:,0];inv=np.linalg.inv(xyz[:,1:]-xyz[:,:1]);tree=cKDTree(xyz.mean(1))
        todo=ids
        for k in (32,128,512):
            if not len(todo):break
            k=min(k,len(cells));pending=[]
            for chunk in np.array_split(todo,max(1,int(np.ceil(len(todo)/256)))):
                _,near=tree.query(target[chunk],k=k);near=np.asarray(near).reshape(len(chunk),k)
                alpha=np.einsum('nki,nkij->nkj',target[chunk,None,:]-origin[near],inv[near]);w=np.concatenate([1-alpha.sum(2,keepdims=True),alpha],axis=2)
                if project:
                    convex=np.maximum(w,0);convex/=convex.sum(2,keepdims=True)
                    point=np.einsum('nkj,nkji->nki',convex,xyz[near]);dist=np.linalg.norm(point-target[chunk,None,:],axis=2)
                    pick=dist.argmin(1);chosen=near[np.arange(len(chunk)),pick];ww=convex[np.arange(len(chunk)),pick];dd=dist[np.arange(len(chunk)),pick]
                    good=dd<=bound['maximum_same_body_boundary_projection_m']
                else:
                    score=w.min(2);pick=score.argmax(1);chosen=near[np.arange(len(chunk)),pick];ww=w[np.arange(len(chunk)),pick]
                    good=(ww.min(1)>=-tol)&(ww.max(1)<=1+tol)
                    ww=np.maximum(ww,0);ww/=ww.sum(1,keepdims=True)
                    dd=np.linalg.norm(np.einsum('nj,nji->ni',ww,xyz[chosen])-target[chunk],axis=1)
                done=chunk[good];source=chosen[good];sn[done]=cells[source];weights[done]=ww[good];owner[done]=indices[source];body[done]=bid;displacement[done]=dd[good]
                pending.extend(chunk[~good])
            todo=np.array(pending,int)
    for bid in order:
        ids=np.unique(tc[tb==bid]);ids=ids[body[ids]<0]
        if not len(ids):continue
        source_nodes=np.unique(c[b==bid]);distance,near=cKDTree(p[source_nodes]).query(target[ids]);hit=distance<=bound['exact_node_tolerance_m']
        done=ids[hit];original=source_nodes[near[hit]];sn[done]=original[:,None];weights[done,0]=1;body[done]=bid;exact[done]=True;displacement[done]=distance[hit]
        search(bid,ids[~hit])
    # Only unresolved target boundary nodes can reach this bounded fallback.
    for bid in order:
        ids=np.unique(tc[tb==bid]);ids=ids[body[ids]<0]
        if len(ids):search(bid,ids,project=True)
    if np.any(body<0):raise ValueError(f'{int((body<0).sum())} target nodes have no admissible same-body P1 transfer')
    if weights.min()<0 or abs(weights.sum(1)-1).max()>bound['weight_sum_tolerance']:raise ValueError('Invalid barycentric weights')
    return {'source_nodes':sn,'weights':weights,'source_cell':owner,'body':body,'exact_node':exact,'displacement_m':displacement}


def interpolate(mapping,values):return np.einsum('ni,nij->nj',mapping['weights'],np.asarray(values)[mapping['source_nodes']])


def ascii_guess(path,values):
    N=len(values)
    with path.open('w') as out:
        out.write(f' ASCII 3\n!Body-aware P1 INITIAL GUESS ONLY, not a solved field\n Degrees of freedom: \npot[temperature:1 potential:1] : {2*N} {N} 2 : thermoelectric\ntemperature : {N} {N} 1 : thermoelectric\npotential : {N} {N} 1 : thermoelectric\n Total DOFs: 2\n Number Of Nodes: {N}\nTime: 1 1 1.00000000E+000\ntemperature\nPerm: {N} {N}\n')
        for i in range(1,N+1):out.write(f'{i} {i}\n')
        np.savetxt(out,values[:,0],fmt='%.17e');out.write('potential\nPerm: use previous\n');np.savetxt(out,values[:,1],fmt='%.17e')


def build(source_mesh,source_case,target_mesh,out):
    import meshio
    if out.exists():raise ValueError('Choose a new transfer label')
    out.mkdir(parents=True);s=np.load(source_mesh/'mesh.npz');d=np.load(target_mesh/'mesh.npz');e=json.loads((source_case/'execution.json').read_text());fieldpath=source_case/e['field_source']
    if sha(fieldpath)!=e['vtu_sha256'] or sha(source_mesh/'mesh.npz')!=e['mesh_sha256']:raise ValueError('Changed genuine source field/mesh')
    if sha(source_mesh/'manifest.json')!=sha(target_mesh/'manifest.json'):raise ValueError('Physical registries differ')
    field=meshio.read(fieldpath);distance,ix=cKDTree(field.points).query(s['points'])
    if distance.max()>1e-12 or len(np.unique(ix))!=len(s['points']):raise ValueError('Source field map is not bijective')
    values=np.column_stack([field.point_data[k].ravel()[ix] for k in ('temperature','potential')]);m=json.loads((source_mesh/'manifest.json').read_text())
    mapping=transfer_nodes(s['points'],s['cells'],s['bodies'],d['points'],d['cells'],d['bodies'],m['conductor_path']);guess=interpolate(mapping,values)
    if not np.isfinite(guess).all() or guess[:,0].min()<90 or guess[:,0].max()>400:raise ValueError('Nonphysical/nonfinite starting temperature')
    nodes=np.loadtxt(target_mesh/'elmer/mesh.nodes');nodes=nodes[np.argsort(nodes[:,0])];distance,node_order=cKDTree(d['points']).query(nodes[:,2:5])
    if distance.max()>1e-12 or not np.array_equal(nodes[:,0],np.arange(1,len(nodes)+1)):raise ValueError('Target Elmer node mapping failed')
    face=d['faces'][d['boundaries']==104];gauge=float(abs(guess[np.unique(face),1]).max());bounds=json.loads(BOUNDS.read_text())
    if gauge>bounds['gauge_face104_tolerance_V']:raise ValueError('Inconsistent voltage gauge')
    constant=interpolate(mapping,np.tile([300.,0.],(len(s['points']),1)));zero_error=float(abs(constant[:,0]-300).max())
    if zero_error>1e-10 or abs(constant[:,1]).max()>1e-15:raise ValueError('Constant-field transfer sanity failed')
    affine=interpolate(mapping,s['points']);affine_error=float(np.linalg.norm(affine-d['points'],axis=1).max())
    np.savez_compressed(out/'map.npz',**mapping);np.savez_compressed(out/'initial_values.npz',target_points=d['points'],initial_temperature_K=guess[:,0],initial_potential_V=guess[:,1])
    ascii_guess(out/'initial_guess.result',guess[node_order]);meta=json.loads((source_case/'case.json').read_text());passive=meta['current_a']==0 and meta['deposited_power_w']==0
    if passive and (abs(guess[:,0]-300).max()>bounds['passive_300K_tolerance_K'] or abs(guess[:,1]).max()>bounds['passive_zero_potential_tolerance_V']):raise ValueError('Real passive transfer sanity failed')
    result={'passed':True,'source_mesh_sha256':sha(source_mesh/'mesh.npz'),'source_field_sha256':sha(fieldpath),'target_mesh_sha256':sha(target_mesh/'mesh.npz'),
        'source_case':str(source_case),'source_mesh':str(source_mesh),'target_mesh':str(target_mesh),'source_sha256':{str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(BOUNDS.relative_to(ROOT)):sha(BOUNDS)},
        'initial_guess_sha256':sha(out/'initial_guess.result'),'map_sha256':sha(out/'map.npz'),'initial_values_sha256':sha(out/'initial_values.npz'),
        'nodes':len(guess),'exact_nodes':int(mapping['exact_node'].sum()),'maximum_same_body_projection_displacement_m':float(mapping['displacement_m'].max()),
        'voltage_gauge_face104_maxabs_V':gauge,'constant300K_transfer_error_K':zero_error,'affine_coordinate_reproduction_error_m':affine_error,
        'real_zero_current_zero_load_transfer':passive,'real_passive_300K_error_K':float(abs(guess[:,0]-300).max()) if passive else None,
        'scope':'convex body-ID-aware tetrahedral P1 INITIAL GUESS ONLY; no final field or PDE solution claim'}
    write(out/'transfer.json',result);print('Body-aware P1 transfer PASS',result,flush=True);return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('source-mesh','source-case','target-mesh','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.source_mesh.resolve(),a.source_case.resolve(),a.target_mesh.resolve(),a.out.resolve())
