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
