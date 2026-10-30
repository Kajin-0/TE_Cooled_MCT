"""Independent analytic tests of raw face signs, source bias and layer geometry."""
import numpy as np
import pytest
from tecooledmct.cold_layer_benchmark import geometry,exact,K,Z,P
from tecooledmct.cold_interface_audit import affine,face_flux
from tecooledmct.fem_g2a import mesh_adjacency


def interface(p,c,b,pair):
    return np.array([f for f,owners in mesh_adjacency(c).items() if len(owners)==2 and sorted(b[owners])==list(pair)])


def test_independent_difference_gradient_is_exact_for_affine_field():
    p,c,b=geometry(2,[1,1,2]);t=300+p@np.array([3.,-5.,7.]);vol,g=affine(p,c,t)
    np.testing.assert_allclose(g,np.tile([3.,-5.,7.],(len(c),1)),atol=2e-8)
    assert vol.sum()==pytest.approx(1e-6*Z[-1])


def test_two_sided_flux_is_winding_invariant_for_three_material_analytic_flow():
    p,c,b=geometry(2,[1,1,2]);t=exact(p,False);kn=np.broadcast_to(np.array([K[int(v)] for v in b])[:,None],(len(c),4))
    for pair in ((1,2),(2,3)):
        faces=interface(p,c,b,pair);r,_=face_flux(p,c,b,faces,t,kn);s,_=face_flux(p,c,b,faces[:,::-1],t,kn)
        np.testing.assert_allclose(r['raw_outward_w'],[-P,P],rtol=1e-7)
        np.testing.assert_allclose(r['raw_outward_w'],s['raw_outward_w'],atol=1e-13)


def test_distributed_source_has_expected_first_layer_P1_raw_flux_bias():
    errors=[]
    for nz in (4,8):
        p,c,b=geometry(2,[1,1,nz]);t=exact(p,True);kn=np.broadcast_to(np.array([K[int(v)] for v in b])[:,None],(len(c),4))
        r,_=face_flux(p,c,b,interface(p,c,b,(2,3)),t,kn)
        expected=P*(1-1/(2*nz))
        assert r['raw_outward_w'][1]==pytest.approx(expected,rel=1e-7)
        errors.append(P-r['raw_outward_w'][1])
    assert errors[0]/errors[1]==pytest.approx(2.,rel=1e-7)


def test_unequal_mesh_power_fit_is_not_false_qualification():
    from tecooledmct.cold_convergence_summary import power_fit
    import numpy as np
    h=np.array([.09,.03,.02]);q=260+2*h*h
    r=power_fit(h,q)
    assert abs(r['observed_order']-2)<1e-7
    assert abs(r['three_point_limit']-260)<1e-9
    assert not r['qualified_GCI']
    assert 'nonmonotone' in power_fit(h,[1,3,2])['status']
    assert 'below1.3' in power_fit([3,2,1.8],[1,2,3])['status']
