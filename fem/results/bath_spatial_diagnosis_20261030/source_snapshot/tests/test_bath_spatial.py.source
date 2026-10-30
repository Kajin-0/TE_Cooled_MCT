"""Independent affine operator, orientation and fixed-mask checks."""
import json
import numpy as np
import pytest
from tecooledmct.bath_spatial_audit import gradients,geometry_flux,partitions,PLAN,ROOT
from tecooledmct.cold_layer_benchmark import geometry
from tecooledmct.flux_presolder_coupon import skin

def test_cross_product_gradient_and_signed_support_identity_are_orientation_independent():
    p,c,b=geometry(2,[1,1,1]);b[:]=300;T=300+p@np.array([2.,-3.,5.]);phi=np.zeros(len(p))
    f,owner=skin(c);tags=np.where(np.all(abs(p[f,2])<1e-13,axis=1),101,999)
    for cc in [c,c[:,[1,0,2,3]]]:
        vol,g=gradients(p,cc,T);np.testing.assert_allclose(g,np.tile([2.,-3.,5.],(len(c),1)),rtol=0,atol=2e-8)
        d,i,j=geometry_flux(p,cc,b,f,tags,T,phi,np.ones(len(c)),{'bodies':[{'id':300,'material':'Kovar'}]})
        assert i['raw_bath_W']==pytest.approx(17.3*5e-6,abs=1e-12)
        assert abs(i['closure_error_W'])<1e-12
        assert i['raw_bath_W']==pytest.approx(np.sum(d['density_W_m2']*d['areas_m2']),abs=1e-15)
        assert np.all(d['outward_area_vectors_m2'][:,2]<0)

def test_physical_partitions_are_geometry_only_and_quadrants_cover_points():
    m=json.loads((ROOT/'fem/results/cold_bath_rev3_20261030/meshes/bath3/manifest.json').read_text());plan=json.loads(PLAN.read_text())
    xy=np.array([[0,0,0],[.0142,0,0],[.0122,.002,0],[-.004368691769624717,-.003174040362379355,0],[-.0028,.0027,0]])
    seg=np.array([[[-.02,-.02],[.02,-.02]],[[-.02,.02],[.02,.02]]])
    groups=partitions(xy,m,seg,plan)
    assert groups['physical'].tolist()==['hot_footprint','mount_hole_2','mount_hole_2','glass_annulus_1','projected_hot_routes']
    assert set(groups)=={'physical','radial','quadrant','angular'}
    for labels in groups.values():assert len(labels)==len(xy)
