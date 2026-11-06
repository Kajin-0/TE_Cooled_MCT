#!/usr/bin/env python3
"""Independent no-PDE readback of preregistered original Gate B P2 coupon.
Reconstruct native two-sided currents, contact integral and terminal flux
from frozen mesh and saved P2 coefficient vector, separately from producer.
No stiffness assembly, P2 solve, mesh generation, or parameter substitution.
"""
from pathlib import Path
from collections import defaultdict
import argparse,hashlib,json,math
import numpy as np
from tecooledmct.v3_et_fem import tensors,SCENARIOS
from tecooledmct.flux_presolder_common import affine_geometry
ROOT=Path('/work')
BASE=ROOT/'data/v3_interconnect_et_20261102/B'
def hashfile(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def compute(result_dir):
    mesh=np.load(BASE/'fine_mesh/mesh.npz')
    orig=json.loads((BASE/'fine_field/result.json').read_text())
    reg=json.loads((BASE/'fine_mesh/registry.json').read_text())
    producer=json.loads((result_dir/'P2_coupon_result.json').read_text())
    coeff=np.load(result_dir/'P2_original_coupon_field.npz')['field']
    pos=mesh['points'];tet=mesh['cells'];mats=mesh['regions']
    triangles=mesh['triangles'];tags=mesh['faceids']
    raw_faces={int(x['tag']):x for x in reg['faces']}
    assert len(tet)==28691 and len(triangles)==17738 and len(coeff)==58993
    sigma=tensors(reg['groups'],mode='electric',scenario='NOM')
    assert SCENARIOS['NOM']['re']==1e-11
    encoded=np.stack((np.repeat(mats,4),tet.ravel()),axis=1)
    unique,back=np.unique(encoded,axis=0,return_inverse=True)
    conn=back.reshape(-1,4)
    edgepairs=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
    stacked=np.concatenate([np.sort(conn[:,[a,b]],axis=1) for a,b in edgepairs])
    edges,index=np.unique(stacked,axis=0,return_inverse=True)
    conn=np.column_stack((conn,index.reshape(6,len(tet)).T+len(unique)))
    assert len(unique)+len(edges)==len(coeff)
    # Build physical face incidence independent from first P2 producer.
    fstack=np.concatenate([tet[:,[1,2,3]],tet[:,[0,2,3]],
                           tet[:,[0,1,3]],tet[:,[0,1,2]]])
    fstack.sort(axis=1)
    ids=np.tile(np.arange(len(tet),dtype=np.int32),4)
    stype=np.dtype([('a','<i4'),('b','<i4'),('c','<i4')])
    fk=lambda x:np.ascontiguousarray(x,dtype=np.int32).view(stype).reshape(-1)
    order=np.argsort(fk(fstack))
    distinct,starts,counts=np.unique(fk(fstack[order]),return_index=True,return_counts=True)
    loc=np.searchsorted(distinct,fk(np.sort(triangles,axis=1)))
    assert np.array_equal(distinct[loc],fk(np.sort(triangles,axis=1)))
    def gradient(e,x):
        p=pos[tet[e]]
        J=np.column_stack((p[1]-p[0],p[2]-p[0],p[3]-p[0]))
        inv=np.linalg.inv(J)
        t=inv@(x-p[0])
        l=np.r_[1-t.sum(),t]
        g=np.vstack(([-1.,-1.,-1.],np.eye(3)))@inv
        gp=np.vstack(((4*l-1)[:,None]*g,
                       [4*(l[a]*g[b]+l[b]*g[a]) for a,b in edgepairs]))
        return coeff[conn[e]]@gp
    ledger=defaultdict(lambda:[0.,0.,0.,0,0.])
    source_out=0.;drain_out=0.
    nat=defaultdict(float)
    for f,tag,k in zip(triangles,tags,loc):
        row=raw_faces[int(tag)]
        entries=ids[order][starts[k]:starts[k]+counts[k]]
        olist=row['owners']
        assert len(entries)==len(olist)
        entries=sorted(entries,key=lambda e:int(mats[e]))
        assert [int(mats[e]) for e in entries]==olist
        a,b,c=pos[f]
        area_vec=np.cross(b-a,c-a)*.5
        centroid=(a+b+c)/3
        if np.dot(area_vec,centroid-pos[tet[entries[0]]].mean(axis=0))<0:
            area_vec=-area_vec
        g0=gradient(entries[0],centroid)
        flux0=float(-area_vec@(sigma[mats[entries[0]]]@g0))
        if len(entries)==2:
            g1=gradient(entries[1],centroid)
            flux1=float(area_vec@(sigma[mats[entries[1]]]@g1))
            r0,r1=olist
            name=(reg['groups'][r0]['name'],reg['groups'][r1]['name'])
            v=ledger[name]
            v[0]+=flux0;v[1]+=flux1;v[3]+=1;v[4]+=np.linalg.norm(area_vec)
            # Separate P2 face integral: vertex P2 shape integrates to zero,
            # three edge shape functions each integrate to area/3.
            look={(int(region),int(vertex)):idx for idx,(region,vertex) in enumerate(unique)}
            a3=np.asarray([look[(r0,int(x))] for x in f],np.int32)
            b3=np.asarray([look[(r1,int(x))] for x in f],np.int32)
            # independent global edge lookup (sorted material-aware solution indices)
            keytype=np.dtype([('x','<i4'),('y','<i4')])
            keys=np.ascontiguousarray(edges,dtype=np.int32).view(keytype).reshape(-1)
            def edge_nodes(verts):
                ps=np.array([sorted((int(verts[i]),int(verts[j])))
                    for i,j in ((0,1),(0,2),(1,2))],np.int32)
                at=np.searchsorted(keys,np.ascontiguousarray(ps,dtype=np.int32).view(keytype).reshape(-1))
                return len(unique)+at
            ja=coeff[edge_nodes(a3)]
            jb=coeff[edge_nodes(b3)]
            contact=float(np.linalg.norm(area_vec)/SCENARIOS['NOM']['re']*
                          np.mean(ja-jb))
            v[2]+=contact
        else:
            ep=int(row['electrical_port'])
            if ep==0:source_out+=flux0
            if ep==1:drain_out+=flux0
    assert len(ledger)==11 and sum(x[3] for x in ledger.values())==1574
    sourceI=producer['P2_unit_potential_current_A']
    originals={tuple(x['pair']):x for x in producer['P2_cuts'] if 'pair' in x}
    result={}
    for name,nums in ledger.items():
        original=originals[name]
        rel1=abs(nums[0]-original['raw_a_A'])/sourceI
        rel2=abs(nums[1]-original['raw_b_A'])/sourceI
        rel3=abs(nums[2]-original['natural_A'])/sourceI
        assert max(rel1,rel2,rel3)<2e-11,(name,rel1,rel2,rel3)
        result[' → '.join(name)]={
           'triangles':nums[3],'area_m2':nums[4],
           'independently_reconstructed_raw_a_A':nums[0],
           'independently_reconstructed_raw_b_out_A':nums[1],
           'independently_reconstructed_contact_A':nums[2],
           'max_original_producer_relative_difference':max(rel1,rel2,rel3)}
    terminal={str(k):next(x for x in producer['P2_cuts'] if x.get('terminal')==k) for k in (0,1)}
    assert abs(source_out-terminal['0']['raw_out_A'])/sourceI<2e-11
    assert abs(drain_out-terminal['1']['raw_out_A'])/sourceI<2e-11
    result_status={
        'status':'PASS independent archived P2 raw/contact current readback; prospective electrical Gate B remains STOP',
        'source':'original 28691 TET4 coupon saved field; no assembly, solve, mesh or coefficient change',
        'original_gate_B':'FAIL/STOP',
        'prospective_P2':'STOP',
        'raw_original_gate_limit_rel':.001,
        'source_unitV_current_A':sourceI,
        'contact_triangles':1574,
        'material_interfaces':11,
        'face_current_results':result,
        'source_terminal_outward_A':source_out,
        'drain_terminal_outward_A':drain_out,
        'max_reconstruction_disagreement_rel':max(x['max_original_producer_relative_difference'] for x in result.values()),
        'source_file_SHA256':{
         'P2_saved_field':hashfile(result_dir/'P2_original_coupon_field.npz'),
         'P2_result':hashfile(result_dir/'P2_coupon_result.json'),
         'fine_mesh':hashfile(BASE/'fine_mesh/mesh.npz'),
         'fine_registry':hashfile(BASE/'fine_mesh/registry.json')},
        'caveats':['This audit independently verifies interface and terminal raw P2 current, not separately converged P2 mesh refinement',
                  'P2 interior-plane integrals are evaluated in original registered producer only',
                  'Material values are original selected NOM assumptions; not measured parameters']}
    return result_status
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--result-dir',type=Path,default=Path('/out'))
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    r=compute(args.result_dir)
    if args.out:
        with args.out.open('x') as f:
            json.dump(r,f,indent=2)
            f.write('\n')
    print('P2_INDEPENDENT',json.dumps({'status':r['status'],'max_reconstruction_disagreement_rel':r['max_reconstruction_disagreement_rel'],
          'contact_triangles':r['contact_triangles']}),flush=True)
if __name__=='__main__':main()
