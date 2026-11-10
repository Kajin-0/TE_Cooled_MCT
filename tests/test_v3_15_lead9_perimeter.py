"""V3.15 saved-field decomposition verification, no PDE and no new mesh."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
O=ROOT/'data/v3_15_lead9_perimeter_20261110'
R=ROOT/'reports/current'

def load(p):return json.loads(p.read_text())
def test_original_source_and_figure_provenance():
    d=load(O/'comparison.json')
    for key,digest in d['input_SHA256'].items():assert hashlib.sha256((ROOT/key).read_bytes()).hexdigest()==digest
    for key,digest in d['figure_SHA256'].items():assert hashlib.sha256((ROOT/key).read_bytes()).hexdigest()==digest

def test_perimeter_concentration_from_actual_saved_fields():
    d=load(O/'comparison.json')
    assert d['gate_B']=='FAIL/STOP' and d['gate_C_D']=='NOT RUN'
    for key in ('lead_land','lead_pin'):
        prior,finer=d['interfaces'][key]
        assert prior['mesh']=='prior P2' and finer['mesh']=='refined P2'
        assert 18<prior['solder_side_rim_area_share_pct']<22
        assert 18<finer['solder_side_rim_area_share_pct']<22
        assert finer['solder_side_rim_abs_mismatch_share_pct']>prior['solder_side_rim_abs_mismatch_share_pct']>70
        assert finer['P2_raw_current_gate_error_pct']<prior['P2_raw_current_gate_error_pct']
        assert finer['counterfactual_no_rim_max_of_sides_pct']>.1
    assert math.isclose(d['interfaces']['lead_land'][1]['counterfactual_no_rim_max_of_sides_pct'],2.123,rel_tol=0.001)
    assert math.isclose(d['interfaces']['lead_pin'][1]['counterfactual_no_rim_max_of_sides_pct'],1.304,rel_tol=0.001)

def test_independent_3d_contact_field_reconstruction():
    receipt=load(ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/v315_perimeter_readback.json')
    assert receipt['no_PDE_or_mesh_changes'] is True
    assert receipt['independent_original_current_integrals_reproduced'] is True
    for key,expected in [('lead_land',180),('lead_pin',176)]:
        x=receipt['lead_interfaces'][key]
        assert x['source_registered_triangles']==expected
        assert len(x['contact_operator_consistency']['radial_triangle_centroid_bins'])==4
        assert math.isclose(sum(b['area_fraction'] for b in x['contact_operator_consistency']['radial_triangle_centroid_bins']),1,rel_tol=1e-12)
    for key,digest in receipt['input_sha256'].items():assert hashlib.sha256((ROOT/key).read_bytes()).hexdigest()==digest

def test_cumulative_addition_and_previous_report_preservation():
    s=(R/'reader_first_report.tex').read_text()
    assert s.count('\\input{v315_contact_perimeter_section.tex}')==1
    assert s.count('\\appendix')==1
    assert (R/'TEC_TO_Reader_First_Assessment_20261110_V315.pdf').is_file()
    assert (R/'TEC_TO_Reader_First_Assessment_20261109_V314.pdf').is_file()
    a=(R/'v315_contact_perimeter_section.tex').read_text()
    assert 'FAIL/STOP' in a and 'NOT RUN' in a
