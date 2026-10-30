"""Independent geometry/sign/continuum checks and opt-in actual 3D Elmer coupon."""
import os, shutil
import numpy as np
import pytest
from tecooledmct.flux_presolder_common import affine_geometry, boundary_owners, outward_vectors, node_map
from tecooledmct.flux_presolder_coupon import extrude, skin, layers


def square():
    return np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]]),np.array([[0,1,2],[0,2,3]])


def test_affine_gradient_normal_orientation_and_negative_flux():
    p=np.array([[0.,0,0],[1.,0,0],[0.,1,0],[0.,0,1]]);c=np.array([[0,1,2,3]]);f=np.array([[0,1,2]])
    volume,g=affine_geometry(p,c);values=300+p@[2.,3.,4.]
    np.testing.assert_allclose(np.einsum('ei,eij->ej',values[c],g),[[2.,3.,4.]])
    assert volume[0]==pytest.approx(1/6)
    owners=boundary_owners(c,f);av=outward_vectors(p,c,f,owners)
    assert av[0,2]==pytest.approx(-.5)
    assert float(np.sum(-4*np.array([[0,0,1]])*av))==pytest.approx(2.)
    np.testing.assert_allclose(outward_vectors(p,c,f[:,::-1],owners),av)
    with pytest.raises(ValueError):node_map(p,np.zeros_like(p))


def test_extrusion_keeps_shared_diagonals_volume_and_material_interfaces():
    p2,tri=square();p,c,b=extrude(p2,tri,[0.,.1,1.],[1,2]);v,_=affine_geometry(p,c)
    assert v[b==1].sum()==pytest.approx(.1)
    assert v[b==2].sum()==pytest.approx(.9)
    f,owner=skin(c);av=outward_vectors(p,c,f,owner)
    np.testing.assert_allclose(av.sum(0),0,atol=1e-14)
    assert len(f)==20  # two top/bottom triangles plus eight sides per axial layer


def test_presolder_continuum_and_contact_series_resistance_limits():
    stack=layers(50e-6,35.,(2e-6,3e-6))
    resistance=sum(h/k for _,h,k,_ in stack)
    assert resistance==pytest.approx(.0011/17.3+50e-6/35+.00022/30+5e-6)
    continuum=layers(50e-6,35.,equal=True)
    assert sum(h/k for _,h,k,_ in continuum)==pytest.approx(sum(v[1] for v in continuum)/17.3)
    assert not any('contact' in name for name,*_ in layers(50e-6,35.))
    for thickness,k,contact in [(0.,35.,(0,0)),(50e-6,2.,(0,0)),(50e-6,35.,(float('nan'),0))]:
        with pytest.raises(ValueError):layers(thickness,k,contact)


def test_region_partition_does_not_invent_glass_or_pin_bath_area():
    import json
    from pathlib import Path
    from tecooledmct.flux_presolder_diagnosis import partition
    r=json.loads((Path(__file__).resolve().parents[1]/'data/g3b/enclosure_registry.json').read_text())
    labels,names=partition(np.array([[0,0,0],[.0054,.0006,0]]),np.array(['Kovar','Kovar']),r)
    assert labels.tolist()==['mount_footprint','seal_adjacent_Kovar_1']
    assert 'glass_annulus_1' in names and 'pin_root_1' in names


def test_discrete_residual_identity_includes_other_exterior_flux():
    from tecooledmct.flux_presolder_diagnosis import residual_identity
    p=np.array([[0.,0,0],[1.,0,0],[0.,1,0],[0.,0,1]]);c=np.array([[0,1,2,3]])
    f,owner=skin(c);tags=np.where(np.all(p[f,2]==0,axis=1),101,105)
    bath=np.unique(f[tags==101]);volume,_=affine_geometry(p,c)
    identity=residual_identity(p,c,f,tags,np.array([0]),np.array([[-2.,-3.,-4.]]),volume,np.array([0.]),bath)
    assert identity['raw_bath_out_w']==pytest.approx(2.)
    total=sum(identity[k] for k in ('raw_bath_out_w','other_exterior_weighted_raw_out_w','internal_face_weighted_jump_w','weighted_electrical_volume_work_w'))
    assert total==pytest.approx(2/3)
    assert abs(identity['other_exterior_weighted_raw_out_w'])>0


def test_genuine_three_dimensional_layered_elmer_coupon(tmp_path):
    if os.environ.get('TE_FEM_SMOKE')!='1' or not shutil.which('ElmerSolver'):pytest.skip('Opt-in actual3D Elmer coupon')
    pytest.importorskip('meshio')
    from tecooledmct.flux_presolder_coupon import solve
    p2,tri=square();p2*=.001;p,c,b=extrude(p2,tri,[0,.0011,.00115,.00137],[1,2,3])
    r,_,_,_,_=solve(tmp_path/'coupon',p,c,b,{1:17.3,2:35.,3:30.},{})
    expected=10/(.0011/17.3+50e-6/35+.00022/30)*1e-6
    assert r['solver_executed'] and r['solver_status']['exit_code']==0
    assert r['bottom_raw_out_w']==pytest.approx(expected,rel=1e-8)
    assert abs(r['reaction_energy_error_w'])<1e-9
