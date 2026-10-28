"""Explicitly geometry-only checks: no assertion of full-TEC solved physics."""
import json
import os
import subprocess
import sys

import pytest

from tecooledmct.fem_g2b_geometry import assembly_manifest


def test_three_stage_assumed_geometry_and_distinct_ports():
    m = assembly_manifest()
    assert sum(b["kind"] == "leg" for b in m["bodies"]) == 88
    assert sum(b["kind"] == "bridge" for b in m["bodies"]) == 85
    assert sum(b["kind"] == "ceramic" for b in m["bodies"]) == 4
    assert len(m["terminal_planes"]) == 6
    assert [n["couples"] for n in m["stage_nets"]] == [28, 12, 4]
    assert m["overall_height_m"] == pytest.approx(.0038)
    assert len(m["bodies"]) == 183
    assert all(n["graph_audit"]["unique_path"] for n in m["stage_nets"])
    paths = [set(n["conductor_path"]) for n in m["stage_nets"]]
    assert not paths[0] & paths[1] and not paths[1] & paths[2] and not paths[0] & paths[2]
    assert "not implemented" in m["module_two_terminal_wiring"]


@pytest.mark.skipif(os.environ.get("TE_FEM_SMOKE") != "1", reason="requires actual Gmsh/ElmerGrid")
def test_real_88_leg_mesh_feasibility(tmp_path):
    out = tmp_path/"g2b"
    p = subprocess.run([sys.executable, "-m", "tecooledmct.fem_g2b_geometry", "--out", str(out)],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    assert p.returncode == 0, p.stdout[-5000:]
    audit = json.loads((out/"audit.json").read_text())
    assert audit["passed"] and not audit["coupled_solution"]
    assert audit["legs"] == 88 and audit["electrical_components"] == 3
    assert audit["unintended_conductor_connections"] == 0
