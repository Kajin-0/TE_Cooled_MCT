"""One pinned local worker, external180s kill, independent child resource receipt."""
from pathlib import Path
import argparse
import datetime
import json
import os
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r31_local_mesh_20261103'


def main(case_id):
    registration = json.loads((DATA/'corrective_registration.json').read_text())
    case = next(q for q in registration['cases'] if q['id'] == case_id)
    out = DATA/'cases'/case_id
    out.mkdir(parents=True, exist_ok=False)
    argv = [sys.executable, '-B', 'scripts/v3_r31_worker_v2.py', '--strategy', case['strategy'],
            '--fixture', case['fixture'], '--out', str(out/'worker')]
    started = time.monotonic()
    observed_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    peak = 0.
    killed = False
    with (out/'stdout.log').open('w') as log:
        child = subprocess.Popen(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        while child.poll() is None:
            status = Path('/proc')/str(child.pid)/'status'
            try:
                for line in status.read_text().splitlines():
                    if line.startswith('VmHWM:'):
                        peak = max(peak, int(line.split()[1])/1024)
            except FileNotFoundError:
                pass
            if time.monotonic()-started >= 180:
                child.kill()
                killed = True
                break
            time.sleep(.05)
        code = child.wait()
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = dict(case, status='STOP180s' if killed else 'COMPLETED WORKER; SEE GATES',
         exit_code=code, hard_budget_seconds=180, timeout=killed,
         wall_seconds=time.monotonic()-started, CPU_seconds=usage.ru_utime+usage.ru_stime,
         maximum_child_RSS_MiB=usage.ru_maxrss/1024, sampled_peak_RSS_MiB=peak,
         observed_start_UTC=observed_start,
         observed_end_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         process_bound='one worker in4CPU/8GiB offline pinned container',
         worker_source=registration['sources_sha256']['scripts/v3_r31_worker_v2.py'],
         no_global_mesh=True, no_PDE=True)
    worker_result = out/'worker/result.json'
    if worker_result.exists():
        result['worker_status'] = json.loads(worker_result.read_text())['status']
    (out/'resources.json').write_text(json.dumps(result, indent=2)+'\n')
    print(case_id, result['status'], code, result['wall_seconds'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True)
    main(parser.parse_args().case)
