"""V3.16 exact-solution interface and finite-patch evidence release checks."""
from pathlib import Path
import json,hashlib,math
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_16_contact_method_benchmark_20261110'
R=ROOT/'reports/current'

def record():return json.loads((D/'benchmark_results.json').read_text())
def test_fixed_test_set_and_smooth_manufactured_exactness():
    d=record()
    assert d['benchmark_only_no_source_3D_qualification'] is True
    assert d['predefined_cases']==[[8,False],[16,False],[8,True],[16,True],[24,True]]
    smooth=[x for x in d['results'] if not x['finite_contact_patch']]
    assert len(smooth)==2
    for x in smooth:
        assert x['max_potential_vs_exact']<1e-8
        assert max(x['raw_vs_contact_abs_relative'].values())<1e-8
        assert max(x['raw_flux_error_vs_smooth_exact_normalized'].values())<1e-8

def test_finite_patch_is_not_a_false_analytical_accuracy_claim():
    d=record();p=[x for x in d['results'] if x['finite_contact_patch']]
    assert [x['n'] for x in p]==[8,16,24]
    assert [x['dofs'] for x in p]==[578,2178,4802]
    assert [x['interface_segments'] for x in p]==[4,8,12]
    assert all(x['max_potential_vs_exact'] is None for x in p)
    assert all(x['raw_flux_error_vs_smooth_exact_normalized'] is None for x in p)
    assert all(x['raw_vs_contact_abs_relative']['right']>.001 for x in p)
    assert p[0]['raw_vs_contact_abs_relative']['right']>p[1]['raw_vs_contact_abs_relative']['right']>p[2]['raw_vs_contact_abs_relative']['right']
    assert 0.04<p[-1]['raw_vs_contact_abs_relative']['right']<0.05

def test_energy_and_residual_closure():
    d=record()
    for x in d['results']:
        assert x['free_equation_residual']<1e-8
        assert x['relative_power_identity_error']<1e-10
        assert x['numerical_bulk_power']>0 and x['numerical_contact_power']>0

def test_original_fail_stop_remains_and_figure_sha():
    d=record()
    assert d['source_3D_electrical_gate_B'].startswith('FAIL/STOP')
    assert d['source_3D_thermal_gate_C']=='NOT RUN'
    assert d['source_3D_Joule_gate_D']=='NOT RUN'
    for name,digest in d['figure_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest

def test_cumulative_retains_previous_report_and_all_sections():
    s=(R/'reader_first_report.tex').read_text()
    assert s.count('\\input{v316_contact_method_section.tex}')==1
    assert s.count('\\input{v315_contact_perimeter_section.tex}')==1
    assert s.count('\\appendix')==1
    assert (R/'TEC_TO_Reader_First_Assessment_20261110_V316.pdf').is_file()
    assert (R/'TEC_TO_Reader_First_Assessment_20261110_V315.pdf').is_file()
    content=(R/'v316_contact_method_section.tex').read_text()
    assert 'FAIL/STOP' in content and 'NOT RUN' in content
