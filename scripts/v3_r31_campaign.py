"""Fixed preregistered local cases only, sequential; no automatic corrective replay."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r31_local_mesh_20261103'


def main():
    reg = json.loads((DATA/'registration.json').read_text())
    for name, digest in reg['sources_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    for name, digest in reg['inputs_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    assert not (DATA/'campaign.json').exists()
    results = []
    stop_C = stop_all = False
    for case in reg['cases']:
        if stop_all or (stop_C and case['strategy'] == 'C_directional'):
            results.append(dict(case, status='NOT RUN source/directional stop'))
            continue
        argv = ['./fem/run.sh', 'env', 'OPENBLAS_NUM_THREADS=1', 'OMP_NUM_THREADS=4',
                'timeout', '195', 'python', '-B', 'scripts/v3_r31_case_runner.py', '--case', case['id']]
        run = subprocess.run(argv, cwd=ROOT, timeout=210)
        out = DATA/'cases'/case['id']
        worker = out/'worker/result.json'
        record = json.loads((out/'resources.json').read_text()) if (out/'resources.json').exists() else dict(case, status='STOP parent runtime')
        if worker.exists():
            q = json.loads(worker.read_text())
            record['worker_status'] = q['status']
            record['error'] = q.get('error')
            if 'SOURCE_' in str(q.get('error')):
                stop_all = True
            if case['strategy'] == 'C_directional' and not q['status'].startswith('PASS'):
                stop_C = True
        if run.returncode:
            stop_all = True
        results.append(record)
        (DATA/'campaign.json').write_text(json.dumps(dict(
            status='COMPLETE registered case iteration' if len(results) == len(reg['cases']) else 'PENDING',
            cases=results, observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            automatic_replays=0, no_global_mesh=True, no_PDE=True), indent=2)+'\n')
        print(case['id'], record.get('worker_status', record['status']), flush=True)
    (DATA/'campaign.json').write_text(json.dumps(dict(status='COMPLETE registered case iteration',
        cases=results, observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        automatic_replays=0, no_global_mesh=True, no_PDE=True), indent=2)+'\n')


if __name__ == '__main__':
    main()
