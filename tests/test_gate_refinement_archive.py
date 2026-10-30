"""Keep actual new normal-volume fields and original gate labels immutable."""
import hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'fem/results/cold_bath_rev3_20261030'

def test_normal_volume_archive_preserves_actual_evidence_and_failed_release():
    if not ARCHIVE.exists():pytest.skip('New numerical archive has not been published yet')
    ledger=json.loads((ARCHIVE/'checksums.json').read_text())
    for key,base in [('sources',ROOT),('artifacts',ARCHIVE)]:
        for name,digest in ledger[key].items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,name
    summary=json.loads((ARCHIVE/'summary.json').read_text())
    assert not summary['full_numerical_release'] and not summary['OEM_validated']
    assert summary['gates']['cold']==.05 and summary['gates']['bath']==.01
    for label,row in summary['trials'].items():
        if not row['completed']:continue
        a=json.loads((ARCHIVE/(label+'_audit')/'summary.json').read_text())
        e=json.loads((ARCHIVE/'cases'/label/'execution.json').read_text())
        assert a['genuine_completed_coupled'] and a['all_nonraw_gates_passed']
        assert a['mesh_sha256']==e['mesh_sha256'] and a['field_sha256']==e['vtu_sha256']
        assert a['same_case_raw_gates_passed']==(all(abs(x)<.05 for x in a['cold_mismatches']) and abs(a['bath_relative_error'])<.01)
    assert summary['trials']['bath2']['bath_relative_error']<-.01
