"""Independent geometry dimensions, frame conversion and actual mesh regressions."""
import copy
import json
import os
import numpy as np
import pytest
from tecooledmct.geometry_registry import load, pins, profile, analytic_metrics


def test_source_registry_fails_closed_for_missing_or_false_provenance(tmp_path):
    registry = load()
    for mutation in ('missing_source', 'false_product', 'outside_range'):
        changed = copy.deepcopy(registry)
        if mutation == 'missing_source':changed['dimensions']['pin_diameter']['source'] = 'unknown'
        elif mutation == 'false_product':changed['identity']['verified_commercial_assembly'] = True
        else:changed['dimensions']['glass_od']['simulated'] = .5
        path = tmp_path/'bad.json'; path.write_text(json.dumps(changed))
        with pytest.raises(ValueError):load(path)


def test_pin_identity_and_handedness_against_independent_coordinate_table():
    data = load(); bottom = pins(data, 'bottom'); top = pins(data, 'top')
    expected = np.array([[4.368692,-3.174040],[1.668692,-5.135705],[-1.668692,-5.135705],
                         [-4.368692,-3.174040],[-5.4,0],[-4.368692,3.174040],
                         [-1.668692,5.135705],[1.668692,5.135705],[4.368692,3.174040]])
    np.testing.assert_allclose([r['xy_mm'] for r in bottom], expected, atol=5e-7)
    np.testing.assert_allclose([r['xy_mm'] for r in top], expected*[-1,1], atol=5e-7)
    assert [r['pin'] for r in top if r['function'].startswith('TEC')] == [1,9]
    assert [r['pin'] for r in top if r['function']=='detector'] == [7,8]
    assert [r['pin'] for r in top if r['function']=='thermistor'] == [5,6]
    # Winding reverses; rotation alone would preserve this orientation.
    a=np.array([r['xy_mm'] for r in bottom]); b=np.array([r['xy_mm'] for r in top])
    assert np.linalg.det(np.stack([a[1]-a[0],a[2]-a[0]]))*np.linalg.det(np.stack([b[1]-b[0],b[2]-b[0]])) < 0


def test_tangent_profile_differs_from_ellipse_and_has_independent_area():
    data=load(); xy=profile(data); area=abs(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1)))/2
    exact=analytic_metrics(data)
    assert area==pytest.approx(exact['outline_area_mm2'],rel=2e-6)
    assert exact['outline_area_mm2']==pytest.approx(367.410804535922)
    assert abs(area-np.pi*15.75*8.75)>60
    np.testing.assert_allclose(np.ptp(xy,axis=0),[31.5,17.5],atol=1e-12)


def test_independent_cad_and_actual_conformal_header_mesh(tmp_path):
    if os.environ.get('TE_FEM_SMOKE')!='1':pytest.skip('Actual Gmsh/OpenCASCADE geometry check')
    pytest.importorskip('gmsh')
    from tecooledmct.geometry_rebaseline import build
    build(tmp_path/'geometry',h_mm=1.0)
    result=json.loads((tmp_path/'geometry/geometry_audit.json').read_text())
    assert result['actual_mesh']['domains']==22
    assert result['actual_mesh']['metal_pin_isolation_passed']
    assert result['source_overlay']['max_bidirectional_polyline_distance_mm']<.08
    assert result['identity']['verified_commercial_assembly'] is False
    assert result['revised_full_device_physics']=='NOT RUN'
