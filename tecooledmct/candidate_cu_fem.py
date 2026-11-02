"""Independent P1 electrical/thermal fixture algebra; no TEC/OEM fitting."""
from itertools import permutations
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu


def assemble(points,tets,conductivity):
    if not np.isfinite(conductivity) or conductivity<=0:raise ValueError('Positive finite conductivity required')
    x=points[tets];E=x[:,1:]-x[:,:1];det=np.linalg.det(E)
    if not np.isfinite(E).all() or np.any(abs(det)<1e-30):raise ValueError('Degenerate/nonfinite element')
    g=np.empty((len(tets),4,3));g[:,1:]=np.linalg.inv(E).transpose(0,2,1);g[:,0]=-g[:,1:].sum(axis=1)
    volume=abs(det)/6
    ke=conductivity*volume[:,None,None]*np.einsum('eia,eja->eij',g,g)
    K=coo_matrix((ke.ravel(),(np.repeat(tets,4,axis=1).ravel(),np.tile(tets,(1,4)).ravel())),shape=(len(points),len(points))).tocsr()
    return K,volume,g,det


def solve_dirichlet(K,boundary,values,source=None):
    boundary=np.asarray(boundary,bool);values=np.asarray(values,float)
    if values.ndim==1:values=values[:,None]
    if len(values)!=K.shape[0] or not boundary.any() or not np.isfinite(values).all():raise ValueError('Invalid Dirichlet system')
    free=~boundary;u=values.copy()
    if source is None:source=np.zeros_like(u)
    if np.asarray(source).ndim==1:source=np.asarray(source)[:,None]
    if free.any():u[free]=splu(K[free][:,free].tocsc()).solve((source-K@values)[free])
    return u,K@u-source


def gradient(u,tets,g):
    return np.einsum('ei,eij->ej',u[tets[:,1:]]-u[tets[:,:1]],g[:,1:])


def plane_current(points,tets,J,axis,position):
    """Exact constant-J integration on true tet/plane polygons, half-open ownership."""
    x=points[tets];d=x[:,:,axis]-position;eps=1e-13
    candidates=np.flatnonzero((d.min(axis=1)<-eps)&(d.max(axis=1)>=-eps))
    total=0.;area_total=0.;other=[j for j in range(3) if j!=axis]
    for e in candidates:
        poly=[x[e,i] for i in range(4) if abs(d[e,i])<=eps]
        for i in range(4):
            for j in range(i+1,4):
                if d[e,i]*d[e,j]<0 and abs(d[e,i])>eps and abs(d[e,j])>eps:
                    poly.append(x[e,i]+(x[e,j]-x[e,i])*d[e,i]/(d[e,i]-d[e,j]))
        if len(poly)<3:continue
        poly=np.unique(np.round(np.array(poly),14),axis=0)[:,other]
        if len(poly)<3:continue
        c=poly.mean(axis=0);poly=poly[np.argsort(np.arctan2(poly[:,1]-c[1],poly[:,0]-c[0]))]
        area=abs(np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1)))/2
        total+=J[e,axis]*area;area_total+=area
    return total,area_total


def uniform_bar():
    shape=(5,3,3);axes=(np.linspace(0,.01,5),np.linspace(0,.001,3),np.linspace(0,.001,3))
    points=np.array(np.meshgrid(*axes,indexing='ij')).reshape(3,-1).T;tets=[]
    index=lambda a:np.ravel_multi_index(tuple(a),shape)
    for i in range(4):
        for j in range(2):
            for k in range(2):
                for perm in permutations(range(3)):
                    p=np.array([i,j,k]);ids=[index(p)]
                    for a in perm:p=p.copy();p[a]+=1;ids.append(index(p))
                    tets.append(ids)
    return points,np.array(tets,int)


def analytic_controls():
    points,tets=uniform_bar();sigma=1/1.72e-8;K,v,g,_=assemble(points,tets,sigma)
    boundary=(points[:,0]==0)|(points[:,0]==.01);values=np.zeros(len(points));values[points[:,0]==0]=1.
    u,r=solve_dirichlet(K,boundary,values);u=u[:,0];r=r[:,0]
    expected=1-points[:,0]/.01;G=sigma*1e-6/.01;grad=gradient(u,tets,g)
    work=float(r[points[:,0]==0].sum());energy=float(np.sum(sigma*v*np.sum(grad*grad,axis=1)))
    current,area=plane_current(points,tets,-sigma*grad,0,.005)
    zero,_=solve_dirichlet(K,boundary,np.zeros(len(points)))
    result=dict(max_affine_error=float(max(abs(u-expected))),relative_G_error=abs(work/G-1),
        relative_energy_error=abs(energy/G-1),relative_cut_error=abs(current/G-1),cut_area_m2=area,
        max_uniform_zero=float(abs(zero).max()),expected_R_ohm=1/G,observed_R_ohm=1/work)
    if max(result[k] for k in ('max_affine_error','relative_G_error','relative_energy_error','relative_cut_error','max_uniform_zero'))>1e-9:
        raise AssertionError('Independent analytic3D electrical bar failed')
    return result
