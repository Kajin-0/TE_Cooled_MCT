"""Read-only frozen-source guards and exact current source/data replay."""
import hashlib,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'data/synthetic_v3_assembly_20261102'
def digest(p):return hashlib.sha256(os.readlink(p).encode() if p.is_symlink() else p.read_bytes()).hexdigest()
def main():
    reg=json.loads((B/'registration.json').read_text());bad=[];count=0
    for name,h in reg['input_hashes'].items():
        if name in ('AGENTS.md','README.md','docs/ENGINEERING_CHRONOLOGY.md'):continue
        count+=1
        if digest(R/name)!=h:bad.append(name)
    # Every baseline tracked blob except current mutable instructions is immutable.
    records=subprocess.check_output(['git','ls-tree','-rz','--full-tree',reg['baseline']],cwd=R).split(b'\0');n=0;size=0
    for record in records:
        if not record:continue
        meta,path=record.split(b'\t',1);mode,typ,obj=meta.split();name=os.fsdecode(path)
        if name in ('AGENTS.md','README.md','docs/ENGINEERING_CHRONOLOGY.md','.gitattributes'):continue
        p=R/name;raw=os.readlink(p).encode() if mode==b'120000' else p.read_bytes();expected=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if expected!=obj.decode():bad.append(name)
        n+=1;size+=len(raw)
    from tecooledmct.tec_assembly_v3 import design
    saved=json.loads((B/'source_final/design.json').read_text());assert saved==json.loads(json.dumps(design()))
    assert not bad,bad
    print(json.dumps(dict(status='PASS baseline bytes and source replay',registered_inputs=count,baseline_blobs=n,bytes=size,source_body_count=len(saved['bodies'])),indent=2))
if __name__=='__main__':main()
