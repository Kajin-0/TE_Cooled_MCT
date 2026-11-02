"""Scoped saved-result verification; never rerun the registered campaign."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('data/v3_conservative_flux_20261102')

def guard():
    registration=json.loads((BASE/'registration.json').read_text())
    for p,h in registration['sealed_files'].items():
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    records=subprocess.check_output(['git','ls-tree','-rz',registration['baseline']]).split(b'\0')
    n=size=0
    for record in records:
        if not record:continue
        meta,p=record.split(b'\t',1);mode,kind,expected=meta.split();p=os.fsdecode(p)
        if p in ('AGENTS.md','README.md','docs/ENGINEERING_CHRONOLOGY.md','.gitattributes'):continue
        raw=os.readlink(p).encode() if mode==b'120000' else Path(p).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==expected.decode(),p
        n+=1;size+=len(raw)
    return dict(status='PASS',baseline=registration['baseline'],blobs=n,bytes=size,sealed=len(registration['sealed_files']))

def main(out):
    out.mkdir(exist_ok=False,parents=True)
    template=json.loads(Path('data/v3_interconnect_et_20261102/verification_portability/checks.json').read_text())
    template[0]['argv'].extend(['tests/test_v3_conservative_flux.py','tests/test_v3_flux_stopped_results.py'])
    records=[]
    for c in template:
        cmd=[x.replace('outputs/v3-et-verification','outputs/v3-flux-verification') for x in c['argv']]
        then=time.monotonic()
        with (out/(c['name']+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        records.append(dict(name=c['name'],argv=cmd,exit_code=r.returncode,seconds=time.monotonic()-then,observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        (out/'checks.json').write_text(json.dumps(records,indent=2)+'\n');print(c['name'],r.returncode,flush=True)
        if r.returncode:raise SystemExit(r.returncode)
    (out/'immutable_guard.json').write_text(json.dumps(guard(),indent=2)+'\n')

if __name__=='__main__':main(Path(sys.argv[1]))
