#!/usr/bin/env python3
"""V2 coarse source-CAD spatial ceramic operator: 4 original 3D FEM plates.

One unit heat through each actual source ceramic, uniformly spread over
registered source metal contact patches; all other boundaries insulated.
Balanced Neumann solve with one gauge fixed, then bottom area-weighted
temperature zeroed. Returns effective top-bottom R [K/W] plus 3D node
profile for interpolation into the V2 29/11/4 coupled reduced system.
This is a spatial coarse HYBRID, not 430-domain coupled FEM.
"""
from pathlib import Path
import argparse,hashlib,json,time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
ROOT=Path(__file__).resolve().parents[1]
MESH=Path('/var/tmp/mct_r3_header_3d_20261107')
PATHS={'node':MESH/'R38_430_domains.1.node','ele':MESH/'R39_430_domains.1.ele',
       'face':MESH/'R38_430_domains.1.face'}
SOURCE=['data/v3_r32_global_surface_20261103/source_metadata.json',
        'data/v1_integrated_full_package_20261107/attempt01/result.json',
        'tecooledmct/materials.py']
FACE_SELECT={
 1:{'bottom':[6],'top':list(range(8,39))},
 2:{'bottom':list(range(44,73)),'top':list(range(74,87))},
 3:{'bottom':list(range(92,103)),'top':list(range(104,109))},
 4:{'bottom':list(range(114,118)),'top':[119]},
}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def matrix(ids,local,n):
 m=ids.shape[1]
 return sp.coo_matrix((local.ravel(),
   (np.repeat(ids,m,axis=1).ravel(),np.tile(ids,(1,m)).ravel())),
   shape=(n,n)).tocsr()

def build(reg):
 start=time.monotonic()
 m=read(ROOT/SOURCE[0]);assert len(m['domains'])==430
 assert reg['actual_original_region_ids']==[1,2,3,4]
 assert reg['source_face_tags']=={str(k):v for k,v in FACE_SELECT.items()}
 assert reg['k_Al2O3_proxy_W_mK']==30.
 for path,h in reg['source_sha256'].items():assert sha(ROOT/path)==h,path
 for key,h in reg['mesh_sha256'].items():assert sha(PATHS[key])==h,key
 with PATHS['node'].open() as f:nnode=int(f.readline().split()[0])
 xyz=np.loadtxt(PATHS['node'],skiprows=1,usecols=(1,2,3))
 assert xyz.shape==(nnode,3)
 with PATHS['ele'].open() as f:ntets=int(f.readline().split()[0])
 assert ntets==1010119
 selected={}
 with PATHS['ele'].open() as f:
  next(f)
  for line in f:
   z=line.split()
   if len(z)!=6:continue
   region=int(z[5])
   if region in FACE_SELECT:selected.setdefault(region,[]).append([int(x)-1 for x in z[1:5]])
 with PATHS['face'].open() as f:
  allfaces={}
  tags=set(x for info in FACE_SELECT.values() for v in info.values() for x in v)
  for line in f:
   z=line.split()
   if len(z)!=5:continue
   t=int(z[4])
   if t in tags:allfaces.setdefault(t,[]).append([int(x)-1 for x in z[1:4]])
 assert set(allfaces)==tags
 out=[];profiles={}
 for region,info in FACE_SELECT.items():
  tets=np.asarray(selected[region],dtype=np.int32)
  nodes=np.unique(tets.ravel())
  ix=np.full(nnode,-1,dtype=np.int32);ix[nodes]=np.arange(len(nodes))
  t=ix[tets];x=xyz[nodes]*.001
  p=x[t]
  D=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=-1)
  det=np.linalg.det(D)
  assert det.min()>0,(region,det.min())
  vol=det/6.
  g=np.empty((len(t),4,3));g[:,1:,:]=np.linalg.inv(D);g[:,0,:]=-g[:,1:,:].sum(axis=1)
  K=matrix(t,30.*vol[:,None,None]*np.einsum('eia,eja->eij',g,g),len(nodes))
  def surface(tags):
   f=np.vstack([allfaces[tag] for tag in tags])
   tri=ix[f];assert tri.min()>=0,(region,tags)
   v=x[tri]
   areas=.5*np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)
   assert areas.min()>0
   return tri,areas
  top,at=surface(info['top'])
  bot,ab=surface(info['bottom'])
  A_top=at.sum();A_bot=ab.sum()
  # Positive heat influx at top and removal from bottom.
  b=np.bincount(top.ravel(),weights=np.repeat(at/A_top/3.,3),minlength=len(nodes))
  b-=np.bincount(bot.ravel(),weights=np.repeat(ab/A_bot/3.,3),minlength=len(nodes))
  assert abs(b.sum())<1e-12
  gauge=0
  free=np.arange(1,len(nodes))
  kff=K[free,:][:,free]
  diag=kff.diagonal();assert diag.min()>0
  M=spla.LinearOperator(kff.shape,matvec=lambda v:v/diag)
  v,info_cg=spla.cg(kff,b[free],M=M,rtol=1e-11,atol=1e-13,maxiter=5000)
  assert info_cg==0,(region,info_cg)
  u=np.r_[0.,v]
  reaction=K@u-b
  assert abs(reaction[free]).max()<1e-9
  assert abs(reaction[gauge])<1e-8
  def avg(tri,a):
   return float(a@u[tri].mean(axis=1)/a.sum())
  up=avg(top,at);down=avg(bot,ab)
  R=up-down
  assert R>0
  energy=float(u@(K@u))
  work=float(u@b)
  assert abs(energy-work)<1e-8 and abs(work-R)<1e-8,(region,energy,work,R)
  u-=down
  # Store ORIGINAL global zero-based index and temperature response K/W.
  profiles[f'ceramic{region-1}_source_global_node_id_1based']=nodes.astype(np.int32)+1
  profiles[f'ceramic{region-1}_temperature_delta_over_bottom_mean_K_per_W']=u.astype(np.float64)
  profiles[f'ceramic{region-1}_source_xyz_mm']=xyz[nodes].astype(np.float32)
  out.append({
   'original_source_region_ID':region,
   'source_ceramic_name':f'ceramic{region-1}',
   'original_tets':len(t),'source_nodes':len(nodes),
   'source_top_face_tags':info['top'],'source_bottom_face_tags':info['bottom'],
   'source_top_contact_TRI3':len(top),'source_bottom_contact_TRI3':len(bot),
   'actual_mesh_top_contact_area_mm2':float(A_top*1e6),
   'actual_mesh_bottom_contact_area_mm2':float(A_bot*1e6),
   'measured_source_Al2O3_grade_k':'UNKNOWN',
   'assumed_constant_Al2O3_k_W_mK':30.,
   'spatial_T_top_minus_bottom_per_unit_heat_K_W':float(R),
   'bottom_flux_area_mean_temperature_delta_K_per_W':float(avg(bot,ab)),
   'top_flux_area_mean_temperature_delta_K_per_W':float(avg(top,at)),
   'min_node_delta_above_bottom_mean_K_per_W':float(u.min()),
   'max_node_delta_above_bottom_mean_K_per_W':float(u.max()),
   'source_sink_integrated_heat_W':[1.,-1.],
   'max_free_residual_W':float(abs(reaction[free]).max()),
   'absolute_fixed_node_reaction_W':float(abs(reaction[gauge])),
   'weak_energy_vs_work_relative':float(abs(energy-work)/energy),
   'source_region_volume_mm3':float(vol.sum()*1e9)
  })
 report={
  'status':'FOUR ORIGINAL SOURCE-CAD CERAMIC 3D STEADY THERMAL RESPONSE OPERATORS PASS; ONE UNIT FLUX PER PLATE, CONDITIONAL k',
  'scope':'11,791 original R3.9 tetrahedral cells across 4 ceramics; balanced source-native pad surface Neumann heat, zero flux elsewhere; integrated only via equivalent delta T',
  'face_source':'original R3.8 source 3D TRI3 tags',
  'meshing':'exact saved R3.9 TET4; no remesh, one source mesh only, NOT h-converged',
  'unit_total_heat_W':1.,
  'source_3D_ceramic_regions':out,
  'integrated_reduced_electrical_model':'not solved in this step; linked by V2 integrated source in next phase',
  'temperature_response_profiles_NPZ':'ceramic_spatial_profiles.npz',
  'source_sha256':reg['source_sha256'],
  'original_mesh_sha256':reg['mesh_sha256'],
  'solver_script_sha256':sha(Path(__file__)),
  'original_P1_Gate_B':'FAIL/STOP',
  'full_430_C_D':'NOT RUN',
  'recorded_runtime_s':time.monotonic()-start
 }
 assert sum(v['original_tets'] for v in out)==11791
 return report,profiles

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--registration',type=Path,required=True)
 p.add_argument('--outdir',type=Path,required=True)
 a=p.parse_args();r=read(a.registration)
 assert r['source_script_sha256']==sha(Path(__file__))
 assert r['one_registered_3D_operator_per_plate'] is True
 rep,profiles=build(r)
 assert not (a.outdir/'ceramic_spatial_operators.json').exists()
 assert not (a.outdir/'ceramic_spatial_profiles.npz').exists()
 (a.outdir/'ceramic_spatial_operators.json').write_text(json.dumps(rep,indent=2)+'\n')
 np.savez_compressed(a.outdir/'ceramic_spatial_profiles.npz',**profiles)
 print('V2_3D_CERAMIC_OPERATORS',json.dumps({
 'tets':sum(v['original_tets'] for v in rep['source_3D_ceramic_regions']),
 'R_plate_K_W':[v['spatial_T_top_minus_bottom_per_unit_heat_K_W'] for v in rep['source_3D_ceramic_regions']],
 'max_free_residual_W':max(v['max_free_residual_W'] for v in rep['source_3D_ceramic_regions']),
 'seconds':rep['recorded_runtime_s']},indent=2))
if __name__=='__main__':main()
