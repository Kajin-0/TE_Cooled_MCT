#!/usr/bin/env python3
"""Restore exact archived field bytes into NEW outputs paths; no PDE claim."""
import argparse,gzip,hashlib,io,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'fem/results/bath_spatial_device_20261030'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def restore(case,name,target):
    case=case.resolve();target=target.resolve()
    if not case.is_relative_to(ARCHIVE) or not target.is_relative_to(ROOT/'outputs') or target.exists() or Path(name).name!=name:raise ValueError('Restore this archive only into a NEW outputs file')
    record=json.loads((case/'uncompressed_sha256.json').read_text());expected=record[name];packed=case/(name+'.gz');parts=case/(name+'.gz.parts.json')
    if packed.exists():stream=gzip.open(packed,'rb')
    else:
        meta=json.loads(parts.read_text());data=[]
        for item in meta['parts']:
            p=case/item['name']
            if sha(p)!=item['sha256']:raise ValueError('Changed compressed part')
            data.append(p.read_bytes())
        raw=b''.join(data)
        if hashlib.sha256(raw).hexdigest()!=meta['gzip_sha256']:raise ValueError('Changed reconstructed gzip')
        stream=gzip.GzipFile(fileobj=io.BytesIO(raw))
    target.parent.mkdir(parents=True,exist_ok=True)
    with stream,target.open('wb') as out:shutil.copyfileobj(stream,out)
    if sha(target)!=expected:raise ValueError('Restored field bytes differ')
    print('Restored exact archival bytes; no new solver execution:',target)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',type=Path,required=True);p.add_argument('--name',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();restore(a.case,a.name,a.out)
