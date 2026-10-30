"""Native CAD geometry/meshing tests for hypothetical corrected TO-66 cap."""
import json
import math
from pathlib import Path

import pytest

from tecooledmct import corrected_enclosure as c


def test_source_dimensions_and_clearance_not_hardcoded():
    g=c.assumptions()
    assert g['outer_radius_m']==pytest.approx(.0076)
    assert g['inner_radius_m']==pytest.approx(.0071)
    assert g['window_radius_m']==pytest.approx(.00295)
    assert g['header_top_z_m']==pytest.approx(.0015)
    assert g['roof_top_z_m']==pytest.approx(.0101)
    assert g['cavity_roof_z_m']==pytest.approx(.00965)
    assert g['window_to_die_top_min_m']==pytest.approx(.00407,abs=1e-7)
    assert g['roof_to_highest_resolved_solid_clearance_m']>0.
    assert len(g['parent_source_sha256'])==2
    assert g['safety'].startswith('geometry fixture only')


def test_gmsh_geometry_and_interface_area_audit(tmp_path):
    pytest.importorskip('gmsh')  # pinned FEM Docker supplies native Gmsh
    out=tmp_path/'cap-window'
    r=c.build(out,mesh=True)
    assert r['meshed_tetrahedra']>3000
    assert r['no_conformal_interface_to_corrected_88leg_mesh']
    assert r['conservative_thermal_3d_solution'] is False
    assert (out/'corrected_cap_window.step').stat().st_size>1000
    assert (out/'cap_window_only.msh').stat().st_size>1000
    audit=json.loads((out/'geometry_audit.json').read_text())
    assert len(audit['face_groups'])==9
    assert len(audit['actual_volumes_m3'])==3
    assert set(audit['volume_physical_groups'].values())=={7301,7302,7303}
    assert {x['physical_group_id'] for x in audit['face_groups'].values()}==set(range(7401,7410))
    for key in ('shell','roof','window'):
        assert audit['actual_volumes_m3'][key]==pytest.approx(
            audit['expected_solid_volumes_m3'][key],rel=1e-8)
    face=audit['face_groups']
    ro=r['outer_radius_m'];ri=r['inner_radius_m'];rw=r['window_radius_m']
    height=r['cavity_roof_z_m']-r['header_top_z_m']
    thickness=r['roof_top_z_m']-r['cavity_roof_z_m']
    assert face['shell_cavity_side']['area_m2']==pytest.approx(2*math.pi*ri*height,rel=1e-8)
    assert face['roof_window_interface']['area_m2']==pytest.approx(2*math.pi*rw*thickness,rel=1e-8)
    assert face['roof_shell_interface']['area_m2']==pytest.approx(math.pi*(ro**2-ri**2),rel=1e-8)
    assert face['window_cavity_underside']['area_m2']==pytest.approx(math.pi*rw**2,rel=1e-8)
    with pytest.raises(ValueError,match='overwrite'):
        c.build(out,mesh=False)


@pytest.mark.parametrize('change,value',[
    ('cap_wall_thickness_m',.01),
    ('window_diameter_m',.018),
    ('cap_height_above_header_m',.003),
    ('window_thickness_m',.001),
])
def test_nonphysical_enclosure_rejected(monkeypatch,tmp_path,change,value):
    data=json.loads(c.REGISTRY.read_text())
    data[change]=value
    f=tmp_path/'modified.json'
    f.write_text(json.dumps(data))
    monkeypatch.setattr(c,'REGISTRY',f)
    with pytest.raises(ValueError):
        c.assumptions()


@pytest.mark.parametrize('dimension',[
    'cap_wall_thickness_m','cap_height_above_header_m','cap_roof_thickness_m',
    'window_diameter_m','window_thickness_m',
])
@pytest.mark.parametrize('invalid',[0.,-.0001,float('nan'),float('inf'),-float('inf'),None,True])
def test_invalid_dimensions_fail_before_cad(monkeypatch,tmp_path,dimension,invalid):
    data=json.loads(c.REGISTRY.read_text());data[dimension]=invalid
    path=tmp_path/'bad.json';path.write_text(json.dumps(data))
    monkeypatch.setattr(c,'REGISTRY',path)
    with pytest.raises(ValueError,match='Finite positive'):
        c.assumptions()


@pytest.mark.parametrize('wall,height',[(.0076,.0086),(.0018,.0086),(.0005,.0040)])
def test_impossible_void_or_internal_collision(monkeypatch,tmp_path,wall,height):
    data=json.loads(c.REGISTRY.read_text())
    data.update(cap_wall_thickness_m=wall,cap_height_above_header_m=height)
    path=tmp_path/'collision.json';path.write_text(json.dumps(data))
    monkeypatch.setattr(c,'REGISTRY',path)
    with pytest.raises(ValueError):
        c.assumptions()
