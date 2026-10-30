"""Prevent obsolete geometry, hidden identifiers and false report qualification."""
import copy,json
from pathlib import Path
import pytest
from reports.rev3_review.validate import reader,provenance

@pytest.mark.parametrize('bad',['A Cold20 result','cold\n30 plot','G2b verified','/home/User/model','github.com/team/project','commit value','a'*40])
def test_review_reader_rejects_machine_and_internal_identifiers(bad):
    with pytest.raises(ValueError):reader(bad)

def test_review_reader_accepts_sources_and_explicit_failure():
    reader('Revision 3 REVIEW DRAFT. VIGO ZTM-TO66-Z030. Full thermal verification incomplete. FAIL 6.48%. doi:10.1364/AO.47.000578')

def test_review_requires_corrected_mesh_and_honest_failed_scope():
    key='fem/results/cold_interface_convergence_20261030/device/cold20um_FAILED/mesh/mesh.npz'
    d={'report_revision':3,'full_qualification':False,'OEM_validated':False,'mesh_nodes':159991,'tetrahedra':647657,'solid_domains':216,'thermoelectric_legs':88,'tetrahedra_bijection_verified':True,'node_bijection_max_distance_m':0.,'inputs':{key:'mesh'},'mesh_sha256':'mesh'}
    assert provenance(d)
    for field,value in [('full_qualification',True),('tetrahedra',366156),('tetrahedra_bijection_verified',False)]:
        bad=copy.deepcopy(d);bad[field]=value
        with pytest.raises(ValueError):provenance(bad)
    bad=copy.deepcopy(d);bad['inputs']['fem/results/g3b_20261029/old.png']='old'
    with pytest.raises(ValueError):provenance(bad)

def test_review_preserves_historical_pdf():
    from reports.rev3_review.build import ROOT,sha
    assert sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment.pdf')=='751284cabaffa34f7f338f85ffa05cd88c59e157831f3dc9f1837d7758f3ac1c'

def test_published_review_edition_has_verified_immutable_inputs_and_pdf():
    from reports.rev3_review.build import ROOT,sha,PUBLIC
    from reports.rev3_review.validate import verify_edition
    current=json.loads((ROOT/'reports/rev3_review/current.json').read_text())
    out=ROOT/current['edition']
    assert verify_edition(out)
    assert sha(PUBLIC)==sha(out/'report.pdf')==current['pdf_sha256']
    assert current['review_draft'] and not current['full_qualification']
