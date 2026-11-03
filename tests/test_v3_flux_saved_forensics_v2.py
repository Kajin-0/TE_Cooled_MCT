"""Tests only saved forensics, with no solver or mesh."""
import json
from pathlib import Path


def test_exact_saved_witnesses():
    path = Path("data/v3_flux_forensics_20261103/saved_diagnostics.json")
    assert path.is_file()
    record = json.loads(path.read_text())
    v = record["mixed_voltage_min"]
    assert v["region"] == "pin_finish"
    assert v["tetra_index"] == 203784
    assert v["cells_below_registered_floor"] == 501
    assert abs(v["V"] + 2.652280857949769e-5) < 1e-12
    assert not record["actual_methods_retained"]["direct_mixed_RT0_flux"]
    loss = record["recovered_loss"]
    assert abs(loss["relative_discrepancy"] - 0.0076915363179273) < 1e-10
    assert abs(loss["bulk_W"] - 32.13642611005566) < 1e-9
    assert abs(loss["contact_W"] - 2.1303697966917508) < 1e-9
    assert loss["recovered_J_centroid_reconstruction_relative"] < 1e-8
