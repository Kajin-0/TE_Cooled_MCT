"""Historical bytes stay sealed; the public master may evolve independently."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'
ORIGINAL=ROOT/'reports/rev3_review/editions/20261030_b/report.pdf'
ORIGINAL_SHA='d173a8ba952462e1b6bf857739406f58eeb8d5c82b900f9fc65b84d40573acc1'
RECORD=ROOT/'reports/historical/rev3_original.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def verify_historical():
    from reports.rev3_review.validate import verify_edition
    for label in ('20261030_a','20261030_b'):
        verify_edition(ROOT/'reports/rev3_review/editions'/label)
    if sha(ORIGINAL)!=ORIGINAL_SHA:raise ValueError('Original Rev3 bytes changed')
    if sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment.pdf')!='751284cabaffa34f7f338f85ffa05cd88c59e157831f3dc9f1837d7758f3ac1c':
        raise ValueError('Historical Rev2 changed')
    if RECORD.exists():
        d=json.loads(RECORD.read_text())
        if d['sha256']!=ORIGINAL_SHA or ROOT/d['historical_pdf']!=ORIGINAL:
            raise ValueError('Historical PDF identity record changed')
    predecessor=ROOT/'reports/historical/rev3_pre_material_20261101'
    if predecessor.exists():
        d=json.loads((predecessor/'historical_identity.json').read_text())
        expected='1bc0d793ac59cfa8b003454846bba2f7c9fe6bf431d57980ae7d95f8bee7ebff'
        if d['pdf_sha256']!=expected or sha(predecessor/'report.pdf')!=expected or d['pages']!=28:
            raise ValueError('Prior 28-page Rev3 bytes changed')
        for name,digest in d['snapshot_sha256'].items():
            if sha(predecessor/name)!=digest:raise ValueError('Prior Rev3 provenance changed: '+name)
    material_master=ROOT/'reports/historical/rev3_pre_identifiability_20261101'
    if material_master.exists():
        d=json.loads((material_master/'historical_identity.json').read_text())
        expected='03eab4a7546301f1f7558afcecf733713c4a804ca1457da7f4c00dbf4917a829'
        if d['pdf_sha256']!=expected or sha(material_master/'report.pdf')!=expected or d['pages']!=34:
            raise ValueError('Prior 34-page Rev3 bytes changed')
        for name,digest in d['snapshot_sha256'].items():
            if sha(material_master/name)!=digest:raise ValueError('Prior material report provenance changed: '+name)
    finite_predecessor=ROOT/'reports/historical/rev3_pre_finite_sink_20261101'
    if finite_predecessor.exists():
        d=json.loads((finite_predecessor/'historical_identity.json').read_text())
        expected='96265010b41a9f41f53fa31c2fa4e8c3098806696675b3766e69f0554a27e006'
        if d['pdf_sha256']!=expected or sha(finite_predecessor/'report.pdf')!=expected or d['pages']!=36:
            raise ValueError('Prior 36-page Rev3 bytes changed')
        for name,h in d['snapshot_sha256'].items():
            if sha(finite_predecessor/name)!=h:raise ValueError('Prior identifiability report provenance changed: '+name)
    v33_predecessor=ROOT/'reports/historical/rev3_pre_v33_20261108'
    if v33_predecessor.exists():
        d=json.loads((v33_predecessor/'historical_identity.json').read_text())
        expected='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
        if d['pdf_sha256']!=expected or d['pages']!=38:raise ValueError('Prior 38-page identity changed')
        for name,h in d['files_sha256'].items():
            if sha(v33_predecessor/name)!=h:raise ValueError('Prior 38-page evidence changed: '+name)
    return True

def preserve():
    verify_historical()
    if RECORD.exists():return
    if sha(PUBLIC)!=ORIGINAL_SHA:raise ValueError('Preserve original before replacing canonical PDF')
    RECORD.parent.mkdir(exist_ok=True)
    RECORD.write_text(json.dumps({
        'kind':'SEALED HISTORICAL EVIDENCE ONLY; not a second current report',
        'historical_pdf':str(ORIGINAL.relative_to(ROOT)),
        'sha256':ORIGINAL_SHA,'pages':15,
        'sealed_manifest':'reports/rev3_review/editions/20261030_b/edition_checksums.json',
        'sealed_manifest_sha256':sha(ORIGINAL.parent/'edition_checksums.json'),
        'original_public_path':str(PUBLIC.relative_to(ROOT)),
        'preservation':'Original public bytes verified identical to existing sealed historical artifact before canonical replacement.'
    },indent=2)+'\n')
