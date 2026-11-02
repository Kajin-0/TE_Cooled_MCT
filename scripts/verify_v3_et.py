"""Existing-field/software verification only; never rerun the coupon campaign.

Use a fresh output directory. The 12 historical CAD/mesh/Elmer runtime cases
remain excluded; the new experiment's actual meshes/fields are checked as data.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/v3_interconnect_et_20261102'
MUTABLE = {'AGENTS.md', 'README.md', 'docs/ENGINEERING_CHRONOLOGY.md', '.gitattributes'}


def frozen_guard():
    registration = json.loads((BASE / 'registration.json').read_text())
    bad = []
    for name, expected in registration['input_hashes'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            bad.append(name)
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', registration['baseline']], cwd=ROOT)
    count = size = 0
    for item in tree.split(b'\0'):
        if not item:
            continue
        meta, name = item.split(b'\t', 1)
        mode, kind, identity = meta.split()
        name = os.fsdecode(name)
        if name in MUTABLE:
            continue
        path = ROOT / name
        raw = os.readlink(path).encode() if mode == b'120000' else path.read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if actual != identity.decode():
            bad.append(name)
        count += 1
        size += len(raw)
    assert not bad, bad
    return dict(status='PASS', baseline=registration['baseline'], blobs=count, bytes=size,
                registered_inputs=len(registration['input_hashes']), mutable_exceptions=sorted(MUTABLE))


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    checks = json.loads((ROOT / 'data/synthetic_v3_assembly_20261102/verification_portability/checks.json').read_text())
    checks[0]['argv'].append('tests/test_v3_et.py')
    records = []
    for old in checks:
        cmd = [arg.replace('outputs/synthetic-v3-cad-20261102', 'outputs/v3-et-verification')
               for arg in old['argv']]
        then = time.monotonic()
        with (out / (old['name'] + '.log')).open('w') as log:
            run = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=300)
        records.append(dict(name=old['name'], argv=cmd, exit_code=run.returncode,
                            seconds=time.monotonic()-then,
                            observed_end_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        (out / 'checks.json').write_text(json.dumps(records, indent=2)+'\n')
        print(old['name'], run.returncode, flush=True)
        if run.returncode:
            raise SystemExit(run.returncode)
    (out / 'frozen_baseline.json').write_text(json.dumps(frozen_guard(), indent=2)+'\n')
    (out / 'completion.json').write_text(json.dumps(dict(
        status='PASS software/integrity only; Gate B FAIL unchanged; C/D NOT RUN',
        observed_end_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        seconds=time.monotonic()-start), indent=2)+'\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
