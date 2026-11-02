"""One registered bounded campaign; no retries and no thermal branches."""
import datetime,json,subprocess,time
from pathlib import Path

BASE=Path('data/v3_conservative_flux_20261102')

def main():
    output=BASE/'execution.json'
    if output.exists():raise ValueError('One campaign only; preserve failed execution')
    records=[]
    for role in ('controls','geometry'):
        then=time.monotonic()
        cmd=['./fem/run.sh','env','OPENBLAS_NUM_THREADS=1','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1',
             'timeout','900','python','-B','-m','tecooledmct.v3_flux_study',role,'--out',str(BASE/role)]
        with (BASE/(role+'.log')).open('w') as log:
            result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=930)
        record=dict(role=role,argv=cmd,exit_code=result.returncode,seconds=time.monotonic()-then,
          observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
        gate=BASE/role/'gate.json'
        record['gate']=json.loads(gate.read_text()) if gate.exists() else dict(status='STOP',reason='Phase exited without gate',exit_code=result.returncode)
        records.append(record);output.write_text(json.dumps(records,indent=2)+'\n')
        print(role,record,flush=True)
        if result.returncode or record['gate']['status']!='PASS':
            (BASE/'STOP.json').write_text(json.dumps(dict(status='STOP',phase=role,
                reason=record['gate'],next_phase='NOT RUN',thermal_C='NOT RUN / NOT AUTHORIZED',
                coupled_D='NOT RUN / NOT AUTHORIZED'),indent=2)+'\n')
            return

if __name__=='__main__':main()
