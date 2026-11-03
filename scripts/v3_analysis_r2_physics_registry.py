"""Explicit R2 all-face multiphysics ownership; all physical coefficients UNSET."""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def generate(old_source,integrity,shell,output):
 if output.exists():raise ValueError('refuse overwrite')
 old=json.loads(old_source.read_text());r=json.loads(integrity.read_text());s=json.loads(shell.read_text())
 stagecounts=Counter();materials=Counter();domain={}
 for name,tag in r['domain_id_map'].items():
  if name=='CAVITY_GAS':
   data={'material':'IDEALIZED_CAVITY_GAS','sources':[], 'stage':None,
    'constitutive_requirement':'gas species, pressure/temperature regime, k(T,p), accommodation, radiation independent'}
  elif name.startswith('pin') and name[3:] in ('1','7','8','9'):
   data={'material':'EFFECTIVE_AXIAL_KOVAR_NI_AU','sources':[name,name+'_Ni',name+'_Au'],
    'stage':None,'z_regions_mm':[[-12.7,2.0,'Kovar_pin'],[2.0,2.002,'Ni'],[2.002,2.0035,'Au']],
    'constitutive_requirement':'NO BULK KOVAR FALLBACK: resolve axial Ni/Au cap/interface law from original layers'}
  else:
   source=old['domain_metadata'][name]
   data={'material':source['material'],'sources':source['source_names'],'stage':source['stage'],
     'constitutive_requirement':source.get('constitutive_assignment','UNSET')}
   if source['material']=='COMPOSITE_MULTILAYER':
    data['layer_stack']=source['layer_stack']
    if len(data['layer_stack'])<2:raise ValueError('lost original layer stack')
  if data['material'] in ('N','P'):
   if data['stage'] not in (0,1,2):raise ValueError('missing stage')
   stagecounts[data['stage']]+=1
  materials[data['material']]+=1
  domain[name]=dict(id=tag,**data,law_status='UNSET',solver_ready=False)
 if len(domain)!=428 or stagecounts!=Counter({0:58,1:22,2:8}) or materials['COMPOSITE_MULTILAYER']!=98:
  raise ValueError('R2 domain law classification fails')
 shell_byface={int(q['derived_lead_gas_face']):q for q in s['mapping']}
 dielectric={'Glass','Al2O3','EP29LPSP','Sapphire','Polyimide_candidate','ZnSe_candidate'}
 faces=[];terminals=Counter();classified=Counter()
 for k,f in sorted(r['face_registry'].items(),key=lambda x:int(x[0])):
  tag=int(k);klass=f['class'];owners=f['owners']
  base={'face_tag':tag,'owner_names':owners,'owner_ids':f['owner_volume_ids'],
    'outward_normals':f['orientation_signs'],'area_m2':f['face_area_mm2']*1e-6,
    'center_m':[x*.001 for x in f['center_mm']],
    'interface_class':klass,'coefficient_status':'UNSET','solver_ready':False}
  if klass=='GAS_SOLID':
   sol=next(n for n in owners if n!='CAVITY_GAS')
   base.update(thermal='GAS_CONDUCTION_REGIME_UNSET',electrical='GAS_ELECTRIC_INSULATION',
      structural='GAS_PRESSURE_LOAD_UNSET',radiation='CANDIDATE_SURFACE_TO_SURFACE_RADIATION',
      optical='MCT_ABSORPTION_CANDIDATE' if sol=='p_HgCdTe_photoconductor' else ('WINDOW_SOURCE_CANDIDATE' if sol=='window' else 'NONE'),
      dielectric_shell='SOURCE_POLYIMIDE_SUBFACE_GEOMETRY_REQUIRED' if tag in shell_byface else 'NONE',
      shell_coverage=shell_byface.get(tag))
  elif klass=='SOLID_SOLID':
   mats=[domain[n]['material'] for n in owners]
   base.update(thermal='FINITE_INTERFACE_LAW_UNSET',
      electrical='DIELECTRIC_INSULATED' if any(x in dielectric for x in mats) else 'FINITE_CONTACT_OR_CONTINUITY_UNSET',
      structural='BONDED_OR_SLIP_NOT_QUALIFIED',radiation='NONE',optical='NONE',dielectric_shell='NONE')
  elif klass=='EXTERIOR':
   name=owners[0];bbox=f['bbox_mm'];end=(name.startswith('pin') and name[3:].isdigit() and name in ('pin1','pin7','pin8','pin9')
      and abs(bbox[2]+12.7)<1e-4 and abs(bbox[5]+12.7)<1e-4)
   terminal='TERMINAL_'+name.upper() if end else 'NONE'
   if end:terminals[terminal]+=1
   base.update(thermal='EXTERNAL_BC_UNSET',electrical=terminal if end else 'EXPOSED_INSULATED_UNSET',
      structural='SUPPORT_OR_TRACTION_UNSET',radiation='EXTERNAL_RADIATION_CANDIDATE' if name.startswith('cap') or name=='window' else 'NONE',
      optical='WINDOW_EXTERNAL_ILLUMINATION' if name=='window' else 'NONE',dielectric_shell='NONE')
  else:raise ValueError('unknown interface class '+klass)
  base['ceramic_stage_ports']=[n for n in owners if n in ('ceramic0','ceramic1','ceramic2','ceramic3')]
  classified[klass]+=1;faces.append(base)
 if len(faces)!=2422 or classified!=Counter({'GAS_SOLID':1832,'SOLID_SOLID':547,'EXTERIOR':43}):
  raise ValueError('missing faces')
 if set(terminals)!={'TERMINAL_PIN1','TERMINAL_PIN7','TERMINAL_PIN8','TERMINAL_PIN9'} or any(v!=1 for v in terminals.values()):
  raise ValueError('terminal coverage incorrect '+str(terminals))
 result={'status':'PASS COMPLETE 428 DOMAINS/2422 FACES LAW REQUIREMENTS; ALL COEFFICIENTS UNSET',
   'source_R2_integrity_sha256':sha(integrity),'original_R1_ownership_sha256':sha(old_source),
   'source_shell_projection_sha256':sha(shell),'solver_ready':False,
   'domain_material_counts':dict(materials),'stage_leg_counts':dict(stagecounts),
   'class_face_counts':dict(classified),'terminal_face_counts':dict(terminals),
   'domain_requirements':domain,'face_requirements':faces,
   'unqualified_operators':['lead polymer jacket partial end subfaces','axial Ni/Au terminal coatings','composite laminate constitutive tensors','gas pressure and radiation boundaries','original failed electrical transport method'],
   'no_PDE':True}
 output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(result['status'])
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--original',type=Path,required=True);p.add_argument('--integrity',type=Path,required=True)
 p.add_argument('--shell',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();generate(a.original,a.integrity,a.shell,a.out)
