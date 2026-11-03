"""External600s/8GiB supervisor; consumes an exclusive single-run slot."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import resource
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_r32_global_surface_20261103'


def atomic(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)


def memory_events():
    path=Path('/sys/fs/cgroup/memory.events')
    return path.read_text() if path.exists() else 'UNAVAILABLE'


def main():
    reg=json.loads((DATA/'registration.json').read_text())
    assert reg['runs']==1 and reg['wall_limit_seconds']==600. and reg['triangle_limit']==800000
    assert reg['CPUs']==4 and reg['memory_GiB']==8
    for field in ('sources_sha256','inputs_sha256'):
        for filename,h in reg[field].items():
            assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==h,filename
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    token=DATA/'global_run_slot.json'
    fd=os.open(token,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'w') as stream:
        json.dump(dict(observed_UTC=now,run_number=1,NO_RETRY=True,registration_SHA256=hashlib.sha256((DATA/'registration.json').read_bytes()).hexdigest()),stream,indent=2)
    start=time.monotonic();peak=0.;reason=None;before=memory_events();last_write=0.
    with (DATA/'worker_stdout.log').open('w') as log:
        child=subprocess.Popen([sys.executable,'-B','scripts/v3_r32_worker.py'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        while child.poll() is None:
            elapsed=time.monotonic()-start;rss=0.
            try:
                for line in (Path('/proc')/str(child.pid)/'status').read_text().splitlines():
                    if line.startswith('VmRSS:'):rss=int(line.split()[1])/1024
                    if line.startswith('VmHWM:'):peak=max(peak,int(line.split()[1])/1024)
            except FileNotFoundError:pass
            if elapsed>=599.5:reason='WALL_BUDGET';child.kill();break
            if rss>=7.5*1024:reason='RSS_EARLY_GUARD';child.kill();break
            if elapsed-last_write>1:
                atomic(DATA/'external_progress.json',dict(run=1,elapsed_seconds=elapsed,RSS_MiB=rss,observed_peak_MiB=peak,
                    observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
                last_write=elapsed
            time.sleep(.02)
        code=child.wait()
    usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    record=dict(status='STOP '+reason if reason else 'WORKER ENDED; SEE QUALIFICATION',run=1,
        observed_start_UTC=now,observed_end_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        wall_seconds=time.monotonic()-start,CPU_seconds=usage.ru_utime+usage.ru_stime,
        peak_child_RSS_MiB=usage.ru_maxrss/1024,sampled_peak_MiB=peak,exit_code=code,
        worker_deadline_seconds=599.5,hard_wall_limit_seconds=600.,poll_seconds=.02,
        container_CPUs=4,container_memory_GiB=8,early_RSS_guard_GiB=7.5,
        cgroup_memory_events_before=before,cgroup_memory_events_after=memory_events(),
        no_second_run=True,tetrahedralization='NOT RUN',PDE='NOT RUN')
    result=DATA/'run/result.json'
    if result.exists():record['worker_status']=json.loads(result.read_text())['status']
    atomic(DATA/'execution_receipt.json',record)
    print(json.dumps(record),flush=True)


if __name__=='__main__':main()
