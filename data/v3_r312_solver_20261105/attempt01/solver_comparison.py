#!/usr/bin/env python3
"""R3.12 audited sparse scalar P1-FEM: unit Poisson on Au bond 8.

Read only native source mesh and native face tags.
Small mesh benchmark: no physical constitutive law, no full-package PDE.
Compare R39 R310 R311 on exactly the same native CAD face 2399 Dirichlet.
Report true unpreconditioned relative residuals, PCG, ILU-GMRES and direct.
"""
from pathlib import Path
import json, hashlib, time, resource, warnings
import numpy as np
import scipy
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spilu, gmres, cg, spsolve, LinearOperator

ROOT=Path('/input')
OUT=Path('/out')
START=time.monotonic()
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for blk in iter(lambda:f.read(4<<20),b''):
            h.update(blk)
    return h.hexdigest()
def record():
    print('R312_PROGRESS',round(time.monotonic()-START,2),flush=True)
meta=json.loads((ROOT/'source_metadata.json').read_text())
fac=np.loadtxt(ROOT/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
faceowners=meta['faces']
region_id=420
eligible_tags=[int(k) for k,v in faceowners.items() if region_id in v['owner_volume_ids']]
mask=np.isin(fac[:,4],eligible_tags)
nativefaces=fac[mask]
counts=np.bincount(nativefaces[:,4],minlength=2441)
dirichlet_face=int(np.argmax(counts))
assert dirichlet_face==2399
dirichlet_nodes=np.unique(nativefaces[nativefaces[:,4]==dirichlet_face,1:4])
meshes=[
    ('R39','R39_430_domains.1.ele','R38_430_domains.1.node'),
    ('R310','R39_430_domains.1.ele','R310_430_domains.1.node'),
    ('R311','R311_430_domains.1.ele','R38_430_domains.1.node')
]
all_results={}
proof={}
for revision,e_name,n_name in meshes:
    t0=time.monotonic()
    efile=ROOT/e_name;nfile=ROOT/n_name
    tets=np.loadtxt(efile,dtype=np.int32,skiprows=1)
    region_tets=tets[tets[:,5]==region_id,1:5]
    node=np.loadtxt(nfile,dtype=np.float64,skiprows=1)
    gnodes=np.unique(region_tets)
    mapnodes=np.full(len(node)+1,-1,dtype=np.int32)
    mapnodes[gnodes]=np.arange(len(gnodes),dtype=np.int32)
    tetra=mapnodes[region_tets]
    fix=mapnodes[dirichlet_nodes]
    free=np.setdiff1d(np.arange(len(gnodes),dtype=np.int32),fix)
    assert 3000<len(free)<5000
    assert len(fix)==3072
    xyz=node[gnodes-1,1:4]
    p=xyz[tetra]
    J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
    det=np.linalg.det(J)
    assert np.all(det>0)
    volumes=det/6
    inv=np.linalg.inv(J)
    grads_ref=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
    grad=np.einsum('tji,aj->tai',inv,grads_ref)
    # Independently check coordinate reproduction: sum_i p_i kron grad(N_i) = I.
    sample=np.linspace(0,len(tetra)-1,17,dtype=int)
    check=np.einsum('tai,taj->tij',p[sample],grad[sample])
    affine_identity_max=float(np.max(np.abs(check-np.eye(3))))
    assert affine_identity_max<2e-8,affine_identity_max
    locK=volumes[:,None,None]*np.einsum('tai,tbi->tab',grad,grad)
    rows=np.broadcast_to(tetra[:,:,None],locK.shape).ravel()
    cols=np.broadcast_to(tetra[:,None,:],locK.shape).ravel()
    full=sp.coo_matrix((locK.ravel(),(rows,cols)),shape=(len(gnodes),len(gnodes))).tocsr()
    full.sum_duplicates()
    A=full[free,:][:,free].tocsr()
    rhs=np.bincount(tetra.ravel(),weights=np.broadcast_to(volumes[:,None]/4,(len(tetra),4)).ravel(),minlength=len(gnodes))[free]
    symmetry=float(sp.linalg.norm(A-A.T)/max(sp.linalg.norm(A),1e-30))
    diag=A.diagonal()
    assert np.min(diag)>0 and symmetry<1e-10
    nblocks,blockid=connected_components(A,directed=False)
    native_volume=float(volumes.sum())
    normb=float(np.linalg.norm(rhs))
    assert normb>0
    def residual(x):return float(np.linalg.norm(A@x-rhs)/normb)
    experiments={}
    print('R312_REGION',revision,'DOF',len(free),'tet',len(region_tets),'matrix_NNZ',A.nnz,'symmetry',symmetry,'affine',affine_identity_max,'wall',round(time.monotonic()-START,2),flush=True)

    # Sparse direct is the reference for algebraic behavior, NOT a physical truth.
    direct_time=time.monotonic()
    with warnings.catch_warnings(record=True) as warning:
        warnings.simplefilter('always')
        u_direct=spsolve(A,rhs)
    assert np.all(np.isfinite(u_direct))
    direct_result={'info':0,'relative_true_residual':residual(u_direct),
        'wall_seconds':round(time.monotonic()-direct_time,4),
        'warnings':[str(x.message) for x in warning]}
    experiments['sparse_direct']=direct_result
    print('R312_DIRECT',revision,direct_result,flush=True)

    jacobi=sp.diags(1./diag,format='csr')
    counter=[0]
    def callback(_):counter[0]+=1
    t1=time.monotonic()
    ucg,info=cg(A,rhs,M=jacobi,rtol=1e-8,atol=0,maxiter=2500,callback=callback)
    experiments['jacobi_CG']={'info':int(info),'iterations':counter[0],
        'relative_true_residual':residual(ucg),
        'wall_seconds':round(time.monotonic()-t1,4)}
    print('R312_CG',revision,experiments['jacobi_CG'],flush=True)

    # Incomplete LU is an asymmetric preconditioner, so use GMRES, NOT CG.
    # No matrix regularization and no change to geometry/physical constraints.
    for drop,fill in ((1e-3,8),(1e-5,16)):
        name=f'ILU_GMRES_drop_{drop:.0e}_fill_{fill}'
        t2=time.monotonic()
        try:
            ilu=spilu(A.tocsc(),drop_tol=drop,fill_factor=fill,permc_spec='COLAMD')
            pmat=LinearOperator(A.shape,matvec=ilu.solve,dtype=np.float64)
            counter=[0];last=[None]
            def cb(pre_res):
                counter[0]+=1
                last[0]=float(pre_res)
            u,info=gmres(A,rhs,M=pmat,restart=60,maxiter=50,
                         rtol=1e-8,atol=0,callback=cb,callback_type='pr_norm')
            experiments[name]={'info':int(info),'iterations':counter[0],
                'relative_true_residual':residual(u),
                'preconditioned_reported_last_residual':last[0],
                'relative_to_direct_solution_L2':float(np.linalg.norm(u-u_direct)/max(np.linalg.norm(u_direct),1e-30)),
                'ILU_nnz_L':int(ilu.L.nnz),'ILU_nnz_U':int(ilu.U.nnz),
                'wall_seconds':round(time.monotonic()-t2,4)}
        except Exception as ex:
            experiments[name]={'status':'ERROR','error':str(ex)[:450],
                'wall_seconds':round(time.monotonic()-t2,4)}
        print('R312_PRECONDITION',revision,name,experiments[name],flush=True)
        if time.monotonic()-START>100:raise TimeoutError('Total wall budget exceeded')
    all_results[revision]={
        'mesh_element_sha256':sha(efile),'mesh_node_sha256':sha(nfile),
        'tetrahedra':len(region_tets),'region_nodes':len(gnodes),
        'free_degrees_of_freedom':len(free),'dirichlet_nodes':len(fix),
        'native_Dirichlet_face':dirichlet_face,
        'native_Dirichlet_TRI3':int(counts[dirichlet_face]),
        'stiffness_NNZ':int(A.nnz),'stiffness_symmetry_relative':symmetry,
        'affine_gradient_identity_max_error':affine_identity_max,
        'signed_volumes_min_mm3':float(volumes.min()),'signed_volumes_total_mm3':native_volume,
        'stiffness_graph_connected_components':int(nblocks),
        'rhs_L2_norm':normb,'solve_experiments':experiments,
        'case_wall_seconds':round(time.monotonic()-t0,4)}
    record()
report={
    'status':'COMPLETED REGIONAL SCALAR SOLVER COMPARISON; NO PHYSICAL PDE / MESH CONVERGENCE QUALIFICATION',
    'model':'Bond 8 P1 scalar unit-coefficient Poisson f=1, homogeneous Dirichlet on CAD face2399, zero Neumann elsewhere',
    'nondimensional_note':'Coordinates in mm; k=1 mathematical benchmark, not device material',
    'meshes':['R39','R310','R311'],'runtime':{'numpy':np.__version__,'scipy':scipy.__version__},
    'geometry_modified':False,'tetrahedral_mesh_modified':False,'solver_regularization':False,
    'PDE_full_device':'NOT RUN','mesh_convergence':'NOT RUN',
    'results':all_results,
    'elapsed_seconds':round(time.monotonic()-START,3),
    'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2)}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'solver_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print('R312_COMPLETE',report['elapsed_seconds'],'results',json.dumps({k:v['solve_experiments'] for k,v in all_results.items()}),flush=True)
