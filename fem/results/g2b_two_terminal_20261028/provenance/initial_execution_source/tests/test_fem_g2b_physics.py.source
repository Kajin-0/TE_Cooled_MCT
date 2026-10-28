"""Cascade sanity identities, immutable checkpoints, and real coupled smoke."""
import json
import os
import subprocess
import sys

import pytest

from tecooledmct.fem_g2b_connected import connected_manifest
from tecooledmct.fem_g2b_physics import cascade_reference, protected_integrity


def test_independent_ideal_cascade_conserves_each_stage():
    m=connected_manifest()
    for current in (-.1,0.,.05,.1):
        r=cascade_reference(m,current,.002)
        q=r["stages"]
        assert q[-1]["cold_heat_w"]==pytest.approx(.002,abs=1e-12)
        for i in (0,1):assert q[i]["cold_heat_w"]==pytest.approx(q[i+1]["hot_heat_w"],abs=1e-12)
        for stage in q:
            assert stage["hot_heat_w"]-stage["cold_heat_w"]==pytest.approx(current*stage["voltage_v"],abs=1e-12)
    zero=cascade_reference(m,0.,0.)
    assert zero["plate_temperatures_k"]==pytest.approx([300.]*4)
    assert cascade_reference(m,.1,.002)["plate_temperatures_k"][-1]<300
    assert cascade_reference(m,-.1,.002)["plate_temperatures_k"][-1]>300


def test_g1_g2a_and_original_six_port_sources_and_evidence_unchanged():
    assert protected_integrity()["passed"]


@pytest.mark.skipif(os.environ.get("TE_FEM_SMOKE")!="1",reason="requires actual full-stack coupled Elmer")
def test_actual_two_terminal_full_stack_smoke(tmp_path):
    out=tmp_path/"coupled"
    p=subprocess.run([sys.executable,"-m","tecooledmct.fem_g2b_run","--quick","--out",str(out)],
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=900)
    assert p.returncode==0,p.stdout[-7000:]
    r=json.loads((out/"summary.json").read_text())
    assert r["verification"]["passed"] and r["quick"]
    assert len([c for c in r["cases"]["loaded_positive"]["cuts"].values() if c["kind"]=="leg"])==88
    assert r["cases"]["loaded_positive"]["cold_mean_k"]<300
    assert r["cases"]["loaded_negative"]["cold_mean_k"]>300
