"""Additive controlled cold-ROI meshes from the identical corrected source registry."""
import argparse,json,time
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .geometry_complete import manifest,construct,audit,wire_routes
from .fem_g1 import tetra_geometry
from .fem_g1_run import execute
from .fem_g2c_mesh import verify_elmer_tetra_mapping

PLAN=ROOT/'data/cold_convergence/plan.json'


def metrics(mesh):
    d=np.load(mesh/'mesh.npz');p,c,b=(d[k] for k in ('points','cells','bodies'));m=json.loads((mesh/'manifest.json').read_text());vol,g=tetra_geometry(p,c)
    rows={}
    for name,ids in [('fixed_cold_ROI',[4,302,303,304,305]),('cold_ceramic',[4]),('attach',[302]),('MCT',[303]),('bath_Kovar',[300]),('TEC_all',m['conductor_path'])]:
        sel=np.isin(b,ids);V=float(vol[sel].sum());N=int(sel.sum());rows[name]={'volume_m3':V,'tetrahedra':N,'h_eff_m':(V/N)**(1/3)}
    rays=[]
    for bid in (302,303):
        sel=b==bid;points=p[c[sel]];gg=g[sel]
        for x,y in [(-.000375,-.000275),(.000125,.000185),(.000385,.000345)]:
            a=np.einsum('ei,eji->ej',np.array([x,y,0.])-points[:,0],gg);a[:,0]+=1;bary_z=gg[:,:,2]
            lower=np.full(len(a),-np.inf);upper=np.full(len(a),np.inf);valid=np.ones(len(a),bool)
            for j in range(4):
                beta=bary_z[:,j];nonzero=abs(beta)>1e-12;cross=-a[:,j]/np.where(nonzero,beta,1.)
                lower=np.where(beta>1e-12,np.maximum(lower,cross),lower);upper=np.where(beta< -1e-12,np.minimum(upper,cross),upper)
                valid&=nonzero|(a[:,j]>=-1e-10)
            good=valid&np.isfinite(lower)&np.isfinite(upper)&(upper-lower>1e-12)
            lengths=upper[good]-lower[good];rays.append({'body':bid,'xy_m':[x,y],'tetra_segments':int(good.sum()),'total_z_span_m':float(lengths.sum()),
                'segment_length_um_quantiles':np.quantile(lengths*1e6,[0,.5,1]).tolist() if len(lengths) else []})
    result={'regions':rows,'axial_ray_segments':rays,'definition':'fixed physical body-union volume/count; ray segments are actual unstructured tetra intersections, not structured layers',
            'mesh_sha256':sha(mesh/'mesh.npz'),'source_sha256':sha(Path(__file__))}
    write(mesh/'cold_mesh_metrics.json',result);return result


def build(out,level):
    import gmsh,meshio
    if out.exists():raise ValueError('Use a new immutable mesh label')
    plan=json.loads(PLAN.read_text())['full_device'];inner=plan['inner_h_m'][level];outer=plan['outer_cold_h_m'][level]
    m=manifest();wires=wire_routes(m);out.mkdir(parents=True);write(out/'manifest.json',m);write(out/'wire_routes.json',wires)
    sources=[Path(__file__),ROOT/'tecooledmct/geometry_complete.py',ROOT/'data/geometry_complete/reference_v2.json',PLAN]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources};start=time.monotonic();gmsh.initialize();gmsh.logger.start()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4)
        gmsh.model.add('same_corrected_mm_CAD');construct(gmsh,m,True);gmsh.write(str(out/'reference.step'));gmsh.clear()
        gmsh.model.add('same_corrected_SI_cold_refinement');owner,surfaces=construct(gmsh,m)
        for key,value in [('Mesh.MeshSizeExtendFromBoundary',0),('Mesh.MeshSizeFromPoints',0),('Mesh.MeshSizeFromCurvature',28),
                          ('Mesh.MinimumCirclePoints',32),('Mesh.MeshSizeMin',.000018),('Mesh.MeshSizeMax',.0008),('Mesh.Algorithm3D',1),('Mesh.RandomSeed',20261030)]:gmsh.option.setNumber(key,value)
        fields=[]
        def boxfield(low,high,h):
            tag=gmsh.model.mesh.field.add('Box')
            for key,value in zip(('XMin','YMin','ZMin'),low):gmsh.model.mesh.field.setNumber(tag,key,float(value)-1e-8)
            for key,value in zip(('XMax','YMax','ZMax'),high):gmsh.model.mesh.field.setNumber(tag,key,float(value)+1e-8)
            gmsh.model.mesh.field.setNumber(tag,'VIn',h);gmsh.model.mesh.field.setNumber(tag,'VOut',.0008);gmsh.model.mesh.field.setNumber(tag,'Thickness',h*2);fields.append(tag)
        # Original non-ROI controls retained exactly.
        boxfield([-.0033,-.0033,m['hot_z_m']],[.0033,.0033,m['cold_z_m']+.0003],.00020)
        for row in m['bodies']:
            if row['kind']=='bridge':
                box=np.array(row['boxes_m'][0]);lo=box[:3].copy();hi=lo+box[3:];axis=row['cut_axis'];lo[axis]+=.0004;hi[axis]-=.0004
                if hi[axis]>lo[axis]:boxfield(lo,hi,.000035)
            if row['kind']=='hot_route':
                for box in row['boxes_m']:boxfield(np.array(box[:3]),np.array(box[:3])+box[3:],.000055)
        z=m['cold_z_m'];w=plan['inner_ROI_halfwidth_m'];dz=plan['inner_ROI_z_relative_to_cold_top_m']
        boxfield([-.0013,-.0013,z-.0006],[.0013,.0013,z+.00025],outer)
        boxfield([-w,-w,z+dz[0]],[w,w,z+dz[1]],inner)
        field=gmsh.model.mesh.field.add('Min');gmsh.model.mesh.field.setNumbers(field,'FieldsList',fields);gmsh.model.mesh.field.setAsBackgroundMesh(field)
        gmsh.model.mesh.generate(3);gmsh.model.mesh.optimize('Netgen')
        ids,xyz,_=gmsh.model.mesh.getNodes();p=np.array(xyz).reshape(-1,3);lookup={int(n):i for i,n in enumerate(ids)}
        def conn(nodes,width):return np.fromiter((lookup[int(v)] for v in nodes),int).reshape(-1,width)
        cc=[];bb=[];ff=[];tt=[];qq=[]
        for volume,bid in owner.items():
            types,elements,arrays=gmsh.model.mesh.getElements(3,volume)
            for typ,els,nodes in zip(types,elements,arrays):
                if typ!=4:raise ValueError('Linear tets only')
                c=conn(nodes,4);cc.append(c);bb.extend([bid]*len(c));qq.extend(gmsh.model.mesh.getElementQualities(els,'minSICN'))
        if sum(map(len,cc))>plan['mesh_cap_tets']:raise ValueError('Registered900000-tet cap exceeded')
        for tag,ss in surfaces.items():
            for s in ss:
                types,_,arrays=gmsh.model.mesh.getElements(2,s)
                for typ,nodes in zip(types,arrays):
                    if typ!=2:raise ValueError('Triangles only')
                    f=conn(nodes,3);ff.append(f);tt.extend([tag]*len(f))
        c=np.concatenate(cc);b=np.array(bb);f=np.concatenate(ff);t=np.array(tt);q=np.array(qq)
        np.savez_compressed(out/'mesh.npz',points=p,cells=c,bodies=b,faces=f,boundaries=t,quality=q)
        gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.write(str(out/'connected.msh'))
        proof=audit(m,p,c,b,f,t,q)
    finally:
        (out/'gmsh.log').write_text('\n'.join(gmsh.logger.get()));gmsh.finalize()
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Mesh source changed during generation')
    proof.update(level=level,inner_h_m=inner,outer_h_m=outer,source_sha256=hashes,mesh_sha256=sha(out/'mesh.npz'),
                 manifest_sha256=sha(out/'manifest.json'),elapsed_s=time.monotonic()-start,geometrically_identical=True,only_cold_sizing_changed=True)
    write(out/'audit.json',proof);metrics(out);execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],out,'grid')
    write(out/'elmer_mapping.json',verify_elmer_tetra_mapping(out));print('Cold mesh PASS',level,len(p),len(c),inner,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--level',type=int,choices=(0,1));p.add_argument('--metrics-only',action='store_true');a=p.parse_args()
    metrics(a.out.resolve()) if a.metrics_only else build(a.out.resolve(),a.level)
