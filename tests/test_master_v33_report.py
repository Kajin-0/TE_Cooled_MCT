"""Frozen-data checks for the Rev3 V3.3 report; no physics solve."""
import json
import numpy as np
from reports.master.history import ROOT,sha
RUN=ROOT/'data/v3_3_cavity_package_feedback_20261108/attempt02'
def load(path):return json.loads(path.read_text())

def test_archived_v33_sources_and_original_mesh_mapping():
    manifest=load(RUN.parent/'manifest.json');reg=load(RUN/'registration.json')
    for name,h in manifest['attempt02_evidence_SHA256'].items():assert sha(RUN/name)==h
    meta=load(ROOT/'reports/master/inputs/v33_ceramic_connectivity.json')
    assert meta['source_mesh_sha256']==reg['original_mesh_SHA256']
    assert meta['coordinates_verified_against_original_node_file']
    fields=np.load(RUN/'source_native_ceramics_V3_3.npz');mesh=np.load(ROOT/'reports/master/inputs/v33_ceramic_connectivity.npz')
    for i,count in enumerate((4936,4085,1986,784)):
        tet=mesh[f'ceramic{i}_tetrahedra_local'];xyz=fields[f'ceramic{i}_xyz_mm'];temp=fields[f'ceramic{i}_temperature_K']
        assert tet.shape==(count,4) and tet.min()>=0 and tet.max()<len(xyz)==len(temp)
        assert np.isfinite(temp).all() and len(np.unique(fields[f'ceramic{i}_source_node_id_1based']))==len(xyz)

def test_all_legs_stage_budgets_and_cavity_closure():
    d=load(RUN/'result.json');a=load(RUN/'independent_read_only_acceptance.json');legs=d['source_individual_leg_flux_and_electric_results']
    assert len(legs)==88 and d['source_stage_couples']==[29,11,4] and a['numerical_accepted']
    for i,stage in enumerate(d['source_stage_thermoelectric_budget']):
        group=[z for z in legs if z['stage']==i];assert len(group)==stage['nlegs']==[58,22,8][i]
        for leg_key,stage_key in [('Qcold_W','qc_w'),('Qhot_W','qh_w'),('terminal_contribution_V','voltage_v')]:
            assert abs(sum(z[leg_key] for z in group)-stage[stage_key])<1e-10
    heat=sum(d['cavity_gas_heat_into_three_ceramics_and_die_W'])+sum(d['gray_radiation_heat_into_three_ceramics_and_die_W'])
    assert abs(heat-d['total_enclosure_heat_into_cold_device_W'])<1e-14
    assert abs(heat+d['enclosure_reservoir_heat_rejected_W'])<1e-14
    assert abs(d['electrical_power_W']-d['operating_current_A']*d['terminal_voltage_V'])<1e-14
    assert abs(d['global_thermoelectric_energy_residual_W'])<1e-8
    assert d['outer_iterations']==len(d['spatial_outer_iteration_history'])==5
    assert d['max_last_spatial_temperature_update_K']<2e-5
    assert a['max_saved_original_face_heat_vs_last_leg_model_discrepancy_W']>2.5e-8

def test_previous_master_exact_bytes_sealed():
    p=ROOT/'reports/historical/rev3_pre_v33_20261108';d=load(p/'historical_identity.json')
    assert d['pages']==38 and d['pdf_sha256']=='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
    for name,h in d['files_sha256'].items():assert sha(p/name)==h
