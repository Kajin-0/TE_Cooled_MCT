"""Independent rejection of the quarantined authoring attempt; no re-export."""
import numpy as np
import pytest

from tecooledmct.cap_export_validation import classify_physical_scale,ROOT,NOTE,read,sha
from tecooledmct.native_gas_audit import step_units


@pytest.mark.parametrize('scale,accepted',[(1.,True),(1e-9,False),(1e9,False)])
def test_physical_volume_scale_rejection_is_bidirectional(scale,accepted):
    expected={'shell':2.,'roof':3.,'window':5.}
    rows=[{'volume_m3':v*scale} for v in (2.,3.,5.)]
    r=classify_physical_scale(rows,expected)
    assert r['physical_scale_qualified'] is accepted
    assert r['length_ratios_from_volumes']==pytest.approx([np.cbrt(scale)]*3)


@pytest.mark.parametrize('values',[[1.,2.],[1.,2.,3.,4.],[1.,2.,-3.],[1.,2.,float('nan')]])
def test_missing_extra_nonphysical_imports_reject(values):
    with pytest.raises(ValueError):classify_physical_scale([{'volume_m3':v} for v in values],{'a':1.,'b':2.,'c':3.})


def test_nonuniform_geometric_change_is_distinct_from_uniform_unit_error():
    r=classify_physical_scale([{'volume_m3':v} for v in (1.,4.,9.)],{'a':1.,'b':2.,'c':3.})
    assert not r['uniform_scale_error'] and not r['physical_scale_qualified']


def test_saved_failed_export_is_quarantined_and_rejected_in_physical_metres():
    base=ROOT/'data/unit_correct_cap_native_gas_20261101';a=read(base/'phase_A_validation.json')
    failed=base/'unaccepted_phase_A_attempt'
    assert a['registration']==NOTE.read_text().split('## Results')[0]
    for group in ('source_sha256','input_sha256'):
        for name,h in a[group].items():assert sha(ROOT/name)==h
    for name,h in read(base/'checksums.json')['artifact_sha256'].items():assert sha(base/name)==h
    assert sha(failed/'author.py.snapshot')==a['failed_author_snapshot_sha256']
    assert sha(failed/'cap_window_unit_correct.step')==a['candidate_STEP_sha256']
    parsed=step_units((failed/'cap_window_unit_correct.step').read_text())
    assert max(parsed['cylinder_radii_declared_m'])==pytest.approx(7.6)
    assert a['outer_radius_ratio_to_intended']==pytest.approx(1000.)
    assert a['scale_check']['volume_ratios_to_intended']==pytest.approx([1e9]*3,rel=1e-8)
    assert a['cube_control']['imported'][0]['volume_m3']==pytest.approx(1e-9,rel=1e-8)
    assert not a['phase_A_qualified'] and not a['valid_derivative_published']
    assert a['geometry_authoring_attempts']==1 and a['additional_exports_in_validation']==0
    assert a['phase_B']['Boolean_void_extractions']==0 and a['phase_C']['gas_PDE_solves']==0
    assert a['phase_B']['boundary_qualification'] is None and a['phase_C']['gas_heat_budgets_w'] is None
    assert not a['source_geometry_or_laws_changed'] and not a['Rev3_modified']
    assert not (ROOT/'tecooledmct/cap_unit_derivative.py').exists()


def test_scale_diagram_is_traceable_geometry_evidence_not_a_field():
    base=ROOT/'data/unit_correct_cap_native_gas_20261101';r=read(base/'figure_provenance.json')
    assert r['source_sha256']==sha(ROOT/'tecooledmct/cap_export_figures.py')
    assert r['figure_sha256']==sha(base/'physical_scale_failure.png')
    for name,h in r['input_sha256'].items():
        path=base/name if (base/name).exists() else ROOT/name
        assert sha(path)==h
    assert r['radii_m']==pytest.approx([7.6e-6,.0076,7.6])
