#!/usr/bin/env python3
"""Restore archival INPUTS into a new outputs path; never claim a new PDE run."""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def restore(source,target):
    source=source.resolve();target=target.resolve()
    if not source.is_relative_to(ROOT/'fem/results') or not target.is_relative_to(ROOT/'outputs'):
        raise ValueError('Read only this repository archives; write only a new outputs directory')
    if target.exists():raise ValueError('Destination must be new')
    target.mkdir(parents=True)
    for p in source.rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        out=target/p.relative_to(source)
        if p.suffix=='.gz':out=out.with_suffix('')
        out.parent.mkdir(parents=True,exist_ok=True)
        if p.suffix=='.gz':
            with gzip.open(p,'rb') as src,out.open('wb') as dst:shutil.copyfileobj(src,dst)
        else:shutil.copy2(p,out)
    count=0
    for manifest in target.rglob('uncompressed_sha256.json'):
        for name,digest in json.loads(manifest.read_text()).items():
            h=hashlib.sha256()
            with (manifest.parent/name).open('rb') as f:
                while chunk:=f.read(1048576):h.update(chunk)
            if h.hexdigest()!=digest:raise ValueError('Archive decompression checksum differs')
            count+=1
    (target/'RESTORED_ARCHIVAL_INPUTS.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),
        'verified_uncompressed_files':count,'new_solver_execution':False,'scope':'archived source/initialization/field evidence only; no new PDE run'},indent=2)+'\n')
    print('Restored archival inputs',target,'verified fields/results',count)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();restore(a.source,a.out)
