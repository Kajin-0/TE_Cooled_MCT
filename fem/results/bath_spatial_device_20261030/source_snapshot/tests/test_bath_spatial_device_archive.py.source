"""Actual failed coupled fields, immutable gates and exact field-byte restoration."""
import hashlib,json,shutil,uuid
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'fem/results/bath_spatial_device_20261030'
def test_split_gzip_restore_checks_exact_bytes_and_refuses_corrupt_parts(monkeypatch):
    import gzip
    import fem.restore_bath_spatial as module
    folder=ROOT/'outputs'/('spatial-split-unit-'+uuid.uuid4().hex);case=folder/'case';case.mkdir(parents=True)
    try:
        monkeypatch.setattr(module,'ARCHIVE',folder);data=b'actual field bytes for deterministic archive restoration\n'*100;packed=gzip.compress(data,mtime=0);parts=[]
        for j,start in enumerate(range(0,len(packed),7)):
            name=f'field.bin.gz.part{j:03d}';chunk=packed[start:start+7];(case/name).write_bytes(chunk);parts.append({'name':name,'sha256':hashlib.sha256(chunk).hexdigest()})
        (case/'field.bin.gz.parts.json').write_text(json.dumps({'gzip_sha256':hashlib.sha256(packed).hexdigest(),'parts':parts}))
        (case/'uncompressed_sha256.json').write_text(json.dumps({'field.bin':hashlib.sha256(data).hexdigest()}))
        target=folder/'restored.bin';module.restore(case,'field.bin',target);assert target.read_bytes()==data
        with pytest.raises(ValueError):module.restore(case,'field.bin',target)
        (case/parts[-1]['name']).write_bytes(b'changed')
        with pytest.raises(ValueError,match='Changed compressed part'):module.restore(case,'field.bin',folder/'bad.bin')
    finally:shutil.rmtree(folder)

def test_actual_spatial_pair_stays_failed_and_all_evidence_is_immutable():
    if not DEST.exists():pytest.skip('Coupled spatial archive not published yet')
    ledger=json.loads((DEST/'checksums.json').read_text())
    for group,base in [('sources',ROOT),('artifacts',DEST)]:
        for name,digest in ledger[group].items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,name
    s=json.loads((DEST/'device_summary.json').read_text());assert len(s['cases'])==2 and not s['combined_case_permitted'] and not s['full_numerical_release']
    for c in s['cases']:
        assert not c['bath_raw_1percent_passed'] and abs(c['bath_relative_error'])>.01
        assert c['all_nonraw_gates_passed'] and c['solver_status']['exit_code']==0 and c['solver_status']['nonlinear_last_relative_change']<1e-9
        e=json.loads((DEST/'cases'/c['case']/'execution.json').read_text());assert e['vtu_sha256']==c['field_sha256'] and e['mesh_sha256']==c['mesh_sha256']
    assert s['original_raw_gates']=={'bath':.01,'cold':.05}

def test_real_native_and_derived_archived_fields_restore_identical_bytes():
    if not DEST.exists():pytest.skip('Coupled spatial archive not published yet')
    from fem.restore_bath_spatial import restore
    out=ROOT/'outputs'/('bath-spatial-restore-test-'+uuid.uuid4().hex)
    try:
        for label,name in [('transverse1','fields_t0001.vtu'),('transverse2','derived.vtu')]:
            target=out/(label+'-'+name);case=DEST/'cases'/label;restore(case,name,target)
            expected=json.loads((case/'uncompressed_sha256.json').read_text())[name]
            assert hashlib.sha256(target.read_bytes()).hexdigest()==expected
    finally:
        if out.exists():shutil.rmtree(out)
