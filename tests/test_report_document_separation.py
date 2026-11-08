"""Regression checks for restored historical Rev3 vs distinct current TEC document."""
from pathlib import Path
import hashlib,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
OLD='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
INTERIM='6a9cb56fc3a78ac31639f4cb0b9c40e29d68997ea73b408ac68651eb1789faf5'
CURRENT='7414831efc95ea09bfd9df483aaf04edac629c48086574a8baefd2385e8e0e66'
def test_document_edition_identity():
    a=ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'
    b=ROOT/'reports/historical/rev3_pre_v33_20261108/report.pdf'
    c=ROOT/'reports/historical/rev3_v33_interim_43pp_20261108/report.pdf'
    d=ROOT/'reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf'
    assert sha(a)==sha(b)==OLD
    assert sha(c)==INTERIM
    assert sha(d)==CURRENT
    assert len({sha(a),sha(c),sha(d)})==3
    pointer=json.loads((ROOT/'reports/rev3_review/current.json').read_text())
    assert pointer['pdf_sha256']==OLD
    assert 'reports/master/generated'==pointer['edition']
def test_current_scientific_source_and_figures():
    p=ROOT/'reports/current'
    m=json.loads((p/'reproduction_manifest.json').read_text())
    assert m['new_physics_solves']==0
    assert m['n_legs']==88 and m['n_pad_faces']==95 and m['n_material_rows']==14
    for name,h in m['figures_sha256'].items():assert sha(p/'figures'/name)==h
    assert 'in V3.3' in (p/'report.tex').read_text()
    assert 'formed' in (p/'report.tex').read_text()
def test_report_page_counts_and_model_identity():
    for filename,n in [('reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf',38),
        ('reports/historical/rev3_v33_interim_43pp_20261108/report.pdf',43),
        ('reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf',21)]:
        # On CI the PDF SHA assertions pin the exact page structures; MuPDF
        # page-count inspection is optional because GitHub runners lack mutool.
        if shutil.which('mutool'):
            out=subprocess.run(['mutool','info',str(ROOT/filename)],capture_output=True,text=True,check=True)
            assert ('Pages: '+str(n)) in out.stdout
    m=(ROOT/'docs/CURRENT_MODEL_DOCUMENTATION_MAP_20261108.md').read_text()
    for marker in ('824','430','formed','net 88','NOT RUN','V3.3'):
        assert marker in m
