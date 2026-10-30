"""Explicit new joint material volume on a protected, conformal88-leg mesh."""
import argparse,copy,json,shutil
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix,save_npz
from .g2d_data import ROOT,sha,dump
from .full_presolder_guard import preserve
from .fem_g1 import tetra_geometry
from .fem_g2a import mesh_adjacency
from .fem_g2b_connectivity import connectivity
from .fem_g2c_mesh import verify_elmer_tetra_mapping
from .fem_g1_run import execute

PARENT=ROOT/'fem/results/g3b_checkpoint_20261029/operators/operator_h0p1'


def audit_geometry(p,c,b,f,tags,m):
    vol,_=tetra_geometry(p,c);adj=mesh_adjacency(c);contacts={};conductor={row['id'] for row in m['bodies'] if row['material'] in ('P','N','Cu')}
    graph={i:set() for i in conductor};pairareas={}
    for face,owners in adj.items():
        if len(owners)>2:raise ValueError('Nonmanifold joint mesh')
        if len(owners)==2 and b[owners[0]]!=b[owners[1]]:
            pair=tuple(sorted((int(b[owners[0]]),int(b[owners[1]]))));x=p[list(face)];area=np.linalg.norm(np.cross(x[1]-x[0],x[2]-x[0]))/2;pairareas[pair]=pairareas.get(pair,0)+area
            if all(v in conductor for v in pair):graph[pair[0]].add(pair[1]);graph[pair[1]].add(pair[0])
    terminals=sorted(k for k,v in graph.items() if len(v)==1)
    if len(conductor)!=181 or sum(map(len,graph.values()))!=360 or len(terminals)!=2 or any(len(v) not in (1,2) for v in graph.values()):raise ValueError('Two-terminal conductor graph changed')
    if terminals!=sorted(m['terminal_planes'][t]['body'] for t in ('103','104')):raise ValueError('Electrical terminal bodies changed')
    physical_joint={191,216,217}&set(b)
    if any(any(x in physical_joint for x in pair) and any(x in conductor for x in pair) for pair in pairareas):raise ValueError('Joint touches a TEC conductor')
    for face,tag in zip(f,tags):
        if len(adj[tuple(sorted(face))])!=(2 if tag>=1001 else 1):raise ValueError('Face/boundary map changed')
    exterior={face for face,owners in adj.items() if len(owners)==1}
    declared={tuple(sorted(face)) for face,tag in zip(f,tags) if tag<1000}
    if exterior!=declared:raise ValueError('Unlisted crack or exterior facet in joint mesh')
    expected={tuple(row['bodies']):row for row in m['contacts']}
    if set(expected)!=set(pairareas):raise ValueError('Unexpected or missing material contact')
    for pair,area in pairareas.items():
        if not np.isclose(area,expected[pair]['area_m2'],rtol=.01 if expected[pair].get('curved') else 1e-7):raise ValueError('Material contact area changed')
    volumes={}
    for row in m['bodies']:
        value=float(vol[b==row['id']].sum());volumes[row['name']]=value
        if not np.isclose(value,row['expected_volume_m3'],rtol=.01 if row['material'] in ('Kovar','Glass','Pin','Steel','ZnSe') else 1e-7):raise ValueError('Material volume mismatch '+row['name'])
    proof=connectivity(c,b,conductor)
    return {'passed':True,'nodes':len(p),'tetrahedra':len(c),'domains':len(np.unique(b)),'graph_vertices':len(graph),'graph_edges':sum(map(len,graph.values()))//2,'terminals':terminals,'all88legs':sum(x['kind']=='leg' for x in m['bodies'])==88,'joint_to_TEC_conductor_contacts':False,'volumes_m3':volumes,'contact_areas_m2':{str(k):v for k,v in pairareas.items()},'connectivity':proof}


def build(out,k=35.,legacy=False):
    import meshio
    preserve()
    if out.exists():raise ValueError('Preserve completed mesh; choose new label')
    if not (10<=k<=80 or legacy and k==2):raise ValueError('Outside declared joint hypotheses')
    d=np.load(PARENT/'mesh.npz');p,c,b,f,tags=[d[x] for x in ('points','cells','bodies','faces','boundaries')];m=json.loads((PARENT/'manifest.json').read_text())
    body=next(x for x in m['bodies'] if x['id']==191);body.update(name='legacy_mount_control' if legacy else 'unidentified_metallic_presolder',material='Presolder',kind='presolder',physical_status='old insulating proxy control' if legacy else 'user-confirmed presence; actual alloy unknown, k is a frozen numerical hypothesis')
    m['presolder_config']={'k_w_mk':k,'lower_k_w_mk':1.,'upper_k_w_mk':2/3,'thickness_m':50e-6,'contacts_Rdoubleprime':[0.,0.],'wetted_fraction':1.,'legacy_control':legacy,'transport_policy':'constant proxy over assumed numerical290..320K interval, not measured k(T)','electrical_policy':'S0/tiny computational sigma preserved; no package carrier-transport claim; alumina separates joint from all P/N/Cu','thermal_geometry':'new physical joint role uses exact prior50um joint volume; protected old mount data remain unchanged'}
    out.mkdir(parents=True);np.savez_compressed(out/'mesh.npz',**{key:d[key] for key in d.files});dump(out/'manifest.json',m)
    for name in ('operators.npz','weights.npz','patches.json'):shutil.copy2(PARENT/name,out/name)
    patches=json.loads((out/'patches.json').read_text())
    for patch in patches:
        if patch['owner']==191:patch['owner_name']=body['name']
    dump(out/'patches.json',patches)
    meshio.write(out/'connected.msh',meshio.Mesh(p,[('triangle',f),('tetra',c)],cell_data={'gmsh:physical':[d['solver_boundaries'],b],'gmsh:geometrical':[d['solver_boundaries'],b]}),file_format='gmsh22',binary=False)
    execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],out,'grid')
    proof=audit_geometry(p,c,b,f,tags,m);proof.update(elmer_mapping=verify_elmer_tetra_mapping(out),source_mesh_sha256=sha(PARENT/'mesh.npz'),mesh_sha256=sha(out/'mesh.npz'),other_physics='same907patch cavity areas,F,gaps and surface weights; joint emissivity retained0.8 as controlled unknown coating hypothesis')
    dump(out/'audit.json',proof);print('Geometry audited:',out,len(p),len(c),flush=True)
    return proof

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--k',type=float,default=35.);parser.add_argument('--legacy',action='store_true');a=parser.parse_args();build(a.out.resolve(),a.k,a.legacy)


def build_split(out,contact=False):
    import meshio
    from .full_presolder_slice import split_joint
    preserve()
    if out.exists():raise ValueError('Preserve completed geometry')
    d=np.load(PARENT/'mesh.npz');m=json.loads((PARENT/'manifest.json').read_text())
    cuts=[-.000268,-.000222] if contact else [-.000245]
    assignments=[216,191,217] if contact else [191,191]
    p,c,b,f,tags,pi,edges=split_joint(d['points'],d['cells'],d['bodies'],d['faces'],d['boundaries'],d['patch_index'],cuts,assignments)
    if len(p)>150000:raise ValueError('Declared150000-node local joint mesh cap')
    if not np.array_equal(c[b<=189],d['cells'][d['bodies']<=189]):raise ValueError('TEC mesh changed')
    layer=next(row for row in m['bodies'] if row['id']==191);layer.update(name='unidentified_metallic_presolder',material='Presolder',kind='presolder')
    if contact:
        layer['box_m'][2]=cuts[0];layer['box_m'][5]=cuts[1]-cuts[0];layer['expected_volume_m3']=.0064**2*(cuts[1]-cuts[0])
        for bid,name,z,material in [(216,'lower_contact_film',-.00027,'ContactLower'),(217,'upper_contact_film',cuts[1],'ContactUpper')]:
            m['bodies'].append({'id':bid,'name':name,'material':material,'kind':'contact_film','box_m':[-.0032,-.0032,z,.0064,.0064,2e-6],'expected_volume_m3':.0064**2*2e-6,'package':True})
        for row in m['contacts']:
            if row['bodies']==[190,191]:row['bodies']=[190,216]
            if row['bodies']==[1,191]:row['bodies']=[1,217]
        next_tag=max(row['boundary_id'] for row in m['contacts'])+1
        pairs={(191,216):next_tag,(191,217):next_tag+1}
        adj=mesh_adjacency(c);extra=[];extra_tags=[]
        for face,owners in adj.items():
            if len(owners)==2:
                pair=tuple(sorted((int(b[owners[0]]),int(b[owners[1]]))))
                if pair in pairs:extra.append(face);extra_tags.append(pairs[pair])
        f=np.vstack([f,np.array(extra)]);tags=np.r_[tags,extra_tags];pi=np.r_[pi,np.full(len(extra),-1)]
        for pair,tag in pairs.items():m['contacts'].append({'bodies':list(pair),'area_m2':.0064**2,'boundary_id':tag})
    m['presolder_config']={'k_w_mk':35.,'lower_k_w_mk':1.,'upper_k_w_mk':2/3,'thickness_m':46e-6 if contact else 50e-6,'contacts_Rdoubleprime':[2e-6,3e-6] if contact else [0.,0.],'film_thickness_m':2e-6 if contact else 0.,'wetted_fraction':1.,'legacy_control':False,'transport_policy':'constant proxy, assumed numerical290..320K interval; alloy and k(T) unidentified','electrical_policy':'original passive potential extension, joint physically separated from TEC conductors by alumina','surface_policy':'same composite joint-side907patch optical law including contact-film sidewalls; emissivity0.8 unmeasured controlled hypothesis'}
    out.mkdir(parents=True);solver=tags.copy();solver[pi>=0]=20000+pi[pi>=0]
    np.savez_compressed(out/'mesh.npz',points=p,cells=c,bodies=b,faces=f,boundaries=tags,solver_boundaries=solver,patch_index=pi);np.savez_compressed(out/'prolongation.npz',edges=edges);dump(out/'manifest.json',m)
    shutil.copy2(PARENT/'operators.npz',out/'operators.npz');patches=json.loads((PARENT/'patches.json').read_text());areas=np.load(PARENT/'operators.npz')['areas'];x=p[f];a=np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1)/2;sel=pi>=0
    weights=csr_matrix((np.repeat(a[sel]/3,3),(np.repeat(pi[sel],3),f[sel].ravel())),shape=(len(areas),len(p)))
    actual=np.asarray(weights.sum(1)).ravel()
    if not np.allclose(actual,areas,rtol=1e-10,atol=1e-20):raise ValueError('Cavity patch area changed')
    weights=weights.multiply((1/areas)[:,None]).tocsr();save_npz(out/'weights.npz',weights)
    for patch in patches:
        patch['triangle_indices']=np.flatnonzero(pi==patch['index']).tolist()
        if patch['owner']==191:patch.update(owner_name='presolder_and_contact_side_group',surface_group_bodies=[191,216,217] if contact else [191])
    dump(out/'patches.json',patches)
    meshio.write(out/'connected.msh',meshio.Mesh(p,[('triangle',f),('tetra',c)],cell_data={'gmsh:physical':[solver,b],'gmsh:geometrical':[solver,b]}),file_format='gmsh22',binary=False);execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],out,'grid')
    proof=audit_geometry(p,c,b,f,tags,m);proof.update(elmer_mapping=verify_elmer_tetra_mapping(out),source_mesh_sha256=sha(PARENT/'mesh.npz'),mesh_sha256=sha(out/'mesh.npz'),source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str((ROOT/'tecooledmct/full_presolder_slice.py').relative_to(ROOT)):sha(ROOT/'tecooledmct/full_presolder_slice.py')},patch_areas_F_and_gaps_unchanged=True,new_points_exact_P1_edges=True)
    dump(out/'audit.json',proof);print('Split joint audited',out,len(p),len(c),flush=True);return proof
