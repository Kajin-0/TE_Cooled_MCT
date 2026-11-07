#!/usr/bin/env python3
"""V3.1 source-CAD 88-leg + four actual ceramic FEM local Neumann feedback.

One registered 0.4A operating condition. Reuses V3 leg and original V2
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
from scripts.v3_integrated_leg_resolved import (
 find_leg_contact_source,contact_temperature_responses,
 read as read_v3,sha as sha_v3)
from scripts.v3_r3_sink_wire_sensitivity import geometry as original_geometry
from scripts.v2_source_ceramic_spatial import PATHS,FACE_SELECT,matrix
ROOT=Path(__file__).resolve().parents[1]
V3=ROOT/'data/v3_integrated_leg_resolved_20261107/attempt01/result.json'
V2=ROOT/'data/v2_integrated_spatial_20261107/attempt02/v2_integrated_result.json'
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
 def solve(self,leg_rows,stage,CuJoule,qcu,Qbath,Qa):
  # Native pad heat into each plate. Top surfaces generally receive
  # heat from the corresponding hot side; lower surfaces reject it
  # into the next TEC stage.
  inputs=[defaultdict(float) for _ in range(4)]
  for q in leg_rows:
   s=q['stage']
   inputs[s][q['hot_tag']]+=q['Qhot_W']
   inputs[s+1][q['cold_tag']]-=q['Qcold_W']
  # On ceramic0, power-wire conduction plus 1/2 Cu Joule is the
  # actual source terminal correction. Place this on the original
  # circuit lead metallization face36, NOT uniformly on legs.
  inputs[0][36]+=qcu+.5*CuJoule
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

def expected():
 v3=read(V3)
 return {'model':'V3.1 original source 88 individual nonlinear P/N legs and full 4 ceramic 3D original native pad heat feedback, source 29/11/4 same .4A end to end case',
 'parent_commit':'e404b141d500550f041cad51f2fbbd636b3d83f8',
 'current_A':.4,'ambient_K':300.,'detector_heat_W':.002,
 'contact_heat_mapping':'88 original source leg-solder-net-native ceramic face tag, nonuniform each individual leg P/N qh and qc, Cu lead+half-Joule original tag36, detector original tag119 and bottom mount face6',
 'actual_mesh_regions':[1,2,3,4],'original_source_ceramic_TET4':11791,
 'ceramic_k_proxy_W_mK':30.,'unmodeled_metal_joule_or_interface':'NOT INCLUDED, conditional',
 'spatial_method':'per-native-source-pad Neumann P1 FEM superposition precomputed one time, fixed lower pad mean, iterative full TEC nonlinear axial transport and spatial ceramic thermal feedback',
 'source_3D_PN_electrical':'NOT RUN, source legs axial 1D nonlinear P/N',
 'nominal_research_transport_above_300K':'unmeasured extrapolation used',
 'one_operating_point_only':True,
 'outer_steps_cap':18,'outer_thermal_field_tolerance_K':2e-7,
 'global_energy_tolerance_W':1e-8,'local_plate_net_heat_tolerance_W':5e-8,
 'individual_leg_energy_tolerance_W':1e-9,'inner_balance_tolerance_W':1e-8,
 'prior_v3_die_K':v3['detector_temperature_K'],
 'original_B':'FAIL/STOP','first_pair_raw_flux':'FAIL 8/8','full_430_C_D':'NOT RUN',
 'source_SHA256':{k:sha(v) for k,v in SOURCE.items()},
 'original_mesh_SHA256':{k:sha(v) for k,v in PATHS.items()},
 'script_SHA256':sha(Path(__file__))}

def solve(reg):
 assert reg==expected()
 tic=time.perf_counter()
 legs,_=find_leg_contact_source()
 spatial=OriginalPlates(legs)
 previous=read(V3)
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
 n=previous['source_temperature_interface_means_K']
 x=np.array([n[k] for k in ('stage0_hot','stage0_cold','stage1_hot','stage1_cold',
 'stage2_hot','stage2_cold','carrier','die')],float)
 # Initialize a complete 3D response using the actual V3 saved
 # per-leg heat rather than treating prior uniform pad flux as final.
 init_rows=[dict(stage=z['stage'],hot_tag=z['original_hot_pad_tag'],
 cold_tag=z['original_cold_pad_tag'],Qhot_W=z['hot_heat_to_plate_W'],
 Qcold_W=z['cold_heat_from_plate_W']) for z in previous['source_individual_leg_temperature_and_flux_data']]
 s3=previous['source_individual_stage_energy_voltage_flux']
 qcu=Gcu*(300-x[0]);CuJoule=I*I*Rcu
 Qbath=s3[0]['qh_w']+qcu+.5*CuJoule
 Qa=(x[7]-x[6])/dieR
 fields,offset=spatial.solve(init_rows,s3,CuJoule,qcu,Qbath,Qa)
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
   Qa=(y[7]-y[6])/dieR;Qd=.002+Gau*(300-y[7])
   qcu=Gcu*(300-y[0]);cuj=I*I*Rcu
   bath=stag[0]['qh_w']+qcu+.5*cuj
   return stag,rows,Qa,Qd,qcu,cuj,bath
  def residual(y):
   st,rows,Qa,Qd,qcu,cuj,bath=model(y)
   return np.array([
    st[0]['qc_w']-st[1]['qh_w'],
    st[1]['qc_w']-st[2]['qh_w'],
    st[2]['qc_w']-Qa,
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
  st,rows,Qa,Qd,qcu,CuJoule,Qbath=model(x,True)
  local_fields,new_offsets=spatial.solve(rows,st,CuJoule,qcu,Qbath,Qa)
  new_gaps=np.array([f['top_minus_bottom_K'] for f in local_fields])
  max_offset=max(abs(new_offsets[k]-offset[k]) for k in offset)
  max_gaps=float(max(abs(new_gaps-gaps)))
  max_delta=max(max_offset,max_gaps)
  hist.append({'outer_iteration':iteration,'inner_evaluations':int(sol.nfev),
    'die_K':float(x[7]),'terminal_V':float(sum(z['voltage_v'] for z in st)+I*Rcu),
    'spatial_pad_K_max_change':float(max_offset),
    'ceramic_total_Tdrop_K_max_change':float(max_gaps),
    'local_load_mismatch_W':float(max(abs(f['total_flux_mismatch_W']) for f in local_fields))})
  print('V3_1_OUTER_STEP',json.dumps(hist[-1]),flush=True)
  if max_delta<reg['outer_thermal_field_tolerance_K']:
   fields=local_fields;offset=new_offsets
   last='CONVERGED'
   break
  # Relax only spatial offsets/drop fields, not the physical source
  # load, to stabilize fixed-point iteration without altering laws.
  relax=.7
  offset={k:offset[k]*(1-relax)+new_offsets[k]*relax for k in offset}
  for i in range(4):
   fields[i]['top_minus_bottom_K']=fields[i]['top_minus_bottom_K']*(1-relax)+new_gaps[i]*relax
 if last is None:raise RuntimeError('V3.1 spatial feedback did not converge '+str(hist[-1]))
 # At convergence the final stored fields correspond to final leg
 # loads. Re-evaluate leg transport at those final actual pad fields.
 st,rows,Qa,Qd,qcu,CuJoule,Qbath=model(x,True)
 err=residual(x)
 assert max(abs(err[:4]))<reg['inner_balance_tolerance_W'], ('stage_final',err.tolist(),hist[-1])
 assert max(abs(err[4:]))<reg['outer_thermal_field_tolerance_K']
 assert max(abs(f['total_flux_mismatch_W']) for f in fields)<reg['local_plate_net_heat_tolerance_W']
 assert max(abs(z['energy_residual_W']) for z in rows)<reg['individual_leg_energy_tolerance_W']
 volt=sum(s['voltage_v'] for s in st)+I*Rcu;power=I*volt
 energy=power+.002+Gau*(300-x[7])+qcu-.5*CuJoule-Qbath
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
  'status':'V3.1 SOURCE-CAD 88 LEG AND FOUR ORIGINAL 3D CERAMIC NATIVE PAD NONUNIFORM FLUX FEEDBACK CONVERGED; CONDITIONAL HYBRID, NOT FULL 430-DOMAIN',
  'operating_current_A':I,'source_stage_couples':[29,11,4],
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
  'global_thermoelectric_energy_residual_W':float(energy),
  'max_full_stage_conservation_residual_W':float(max(abs(err[:4]))),
  'max_mean_plate_temperature_residual_K':float(max(abs(err[4:]))),
  'max_native_plate_net_heat_imbalance_W':float(max(abs(f['total_flux_mismatch_W']) for f in fields)),
  'max_separate_leg_energy_residual_W':float(max(abs(z['energy_residual_W']) for z in rows)),
  'spatial_outer_iteration_history':hist,
  'outer_iterations':len(hist),
  'max_last_spatial_temperature_update_K':float(max_delta),
  'original_source_3D_ceramic_fields':'source_native_ceramics_V3_1.npz',
  'comparison_to_original_V3':{'V3_detector_K':baseline['detector_temperature_K'],
    'delta_die_K':float(x[7]-baseline['detector_temperature_K']),
    'V3_terminal_voltage_V':baseline['terminal_voltage_V'],
    'delta_terminal_voltage_V':float(volt-baseline['terminal_voltage_V']),
    'V3_bath_heat_W':baseline['bath_heat_rejected_W'],
    'delta_bath_heat_W':float(Qbath-baseline['bath_heat_rejected_W'])},
  'spatial_PN_bulk_electrical_FEM':'NOT RUN',
  'source_original_B':'FAIL/STOP','source_first_pair_raw_gradient':'FAIL 8/8',
  'full_original_430_domain_C_D':'NOT RUN',
  'matched_OEM_material_or_contacts':'UNAVAILABLE',
  'temperature_above_research_transport_300K':'ASSUMED CONTINUATION',
  'source_CAD_and_original_mesh_modified':False,
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
 assert reg==expected()
 out,arrays=solve(reg)
 path=a.outputdir/'result.json'; field=a.outputdir/'source_native_ceramics_V3_1.npz'
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
 print('V3_1_NONUNIFORM_CERAMIC_FEEDBACK',json.dumps({
  k:out[k] for k in ('status','calculated_detector_temperature_K',
  'terminal_voltage_V','electrical_power_W','bath_heat_rejected_W',
  'global_thermoelectric_energy_residual_W','max_native_plate_net_heat_imbalance_W',
  'outer_iterations','max_last_spatial_temperature_update_K','solve_time_s')},indent=2))
 print('V3_1_V3_DELTA',out['comparison_to_original_V3'])
if __name__=='__main__':main()
