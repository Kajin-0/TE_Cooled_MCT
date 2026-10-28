"""Topology mutations, independent reference identities, and real G2a smoke."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from tecooledmct.fem_g2a import Stage, audit_boxes, ideal_reference, stage_manifest, validate_path
from tecooledmct.fem_g2a_post import plane_sections
from tecooledmct.fem_g2a_run import g1_integrity


@pytest.mark.parametrize("couples,columns", [(1, 2), (4, 4), (6, 3), (8, 8)])
def test_series_path_all_geometry_sizes(couples, columns):
    m = stage_manifest(Stage(couples=couples, columns=columns))
    assert sum(b["kind"] == "leg" for b in m["bodies"]) == 2*couples
    assert sum(b["kind"] == "bridge" for b in m["bodies"]) == 2*couples-1
    assert sum(b["kind"] == "terminal" for b in m["bodies"]) == 2
    assert m["graph_audit"]["unique_path"]
    assert m["graph_audit"]["nodes"] == 4*couples+1
    degrees = list(m["graph_audit"]["degrees"].values())
    assert degrees.count(1) == 2
    assert degrees.count(2) == 4*couples-1


def test_short_and_broken_netlists_are_rejected():
    with pytest.raises(ValueError):
        validate_path([1, 2, 3, 4], [(1, 2), (2, 3), (3, 4), (1, 4)], [1, 4])
    with pytest.raises(ValueError):
        validate_path([1, 2, 3, 4], [(1, 2), (3, 4)], [1, 4])
    m = stage_manifest()
    overlapping = copy.deepcopy(m)
    # Move the first cold bridge down into the legs: this must fail before mesh.
    next(b for b in overlapping["bodies"] if b["kind"] == "bridge")["box_m"][2] -= .1e-3
    with pytest.raises(ValueError, match="Overlapping"):
        audit_boxes(overlapping)
    invalid_contact = copy.deepcopy(m)
    invalid_contact["contacts"].pop()
    with pytest.raises(ValueError, match="graph"):
        audit_boxes(invalid_contact)


def test_four_couple_reference_scaling_and_conservation():
    single = ideal_reference(stage_manifest(Stage(couples=1, columns=2)), .1, .002)
    multi = ideal_reference(stage_manifest(), .1, .008)
    for key in ("alpha_v_k", "leg_resistance_ohm", "conductance_w_k"):
        assert multi[key] == pytest.approx(4*single[key])
    for current in (-.1, 0., .1, .2):
        r = ideal_reference(stage_manifest(), current, .008)
        a, resistance, conductance = r["alpha_v_k"], r["resistance_ohm"], r["conductance_w_k"]
        cold = r["cold_k"]
        qc = a*current*cold-.5*current**2*resistance-conductance*(300-cold)
        qh = a*current*300+.5*current**2*resistance-conductance*(300-cold)
        assert qc == pytest.approx(.008, abs=1e-14)
        assert qh-qc == pytest.approx(r["power_w"], abs=1e-14)


def test_cut_integrates_affine_heat_on_known_triangle():
    # x+y+z<=1 cut at z=.25: area=.75²/2, mean x=.25.
    p = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    pieces = list(plane_sections(p, np.array([[0, 1, 2, 3]]), np.array([True]), 2, .25))
    area = sum(a for _, a, _ in pieces)
    integral = sum(a*(2+3*center[0]) for _, a, center in pieces)
    assert area == pytest.approx(.75**2/2)
    assert integral == pytest.approx(area*(2+3*.25))


def test_g1_sources_and_published_evidence_remain_unchanged():
    assert g1_integrity()["passed"]


@pytest.mark.skipif(os.environ.get("TE_FEM_SMOKE") != "1", reason="requires actual Elmer/Gmsh in fem/run.sh")
def test_real_four_couple_solver_smoke(tmp_path):
    run = tmp_path/"g2a"
    process = subprocess.run([sys.executable, "-m", "tecooledmct.fem_g2a_run", "--quick", "--out", str(run)],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    assert process.returncode == 0, process.stdout[-7000:]
    r = json.loads((run/"summary.json").read_text())
    assert r["verification"]["passed"] and r["g1_integrity"]["passed"]
    assert len(r["cases"]["sweep_p0100"]["cuts"]) == 15
    assert r["audits"][0]["mesh_graph"]["unique_path"]
