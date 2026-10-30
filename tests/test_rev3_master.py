"""Single professional master, original-byte preservation and provenance."""
import hashlib
import json
from pathlib import Path
import pytest

from reports.master.history import ROOT,ORIGINAL,ORIGINAL_SHA,verify_historical
from reports.master.validate import reader,required_content,verify_current


@pytest.mark.parametrize('text',['Codex generated','Agent notes','TODO item',
    'reports/master/report.tex','inputs.json','CI passed','Revision 4',
    'Review draft','github.com/example','/home/User/model','a'*64])
def test_master_reader_rejects_admin_paths_and_competing_revision(text):
    with pytest.raises(ValueError):reader('Revision 3. '+text)


def test_master_reader_accepts_standalone_science_and_citations():
    reader('Revision 3. Hypothetical reference article. Numerical release incomplete. '
           'Gray radiation, source geometry and nonlinear thermoelectric transport; '
           'doi:10.1088/0256-307X/42/5/056304. FAIL 1.069%.')


def test_original_exact_pdf_stays_sealed_historical_evidence():
    assert verify_historical()
    record=json.loads((ROOT/'reports/historical/rev3_original.json').read_text())
    assert 'HISTORICAL' in record['kind']
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()==record['sha256']==ORIGINAL_SHA


def test_one_live_master_has_verified_reader_and_all_page_review():
    assert verify_current()
    current=json.loads((ROOT/'reports/rev3_review/current.json').read_text());out=ROOT/current['edition']
    assert (out/'report.pdf').is_symlink()
    assert not current['review_draft']
    required_content((out/'reader.txt').read_text())
    v=json.loads((out/'validation.json').read_text());visual=json.loads((out/'visual_review.json').read_text())
    assert v['all_pages_rendered'] and visual['all_pages_inspected']
    assert visual['pages']==v['pages'] and len(visual['inspected_pages'])==v['pages']
    assert len(v['render_pixel_checks'])==v['pages']
    assert all(not x['edge_ink'] for x in v['render_pixel_checks'])
    reproducibility=json.loads((out/'reproducibility.json').read_text())
    assert reproducibility['pdf_exact_bytes_reproduced'] and reproducibility['figures_exact_bytes_reproduced']
