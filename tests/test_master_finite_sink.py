"""Frozen-evidence report projection, physical scope and predecessor guards."""
import json
import matplotlib.pyplot as plt
import pytest

from reports.master import finite_sink
from reports.master.history import ROOT,sha,verify_historical


def test_report_projects_actual_target_power_and_preserves_36_page_predecessor(tmp_path):
    names=[]
    def save(fig,name):names.append(name);plt.close(fig)
    finite_sink.generate(tmp_path,save)
    tex=(tmp_path/'finite_sink_numerics.tex').read_text()
    assert '0.548425' in tex and '0.622176' in tex and '0.582632' in tex and '13.4478' in tex
    assert names==['finite_sink_operating','finite_sink_heat']
    p=ROOT/'reports/historical/rev3_pre_finite_sink_20261101'
    assert json.loads((p/'historical_identity.json').read_text())['pages']==36
    assert sha(p/'report.pdf')=='96265010b41a9f41f53fa31c2fa4e8c3098806696675b3766e69f0554a27e006'
    assert verify_historical()


def test_report_fails_closed_on_changed_scientific_ledger(tmp_path,monkeypatch):
    (tmp_path/'cases.json').write_text('unaccepted change')
    (tmp_path/'checksums.json').write_text(json.dumps({'artifact_sha256':{'cases.json':'0'*64}}))
    monkeypatch.setattr(finite_sink,'DATA',tmp_path)
    with pytest.raises(ValueError,match='Changed finite-sink evidence'):
        finite_sink.generate(tmp_path,lambda *_:pytest.fail('Plotted corrupt data'))
