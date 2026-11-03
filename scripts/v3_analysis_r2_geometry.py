"""V3 R2 analysis-only coating reduction. Frozen R1 physical STEP is never modified.

Unlike a new physical CAD, this BREP transfers two 15um lead polymer jackets
into boundary operators, and four 3.5um Ni/Au pin caps into effective axial
terminal regions; no 3D conductor, solder or detector bond contact is omitted.

Source and explicit seam area remain authoritative. No PDE or fitted coefficients.
"""
from __future__ import annotations
import argparse,hashlib,json,math,time
from pathlib import Path
import gmsh

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'data/v3_derived_multiphysics_20261103'
SRC=ROOT/'data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step'
REV3=ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'
PINS=(1,7,8,9)
INS=(1,9)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')

def build(out):
 if out.exists():raise ValueError('refuse overwrite')
 out.mkdir(parents=True)
 orig=json.loads((OLD/'face_ownership.json').read_text())
 nameids={k:v['tag'] for k,v in orig['domain_metadata'].items() if k!='CAVITY_GAS'}
 removal={f'pin{n}_{mat}' for n in PINS for mat in ('Ni','Au')}
 removal|={f'lead{n}_insulation' for n in INS}
 assert len(removal)==10 and len(nameids)==437 and removal<set(nameids)
 receipt={'status':'PENDING','starting_geometry_sha256':sha(OLD/'analysis_solids_mm.brep'),
    'source_824_STEP_sha256':sha(SRC),'canonical_Rev3_sha256':sha(REV3),
    'source_face_registry_sha256':sha(OLD/'face_ownership.json'),
    'original_437':437,'removed_as_nonvolume':sorted(removal),
    'expected_3d_domain_count':428,'no_PDE':True,'sealed_physical_R1_unchanged':True,
    'R2_idealizations':{'lead_insulation':'15um radial polyimide reduced to gas/lead shell law; surface radiative area must use source outer area; no homogeneous Cu jacket',
       'pin_tip':'Ni 2um / Au1.5um effective axial composite end cap; source film law + interface contact not bulk Kovar'},
    'interface_law_status':'UNSET; NOT SOLVER READY'}
 save(out/'build_receipt.json',receipt)
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
 gmsh.option.setString('Geometry.OCCTargetUnit','MM');gmsh.option.setNumber('General.NumThreads',4)
 start=time.monotonic()
 try:
  occ=gmsh.model.occ
  occ.importShapes(str(OLD/'analysis_solids_mm.brep'));occ.synchronize()
  assert len(gmsh.model.getEntities(3))==437
  masses={k:occ.getMass(3,tag) for k,tag in nameids.items()}
  # Nonuniform OCC dilation of imported round pins is not shape-safe: reject it.
  # Rebuild only the *analysis* effective round terminal from frozen pin axes.
  effective_pins={}
  physical_source=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
  physical_byname={x['name']:x for x in physical_source['bodies']}
  for n in PINS:
   name=f'pin{n}'
   source=physical_byname[name]
   assert source['shape']=='cylinder' and source['radius']==.38
   assert source['height']==14.7 and abs(source['base'][2]+12.7)<1e-9
   x,y,z=source['base']
   old_tag=nameids[name]
   occ.remove([(3,old_tag)],recursive=False)
   fresh=occ.addCylinder(x,y,z,0,0,14.7035,.38)
   effective_pins[name]=fresh
  occ.synchronize()
  occ.remove([(3,nameids[k]) for k in sorted(removal)],recursive=False)
  occ.synchronize()
  solids=sorted(gmsh.model.getEntities(3))
  assert len(solids)==427
  nameids.update(effective_pins)
  pin_cap_records=[]
  for n in PINS:
   tag=nameids[f'pin{n}'];base=math.pi*.38**2
   mass=occ.getMass(3,tag);original=masses[f'pin{n}'];target=original+base*.0035
   if abs(mass-target)>1e-8:raise ValueError('pin cap wrong mass '+str(n)+' '+repr((mass,target)))
   pin_cap_records.append({'pin':n,'original_pin_mm3':original,'new_effective_pin_mm3':mass,
     'thin_film_effective_thickness_mm':.0035,'finish_source_names':[f'pin{n}_Ni',f'pin{n}_Au'],
     'effective_axial_cap_area_mm2':base,'cap_material':'COMPOSITE_NI_AU_FINISH_NOT_KOVAR',
     'sheet_law':'UNSET explicit through-thickness finite electrical/thermal contact resistance'})
  receipt['pin_caps']=pin_cap_records
  receipt['lead_jacket_records']=[]
  for n in INS:
   src=next(k for k in orig['domain_metadata'].values() if k['tag']==nameids[f'lead{n}_insulation'])
   tag=nameids[f'lead{n}_insulation']
   receipt['lead_jacket_records'].append({'source_name':f'lead{n}_insulation',
    'source_3d_polyimide_mm3':masses[f'lead{n}_insulation'],
    'inner_radius_mm':.100,'outer_radius_mm':.115,'jacket_thickness_mm':.015,
    'copper_source':f'TEC_lead{n}',
    'shell_law':'UNSET radial k/ln(ro/ri), finite insulating electric current, surface radiation at physical outer radius'})
  gmsh.write(str(out/'r2_reduced_solids_mm.brep'))
  # Create native connected gas occupying original inner cavity minus all R2 solids.
  void=occ.addCylinder(0,0,1.5,0,0,8.15,7.1)
  cap_excluded={nameids[k] for k in ('cap_shell','cap_roof','window')}
  tools=[q for q in solids if q[1] not in cap_excluded]
  gas, _=occ.cut([(3,void)],tools,removeObject=True,removeTool=False)
  occ.synchronize();gas_tags=[t for d,t in gas if d==3]
  if len(gas_tags)!=1:raise ValueError('R2 gas disconnected: '+str(gas_tags))
  gasmass=occ.getMass(3,gas_tags[0]);
  if gasmass<1200 or gasmass>1250:raise ValueError('R2 gas volume invalid')
  receipt['R2_gas_volume_mm3']=gasmass
  gmsh.write(str(out/'r2_with_gas_mm.brep'))
  print('R2 OCC fragment start',len(solids),'solids and gas',flush=True)
  produced,mapping=occ.fragment([(3,gas_tags[0])],solids,removeObject=True,removeTool=True)
  occ.synchronize()
  assert len(mapping)==len(solids)+1
  names={tag:name for name,tag in nameids.items() if name not in removal}
  inputs=['CAVITY_GAS']+[names[t] for _,t in solids]
  audit={}
  for name,group in zip(inputs,mapping):
   tags=[t for d,t in group if d==3]
   if len(tags)!=1:raise ValueError('source split into multiple analysis solids: '+name+str(tags))
   audit[name]=tags[0]
  if len(audit)!=428 or len(set(audit.values()))!=428 or len(gmsh.model.getEntities(3))!=428:
   raise ValueError('Conformal domain count/topology mismatch')
  # OCC fragmentation leaves occasional orphan faces from the discarded jacket surfaces.
  # Never remove a face referenced by a volume, or any original physical source volume.
  orphan_faces=[(2,tag) for dim,tag in gmsh.model.getEntities(2)
                if not len(gmsh.model.getAdjacencies(2,tag)[0])]
  receipt['orphan_surfaces_removed']=[t for _,t in orphan_faces]
  if orphan_faces:
   occ.remove(orphan_faces,recursive=False)
   occ.synchronize()
  if len(gmsh.model.getEntities(3))!=428:raise ValueError('orphan removal changed R2 domains')
  gmsh.write(str(out/'r2_conformal_mm.brep'))
  # imported geometry assigns consecutive volume tags by ascending output tag order.
  preserved={name:occ.getMass(3,tag) for name,tag in audit.items()}
  facecount=len(gmsh.model.getEntities(2));faceowners={}
  reverse={tag:name for name,tag in audit.items()}
  for _,f in gmsh.model.getEntities(2):
   owners=sorted(map(int,gmsh.model.getAdjacencies(2,f)[0]))
   if len(owners) not in (1,2):
    receipt['nonmanifold_diagnostic']={'face':f,'owners':owners,'names':[reverse.get(t,'?') for t in owners],'face_mm2':occ.getMass(2,f)}
    raise ValueError('nonmanifold face '+str(f)+' '+str(receipt['nonmanifold_diagnostic']))
   if audit['CAVITY_GAS'] in owners and len(owners)!=2:
    raise ValueError('open gas face '+str(f))
   faceowners[str(f)]=owners
  receipt.update(status='PASS R2 BREP DERIVED, GLOBAL MESH NOT QUALIFIED',
    final_volume_count=len(audit),face_count=facecount,
    OCC_output_volume_tags=audit,
    face_adjacencies=faceowners,
    volume_mm3=preserved,
    gas_connected_components=1,
    conformal_brep_sha256=sha(out/'r2_conformal_mm.brep'),
    solids_brep_sha256=sha(out/'r2_reduced_solids_mm.brep'),
    with_gas_brep_sha256=sha(out/'r2_with_gas_mm.brep'),seconds=time.monotonic()-start)
  print('R2 BREP PASSED',len(audit),'volumes',facecount,'faces',round(time.monotonic()-start,2),'s',flush=True)
 except Exception as ex:
  receipt.update(status='FAIL/STOP R2 BREP',error=repr(ex),seconds=time.monotonic()-start)
  raise
 finally:
  save(out/'build_receipt.json',receipt);gmsh.finalize()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
