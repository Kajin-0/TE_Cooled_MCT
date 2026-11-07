#!/usr/bin/env python3
"""One registered original R3.9 Kovar-header 3D TIM + radiator reference condition.

Uniform hypothetical entire face2225 coated with a 0.1mm k=1 W/mK
TIM (local h=10000 W/m2K). Radiator R=2K/W to 300K ambient is
represented as a *separate lumped node*, not a second local surface h:
for fixed source Q, solve header Robin to zero sink-temperature-rise
then shift all temperatures by Q*R_radiator exactly. Nonuniform-contact
empirical correction factor is NOT additionally applied since full
header spatial spreading is resolved. No as-built or 430-domain claim.
"""
from pathlib import Path
import argparse,hashlib,json,time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from tecooledmct.materials import KOVAR

ROOT=Path(__file__).resolve().parents[1]
MESH=Path('/var/tmp/mct_r3_header_3d_20261107')
PATHS={'nodes':MESH/'R38_430_domains.1.node',
       'tets':MESH/'R39_430_domains.1.ele',
       'faces':MESH/'R38_430_domains.1.face'}
SOURCE=[
 ROOT/'data/v3_r3_header_spreading_20261107/attempt01/manifest.json',
 ROOT/'data/v3_r3_header_spreading_20261107/attempt01/result.json',
 ROOT/'data/v3_oem_sink_boundary_20261107/attempt01/boundary_evidence.json',
 ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json',
 ROOT/'tecooledmct/materials.py']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def solve(reg):
 start=time.monotonic()
 with PATHS['nodes'].open() as f:n=int(f.readline().split()[0])
 xyz=np.loadtxt(PATHS['nodes'],skiprows=1,usecols=(1,2,3))
 assert xyz.shape==(n,3)
 with PATHS['tets'].open() as f:m=int(f.readline().split()[0])
 tetarray=np.loadtxt(PATHS['tets'],skiprows=1,dtype=np.int32)
 assert tetarray.shape==(m,6)
 tets=tetarray[tetarray[:,5]==386,1:5]-1
 assert len(tets)==47702
 with PATHS['faces'].open() as f:nf=int(f.readline().split()[0])
 faces=np.loadtxt(PATHS['faces'],skiprows=1,dtype=np.int32)
 assert faces.shape==(nf,5)
 top=faces[faces[:,4]==2228,1:4]-1
 bottom=faces[faces[:,4]==2225,1:4]-1
 assert (len(top),len(bottom))==(1000,9617)
 used=np.unique(tets.ravel())
 index=np.full(len(xyz),-1,dtype=np.int32);index[used]=np.arange(len(used))
 t=index[tets];ft=index[top];fb=index[bottom]
 assert (t.min(),ft.min(),fb.min())>=(0,0,0)
 x=xyz[used]*1e-3
 n=len(x)
 vert=x[t]
 D=np.stack((vert[:,1]-vert[:,0],vert[:,2]-vert[:,0],vert[:,3]-vert[:,0]),axis=-1)
 det=np.linalg.det(D)
 assert np.all(det>0)
 vols=det/6
 inv=np.linalg.inv(D)
 grad=np.empty((len(t),4,3))
 grad[:,1:,:]=inv
 grad[:,0,:]=-inv.sum(axis=1)
 k=reg['header_k_W_mK']
 local=k*vols[:,None,None]*np.einsum('nik,njk->nij',grad,grad)
 def matrix(inds,vals,nd):
  return sp.coo_matrix((vals.ravel(),(np.repeat(inds,inds.shape[1],axis=1).ravel(),
    np.tile(inds,(1,inds.shape[1])).ravel())),shape=(nd,nd)).tocsr()
 K=matrix(t,local,n)
 def tri_area(inds):
  v=x[inds]
  return .5*np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)
 atop=tri_area(ft);abot=tri_area(fb)
 A_top=float(atop.sum());A_bottom=float(abot.sum())
 assert abs(A_top/37.21e-6-1)<.02
 assert abs(A_bottom/333.96069675687096e-6-1)<.02
 Q=reg['source_Q_W']
 rhs=np.bincount(ft.ravel(),weights=np.repeat(Q*atop/A_top/3,3),minlength=n)
 assert abs(rhs.sum()-Q)<1e-12
 h=reg['TIM_conductivity_W_mK']/reg['TIM_thickness_m']
 # Consistent, exactly integrated P1 triangle surface Robin matrix
 # h A/12 * [2 1 1; 1 2 1; 1 1 2].
 base=np.ones((3,3));np.fill_diagonal(base,2)
 H=matrix(fb,h*abot[:,None,None]*base[None,:,:]/12.,n)
 A=K+H
 tic=time.monotonic()
 diag=A.diagonal()
 assert np.min(diag)>0
 jacobi=spla.LinearOperator(A.shape,matvec=lambda z:z/diag)
 u,info=spla.cg(A,rhs,M=jacobi,rtol=1e-10,atol=1e-13,maxiter=4000)
 assert info==0,info
 # u: temp above *radiator* node, which itself is Q Rrad above 300 K.
 Rrad=reg['radiator_R_to_ambient_K_W']
 T_sink=300+Q*Rrad
 ttop=np.mean(u[ft],axis=1)
 tbot=np.mean(u[fb],axis=1)
 top_mean=float(atop@ttop/A_top)
 bottom_mean=float(abot@tbot/A_bottom)
 R=top_mean/Q
 Qlocal=h*abot*tbot
 Q_robin=float(Qlocal.sum())
 # independent surface reaction formulation (consistent full H)
 Q_matrix=float(np.ones(n)@(H@u))
 residual=A@u-rhs
 energy_volume=float(u@(K@u))
 energy_interface=float(u@(H@u))
 energy_input=float(u@rhs)
 assert abs(Q_robin-Q_matrix)<1e-11
 assert abs(energy_volume+energy_interface-energy_input)<1e-9
 assert abs(Q_robin/Q-1)<1e-8
 assert np.max(np.abs(residual))<1e-8
 legacy=read(ROOT/'data/v3_r3_header_spreading_20261107/attempt01/result.json')
 prevR=legacy['mean_face_temperature_weighted_effective_header_R_K_W']
 assert R>prevR,('Robin TIM must add face temperature cost')
 # In a series isothermal-interface approximation R_TIM=1/(h*A);
 # full 3D Robin solution should be close but not silently equated.
 ideal_R_TIM=1/(h*A_bottom)
 result={
  'status':'NUMERICAL PASS source R3.9 header single TIM Robin condition; EXTERNAL CONTACT/OEM AS-BUILT UNQUALIFIED',
  'physical_scenario':'full exposed original header underside uniformly coated with assumed grease; heat sink radiator is a separate lumped node',
  'source_header_volume_ID':386,'source_header_top_face_tag':2228,'source_header_bottom_face_tag':2225,
  'source_header_tetrahedra':int(len(t)),'source_header_nodes':int(n),
  'top_source_triangles':int(len(ft)),'bottom_TIM_triangles':int(len(fb)),
  'source_top_area_m2':A_top,'source_bottom_area_m2':A_bottom,
  'source_power_W':Q,'Kovar_k_W_mK':k,
  'reference_TIM_thickness_m':reg['TIM_thickness_m'],
  'reference_TIM_conductivity_W_mK':reg['TIM_conductivity_W_mK'],
  'reference_TIM_local_h_W_m2K':h,
  'reference_TIM_contact_area_assumption':'FULL source native CAD exterior face2225, not measured actual contact',
  'radiator_lumped_R_to_ambient_K_W':Rrad,
  'radiator_R_is_manufacturer_recommended_not_measured':True,
  'Kf_empirical_nonuniform_transfer_correction_not_applied':True,
  'radiator_node_temperature_K':T_sink,
  'source_contact_mean_temperature_K':T_sink+top_mean,
  'source_contact_min_temperature_K':float(T_sink+u[np.unique(ft.ravel())].min()),
  'source_contact_max_temperature_K':float(T_sink+u[np.unique(ft.ravel())].max()),
  'bottom_face_mean_T_above_radiator_K':bottom_mean,
  'header_plus_local_TIM_effective_R_K_W':R,
  'radiator_plus_header_plus_TIM_effective_R_K_W':R+Rrad,
  'prior_isothermal_full_bottom_header_R_K_W':prevR,
  'effect_of_finite_TIM_boundary_K_W':R-prevR,
  'uniform_one_dimensional_TIM_R_K_W':ideal_R_TIM,
  'sink_heat_integrated_W':Q_robin,
  'sink_heat_matrix_W':Q_matrix,
  'source_sink_relative_power_error':abs(Q_robin/Q-1),
  'max_absolute_all_node_heat_residual_W':float(np.max(np.abs(residual))),
  'bulk_gradient_energy_quadratic_WK':energy_volume,
  'TIM_interface_energy_quadratic_WK':energy_interface,
  'source_thermal_work_WK':energy_input,
  'discrete_energy_relative_error':abs(energy_volume+energy_interface-energy_input)/energy_input,
  'matrix_shape':[n,n],
  'runtime_s':time.monotonic()-tic,
  'single_original_mesh_not_h_converged':True,
  'not_full_430_domain_thermal_C_D':True,
  'geometry_and_source_mesh_unchanged':True,
  'actual_interface_bondline_or_contact_pressure_measured':False,
  'as_built_detector_temperature_qualified':False,
  'source_input_sha256':{str(f.relative_to(ROOT)):sha(f) for f in SOURCE},
  'source_extracted_mesh_sha256':{k:sha(v) for k,v in PATHS.items()},
  'source_solver_SHA256':sha(Path(__file__)),
  'preserved_legacy_gate_B':'FAIL/STOP',
  'preserved_prospective_P2':'STOP'}
 return result

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--registration',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 args=p.parse_args();reg=read(args.registration)
 assert reg['source_script_sha256']==sha(Path(__file__))
 assert reg['source_input_sha256']=={str(f.relative_to(ROOT)):sha(f) for f in SOURCE}
 assert reg['extracted_mesh_sha256']=={k:sha(v) for k,v in PATHS.items()}
 assert reg['single_registered_solve'] is True
 old=read(ROOT/'data/v3_r3_header_spreading_20261107/attempt01/result.json')
 assert abs(reg['source_Q_W']-old['source_power_W'])<1e-12
 r=solve(reg)
 if args.verify_only:
  saved=read(args.out)
  for k,v in r.items():
   if k=='runtime_s':continue
   if isinstance(v,float):assert abs(v-saved[k])<=max(1e-9*abs(v),1e-12),(k,v,saved[k])
   else:assert v==saved[k],k
 else:
  assert not args.out.exists()
  with args.out.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
 print('R3_TIM_ROBIN_RESULT',json.dumps({k:r[k] for k in
  ('source_header_tetrahedra','source_power_W','reference_TIM_local_h_W_m2K',
   'radiator_node_temperature_K','source_contact_mean_temperature_K',
   'header_plus_local_TIM_effective_R_K_W','radiator_plus_header_plus_TIM_effective_R_K_W',
   'effect_of_finite_TIM_boundary_K_W','source_sink_relative_power_error',
   'discrete_energy_relative_error','runtime_s')},indent=2))
if __name__=='__main__':main()
