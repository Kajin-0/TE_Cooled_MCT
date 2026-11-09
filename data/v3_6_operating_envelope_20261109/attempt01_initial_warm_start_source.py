#!/usr/bin/env python3
"""V3.6 current/load operating envelope using unchanged V3.5 geometry and physics.
This is a physically declared, area-scaled thermal proxy, not native
void-domain gas PDE or source full 430-domain radiation view factors.

Registered practical drive-current and detector-load conditions. Reuses V3 leg and original V2
ceramic meshes. Solves a fixed-point system of individual P/N leg nonlinear
axial transport and spatial ceramic thermal conduction with per-native-pad
nonuniform heat release. No P/N 3D electrical PDE or as-built validation.
"""
from pathlib import Path
import argparse,hashlib,json,time
from collections import defaultdict
import numpy as np
import scipy.sparse as sp
from scipy.optimize import least_squares
from scipy.sparse.linalg import splu
from tecooledmct.nonlinear_tec import leg
from tecooledmct.integrated_reference import Scenario,gas_transport,radiative_load
from scripts.v3_5_supply_lead_boundary import (evaluate as lead_eval, LEADS as LEADS, MODELS as LEAD_MODELS)
from scripts.v3_4_source_copper_multiport import (
 evaluate as copper_evaluate, PORTS as COPPER_PORTS, STAGES as COPPER_STAGES,
 SPEC as COPPER_SPEC, THERMAL_CONTACT_R_AREA_M2K_W,
 ELECTRICAL_CONTACT_R_AREA_OHM_M2)
from scripts.v3_integrated_leg_resolved import (
 find_leg_contact_source,contact_temperature_responses,
 read as read_v3,sha as sha_v3)
from scripts.v3_r3_sink_wire_sensitivity import geometry as original_geometry
from scripts.v2_source_ceramic_spatial import PATHS,FACE_SELECT,matrix
ROOT=Path(__file__).resolve().parents[1]
V31=ROOT/'data/v3_1_native_pad_feedback_20261107/attempt02/result.json'
JOINTS=ROOT/'data/v3_tec_contact_scale_20261107/attempt01/conditional_contact_scale.json'
V3=ROOT/'data/v3_integrated_leg_resolved_20261107/attempt01/result.json'
V2=ROOT/'data/v2_integrated_spatial_20261107/attempt02/v2_integrated_result.json'
V32=ROOT/'data/v3_2_joint_loss_feedback_20261107/attempt01/result.json'
META=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
SOURCE={
 'V3_working_baseline':V3,
 'V2_working_baseline':V2,
 'R3_original_CAD_tags':META,
 'original_824_body_design':ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json',
 'original_frozen_ceramic_FEM_source':ROOT/'scripts/v2_source_ceramic_spatial.py',
 'original_frozen_88_leg_source':ROOT/'scripts/v3_integrated_leg_resolved.py',
 'unchanged_TE_law':ROOT/'tecooledmct/nonlinear_tec.py',
 'unchanged_research_transport':ROOT/'tecooledmct/graded_tec.py',
 'wire_and_die_geometry':'',
}
SOURCE['wire_and_die_geometry']=ROOT/'scripts/v3_r3_sink_wire_sensitivity.py'
SOURCE['canonical_V3_1_baseline']=V31
SOURCE['source_SnSb_and_contact_scale']=JOINTS
SOURCE['V3_2_original_integrated_baseline']=V32
SOURCE['existing_verified_gas_radiation_operators']=ROOT/'tecooledmct/integrated_reference.py'
SOURCE['source_gas_NIST_property_operators']=ROOT/'tecooledmct/fem_g3b_exchange.py'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4<<20),b''):h.update(chunk)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())

class OriginalPlates:
 def __init__(self,legs):
  meta=read(META)
  self.legs=legs
  alltags={z for d in FACE_SELECT.values() for arr in d.values() for z in arr}
  with PATHS['node'].open() as f: n=int(next(f).split()[0])
  xyz=np.loadtxt(PATHS['node'],skiprows=1,usecols=(1,2,3))
  assert xyz.shape==(n,3)
  selected=defaultdict(list)
  with PATHS['ele'].open() as f:
   assert int(next(f).split()[0])==1010119
   for s in f:
    z=s.split()
    if len(z)==6 and int(z[-1]) in FACE_SELECT:
     selected[int(z[-1])].append([int(x)-1 for x in z[1:5]])
  original_faces=defaultdict(list)
  with PATHS['face'].open() as f:
   for s in f:
    z=s.split()
    if len(z)==5 and int(z[-1]) in alltags:
     original_faces[int(z[-1])].append([int(x)-1 for x in z[1:4]])
  assert set(original_faces)==alltags
  self.plates=[]
  for rid,group in FACE_SELECT.items():
   tets=np.asarray(selected[rid],dtype=np.int32)
   nodes=np.unique(tets.ravel());index=np.full(n,-1,dtype=np.int32)
   index[nodes]=np.arange(len(nodes))
   t=index[tets];coord=xyz[nodes]*1e-3
   c=coord[t];D=np.stack((c[:,1]-c[:,0],c[:,2]-c[:,0],c[:,3]-c[:,0]),axis=-1)
   det=np.linalg.det(D)
   assert np.min(det)>0
   vol=det/6
   grad=np.empty((len(t),4,3))
   grad[:,1:,:]=np.linalg.inv(D)
   grad[:,0,:]=-grad[:,1:,:].sum(axis=1)
   K=matrix(t,30*vol[:,None,None]*np.einsum('eia,eja->eij',grad,grad),len(nodes))
   tagloads={};tagareas={};tris={};areas={}
   for tag in group['top']+group['bottom']:
    tr=index[np.asarray(original_faces[tag],np.int32)]
    assert tr.min()>=0,(rid,tag)
    v=coord[tr];ar=.5*np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)
    assert np.min(ar)>0
    A=float(ar.sum());cad=meta['faces'][str(tag)]['face_area_mm2']*1e-6
    assert abs(A/cad-1)<.02
    tagloads[tag]=np.bincount(tr.ravel(),weights=np.repeat(ar/A/3,3),minlength=len(nodes))
    tagareas[tag]=A;tris[tag]=tr;areas[tag]=ar
   bot=group['bottom'];top=group['top']
   def area_vec(tags):
    weights=np.array([tagareas[z] for z in tags])
    return sum(tagloads[z]*tagareas[z] for z in tags)/weights.sum()
   bweight=area_vec(bot);tweight=area_vec(top)
   assert abs(bweight.sum()-1)<1e-10
   assert abs(tweight.sum()-1)<1e-10
   lu=splu(K[1:,1:].tocsc())
   # Solve source-tag Neumann spatial influence basis once, not a new
   # 3D PDE for each nonlinear residual evaluation. Tags and node IDs
   # identify original CAD mesh. Gauge is removed by subtracting lower
   # surface area mean.
   taglist=sorted(tagloads)
   rhs=np.stack([tagloads[z] for z in taglist],axis=1)
   basis=np.vstack([np.zeros((1,len(taglist))),lu.solve(rhs[1:])])
   basis-=bweight@basis
   patch={}
   for tag in taglist:
    patch[tag]=tagloads[tag]@basis
   patch_response=np.stack([patch[tag] for tag in taglist])
   self.plates.append(dict(region=rid,node_ids=nodes+1,xyz_mm=xyz[nodes],
    K=K,taglist=taglist,tagindex={z:i for i,z in enumerate(taglist)},
    basis=basis,tagloads=tagloads,tagareas=tagareas,
    tweight=tweight,bweight=bweight,patch_response=patch_response,
    top=top,bot=bot,volumes=len(t),source_triangle_count=sum(len(tris[z]) for z in taglist)))
  assert sum(x['volumes'] for x in self.plates)==11791
 def solve(self,leg_rows,stage,CuJoule,qcu,Qbath,Qa,external_ceramic_W=(0.,0.,0.,0.),metal_face_heat_W=None,lead_face_heat_W=None):
  # Native pad heat into each plate. Top surfaces generally receive
  # heat from the corresponding hot side; lower surfaces reject it
  # into the next TEC stage.
  inputs=[defaultdict(float) for _ in range(4)]
  for q in leg_rows:
   s=q['stage']
   inputs[s][q['hot_tag']]+=q['Qhot_W']
   inputs[s+1][q['cold_tag']]-=q['Qcold_W']
  # Model-form approximation: enclosure loads enter via the existing
  # real native upper metal-pad FEM basis, weighted by the native area.
  # Source-CAD exposed bare-ceramic/gas interfaces are NOT represented
  # by these pad triangles; no claim of resolved 3D surface HTC.
  assert len(external_ceramic_W)==4 and abs(external_ceramic_W[0])<1e-15
  for ci in (1,2,3):
   qext=float(external_ceramic_W[ci])
   pads=self.plates[ci]['top']
   areas=self.plates[ci]['tagareas']
   total=sum(areas[t] for t in pads)
   for tag in pads:inputs[ci][tag]+=qext*areas[tag]/total
  # On ceramic0, power-wire conduction plus 1/2 Cu Joule is the
  # actual source terminal correction. Place this on the original
  # circuit lead metallization face36, NOT uniformly on legs.
  if lead_face_heat_W is None:
   inputs[0][36]+=qcu+.5*CuJoule # V3.4 warm-start only, replaced on first iteration
  else:
   assert set(lead_face_heat_W)=={8,36}
   for tag,q in lead_face_heat_W.items():inputs[0][tag]+=float(q)
  if metal_face_heat_W:
   for tag,q in metal_face_heat_W.items():
    inputs[COPPER_STAGES[tag]][tag]+=float(q)
  # ceramic0 underside_Au original mounted sink face6
  inputs[0][6]-=Qbath
  # ceramic3 detector-facing Au finish original CAD face119
  inputs[3][119]+=Qa
  # Assumed zero at original connecting metal pad74 on ceramic1
  # (other interconnect contributions are unmodeled).
  out=[];offset={}
  for i,p in enumerate(self.plates):
   loads=inputs[i]
   assert set(loads).issubset(p['tagindex'])
   currents=np.array([loads.get(tag,0.) for tag in p['taglist']])
   imbalance=float(currents.sum())
   assert abs(imbalance)<5e-8,('CERAMIC_NET_FLUX_MISMATCH',i,imbalance)
   u=p['basis']@currents
   # Do NOT use gauge reaction to conceal flux imbalance: record
   # and verify exact original nodal surface weak balance.
   nodal=sum((p['tagloads'][z]*q for z,q in loads.items()),np.zeros(len(p['node_ids'])))
   assert abs(nodal.sum()-imbalance)<1e-12
   free_res=p['K']@u-nodal
   assert np.max(abs(free_res[1:]))<2e-8
   patchvals=p['patch_response']@currents
   top=(p['tweight']@u);bottom=(p['bweight']@u)
   assert abs(bottom)<1e-8
   for tag,val in zip(p['taglist'],patchvals):
    side='top' if tag in p['top'] else 'bottom'
    offset[tag]=float(val-(top if side=='top' else bottom))
   out.append({
    'index':i,'u':u,'heat_per_source_face_W':{str(k):float(v) for k,v in loads.items()},
    'top_minus_bottom_K':float(top-bottom),'total_flux_mismatch_W':imbalance,
    'free_thermal_residual_W':float(max(abs(free_res[1:]))),
    'heat_from_top_W':float(sum(loads.get(tag,0.) for tag in p['top'])),
    'heat_from_bottom_W':float(sum(loads.get(tag,0.) for tag in p['bot'])),
    'original_tets':p['volumes'],
    'source_contact_TRI3':p['source_triangle_count'],
    'num_surface_tags':len(p['taglist']),
    'max_patch_heat_abs_W':float(max(abs(currents)))})
  return out,offset

def expected(lead_alloy,lead_length_factor,Cu_contact_Rth,current_A,detector_heat_W):
 v3=read(V3)
 j=read(JOINTS)
 assert j['source_SnSb_joint_solids']==176 and j['source_SnSb_native_contact_faces']==352
 ret={'model':'V3.6 source-faithful TEC current and detector heat-load operating envelope',
 'parent_commit':'885c8d6bd717d41c8b67c7b760c1125feb30d69a',
 'source_3D_reference_baseline':'data/v3_2_joint_loss_feedback_20261107/attempt01/result.json',
 'gas_species':'Kr','gas_pressure_Pa':100.,'gas_gap_m':.003,
 'gas_accommodation':.8,'gas_area_scale':1.,
 'cap_gray_emissivity':.20,'ceramic_gray_emissivity':.8,
 'die_window_gray_emissivity':.10,
 'ceramic_view_factor':.5,'die_window_view_factor':.7,
 'original_CAD_ceramic_halfwidth_mm':[3.2,2.6,1.9,1.2],
 'original_CAD_die_width_mm':1.,
 'source_gas_radiation_contact_distribution':'ceramic1/2/3 exposed annular area source and die top effective-to-reservoir Q, applied through area weighted actual upper metallization native TRI3 pads as approximate proxy, NOT actual exposed outer ceramic face',
 'cavity_cap_and_window_temperature_K':300.,
 'gas_model':'existing NIST k 200/300/400K, Eucken lambda + two temperature jumps, explicit p=0 limit and above/below range labels',
 'gas_cavity_shape_is_native_3D_void':'NO, area gap and view assumptions only',
 'prior_running_V31':'data/v3_1_native_pad_feedback_20261107/attempt02/result.json',
 'solder_contact_Joule_placement':'both hot and cold solder joint bulk and two contacts, all electrical Joule deposited into corresponding source ceramic metal-pad, zero thermal contact temperature jumps by assumption',
 'unmeasured_hypothetical_contact_rho_e_ohm_m2':1e-11,
 'hypothetical_bulk_SnSb_rho_ohm_m':j['source_old_GateB_hypothetical_SnSb_bulk_electrical_rho_ohm_m'],
 'source_SnSb_joint_thickness_m':j['source_joint_thickness_mm']*1e-3,
 'source_SnSb_contact_face_area_m2':j['source_nominal_contact_area_per_face_mm2']*1e-6,
 'source_SnSb_joint_count':176,
 'source_SnSb_interface_count':352,
 'thermal_interface_R_and_SnSb_axial_k':'NOT ADDED THIS ITERATION',
 'current_A':float(current_A),'ambient_K':300.,'detector_heat_W':float(detector_heat_W),
 'contact_heat_mapping':'88 original source leg-solder-net-native ceramic face tag, nonuniform each individual leg P/N qh and qc, Cu lead+half-Joule original tag36, detector original tag119 and bottom mount face6',
 'actual_mesh_regions':[1,2,3,4],'original_source_ceramic_TET4':11791,
 'ceramic_k_proxy_W_mK':30.,'unmodeled_metal_joule_or_interface':'Other metal net and interface thermal contact not modeled; hypothetical original 176 SnSb bulk Joule and 352 electrical contact losses added only',
 'spatial_method':'per-native-source-pad Neumann P1 FEM superposition precomputed one time, fixed lower pad mean, iterative full TEC nonlinear axial transport and spatial ceramic thermal feedback',
 'source_3D_PN_electrical':'NOT RUN, source legs axial 1D nonlinear P/N',
 'nominal_research_transport_above_300K':'unmeasured extrapolation used',
 'one_operating_point_only':False,'operating_envelope_current_range_A':[0.15,0.60],'operating_envelope_detector_load_range_W':[0.001,0.008],
 'outer_steps_cap':26,'outer_thermal_field_tolerance_K':3e-7,
 'global_energy_tolerance_W':1e-8,'local_plate_net_heat_tolerance_W':5e-8,
 'individual_leg_energy_tolerance_W':1e-9,'inner_balance_tolerance_W':1e-8,
 'prior_v3_die_K':v3['detector_temperature_K'],
 'original_B':'FAIL/STOP','first_pair_raw_flux':'FAIL 8/8','full_430_C_D':'NOT RUN',
 'source_SHA256':{k:sha(v) for k,v in SOURCE.items()},
 'original_mesh_SHA256':{k:sha(v) for k,v in PATHS.items()},
 'script_SHA256':sha(Path(__file__))}
 ret.update({'source_Cu_multiport_geometry_sha256':sha(ROOT/'scripts/v3_4_source_copper_multiport.py'),
  'source_Cu_cad':{str(k):v for k,v in COPPER_SPEC.items()},
  'Cu_port_thermal_Rarea_m2K_W':THERMAL_CONTACT_R_AREA_M2K_W,
  'Cu_port_electrical_Rarea_ohm_m2':ELECTRICAL_CONTACT_R_AREA_OHM_M2,
  'Cu_port_mapping':{str(k):list(v) for k,v in COPPER_PORTS.items()},
  'selected_Cu_bulk_law':'rho293=1.724e-8 ohm*m, alpha=0.0039/K, k=385 W/m/K; unmeasured hypothetical; local face-coupled thermal multiport',
  'internal_form_tab_contact_thermopower':'NOT MODELED; joule allocated into contact-associated ceramic pad; isolated trace losses omitted',
  'source_copper_field':'1D centerline lumped multiport with thermal contact impedance, not full 3D metal current/thermal PDE',
  'v3_3_original_case_immutable':'data/v3_3_cavity_package_feedback_20261108/attempt02/result.json',
  'v3_4_original_case_immutable':'data/v3_4_copper_multiport_20261108/attempt03/result.json',
  'lead_alloy_scenario':lead_alloy,'lead_internal_path_length_factor':lead_length_factor,
  'lead_source_pins_and_pad_faces':{str(x['pin']):x['ceramic_face_tag'] for x in LEADS.values()},
  'lead_alloy_selected_properties':LEAD_MODELS,
  'source_separate_power_lead_script_sha256':sha(ROOT/'scripts/v3_5_supply_lead_boundary.py'),
  'Cu_port_thermal_Rarea_m2K_W':Cu_contact_Rth})
 assert lead_alloy in LEAD_MODELS and 0.5<=lead_length_factor<=3
 assert Cu_contact_Rth in (1e-6,1e-5,1e-4)
 assert .15<=current_A<=.60 and .001<=detector_heat_W<=.008
 return json.loads(json.dumps(ret))

def solve(reg):
 assert reg==expected(reg['lead_alloy_scenario'],reg['lead_internal_path_length_factor'],reg['Cu_port_thermal_Rarea_m2K_W'],reg['current_A'],reg['detector_heat_W'])
 tic=time.perf_counter()
 legs,_=find_leg_contact_source()
 spatial=OriginalPlates(legs)
 previous=read(ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json')
 geo=original_geometry()
 cu=[w for w in geo['wires'] if w['material']=='Cu']
 au=[w for w in geo['wires'] if w['material']=='Au']
 Gcu=sum(x['G_W_K'] for x in cu);Rcu=sum(x['R_ohm'] for x in cu)
 Gau=sum(x['G_W_K'] for x in au)
 assert len(cu)==len(au)==2
 A=geo['stages'][0]['leg_area_m2'];L=geo['stages'][0]['leg_length_m']
 dieR=geo['die_attach_thickness_over_area_m_inverse']
 Rext=read(V2)['hot_external_R_without_ceramic0_K_W']
 I=reg['current_A']
 A_joint=reg['source_SnSb_contact_face_area_m2']
 R_solder=reg['hypothetical_bulk_SnSb_rho_ohm_m']*reg['source_SnSb_joint_thickness_m']/A_joint
 R_interface=reg['unmeasured_hypothetical_contact_rho_e_ohm_m2']/A_joint
 R_joint=R_solder+2*R_interface
 P_joint=I*I*R_joint
 R_added=176*R_joint
 P_added=176*P_joint
 assert abs(R_added-0.028545)<1e-13,(R_added,R_joint)
 assert abs(P_added-I*I*R_added)<1e-13
 # Original legs are [58,22,8] across three stages, with two solder
 # joints per leg. Every original solder has exactly two contacts.
 stage_joints=[58,22,8]
 assert sum(stage_joints)==88
 def cavity_heating(temps):
  # Original CAD ceramic side lengths 5.2, 3.8, 2.4 mm;
  # rings are area-difference PROXIES for exposed upper cold plates.
  side=np.asarray([5.2,3.8,2.4],float)
  area=np.r_[(side[0]**2-side[1]**2),
              (side[1]**2-side[2]**2),
              (side[2]**2-1.**2),1.]*1e-6
  assert np.all(area>0) and abs(area.sum()-27.04e-6)<1e-12
  cold=np.array([temps[2],temps[4],temps[6],temps[7]])
  cfg=Scenario(gas=reg['gas_species'],cavity_pressure_pa=reg['gas_pressure_Pa'],
               accommodation=reg['gas_accommodation'])
  qgas=np.zeros(4);qrad=np.zeros(4);g_conductance=np.zeros(4)
  for i,(Aex,T) in enumerate(zip(area,cold)):
   avg=.5*(reg['ambient_K']+T)
   if reg['gas_pressure_Pa']>0:
    kg,jump,below=gas_transport(cfg,avg)
    g_conductance[i]=kg*Aex*reg['gas_area_scale']/(reg['gas_gap_m']+2*jump)
    qgas[i]=g_conductance[i]*(reg['ambient_K']-T)
   eps=(reg['die_window_gray_emissivity'] if i==3 else reg['cap_gray_emissivity'])
   view=(reg['die_window_view_factor'] if i==3 else reg['ceramic_view_factor'])
   qrad[i]=radiative_load(reg['ambient_K'],T,Aex,eps,
                       reg['ceramic_gray_emissivity'],view)
  return qgas,qrad,area,g_conductance
 def plus_solder_into_ceramic(rows):
  # spatial.solve removes Qcold from a cold ceramic. Subtracting
  # P_joint from Qcold adds one positive Joule source at that pad.
  # Hot solder deposits +P_joint at the opposite ceramic face.
  return [{**r,'Qhot_W':r['Qhot_W']+P_joint,
           'Qcold_W':r['Qcold_W']-P_joint} for r in rows]
 def powerleads(y):
  faceT={x['ceramic_face_tag']:float(y[0]+offset[x['ceramic_face_tag']])
         for x in LEADS.values()}
  return lead_eval(faceT,reg['lead_alloy_scenario'],
                   reg['lead_internal_path_length_factor'],
                   I,reg['ambient_K'])
 def copper(y):
  Tface={tag:float(y[2*COPPER_STAGES[tag]]+offset[tag])
         for tags in COPPER_PORTS.values() for tag in tags}
  return copper_evaluate(I,Tface,
    thermal_area_resistance=reg['Cu_port_thermal_Rarea_m2K_W'],
    electrical_area_resistance=reg['Cu_port_electrical_Rarea_ohm_m2'])
 n=previous['source_full_temperature_nodes_K']
 x=np.array([n[k] for k in ('stage0_hot','stage0_cold','stage1_hot','stage1_cold',
 'stage2_hot','stage2_cold','carrier','die')],float)
 # Initialize a complete 3D response using the actual V3 saved
 # per-leg heat rather than treating prior uniform pad flux as final.
 init_rows=[dict(stage=z['stage'],hot_tag=z['hot_tag'],
 cold_tag=z['cold_tag'],Qhot_W=z['Qhot_W'],
 Qcold_W=z['Qcold_W']) for z in previous['source_individual_leg_flux_and_electric_results']]
 s3=previous['source_stage_thermoelectric_budget']
 qcu=Gcu*(300-x[0]);CuJoule=I*I*Rcu
 Qbath=previous['bath_heat_rejected_W']
 Qa=(x[7]-x[6])/dieR
 fields,offset=spatial.solve(plus_solder_into_ceramic(init_rows),s3,CuJoule,qcu,Qbath,Qa,
   metal_face_heat_W={int(k):v for k,v in previous['Cu_form_tab_electrothermal_result']['heat_into_face_W'].items()},
   external_ceramic_W=[0.]+[a+b for a,b in zip(previous['cavity_gas_heat_into_three_ceramics_and_die_W'][:3],previous['gray_radiation_heat_into_three_ceramics_and_die_W'][:3])])
 # For each original ceramic solve, preserve the fully 3D computed
 # patch offset and through-plate mean drop. The leg transport then
 # updates every pad flux. This outer loop has no new parameters.
 hist=[]
 last=None
 for iteration in range(1,reg['outer_steps_cap']+1):
  gaps=np.array([f['top_minus_bottom_K'] for f in fields])
  th0=300+Rext*Qbath+gaps[0]
  x[0]=th0
  def model(y,include=False):
   stag=[dict(qh_w=0.,qc_w=0.,voltage_v=0.,joule_w=0.,energy_residual_w=0.,nlegs=0) for _ in range(3)]
   rows=[]
   for z in legs:
    s=z['stage'];hot_base=y[2*s];cold_base=y[2*s+1]
    hot=hot_base+offset[z['hot']['original_pad_face_tag']]
    cold=cold_base+offset[z['cold']['original_pad_face_tag']]
    pol=z['material']
    r=leg(pol,hot,cold,I/A*(1 if pol=='N' else -1),L,intervals=32,scales=(1.,1.,1.))
    qh=-A*r['q_hot_w_m2'];qc=-A*r['q_cold_w_m2']
    vol=r['electric_integral_v']*(1 if pol=='N' else -1)
    stag[s]['qh_w']+=qh;stag[s]['qc_w']+=qc;stag[s]['voltage_v']+=vol
    stag[s]['joule_w']+=A*r['joule_w_m2'];stag[s]['energy_residual_w']+=qh-qc-I*vol
    stag[s]['nlegs']+=1
    rows.append({'original_leg_name':z['leg_name'],'source_leg_ID':z['original_region_ID'],
    'stage':s,'material':pol,'hot_tag':z['hot']['original_pad_face_tag'],
    'cold_tag':z['cold']['original_pad_face_tag'],
    'Th_K':float(hot),'Tc_K':float(cold),'Qhot_W':float(qh),'Qcold_W':float(qc),
    'terminal_contribution_V':float(vol),'energy_residual_W':float(qh-qc-I*vol)})
   Qa=(y[7]-y[6])/dieR
   qgas,qrad,area,Ggas=cavity_heating(y)
   Qd=reg['detector_heat_W']+Gau*(reg['ambient_K']-y[7])+qgas[3]+qrad[3]
   lead=powerleads(y);qcu=lead['conduction_into_ceramic_W'];cuj=lead['joule_W']
   cm=copper(y)
   bath=stag[0]['qh_w']+lead['total_pad_heat_W']+stage_joints[0]*P_joint+cm['heat_into_ceramic_by_stage_W'][0]
   return stag,rows,Qa,Qd,qcu,cuj,bath,cm,lead
  def residual(y):
   st,rows,Qa,Qd,qcu,cuj,bath,cm,lead=model(y)
   qgas,qrad,areas,gcond=cavity_heating(y)
   qext=qgas+qrad
   return np.array([
    st[0]['qc_w']-st[1]['qh_w']-(stage_joints[0]+stage_joints[1])*P_joint-qext[0]-cm['heat_into_ceramic_by_stage_W'][1],
    st[1]['qc_w']-st[2]['qh_w']-(stage_joints[1]+stage_joints[2])*P_joint-qext[1]-cm['heat_into_ceramic_by_stage_W'][2],
    st[2]['qc_w']-Qa-stage_joints[2]*P_joint-qext[2],
    Qa-Qd,
    y[2]-y[1]-gaps[1],
    y[4]-y[3]-gaps[2],
    y[6]-y[5]-gaps[3],
    y[0]-300-Rext*bath-gaps[0]])
  weights=np.array([10.,10.,100.,100.,.1,.1,.1,.5])
  sol=least_squares(lambda y:weights*residual(y),x,bounds=(np.full(8,180.00001),np.full(8,389.99999)),
       x_scale=np.full(8,10.),max_nfev=45,
       ftol=1e-12,xtol=1e-12,gtol=1e-12)
  assert sol.success,sol.message
  x=sol.x
  st,rows,Qa,Qd,qcu,CuJoule,Qbath,cm,lead=model(x,True)
  qgas,qrad,exposed,Ggas=cavity_heating(x)
  local_fields,new_offsets=spatial.solve(plus_solder_into_ceramic(rows),st,CuJoule,qcu,Qbath,Qa,
        external_ceramic_W=np.r_[0.,(qgas+qrad)[:3]],
        metal_face_heat_W=cm['heat_into_face_W'],lead_face_heat_W=lead['face_heats_W'])
  new_gaps=np.array([f['top_minus_bottom_K'] for f in local_fields])
  max_offset=max(abs(new_offsets[k]-offset[k]) for k in offset)
  max_gaps=float(max(abs(new_gaps-gaps)))
  max_delta=max(max_offset,max_gaps)
  hist.append({'outer_iteration':iteration,'inner_evaluations':int(sol.nfev),
    'die_K':float(x[7]),'terminal_V':float(sum(z['voltage_v'] for z in st)+I*lead['total_R_ohm']+I*R_added+I*cm['total_electrical_R_ohm']),
    'spatial_pad_K_max_change':float(max_offset),
    'ceramic_total_Tdrop_K_max_change':float(max_gaps),
    'local_load_mismatch_W':float(max(abs(f['total_flux_mismatch_W']) for f in local_fields))})
  print('V3_4_OUTER_STEP',json.dumps(hist[-1]),flush=True)
  if max_delta<reg['outer_thermal_field_tolerance_K']:
   fields=local_fields;offset=new_offsets
   last='CONVERGED'
   break
  # Relax only spatial offsets/drop fields, not the physical source
  # load, to stabilize fixed-point iteration without altering laws.
  relax=.95
  offset={k:offset[k]*(1-relax)+new_offsets[k]*relax for k in offset}
  for i in range(4):
   fields[i]['top_minus_bottom_K']=fields[i]['top_minus_bottom_K']*(1-relax)+new_gaps[i]*relax
 if last is None:raise RuntimeError('V3.4 spatial feedback did not converge '+str(hist[-1]))
 # At convergence the final stored fields correspond to final leg
 # loads. Re-evaluate leg transport at those final actual pad fields.
 st,rows,Qa,Qd,qcu,CuJoule,Qbath,cm,lead=model(x,True)
 err=residual(x)
 assert max(abs(err[:4]))<reg['inner_balance_tolerance_W'], ('stage_final',err.tolist(),hist[-1])
 assert max(abs(err[4:]))<reg['outer_thermal_field_tolerance_K']
 assert max(abs(f['total_flux_mismatch_W']) for f in fields)<reg['local_plate_net_heat_tolerance_W']
 assert max(abs(z['energy_residual_W']) for z in rows)<reg['individual_leg_energy_tolerance_W']
 volt=sum(s['voltage_v'] for s in st)+I*lead['total_R_ohm']+I*R_added+I*cm['total_electrical_R_ohm'];power=I*volt
 qgas,qrad,exposed,Ggas=cavity_heating(x)
 energy=power+reg['detector_heat_W']+Gau*(reg['ambient_K']-x[7])+sum(qgas+qrad)+qcu-.5*CuJoule-Qbath
 assert abs(energy)<reg['global_energy_tolerance_W']
 # Unlike old V3: original spatial source patches carry actual
 # individual leg heat, original Cu pad36, die top tag119, and
 # original external header sink face6, not uniform assumed area.
 # Save all source mesh original node ID and spatial temperature.
 arrays={};plate=[]
 for i,f in enumerate(fields):
  p=spatial.plates[i]
  Tbase=(300+Rext*Qbath) if i==0 else x[2*i-1]
  arr=Tbase+f['u']
  arrays[f'ceramic{i}_source_node_id_1based']=p['node_ids']
  arrays[f'ceramic{i}_xyz_mm']=p['xyz_mm']
  arrays[f'ceramic{i}_temperature_K']=arr
  plate.append({k:v for k,v in f.items() if k!='u'}|
    {'min_T_K':float(arr.min()),'max_T_K':float(arr.max()),
     'bottom_mean_temperature_K':float(Tbase)})
 baseline=read(V3)
 out={
  'status':'V3.6 CONDITIONAL CURRENT-HEATLOAD WHOLE-DEVICE OPERATING POINT CONVERGED; 88-LEG/4-CERAMIC V3.5 PHYSICS, NOT 3D METAL PDE',
  'V3_2_historical_0p4A_reference_DIFFERENT_CURRENT_UNLESS_0p4A':{
    'V3_2_Tdie_K':read(V32)['calculated_detector_temperature_K'],
    'V3_4_minus_V3_2_Tdie_K':float(x[7]-read(V32)['calculated_detector_temperature_K']),
    'V3_2_Vterminal_V':read(V32)['terminal_voltage_V'],
    'V3_4_minus_V3_2_Vterminal_V':float(volt-read(V32)['terminal_voltage_V']),
    'V3_2_electrical_P_W':read(V32)['electrical_power_W'],
    'V3_4_minus_V3_2_electrical_P_W':float(power-read(V32)['electrical_power_W']),
    'V3_2_bath_Q_W':read(V32)['bath_heat_rejected_W'],
    'V3_4_minus_V3_2_bath_Q_W':float(Qbath-read(V32)['bath_heat_rejected_W'])},
  'cavity_gas_species':reg['gas_species'],
  'cavity_pressure_Pa':reg['gas_pressure_Pa'],
  'source_exposed_effective_surface_area_m2':exposed.tolist(),
  'gas_effective_conductance_W_K':Ggas.tolist(),
  'cavity_gas_heat_into_three_ceramics_and_die_W':qgas.tolist(),
  'gray_radiation_heat_into_three_ceramics_and_die_W':qrad.tolist(),
  'total_enclosure_heat_into_cold_device_W':float(sum(qgas+qrad)),
  'enclosure_reservoir_heat_rejected_W':float(-sum(qgas+qrad)),
  'source_3D_ceramic_gas_radiation_heat_spread':'approximate native pad area weighted from exposed ceramic top area proxy; NOT source bare ceramic true surface solution',
  'source_tec_power_leads':lead,
  'Cu_form_tab_electrothermal_result':cm,
  'Cu_form_tab_electrical_R_ohm':cm['total_electrical_R_ohm'],
  'Cu_form_tab_electrical_Joule_W':cm['total_electrical_power_W'],
  'Cu_form_tab_heat_into_ceramic_by_stage_W':cm['heat_into_ceramic_by_stage_W'],
  'source_joint_count':176,'original_source_SnSb_contact_count':352,
  'one_joint_series_resistance_ohm':float(R_joint),
  'source_total_solder_and_contact_series_resistance_ohm':float(R_added),
  'hypothetical_original_contact_rho_e_ohm_m2':reg['unmeasured_hypothetical_contact_rho_e_ohm_m2'],
  'source_SnSb_bulk_series_R_ohm':float(176*R_solder),
  'source_352_interface_series_R_ohm':float(352*R_interface),
  'source_joint_additional_terminal_V':float(I*R_added),
  'source_joint_additional_electrical_Joule_W':float(P_added),
  'source_solder_and_interface_energy_per_single_joint_pad_W':float(P_joint),
  'source_4_ceramic_distributed_joint_heating_W':[
   float(t*P_joint) for t in (58,80,30,8)],
  'source_contact_thermal_R':'NOT INCLUDED, no temperature jump at solder-metal leg interfaces',
  'V3_1_historical_0p4A_reference_DIFFERENT_CURRENT_UNLESS_0p4A':{
    'V3_1_die_T_K':read(V31)['calculated_detector_temperature_K'],
    'V3_2_minus_V3_1_die_K':float(x[7]-read(V31)['calculated_detector_temperature_K']),
    'V3_1_terminal_voltage_V':read(V31)['terminal_voltage_V'],
    'V3_2_minus_V3_1_voltage_V':float(volt-read(V31)['terminal_voltage_V']),
    'V3_1_electrical_power_W':read(V31)['electrical_power_W'],
    'V3_2_minus_V3_1_electrical_power_W':float(power-read(V31)['electrical_power_W']),
    'V3_1_bath_heat_W':read(V31)['bath_heat_rejected_W'],
    'V3_2_minus_V3_1_bath_heat_W':float(Qbath-read(V31)['bath_heat_rejected_W'])},
  'operating_current_A':I,'detector_imposed_heat_W':reg['detector_heat_W'],'source_stage_couples':[29,11,4],
  'source_individual_leg_count':len(rows),'original_ceramic_TET4':11791,
  'original_native_source_ceramic_pad_flux_by_face':plate,
  'source_individual_leg_flux_and_electric_results':rows,
  'source_stage_thermoelectric_budget':st,
  'source_full_temperature_nodes_K':dict(zip(['stage0_hot','stage0_cold','stage1_hot','stage1_cold','stage2_hot','stage2_cold','carrier','die'],map(float,x))),
  'calculated_detector_temperature_K':float(x[7]),
  'terminal_voltage_V':float(volt),'electrical_power_W':float(power),
  'bath_heat_rejected_W':float(Qbath),
  'detector_bond_heat_and_bias_W':float(Qd),
  'heat_Cu_lead_correction_W':float(qcu+.5*CuJoule),
  'source_power_lead_native_faces_W':lead['face_heats_W'],
  'global_thermoelectric_energy_residual_W':float(energy),
  'max_full_stage_conservation_residual_W':float(max(abs(err[:4]))),
  'max_mean_plate_temperature_residual_K':float(max(abs(err[4:]))),
  'max_native_plate_net_heat_imbalance_W':float(max(abs(f['total_flux_mismatch_W']) for f in fields)),
  'max_separate_leg_energy_residual_W':float(max(abs(z['energy_residual_W']) for z in rows)),
  'spatial_outer_iteration_history':hist,
  'outer_iterations':len(hist),
  'max_last_spatial_temperature_update_K':float(max_delta),
  'original_source_3D_ceramic_fields':'source_native_ceramics_V3_6.npz',
  'comparison_to_original_V3_historical_not_matched_except_0p4A':{'V3_detector_K':baseline['detector_temperature_K'],
    'delta_die_K':float(x[7]-baseline['detector_temperature_K']),
    'V3_terminal_voltage_V':baseline['terminal_voltage_V'],
    'delta_terminal_voltage_V':float(volt-baseline['terminal_voltage_V']),
    'V3_bath_heat_W':baseline['bath_heat_rejected_W'],
    'delta_bath_heat_W':float(Qbath-baseline['bath_heat_rejected_W'])},
  'spatial_PN_bulk_electrical_FEM':'NOT RUN',
  'solder_interfacial_Peltier_and_thermal_drop':'NOT RUN',
  'source_original_B':'FAIL/STOP','source_first_pair_raw_gradient':'FAIL 8/8',
  'full_original_430_domain_C_D':'NOT RUN',
  'matched_OEM_material_or_contacts':'UNAVAILABLE',
  'temperature_above_research_transport_300K':'ASSUMED CONTINUATION',
  'model_version_vs_material_physics':'V3.6 changes only prescribed drive current and detector load; P/N transport and material laws unchanged from V3.5',
  'source_CAD_and_original_mesh_modified':False,
  'source_original_older_V3_1_P1_gate':'UNCHANGED',
  'source_input_sha256':reg['source_SHA256'],
  'source_mesh_sha256':reg['original_mesh_SHA256'],
  'solver_source_sha256':reg['script_SHA256'],
  'solve_time_s':time.perf_counter()-tic}
 return out,arrays

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--registration',type=Path,required=True)
 p.add_argument('--outputdir',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 a=p.parse_args();reg=read(a.registration)
 assert reg==expected(reg['lead_alloy_scenario'],reg['lead_internal_path_length_factor'],reg['Cu_port_thermal_Rarea_m2K_W'],reg['current_A'],reg['detector_heat_W'])
 out,arrays=solve(reg)
 path=a.outputdir/'result.json'; field=a.outputdir/'source_native_ceramics_V3_6.npz'
 if a.verify_only:
  previous=read(path)
  for k,v in out.items():
   if k in ('solve_time_s',):continue
   if isinstance(v,float):assert abs(v-previous[k])<max(1e-8*abs(v),1e-10),k
   else:assert v==previous[k],k
  with np.load(field,allow_pickle=False) as loaded:
   assert set(loaded.files)==set(arrays)
   assert all(np.array_equal(loaded[k],v) for k,v in arrays.items())
 else:
  assert not path.exists() and not field.exists()
  path.write_text(json.dumps(out,indent=2)+'\n')
  np.savez_compressed(field,**arrays)
 print('V3_6_TEC_CURRENT_HEAT_LOAD_OPERATING_POINT',json.dumps({
  k:out[k] for k in ('status','calculated_detector_temperature_K',
  'terminal_voltage_V','electrical_power_W','bath_heat_rejected_W',
  'global_thermoelectric_energy_residual_W','max_native_plate_net_heat_imbalance_W',
  'outer_iterations','max_last_spatial_temperature_update_K','solve_time_s')},indent=2))
 print('V3_1_V3_DELTA',out['comparison_to_original_V3'])
if __name__=='__main__':main()
