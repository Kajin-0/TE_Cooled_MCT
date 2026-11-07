#!/usr/bin/env python3
"""ONE registered source-R3.9 Kovar-header-only P1 spreading calculation.

Only original CAD volume386 and original CAD faces2225/2228 are used.
Fixed T=300 K on ENTIRE original underside face2225, uniform positive
inward power from TEC at original top interface face2228, all other
external header faces insulated. No contact thermal resistance, no
source CAD/mesh edits, no coupled TEC physics, no reclassified Gate B.
Absolute temperature is 300+computed rise; source Q comes from the
previous conditional 29/11/4 reduced sink model (not a measurement).
"""
from pathlib import Path
import argparse,hashlib,json,time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from tecooledmct.materials import KOVAR

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('/var/tmp/mct_r3_header_3d_20261107')
MESH_INPUTS={
 'nodes':WORK/'R38_430_domains.1.node',
 'faces':WORK/'R38_430_domains.1.face',
 'tets':WORK/'R39_430_domains.1.ele'}
SOURCE=[
 ROOT/'data/v3_r38_global_tetgen_20261105/attempt01/manifest.json',
 ROOT/'data/v3_r39_quality_20261105/attempt01/manifest.json',
 ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json',
 ROOT/'data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json',
 ROOT/'data/v3_r3_sink_wire_20261107/attempt01/summary.json',
 ROOT/'tecooledmct/materials.py']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def load_tetgen():
 with MESH_INPUTS['nodes'].open() as f:
  n=int(f.readline().split()[0])
 xyz=np.loadtxt(MESH_INPUTS['nodes'],skiprows=1,usecols=(1,2,3),dtype=np.float64)
 assert xyz.shape==(n,3)
 with MESH_INPUTS['tets'].open() as f:
  m=int(f.readline().split()[0])
 # memory ~50MiB
 arr=np.loadtxt(MESH_INPUTS['tets'],skiprows=1,dtype=np.int32)
 assert arr.shape==(m,6)
 cand=arr[arr[:,5]==386][:,1:5]-1
 assert len(cand)==47702
 with MESH_INPUTS['faces'].open() as f:
  nf=int(f.readline().split()[0])
 face=np.loadtxt(MESH_INPUTS['faces'],skiprows=1,dtype=np.int32)
 assert face.shape==(nf,5)
 top=face[face[:,4]==2228][:,1:4]-1
 bottom=face[face[:,4]==2225][:,1:4]-1
 assert len(top)==1000 and len(bottom)==9617
 return xyz,cand,top,bottom

def solve(reg):
 xyz,tets,top,bottom=load_tetgen()
 q=reg['source_Q_W']
 k=reg['header_Kovar_bulk_proxy_W_mK']
 n_all=len(xyz)
 used=np.unique(tets.flatten())
 ix=np.full(n_all,-1,dtype=np.int32)
 ix[used]=np.arange(len(used),dtype=np.int32)
 assert ix[top].min()>=0 and ix[bottom].min()>=0
 p=xyz[used]*1e-3
 t=ix[tets];f_top=ix[top];f_bottom=ix[bottom]
 n=len(p)
 verts=p[t]
 D=np.stack((verts[:,1]-verts[:,0],verts[:,2]-verts[:,0],verts[:,3]-verts[:,0]),axis=-1)
 determinants=np.linalg.det(D)
 volumes=np.abs(determinants)/6.
 assert np.all(volumes>0)
 # All four gradients (rows) of barycentric coordinates, in 1/m
 g123=np.linalg.inv(D)
 g=np.empty((len(t),4,3),dtype=np.float64)
 g[:,1:,:]=g123
 g[:,0,:]=-g123.sum(axis=1)
 lhs=k*volumes[:,None,None]*np.einsum('nik,njk->nij',g,g)
 rows=np.repeat(t,4,axis=1).ravel()
 cols=np.tile(t,(1,4)).ravel()
 K=sp.coo_matrix((lhs.reshape(-1),(rows,cols)),shape=(n,n)).tocsr()
 K.sum_duplicates()
 def triangle_geometry(tris):
  x=p[tris]
  ar=np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1)*.5
  assert (ar>0).all()
  return ar
 a_top=triangle_geometry(f_top)
 a_bottom=triangle_geometry(f_bottom)
 area_top=a_top.sum();area_bottom=a_bottom.sum()
 # Native CAD reference: 37.21mm2 face2228, 333.96069675mm2
 # underside2225. Absolute triangulation deviations explicit.
 assert abs(area_top/37.21e-6-1)<.02
 assert abs(area_bottom/(333.96069675687096e-6)-1)<.02
 rhs=np.bincount(f_top.ravel(),weights=np.repeat(q*a_top/area_top/3,3),minlength=n)
 assert abs(rhs.sum()-q)<1e-12
 fixed=np.unique(f_bottom.ravel())
 isfixed=np.zeros(n,dtype=bool);isfixed[fixed]=True
 free=np.flatnonzero(~isfixed)
 assert len(free)>0 and len(fixed)>0
 tic=time.monotonic()
 # With zero temperature rise Dirichlet, solve SPD CG with Jacobi
 kff=K[free,:][:,free]
 pre=spla.LinearOperator(kff.shape,matvec=lambda z:z/kff.diagonal())
 z,info=spla.cg(kff,rhs[free],M=pre,rtol=1e-10,atol=1e-13,maxiter=3000)
 assert info==0,info
 T=np.zeros(n,dtype=float);T[free]=z
 residual=K@T-rhs
 Rbottom=float(residual[fixed].sum())
 free_absolute=np.max(np.abs(residual[free]))
 # Alternative independent physical energy identity:
 # Q = int volume k |grad T|² / mean T_contact, since bottom T=0
 conduction=float(T@(K@T))
 work=float(T@rhs)
 assert abs(conduction-work)<max(1e-9*work,1e-13)
 # Q-normalized face flux averaged temperature on source contact
 t_top=np.mean(T[f_top],axis=1)
 tbar=float(np.sum(a_top*t_top)/area_top)
 r_effective=tbar/q
 # Internal absolute gradient variation at contact is resolved only by
 # triangulated P1; report as such, not an OEM contact temperature.
 records={
  'status':'ONE-condition original R3.9 header-only P1 steady 3D conduction: NUMERICAL CHECKS PASS, PHYSICAL EXTERIOR BC HYPOTHETICAL',
  'model':'3D Kovar-only original source domain386, existing saved R3.9 430-domain tetra mesh',
  'original_CAD_Kovar_header_volume_ID':386,
  'original_top_source_face_tag':2228,
  'original_bottom_sink_face_tag':2225,
  'CAD_top_face_area_m2':37.21e-6,
  'CAD_bottom_face_area_m2':333.96069675687096e-6,
  'meshed_top_face_area_m2':float(area_top),
  'meshed_bottom_face_area_m2':float(area_bottom),
  'bulk_thermal_conductivity_hypothesis_W_mK':k,
  'bulk_material_assumption':'Kovar generic 293K proxy; as-built header alloy and k(T) NOT independently identified',
  'source_power_W':q,
  'source_power_origin':'previous conditional R3 nominal 0.4A 5K/W wires-ON reduced case, NOT physical product measurement',
  'sink_external_condition':'ENTIRE original header underside face2225 ideally held at 300 K; not the as-built clamped contact',
  'side_boundary_condition':'all other surfaces of original Kovar header region adiabatic',
  'upper_interface_condition':'uniform integrated Neumann input over all face2228 triangles, no composite Ni/solder/contact thermal impedance',
  'P1_tetrahedron_count':len(t),
  'P1_used_nodes':n,
  'P1_fixed_nodes':len(fixed),
  'P1_free_nodes':len(free),
  'top_source_face_TRI3':len(f_top),
  'bottom_isothermal_face_TRI3':len(f_bottom),
  'sum_volume_m3':float(volumes.sum()),
  'max_tetra_volume_m3':float(volumes.max()),
  'min_tetra_volume_m3':float(volumes.min()),
  'min_signed_jacobian_determinant_m3':float(determinants.min()),
  'negative_orientation_tet_count':int((determinants<0).sum()),
  'mean_heat_source_face_temperature_above_300K':tbar,
  'mean_hot_face_temperature_K':300+tbar,
  'max_hot_face_temperature_K':float(300+T[np.unique(f_top.ravel())].max()),
  'min_hot_face_temperature_K':float(300+T[np.unique(f_top.ravel())].min()),
  'max_all_header_temperature_K':float(300+T.max()),
  'mean_face_temperature_weighted_effective_header_R_K_W':r_effective,
  'total_Dirichlet_reaction_W':Rbottom,
  'source_sink_power_closure_relative':abs(Rbottom+q)/q,
  'max_free_node_absolute_heat_residual_W':float(free_absolute),
  'energy_quadratic_integral_WK':conduction,
  'energy_work_integral_WK':work,
  'energy_relative_work_closure':abs(conduction-work)/work,
  'solver_algorithm':'scipy CG Jacobi rtol1e-10; P1 Galerkin tetra constant k, no solver adaptivity',
  'solver_code':'scripts/v3_r3_header_one_condition.py',
  'solve_seconds':time.monotonic()-tic,
  'numerical_results_scope':'Single original source mesh; neither h-convergence nor 3D OEM physical validation',
  'physics_models_NOT_INCLUDED':['all TEC legs and interfaces','contact thermal resistance','Ni composite','In52Sn48 solder','Au composite','alumina','real fixture footprint','finite sink thermal impedance','radiation, cavity gas and Au/Cu heat leads'],
  'all_source_geometry_immutable':True,
  'original_Gate_B':'FAIL/STOP',
  'prospective_P2_gate':'STOP',
  '3D_full_430_domain_C_D':'NOT RUN',
  'source_input_sha256':{str(x.relative_to(ROOT)):sha(x) for x in SOURCE},
  'original_mesh_extracted_file_sha256':{k:sha(v) for k,v in MESH_INPUTS.items()},
 }
 assert records['source_sink_power_closure_relative']<1e-8
 assert records['energy_relative_work_closure']<1e-8
 assert tbar>0
 assert 300+T.min()>=300-1e-9
 return records

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--registration',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 a=p.parse_args()
 reg=read(a.registration)
 assert reg['one_condition_no_retry'] is True
 assert reg['original_mesh_sha256']=={k:sha(v) for k,v in MESH_INPUTS.items()}
 assert reg['source_code_sha256']==sha(Path(__file__))
 assert reg['source_input_sha256']=={str(x.relative_to(ROOT)):sha(x) for x in SOURCE}
 ref=read(ROOT/'data/v3_r3_sink_wire_20261107/attempt01/summary.json')
 case=next(v for v in ref['cases'] if v['hypothesis']=='nominal' and v['current_A']==.4 and v['sink_K_W']==5 and v['wires_mode']!='OFF')
 assert abs(reg['source_Q_W']-case['rejected_at_sink_W'])<1e-12
 o=solve(reg)
 if a.verify_only:
  archived=read(a.out)
  fixed={k:v for k,v in o.items() if k!='solve_seconds'}
  archive_fixed={k:v for k,v in archived.items() if k!='solve_seconds'}
  assert fixed.keys()==archive_fixed.keys()
  for k in fixed:
   if isinstance(fixed[k],float):assert abs(fixed[k]-archive_fixed[k])<=max(1e-10*abs(fixed[k]),1e-12),(k,fixed[k],archive_fixed[k])
   else:assert fixed[k]==archive_fixed[k],k
 else:
  assert not a.out.exists()
  with a.out.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
 print('R3_HEADER_ONE_CONDITION',json.dumps({k:o[k] for k in ('P1_tetrahedron_count','P1_used_nodes','mean_face_temperature_weighted_effective_header_R_K_W','mean_hot_face_temperature_K','max_hot_face_temperature_K','source_sink_power_closure_relative','energy_relative_work_closure','solve_seconds')},indent=2))
if __name__=='__main__':main()
