#!/usr/bin/env python3
"""V3 WORKING leg-resolved spatial hybrid, original 88 CAD P/N legs.

Retains V2 four original-source 3D ceramic FEM response fields, same 0.4 A
full 29/11/4 system, detector, metal power/Au bond wires and header/TIM.
Maps all 88 source leg -> two solder solids -> actual metal net -> exact
native ceramic CAD face tag; computes metal patch mean temperature from
original 3D FEM TRI3 and unit-flux nodal temperatures. Feeds its spatial
offset into one unchanged nonlinear conservative 32-slice TE solve PER
ACTUAL P/N LEG. Simultaneously solves 8 mean temperature and 4 interplate
heat flows. This is NOT a 3D P/N electric/heat PDE: leg transport remains
axial and each source ceramic uses V2's uniform patch-total flux response.
"""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,hashlib,json,time
import numpy as np
from scipy.optimize import least_squares
from tecooledmct.nonlinear_tec import leg
from scripts.v3_r3_sink_wire_sensitivity import geometry as original_geometry

ROOT=Path(__file__).resolve().parents[1]
MESH_FACE=Path('/var/tmp/mct_r3_header_3d_20261107/R38_430_domains.1.face')
V2=ROOT/'data/v2_integrated_spatial_20261107/attempt02/v2_integrated_result.json'
CER=ROOT/'data/v2_integrated_spatial_20261107/attempt01/ceramic_spatial_operators.json'
FIELD=ROOT/'data/v2_integrated_spatial_20261107/attempt01/ceramic_spatial_profiles.npz'
META=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
SOURCES={
 'V2_full_result':V2,'original_3D_ceramic_operator':CER,
 'saved_original_ceramic_field':FIELD,
 'original_430_domain_face_owner_metadata':META,
 'original_824_body_design':DESIGN,
 'original_1D_TE_transport':ROOT/'tecooledmct/nonlinear_tec.py',
 'original_PN_source_transport':ROOT/'tecooledmct/graded_tec.py',
 'V2_source_geometry':ROOT/'scripts/v3_r3_sink_wire_sensitivity.py',
 'V2_nonlinear_integrator':ROOT/'scripts/v2_integrated_spatial_hybrid.py',
 'V2_hot_side_reference':ROOT/'data/v3_header_tim_robin_20261107/attempt01/result.json',
}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())

def find_leg_contact_source():
 """Original CAD graph; no geometric nearest-neighbor guessing."""
 meta=read(META);dom=meta['domains'];faces=meta['faces']
 adj=defaultdict(set);pad_faces={}
 for text_tag,f in faces.items():
  if f['class_']!='SOLID_SOLID':continue
  a,b=f['owners']
  adj[a].add(b);adj[b].add(a)
  if (a.startswith('ceramic') and dom[b]['material']=='COMPOSITE_MULTILAYER'):
   key=(a,b)
  elif (b.startswith('ceramic') and dom[a]['material']=='COMPOSITE_MULTILAYER'):
   key=(b,a)
  else:continue
  assert key not in pad_faces
  pad_faces[key]=int(text_tag)
 design=read(DESIGN)
 bodies={b['name']:b for b in design['bodies']}
 out=[]
 for name,v in dom.items():
  if v['material'] not in ('P','N'):continue
  assert name in bodies and bodies[name]['stage']==v['stage']
  stage=v['stage']
  sold=[q for q in adj[name] if dom[q]['material']=='SnSb']
  assert len(sold)==2,(name,sold)
  contact={}
  for s in sold:
   nets=[net for net in adj[s] if net!=name and dom[net]['material']=='COMPOSITE_MULTILAYER']
   assert len(nets)==1,(name,s,nets)
   net=nets[0]
   ceramic=[n for n in adj[net] if n.startswith('ceramic')]
   assert len(ceramic)==1,(name,net,ceramic)
   c=ceramic[0]
   idx=int(c.removeprefix('ceramic'))
   side='hot' if idx==stage else 'cold' if idx==stage+1 else None
   assert side is not None,(name,stage,c)
   tag=pad_faces[(c,net)]
   contact[side]={'solder_source':s,'metal_net_source':net,
                  'ceramic_source':c,'original_pad_face_tag':tag,
                  'original_source_CAD_area_mm2':faces[str(tag)]['face_area_mm2']}
  assert set(contact)=={'hot','cold'},name
  box=bodies[name]['bbox_mm']
  loc=[(box[0]+box[3])/2,(box[1]+box[4])/2]
  out.append({'leg_name':name,'original_region_ID':v['id'],
      'material':v['material'],'stage':stage,
      'source_series_chain_index':bodies[name]['chain_index'],
      'xy_center_mm':loc,'leg_length_mm':box[5]-box[2],
      'leg_cross_section_mm2':(box[3]-box[0])*(box[4]-box[1]),
      **contact})
 out.sort(key=lambda x:x['source_series_chain_index'])
 assert len(out)==88
 assert [x['source_series_chain_index'] for x in out]==list(range(88))
 assert Counter(x['stage'] for x in out)=={0:58,1:22,2:8}
 assert Counter(x['material'] for x in out)=={'N':44,'P':44}
 assert all(abs(x['leg_length_mm']-.5)<1e-12 and abs(x['leg_cross_section_mm2']-.16)<1e-12 for x in out)
 return out,meta

def contact_temperature_responses():
 """Exact TRI3 area-mean on the physical ceramic–metal CAD faces."""
 legs,meta=find_leg_contact_source()
 originals=read(CER)['source_3D_ceramic_regions']
 assert [x['original_source_region_ID'] for x in originals]==[1,2,3,4]
 tags={item[side]['original_pad_face_tag']:(item['stage']+(side=='cold')) for item in legs for side in ('hot','cold')}
 assert len(tags)>=40
 faces=defaultdict(list)
 with MESH_FACE.open() as f:
  for line in f:
   z=line.split()
   if len(z)!=5:continue
   t=int(z[-1])
   if t in tags:faces[t].append([int(x) for x in z[1:4]])
 assert set(faces)==set(tags),(len(faces),len(tags))
 result={}
 with np.load(FIELD,allow_pickle=False) as fp:
  for tag,ceramic in sorted(tags.items()):
   stem=f'ceramic{ceramic}'
   ids=fp[stem+'_source_global_node_id_1based']
   values=fp[stem+'_temperature_delta_over_bottom_mean_K_per_W']
   xyz=fp[stem+'_source_xyz_mm']
   tri=np.asarray(faces[tag],int)
   index=np.searchsorted(ids,tri)
   assert index.max()<len(ids) and np.array_equal(ids[index],tri),(tag,ceramic)
   xyztri=xyz[index].astype(float)*1e-3
   area=.5*np.linalg.norm(np.cross(xyztri[:,1]-xyztri[:,0],xyztri[:,2]-xyztri[:,0]),axis=1)
   assert min(area)>0
   A=float(sum(area))
   cad=meta['faces'][str(tag)]['face_area_mm2']*1e-6
   assert abs(A/cad-1)<.02,(tag,A,cad)
   patch=float(area@values[index].mean(axis=1)/A)
   result[tag]={'ceramic_index':ceramic,'original_triangle_count':len(tri),
      'source_CAD_contact_area_mm2':float(cad*1e6),
      'meshed_contact_area_mm2':float(A*1e6),
      'unit_heat_patch_mean_K_per_W':patch,
      'unit_heat_global_top_reference_K_per_W':originals[ceramic]['top_flux_area_mean_temperature_delta_K_per_W'],
      'unit_heat_global_bottom_reference_K_per_W':originals[ceramic]['bottom_flux_area_mean_temperature_delta_K_per_W']}
 for l in legs:
  for side in ('hot','cold'):
   t=l[side]['original_pad_face_tag']
   z=result[t]
   ref=z['unit_heat_global_top_reference_K_per_W'] if side=='hot' else z['unit_heat_global_bottom_reference_K_per_W']
   l[side]['relative_local_offset_K_per_W']=z['unit_heat_patch_mean_K_per_W']-ref
   l[side]['original_contact_TRI3']=z['original_triangle_count']
 return legs,result

def expected_registration():
 baseline=read(V2)
 return {
  'version':'V3 first source-resolved 88-leg local ceramic contact temperatures + existing 32-interval nonlinear P/N stages, same .4A complete package',
  'parent_commit':'7426b9cda14950a714cea71050bffd81ac81f174',
  'source_operating_point':{'current_A':.4,'ambient_K':300.,'die_heat_W':.002,'optical_heat_W':0.,
    'die_attach_k_W_mK':1.,'cavity_gas_and_radiation':'OFF'},
  '88_leg_mapping':'exact original native leg-solder-metal-ceramic face graph, no nearest-neighbor guesses',
  'local_T_from_3D':'exact TRI3-area-mean original ceramic 3D unit heat field on actual metal contact face, subtract respective all-pad area mean, scale by same ceramic through-heat',
  'ceramic_heat_distribution_assumption':'V2 frozen uniform total heat per respective source metal pad area; leg-specific heat redistribution NOT yet solved as a spatial source term',
  'stage_couples':[29,11,4],
  'leg_transport':'unchanged Zhang2025 unmatched 40-300K P and N nonlinear, 32 axial intervals and >300K assumed continuation; each leg individual hot/cold boundary',
  'spatial_3D_PN_bulk_current_PDE':'NOT RUN',
  'full_430_coupled_3D_C_D':'NOT RUN',
  'first_pair_P1_raw_contact':'FAIL 8/8',
  'original_P1_Gate_B':'FAIL/STOP',
  'one_operating_point_only':True,
  'max_allowed_global_energy_residual_W':1e-8,
  'max_allowed_individual_leg_energy_residual_W':1e-9,
  'max_allowed_interface_temperature_closure_K':1e-7,
  'max_allowed_stage_heat_balance_W':1e-8,
  'baseline_V2_die_K':baseline['full_detector_die_temperature_K'],
  'source_sha256':{k:sha(v) for k,v in SOURCES.items()},
  'original_R3_face_mesh_sha256':sha(MESH_FACE),
  'source_script_sha256':sha(Path(__file__)),
 }

def solve_case(reg):
 assert reg==expected_registration()
 tic=time.perf_counter()
 legs,patches=contact_temperature_responses()
 v2=read(V2)
 geometry=original_geometry()
 assert [s['couples'] for s in geometry['stages']]==[29,11,4]
 copper=[w for w in geometry['wires'] if w['material']=='Cu']
 gold=[w for w in geometry['wires'] if w['material']=='Au']
 assert len(copper)==len(gold)==2
 Gcu=sum(w['G_W_K'] for w in copper)
 Rau=sum(w['R_ohm'] for w in copper)
 Gau=sum(w['G_W_K'] for w in gold)
 I=.4;A=geometry['stages'][0]['leg_area_m2'];L=geometry['stages'][0]['leg_length_m']
 assert all(abs(g['leg_area_m2']-A)<1e-15 and abs(g['leg_length_m']-L)<1e-15 for g in geometry['stages'])
 R=np.asarray([s['source_3D_operator_R_K_W'] for s in v2['source_original_four_ceramics_spatial_summaries']])
 Rext=v2['hot_external_R_without_ceramic0_K_W']
 die_R=geometry['die_attach_thickness_over_area_m_inverse']
 assert abs(die_R-20)<1e-12
 # V2-like temperature nodes, plus four independent plate heat powers.
 n=v2['temperature_interface_nodes_K']
 temp0=np.array([n[k] for k in ('TEC_hot_contact','stage0_cold_ceramic1_lower',
 'stage1_hot_ceramic1_upper','stage1_cold_ceramic2_lower','stage2_hot_ceramic2_upper',
 'stage2_cold_ceramic3_lower','carrier_ceramic3_upper','HgCdTe_die')],float)
 q0=np.asarray(v2['source_four_ceramic_heat_W'],float)
 x0=np.r_[temp0,q0]
 def evaluate(x,details=False):
  temps=x[:8];powers=x[8:]
  boundaries=[(temps[0],temps[1]),(temps[2],temps[3]),(temps[4],temps[5])]
  stage=[dict(qh_w=0.,qc_w=0.,voltage_v=0.,joule_w=0.,energy_residual_w=0.,
       min_leg_T_K=999.,max_leg_T_K=0.,source_leg_count=0) for _ in range(3)]
  rows=[]
  for z in legs:
   s=z['stage']
   th=boundaries[s][0]+powers[s]*z['hot']['relative_local_offset_K_per_W']
   tc=boundaries[s][1]+powers[s+1]*z['cold']['relative_local_offset_K_per_W']
   polarity=z['material']
   res=leg(polarity,th,tc,I/A*(1 if polarity=='N' else -1),L,
           intervals=32,scales=(1.,1.,1.))
   hot=-A*res['q_hot_w_m2']
   cold=-A*res['q_cold_w_m2']
   v=res['electric_integral_v']*(1 if polarity=='N' else -1)
   energy=hot-cold-I*v
   stage[s]['qh_w']+=hot
   stage[s]['qc_w']+=cold
   stage[s]['voltage_v']+=v
   stage[s]['energy_residual_w']+=energy
   stage[s]['joule_w']+=A*res['joule_w_m2']
   stage[s]['source_leg_count']+=1
   stage[s]['min_leg_T_K']=min(stage[s]['min_leg_T_K'],th,tc)
   stage[s]['max_leg_T_K']=max(stage[s]['max_leg_T_K'],th,tc)
   if details:
    rows.append({
     'original_source_leg_ID':z['original_region_ID'],
     'source_name':z['leg_name'],'source_material':polarity,
     'stage':s,'source_chain_index':z['source_series_chain_index'],
     'source_xy_center_mm':z['xy_center_mm'],
     'original_hot_pad_tag':z['hot']['original_pad_face_tag'],
     'original_cold_pad_tag':z['cold']['original_pad_face_tag'],
     'hot_pad_area_mean_T_K':float(th),'cold_pad_area_mean_T_K':float(tc),
     'hot_heat_to_plate_W':float(hot),'cold_heat_from_plate_W':float(cold),
     'electric_voltage_contribution_V':float(v),
     'bulk_ohmic_joule_W':float(A*res['joule_w_m2']),
     'thermoelectric_leg_energy_residual_W':float(energy),
     'axial_33_node_T_K':[float(t) for t in res['temperatures_k']],
     'contact_offsets_K_per_W':[
         z['hot']['relative_local_offset_K_per_W'],
         z['cold']['relative_local_offset_K_per_W']]})
  assert [q['source_leg_count'] for q in stage]==[58,22,8]
  die_heat=(temps[7]-temps[6])/die_R
  die_source=.002+Gau*(300.-temps[7])
  qcu=Gcu*(300.-temps[0])
  cujoule=I*I*Rau
  qbath=stage[0]['qh_w']+qcu+.5*cujoule
  return stage,die_heat,die_source,qbath,qcu,cujoule,rows
 def residual(x):
  st,Qa,Qd,Qbath,qcu,CuJoule,_=evaluate(x)
  T=x[:8];q=x[8:]
  return np.array([
   st[0]['qc_w']-st[1]['qh_w'],
   st[1]['qc_w']-st[2]['qh_w'],
   st[2]['qc_w']-Qa,
   Qa-Qd,
   T[2]-T[1]-R[1]*q[1],
   T[4]-T[3]-R[2]*q[2],
   T[6]-T[5]-R[3]*q[3],
   T[0]-300.-(Rext+R[0])*q[0],
   q[0]-Qbath,
   q[1]-st[1]['qh_w'],
   q[2]-st[2]['qh_w'],
   q[3]-Qa])
 lo=np.r_[np.full(8,180.00001),np.zeros(4)+1e-9]
 hi=np.r_[np.full(8,389.99999),np.full(4,2.)]
 weights=np.r_[np.array([10.,10.,100.,100.,.1,.1,.1,.5]),np.full(4,10.)]
 fit=least_squares(lambda x:weights*residual(x),x0,bounds=(lo,hi),
  x_scale=np.r_[np.full(8,10.),np.full(4,.1)],
  max_nfev=70,ftol=1e-12,xtol=1e-12,gtol=1e-12)
 assert fit.success,fit.message
 x=fit.x
 st,Qa,Qd,Qbath,qcu,CuJoule,rows=evaluate(x,True)
 err=residual(x)
 assert max(abs(err[:4]))<reg['max_allowed_stage_heat_balance_W'],err
 assert max(abs(err[4:8]))<reg['max_allowed_interface_temperature_closure_K'],err
 assert max(abs(err[8:]))<reg['max_allowed_stage_heat_balance_W'],err
 assert max(abs(z['thermoelectric_leg_energy_residual_W']) for z in rows)<reg['max_allowed_individual_leg_energy_residual_W']
 assert all(abs(z['energy_residual_w'])<1e-9 for z in st)
 volt=sum(s['voltage_v'] for s in st)+I*Rau
 P=I*volt
 reservoir_cu=qcu-.5*CuJoule
 energy=P+.002+Gau*(300.-x[7])+reservoir_cu-Qbath
 assert abs(energy)<reg['max_allowed_global_energy_residual_W'],energy
 assert abs(x[7]-temp0[7])<10.,'Unexpected V3 discontinuity relative V2'
 assert abs(Qbath-x[8])<1e-8
 assert all(z['hot_pad_area_mean_T_K']>z['cold_pad_area_mean_T_K'] for z in rows)
 assert max(z['max_leg_T_K'] for z in st)>300
 # Source temperatures with V2 original unit 3D plate fields,
 # now at the new coupled V3 through-heats and mean boundary values.
 profiles=np.load(FIELD,allow_pickle=False)
 arrays={}
 ranges=[]
 top_indices=(0,2,4,6);bot_indices=(None,1,3,5)
 for i in range(4):
  name=f'ceramic{i}'
  u=profiles[name+'_temperature_delta_over_bottom_mean_K_per_W']
  pos=profiles[name+'_source_xyz_mm']
  ids=profiles[name+'_source_global_node_id_1based']
  Tb=x[top_indices[i]]-R[i]*x[8+i] if i==0 else x[bot_indices[i]]
  a=Tb+x[8+i]*u
  arrays[name+'_source_mesh_node_ID_1based']=ids
  arrays[name+'_source_xyz_mm']=pos
  arrays[name+'_temperature_K']=a
  ranges.append({'original_source_ceramic_ID':i+1,'min_K':float(a.min()),
   'max_K':float(a.max()),'spread_K':float(np.ptp(a)),
   '3D_heat_W':float(x[8+i])})
 profiles.close()
 arrays['source_leg_region_ID']=np.array([z['original_source_leg_ID'] for z in rows],dtype=np.int32)
 arrays['source_leg_axial_33_node_T_K']=np.array([z['axial_33_node_T_K'] for z in rows],dtype=np.float64)
 arrays['source_leg_xy_center_mm']=np.array([z['source_xy_center_mm'] for z in rows],dtype=np.float64)
 assert arrays['source_leg_axial_33_node_T_K'].shape==(88,33)
 result={
  'status':'V3 SOURCE-88-LEG LOCATION-RESOLVED NONLINEAR TE + ORIGINAL FOUR 3D CERAMIC RESPONSE TWO-WAY FULL PACKAGE: CONDITIONAL NUMERICAL PASS',
  'current_A':I,
  'stage_couple_count':[29,11,4],
  'actual_source_leg_count':88,
  'original_source_ceramic_region_ids':[1,2,3,4],
  'original_source_ceramic_tets':11791,
  'source_ceramic_contact_pad_faces_used':len(patches),
  'source_individual_leg_temperature_and_flux_data':rows,
  'source_individual_stage_energy_voltage_flux':st,
  'source_original_ceramic_temperature_ranges':ranges,
  'source_temperature_interface_means_K':dict(zip([
      'stage0_hot','stage0_cold','stage1_hot','stage1_cold',
      'stage2_hot','stage2_cold','carrier','die'],map(float,x[:8]))),
  'four_source_ceramic_through_heat_W':[float(v) for v in x[8:]],
  'terminal_voltage_V':float(volt),
  'terminal_electrical_power_W':float(P),
  'detector_temperature_K':float(x[7]),
  'bath_heat_rejected_W':float(Qbath),
  'detector_die_attach_flux_W':float(Qa),
  'source_Au_wire_leak_W':float(Gau*(300.-x[7])),
  'hot_external_R_without_ceramic0_K_W':float(Rext),
  'source_ceramic_spatial_R_K_W':[float(q) for q in R],
  'global_electrical_thermal_energy_W':float(energy),
  'max_node_energy_residual_W':float(max(abs(err[:4]))),
  'max_3D_ceramic_temperature_closure_K':float(max(abs(err[4:8]))),
  'max_four_ceramic_heat_residual_W':float(max(abs(err[8:]))),
  'max_individual_leg_energy_residual_W':float(max(abs(z['thermoelectric_leg_energy_residual_W']) for z in rows)),
  'source_individual_PN_leg_voltage_series_sum_V':float(sum(z['electric_voltage_contribution_V'] for z in rows)),
  'optimizer_nfev':int(fit.nfev),
  'original_Source_PN_bulk_spatial_E_T_FEM':'NOT RUN; per-leg nonlinear axial 1D transport on source-specific local 3D boundary traces',
  'V2_same_current_comparison':{
   'die_K':v2['full_detector_die_temperature_K'],
   'V3_minus_V2_die_K':float(x[7]-v2['full_detector_die_temperature_K']),
   'terminal_voltage_V':v2['terminal_voltage_V'],
   'V3_minus_V2_terminal_V':float(volt-v2['terminal_voltage_V']),
   'V3_minus_V2_bath_W':float(Qbath-v2['bath_sink_rejected_heat_W'])},
  'spatial_fields':'v3_source_4_ceramic_and_88_leg_profiles.npz',
  'actual_module_transport_and_contact_measured':False,
  'PN_transport_assumed_extension_above_300K':True,
  'original_P1_B':'FAIL/STOP',
  'first_source_pair_original_raw_flux':'FAIL 8/8',
  'full_430_C_D':'NOT RUN',
  'full_source_3D_E_T_mesh_spatial_solve':False,
  'source_geometry_and_mesh_modified':False,
  'source_hashes':reg['source_sha256'],
  'original_R3_face_mesh_SHA256':reg['original_R3_face_mesh_sha256'],
  'script_sha256':reg['source_script_sha256'],
  'runtime_s':time.perf_counter()-tic
 }
 return result,arrays

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--registration',type=Path,required=True)
 p.add_argument('--outdir',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 a=p.parse_args();reg=read(a.registration)
 assert reg==expected_registration()
 result,arrays=solve_case(reg)
 if a.verify_only:
  before=read(a.outdir/'result.json')
  for k,v in result.items():
   if k in ('runtime_s',):continue
   if isinstance(v,float):assert abs(v-before[k])<max(1e-10,1e-8*abs(v)),k
   else:
    assert v==before[k],k
  with np.load(a.outdir/'v3_source_4_ceramic_and_88_leg_profiles.npz',allow_pickle=False) as npz:
   assert set(npz.files)==set(arrays)
   for k,v in arrays.items():assert np.array_equal(v,npz[k]),k
 else:
  assert not (a.outdir/'result.json').exists()
  assert not (a.outdir/'v3_source_4_ceramic_and_88_leg_profiles.npz').exists()
  (a.outdir/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  np.savez_compressed(a.outdir/'v3_source_4_ceramic_and_88_leg_profiles.npz',**arrays)
 print('V3_FULL_INTEGRATED_LEG_SPATIAL',json.dumps({
  k:result[k] for k in ('status','actual_source_leg_count','source_ceramic_contact_pad_faces_used',
  'detector_temperature_K','terminal_voltage_V','terminal_electrical_power_W',
  'bath_heat_rejected_W','global_electrical_thermal_energy_W',
  'max_node_energy_residual_W','max_individual_leg_energy_residual_W',
  'optimizer_nfev','runtime_s')},indent=2))
 print('V3_V2_DELTA',result['V2_same_current_comparison'])
if __name__=='__main__':main()
