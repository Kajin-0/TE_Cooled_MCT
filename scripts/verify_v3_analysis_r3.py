"""No-new-PDE R3 publication checks; source identity and STOP are independent gates."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import time

from tecooledmct.v3_analysis_r3_integrity import verify_hashes

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_analysis_r3_20261103'
BASELINE = '4955177acb6eea8bbf8a9e03d2065a8ab8dbc003'
MUTABLE = {'AGENTS.md', 'README.md', 'docs/ENGINEERING_CHRONOLOGY.md', '.gitattributes'}


def frozen_guard():
    count = size = 0
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', BASELINE], cwd=ROOT)
    for item in tree.split(b'\0'):
        if not item:
            continue
        metadata, path = item.split(b'\t', 1)
        mode, kind, identity = metadata.split()
        filename = os.fsdecode(path)
        if filename in MUTABLE:
            continue
        p = ROOT/filename
        raw = os.readlink(p).encode() if mode == b'120000' else p.read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == identity.decode(), filename
        count += 1
        size += len(raw)
    for name in ('protected_inputs.json', 'preserved_untracked.json'):
        records = json.loads((DATA/name).read_text())['files']
        assert verify_hashes(ROOT, records)
    return dict(status='PASS exact baseline blobs and preexisting trial bytes',
                baseline=BASELINE, tracked_immutable_blobs=count, bytes=size,
                protected_inputs=23, prior_untracked_files=84,
                mutable_exceptions=sorted(MUTABLE))


def main():
    out = DATA/'verification_01'
    out.mkdir(exist_ok=False)
    commands = [
        ('applicable_no_PDE', ['./fem/run.sh', 'env', '-u', 'TE_FEM_SMOKE',
           'OPENBLAS_NUM_THREADS=1', 'OMP_NUM_THREADS=4', 'timeout', '600',
           'python', '-B', '-m', 'pytest', '-q', '--ignore=outputs']),
        ('master', ['python3', '-B', '-m', 'reports.master.validate', '--current']),
        ('archive', ['./fem/run.sh', 'python', '-B', 'fem/archive_bath_spatial_device.py', '--verify']),
        ('legacy_cli', ['./fem/run.sh', 'python', '-B', '-m', 'tecooledmct.cli', '--quick',
           '--out', 'outputs/v3-analysis-r3-20261103/legacy-cli']),
        ('legacy_geometry', ['./fem/run.sh', 'python', '-B', '-m', 'tecooledmct.geometry_demo',
           '--out', 'outputs/v3-analysis-r3-20261103/legacy-geometry']),
        ('historical_frozen_guard', ['./fem/run.sh', 'python', '-B', 'scripts/verify_synthetic_v3_checkpoint.py']),
    ]
    results = []
    for name, argv in commands:
        start = time.monotonic()
        with (out/(name+'.log')).open('w') as log:
            p = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        results.append(dict(name=name, argv=argv, exit_code=p.returncode,
             seconds=time.monotonic()-start,
             observed_end_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        (out/'checks.json').write_text(json.dumps(results, indent=2)+'\n')
        print(name, p.returncode, flush=True)
        if p.returncode:
            raise SystemExit(p.returncode)
    (out/'frozen_baseline.json').write_text(json.dumps(frozen_guard(), indent=2)+'\n')
    (out/'completion.json').write_text(json.dumps(dict(
        status='PASS software/protection checks only; R3 GLOBAL MESH STOP',
        no_new_PDE=True, surface_mesh_qualified=False, global_3D='NOT RUN',
        observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()), indent=2)+'\n')


if __name__ == '__main__':
    main()
