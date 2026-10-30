"""Immutable spatial diagnostics and manufactured evidence retain failed gates."""
import hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'fem/results/bath_spatial_diagnosis_20261030'
def test_spatial_archive_preserves_diagnostic_scope_and_approved_report():
    if not DEST.exists():pytest.skip('Spatial archive not published yet')
    d=json.loads((DEST/'checksums.json').read_text())
    for group,base in [('sources',ROOT),('artifacts',DEST)]:
        for name,digest in d[group].items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,name
    q=json.loads((DEST/'qualification.json').read_text());assert q['manufactured_operator_target_passed'] and not q['device_qualified'] and not q['full_device_GCI']
    s=json.loads((DEST/'audit/summary.json').read_text());assert len(s['cases'])==4
    for case in s['cases']:
        assert abs(case['raw_relative_error'])>.01
        assert abs(case['identity']['closure_error_W'])<1e-10
        assert not case['local_physical_error_known'] and not case['qualified_recovery']
    for label in ['transverse1','transverse2']:
        a=json.loads((DEST/'geometry'/label/'audit.json').read_text());assert a['passed'] and all(a['fixed_cell_sets_byte_identical'].values())
    b=json.loads((DEST/'benchmark/summary.json').read_text());assert b['benchmark_qualified'] and not b['device_qualified']
    assert not b['cases'][1]['raw_1percent_passed'] and b['cases'][3]['raw_1percent_passed']
    assert hashlib.sha256((ROOT/'reports/rev3_review/editions/20261030_b/report.pdf').read_bytes()).hexdigest()=='d173a8ba952462e1b6bf857739406f58eeb8d5c82b900f9fc65b84d40573acc1'
