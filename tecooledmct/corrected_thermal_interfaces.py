"""One-sided raw P1 face fluxes and layer averages, never recovered bath flux."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import sha,write
from .fem_g1 import tetra_geometry
from .fem_g2a import mesh_adjacency
from .corrected_thermal import material


def audit(mesh,case):
    import meshio
    d=np.load(mesh/'mesh.npz');p,c,b,f,tags=(d[n] for n in ('points','cells','bodies','faces','boundaries'))
    m=json.loads((mesh/'manifest.json').read_text());meta=json.loads((case/'case.json').read_text());e=json.loads((case/'execution.json').read_text());source=case/e['field_source']
    if sha(source)!=e['vtu_sha256']:raise ValueError('Changed actual field')
    field=meshio.read(source);dist,ix=cKDTree(field.points).query(p)
    if dist.max()>1e-12:raise ValueError('Actual field/mesh mapping differs')
    t=field.point_data['temperature'].ravel()[ix];vol,g=tetra_geometry(p,c);gt=np.einsum('ei,eij->ej',t[c],g);adj=mesh_adjacency(c);by={r['id']:r for r in m['bodies']}
    rows=[];layer_ends={301:[],302:[]}
    for bodies in ((300,301),(1,301),(4,302),(302,303)):
        pair=sorted(bodies);tag=next(v['boundary_id'] for v in m['contacts'] if v['bodies']==pair);ff=f[tags==tag];xyz=p[ff];powers=[]
        a=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2;mean=float(a@t[ff].mean(1)/a.sum());z=float(a@xyz.mean(1)[:,2]/a.sum())
        for body in pair:
            owners=np.array([next(ci for ci in adj[tuple(sorted(face))] if b[ci]==body) for face in ff]);ks=material(by[body]['material'],t[c[owners]],meta['package_sigma_s_m'])[0]
            bary=np.array([np.r_[1.,center]@np.linalg.inv(np.c_[np.ones(4),p[c[ci]]]) for center,ci in zip(xyz.mean(1),owners)])
            kface=np.sum(ks*bary,axis=1);q=-kface[:,None]*gt[owners]
            av=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2;av[np.einsum('ij,ij->i',av,xyz.mean(1)-p[c[owners]].mean(1))<0]*=-1
            powers.append(float(np.einsum('ij,ij->',q,av)))
        error=sum(powers)/max(sum(map(abs,powers))/2,1e-4)
        rows.append({'bodies':pair,'area_m2':float(a.sum()),'area_mean_T_k':mean,'z_m':z,'raw_face_Fourier_outward_w':powers,
                     'raw_interface_relative_mismatch':error,'five_percent_diagnostic_passed':bool(abs(error)<.05)})
        for bid in layer_ends:
            if bid in pair:layer_ends[bid].append((z,mean))
    layers=[]
    for bid,ends in layer_ends.items():
        ends.sort();box=by[bid]['boxes_m'][0];k=float(material(by[bid]['material'],300.,meta['package_sigma_s_m'])[0])
        gradient_average=float(-vol[b==bid]@gt[b==bid,2]*k/box[5]);drop=ends[1][1]-ends[0][1]
        layers.append({'body':bid,'thickness_m':box[5],'mean_top_minus_bottom_k':drop,'layer_average_down_w':-gradient_average,
                       'kA_deltaT_over_thickness_w':k*box[3]*box[4]*drop/box[5],
                       'scope':'through-layer volume average/temperature identity; NOT raw face recovery or an independent bath validation'})
    plates=[]
    for bid in (1,2,3,4):
        box=by[bid]['boxes_m'][0];sides={}
        for label,z in (('bottom',box[2]),('top',box[2]+box[5])):
            candidates=f[np.all(abs(p[f,2]-z)<1e-11,axis=1)]
            selected=np.array([face for face in candidates if any(b[ci]==bid for ci in adj[tuple(sorted(face))])])
            xyz=p[selected];area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
            sides[label]={'area_m2':float(area.sum()),'area_mean_k':float(area@t[selected].mean(1)/area.sum())}
        ids=b==bid
        plates.append({'body':bid,'volume_mean_k':float(vol[ids]@t[c[ids]].mean(1)/vol[ids].sum()),'faces':sides})
    result={'field_sha256':e['vtu_sha256'],'mesh_sha256':sha(mesh/'mesh.npz'),'source_sha256':sha(Path(__file__)),
            'interfaces':rows,'layers':layers,'all_extra_interface_checks_passed':all(r['five_percent_diagnostic_passed'] for r in rows),
            'ceramic_plates':plates,
            'method':'actual one-sided P1 gradients with nodal k(T) interpolated at true triangle centroids; all selected materials S0',
            'qualified_device_result':False,'bath_recovery_applied':False}
    write(case/'raw_interface_audit.json',result);print(case.name,'raw interface diagnostics',result['all_extra_interface_checks_passed'],layers,flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mesh',type=Path,required=True);parser.add_argument('--case',type=Path,required=True);args=parser.parse_args()
    audit(args.mesh.resolve(),args.case.resolve())
