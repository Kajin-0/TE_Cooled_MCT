"""Export explicit no-fit law requirements from frozen V3 face registry."""
import argparse,json,hashlib
from pathlib import Path
from tecooledmct.v3_physics_law_requirements import generate_requirements

def run(source,out):
 if out.exists():raise ValueError('refuse overwrite')
 data=json.loads(source.read_text());result=generate_requirements(data)
 result['face_registry_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
 out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(result['status'],result['volume_count'],result['face_count'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
 a=p.parse_args();run(a.source,a.out)
