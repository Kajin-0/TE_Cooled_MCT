"""Independent original mesh/TRI3 ownership audit for rigid plate translations."""
from pathlib import Path
from collections import defaultdict
import json,numpy as np
from tecooledmct.height_coupling_v320 import mapping,read,CANDIDATE
from scripts.v2_source_ceramic_spatial import PATHS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/tec_height_coupling_20261110'
def inside_rect(x,y,q,tol=2e-6):return (x>=q[0]-tol)&(x<=q[0]+q[3]+tol)&(y>=q[1]-tol)&(y<=q[1]+q[4]+tol)
def main():
 m=mapping();by={b['name']:b for b in read(CANDIDATE)['bodies']};tags=set(m['faces']);xyz=np.loadtxt(PATHS['node'],skiprows=1,usecols=(1,2,3));tris=defaultdict(list)
 with PATHS['face'].open() as f:
  for line in f:
   a=line.split()
   if len(a)==5 and int(a[-1]) in tags:tris[int(a[-1])].append([int(v)-1 for v in a[1:4]])
 assert set(tris)==tags
 rows=[];max_area=0.;total=0
 for tag,f in sorted(m['faces'].items()):
  tri=np.array(tris[tag],int);v=xyz[tri].copy();v[:,:,2]+=f['translated_z_mm'];ar=.5*np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)
  assert min(ar)>0;A=float(ar.sum());err=abs(A/f['face_area_mm2']-1);assert err<.02,(tag,err)
  skin=by[f['candidate_physical_skin']];p=v.mean(axis=1);on=np.zeros(len(p),bool)
  for q in skin['boxes_mm']:
   atz=(abs(p[:,2]-q[2])<2e-6)|(abs(p[:,2]-(q[2]+q[5]))<2e-6)
   on|=inside_rect(p[:,0],p[:,1],q)&atz
  assert on.all(),(tag,int((~on).sum()))
  total+=len(tri);max_area=max(err,max_area)
  rows.append({'source_tag':tag,'stage':f['ceramic_stage'],'candidate_skin':f['candidate_physical_skin'],'triangles':len(tri),'mesh_area_mm2':A,'cad_area_mm2':f['face_area_mm2'],'relative_area_error':err,'all_translated_triangle_centroids_in_candidate_skin':True})
 # Actual original ceramic 3D nodes are translated, never overwrite source mesh.
 elems=defaultdict(list)
 with PATHS['ele'].open() as f:
  next(f)
  for line in f:
   a=line.split()
   if len(a)==6 and int(a[-1]) in (1,2,3,4):elems[int(a[-1])].append([int(i)-1 for i in a[1:5]])
 out={};counts=[]
 for rid in (1,2,3,4):
  t=np.array(elems[rid],int);ids=np.unique(t);src=xyz[ids];dst=src.copy();dst[:,2]+=m['plate_shifts_mm'][rid-1]
  assert np.allclose(dst-src,[0,0,m['plate_shifts_mm'][rid-1]],atol=1e-12,rtol=0)
  out[f'ceramic{rid-1}_source_node_ids_1based']=ids+1;out[f'ceramic{rid-1}_translated_xyz_mm']=dst
  counts.append(len(t))
 assert sum(counts)==11791
 path=OUT/'translated_ceramic_nodes.npz';assert not path.exists();np.savez_compressed(path,**out)
 import hashlib
 result={'status':'PASS source-face/owner and actual TRI3 translation; independent candidate conformal mesh NOT RUN',
  'source_face_count':len(rows),'leg_face_count':len(m['leg_faces']),'translated_triangle_count':total,'max_relative_area_error':max_area,
  'tet_counts':counts,'tets_total':sum(counts),'plate_shifts_mm':m['plate_shifts_mm'],'faces':rows,
  'translated_nodes_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 f=OUT/'mesh_mapping_audit.json';assert not f.exists();f.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='faces'})
if __name__=='__main__':main()
