"""No-mesher controls before the one global trial; immutable output tests later."""
import json
from pathlib import Path
import numpy as np
import pytest
from tecooledmct.v3_r32_surface_integrity import (
    DIRECTIONAL_FACES,boundary_sign,skin_incidence,validate_registration,
)
from tecooledmct.v3_r32_intersections import intersect_pairs,full_intersection_check

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_r32_global_surface_20261103'


def test_oriented_square_cad_boundary_and_reversal():
    t=np.array([[0,1,2],[0,2,3]])
    curves={1:np.array([[0,1]]),2:np.array([[1,2]]),3:np.array([[2,3]]),4:np.array([[3,0]])}
    assert boundary_sign(t,curves,[1,2,3,4])==1
    assert boundary_sign(t[:,[0,2,1]],curves,[1,2,3,4])==-1
    bad=t.copy();bad[0]=bad[0,[0,2,1]]
    with pytest.raises(ValueError):boundary_sign(bad,curves,[1,2,3,4])


def test_closed_positive_tetrahedral_SKIN_only_no_tets_generated():
    faces=np.array([[0,2,1],[0,1,3],[0,3,2],[1,2,3]])
    assert skin_incidence(faces)['PASS']
    assert not skin_incidence(faces[:-1])['PASS']
    faces[0]=faces[0,[0,2,1]]
    assert not skin_incidence(faces)['PASS']


@pytest.mark.parametrize('mode,expected',[('separate',False),('pierce',True),('coplanar_overlap',True),('touch',False),('parallel_gap',False)])
def test_triangle_intersection_independent_analytic_cases(mode,expected):
    a=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
    b=np.array([[2.,0.,0.],[3.,0.,0.],[2.,1.,0.]])
    if mode=='pierce':b=np.array([[.2,.2,-1.],[.2,.2,1.],[.5,.2,0.]])
    if mode=='coplanar_overlap':b=a+np.array([.1,.1,0.])
    if mode=='touch':b=np.array([[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]])
    if mode=='parallel_gap':b=a+np.array([0.,0.,.000001])
    assert bool(intersect_pairs(a[None],b[None])[0])==expected
    assert bool(intersect_pairs(b[None],a[None])[0])==expected


def test_BVH_complete_controls_detect_crossing_and_disjoint_cases():
    points=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[.2,.2,-1.],[.2,.2,1.],[.5,.2,0.]])
    triangles=np.array([[0,1,2],[3,4,5]])
    hit=full_intersection_check(points,triangles,np.array([10,20]),leaf_size=1)
    assert hit['measured_proper_intersections']==1 and not hit['traversal_complete']
    points[3:]+=10
    ok=full_intersection_check(points,triangles,np.array([10,20]),leaf_size=1)
    assert ok['traversal_complete'] and ok['measured_proper_intersections']==0


def test_exact_metadata_scope_without_hidden_mesh():
    source=json.loads((DATA/'source_metadata.json').read_text())
    assert len(source['faces'])==2440 and len(source['curves'])==4521
    assert len(source['domain_id_map'])==430
    assert DIRECTIONAL_FACES==set(range(2385,2390))|set(range(2397,2402))
    r=dict(runs=1,wall_limit_seconds=600.,CPUs=4,memory_GiB=8,triangle_limit=800000,
        directional_faces=sorted(DIRECTIONAL_FACES),tetrahedralization='NOT AUTHORIZED',PDE='NOT AUTHORIZED')
    assert validate_registration(r,source)
    r['directional_faces'].append(2411)
    with pytest.raises(ValueError,match='exact ten'):validate_registration(r,source)


@pytest.mark.parametrize('key,value',[('runs',2),('wall_limit_seconds',601.),('CPUs',5),('memory_GiB',12),('triangle_limit',800001)])
def test_no_budget_or_single_run_waiver(key,value):
    source=json.loads((DATA/'source_metadata.json').read_text())
    r=dict(runs=1,wall_limit_seconds=600.,CPUs=4,memory_GiB=8,triangle_limit=800000,
        directional_faces=sorted(DIRECTIONAL_FACES),tetrahedralization='NOT AUTHORIZED',PDE='NOT AUTHORIZED')
    r[key]=value
    with pytest.raises(ValueError):validate_registration(r,source)
