"""Independent P1 transfer accuracy, body isolation and curved-skin bounds."""
import numpy as np
import pytest
from tecooledmct.cold20_projection import transfer_nodes,interpolate


def two_tets():
    base=np.array([[0,0,0],[.001,0,0],[0,.001,0],[0,0,.001]])
    base=base@np.array([[1,.3,.2],[.2,1,.1],[.1,.2,1.]])
    p=np.vstack([base,base+[.003,0,0]]);c=np.array([[0,1,2,3],[4,5,6,7]]);b=np.array([1,2])
    q=np.vstack([p,base.mean(0),(base+[.003,0,0]).mean(0)]);tc=[];tb=[]
    for i,cell in enumerate(c):
        for omit in range(4):tc.append([*np.delete(cell,omit),8+i]);tb.append(i+1)
    return p,c,b,q,np.array(tc),np.array(tb)


def test_P1_preserves_affine_and_constant_values_inside_each_body():
    p,c,b,q,tc,tb=two_tets();m=transfer_nodes(p,c,b,q,tc,tb)
    values=300+np.repeat([0,20],4)+p@np.array([5.,-7.,11.]);v=interpolate(m,values[:,None]).ravel()
    expected=300+np.array([0]*4+[20]*4+[0,20])+q@np.array([5.,-7.,11.])
    np.testing.assert_allclose(v,expected,atol=2e-12,rtol=0)
    np.testing.assert_allclose(interpolate(m,np.tile([300.,0.],(8,1))),np.tile([300.,0.],(10,1)),atol=1e-12)
    assert m['weights'].min()>=0 and m['displacement_m'].max()<1e-12
    for body in (1,2):assert np.isin(m['source_nodes'][m['body']==body],np.unique(c[b==body])).all()


def test_transfer_rejects_same_position_in_wrong_material_body():
    p,c,b,*unused=two_tets()
    with pytest.raises(ValueError,match='no admissible same-body'):
        transfer_nodes(p,c,b,p[4:],np.array([[0,1,2,3]]),np.array([1]))


def test_skin_projection_is_same_body_convex_and_bounded():
    p=np.array([[0,0,0],[.001,0,0],[0,.001,0],[0,0,.001]]);c=np.array([[0,1,2,3]]);b=np.array([1]);q=p.copy();q[0,0]=-1e-7
    m=transfer_nodes(p,c,b,q,c,b)
    assert 0<m['displacement_m'][0]<2e-6
    assert (m['body']==1).all() and m['weights'].min()>=0
    np.testing.assert_allclose(interpolate(m,np.ones((4,1))*300),300,atol=1e-12)


def test_bath_edge_star_bisection_is_conformal_conservative_and_preserves_cold_cells():
    from tecooledmct.cold_layer_benchmark import geometry
    from tecooledmct.fem_g2a import mesh_adjacency
    from tecooledmct.cold_interface_audit import affine
    from tecooledmct.cold20_bath_mesh import refine_stars
    p,c,b=geometry(2,[1,1,1]);adj=mesh_adjacency(c);faces=[];tags=[];selected=[]
    for face,owners in adj.items():
        if len(owners)==1 or b[owners[0]]!=b[owners[1]]:
            faces.append(face);bottom=np.all(abs(p[list(face),2])<1e-14);tags.append(101 if bottom else 999)
            if bottom:selected.extend(owners)
    f=np.array(faces);tags=np.array(tags);pp,cc,bb,ff,tt,edges=refine_stars(p,c,b,f,tags,selected)
    assert edges>0 and len(cc)>len(c)
    np.testing.assert_array_equal(pp[:len(p)],p)
    np.testing.assert_array_equal(cc[bb==3],c[b==3])
    v,_=affine(p,c,np.zeros(len(p)));vv,_=affine(pp,cc,np.zeros(len(pp)))
    for body in (1,2,3):assert vv[bb==body].sum()==pytest.approx(v[b==body].sum(),rel=1e-12)
    newadj=mesh_adjacency(cc);declared={tuple(sorted(x)) for x in ff}
    assert all(len(owners)==2 or face in declared for face,owners in newadj.items())
    for face,owners in newadj.items():
        if len(owners)==2 and bb[owners[0]]!=bb[owners[1]]:assert face in declared
    xyz=pp[ff[tt==101]];area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1).sum()/2
    assert area==pytest.approx(1e-6,rel=1e-12)
