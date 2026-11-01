"""Sequential independent author/reader processes; exactly one author call."""
import argparse
from pathlib import Path
import subprocess
import sys

from .native_gas_audit import ROOT,read,write,sha


def run(out):
    out=Path(out)
    if out.exists():raise ValueError('Use an absent checkpoint directory')
    out.mkdir(parents=True)
    note=ROOT/'docs/ISOLATED_CAP_AND_NATIVE_GAS_20261101.md'
    write(out/'registration.json',{'registration':note.read_text().split('## Results')[0],
        'writer_attempts_authorized':1,'source_sha256':{n:sha(ROOT/n) for n in ('tecooledmct/isolated_cap_pipeline.py','tecooledmct/isolated_cap_writer.py','tecooledmct/isolated_cap_reader.py')}})
    for stage,module,args in [('writer','tecooledmct.isolated_cap_writer',['--out',str(out/'phase_A')]),
                              ('reader','tecooledmct.isolated_cap_reader',['--data',str(out/'phase_A')])]:
        with (out/(stage+'.log')).open('w') as log:
            completed=subprocess.run([sys.executable,'-m',module,*args],stdout=log,stderr=subprocess.STDOUT,timeout=120)
        if completed.returncode:
            write(out/'phase_A_status.json',{'qualified':False,'failed_stage':stage,'exit_code':completed.returncode,'author_calls':1,'phase_B':'NOT RUN','phase_C':'NOT RUN'})
            raise RuntimeError('Isolated '+stage+' failed; no retry')
    q=read(out/'phase_A/qualification.json')
    if not q['phase_A_qualified']:raise ValueError('Phase A not qualified')
    write(out/'phase_A_status.json',{'qualified':True,'author_calls':1,'writer_pid':q['writer_pid'],'reader_pid':q['reader_pid'],'phase_B':'PENDING','phase_C':'PENDING'})
    print('Phase A qualified; separate writer/reader PIDs',q['writer_pid'],q['reader_pid'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();run(args.out)
