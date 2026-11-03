"""Publication checks for the failed one-global-surface trial; never runs a mesh."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r32_global_surface_20261103'
BASELINE = 'efd853cbd33a85acba5012b0b70521389ea31e0b'
MUTABLE = {'AGENTS.md', 'README.md', '.gitattributes', 'docs/ENGINEERING_CHRONOLOGY.md'}


def frozen_guard():
    count = size = 0
    for item in subprocess.check_output(['git', 'ls-tree', '-rz', BASELINE], cwd=ROOT).split(b'\0'):
        if not item:
            continue
        metadata, path = item.split(b'\t', 1)
        mode, kind, identity = metadata.split()
        name = os.fsdecode(path)
        if name in MUTABLE:
            continue
        p = ROOT/name
        raw = os.readlink(p).encode() if mode == b'120000' else p.read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == identity.decode(), name
        count += 1
        size += len(raw)
    preserved = {}
    for name in ('protected_inputs.json', 'preserved_untracked.json'):
        files = json.loads((DATA/name).read_text())['files']
        for filename, q in files.items():
            expected = q if isinstance(q, str) else q['sha256']
            assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest() == expected, filename
        preserved[name] = len(files)
    return dict(status='PASS exact baseline, parent and preexisting trial identities', baseline=BASELINE,
                immutable_tracked_blobs=count, bytes=size, ledgers=preserved,
                mutable_exceptions=sorted(MUTABLE))


def main():
    out = DATA/'verification_01'
    out.mkdir(exist_ok=False)
    commands = [
        ('applicable_no_new_PDE', ['./fem/run.sh', 'env', '-u', 'TE_FEM_SMOKE',
          'OPENBLAS_NUM_THREADS=1', 'OMP_NUM_THREADS=4', 'timeout', '600',
          'python', '-B', '-m', 'pytest', '-q', '--ignore=outputs']),
        ('master', ['python3', '-B', '-m', 'reports.master.validate', '--current']),
        ('archive', ['./fem/run.sh', 'python', '-B', 'fem/archive_bath_spatial_device.py', '--verify']),
        ('legacy_cli', ['./fem/run.sh', 'python', '-B', '-m', 'tecooledmct.cli', '--quick',
          '--out', 'outputs/v3-r32-surface-20261103/legacy-cli']),
        ('legacy_geometry', ['./fem/run.sh', 'python', '-B', '-m', 'tecooledmct.geometry_demo',
          '--out', 'outputs/v3-r32-surface-20261103/legacy-geometry']),
        ('historical_guard', ['./fem/run.sh', 'python', '-B', 'scripts/verify_synthetic_v3_checkpoint.py']),
    ]
    results = []
    for name, argv in commands:
        start = time.monotonic()
        with (out/(name+'.log')).open('w') as log:
            run = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        results.append(dict(name=name, argv=argv, exit_code=run.returncode,
            seconds=time.monotonic()-start, observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        (out/'checks.json').write_text(json.dumps(results, indent=2)+'\n')
        print(name, run.returncode, flush=True)
        if run.returncode:
            raise SystemExit(run.returncode)
    (out/'frozen_guard.json').write_text(json.dumps(frozen_guard(), indent=2)+'\n')
    (out/'completion.json').write_text(json.dumps(dict(status='PASS SOFTWARE/INTEGRITY ONLY; GLOBAL MESH STOP',
         observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         global_mesh_attempts=1, global_mesh_qualified=False, PDE_RUN=False, original_numerical_FAILs_unchanged=True), indent=2)+'\n')


if __name__ == '__main__':
    main()
