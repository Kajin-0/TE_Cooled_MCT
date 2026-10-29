"""Small analytic tests for reporting geometry, not additional PDE executions."""
import numpy as np
import pytest
from reports.field_geometry import plane_section,section_values,node_map,cell_map


def test_true_tetra_section_area_and_affine_field():
    p=np.array([[0.,0,0],[1.,0,0],[0.,1,0],[0.,0,1]]);c=np.array([[0,1,2,3]])
    section=plane_section(p,c,axis=2,coordinate=.25);xyz=section['xyz'];area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1).sum()/2
    assert area==pytest.approx(.75**2/2,rel=1e-13)
    values=280+p@[1.,2.,3.];np.testing.assert_allclose(section_values(section,c,values),280+xyz@[1.,2.,3.],atol=1e-13)


def test_coplanar_face_is_not_double_counted():
    p=np.array([[0.,0,0],[1.,0,0],[0.,1,0],[0.,0,1],[0.,0,-1]]);c=np.array([[0,1,2,3],[0,2,1,4]])
    section=plane_section(p,c,axis=2,coordinate=0.)
    assert len(section['xyz'])==1 and section['cells'][0]==0


def test_permuted_nodes_and_cells_are_matched_and_duplicates_rejected():
    p=np.array([[0.,0,0],[1.,0,0],[0.,1,0],[0.,0,1],[0.,0,-1]]);permutation=np.array([3,2,0,4,1]);index,distance=node_map(p,p[permutation]);np.testing.assert_array_equal(p[permutation][index],p);assert distance==0
    c=np.array([[0,1,2,3],[0,2,1,4]]);np.testing.assert_array_equal(cell_map(c,c[::-1,::-1]),[1,0])
    with pytest.raises(ValueError):node_map(p,np.array([p[0]]*len(p)))


def test_section_does_not_fill_separated_solid_voids():
    tet=np.array([[0.,0,0],[1.,0,0],[0.,1,0],[0.,0,1]]);p=np.vstack([tet,tet+[10,0,0]]);c=np.array([[0,1,2,3],[4,5,6,7]])
    section=plane_section(p,c,axis=2,coordinate=.25);tri=section['xyz']
    assert len(tri)==2
    assert np.all(np.ptp(tri[:,:,0],axis=1)<1.)
