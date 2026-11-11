"""Construct source TRI3–rectangle–TRI3 common-refinement P1 gas operator."""
from pathlib import Path
from itertools import combinations
from collections import defaultdict
import json,hashlib,math,time
import numpy as np
from tecooledmct.nominal_gas_p1_v325 import clip,centroid_area,weights,exchange
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_p1_20261111';M=Path('/var/tmp/mct_r3_header_3d_20261107');TAGS={7:0,43:1,73:1,91:2,103:2,113:3};PAIRS=[(7,43),(73,91),(103,113)]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 tic=time.monotonic();reg=read(D/'registration.json');contract=read(D/'operator_contract.json')
 for p,h in {**reg['source_sha256'],**reg['mesh_sha256'],**contract['executed_source_sha256']}.items():assert sha(Path(p) if p.startswith('/') else R/p)==h,p
 patches=read(R/'data/nominal_gas_coupler_20261110/source_bare_column_subset.json')['patches'];data=np.load(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz',allow_pickle=False);meta=read(R/'data/v3_r32_global_surface_20261103/source_metadata.json')['faces'];nodes={};T={};region={}
 for i in range(4):
  for nid,xyz,t in zip(data[f'ceramic{i}_source_node_id_1based'],data[f'ceramic{i}_xyz_mm'],data[f'ceramic{i}_temperature_K']):
   k=int(nid);assert k not in nodes;nodes[k]=np.asarray(xyz);T[k]=float(t);region[k]=i
 tris=defaultdict(list);keys={}
 with (M/'R38_430_domains.1.face').open() as f:
  next(f)
  for row in f:
   z=row.split()
   if len(z)!=5 or int(z[-1]) not in TAGS:continue
   tid=int(z[0]);ns=tuple(map(int,z[1:4]));tag=int(z[4]);key=tuple(sorted(ns));assert key not in keys and all(n in nodes and region[n]==TAGS[tag] for n in ns);keys[key]=(tag,tid,ns);tris[tag].append((tid,ns))
 assert set(tris)==set(TAGS);adj=defaultdict(list)
 with (M/'R39_430_domains.1.ele').open() as f:
  next(f)
  for row in f:
   z=row.split()
   if len(z)!=6 or int(z[-1]) not in (1,2,3,4):continue
   ns=list(map(int,z[1:5]));rid=int(z[-1])-1
   for tri in combinations(ns,3):
    key=tuple(sorted(tri))
    if key in keys:adj[key].append((rid,next(v for v in ns if v not in tri)))
 orientation={};tridat={}
 for tag,items in tris.items():
  arr=[];orientation[tag]=[]
  for tid,ns in items:
   k=tuple(sorted(ns));assert len(adj[k])==1 and adj[k][0][0]==TAGS[tag],(tag,k,adj[k]);v=np.array([nodes[n] for n in ns]);opp=nodes[adj[k][0][1]];cross=np.cross(v[1]-v[0],v[2]-v[0]);assert abs(cross[2])>1e-14 and np.max(abs(v[:,2]-v[0,2]))<1e-8
   outward=-cross if np.dot(cross,opp-v[0])>0 else cross;sign=int(np.sign(outward[2]));assert sign==(1 if tag in (7,73,103) else -1),(tag,sign);orientation[tag].append(sign)
   xy=v[:,:2];arr.append({'id':tid,'nodes':ns,'xy':xy,'bounds':(xy[:,0].min(),xy[:,1].min(),xy[:,0].max(),xy[:,1].max())})
  tridat[tag]=arr
 out=[];cell_errors=[];arearows=[]
 def hit(a,b):return a[0]<b[2]-1e-12 and a[2]>b[0]+1e-12 and a[1]<b[3]-1e-12 and a[3]>b[1]+1e-12
 for stage,patch in enumerate(patches):
  ht,ct=PAIRS[stage];assert (patch['hot_gas_face_tag'],patch['cold_gas_face_tag'])==(ht,ct) and abs(patch['gap_m']-.0006)<1e-12
  total=0.
  for cellno,rect in enumerate(patch['cells_xy_mm']):
   rectpoly=[(rect[0],rect[1]),(rect[2],rect[1]),(rect[2],rect[3]),(rect[0],rect[3])];area=0.;hc=[t for t in tridat[ht] if hit(t['bounds'],rect)];cc=[t for t in tridat[ct] if hit(t['bounds'],rect)]
   for h in hc:
    hp=clip([tuple(z) for z in h['xy']],rectpoly)
    if centroid_area(hp)[0]==0:continue
    for c in cc:
     if not hit(h['bounds'],c['bounds']):continue
     p=clip(hp,[tuple(z) for z in c['xy']]);A,point=centroid_area(p)
     if A<=1e-14:continue
     wh=weights(h['xy'],point);wc=weights(c['xy'],point);assert abs(sum(wh)-1)<1e-12 and abs(sum(wc)-1)<1e-12
     out.append({'stage':stage,'cell':cellno,'area_mm2':A,'centroid_xy_mm':point,'gap_m':patch['gap_m'],'hot':{'face_tag':ht,'triangle_id':h['id'],'node_ids':h['nodes'],'weights':wh.tolist()},'cold':{'face_tag':ct,'triangle_id':c['id'],'node_ids':c['nodes'],'weights':wc.tolist()}});area+=A
   expected=(rect[2]-rect[0])*(rect[3]-rect[1]);cell_errors.append({'stage':stage,'cell':cellno,'expected_mm2':expected,'overlay_mm2':area,'error_mm2':area-expected});total+=area
  expected=patch['unobstructed_column_area_mm2'];arearows.append({'stage':stage,'face_tags':[ht,ct],'expected_area_mm2':expected,'overlap_area_mm2':total,'error_mm2':total-expected});print('AREA',json.dumps(arearows[-1]),flush=True)
 results={}
 for alpha in (.5,.8,1.):
  e=exchange(out,T,p=100,alpha=alpha);results[str(alpha)]={'stage_heat_hot_to_cold_W':e['stage_heat_hot_to_cold_W'],'global_heat_W':e['global_heat_W'],'entropy_generation_W_K':e['entropy_generation_W_K'],'sparse_node_load_W':{str(k):v for k,v in sorted(e['node_load_W'].items())},'pair_heat_hot_to_cold_W':e['pair_heat_hot_to_cold_W']}
 summary={'face_triangles':{str(k):len(v) for k,v in tris.items()},'ceramic_adjacent_tet_verified':len(keys),'outward_normal_sign':{str(k):orientation[k][0] for k in orientation},'overlay_pieces':len(out),'rectangles':len(cell_errors),'area_rows':arearows,'worst_cell_absolute_error_mm2':max(abs(x['error_mm2']) for x in cell_errors),'elapsed_s':time.monotonic()-tic}
 print('SUMMARY',json.dumps(summary),flush=True)
 result={'status':'PASS exact source TRI3 common-refinement geometry and discrete P1 load; physical gas law remains conditional' if all(abs(x['error_mm2'])<=reg['area_absolute_tolerance_mm2'] for x in arearows) and max(abs(x['error_mm2']) for x in cell_errors)<=reg['area_absolute_tolerance_mm2'] else 'FAIL area closure; source mesh does not cover registered rectangles','summary':summary,'cells':cell_errors,'pairs':out,'saved_field_results':results}
 (D/'p1_operator.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print('STATUS',result['status'],flush=True)
 if not result['status'].startswith('PASS'):raise SystemExit(2)
if __name__=='__main__':main()
