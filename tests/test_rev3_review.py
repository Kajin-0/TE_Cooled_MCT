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
    bad=copy.deepcopy(d);bad['normal_volume_study']={'full_numerical_release':True,'actual_completed_cases':['cold1','bath2','bath3']}
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
    for edition in (ROOT/'reports/rev3_review/editions').iterdir():
        if (edition/'edition_checksums.json').exists():assert verify_edition(edition)
    assert sha(PUBLIC)==sha(out/'report.pdf')==current['pdf_sha256']
    assert not current['full_qualification']
    if current.get('mode')=='continuous_rev3_master':
        from reports.master.validate import verify_current
        assert not current['review_draft'] and verify_current()
    else:
        assert current['review_draft']

@pytest.mark.parametrize('operation',['figures','supplement'])
def test_generators_refuse_to_overwrite_a_published_edition(tmp_path,operation):
    from reports.rev3_review.build import figures
    from reports.rev3_review.latest_study import supplement
    (tmp_path/'edition_checksums.json').write_text('{}')
    with pytest.raises(ValueError,match='immutable'):
        {'figures':figures,'supplement':supplement}[operation](tmp_path)

def test_validating_a_published_edition_is_read_only():
    from reports.rev3_review.build import ROOT,sha
    from reports.rev3_review.validate import validate
    current=json.loads((ROOT/'reports/rev3_review/current.json').read_text());out=ROOT/current['edition']
    before={p:sha(p) for p in out.rglob('*') if p.is_file()}
    assert validate(out)['passed']
    assert before=={p:sha(p) for p in out.rglob('*') if p.is_file()}
