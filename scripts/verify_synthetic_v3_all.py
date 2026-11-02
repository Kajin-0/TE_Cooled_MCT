"""Bounded existing verification sequence; no new mesh/PDE invoked."""
import datetime,json,subprocess,time,sys
from pathlib import Path
B=Path('data/synthetic_v3_assembly_20261102');O=Path(sys.argv[1]) if len(sys.argv)>1 else B/'verification'
O.mkdir(exist_ok=False);checks=json.loads(Path('data/tec_assembly_v3_20261102/verification/checks.json').read_text());records=[]
checks[0]['argv'].append('tests/test_synthetic_v3_assembly.py')
checks.append(dict(name='integrity',argv=['./fem/run.sh','python','-B','scripts/verify_synthetic_v3_checkpoint.py']))
for c in checks:
    cmd=[a.replace('outputs/v3-assembly-source-gate-20261102','outputs/synthetic-v3-cad-20261102') for a in c['argv']]
    start=time.monotonic()
    with (O/(c['name']+'.log')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=300)
    records.append(dict(name=c['name'],argv=cmd,observed_end_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),seconds=time.monotonic()-start,exit_code=r.returncode))
    (O/'checks.json').write_text(json.dumps(records,indent=2)+'\n');print(c['name'],r.returncode,flush=True)
    if r.returncode:raise SystemExit(r.returncode)
