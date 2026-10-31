"""Seven-port trace admissibility and independent analytic negative controls."""
import copy

import numpy as np
import pytest

from tecooledmct.passive_plate_audit import (ROOT,NOTE,PORTS,selection,port_for,
    trace_collisions,decision,wedge_energy,read,sha)


def test_selection_includes_all_four_plates_and_original_Cu_terminals():
    by,selected=selection(read(ROOT/'fem/results/geometry_complete_checkpoint_20261030/manifest.json'))
    assert len(selected)==104
    assert {1,2,3,4,116,117,165,166,182,183}.issubset(selected)
    assert len([b for b in selected if by[b]['kind']=='bridge'])==85
    assert len([b for b in selected if by[b]['kind']=='terminal'])==6
    assert not any(by[b]['kind']=='leg' for b in selected)


def test_independent_port_constants_conflict_on_a_shared_edge():
    p=np.array([[0.,0.,0.],[0.,1.,0.],[1.,0.,0.],[0.,0.,1.]])
    f=np.array([[0,1,2],[0,1,3]]);labels=np.array([0,1])
    rows,edges=trace_collisions(p,f,labels)
    assert len(rows)==1 and rows[0]['shared_edge_length_m']==pytest.approx(1.)
    assert not rows[0]['independent_unit_values_compatible']
    assert np.array_equal(edges,[[0,1]])
    assert not decision([],rows)['seven_port_admissible']


def test_disjoint_ports_pass_geometry_gate_without_claiming_a_solve():
    p=np.array([[0.,0.,0.],[0.,1.,0.],[1.,0.,0.],[0.,0.,1.],[0.,1.,1.],[1.,0.,1.]])
    rows,edges=trace_collisions(p,np.array([[0,1,2],[3,4,5]]),np.array([0,1]))
    result=decision([],rows)
    assert result['seven_port_admissible'] and not len(edges)
    assert not result['operator_built'] and result['passive_unit_solves_executed']==0


def test_unmapped_physical_contact_stops_even_with_disjoint_ports():
    result=decision([{'area_m2':1.}],[])
    assert not result['seven_port_admissible']
    assert result['stop_reasons']==['Unregistered physical cut interfaces']
    assert not result['extra_boundary_conditions_added']


def test_analytic_wedge_energy_exposes_cutoff_dependence_and_entropy_sign():
    # Exact solution T=300+theta/pi in a homogeneous extruded wedge.
    a=wedge_energy(2.,3.,np.pi,1.,.1,1.)
    b=wedge_energy(2.,3.,np.pi,1.,.01,1.)
    assert a==pytest.approx(6*np.log(10)/np.pi)
    assert b==pytest.approx(2*a)
    assert wedge_energy(2.,3.,np.pi,-1.,.1,1.)==pytest.approx(a)
    assert wedge_energy(2.,3.,np.pi,0.,.1,1.)==0
    # Entropy integral is bounded by D/Tmax² and D/Tmin², both positive.
    assert 0<a/301**2<a/300**2


@pytest.mark.parametrize('args',[(0.,1.,1.,1.,.1,1.),(1.,1.,1.,1.,1.,.1),
                               (1.,1.,float('nan'),1.,.1,1.)])
def test_invalid_analytic_controls_reject(args):
    with pytest.raises(ValueError):wedge_energy(*args)


def test_leg_port_mapping_uses_actual_geometric_endpoint_and_rejects_side_guess():
    by={1:{'kind':'leg','stage':1,'boxes_m':[[0,0,1,1,1,2]]},2:{'kind':'terminal'}}
    p=np.array([[[0.,0.,1.],[1.,0.,1.],[0.,1.,1.]]])
    assert port_for([1,2],by,{2},p)==2
    p[:,:,2]=3
    assert port_for([1,2],by,{2},p)==3
    p[:,:,2]=2
    with pytest.raises(ValueError):port_for([1,2],by,{2},p)


def test_saved_native_boundary_audit_preserves_honest_stop_and_identities():
    folder=ROOT/'data/passive_plate_port_audit_20261031';a=read(folder/'boundary_audit.json')
    assert a['registration']==NOTE.read_text().split('## Results')[0]
    for group in ('input_sha256','source_sha256'):
        for name,h in a[group].items():assert sha(ROOT/name)==h
    for name,h in read(folder/'checksums.json')['artifact_sha256'].items():assert sha(folder/name)==h
    assert a['two_sided_face_ownership_verified'] and a['native_body_and_contact_geometry_verified']
    assert len(a['selection'])==104 and a['source_materials']['Alumina']['k_w_mk']==30
    assert [(r['footprint_patches'],r['port']) for r in a['ports']]==list(zip([56,56,24,24,8,8,1],PORTS))
    assert a['grouping']['scalar_rank']==7
    assert a['grouping']['unrepresented_zero_group_mean_patch_modes']==170
    assert {tuple(r['bodies']) for r in a['unmapped_physical_interfaces']}=={(1,301),(4,302)}
    assert sum(r['shared_edge_length_m'] for r in a['trace_collisions'])==pytest.approx(.00022,abs=1e-12)
    assert sum(r['shared_edge_length_m'] for r in a['previous_isothermal_side_closure_native_edge'])==pytest.approx(.00022,abs=1e-12)
    assert not a['decision']['seven_port_admissible'] and not a['decision']['operator_built']
    assert a['decision']['passive_unit_solves_executed']==0
    assert not a['decision']['reference_temperature_fields_read']
    assert all(v is None for k,v in a['comparisons'].items() if k!='meaning')
    assert not a['new_numerical_release'] and not a['Rev3_modified']
    assert 'gas conduction' in a['next_science_priority']
