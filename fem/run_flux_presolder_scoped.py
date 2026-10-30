#!/usr/bin/env python3
"""Bounded coupon driver with container high-water memory and child-process RSS."""
import argparse,json,resource,time
from pathlib import Path
from tecooledmct.flux_presolder_coupon import main
from tecooledmct.g2d_data import dump

parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['junction','presolder']);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
start=time.monotonic();status='failed'
try:
    main(args.out.resolve(),args.kind);status='completed'
finally:
    record={'status':status,'wall_seconds':time.monotonic()-start,'child_peak_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'child_rss_scope':'maximum of completed child processes in this driver, including ElmerGrid/ElmerSolver; not sum of concurrent RSS','container_cpu_limit':4,'container_memory_limit_bytes':12*1024**3}
    peak=Path('/sys/fs/cgroup/memory.peak')
    if peak.exists():record['container_memory_peak_bytes']=int(peak.read_text())
    args.out.mkdir(parents=True,exist_ok=True);dump(args.out/'runtime_resources.json',record)
