"""Independent unit/scale/regime controls for a stopped native gas audit."""
import numpy as np
import pytest

from tecooledmct.native_gas_audit import ROOT,NOTE,step_units,interleg_gaps,regime,gate,read,sha


def test_declared_STEP_mm_is_physical_mm_not_metres():
    text="( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) );\nCYLINDRICAL_SURFACE('',#1,7.6E-03);"
    x=step_units(text)
    assert x['metres_per_coordinate_unit']==.001
    assert x['cylinder_radii_declared_m']==pytest.approx([7.6e-6],rel=1e-14)
    assert step_units(text.replace('.MILLI.','$'))['cylinder_radii_declared_m']==pytest.approx([.0076])


@pytest.mark.parametrize('text',["",'( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.UNKNOWN.,.METRE.) );',
    '( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) ); ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT($,.METRE.) );'])
def test_ambiguous_or_unknown_units_fail_closed(text):
    with pytest.raises(ValueError):step_units(text)


def test_volume_scaling_uses_cubic_not_linear_unit_factor():
    expected={'a':1.,'b':2.,'c':3.}
    good=gate(expected,[{'volume_m3':x} for x in (1.,2.,3.)],True)
    bad=gate(expected,[{'volume_m3':x*1e-9} for x in (1.,2.,3.)],True)
    assert good['source_units_admissible']
    assert not bad['source_units_admissible']
    assert bad['cap_import_to_SI_registry_volume_ratios']==pytest.approx([1e-9]*3)
    assert bad['gas_PDE_solves']==0 and bad['gas_cells']==0


def test_actual_interleg_scale_is_independent_of_temperature_or_pressure():
    m=read(ROOT/'fem/results/geometry_complete_checkpoint_20261030/manifest.json')
    rows=interleg_gaps(m)
    assert [r['legs'] for r in rows]==[56,24,8]
    assert [r['minimum_xy_surface_gap_m'] for r in rows]==pytest.approx([.00015]*3,abs=1e-14)


def test_conditional_N2_Kn_and_Ra_pressure_scaling():
    a=regime(.00015,.00815,100.);b=regime(.00015,.00815,101325.)
    assert a['Kn_interleg']/b['Kn_interleg']==pytest.approx(1013.25)
    assert b['Ra_nominal_cavity_height']/a['Ra_nominal_cavity_height']==pytest.approx(1013.25**2)
    assert not a['interleg_continuum_screen_Kn_below_001']
    assert b['interleg_continuum_screen_Kn_below_001'] and b['nominal_cavity_buoyancy_flag']
    assert b['Ra_interleg']<1
    assert a['k_w_mk']==b['k_w_mk']==.0259


@pytest.mark.parametrize('kwargs',[{'gap':0.},{'pressure':0.},{'pressure':-1.},{'temperature':199.},
                                  {'temperature':401.},{'contrast':float('nan')}])
def test_invalid_or_unsourced_regime_arguments_reject(kwargs):
    args={'gap':.00015,'height':.00815,'pressure':101325.};args.update(kwargs)
    with pytest.raises(ValueError):regime(**args)


def test_saved_unit_aware_reader_control_and_scientific_stop():
    folder=ROOT/'data/native_gas_domain_audit_20261101';r=read(folder/'audit.json')
    assert r['registration']==NOTE.read_text().split('## Results')[0]
    for group in ('source_sha256','input_sha256'):
        for name,h in r[group].items():assert sha(ROOT/name)==h
    for name,h in read(folder/'checksums.json')['artifact_sha256'].items():assert sha(folder/name)==h
    assert r['analytic_cube']['passed'] and r['reader_target_unit']=='M'
    assert r['analytic_cube']['actual'][0]['volume_m3']==pytest.approx(1e-9,rel=1e-8)
    assert r['package_CAD']['volumes']==216 and r['package_CAD']['SI_source_volumes_consistent']
    assert r['native_counts']['legs']==88 and r['native_counts']['pins']==9
    assert r['native_cap_mesh']['tetrahedra']==8143
    assert r['cap_STEP_to_intended_length_ratio']==pytest.approx(.001)
    assert r['decision']['cap_import_to_SI_registry_volume_ratios']==pytest.approx([1e-9]*3,rel=1e-7)
    assert r['as_imported_cap_inside_Kovar_core']
    assert r['cap_import_bbox_m']['high'][2]<r['header_top_m']
    assert not r['decision']['source_units_admissible']
    assert r['decision']['Boolean_void_extractions']==r['decision']['gas_PDE_solves']==0
    assert all(x is None for x in r['gas_domain_checks'].values())
    assert r['gas_heat_budgets_w'] is None and r['gas_temperature_field'] is None
    assert r['selected_operating_pressure_pa'] is None
    assert not r['Rev3_modified'] and r['original_solid_stops_and_raw_release_failures_retained']
