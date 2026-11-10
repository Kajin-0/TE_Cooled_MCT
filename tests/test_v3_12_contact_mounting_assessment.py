"""Read-only V3.12 engineering-data and report reproduction gates.

No solver or simulation is executed by these tests.
"""
from pathlib import Path
import hashlib,json,math

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/v3_12_contact_mounting_assessment_20261109/assessment.json'

def record():return json.loads(P.read_text())

def test_input_integrity_and_figures():
    d=record()
    assert len(d['input_hashes_sha256'])>=19
    for name,digest in d['input_hashes_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    assert len(d['output_plot_sha256'])==4
    for name,digest in d['output_plot_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name

def test_source_copper_network_energy_and_port_topology():
    d=record();q=d['source_component_budget']
    assert math.isclose(q['Cu_into_hot_ceramic_mW']+q['Cu_into_middle_ceramic_mW']+
        q['Cu_into_upper_ceramic_mW'],q['Cu_total_Joule_mW'],abs_tol=1e-9)
    assert math.isclose(q['Cu_net_80_upper_mW']+q['Cu_net_88_upper_mW'],
        q['Cu_into_upper_ceramic_mW'],abs_tol=1e-9)
    assert math.isclose(q['pin1_into_ceramic_mW']+q['pin9_into_ceramic_mW'],
        q['two_leads_net_into_ceramic_mW'],abs_tol=1e-9)
    assert math.isclose(q['TEC_input_W'],.5956680349614825,abs_tol=1e-10)
    assert d['Cu_foil_cross_section_m2']==9e-9

def test_bulk_bondline_geometry_and_monotone_fixed_face_effect():
    d=record();rows=d['fixed_ceramic_face_hypotheses'];assert len(rows)==6
    for alloy,k in [('Sn95Sb5',28),('SAC305 counterfactual',61)]:
        a=[r for r in rows if r['alloy']==alloy]
        assert [r['assumed_bondline_thickness_um'] for r in a]==[20,25,35]
        assert all(math.isclose(r['bulk_only_Rarea_m2K_W'],
            r['assumed_bondline_thickness_um']*1e-6/k,rel_tol=1e-13) for r in a)
        assert a[0]['fixed_field_upper_Cu_heat_mW']>a[1]['fixed_field_upper_Cu_heat_mW']>a[2]['fixed_field_upper_Cu_heat_mW']
    assert d['joint_nominal_equivalent_SnSb_bulk_thickness_um']==28.0
    assert d['joint_high_hypothesis_equivalent_SnSb_bulk_thickness_um']==2800.0

def test_mounting_matches_previous_fully_coupled_archives():
    d=record();a=d['accepted_mounting_cases']
    assert len(a)==5
    assert a[1]['detector_T_K']>a[0]['detector_T_K']
    assert a[2]['detector_T_K']>a[1]['detector_T_K']
    assert 8.8<a[3]['extra_power_vs_baseline_percent']<8.9
    assert 19.5<a[4]['extra_power_vs_baseline_percent']<19.7
    assert abs(a[4]['detector_T_K']-a[0]['detector_T_K'])<.032

def test_additive_report_no_replaced_original_evidence():
    s=(ROOT/'reports/current/cumulative_report.tex').read_text()
    a=(ROOT/'reports/current/v312_contact_mounting_section.tex').read_text()
    assert s.count('\\input{v312_contact_mounting_section.tex}')==1
    assert s.index('\\input{v312_contact_mounting_section.tex}')<s.index('\\section{Original V3.4 copper-bridge result')
    assert 'v312_source_copper_heat_ledger' in a
    assert 'v312_solder_contact_fixed_field_screen' in a
    assert (ROOT/'reports/current/TEC_HgCdTe_Cumulative_TEC_TO_20261109_Plot_QA_Rev3.pdf').is_file()
