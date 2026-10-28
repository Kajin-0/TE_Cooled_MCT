"""Independent reference identities and optional real-solver smoke test."""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import pytest

from tecooledmct.fem_g1 import reference, tetra_geometry
from tecooledmct.fem_g1_post import section_current


def test_ideal_couple_conserves_energy_both_polarities():
    for current in (-.4, -.2, 0., .2, .4):
        load, hot = .002, 300.
        r = reference(current, load, hot)
        cold = r["cold_k"]
        alpha, resistance, conductance = (r[k] for k in
            ("alpha_v_k", "resistance_ohm", "conductance_w_k"))
        qc = alpha*current*cold-.5*current**2*resistance-conductance*(hot-cold)
        qh = alpha*current*hot+.5*current**2*resistance-conductance*(hot-cold)
        assert qc == pytest.approx(load, abs=1e-14)
        assert qh-qc == pytest.approx(r["power_w"], abs=1e-14)
    assert reference(.2)["cold_k"] < 300 < reference(-.2)["cold_k"]
    assert reference(0., load_w=0.)["cold_k"] == pytest.approx(300.)


def test_tetra_gradients_exact_affine_field():
    # Deliberately skewed element checks transpose/order and SI scaling.
    points = np.array([[.1, .2, .3], [.8, .2, .4], [.2, .9, .3], [.3, .4, 1.1]])*1e-3
    cells = np.array([[0, 1, 2, 3]])
    volume, gradients = tetra_geometry(points, cells)
    slope = np.array([100., -300., 200.])
    temperature = 300.+points@slope
    recovered = temperature[cells]@gradients[0]
    np.testing.assert_allclose(recovered[0], slope, rtol=1e-11)
    np.testing.assert_allclose(gradients.sum(axis=1), 0., atol=1e-12)
    assert volume[0] == pytest.approx(abs(np.linalg.det(points[1:]-points[0]))/6)


def test_interior_cut_integrates_known_uniform_current():
    points = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    cells = np.array([[0, 1, 2, 3]])
    flux, area = section_current(points, cells, np.array([1]),
                                 np.array([[0., 0., 2.]]), 1, 2, .25)
    assert area == pytest.approx(.75**2/2)
    assert flux == pytest.approx(2*area)


@pytest.mark.skipif(os.environ.get("TE_FEM_SMOKE") != "1", reason="set TE_FEM_SMOKE=1 inside fem/run.sh to run actual Gmsh/Elmer")
def test_real_elmer_coupled_smoke(tmp_path):
    assert shutil.which("ElmerSolver") and shutil.which("ElmerGrid")
    process = subprocess.run([sys.executable, "-m", "tecooledmct.fem_g1_run", "--quick",
                              "--out", str(tmp_path/"smoke")], text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    assert process.returncode == 0, process.stdout[-8000:]
    summary = json.loads((tmp_path/"smoke"/"summary.json").read_text())
    assert summary["verification"]["passed"]
    assert summary["upstream_test"]["exit_code"] == 0
    assert len(summary["cases"]) == 4
