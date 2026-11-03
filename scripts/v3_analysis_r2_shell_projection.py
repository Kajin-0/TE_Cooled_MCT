"""Trace original inner lead/polyimide faces onto the analysis-only R2 shell operators.

Partial face coverage is explicitly a solver BLOCKER; no averaging/guessing.
"""
from pathlib import Path
import argparse,hashlib,json,math

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(original,derived,out):
 if out.exists():raise ValueError('Refuse overwrite')
 old=json.loads(original.read_text())['interface_records']
 new=json.loads(derived.read_text())['face_registry']
 result={'source_438_domain_registry_sha256':sha(original),
  'r2_428_domain_registry_sha256':sha(derived),
  'mapping':[],'status':'PENDING','solver_ready':False,
  'boundary_model':'15um dielectric annulus reduced to boundary shell; radial/axial coefficients UNSET; no homogenized Cu'}
 for pin in (1,9):
  lead=f'TEC_lead{pin}';jacket=f'lead{pin}_insulation'
  originals=[f for f in old if {o['source_name'] for o in f['owners']}=={lead,jacket}]
  candidates=[f for f in new.values() if set(f['owners'])=={lead,'CAVITY_GAS'}]
  if len(originals)!=5 or len(candidates)!=5:raise ValueError('missing lead source shell')
  matched=set()
  for q in originals:
   xy=[v*1000 for v in q['center_m'][:2]]
   comp=[(math.dist(xy,f['center_mm'][:2]),f) for f in candidates if f['face_tag'] not in matched]
   delta,chosen=min(comp,key=lambda v:v[0])
   if delta>1e-5:raise ValueError('shell XY projected center mismatch '+str(q['face_tag']))
   old_area=q['area_m2']*1e6;new_area=chosen['face_area_mm2']
   if old_area>new_area*(1+1e-6):raise ValueError('physical shell area exceeds destination')
   fraction=old_area/new_area
   condition=('FULL_FACE_MATCH' if abs(fraction-1)<1e-6 else 'PARTIAL_SUBFACE_OPERATOR_REQUIRED')
   result['mapping'].append({'original_lead_polyimide_face':q['face_tag'],
     'derived_lead_gas_face':chosen['face_tag'],'physical_jacket':jacket,
     'physical_Cu':lead,'physical_inner_area_mm2':old_area,
     'derived_face_area_mm2':new_area,'coverage_area_fraction_only':fraction,
     'condition':condition,'constitutive_law_status':'UNSET',
     'boundary_quadrature':'SOURCE_GEOMETRY_SUBFACE_REQUIRED' if condition.startswith('PARTIAL') else 'FULL_FACE'})
   matched.add(chosen['face_tag'])
  if len(matched)!=5:raise ValueError('nonbijection in dielectric shell')
 if len(result['mapping'])!=10:raise ValueError('shell map incomplete')
 result['full_face_count']=sum(q['condition']=='FULL_FACE_MATCH' for q in result['mapping'])
 result['partial_face_count']=len(result['mapping'])-result['full_face_count']
 if (result['full_face_count'],result['partial_face_count'])!=(6,4):
  raise ValueError('unexpected end of insulation footprint')
 result['status']='PASS SOURCE SHELL PROJECTION; PARTIAL SUBFACE BC UNQUALIFIED'
 out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(result['status'],result['full_face_count'],'complete faces',result['partial_face_count'],'partial',flush=True)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--original',type=Path,required=True);p.add_argument('--derived',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();run(a.original,a.derived,a.out)
