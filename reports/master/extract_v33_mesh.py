"""Extract portable source-ceramic TET4 connectivity from the recorded original mesh."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from .history import ROOT

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 run=ROOT/'data/v3_3_cavity_package_feedback_20261108/attempt02';reg=json.loads((run/'registration.json').read_text());fields=np.load(run/'source_native_ceramics_V3_3.npz')
 paths={'node':a.mesh/'R38_430_domains.1.node','ele':a.mesh/'R39_430_domains.1.ele','face':a.mesh/'R38_430_domains.1.face'}
 for k,path in paths.items():
  if sha(path)!=reg['original_mesh_SHA256'][k]:raise ValueError('Original mesh identity mismatch: '+k)
 xyz=np.loadtxt(paths['node'],skiprows=1,usecols=(1,2,3));groups={i:[] for i in range(1,5)}
 with paths['ele'].open() as stream:
  n=int(next(stream).split()[0]);assert n==1010119
  for line in stream:
   s=line.split()
   if len(s)==6 and int(s[-1]) in groups:groups[int(s[-1])].append([int(x) for x in s[1:5]])
 arrays={}
 for i in range(4):
  ids=fields[f'ceramic{i}_source_node_id_1based'];assert np.array_equal(fields[f'ceramic{i}_xyz_mm'],xyz[ids-1]);t=np.asarray(groups[i+1],np.int32)
  ix=np.full(len(xyz)+1,-1,np.int32);ix[ids]=np.arange(len(ids));arrays[f'ceramic{i}_tetrahedra_local']=ix[t];assert arrays[f'ceramic{i}_tetrahedra_local'].min()>=0
 counts=[len(groups[i]) for i in range(1,5)];assert counts==[4936,4085,1986,784]
 a.out.mkdir(parents=True,exist_ok=True);np.savez_compressed(a.out/'v33_ceramic_connectivity.npz',**arrays)
 meta=dict(source_mesh_sha256=reg['original_mesh_SHA256'],source_tetrahedra=1010119,ceramic_tetrahedra=counts,mapping='original one-based saved-node IDs mapped to local saved ceramic array order',coordinates_verified_against_original_node_file=True,unit='mm')
 (a.out/'v33_ceramic_connectivity.json').write_text(json.dumps(meta,indent=2)+'\n')
if __name__=='__main__':main()
