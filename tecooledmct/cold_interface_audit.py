"""Independent raw tetrahedron-face Fourier fluxes, geometry and corner partitions."""
import argparse,json,gzip,shutil,tempfile
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import ROOT,sha,write
from .fem_g2a import mesh_adjacency
from .corrected_thermal import material


def affine(p,c,t):
    A=p[c[:,1:]]-p[c[:,:1]]
    return abs(np.linalg.det(A))/6,np.linalg.solve(A,(t[c[:,1:]]-t[c[:,:1]])[...,None])[...,0]


def face_flux(p,c,b,faces,t,k_nodes,quality=None):
    """Independent difference-based gradient; kface is mean of actual face nodes.

    k_nodes is per-cell four nodal coefficients. No FE reaction is an input.
    Selected interfaces must have two real tetrahedron owners, different bodies.
    """
    vol,grad=affine(p,c,t);adj=mesh_adjacency(c);xyz=p[faces];center=xyz.mean(1)
    av=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2;area=np.linalg.norm(av,axis=1)
    owners=np.array([adj[tuple(sorted(face))] for face in faces])
    if owners.shape!=(len(faces),2):raise ValueError('Not a two-sided actual interface')
    pairs=np.sort(b[owners],axis=1)
    if len(np.unique(pairs,axis=0))!=1:raise ValueError('Mixed material-pair selection')
    owners=np.array([row[np.argsort(b[row])] for row in owners]);powers=[];heights=[];edges=[];aspect=[];sicn=[]
    for side in range(2):
        ids=owners[:,side];normal=av.copy();normal[np.einsum('ij,ij->i',normal,center-p[c[ids]].mean(1))<0]*=-1
        # Exactly the three real face nodes; no absolute-coordinate barycentric inverse.
        mask=np.any(c[ids,:,None]==faces[:,None,:],axis=2)
        if not np.all(mask.sum(1)==3):raise ValueError('Face does not belong to owner')
        kface=(k_nodes[ids]*mask).sum(1)/3;q=-kface[:,None]*grad[ids];powers.append(np.einsum('ij,ij->i',q,normal))
        height=3*vol[ids]/area;edge=np.max(np.linalg.norm(p[c[ids]][:,:,None]-p[c[ids]][:,None,:],axis=3),axis=(1,2))
        heights.append(height);edges.append(edge);aspect.append(edge/height)
        sicn.append(quality[ids] if quality is not None else np.full(len(ids),np.nan))
    power=np.array(powers).T;totals=power.sum(0);jump=power.sum(1);halfwidth=.0005
    corner=np.array([[x,y] for x in (-halfwidth,halfwidth) for y in (-halfwidth,halfwidth)])
    distance=np.linalg.norm(center[:,None,:2]-corner[None,:,:],axis=2).min(1)
    edge_distance=halfwidth-np.abs(center[:,:2]).max(1);groups=[]
    for name,lo,hi in [('corner_0_100um',0,.0001),('corner_100_250um',.0001,.00025),('beyond_250um',.00025,np.inf)]:
        sel=(distance>=lo)&(distance<hi);groups.append({'group':name,'triangles':int(sel.sum()),'area_m2':float(area[sel].sum()),
               'side_powers_w':power[sel].sum(0).tolist(),'sum_outward_w':float(jump[sel].sum()),'absolute_jump_w':float(abs(jump[sel]).sum())})
    mismatch=float(totals.sum()/max(abs(totals).mean(),1e-4))
    unweighted=(power/area[:,None]).mean(0)*area.sum()
    summary={'bodies':pairs[0].tolist(),'triangles':len(faces),'area_m2':float(area.sum()),'raw_outward_w':totals.tolist(),
       'mismatch':mismatch,'five_percent_passed':bool(abs(mismatch)<.05),'corner_partitions':groups,
       'arithmetic_mean_density_times_area_w':unweighted.tolist(),'area_weighting_scope':'actual integral is area weighted; arithmetic density average is a diagnostic only',
       'owner_height_um_quantiles':[np.quantile(h*1e6,[0,.25,.5,.75,1]).tolist() for h in heights],
       'owner_edge_um_quantiles':[np.quantile(h*1e6,[0,.5,1]).tolist() for h in edges],
       'owner_edge_over_height_quantiles':[np.quantile(h,[0,.5,1]).tolist() for h in aspect],
       'owner_SICN_quantiles':[np.quantile(q,[0,.5,1]).tolist() if np.isfinite(q).all() else None for q in sicn]}
    arrays={'faces':faces,'centroids_m':center,'areas_m2':area,'owners':owners,'power_outward_w':power,
            'jump_density_W_m2':jump/area,'corner_distance_m':distance,'edge_distance_m':edge_distance,
            'owner_height_m':np.array(heights).T,'owner_edge_m':np.array(edges).T,'owner_SICN':np.array(sicn).T}
    return summary,arrays


def device(mesh,case,out):
    import meshio
    if out.exists():raise ValueError('Choose new diagnostic label')
    out.mkdir(parents=True);m=json.loads((mesh/'manifest.json').read_text());meta=json.loads((case/'case.json').read_text())
    execution=json.loads((case/'execution.json').read_text());source=case/execution['field_source']
    if sha(source)!=execution['vtu_sha256']:raise ValueError('Changed actual solved field')
    d=np.load(mesh/'mesh.npz');p,c,b,f,tags=(d[k] for k in ('points','cells','bodies','faces','boundaries'));field=meshio.read(source)
    dist,ix=cKDTree(field.points).query(p)
    if dist.max()>1e-12 or len(np.unique(ix))!=len(p):raise ValueError('Field mapping differs')
    t=field.point_data['temperature'].ravel()[ix];k=np.empty((len(c),4));rows=[]
    for body in m['bodies']:
        sel=b==body['id'];k[sel]=material(body['material'],t[c[sel]],meta['package_sigma_s_m'])[0]
    for pair in ((4,302),(302,303)):
        tag=next(row['boundary_id'] for row in m['contacts'] if row['bodies']==list(pair));faces=f[tags==tag]
        result,arrays=face_flux(p,c,b,faces,t,k,d['quality']);rows.append(result);np.savez_compressed(out/f'face_{pair[0]}_{pair[1]}.npz',**arrays)
    # All raw outer-body flux, separated into bottom, top and lateral surfaces.
    vol,grad=affine(p,c,t);adj=mesh_adjacency(c);whole=[]
    for bid in (302,303):
        sums={'bottom':0.,'top':0.,'sides':0.};body=next(row for row in m['bodies'] if row['id']==bid);box=body['boxes_m'][0]
        for face,owners in adj.items():
            own=[i for i in owners if b[i]==bid]
            if len(own)!=1 or len(owners)==2 and all(b[i]==bid for i in owners):continue
            ci=own[0];xyz=p[list(face)];normal=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])/2
            if np.dot(normal,xyz.mean(0)-p[c[ci]].mean(0))<0:normal*=-1
            mask=np.isin(c[ci],face);q=-k[ci,mask].mean()*grad[ci];power=float(q@normal)
            label='bottom' if np.all(abs(xyz[:,2]-box[2])<1e-11) else 'top' if np.all(abs(xyz[:,2]-box[2]-box[5])<1e-11) else 'sides'
            sums[label]+=power
        whole.append({'body':bid,'raw_outward_w':sums,'raw_total_outward_w':sum(sums.values()),
            'known_volume_source_w':meta['deposited_power_w'] if bid==303 else 0.,
            'physical_exterior_BC':'adiabatic; Au hybrid OFF in these comparisons. Raw nonzero exterior estimates are discretization defects, not prescribed losses'})
    old=case/'raw_interface_audit.json'
    if old.exists():
        previous=json.loads(old.read_text())['interfaces'][2:]
        for result,reference in zip(rows,previous):
            if abs(result['mismatch']-reference['raw_interface_relative_mismatch'])>1e-6:raise ValueError('Independent extraction does not reproduce archived failure')
    result={'interfaces':rows,'whole_body_raw_balance':whole,'source_sha256':sha(Path(__file__)),'mesh_sha256':sha(mesh/'mesh.npz'),
            'field_sha256':execution['vtu_sha256'],'actual_die_thickness_m':next(v for v in m['bodies'] if v['id']==303)['boxes_m'][0][5],
            'method':'true face normals and owner IDs; difference-based3x3 gradient; exact face nodal k average; NO weak reactions or recovery',
            'all_local_gates_passed':all(v['five_percent_passed'] for v in rows)}
    write(out/'diagnosis.json',result);print('Independent interface audit',case.name,[v['mismatch'] for v in rows],flush=True);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mesh',type=Path,required=True);parser.add_argument('--case',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();device(a.mesh.resolve(),a.case.resolve(),a.out.resolve())
