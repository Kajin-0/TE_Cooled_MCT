import pytest
from tecooledmct.materials import (
    MATERIALS, P_BI_TE, N_BI_TE, ALUMINA_96, ALUMINA_HIGH_PURITY,
    KOVAR, GOLD_WIRE_4N,SN_SB_95_5, layer_temperature_drop,
)
from tecooledmct.material_transport import literature_stage_coefficients,compare_coefficients
from tecooledmct.geometry_sweep import TECGeometry,solve_geometry
from tecooledmct.model import Scenario

def test_source_record_units_and_sign():
    assert P_BI_TE.seebeck_v_k>0>N_BI_TE.seebeck_v_k
    assert P_BI_TE.electrical_resistivity_ohm_m == pytest.approx(1/140000)
    assert ALUMINA_HIGH_PURITY.thermal_conductivity_w_mk > ALUMINA_96.thermal_conductivity_w_mk
    assert GOLD_WIRE_4N.thermal_conductivity_w_mk == pytest.approx(315)
    assert KOVAR.thermal_conductivity_w_mk==pytest.approx(17.3)
    assert SN_SB_95_5.thermal_conductivity_w_mk==pytest.approx(64.7)
    for mat in MATERIALS.values():
        assert mat.source_url.startswith("https://")
        assert mat.thermal_conductivity_w_mk>0

def test_alumina_layer_resistance():
    low=layer_temperature_drop(ALUMINA_96,.22,2.4,.015)
    high=layer_temperature_drop(ALUMINA_HIGH_PURITY,.22,2.4,.015)
    assert high["thermal_resistance_k_w"]<low["thermal_resistance_k_w"]
    assert high["delta_t_k"]==pytest.approx(.019097222222, rel=1e-6)

def test_literature_transport_vs_fit():
    coeff=literature_stage_coefficients(TECGeometry())
    assert sum(coeff["alpha_v_per_k"])==pytest.approx(44*330e-6)
    assert sum(coeff["resistance_ohm"])>0
    compare=compare_coefficients()
    assert compare["OEM_limit_fitted"]["resistance_total_ohm"]!=pytest.approx(
        compare["uncalibrated_literature_300K"]["resistance_total_ohm"])

def test_optional_literature_profile_does_not_change_default():
    s=Scenario()
    a=solve_geometry(s,TECGeometry())
    b=solve_geometry(s,TECGeometry(),coefficients=literature_stage_coefficients(TECGeometry()))
    assert a["detector_k"]!=pytest.approx(b["detector_k"])
    assert abs(a["detector_k"]-195.5)<1
