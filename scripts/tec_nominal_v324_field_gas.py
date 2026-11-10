"""One-way per-cell gas subset from actual saved source-ceramic nodal fields."""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.spatial import cKDTree
from tecooledmct.nominal_gas_v324 import flux
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_coupler_20261110'
def read(p):return json.loads(p.read_text())
def main():
 src=read(D/'source_bare_column_subset.json');data=np.load(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz',allow_pickle=False);rows=[];summary={}
 for patch in src['patches']:
  j=patch['stage'];coords=[]
  for side,z,plate in [('hot',patch['z0_mm'],j),('cold',patch['z1_mm'],j+1)]:
   xyz=data[f'ceramic{plate}_xyz_mm'];mask=np.abs(xyz[:,2]-z)<1e-7
   assert mask.sum()>0,(plate,z);coords.append((xyz[mask],data[f'ceramic{plate}_temperature_K'][mask],data[f'ceramic{plate}_source_node_id_1based'][mask],cKDTree(xyz[mask,:2])))
  for cell in patch['cells_xy_mm']:
   x=(cell[0]+cell[2])/2;y=(cell[1]+cell[3])/2;area=(cell[2]-cell[0])*(cell[3]-cell[1]);nodes=[]
   for xyz,temperatures,ids,tree in coords:
    dist,index=tree.query([x,y]);nodes.append({'source_node_id_1based':int(ids[index]),'temperature_K':float(temperatures[index]),'nearest_xy_distance_mm':float(dist),'node_xyz_mm':xyz[index].tolist(),'weight':1.})
   qs={str(a):flux(nodes[0]['temperature_K'],nodes[1]['temperature_K'],area,patch['gap_m'],100.,a)['Q_hot_to_cold_W'] for a in (.5,.8,1.)}
   rows.append({'stage':j,'rect_xy_mm':cell,'area_mm2':area,'hot_face_tag':patch['hot_gas_face_tag'],'cold_face_tag':patch['cold_gas_face_tag'],'hot_ceramic_node_proxy':nodes[0],'cold_ceramic_node_proxy':nodes[1],'Q_hot_to_cold_W':qs})
 for key in ('0.5','0.8','1.0'):
  links=[sum(x['Q_hot_to_cold_W'][key] for x in rows if x['stage']==j) for j in range(3)];stage=[-links[0],links[0]-links[1],links[1]-links[2],links[2]];assert abs(sum(stage))<1e-15;summary[key]={'link_W':links,'stage_heat_into_ceramic_W':stage,'sum_W':sum(stage)}
 srcsha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();o={'status':'CONDITIONAL one-way subset on actual saved spatial source fields; nearest-node quadrature, not solved gas field or full device','source_field_sha256':srcsha(R/'data/tec_height_coupling_20261110/nominal/ceramic_fields.npz'),'subset_sha256':srcsha(D/'source_bare_column_subset.json'),'pressure_Pa':100.,'max_nearest_xy_distance_mm':max(max(x['hot_ceramic_node_proxy']['nearest_xy_distance_mm'],x['cold_ceramic_node_proxy']['nearest_xy_distance_mm']) for x in rows),'summary':summary,'cells':rows,'full_system_solves':0}
 p=D/'source_field_subset_exchange.json';assert not p.exists();p.write_text(json.dumps(o,indent=2,allow_nan=False)+'\n');print('count',len(rows),'max nearest mm',o['max_nearest_xy_distance_mm']);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
