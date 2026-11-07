#!/usr/bin/env python3
"""All 88 ORIGINAL R3.9 P/N conductor TET4 geometrical conductance.

On each intact P/N source region, solve -div(grad u)=0 with full original
leg/solder hot and cold native TRI3 face nodes Dirichlet 1/0, insulating
lateral exterior. 3D conductance G[metres] = energy for 1K and k=1;
compare to CAD A/L. Source geometry-only correction, not a thermoelectric
or measured material law. Never reclassify failed original Gate B.
"""
from pathlib import Path
import json,hashlib,argparse
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as sla
from scripts.v3_integrated_leg_resolved import find_leg_contact_source
ROOT=Path(__file__).resolve().parents[1]
MESH=Path('/var/tmp/mct_r3_header_3d_20261107')
PATHS={'node':MESH/'R38_430_domains.1.node','ele':MESH/'R39_430_domains.1.ele','face':MESH/'R38_430_domains.1.face'}
META=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(4<<20),b''):h.update(x)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def solve_case(reg):
 legs,_=find_leg_contact_source()
 ids={x['original_region_ID'] for x in legs}
 assert len(ids)==88
 meta=read(META)
 neighbors={}
 for ftag,f in meta['faces'].items():
  if f['class_']!='SOLID_SOLID':continue
  for x in f['owners']:
   if x in meta['domains'] and meta['domains'][x]['material'] in ('P','N'):
    other=[y for y in f['owners'] if y!=x]
    if len(other)==1 and meta['domains'][other[0]]['material']=='SnSb':
     neighbors.setdefault(x,{})[other[0]]=int(ftag)
 for leg in legs:
  name=leg['leg_name']
  assert len(neighbors[name])==2
  for side in ('hot','cold'):
   tag=neighbors[name][leg[side]['solder_source']]
   leg[side]['original_leg_to_solder_TRI3_face_tag']=tag
   assert abs(meta['faces'][str(tag)]['face_area_mm2']-.16)<1e-9
 with PATHS['node'].open() as f:
  n=int(next(f).split()[0])
 xyz=np.loadtxt(PATHS['node'],skiprows=1,usecols=(1,2,3))
 assert len(xyz)==n
 ele={}
 with PATHS['ele'].open() as f:
  assert int(next(f).split()[0])==1010119
  for line in f:
   q=line.split()
   if len(q)==6:
    r=int(q[-1])
    if r in ids:ele.setdefault(r,[]).append([int(y)-1 for y in q[1:5]])
 tags={x[side]['original_leg_to_solder_TRI3_face_tag'] for x in legs for side in ('hot','cold')}
 faces={}
 with PATHS['face'].open() as f:
  for line in f:
   q=line.split()
   if len(q)==5 and int(q[-1]) in tags:
    faces.setdefault(int(q[-1]),[]).append([int(y)-1 for y in q[1:4]])
 assert set(faces)==tags and len(tags)==176
 out=[]
 for leg in legs:
  rid=leg['original_region_ID'];cells=np.asarray(ele[rid],dtype=np.int32)
  unique=np.unique(cells)
  tolocal=np.full(n,-1,dtype=np.int32)
  tolocal[unique]=np.arange(len(unique))
  t=tolocal[cells];coords=xyz[unique]*1e-3
  points=coords[t]
  D=np.stack((points[:,1]-points[:,0],points[:,2]-points[:,0],
              points[:,3]-points[:,0]),axis=-1)
  det=np.linalg.det(D)
  assert det.min()>0,(rid,det.min())
  grads=np.empty((len(t),4,3))
  grads[:,1:]=np.linalg.inv(D)
  grads[:,0]=-grads[:,1:].sum(axis=1)
  kt=(det/6)[:,None,None]*np.einsum('eia,eja->eij',grads,grads)
  ni=len(unique)
  rows=np.repeat(t,4,axis=1).ravel()
  cols=np.tile(t,(1,4)).ravel()
  K=sp.coo_matrix((kt.ravel(),(rows,cols)),shape=(ni,ni)).tocsr()
  hot=leg['hot']['original_leg_to_solder_TRI3_face_tag']
  cold=leg['cold']['original_leg_to_solder_TRI3_face_tag']
  bh=np.unique(tolocal[np.asarray(faces[hot]).ravel()])
  bc=np.unique(tolocal[np.asarray(faces[cold]).ravel()])
  assert (bh>=0).all() and (bc>=0).all()
  assert len(set(bh)&set(bc))==0
  known=np.r_[bh,bc]
  values=np.r_[np.ones(len(bh)),np.zeros(len(bc))]
  u=np.zeros(ni)
  u[known]=values
  free=np.setdiff1d(np.arange(ni),known)
  if free.size:
   u[free]=sla.spsolve(K[free,:][:,free],-(K[free,:][:,known]@values))
  reaction=K@u
  power=float(u@(K@u))
  hotflow=float(reaction[bh].sum())
  coldflow=float(reaction[bc].sum())
  assert abs(power-hotflow)<1e-11
  assert abs(hotflow+coldflow)<1e-11
  assert abs(reaction[free]).max(initial=0)<1e-11
  A=leg['leg_cross_section_mm2']*1e-6
  L=leg['leg_length_mm']*1e-3
  G=A/L
  ratio=power/G
  assert .5<ratio<1.5,(rid,ratio)
  out.append({'source_chain_index':leg['source_series_chain_index'],
   'original_region_ID':rid,'stage':leg['stage'],
   'source_P_or_N':leg['material'],'source_name':leg['leg_name'],
   'original_TET4':len(t),'native_source_nodes':ni,
   'original_hot_leg_solder_face':hot,'original_cold_leg_solder_face':cold,
   'hot_terminal_nodes':len(bh),'cold_terminal_nodes':len(bc),
   'leg_CAD_A_over_L_m':G,
   'source_3D_unit_k_conductance_m':power,
   'source_3D_to_ideal_cuboid_geometry_factor':ratio,
   'full_source_3D_current_or_TE_PDE':'NOT RUN; unit scalar Laplace geometry only',
   'hot_normal_heat_for_unit_T_and_k_W':hotflow,
   'cold_normal_heat_for_unit_T_and_k_W':coldflow,
   'max_source_free_node_balance_W':float(abs(reaction[free]).max(initial=0))})
 assert len(out)==88 and sum(x['original_TET4'] for x in out)==7357
 ratios=np.array([x['source_3D_to_ideal_cuboid_geometry_factor'] for x in out])
 return {'status':'ORIGINAL 88 SOURCE P/N LEG 3D GEOMETRIC AXIAL UNIT CONDUCTANCE: source-CAD scalar thermal shape verified; NOT full coupled TE, not OEM prediction',
 'original_source_leg_count':88,'actual_original_TET4':7357,
 'source_leg_geometry_factors':out,
 'min_geometry_factor':float(ratios.min()),'max_geometry_factor':float(ratios.max()),
 'max_abs_deviation_from_1':float(max(abs(ratios-1))),
 'mean_geometry_factor':float(ratios.mean()),
 'source_original_P1_Gate_B':'FAIL/STOP',
 'full_original_430_domain_C_D':'NOT RUN',
 'mesh_changed':False,'material_laws_qualified':False,
 'source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in (META,DESIGN)},
 'original_mesh_sha256':{k:sha(v) for k,v in PATHS.items()},
 'script_sha256':sha(Path(__file__))}

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--registration',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 reg=read(a.registration)
 assert reg['source_script_sha256']==sha(Path(__file__))
 assert reg['source_mesh_sha256']=={k:sha(v) for k,v in PATHS.items()}
 assert reg['source_metadata_sha256']==sha(META)
 assert reg['source_design_sha256']==sha(DESIGN)
 assert reg['source_3D_88_unit_laplace_only'] and reg['one_original_mesh_no_refinement']
 r=solve_case(reg)
 assert not a.output.exists()
 a.output.write_text(json.dumps(r,indent=2)+'\n')
 print('SOURCE_88_PN_3D_GEOMETRIC',json.dumps({k:r[k] for k in (
  'status','actual_original_TET4','min_geometry_factor',
  'max_geometry_factor','max_abs_deviation_from_1','mean_geometry_factor')},indent=2))
if __name__=='__main__':main()
