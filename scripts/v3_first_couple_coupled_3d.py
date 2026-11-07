#!/usr/bin/env python3
"""Prospective conditional 3D coupled TE on 9 ORIGINAL R3 conductor solids.

Source regions: leg0_N(5), solder0_hot/cold(6,7), leg1_P(8),
solder1_hot/cold(9,10), net0/1/2(269,270,271).
Uses ORIGINAL R3.9 1000 existing TET4 (no remesh), source TRI3
contact/cut face tags and region-disjoint P1 V,T traces.

Definitions:
    J = -sigma (gradV + S gradT)
    q = S T J - k gradT
    F = q + V J ; div J=div F=0.
An idealized zero-Seebeck finite interface uses:
    j_ab = (Va-Vb)/re
    F_ab = (Ta-Tb)/rt + 0.5*(Va+Vb)*j_ab.
Hence q_b-q_a=j_ab*(Va-Vb)>=0 and interface Joule release is
nonnegative, divided equally between adjacent material sides.
Seebeck-jump Peltier energy emerges from bulk q=STJ and total F
continuity, never by substituting q=Fourier alone.

At source cut current ports 1531/162, impose current density and
adiabatic HEAT q.n=0 => F.n=V J.n. T on ceramic-pad source faces
8,9,44 is IDEALIZED and physically unmeasured (no ceramics solved).

Keep historical Gate B FAIL/STOP and source 430/2440 transport UNSET.
This is ONE independently preregistered prospective *conditional*
coupled small-domain experiment, not production detector prediction.
"""
from pathlib import Path
import argparse,hashlib,json,time,collections,itertools
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from tecooledmct.graded_tec import props
from tecooledmct.v3_et_fem import laminate,LAYERS,PROPS

ROOT=Path(__file__).resolve().parents[1]
MESH=Path('/var/tmp/mct_r3_header_3d_20261107')
SOURCE_MESH={'nodes':MESH/'R38_430_domains.1.node',
             'faces':MESH/'R38_430_domains.1.face',
             'tets':MESH/'R39_430_domains.1.ele'}
SOURCE=[
 ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json',
 ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json',
 ROOT/'data/v3_tec_contact_scale_20261107/attempt01/conditional_contact_scale.json',
 ROOT/'data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json',
 ROOT/'data/g2c/zhang2025_he_40_300_v2.json',
 ROOT/'tecooledmct/graded_tec.py',
 ROOT/'tecooledmct/v3_et_fem.py',
 ROOT/'tecooledmct/material_profiles.py',
]
IDS=(5,6,7,8,9,10,269,270,271)
CONTACT_TAGS=(124,125,130,135,140,141,146,151)
HOT_TAGS=(8,9)
COLD_TAG=44
PORT_TAGS=(1531,162)

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())

def triplets(ids,local,n):
 # ids shape (m,nnode); local shape (m,nnode,nnode)
 d=ids.shape[1]
 return sp.coo_matrix((local.reshape(-1),
   (np.repeat(ids,d,axis=1).reshape(-1),
    np.tile(ids,(1,d)).reshape(-1))),shape=(n,n)).tocsr()

class Assembly:
 def __init__(self,reg):
  self.reg=reg
  src=read(SOURCE[0])
  assert len(src['domains'])==430 and len(src['faces'])==2440
  assert src['stage_leg_counts']=={'0':58,'1':22,'2':8}
  assert read(SOURCE[2])['source_SnSb_native_contact_faces']==352
  with SOURCE_MESH['nodes'].open() as f:nnode=int(f.readline().split()[0])
  xyz=np.loadtxt(SOURCE_MESH['nodes'],skiprows=1,usecols=(1,2,3))
  assert xyz.shape==(nnode,3)
  cells=[];regions=[]
  with SOURCE_MESH['tets'].open() as f:ntet=int(f.readline().split()[0])
  assert ntet==1010119
  with SOURCE_MESH['tets'].open() as f:
   next(f)
   for line in f:
    z=line.split()
    if int(z[-1]) in IDS:
     cells.append([int(x)-1 for x in z[1:5]])
     regions.append(int(z[-1]))
  self.region=np.array(regions,dtype=np.int32)
  self.cells=np.array(cells,dtype=np.int32)
  assert len(cells)==1000
  assert set(self.region)==set(IDS)
  refs=np.stack((np.repeat(self.region,4),self.cells.ravel()),axis=1)
  unique,rev=np.unique(refs,axis=0,return_inverse=True)
  self.trace=unique
  self.dof=rev.reshape(-1,4)
  self.ndof=len(unique)
  lookup={(int(r),int(v)):i for i,(r,v) in enumerate(unique)}
  self.lookup=lookup
  self.xyz=xyz*1e-3
  self.coord=self.xyz[self.cells]
  v=self.coord
  D=np.stack((v[:,1]-v[:,0],v[:,2]-v[:,0],v[:,3]-v[:,0]),axis=-1)
  det=np.linalg.det(D)
  assert np.min(det)>0,('Original source inverted TET4!',det.min())
  self.volume=det/6
  inv=np.linalg.inv(D)
  self.grad=np.empty((len(self.cells),4,3))
  self.grad[:,1:]=inv
  self.grad[:,0]=-inv.sum(axis=1)
  incidence=collections.defaultdict(list)
  for i,cell in enumerate(self.cells):
   for a in itertools.combinations(cell,3):
    incidence[tuple(sorted(int(t) for t in a))].append(i)
  assert max(len(a) for a in incidence.values())==2
  marker={}
  with SOURCE_MESH['faces'].open() as f:
   for line in f:
    z=line.split()
    if len(z)!=5 or not z[0].isdigit():continue
    key=tuple(sorted(int(t)-1 for t in z[1:4]))
    if key in incidence:
     assert key not in marker
     marker[key]=int(z[4])
  all_fac=[]
  for key,owners in incidence.items():
   if len(owners)==2 and self.region[owners[0]]==self.region[owners[1]]:
    continue
   assert key in marker,('Missing source face',key)
   tri=np.array(key,dtype=np.int32)
   area=.5*np.linalg.norm(np.cross(self.xyz[tri[1]]-self.xyz[tri[0]],
                                      self.xyz[tri[2]]-self.xyz[tri[0]]))
   assert area>0
   unordered_pair=tuple(int(self.region[i]) for i in owners)
   tag=marker[key]
   fsrc=src['faces'][str(tag)]
   # CRITICAL: original CAD face owner order, NOT tetrahedron iteration
   # order, defines one consistent outward direction for all triangles
   # on each physical contact. Mixed owner-order triangles would cancel
   # contact and raw currents even though the matrix is conservative.
   rpair=tuple(int(i) for i in fsrc['owner_volume_ids'] if i in IDS)
   assert len(rpair)==len(owners)
   assert set(rpair)==set(unordered_pair),(tag,rpair,unordered_pair)
   owners=tuple(next(int(e) for e in owners if self.region[e]==r)
                for r in rpair)
   da=np.array([lookup[(rpair[0],v)] for v in tri])
   db=np.array([lookup[(rpair[1],v)] for v in tri]) if len(owners)==2 else None
   all_fac.append(dict(tag=tag,global_nodes=tri,area=area,
                       owner_elements=owners,owner_regions=rpair,
                       da=da,db=db))
  self.facets=all_fac
  self.contact=[f for f in all_fac if f['db'] is not None]
  self.bound=[f for f in all_fac if f['db'] is None]
  assert set(f['tag'] for f in self.contact)==set(CONTACT_TAGS)
  assert len(self.contact)==112
  assert len(self.bound)==648
  for tag in CONTACT_TAGS+HOT_TAGS+(COLD_TAG,)+PORT_TAGS:
   face=[f for f in all_fac if f['tag']==tag]
   assert face,tag
   assert (tag in CONTACT_TAGS)==(face[0]['db'] is not None)
   total=sum(f['area'] for f in face)
   exact=src['faces'][str(tag)]['face_area_mm2']*1e-6
   assert abs(total/exact-1)<.015,(tag,total,exact)
  self.faces_by_tag={tag:[f for f in all_fac if f['tag']==tag]
                     for tag in CONTACT_TAGS+HOT_TAGS+(COLD_TAG,)+PORT_TAGS}
  self.fixed_temp={}
  for tag,temperature in ((8,reg['T_hot_K']),(9,reg['T_hot_K']),
                          (44,reg['T_cold_K'])):
   for f in self.faces_by_tag[tag]:
    for a in f['da']:
     if int(a) in self.fixed_temp:
      assert abs(self.fixed_temp[int(a)]-temperature)<1e-12
     self.fixed_temp[int(a)]=temperature
  self.fixed=np.array(sorted(self.fixed_temp),dtype=int)
  self.free=np.setdiff1d(np.arange(self.ndof),self.fixed)
  assert self.fixed.size>0 and self.free.size>0
  self.gauge=int(self.faces_by_tag[162][0]['da'][0])
  assert self.trace[self.gauge,0]==271
  self.vfree=np.setdiff1d(np.arange(self.ndof),[self.gauge])
  # Positive-exact TRI3 face matrices and four-point cubic quadrature.
  self.M=np.ones((3,3))+np.eye(3)
  self.quad=np.array([(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)])
  self.qwt=np.array([-27/48,25/48,25/48,25/48])
  assert abs(self.qwt.sum()-1)<1e-14
  assert np.allclose(self.quad.sum(axis=1),1)
  self.ke_solder=PROPS['SnSb'][0]
  self.kt_solder=PROPS['SnSb'][1]
  self.se=laminate(LAYERS,'electric','NOM')
  self.st=laminate(LAYERS,'thermal','NOM')
  self.cs=self.cells.shape[0]
  self.per_material=collections.Counter(int(r) for r in self.region)
  # Face contact matrix shared by both independent weak operators
  self.Kce=self.build_contact_matrix(reg['r_e_ohm_m2'])
  self.Kct=self.build_contact_matrix(reg['r_th_m2_K_W'])
  self.port_areas={tag:sum(f['area'] for f in self.faces_by_tag[tag])
                   for tag in PORT_TAGS}

 def build_contact_matrix(self,R):
  assert R>0
  rows=[];cols=[];vals=[]
  for f in self.contact:
   a,b=f['da'],f['db']
   M=f['area']/12*self.M/R
   ix=np.r_[a,b]
   L=np.block([[M,-M],[-M,M]])
   rows.extend(np.repeat(ix,6));cols.extend(np.tile(ix,6));vals.extend(L.ravel())
  return sp.coo_matrix((vals,(rows,cols)),shape=(self.ndof,self.ndof)).tocsr()

 def fields(self,T):
  te=np.mean(T[self.dof],axis=1)
  if not np.all(np.isfinite(te)) or te.min()<180 or te.max()>300:
   raise ValueError('Outside original measured-source P/N operation domain 180-300K: '+str((te.min(),te.max())))
  sig=np.zeros((self.cs,3,3));k=np.zeros_like(sig);S=np.zeros(self.cs)
  for r in IDS:
   idx=np.flatnonzero(self.region==r)
   if r in (5,8):
    material='N' if r==5 else 'P'
    p=props(material,te[idx])
    sig[idx]=np.eye(3)[None,:,:]*np.asarray(p['sigma'])[:,None,None]
    k[idx]=np.eye(3)[None,:,:]*np.asarray(p['k'])[:,None,None]
    S[idx]=np.asarray(p['S'])
   elif r in (6,7,9,10):
    sig[idx]=np.eye(3)/self.ke_solder
    k[idx]=np.eye(3)*self.kt_solder
   elif r in (269,270,271):
    sig[idx]=self.se
    k[idx]=self.st
   else:raise AssertionError(r)
  return sig,k,S,te

 def bulk(self,tensor):
  ke=self.volume[:,None,None]*np.einsum('eia,eab,ejb->eij',
                                         self.grad,tensor,self.grad)
  return triplets(self.dof,ke,self.ndof)

 def accumulate_cells(self,rows):
  b=np.zeros(self.ndof)
  np.add.at(b,self.dof.ravel(),rows.ravel())
  return b

 def source_load(self,I):
  b=np.zeros(self.ndof)
  for tag,sgn in ((1531,-1.),(162,+1.)):
   for f in self.faces_by_tag[tag]:
    jn=sgn*I/self.port_areas[tag]
    np.add.at(b,f['da'],np.repeat(-jn*f['area']/3,3))
  assert abs(b.sum())<1e-12
  return b

 def electric(self,T,I,sigma,S):
  gT=np.einsum('ei,eij->ej',T[self.dof],self.grad)
  btherm=self.accumulate_cells(self.volume[:,None]*
            np.einsum('eia,ea->ei',self.grad,np.einsum('eab,eb->ea',sigma,S[:,None]*gT)))
  A=self.bulk(sigma)+self.Kce
  rhs=self.source_load(I)-btherm
  vv=np.zeros(self.ndof)
  a=A[self.vfree][:,self.vfree].tocsc()
  vv[self.vfree]=splinalg_solve(a,rhs[self.vfree])
  r=A@vv-rhs
  max_e=float(np.abs(r[self.vfree]).max())
  return vv,max_e

 def current(self,V,T,sigma,S):
  gV=np.einsum('ei,eij->ej',V[self.dof],self.grad)
  gT=np.einsum('ei,eij->ej',T[self.dof],self.grad)
  J=-np.einsum('eab,eb->ea',sigma,gV+S[:,None]*gT)
  return J,gV,gT

 def interface_potential_flux_rhs(self,V):
  # ∫ N_i [(Va+Vb)/2] [(Va-Vb)/re] on original faces.
  rhs=np.zeros(self.ndof)
  r=self.reg['r_e_ohm_m2']
  contact_joule=0.
  for f in self.contact:
   va=V[f['da']];vb=V[f['db']]
   jm=self.quad@(va-vb)/r
   vm=self.quad@((va+vb)/2)
   h=f['area']*np.sum((self.qwt*jm*vm)[:,None]*self.quad,axis=0)
   np.add.at(rhs,f['da'],-h)
   np.add.at(rhs,f['db'],h)
   contact_joule+=f['area']*np.dot(self.qwt,jm*jm*r)
  return rhs,contact_joule

 def energy_rhs(self,V,T,J,S):
  vmax=np.mean(V[self.dof],axis=1)
  tmax=np.mean(T[self.dof],axis=1)
  F0=(vmax+S*tmax)[:,None]*J
  b=self.accumulate_cells(self.volume[:,None]*
      np.einsum('eia,ea->ei',self.grad,F0))
  cb,pcontact=self.interface_potential_flux_rhs(V)
  b+=cb
  # Physical thermal insulation on both current cut ports: q.n=0.
  # Hence total energy F.n=V jn, exactly integrated using TRI3 mass.
  power_boundary=0.
  for tag,sgn in ((1531,-1.),(162,+1.)):
   for f in self.faces_by_tag[tag]:
    vn=V[f['da']]
    jn=sgn*self.reg['current_A']/self.port_areas[tag]
    contrib=jn*f['area']/12*self.M@vn
    np.add.at(b,f['da'],-contrib)
    power_boundary+=float(np.sum(contrib))
  return b,pcontact,power_boundary

 def solve_temperature(self,V,T,J,thermal,S):
  K=self.bulk(thermal)+self.Kct
  b,pcontact,pport=self.energy_rhs(V,T,J,S)
  fixed_t=np.array([self.fixed_temp[i] for i in self.fixed])
  tnew=np.zeros(self.ndof)
  tnew[self.fixed]=fixed_t
  a=K[self.free][:,self.free].tocsc()
  rhs=b[self.free]-(K@tnew)[self.free]
  tnew[self.free]=splinalg_solve(a,rhs)
  return tnew,K,b,pcontact,pport

 def initialize(self):
  z=self.xyz[self.trace[:,1],2]
  # two-plate reference profile only to start a fixed-point solve
  h=self.reg['T_hot_K'];c=self.reg['T_cold_K']
  t=h-(z-.00208425)/(.00268425-.00208425)*(h-c)
  t=np.clip(t,c,h)
  for i,temp in self.fixed_temp.items():t[i]=temp
  return t

 def solve(self):
  I=self.reg['current_A']
  T=self.initialize()
  hist=[]
  last=None
  for it in range(1,self.reg['max_picard_steps']+1):
   sigma,thermal,S,tcell=self.fields(T)
   V,er=self.electric(T,I,sigma,S)
   J,gV,gT=self.current(V,T,sigma,S)
   tnew,K,b,pcontact,pport=self.solve_temperature(V,T,J,thermal,S)
   delta=float(np.max(np.abs(tnew-T)))
   assert np.isfinite(delta)
   hist.append({'step':it,'max_T_update_K':delta,'max_free_electric_weak_residual_A':er,
                'Tmax_K':float(tnew.max()),'Tmin_K':float(tnew.min())})
   if tnew.min()<self.reg['min_accepted_temperature_K'] or tnew.max()>self.reg['max_accepted_temperature_K']:
    raise ValueError('UNRELEASED/outside measured-domain thermal field '+str(hist[-1]))
   if delta <self.reg['temperature_picard_abs_tolerance_K']:
    T=tnew
    last='CONVERGED'
    break
   T=T+self.reg['picard_mix']*(tnew-T)
   for i,value in self.fixed_temp.items():T[i]=value
  if last is None:
   raise RuntimeError('Picard original budget exhausted: '+str(hist[-1]))
  sigma,thermal,S,te=self.fields(T)
  V,er=self.electric(T,I,sigma,S)
  J,gV,gT=self.current(V,T,sigma,S)
  tnew,K,b,pcontact,pport=self.solve_temperature(V,T,J,thermal,S)
  deviation=float(np.max(np.abs(tnew-T)))
  assert deviation<self.reg['temperature_picard_abs_tolerance_K']*5
  weak=K@T-b
  max_h=float(np.max(np.abs(weak[self.free])))
  # Dirichlet reaction from TOTAL energy weak residual:
  # energy residual R_F = b-KT, so fixed thermal sum equals
  # supplied electrical work - integral V jn on current ports.
  thermal_reaction=b-K@T
  Q_hot=float(np.sum(thermal_reaction[list(set(i for tag in HOT_TAGS for f in
                      self.faces_by_tag[tag] for i in f['da']))]))
  Q_cold=float(np.sum(thermal_reaction[list(set(i for f in
                      self.faces_by_tag[COLD_TAG] for i in f['da']))]))
  Pe=-pport
  # Independent electrical WORK identity derived from constitutive law:
  # P_terminal = integral rho : J J + integral S J.gradT
  #            + sum native-interface (DeltaV)^2/re.
  # This is NOT only I^2 R: the Seebeck transport work may be signed.
  inverse_sigma=np.linalg.inv(sigma)
  local_joule=np.einsum('ei,eij,ej->e',J,inverse_sigma,J)
  bulk_ohmic=float(self.volume @ local_joule)
  bulk_seebeck=float(self.volume @ (S*np.einsum('ei,ei->e',J,gT)))
  independent_power=bulk_ohmic+bulk_seebeck+pcontact
  work_error=abs(independent_power-Pe)/max(abs(Pe),1e-30)
  assert I>0
  assert work_error<self.reg['independent_electrical_work_relative_gate'],('Electrical work failed',work_error,bulk_ohmic,bulk_seebeck,pcontact,Pe)
  assert Pe>0,('This drive should draw power, not generator branch',Pe)
  portmean={}
  for tag in PORT_TAGS:
   A=self.port_areas[tag]
   portmean[str(tag)]=float(sum(f['area']*V[f['da']].mean() for f in self.faces_by_tag[tag])/A)
  rawcuts=[]
  for tag in CONTACT_TAGS:
   Ia=Ib=Icontact=0.
   for f in self.faces_by_tag[tag]:
    e0,e1=f['owner_elements']
    # Source owner side0, matching positive current into side1
    tri=f['global_nodes'];p=self.xyz[tri]
    normal=np.cross(p[1]-p[0],p[2]-p[0])*.5
    center=p.mean(axis=0)
    if np.dot(normal,center-self.coord[e0].mean(axis=0))<0:normal=-normal
    Ia+=float(J[e0]@normal)
    Ib+=float(J[e1]@(-normal))
    Icontact+=f['area']*float((V[f['da']]-V[f['db']]).mean())/self.reg['r_e_ohm_m2']
   # Each actual CAD solder contact is a mandatory series interface
   # between the two *mathematical* source cut current ports. Its
   # consistent signed finite-contact current MUST have |I|=drive I.
   weak_error=abs(abs(Icontact)-I)/I
   raw_error=max(abs(Ia-Icontact),abs(Ib+Icontact))/I
   rawcuts.append(dict(face_tag=tag,owners=list(self.faces_by_tag[tag][0]['owner_regions']),
      weak_contact_current_A=Icontact,weak_series_relative_error=weak_error,
      raw_side_a_out_A=Ia,raw_side_b_out_A=Ib,
      worst_raw_vs_contact_relative_current_error=raw_error))
  return {
   'status':'CONDITIONAL SOURCE ORIGINAL 9-DOMAIN 3D TE COUPLE, PROSPECTIVE NUMERICAL CHECKS',
   'current_A':I,'T_hot_ideal_K':self.reg['T_hot_K'],'T_cold_ideal_K':self.reg['T_cold_K'],
   'original_tet_count':len(self.cells),
   'source_region_cell_counts':dict(sorted(self.per_material.items())),
   'original_trace_DOF_per_field':self.ndof,
   'thermal_fixed_trace_DOF':len(self.fixed),
   'electric_potential_gauge_DOF':self.gauge,
   'source_original_internal_contact_TRI3_count':len(self.contact),
   'source_contact_tags':list(CONTACT_TAGS),
   'source_ceramic_hot_face_tags':list(HOT_TAGS),
   'source_ceramic_cold_face_tags':[COLD_TAG],
   'source_mathematical_electrical_cut_tags':list(PORT_TAGS),
   'current_port_face_areas_m2':{str(t):a for t,a in self.port_areas.items()},
   'T_global_min_max_K':[float(T.min()),float(T.max())],
   'T_cell_centroid_min_max_K':[float(te.min()),float(te.max())],
   'terminal_mean_potentials_V':portmean,
   'terminal_voltage_V':portmean['1531']-portmean['162'],
   'electric_power_from_faces_W':Pe,
   'interface_electrical_Joule_power_W':pcontact,
   'bulk_positive_Joule_power_W':bulk_ohmic,
   'bulk_signed_Seebeck_conversion_work_W':bulk_seebeck,
   'independent_electric_work_reconstruction_W':independent_power,
   'independent_electric_work_relative_error':work_error,
   'field_region_and_original_global_node':self.trace.tolist(),
   'field_potential_V':V.tolist(),
   'field_temperature_K':T.tolist(),
   'total_energy_thermal_reaction_hot_W':Q_hot,
   'total_energy_thermal_reaction_cold_W':Q_cold,
   'thermal_boundary_reaction_sum_W':Q_hot+Q_cold,
   'global_total_energy_conservation_error_W':Q_hot+Q_cold-Pe,
   'global_total_energy_conservation_rel':abs(Q_hot+Q_cold-Pe)/max(abs(Pe),1e-30),
   'final_electrical_free_node_residual_A':er,
   'final_energy_free_node_residual_W':max_h,
   'last_picard_fixed_point_difference_K':deviation,
   'picard_iterations':len(hist),
   'picard_iteration_log':hist,
   'native_source_P1_raw_contact_current_cuts':rawcuts,
   'worst_native_raw_current_discrepancy_fraction':max(x['worst_raw_vs_contact_relative_current_error'] for x in rawcuts),
   'worst_weak_series_interface_current_relative_error':max(x['weak_series_relative_error'] for x in rawcuts),
   'raw_gradient_contact_gate_0p1pct_PASS':all(x['worst_raw_vs_contact_relative_current_error']<=.001 for x in rawcuts),
   'raw_gradient_contact_failed_faces':sum(x['worst_raw_vs_contact_relative_current_error']>.001 for x in rawcuts),
   'original_historical_Gate_B':'FAIL/STOP',
   'full_original_430_domain_thermal_C_D':'NOT RUN',
   'source_430_2440_actual_constitutive_release':'UNSET',
   'source_CAD_and_original_global_mesh_modified':False,
   'manufactured_detector_temperature':'NOT PREDICTED',
   'real_physical_contact_laws':'UNKNOWN',
   'solver_method':'source TET4 P1 region-disjoint V and T traces, finite contact weak matrices; total energy F=q+VJ conservative Picard',
   'source_input_SHA256':{str(p.relative_to(ROOT)):sha(p) for p in SOURCE},
   'source_original_mesh_SHA256':{k:sha(p) for k,p in SOURCE_MESH.items()},
   'script_SHA256':sha(Path(__file__)),
  }

def json_source_scalar(x):
 if isinstance(x,np.generic):return x.item()
 raise TypeError('Unsupported JSON output type '+str(type(x)))

def splinalg_solve(a,b):
 out=spla.spsolve(a,b)
 if not np.all(np.isfinite(out)):raise ValueError('Sparse solve nonfinite result')
 return out

def run(reg,out,verify=False):
 assert reg['script_SHA256']==sha(Path(__file__))
 assert reg['source_input_SHA256']=={str(p.relative_to(ROOT)):sha(p) for p in SOURCE}
 assert reg['source_original_mesh_SHA256']=={k:sha(p) for k,p in SOURCE_MESH.items()}
 assert reg['source_9_region_ids']==list(IDS)
 assert reg['one_case_no_parameter_sweep'] is True
 tic=time.monotonic()
 a=Assembly(reg)
 o=a.solve()
 o['solve_wall_s']=time.monotonic()-tic
 assert o['final_electrical_free_node_residual_A']<reg['electrical_residual_gate_A']
 assert o['final_energy_free_node_residual_W']<reg['energy_residual_gate_W']
 assert o['global_total_energy_conservation_rel']<reg['energy_global_gate_relative']
 assert o['worst_weak_series_interface_current_relative_error']<reg['weak_interface_series_current_relative_gate']
 assert o['independent_electric_work_relative_error']<reg['independent_electrical_work_relative_gate']
 assert o['raw_gradient_contact_gate_0p1pct_PASS'] is False
 assert o['T_global_min_max_K'][0]>=reg['min_accepted_temperature_K']
 assert o['T_global_min_max_K'][1]<=reg['max_accepted_temperature_K']
 if verify:
  previous=read(out)
  for k,v in o.items():
   if k in ('solve_wall_s','picard_iteration_log','picard_iterations'):continue
   if isinstance(v,float):
    assert abs(v-previous[k])<=max(1e-8*abs(v),1e-11),(k,v,previous[k])
   else:assert v==previous[k],k
 else:
  assert not out.exists()
  payload=json.dumps(o,indent=2,default=json_source_scalar)+'\n'
  with out.open('x') as f:f.write(payload)
 print('R3_FIRST_COUPLE_COUPLED',json.dumps({
   k:o[k] for k in ('status','original_tet_count','original_trace_DOF_per_field',
   'T_global_min_max_K','terminal_voltage_V','electric_power_from_faces_W',
   'interface_electrical_Joule_power_W','total_energy_thermal_reaction_hot_W',
   'total_energy_thermal_reaction_cold_W',
   'global_total_energy_conservation_rel',
   'final_electrical_free_node_residual_A','final_energy_free_node_residual_W',
   'worst_native_raw_current_discrepancy_fraction',
   'worst_weak_series_interface_current_relative_error','picard_iterations',
   'solve_wall_s')},indent=2))
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--registration',type=Path,required=True)
 parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--verify-only',action='store_true')
 opts=parser.parse_args()
 run(read(opts.registration),opts.output,opts.verify_only)
if __name__=='__main__':main()
