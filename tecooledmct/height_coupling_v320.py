"""Geometry-mapped reduced coupling operators for custom 0.60 mm assembly.

No system solver or native gas field. Original mesh tags remain lineage IDs;
all candidate physical positions and ownership must be established first.
"""
from pathlib import Path
from collections import Counter
import json,math
import numpy as np
from scripts.v3_4_source_copper_multiport import PORTS,STAGES,ENDPOINTS,K_CU_W_MK,copper_rho,THERMAL_CONTACT_R_AREA_M2K_W,ELECTRICAL_CONTACT_R_AREA_OHM_M2
from scripts.v2_source_ceramic_spatial import FACE_SELECT
from tecooledmct.tec_assembly_v3 import area
from tecooledmct.integrated_reference import Scenario,gas_transport
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
CANDIDATE=ROOT/'data/tec_height_060_cad_20261110/source_candidate/design.json'
META=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
IMPORTED=ROOT/'data/tec_height_060_cad_20261110/imported_contact_audit_attempt01.json'
def read(p):return json.loads(p.read_text())
def face_skin(name):
 if name.startswith('net') and name.endswith('_Cu'):return name[:-3]+'_Ti'
 if name=='underside_Au':return 'underside_Ti'
 if name=='cold_finish_Au':return 'cold_finish_Ti'
 raise ValueError('Unknown ceramic-face composite '+name)
def mapping():
 original=read(ORIGINAL);candidate=read(CANDIDATE);meta=read(META);brep=read(IMPORTED)
 assert brep['status'].startswith('PASS') and brep['independent_contacts']==923
 ob={x['name']:x for x in original['bodies']};cb={x['name']:x for x in candidate['bodies']}
 verified={frozenset((x['a'],x['b'])) for x in brep['contacts']}
 shifts=[]
 for i in range(4):
  a=ob[f'ceramic{i}']['boxes_mm'][0];b=cb[f'ceramic{i}']['boxes_mm'][0]
  assert np.allclose([a[k] for k in (0,1,3,4,5)],[b[k] for k in (0,1,3,4,5)],rtol=0,atol=1e-11)
  shift=b[2]-a[2];assert abs(shift-i*.1)<1e-10;shifts.append(shift)
 face_map={}
 for rid,group in FACE_SELECT.items():
  stage=rid-1
  for side in ('top','bottom'):
   for tag in group[side]:
    face=meta['faces'][str(tag)];owners=face['owners'];assert owners[0]==f'ceramic{stage}'
    skin=face_skin(owners[1]);a=ob[skin];b=cb[skin];assert frozenset((owners[0],skin)) in verified
    aq=a['boxes_mm'];bq=b['boxes_mm'];assert len(aq)==len(bq)
    for u,v in zip(aq,bq):
     assert np.allclose([u[k] for k in (0,1,3,4,5)],[v[k] for k in (0,1,3,4,5)],rtol=0,atol=1e-11)
     assert abs(v[2]-u[2]-shifts[stage])<1e-10
    A=area([[q[0],q[1],q[3],q[4]] for q in bq]);assert abs(A-face['face_area_mm2'])<1e-8,(tag,A,face['face_area_mm2'])
    centre=face['center_mm'];candidate_centre=[centre[0],centre[1],centre[2]+shifts[stage]]
    face_map[tag]={'tag':tag,'ceramic_stage':stage,'side':side,'source_owners':owners,'candidate_physical_skin':skin,
      'original_center_mm':centre,'candidate_center_mm':candidate_centre,'face_area_mm2':A,'translated_z_mm':shifts[stage],
      'imported_candidate_solid_witness':'PASS','candidate_face_tag':'NOT ASSIGNED; source TRI3 tag is lineage key'}
 assert len(face_map)==95
 from scripts.v3_integrated_leg_resolved import find_leg_contact_source
 legs,_=find_leg_contact_source();pairs=[]
 for l in legs:
  i=l['source_series_chain_index'];q=cb[l['leg_name']]['boxes_mm'][0];assert abs(q[5]-.6)<1e-10
  for side in ('hot','cold'):
   v=l[side];tag=v['original_pad_face_tag'];j=l['stage']+(side=='cold');assert face_map[tag]['ceramic_stage']==j
   s=cb[v['solder_source']];assert s['leg']==i and s['face']==side
   assert frozenset((l['leg_name'],s['name'])) in verified
   pairs.append({'leg':l['leg_name'],'side':side,'solder':s['name'],'ceramic':f'ceramic{j}','source_face_tag':tag,'candidate_physical_skin':face_map[tag]['candidate_physical_skin']})
 assert len(pairs)==176
 return {'status':'PASS rigid source-ceramic/face/solid-witness mapping; no new native conformal mesh','plate_shifts_mm':shifts,'faces':face_map,'leg_faces':pairs,'candidate_3D_pn_pde':'NOT RUN'}
def copper_specs(design):
 b={x['name']:x for x in design['bodies']};out={}
 for net,tags in PORTS.items():
  body=b[f'formed_tab{net}'];joints=({58:(0,1),80:(2,3),88:(4,5,6)})[net];feet=[b[f'tab_joint{i}'] for i in joints]
  lengths=[p['length']*1e-3 for p in body['parts']];centre=[(x['bbox_mm'][1]+x['bbox_mm'][4])/2 for x in feet]
  initial=abs(body['parts'][0]['a'][0]-centre[0])*1e-3;final=abs(body['parts'][-1]['b'][0]-centre[-1])*1e-3
  if net!=88:segments=[sum(lengths)-initial-final]
  else:
   midseg=4;L1=sum(lengths[:midseg])+(body['parts'][midseg]['a'][0]-centre[1])*1e-3-initial
   segments=[L1,sum(lengths)-initial-final-L1]
  assert min(segments)>0
  Ac=[(x['bbox_mm'][3]-x['bbox_mm'][0])*(x['bbox_mm'][4]-x['bbox_mm'][1])*1e-6 for x in feet]
  assert max(abs(x-.06e-6) for x in Ac)<1e-17
  out[net]={'net':net,'faces':tags,'stage':ENDPOINTS[net],'source_centerline_total_length_m':sum(lengths),'contact_centre_span_m':sum(segments),'segments_m':tuple(segments),'cross_section_m2':body['width']*body['thickness']*1e-6,'contact_area_m2':Ac,'joining_source_solids':tuple(f'tab_joint{i}' for i in joints)}
 return out
def copper_eval(spec,I,plate_T,thermal_Rarea=THERMAL_CONTACT_R_AREA_M2K_W,electrical_Rarea=ELECTRICAL_CONTACT_R_AREA_OHM_M2,legacy_middle_electric=False):
 assert I>=0 and thermal_Rarea>=0 and electrical_Rarea>=0
 loads={int(t):0. for tags in PORTS.values() for t in tags};detail={}
 for net,s in spec.items():
  tags=s['faces'];p=np.array([plate_T[t] for t in tags]);A=s['cross_section_m2'];L=np.asarray(s['segments_m']);G=K_CU_W_MK*A/L
  Rseg=copper_rho((p[1:]+p[:-1])/2)*L/A;Re=electrical_Rarea/np.asarray(s['contact_area_m2'])
  if net==88 and not legacy_middle_electric:Re[1]=0. # middle foot is thermal-only, no series-current passage
  pj=I*I*Rseg;pc=I*I*Re;src=np.zeros(len(tags));src[:-1]+=.5*pj;src[1:]+=.5*pj
  if thermal_Rarea:
   Gc=np.asarray(s['contact_area_m2'])/thermal_Rarea;M=np.diag(Gc)
   for j,g in enumerate(G):M[j,j]+=g;M[j+1,j+1]+=g;M[j,j+1]-=g;M[j+1,j]-=g
   ft=np.linalg.solve(M,Gc*p+src);q=Gc*(ft-p)+pc
  else:
   ft=p.copy();q=src+pc;q[:-1]-=G*(p[:-1]-p[1:]);q[1:]+=G*(p[:-1]-p[1:])
  R=float(sum(Rseg)+sum(Re));power=I*I*R;assert abs(q.sum()-power)<1e-11
  for tag,v in zip(tags,q):loads[tag]+=float(v)
  detail[str(net)]={'face_tags':list(tags),'plate_temperature_K':p.tolist(),'foil_node_temperature_K':ft.tolist(),'thermal_segment_conductance_W_K':G.tolist(),'segment_length_m':L.tolist(),'metal_electrical_segment_R_ohm':Rseg.tolist(),'contact_electrical_R_ohm':Re.tolist(),'face_heat_into_ceramic_W':q.tolist(),'electric_resistance_ohm':R,'electric_Joule_W':power,'electric_voltage_V':I*R}
 qplates=[float(sum(q for t,q in loads.items() if STAGES[t]==s)) for s in range(3)];power=sum(x['electric_Joule_W'] for x in detail.values());assert abs(sum(qplates)-power)<1e-11
 return {'heat_into_face_W':loads,'net_details':detail,'heat_into_ceramic_by_stage_W':qplates,'total_electrical_power_W':power,'total_electrical_R_ohm':sum(x['electric_resistance_ohm'] for x in detail.values())}
def wire_geometry(design):
 from tecooledmct.materials import COPPER,GOLD_WIRE_4N
 b={x['name']:x for x in design['bodies']};out=[]
 for name,prop in [('TEC_lead1',COPPER),('TEC_lead9',COPPER),('detector_bond7',GOLD_WIRE_4N),('detector_bond8',GOLD_WIRE_4N)]:
  w=b[name];r=w['radius']*1e-3;L=sum(x['length'] for x in w['parts'])*1e-3;A=math.pi*r*r
  out.append({'name':name,'length_m':L,'radius_m':r,'G_W_K':prop.thermal_conductivity_w_mk*A/L,'R_ohm':prop.electrical_resistivity_ohm_m*L/A})
 return out
def interstage_gas_geometry(design):
 b={x['name']:x for x in design['bodies']};res=[]
 for stage,n in enumerate((58,22,8)):
  low=b[f'ceramic{stage}']['boxes_mm'][0];high=b[f'ceramic{stage+1}']['boxes_mm'][0]
  substrate_gap=high[2]-(low[2]+low[5]);plate_overlap=high[3]*high[4];A=plate_overlap-n*.4*.4
  # One-dimensional parallel-path engineering proxy; both 15um face films bound the gap.
  gap=substrate_gap-.030;assert A>0 and gap>0
  for l in design['legs']:
   if l['stage']!=stage:continue
   x,y=l['center_mm'];assert abs(x)+.2<=high[3]/2+1e-10 and abs(y)+.2<=high[4]/2+1e-10
  res.append({'stage':stage,'gap_m':gap*1e-3,'area_m2':A*1e-6,'substrate_gap_mm':substrate_gap,'method':'upper-plate projected area less leg footprints; parallel-path proxy, connected side cavity and coatings omitted'})
 return res
def interstage_gas(T_hot,T_cold,gap_m,area_m2,pressure_Pa=100.):
 assert gap_m>0 and area_m2>0 and pressure_Pa>=0
 if pressure_Pa==0:return {'Q_W':0.,'G_W_K':0.,'temperature_jump_m':None}
 cfg=Scenario(gas='Kr',cavity_pressure_pa=pressure_Pa,accommodation=.8);k,jump,below=gas_transport(cfg,.5*(T_hot+T_cold))
 G=k*area_m2/(gap_m+2*jump)
 return {'Q_W':G*(T_hot-T_cold),'G_W_K':G,'temperature_jump_m':jump,'k_W_mK':k,'source_below_range':bool(below)}
