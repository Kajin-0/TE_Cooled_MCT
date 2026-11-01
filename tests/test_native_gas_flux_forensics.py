"""Independent cofactor, oriented-facet, sparse-reaction and frozen-field checks."""
from pathlib import Path
import json

import numpy as np
import pytest

from tecooledmct import native_gas_flux_forensics as a

BASE=a.ROOT/'data/native_gas_flux_forensics_20261101'


def two_tets():
    p=np.array([[0.,0.,0.],[.001,0.,0.],[0.,.001,0.],[0.,0.,.001],[0.,0.,-.001]])
    return p,np.array([[0,1,2,3],[0,2,1,4]])


def test_exact_continuous_trace_can_have_raw_imbalance_with_conservative_reactions():
    p,c=two_tets();T=np.array([300.,300.,300.,290.,300.]);r=a.reconstruct(p,c,T,.0259)
    count=r['incidence']['count'];raw=r['face_power'][count==1].sum();jump=r['face_power'][count==2].sum()
    # One tet has grad T_z=-10/.001; the other zero. Shared trace is 300 K.
    exact=.0259*(10/.001)*(.001**2/2)
    assert raw==pytest.approx(exact,abs=1e-18)
    assert jump==pytest.approx(-exact,abs=1e-18)
    assert r['reaction'].sum()==pytest.approx(0.,abs=1e-18)
    assert r['reaction']+r['boundary_node_raw']+r['node_jump']==pytest.approx(np.zeros(5),abs=1e-18)
    assert np.allclose(T[c[0,:3]],300.) and np.allclose(T[c[1,:3]],300.)


@pytest.mark.parametrize('reverse',[False,True])
def test_affine_oblique_and_uniform_controls_have_exact_normals_flux_and_energy(reverse):
    p,c=two_tets();p=p@np.array([[1.,.2,-.1],[.3,1.4,.2],[0.,-.1,.8]])+.004
    if reverse:c=c[:,[1,0,2,3]]
    slope=np.array([450.,-730.,1200.]);T=280+p@slope;r=a.reconstruct(p,c,T,.0259)
    assert r['gradient']==pytest.approx(np.tile(slope,(2,1)),abs=1e-9)
    assert r['basis'].sum(1)==pytest.approx(np.zeros((2,3)),abs=1e-12)
    assert r['face_power'][r['incidence']['count']==2]==pytest.approx([0.],abs=1e-17)
    assert r['face_power'].sum()==pytest.approx(0.,abs=1e-17)
    inc=r['incidence'];v=inc['vectors'].reshape(-1,4,3)
    assert v.sum(1)==pytest.approx(np.zeros((2,3)),abs=1e-20)
    assert (r['K']-r['K'].T).toarray()==pytest.approx(np.zeros((5,5)),abs=1e-18)
    assert np.linalg.eigvalsh(r['K'].toarray()).min()>-1e-18
    assert (T-300)@r['reaction']==pytest.approx(.0259*np.sum(r['volume'])*slope@slope,rel=1e-12)
    z=a.reconstruct(p,c,np.full(5,300.),.0259)
    assert np.max(abs(z['face_power']))==np.max(abs(z['reaction']))==0.


@pytest.mark.parametrize('k',[0.,-1.,float('nan'),float('inf')])
def test_nonphysical_conductivity_is_rejected(k):
    p,c=two_tets()
    with pytest.raises(ValueError):a.reconstruct(p,c,np.full(5,300.),k)


def test_missing_duplicate_nonmanifold_and_degenerate_topology_fail():
    p,c=two_tets()
    with pytest.raises(ValueError):a.row_map(c,np.array([[0,1,2,99]]))
    with pytest.raises(ValueError):a.row_map(np.concatenate([c,c[:1]]),c)
    bad=p.copy();bad[3]=bad[0]
    with pytest.raises(ValueError):a.cofactor_geometry(bad,c)
    with pytest.raises(ValueError):a.oriented_incidence(p,np.concatenate([c,c[:1]]))
    with pytest.raises(ValueError):a.reconstruct(p,c,np.array([300.,300.,np.nan,300.,300.]),.0259)


def test_group_decomposition_redistribution_is_zero_sum_without_being_zero_locally():
    p,c=two_tets();r=a.reconstruct(p,c,np.array([300.,300.,300.,290.,300.]),.0259)
    inc=r['incidence'];bf=inc['count']==1;faces=inc['unique'][bf];raw=r['face_power'][bf]
    area=np.linalg.norm(inc['vectors'][inc['first'][bf]],axis=1);bodies=np.arange(len(faces))%2
    rows,allocated,_=a.allocation_decomposition(faces,bodies,raw,area,r['reaction'],r['boundary_node_raw'],r['node_jump'])
    assert sum(x['shared_node_redistribution_W'] for x in rows)==pytest.approx(0.,abs=1e-18)
    assert any(abs(x['shared_node_redistribution_W'])>1e-8 for x in rows)
    assert all(abs(x['identity_error_W'])<1e-18 for x in rows)
    assert allocated.sum()==pytest.approx(-r['reaction'].sum(),abs=1e-18)


def test_actual_SIF_controls_are_parsed_and_incompatible_laws_rejected():
    sif=(a.FROZEN/'phase_C/case.sif').read_text();k,laws=a.boundary_laws(sif)
    assert k==.0259 and len(laws)==217 and laws[27301] is None
    assert a.wall_values(np.array([[0.,0.,.0015],[0.,0.,.00559]]),laws[20004])==pytest.approx([300.,250.])
    with pytest.raises(ValueError):a.boundary_laws(sif.replace('300-50','300-49'))
    with pytest.raises(ValueError):a.boundary_laws(sif+'\nHeat Source = 1\n')
    with pytest.raises(ValueError):a.wall_values(np.array([[0.,0.,.02]]),laws[20004])


@pytest.fixture(scope='module')
def actual_reconstruction():
    m=np.load(a.FROZEN/'phase_C/mesh.npz');field=np.load(a.FROZEN/'phase_C/audited_field.npz')
    calc=a.reconstruct(m['points'],m['cells'],field['temperature_K'],.0259)
    return m,field,calc


def test_full_frozen_field_is_independently_reconstructed_without_solver(actual_reconstruction):
    m,old,r=actual_reconstruction;ids=a.row_map(r['incidence']['unique'],m['faces'])
    raw=r['face_power'][ids]
    assert raw==pytest.approx(old['raw_face_power_W'],abs=1e-16)
    assert raw.sum()==pytest.approx(-.01134729991118609,abs=1e-15)
    J=r['face_power'][r['incidence']['count']==2]
    assert len(J)==436389 and J.sum()==pytest.approx(.01134729991118609,abs=1e-15)
    assert np.max(abs(r['reaction']+r['node_jump']+r['boundary_node_raw']))<1e-15
    fixed=np.unique(m['faces']);free=np.ones(len(m['points']),bool);free[fixed]=False
    assert np.abs(r['reaction'][free]).sum()<1e-9
    assert np.abs(r['node_jump'][free]).sum()<1e-9
    assert r['node_jump'][fixed].sum()==pytest.approx(.01134729990950843,abs=1e-14)


def test_saved_exact_group_attribution_does_not_requalify_original_failure():
    r=a.read(BASE/'audit.json');groups={x['body']:x for x in r['groups']}
    assert r['new_meshes']==r['Elmer_runs']==r['linear_solves']==0
    assert r['new_device_temperature'] is None and not r['Rev3_modified']
    assert not r['original_raw_1percent_passed']
    assert r['original_raw_relative_mismatch']==pytest.approx(.3262738922721323)
    assert r['node_trace_conflict_K']==r['shared_edge_midpoint_trace_conflict_K']==0
    assert r['independent_reproduction']['owner_mismatches']==0
    assert r['native_CAD_faces_matched']==927 and r['node_connected_components']==1
    assert sum(groups[b]['difference_W'] for b in (3,4))==pytest.approx(.00864659931495372)
    assert sum(groups[b]['jump_contribution_W'] for b in (3,4))==pytest.approx(.00883737903358054)
    assert sum(groups[b]['shared_node_redistribution_W'] for b in (3,4))==pytest.approx(-.000190779718626818)
    assert abs(r['global_shared_node_redistribution_W'])<1e-15
    assert abs(r['work_W_times_K']-r['energy_W_times_K'])<1e-12
    assert r['planar_vs_curved']['planar']['allocation_minus_raw_W']>.011
    registration=a.read(BASE/'registration.json')
    assert registration['registration']==a.NOTE.read_text().split('## Results')[0]
    assert registration['source_sha256']==a.sha(Path(a.__file__))
    assert registration['original_extractor_sha256']==a.sha(a.ROOT/'tecooledmct/native_gas_conduction.py')
    for name,digest in a.read(a.FROZEN/'checksums.json')['artifact_sha256'].items():assert a.sha(a.FROZEN/name)==digest
    for name,digest in a.read(BASE/'checksums.json')['artifact_sha256'].items():assert a.sha(BASE/name)==digest


def test_actual_cold_solid_top_and_gas_normal_labels_are_consistent():
    # Gas-outward normal on a solid top is negative z, unlike a solid normal.
    loc=a.read(BASE/'localization.json');fig=a.read(BASE/'figure_provenance.json')
    top=next(p for p in loc['ceramic_patches'] if p['body']==4 and p['patch']=='top')
    assert top['triangles']==loc['cold_top_triangles']==fig['triangles']==424
    assert top['allocated_minus_raw_W']==pytest.approx(loc['cold_top_allocated_minus_raw_W'])
    assert loc['cold_top_outer_150um_strip']['fraction_of_cold_top_difference']==pytest.approx(.954663584589121)
    assert fig['source_sha256']==a.sha(a.ROOT/'tecooledmct/native_gas_flux_forensic_figures.py')
    assert fig['figure_sha256']==a.sha(BASE/'flux_jump_decomposition.png')
