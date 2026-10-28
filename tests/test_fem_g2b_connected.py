"""The new two-terminal topology must not change original six-port feasibility."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tecooledmct.fem_g2b_connected import connected_manifest, orthogonal_audit
from tecooledmct.fem_g2b_geometry import assembly_manifest


def test_two_terminal_path_and_explicit_dielectric_removal():
    m = connected_manifest()
    r = orthogonal_audit(m)
    assert r["passed"] and r["graph"]["unique_path"]
    assert r["graph"]["nodes"] == 181 and r["graph"]["edges"] == 180
    assert len(m["terminal_planes"]) == 2 and len(m["interstage_links"]) == 2
    assert len(set(m["conductor_path"])) == len(m["conductor_path"])
    legs = [bid for bid in m["conductor_path"] if m["bodies"][bid-1]["kind"] == "leg"]
    assert len(legs) == 88
    assert any(b["expected_volume_m3"] < sum(x[3]*x[4]*x[5] for x in b["boxes_m"])
               for b in m["bodies"] if b["kind"] == "ceramic")
    # The preserved geometry still has three isolated circuits and six ports.
    original = assembly_manifest()
    assert len(original["terminal_planes"]) == 6 and len(original["stage_nets"]) == 3


def test_broken_or_short_routing_fails_closed():
    m = connected_manifest()
    # Removing the tab leaves the column physically disconnected from its pad.
    m["bodies"][m["interstage_links"][0]-1]["boxes_m"].pop(0)
    with pytest.raises(ValueError, match="contacts"):
        orthogonal_audit(m)
    m = connected_manifest()
    other = m["bodies"][m["interstage_links"][1]-1]
    other["boxes_m"].append(m["bodies"][m["interstage_links"][0]-1]["boxes_m"][0])
    with pytest.raises(ValueError, match="overlap"):
        orthogonal_audit(m)


@pytest.mark.skipif(os.environ.get("TE_FEM_SMOKE") != "1", reason="requires actual Gmsh connected mesh")
def test_actual_two_terminal_88_leg_mesh(tmp_path):
    out = tmp_path/"connected"
    p = subprocess.run([sys.executable, "-m", "tecooledmct.fem_g2b_connected", "--out", str(out)],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    assert p.returncode == 0, p.stdout[-5000:]
    audit = json.loads((out/"audit.json").read_text())
    assert audit["passed"] and audit["electrical_components"] == 1
    assert audit["legs"] == 88 and audit["external_terminals"] == 2
    assert audit["quality_below_001"] == 0
