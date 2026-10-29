"""Guard the reader matrix against promoting rejected fine solutions."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('report_verification', Path(__file__).with_name('verification.py'))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


def test_matrix_preserves_archived_coarse_and_fine_verdicts():
    summary = json.loads((ROOT / 'fem/results/g3b_checkpoint_20261029/charts/summary.json').read_text())
    registry = json.loads((ROOT / 'data/g3b/enclosure_registry.json').read_text())
    rows = _module.verification_matrix(summary, {'passed': True}, registry['numerical_limits'])
    by_test = {row['test']: row for row in rows}
    assert by_test['Coarse bath gradient']['status'] == 'PASS'
    assert by_test['Fine bath gradient']['status'] == 'FAIL'
    assert by_test['Fine-mesh qualification']['status'] == 'NOT QUALIFIED'
    assert by_test['Manufacturer / device accuracy']['status'] == 'NOT QUALIFIED'
    assert all(row['source'] for row in rows)
