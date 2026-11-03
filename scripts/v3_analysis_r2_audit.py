"""R2 independent solid, gas, source-contact and shell map verification. No FEM/PDE."""
from __future__ import annotations
from collections import Counter,defaultdict
from pathlib import Path
import argparse,hashlib,json,math
import gmsh

ROOT=Path(__file__).resolve().parents[1]
R1=ROOT/'data/v3_derived_multiphysics_20261103'
SRC=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,payload):path.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')

def audit(brep,receipt,out):
 if out.exists():raise ValueError('Refuse overwrite')
 out.mkdir(parents=True)
 raw=json.loads(receipt.read_text())
 prior=json.loads((R1/'face_ownership.json').read_text())
 physical=json.loads(SRC.read_text());source_byname={x['name']:x for x in physical['bodies']}
 required=raw['OCC_output_volume_tags']
 result={'status':'INCOMPLETE','input_r2_brep_sha256':sha(brep),'original_source_sha256':sha(SRC),
     'baseline_r1_brep_sha256':sha(R1/'analysis_conformal_mm.brep')}
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
 try:
  oc=gmsh.model.occ;oc.importShapes(str(brep));oc.synchronize()
  vids=[tag for dim,tag in gmsh.model.getEntities(3)]
  known=[name for name,tag in sorted(required.items(),key=lambda v:v[1])]
  assert len(vids)==len(known)==428
  names=dict(zip(vids,known));byname={n:t for t,n in names.items()}
  for tag,name in names.items():
   v=oc.getMass(3,tag);ex=raw['volume_mm3'][name]
   if abs(v/ex-1)>1e-6:raise ValueError('reimport CAD identity/volume changed '+name)
  if set(names.values())!=set(required):raise ValueError('name set missing')
  source_to_analysis={}
  for sname,oldname in prior['removed_to_retained'].items():
   if oldname in byname:
    source_to_analysis[sname]={'kind':'VOLUME','name':oldname,'id':byname[oldname]}
   elif oldname.startswith('pin') and oldname.rsplit('_',1)[-1] in ('Au','Ni') and oldname.split('_')[0] in byname:
    newname=oldname.split('_')[0]
    source_to_analysis[sname]={'kind':'EFFECTIVE_AXIAL_TERMINAL_LAYER','name':newname,'id':byname[newname],
      'material':source_byname[sname]['material'],'law':'FINITE_SHEET/INTERFACE LAW UNSET'}
   elif oldname in ('lead1_insulation','lead9_insulation'):
    source_to_analysis[sname]={'kind':'NONVOLUMETRIC_DIELECTRIC_SHELL','name':oldname,
      'source_material':'Polyimide_candidate','physical_volume_mm3':raw['lead_jacket_records'][0 if '1_' in oldname else 1]['source_3d_polyimide_mm3'],
      'law':'UNSET_THERMAL_RADIAL/ELECTRIC_ISOLATION/EXTERIOR_RADIATION'}
   else:raise ValueError('unmapped source solid '+sname+' => '+oldname)
  if len(source_to_analysis)!=824:raise ValueError('missing original physical source')
  byface={};pairfaces=defaultdict(list);ftype=Counter();signed={};nonmanifold=[];gas_unowned=[]
  for tag in vids:
   for d,f in gmsh.model.getBoundary([(3,tag)],oriented=True,recursive=False):
    if d!=2:raise ValueError('boundary nonface')
    signed[(tag,abs(f))]=1 if f>0 else -1
  for _,face in gmsh.model.getEntities(2):
   pair=sorted(map(int,gmsh.model.getAdjacencies(2,face)[0]))
   if len(pair) not in (1,2):nonmanifold.append((face,pair));continue
   if len(pair)==2 and signed[(pair[0],face)]+signed[(pair[1],face)]!=0:
    raise ValueError('face normals inconsistent '+str(face))
   involved=[names[t] for t in pair]
   area=oc.getMass(2,face)
   if area<=1e-12:raise ValueError('zero face')
   klass=('GAS_SOLID' if 'CAVITY_GAS' in involved else 'SOLID_SOLID') if len(pair)==2 else 'EXTERIOR'
   if 'CAVITY_GAS' in involved and len(pair)!=2:gas_unowned.append(face)
   data={'face_tag':face,'owners':involved,'owner_volume_ids':pair,'face_area_mm2':area,
       'center_mm':oc.getCenterOfMass(2,face),'bbox_mm':oc.getBoundingBox(2,face),
       'class':klass,'orientation_signs':[signed[(v,face)] for v in pair],
       'law_status':'UNSET'}
   byface[str(face)]=data;ftype[klass]+=1
   if len(pair)==2:pairfaces[tuple(sorted(involved))].append(face)
  if nonmanifold or gas_unowned:raise ValueError('R2 orphan/nonmanifold '+str((nonmanifold[:5],gas_unowned[:5])))
  if len(byface)!=len(gmsh.model.getEntities(2)):raise ValueError('missing geometry surface')
  missing=[];area_errors=[];contacts=[]
  for i,c in enumerate(physical['explicit_contacts']):
   a=source_to_analysis[c['a']]['name'];b=source_to_analysis[c['b']]['name']
   if a==b:
    contacts.append({'index':i,'source':(c['a'],c['b']),'type':'COLLAPSED_COMPOSITE','source_witness_mm2':c['area']})
    continue
   ids=pairfaces.get(tuple(sorted((a,b))),[])
   if not ids:
    missing.append({'index':i,'original':(c['a'],c['b']),'mapped':(a,b)})
    continue
   area=sum(byface[str(f)]['face_area_mm2'] for f in ids)
   rel=abs(area/c['area']-1)
   if rel>1e-6:area_errors.append({'index':i,'original':(c['a'],c['b']),'mapped':(a,b),'source_area':c['area'],'new_area':area,'relative_error':rel})
   contacts.append({'index':i,'source':(c['a'],c['b']),'mapped':(a,b),
       'source_witness_mm2':c['area'],'new_shared_area_mm2':area,'relative_error':rel,
       'face_tags':ids,'type':'FINITE_SHARED_FACE'})
  cross_net=[]
  for pair,fs in pairfaces.items():
   if 'CAVITY_GAS' in pair:continue
   original=[(n,source_byname[n]) for n in pair if n in source_byname]
   gs=[q.get('group') for n,q in original]
   if len(gs)==2 and all(isinstance(z,int) for z in gs) and gs[0]!=gs[1]:cross_net.append(pair)
   if len(gs)==2 and ((isinstance(gs[0],int) and str(gs[1]).startswith('DET')) or (isinstance(gs[1],int) and str(gs[0]).startswith('DET'))):cross_net.append(pair)
  if missing or area_errors or cross_net: result['status']='STOP CONTACT/SHORT INTEGRITY'
  else:result['status']='PASS R2 CAD SOURCE/CONTACT/SHARED-FACE GRAPH; NO FEM'
  result.update(volume_count=len(vids),face_count=len(byface),face_class_counts=dict(ftype),
      gas_volume_mm3=raw['R2_gas_volume_mm3'],gas_components=1,missing_contacts=missing,
      area_errors=area_errors,unintended_electrical_contacts=cross_net,
      contacts_checked=len(contacts),source_count=len(source_to_analysis),
      domain_id_map=byname,source_to_analysis=source_to_analysis,face_registry=byface,
      source_contacts=contacts,no_PDE=True,solver_ready=False)
  save(out/'r2_integrity.json',result)
  print(result['status'],'domains',len(vids),'faces',len(byface),'missing',len(missing),
       'areas failed',len(area_errors),'shorts',len(cross_net),flush=True)
  if missing:print('MISSING',missing[:12],flush=True)
  if area_errors:print('AREA FAIL',area_errors[:12],flush=True)
  if cross_net:print('SHORT',cross_net[:12],flush=True)
  return result
 except Exception as ex:
  result['status']='FAIL/STOP R2 REGISTRY';result['error']=repr(ex)
  save(out/'failure.json',result)
  raise
 finally:gmsh.finalize()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--brep',type=Path,required=True)
 p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();audit(a.brep,a.receipt,a.out)
