"""Independent polynomial sampling identity, not a fabricated device sample."""
import numpy as np
import pytest
from tecooledmct.bath_spatial_modes import polynomial_trace
from tecooledmct.bath_spatial_audit import gradients
def test_polynomial_trace_components_match_direct_exact_nodal_interpolant():
    p=np.array([[0.,0.,0.],[.001,0,0],[0,.001,0],[.0003,.0002,.0005]]);c=np.array([[0,1,2,3]]);face=p[:3];area=np.linalg.norm(np.cross(face[1]-face[0],face[2]-face[0]))/2;center=face.mean(0)
    d={'areas_m2':np.array([area]),'centroids_m':center[None,:],'apex_offset_xy_m':(p[3,:2]-center[:2])[None,:],'normal_height_m':np.array([p[3,2]])}
    T=300+p[:,2]*(10+2000*p[:,0]-1500*p[:,1])-200*p[:,2]**2;vol,g=gradients(p,c,T);r=polynomial_trace(d)
    assert r['exact_nodal_P1_trace_W']==pytest.approx(17.3*g[0,2]*area,abs=1e-12)
    assert not r['device_error_estimate']
