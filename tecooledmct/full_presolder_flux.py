"""Independent full-mass Raviart--Thomas RT0 equilibration and P2 reference."""
import itertools
import numpy as np
from scipy.sparse import coo_matrix,bmat,csr_matrix
from scipy.sparse.linalg import spsolve
from .flux_presolder_common import affine_geometry,outward_vectors

PAIRS=list(itertools.combinations(range(4),2))
QUAD=np.full((4,4),.1381966011250105);np.fill_diagonal(QUAD,.5854101966249685)


def face_geometry(p,c):
    nc=len(c);allf=np.concatenate([np.delete(c,i,axis=1) for i in range(4)]);owner=np.tile(np.arange(nc),4)
    unique,first,inverse,count=np.unique(np.sort(allf,axis=1),axis=0,return_index=True,return_inverse=True,return_counts=True)
    if np.max(count)>2:raise ValueError('Nonmanifold flux domain')
    av=outward_vectors(p,c,allf[first],owner[first]);localav=outward_vectors(p,c,allf,owner)
    sign=np.sign(np.einsum('ij,ij->i',localav,av[inverse]));cellfaces=inverse.reshape(4,nc).T;sign=sign.reshape(4,nc).T
    return {'faces':unique,'area_vectors':av,'area':np.linalg.norm(av,axis=1),'owner':owner[first],'count':count,'cell_faces':cellfaces,'sign':sign}


def equilibrate(p,c,k,raw_q,source_w_m3,fixed=None):
    """Minimize integral |q_RT0-q_raw|²/k subject to each cell's heat balance.

    Face powers are shared H(div) unknowns. No FE reaction enters this method.
    The integrated boundary balance is constrained, NOT independent validation.
    """
    if len(c)>40000:raise ValueError('Declared40000-tet recovery benchmark cap')
    v,_=affine_geometry(p,c);geom=face_geometry(p,c);faces=geom['cell_faces'];sgn=geom['sign'];nf=len(geom['faces']);nc=len(c)
    matrix=np.zeros((nc,4,4));rhs=np.zeros((nc,4))
    for bary in QUAD:
        x=np.einsum('i,eij->ej',bary,p[c]);basis=(x[:,None,:]-p[c])/(3*v[:,None,None]);weight=v/(4*k)
        matrix+=np.einsum('eij,ekj,e->eik',basis,basis,weight)
        rhs+=np.einsum('eij,ej,e->ei',basis,raw_q,weight)
    matrix*=sgn[:,:,None]*sgn[:,None,:];rhs*=sgn
    M=coo_matrix((matrix.ravel(),(np.repeat(faces,4,axis=1).ravel(),np.tile(faces,(1,4)).ravel())),shape=(nf,nf)).tocsr()
    b=np.bincount(faces.ravel(),weights=rhs.ravel(),minlength=nf)
    B=coo_matrix((sgn.ravel(),(np.repeat(np.arange(nc),4),faces.ravel())),shape=(nc,nf)).tocsr()
    prescribed=np.zeros(nf);free=np.ones(nf,bool)
    if fixed:
        for face,value in fixed.items():prescribed[face]=value;free[face]=False
    source=v*np.broadcast_to(source_w_m3,nc);r=b-M@prescribed;s=source-B@prescribed
    mass=M[free][:,free];A=B[:,free];scale=float(np.median(mass.diagonal()))
    K=bmat([[mass/scale,A.T],[A,None]],format='csc');solution=spsolve(K,np.r_[r[free]/scale,s])
    flux=prescribed.copy();flux[free]=solution[:sum(free)]
    if not np.isfinite(flux).all():raise ValueError('Nonfinite recovered flux')
    residual=B@flux-source
    geom.update(flux=flux,raw_face_flux=np.einsum('ij,ij->i',raw_q[geom['owner']],geom['area_vectors']),cell_residual_w=residual,max_cell_residual_w=float(abs(residual).max()),global_balance_enforced=True,reaction_used=False)
    return geom


def evaluate_rt0(p,c,geom,bary):
    v,_=affine_geometry(p,c);x=np.einsum('i,eij->ej',bary,p[c]);out=geom['flux'][geom['cell_faces']]*geom['sign']
    return np.sum(out[:,:,None]*(x[:,None,:]-p[c])/(3*v[:,None,None]),axis=1)


def p2_reference(p,c,k,source,dirichlet):
    """Independent conforming quadratic thermal FEM; no Elmer or RT0 assembly."""
    if len(c)>40000:raise ValueError('Declared40000-tet independent P2 cap')
    vol,g=affine_geometry(p,c);edges=np.stack([c[:,pair] for pair in PAIRS],axis=1);unique,ix=np.unique(np.sort(edges.reshape(-1,2),axis=1),axis=0,return_inverse=True);conn=np.c_[c,ix.reshape(-1,6)+len(p)];points=np.vstack([p,p[unique].mean(1)])
    matrix=np.zeros((len(c),10,10));load=np.zeros((len(c),10))
    for bary in QUAD:
        grad=np.empty((len(c),10,3));grad[:,:4]=(4*bary-1)[None,:,None]*g
        shape=list(bary*(2*bary-1))
        for j,(a,b) in enumerate(PAIRS,4):grad[:,j]=4*(bary[a]*g[:,b]+bary[b]*g[:,a]);shape.append(4*bary[a]*bary[b])
        matrix+=np.einsum('eij,ekj,e->eik',grad,grad,vol*k/4);load+=vol[:,None]*np.broadcast_to(source,len(c))[:,None]*np.array(shape)[None,:]/4
    rows=np.repeat(conn,10,axis=1).ravel();cols=np.tile(conn,(1,10)).ravel();K=coo_matrix((matrix.ravel(),(rows,cols)),shape=(len(points),len(points))).tocsr();rhs=np.bincount(conn.ravel(),weights=load.ravel(),minlength=len(points))
    geom=face_geometry(p,c);boundary=geom['faces'][geom['count']==1];bn=np.unique(boundary);bedges=np.unique(np.sort(np.concatenate([boundary[:,[a,b]] for a,b in ((0,1),(0,2),(1,2))]),axis=1),axis=0)
    edge_map={tuple(row):i+len(p) for i,row in enumerate(unique)};nodes=np.r_[bn,[edge_map[tuple(row)] for row in bedges]];free=np.ones(len(points),bool);free[nodes]=False;t=np.zeros(len(points));t[nodes]=dirichlet(points[nodes]);rhs-=K@t;t[free]=spsolve(K[free][:,free].tocsc(),rhs[free])
    return {'points':points,'cells':conn,'temperature':t,'tet_gradients':g,'free_residual_l1_w':float(abs((K@t-rhs-K@np.where(free,0,t))[free]).sum())}


def p2_gradient(reference,bary):
    g=reference['tet_gradients'];t=reference['temperature'][reference['cells']];grad=np.einsum('ei,eij->ej',t[:,:4]*(4*bary-1),g)
    for j,(a,b) in enumerate(PAIRS,4):grad+=4*t[:,j,None]*(bary[a]*g[:,b]+bary[b]*g[:,a])
    return grad
