"""Guard the saved correction of external cavity source-face indexing."""
from pathlib import Path
import json,pytest
R=Path(__file__).resolve().parents[1]
def test_corrected_external_reference_matches_archived_source_and_old_is_distinct():
 d=R/'data/tec_height_coupling_20261110'
 corrected=json.loads((d/'external_gap_fixed_field_corrected.json').read_text())
 old=json.loads((d/'external_gap_fixed_field_sensitivity.json').read_text())
 source=json.loads((R/'data/v3_11_rev3_backfill_source_20261109/Kr100_I040/result.json').read_text())
 v=corrected['gaps'][1]['gas_by_surface_W'];expected=source['cavity_gas_heat_into_three_ceramics_and_die_W']
 assert corrected['gaps'][1]['external_gap_m']==.003 and v==pytest.approx(expected,abs=1e-14)
 assert abs(old['gaps'][1]['total_gas_W']-sum(expected))>1e-6
 marker=json.loads((d/'external_gap_index_correction.json').read_text())
 assert marker['status'].startswith('SUPERSEDED')
