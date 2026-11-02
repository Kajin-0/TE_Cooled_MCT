"""Frozen failed-field diagnostics; do not execute or repair the producer."""
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]/'data/v3_conservative_flux_20261102'

def test_preserved_producer_failure_stops_after_one_mesh():
    import numpy as np
    execution=json.loads((BASE/'execution.json').read_text())
    assert execution[0]['gate']['status']=='PASS'
    assert execution[1]['exit_code']==1
    assert 'KeyError' in (BASE/'geometry.log').read_text()
    assert 'mixed' in (BASE/'geometry.log').read_text()
    assert json.loads((BASE/'geometry/L1/fidelity.json').read_text())['status']=='PASS'
    assert not (BASE/'geometry/L2').exists()
    assert set(json.loads((BASE/'geometry/L1_field/alternative.json').read_text()))=={'lead9'}
    # CF-03: only the first, mixed iteration writes this surviving array.
    with np.load(BASE/'geometry/L1_field/fields.npz') as fields:
        assert 'mixed_q' not in fields and 'recovered_q' not in fields
        assert fields['lead9_cell_V'].shape==(207396,)
        assert fields['lead9_cell_V'].min() < -1e-8
        assert abs(float(fields['lead9_cell_V'].min())+2.652280857949769e-5)<1e-12

def test_independent_loss_audit_rejects_conservation_only_qualification():
    a=json.loads((BASE/'saved_audit.json').read_text())
    r=json.loads((BASE/'registration.json').read_text())
    assert a['all_element_face_normal_error_relative']<1e-9
    assert a['independent_terminal_relative_error']<1e-9
    assert a['independent_IV_loss_relative_error']>r['IV_loss_relative_limit']
    assert a['recovered_field_J_reconstruction_relative']<1e-7
    assert a['P1_cofactor_J_reconstruction_relative']<1e-7
