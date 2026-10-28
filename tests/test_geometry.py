from dataclasses import replace
import pytest
from tecooledmct.model import Scenario, solve
from tecooledmct.geometry_sweep import TECGeometry, geometry_coefficients, solve_geometry, sweep_pellet_height, transport_geometry
from tecooledmct.pellet_fvm import PelletField, simulate_pellet
from tecooledmct.geometry_demo import minimum_power_at_target

def test_nominal_reference_matches_previous_solver():
    s=Scenario()
    assert solve_geometry(s,TECGeometry())["detector_k"]==pytest.approx(solve(s)["detector_k"],abs=1e-7)

def test_leg_height_and_area_change_transport():
    base=geometry_coefficients(TECGeometry())
    taller=geometry_coefficients(TECGeometry(leg_lengths_mm=(1.07,.82,.8)))
    wider=geometry_coefficients(TECGeometry(leg_side_mm=.5))
    assert taller["resistance_ohm"][2]>base["resistance_ohm"][2]
    assert taller["thermal_conductance_w_per_k"][2]<base["thermal_conductance_w_per_k"][2]
    assert wider["resistance_ohm"][2]<base["resistance_ohm"][2]
    assert wider["thermal_conductance_w_per_k"][2]>base["thermal_conductance_w_per_k"][2]

def test_fixed_current_geometry_tradeoff():
    rows=sweep_pellet_height(Scenario(),(.7,1.,1.3))
    assert rows[0]["detector_k"]>rows[1]["detector_k"]>rows[2]["detector_k"]
    assert rows[0]["electrical_power_w"]<rows[1]["electrical_power_w"]<rows[2]["electrical_power_w"]
    assert all(r["energy_balance_max_w"]<1e-6 for r in rows)

def test_contact_fraction_changes_length_response():
    g=TECGeometry(contact_fraction=.25)
    base=geometry_coefficients(g)
    thin=geometry_coefficients(replace(g,leg_lengths_mm=(1.07,.82,.32)))
    assert 0<thin["resistance_ohm"][2]<base["resistance_ohm"][2]

def test_voxel_fvm_adiabatic_matches_analytic_leg_transport():
    p=PelletField(side_h_w_m2k=0.,nx=6,ny=6,nz=20)
    r=simulate_pellet(p)
    expected=transport_geometry(2,p.current_a,p.cold_k,p.hot_k,geometry_coefficients(TECGeometry()))
    assert 8*r["qc_w_per_pellet"]==pytest.approx(expected["qc_w"],rel=1e-6)
    assert r["pde_energy_residual_w"]<1e-9

def test_voxel_fvm_convergence_and_sidewall_heat():
    p=PelletField(side_h_w_m2k=5.)
    coarse=simulate_pellet(replace(p,nx=4,ny=4,nz=10))
    fine=simulate_pellet(replace(p,nx=10,ny=10,nz=30))
    assert coarse["pde_energy_residual_w"]<1e-9
    assert fine["pde_energy_residual_w"]<1e-9
    assert coarse["heat_out_sides_w_per_pellet"]<0
    assert abs(coarse["qc_w_per_pellet"]-fine["qc_w_per_pellet"])<1e-5

def test_200k_power_optimization_tradeoff():
    s=Scenario()
    shorter=TECGeometry(leg_lengths_mm=(.749,.574,.448))
    short=minimum_power_at_target(s,shorter,200.)
    nominal=minimum_power_at_target(s,TECGeometry(),200.)
    assert short["feasible"] and nominal["feasible"]
    assert short["power_w"]>nominal["power_w"]
