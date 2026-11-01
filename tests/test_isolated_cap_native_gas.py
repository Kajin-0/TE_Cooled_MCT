"""Independent SI controls and saved native-geometry gates; no CAD reattempt."""
from copy import deepcopy

import numpy as np
import pytest

from tecooledmct.corrected_enclosure import assumptions
from tecooledmct.isolated_cap_reader import cap_roles, expected_boxes
from tecooledmct.native_gas_audit import ROOT, PACKAGE, read, sha, step_units
from tecooledmct.native_gas_csg import identify_sources, source_bbox, partition_owners, check_manifold
from tecooledmct.native_gas_conduction import analytic_controls, profile, residual_and_flux, reservoir

BASE = ROOT/'data/isolated_cap_native_gas_20261101'


@pytest.mark.parametrize('length_scale', [1e-3, 1e3])
def test_both_thousandfold_length_errors_fail_closed(length_scale):
    a = assumptions()
    rows = [{'tag': i, 'volume_m3': v*length_scale**3,
             'bbox_m': (np.array(expected_boxes(a)[name])*length_scale).tolist()}
            for i,(name,v) in enumerate(a['expected_solid_volumes_m3'].items(),1)]
    with pytest.raises(ValueError): cap_roles(rows,a)


@pytest.mark.parametrize('fault',['missing','extra','negative','nan','datum','volume'])
def test_cap_roles_reject_missing_nonphysical_or_displaced_geometry(fault):
    q = read(BASE/'phase_A/qualification.json');rows=deepcopy(list(q['cap_roles'].values()))
    if fault=='missing':rows.pop()
    elif fault=='extra':rows.append(deepcopy(rows[0]))
    elif fault=='negative':rows[0]['volume_m3']*=-1
    elif fault=='nan':rows[0]['bbox_m'][0]=float('nan')
    elif fault=='datum':rows[0]['bbox_m'][2]+=1e-5
    elif fault=='volume':rows[0]['volume_m3']*=1.001
    with pytest.raises(ValueError):cap_roles(rows,assumptions())


def test_isolated_writer_and_independent_physical_reader():
    q=read(BASE/'phase_A/qualification.json');w=read(BASE/'phase_A/writer.json')
    assert q['phase_A_qualified'] and q['writer_pid']!=q['reader_pid']
    assert q['writer_CAD_imports']==q['reader_exports']==0
    assert w['attempts']==1 and read(BASE/'phase_A_final_status.json')['author_calls']==1
    assert q['cube_control'][0]['volume_m3']==pytest.approx(1e-9,rel=1e-8)
    assert q['reader_target_unit']=='M'
    text=(BASE/'phase_A/cap_window_mm_derivative.step').read_text()
    assert step_units(text)['cylinder_radii_declared_m']==pytest.approx([.00295,.0071,.0076])
    a=assumptions();roles=cap_roles(list(q['cap_roles'].values())[::-1],a)
    # Direct independent cylinder/annulus integrals, all in SI.
    volumes={'shell':np.pi*(.0076**2-.0071**2)*(.00965-.0015),
             'roof':np.pi*(.0076**2-.00295**2)*(.0101-.00965),
             'window':np.pi*.00295**2*(.0101-.00965)}
    for name,v in volumes.items():assert roles[name]['volume_m3']==pytest.approx(v,rel=1e-8)
    assert q['header_seal']['complete_annulus'] and not q['header_seal']['positive_volume_header_intrusion']
    assert q['header_seal']['area_m2']==pytest.approx(np.pi*(.0076**2-.0071**2),rel=1e-12)
    assert q['interfaces_m2']['roof_window']==pytest.approx(2*np.pi*.00295*.00045,rel=1e-10)
    assert sha(ROOT/q['derivative_path'])==q['derivative_sha256']==w['derivative_STEP_sha256']
    for group in ('source_sha256','input_sha256'):
        for path,digest in q[group].items():assert sha(ROOT/path)==digest


def test_first_reader_metadata_failure_retained_without_second_export():
    repair=read(BASE/'reader_metadata_repair.json')
    assert not repair['writer_reexecuted'] and repair['qualified']
    assert repair['initial_reader_sha256']==sha(BASE/'reader_metadata_failure/reader.py.snapshot')
    assert repair['final_reader_sha256']==sha(ROOT/'tecooledmct/isolated_cap_reader.py')
    assert repair['candidate_sha256']==sha(BASE/'phase_A/cap_window_mm_derivative.step')
    assert read(BASE/'phase_A_status.json')['failed_stage']=='reader'
    assert 'relative_to' in (BASE/'reader_metadata_failure/reader.log').read_text()
    registration=read(BASE/'registration.json')
    assert registration['registration']==(ROOT/'docs/ISOLATED_CAP_AND_NATIVE_GAS_20261101.md').read_text().split('## Results')[0]
    for path,digest in registration['source_sha256'].items():
        actual=sha(ROOT/path) if not path.endswith('isolated_cap_reader.py') else repair['initial_reader_sha256']
        assert actual==digest


def test_exact_source_body_mapping_and_negative_missing_duplicate_controls():
    m=read(PACKAGE/'manifest.json')
    rows=[{'tag':1000+i,'volume_m3':b['expected_volume_m3'],
           'bbox_m':source_bbox(b,m['registry']['dimensions'])} for i,b in enumerate(m['bodies'])]
    expected={r['tag']:b['id'] for r,b in zip(rows,m['bodies'])}
    assert identify_sources(rows[::-1],m)==expected
    assert len(expected)==216 and sum(b['kind']=='leg' for b in m['bodies'])==88
    with pytest.raises(ValueError):identify_sources(rows[:-1],m)
    with pytest.raises(ValueError):identify_sources(rows+[rows[0]],m)
    bad=deepcopy(rows);bad[0]['bbox_m'][2]+=1e-5
    with pytest.raises(ValueError):identify_sources(bad,m)


def test_boolean_ownership_rejects_overlap_and_disconnected_void():
    owner,envelope,gas=partition_owners([[(3,1),(3,2)],[(3,2)]],[42])
    assert owner=={2:42} and envelope=={1,2} and gas==1
    with pytest.raises(ValueError,match='overlap'):
        partition_owners([[(3,1)],[(3,2)],[(3,2)]],[42,43])
    with pytest.raises(ValueError,match='connected'):
        partition_owners([[(3,1),(3,3)],[(3,2)]],[42])


def test_oriented_manifold_control_checks_incidence_and_winding():
    # Boundary of an oriented tetrahedron; each edge appears once each way.
    edges={1:[1,2,-3],2:[3,4,-5],3:[-2,5,-6],4:[-1,6,-4]}
    assert check_manifold([1,2,3,4],edges)['curves']==6
    with pytest.raises(ValueError):check_manifold([1,2,3],edges)
    with pytest.raises(ValueError):check_manifold([-1,2,3,4],edges)


def test_saved_native_void_preserves_all_physical_bodies_and_interfaces():
    base=BASE/'phase_B';status=read(base/'status.json');p=read(base/'partition.json');g=read(base/'geometry.json')
    assert status['qualified'] and status['Boolean_calls']==1 and status['elapsed_seconds']<180
    assert status['native_solids']==219 and status['output_solids']==228
    assert status['external_hybrid_wires']=='OFF'
    assert len(set(p['owner'].values()))==219
    assert not p['unexpected_contacts_m2']
    assert max(abs(v) for v in p['source_volume_relative_errors'].values())<2e-7
    assert max(abs(v) for v in p['contact_relative_errors'].values())<1e-6
    assert g['volume_m3']+p['inside_solid_volume_m3']==pytest.approx(p['cylinder_volume_m3'],rel=2e-7)
    assert g['volume_m3']==pytest.approx(1.2531742112835103e-6,rel=1e-12)
    assert sha(base/'gas_only.brep')==g['BREP_sha256']
    assert g['topology']['all_incidence_two'] and g['topology']['all_oriented_sums_zero']
    faces=read(base/'gas_faces.json')
    assert len(faces)==g['face_count']==927
    for f in faces:
        assert f['body'] in set(p['owner'].values()) and f['area_m2']>0
        witness=f['normal_witness']
        assert witness['gas_inside'] and witness['solid_outside']
        assert np.linalg.norm(witness['outward_unit_normal'])==pytest.approx(1.,rel=1e-8)
        assert np.isfinite(witness['point_m']).all()
        assert (np.array(witness['point_m'])>=np.array(f['bbox_m'][:3])-1e-10).all()
        assert (np.array(witness['point_m'])<=np.array(f['bbox_m'][3:])+1e-10).all()
    r=read(base/'registration.json')
    assert r['code_sha256']==sha(ROOT/'tecooledmct/native_gas_csg.py')
    for name,digest in r['input_sha256'].items():assert sha(ROOT/name)==digest


def test_gas_uniform_and_analytic_slab_are_independent_exact_limits():
    c=analytic_controls()
    assert c['passed'] and c['uniform_max_W']==0.
    assert c['slab_exact_Q_w']==pytest.approx(.0259*1e-6*50/.001)
    assert c['slab_raw_relative_error']<1e-12
    assert c['work_W_K']==pytest.approx(c['dissipation_W_K'],rel=1e-12)


def test_passive_response_symmetry_positivity_and_uniform_nullspace():
    # Independent one-tet port response: K_ij from unit-temperature columns.
    p=np.array([[0.,0.,0.],[.001,0.,0.],[0.,.002,0.],[0.,0.,.003]])
    c=np.array([[0,1,2,3]]);f=np.array([[0,1,2],[0,1,3],[0,2,3],[1,2,3]])
    columns=[residual_and_flux(p,c,300.+np.eye(4)[j],f)[0] for j in range(4)]
    K=np.array(columns).T
    assert K==pytest.approx(K.T,abs=1e-16)
    assert K.sum(1)==pytest.approx(np.zeros(4),abs=1e-16)
    assert np.linalg.eigvalsh(K).min()>-1e-16
    T=np.array([300.,270.,285.,255.]);r,q,*_=residual_and_flux(p,c,T,f)
    assert r.sum()==pytest.approx(0.,abs=1e-15)
    assert q.sum()==pytest.approx(0.,abs=1e-15)
    assert (T-300.)@r>0


def test_analytic_wall_trace_compatibility_and_no_domain_clamping():
    z=np.array([[0.,0.,.0015],[0.,0.,.003545],[0.,0.,.00559]])
    assert profile(z,.00559)==pytest.approx([300.,275.,250.])
    for value in (.0014,.0057,float('nan')):
        with pytest.raises(ValueError):profile([[0.,0.,value]],.00559)
    assert all(reservoir(b) for b in (300,401,409,501,509,7301,7302,7303))
    assert not any(reservoir(b) for b in (1,2,3,4,174,184,303))


def test_actual_gas_field_retains_failed_raw_gate_separately_from_reactions():
    base=BASE/'phase_C';r=read(base/'result.json');m=np.load(base/'mesh.npz');f=np.load(base/'audited_field.npz')
    assert read(base/'solver_status.json')['returncode']==0
    assert read(base/'mesh_status.json')['mesh_attempts']==read(base/'PDE_registration.json')['PDE_solves']==1
    assert len(m['cells'])==r['tetrahedra']==228710<300000
    assert read(base/'mesh_audit.json')['all_elements_positive']
    assert read(base/'mesh_audit.json')['all_boundary_faces_owned_once']
    assert not r['registered_numerical_gates_passed'] and not r['gates']['raw_global_1percent']
    assert r['gates']['global_reaction_1nW'] and r['gates']['free_reaction_L1_1nW']
    raw=f['raw_face_power_W'];allocated=f['allocated_face_power_W']
    assert raw.sum()==pytest.approx(r['raw_outward_sum_W'],abs=1e-14)
    assert abs(raw.sum())/max(raw[raw>0].sum(),-raw[raw<0].sum())==pytest.approx(r['raw_global_relative_mismatch'])
    assert r['raw_global_relative_mismatch']==pytest.approx(.3262738922721323)
    assert allocated.sum()==pytest.approx(r['allocated_global_into_solid_W'],abs=1e-14)
    for b in r['bodies']:
        selected=m['solid_bodies']==b['body']
        assert raw[selected].sum()==pytest.approx(b['raw_out_of_gas_W'],abs=1e-14)
        assert allocated[selected].sum()==pytest.approx(b['allocated_reaction_into_solid_W'],abs=1e-14)
    assert sha(base/r['field_path'])==r['field_sha256']
    assert r['new_device_temperature'] is None and not r['physical_device_validation']
    assert r['regime']['interleg_continuum_screen_Kn_below_001'] and r['regime']['nominal_cavity_buoyancy_flag']
    assert r['temperature_min_K']>=250-1e-6 and r['temperature_max_K']<=300+1e-6
    assert read(base/'controls.json')['source_sha256']==sha(ROOT/'tecooledmct/native_gas_conduction.py')


def test_actual_mesh_figure_provenance_and_new_checkpoint_identities():
    fig=read(BASE/'figure_provenance.json')
    assert not fig['registered_raw_gate_passed']
    assert fig['source_sha256']==sha(ROOT/'tecooledmct/native_gas_figures.py')
    assert fig['figure_sha256']==sha(BASE/'native_gas_control.png')
    for name,digest in fig['input_sha256'].items():assert sha(ROOT/name)==digest
    for name,digest in read(BASE/'checksums.json')['artifact_sha256'].items():assert sha(BASE/name)==digest
