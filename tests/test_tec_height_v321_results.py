"""Check archived paired outputs without running the coupled model."""
from pathlib import Path
import hashlib
import json
import pytest
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/tec_height_robustness_20261110'

def load(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def test_registered_inputs_still_identical():
    contract = load(DATA / 'contract.json')
    for name, digest in contract['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    assert contract['max_full_system_solves'] == 6

def test_summary_only_counts_audited_complete_pairs():
    s = load(DATA / 'summary.json')
    assert s['new_full_system_solves_with_audit'] == 2 * s['new_paired_scenarios'] <= 6
    assert s['pairs'][0]['new_solves'] == 0
    for p in s['pairs']:
        assert p['delta_die_K'] == pytest.approx(p['custom_060']['die_K'] - p['nominal']['die_K'])
        assert p['delta_top_K'] == pytest.approx(p['custom_060']['top_K'] - p['nominal']['top_K'])
        for key in ('nominal', 'custom_060'):
            r = p[key]
            assert abs(r['power_W'] - s['power_target_W']) < 1e-8
            assert abs(r['global_residual_W']) < 1e-8
            assert abs(r['stage_residual_W']) < 1e-8
            if p['new_solves']:
                d = DATA/'cases'/p['scenario']/key
                for audit in ('independent_audit.json', 'ports_crosscheck.json'):
                    a = load(d/audit)
                    assert a['status'].startswith('PASS')
                    assert sha(d/'result.json') in (a.get('result_sha256'),a.get('source_result_sha256'))

def test_fixed_field_copper_is_only_fixed_field():
    a = load(DATA/'copper_fixed_independent_audit.json')
    assert a['status'].startswith('PASS') and 'fixed temperature only' in a['status']
    assert len(a['checks']) == 6
    assert all(abs(x['max_stage_diff_W']) < 1e-12 for x in a['checks'])
