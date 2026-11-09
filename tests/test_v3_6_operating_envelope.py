"""V3.6 operating-envelope regression: actual full-system accepted results, not mock numbers."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_6_operating_envelope_20261109'
CASES=['I025_Q002_corrected','I040_Q002','I055_Q002_corrected','I060_Q002_corrected','I040_Q001','I040_Q006']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def loaded(name):
    p=D/name
    return (json.loads((p/'registration.json').read_text()),
            json.loads((p/'result.json').read_text()),
            json.loads((p/'independent_energy_audit.json').read_text()))
def test_original_reference_frozen_and_exactly_reproduced():
    prev=ROOT/'data/v3_5_power_lead_and_copper_sensitivity_20261108/copper_native_pad/result.json'
    assert sha(prev)=='8a47c9a18a5e6a79b30b7bfa81cdfc05e7cfe2ba6d3b6aac8fcd1054b1c966a6'
    original=json.loads(prev.read_text())
    r,d,a=loaded('I040_Q002')
    for k in ('calculated_detector_temperature_K','terminal_voltage_V','electrical_power_W','bath_heat_rejected_W',
              'outer_iterations','global_thermoelectric_energy_residual_W','max_last_spatial_temperature_update_K'):
        assert d[k]==original[k],k
    assert r['current_A']==.4 and r['detector_heat_W']==.002
def test_all_six_scenarios_independently_accepted():
    for case in CASES:
        r,d,a=loaded(case)
        assert d['status'].startswith('V3.6 CONDITIONAL')
        assert a['verdict'].startswith('PASS V3.6')
        assert sha(D/case/'result.json')==a['result_sha256']
        assert sha(D/case/'registration.json')==a['registration_sha256']
        assert abs(a['global_energy_residual_W'])<1e-8
        assert a['max_stage_energy_residual_W']<1e-8
        assert d['max_native_plate_net_heat_imbalance_W']<5e-8
        assert d['max_last_spatial_temperature_update_K']<3e-7
        assert len(d['source_individual_leg_flux_and_electric_results'])==88
        assert d['original_ceramic_TET4']==11791
        assert r['current_A']==d['operating_current_A']
        assert r['detector_heat_W']==d['detector_imposed_heat_W']
        assert all(s['nlegs']==n for s,n in zip(d['source_stage_thermoelectric_budget'],(58,22,8)))
def test_current_envelope_is_monotone_over_observed_points_only():
    vals=[loaded(s)[1] for s in CASES[:4]]
    i=[v['operating_current_A'] for v in vals]
    t=[v['calculated_detector_temperature_K'] for v in vals]
    p=[v['electrical_power_W'] for v in vals]
    assert i==[.25,.4,.55,.6]
    assert all(b<a for a,b in zip(t,t[1:])),t
    assert all(b>a for a,b in zip(p,p[1:])),p
    # Does not establish a global optimal operating current.
def test_thermal_load_cases_and_sensitivity():
    vals=[loaded(n)[1] for n in ('I040_Q001','I040_Q002','I040_Q006')]
    assert [v['detector_imposed_heat_W'] for v in vals]==[.001,.002,.006]
    T=[v['calculated_detector_temperature_K'] for v in vals]
    assert T[0]<T[1]<T[2]
    slope=(T[2]-T[0])/.005
    assert 250<slope<400,slope # K/W, intentionally wide diagnostic gate
def test_attempt01_failure_preserved_and_current_warmstart_is_corrected():
    src=D/'attempt01_initial_warm_start_source.py'
    assert sha(src)=='08b0d21fd16038e24b3a7b7c4e20e329811e1d13d0f29cdb6ff8fd4748b7bd58'
    assert sha(ROOT/'scripts/v3_6_current_heatload_envelope.py')!=sha(src)
    for name in ('I025_Q002','I055_Q002'):
        fail=(D/name/'run.log').read_text()
        assert 'CERAMIC_NET_FLUX_MISMATCH' in fail
        assert not (D/name/'result.json').exists()
    fixed=(ROOT/'scripts/v3_6_current_heatload_envelope.py').read_text()
    assert 'warm_start_I=0.4' in fixed
    assert 'plus_solder_into_ceramic(init_rows,warm_start_I**2*R_joint)' in fixed
def test_source_identity_and_original_historical_reports_preserved():
    assert sha(ROOT/'scripts/v3_5_power_lead_and_copper_sensitivity.py')=='669f713e9e5be6a2df88f6f8fd6b43a42846db463c0c375a62fd5f679ee556e9'
    assert sha(ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json')=='023d8b26931fcb758d379a4150470305f4f613bf3543aae3065a98bc5be762c8'
    assert sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf')=='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
if __name__=='__main__':
    for name,f in sorted(globals().items()):
        if name.startswith('test_') and callable(f):
            f();print(name,'PASS')
