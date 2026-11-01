"""Report-only evidence projection and retained predecessor identity."""
import json
import matplotlib.pyplot as plt
import pytest

from reports.master import identifiability
from reports.master.history import ROOT,sha,verify_historical


def test_report_keeps_raw_rank_artifact_signed_residual_and_original_34_pages(tmp_path):
    def save(fig,name):plt.close(fig)
    identifiability.generate(tmp_path,save)
    tex=(tmp_path/'identifiability_numerics.tex').read_text()
    assert '+6.372118' in tex and '+0.088846' in tex
    assert '5.18915 & 4' in tex and '1.05019 & 3' in tex
    p=ROOT/'reports/historical/rev3_pre_identifiability_20261101'
    d=json.loads((p/'historical_identity.json').read_text())
    assert d['pages']==34 and 'HISTORICAL' in d['kind']
    assert sha(p/'report.pdf')=='03eab4a7546301f1f7558afcecf733713c4a804ca1457da7f4c00dbf4917a829'
    assert verify_historical()


def test_report_fails_closed_before_plotting_on_corrupted_scientific_input(tmp_path,monkeypatch):
    (tmp_path/'cases.json').write_text('altered')
    (tmp_path/'checksums.json').write_text(json.dumps({'artifact_sha256':{'cases.json':'0'*64}}))
    monkeypatch.setattr(identifiability,'DATA',tmp_path)
    with pytest.raises(ValueError,match='Changed identifiability evidence'):
        identifiability.generate(tmp_path,lambda *_:pytest.fail('Plotted corrupt data'))
