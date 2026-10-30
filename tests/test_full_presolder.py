"""New geometry and independent flux/reference checks; older evidence is immutable."""
import numpy as np
import pytest
from tecooledmct.full_presolder_slice import split_joint
from tecooledmct.flux_presolder_coupon import extrude,skin
from tecooledmct.flux_presolder_common import affine_geometry
from tecooledmct.full_presolder_flux import equilibrate,evaluate_rt0,p2_reference,p2_gradient


def cube():
    xy=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]]);tri=np.array([[0,1,2],[0,2,3]])
    return extrude(xy,tri,[0.,1.],[191])


def test_joint_clipping_is_conformal_and_exact_p1_without_moving_old_nodes():
    p,c,b=cube();f,owner=skin(c);tags=np.full(len(f),105);pi=np.zeros(len(f),int)
    pp,cc,bb,ff,tt,patch,edges=split_joint(p,c,b,f,tags,pi,[.25,.75],[216,191,217]);vol,_=affine_geometry(pp,cc)
    assert vol[bb==216].sum()==pytest.approx(.25)
    assert vol[bb==191].sum()==pytest.approx(.5)
    assert vol[bb==217].sum()==pytest.approx(.25)
    exterior,_=skin(cc)
    assert {tuple(sorted(row)) for row in ff}=={tuple(sorted(row)) for row in exterior}
    assert np.array_equal(pp[:len(p)],p)
    values=list(300+p@[1.,2.,3.])
    for a,b,t in edges:values.append((1-t)*values[int(a)]+t*values[int(b)])
    np.testing.assert_allclose(values,300+pp@[1.,2.,3.],atol=1e-12)


def test_rt0_constant_field_and_local_divergence_without_reactions():
    p,c,_=cube();q=np.tile([2.,-3.,4.],(len(c),1));r=equilibrate(p,c,np.ones(len(c)),q,np.zeros(len(c)))
    np.testing.assert_allclose(evaluate_rt0(p,c,r,np.full(4,.25)),q,atol=1e-12)
    assert r['max_cell_residual_w']<1e-12
    assert r['reaction_used'] is False


def test_independent_quadratic_reference_reproduces_polynomial_and_flux():
    p,c,_=cube();k=np.full(len(c),2.)
    def exact(x):return 300+x[:,0]**2+2*x[:,1]**2+3*x[:,2]**2+x[:,0]*x[:,1]
    r=p2_reference(p,c,k,-24.,exact)
    np.testing.assert_allclose(r['temperature'],exact(r['points']),atol=1e-9)
    center=p[c].mean(1);want=np.c_[2*center[:,0]+center[:,1],4*center[:,1]+center[:,0],6*center[:,2]]
    np.testing.assert_allclose(p2_gradient(r,np.full(4,.25)),want,atol=1e-9)


def test_joint_local_temperature_range_fails_closed():
    from tecooledmct.full_presolder_reference import material_properties
    joint={'k_w_mk':35.,'lower_k_w_mk':1.,'upper_k_w_mk':2/3}
    with pytest.raises(ValueError):material_properties('Presolder',np.array([289.]),joint=joint)
    with pytest.raises(ValueError):material_properties('Presolder',np.array([300.]))


def test_pin_view_mirror_preserves_functional_identities():
    from tecooledmct.full_presolder_geometry_audit import pin_profile
    bottom=pin_profile();top=pin_profile('top')
    assert [v['pin'] for v in bottom]==list(range(1,10))
    for a,b in zip(bottom,top):
        assert b['x_mm']==pytest.approx(-a['x_mm'])
        assert b['y_mm']==pytest.approx(a['y_mm'])
        assert a['function']==b['function']
    assert bottom[0]['function']=='TEC+' and bottom[8]['function']=='TEC-'
    assert bottom[4]['function']==bottom[5]['function']=='thermistor'


def test_existing_functional_endpoint_pair_cannot_match_reference_by_rotation():
    from tecooledmct.full_presolder_geometry_audit import pin_profile
    reference=pin_profile();xy=np.array([[r['x_mm'],r['y_mm']] for r in reference])
    tec_distance=np.linalg.norm(xy[0]-xy[8]);detector_distance=np.linalg.norm(xy[6]-xy[7])
    assert tec_distance==pytest.approx(10.8*np.sin(np.deg2rad(36)))
    assert detector_distance==pytest.approx(10.8*np.sin(np.deg2rad(18)))
    current_tec_distance=10.8*np.sin(np.deg2rad(18))
    assert current_tec_distance!=pytest.approx(tec_distance)
    assert 10.8!=pytest.approx(detector_distance)  # existing Au endpoints opposite


def test_genuine_oblique_elmer_and_independent_quadratic_reference(tmp_path):
    import os,shutil
    if os.environ.get('TE_FEM_SMOKE')!='1' or not shutil.which('ElmerSolver'):pytest.skip('Actual3D oblique Elmer verification')
    pytest.importorskip('meshio')
    from tecooledmct.full_presolder_benchmark import box,elmer,exact_t,K
    p,c,b=box(3);t,source=elmer(tmp_path/'oblique',p,c,b,'oblique');k=np.array([K[int(v)] for v in b]);_,g=affine_geometry(p,c);raw=-k[:,None]*np.einsum('ei,eij->ej',t[c],g)
    recovered=equilibrate(p,c,k,raw,np.full(len(c),source))
    reference=p2_reference(p,c,k,source,lambda x:exact_t(x,'oblique'))
    np.testing.assert_allclose(reference['temperature'],exact_t(reference['points'],'oblique'),atol=1e-8)
    assert recovered['max_cell_residual_w']<1e-9
