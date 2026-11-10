"""Independent readback against archived R3 face_registry, no FEM solve."""
from pathlib import Path
from collections import Counter
import json,math,hashlib
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_ports_20261110'
def check(reg,meta):
 rows=reg['faces'];tags=[r['face_tag'] for r in rows];assert len(tags)==len(set(tags))==1840
 expected={int(t):v for t,v in meta['face_registry'].items() if v['class_']=='GAS_SOLID'};assert set(tags)==set(expected)
 for r in rows:
  f=expected[r['face_tag']];o=f['owners'];assert o.count('CAVITY_GAS')==1 and len(o)==2
  idx=o.index('CAVITY_GAS');assert r['solid_domain']==o[1-idx] and r['gas_volume_id']==f['owner_volume_ids'][idx] and r['solid_volume_id']==f['owner_volume_ids'][1-idx]
  assert r['gas_orientation_sign']==f['orientation_signs'][idx] and r['solid_orientation_sign']==-r['gas_orientation_sign']
  assert r['area_mm2']==f['face_area_mm2'] and r['centre_mm']==f['center_mm'] and r['bbox_mm']==f['bbox_mm']
  assert r['physical_sources']==meta['domains'][r['solid_domain']]['sources']
  assert r['gas_boundary_condition_installed'] is False
 A=math.fsum(r['area_mm2'] for r in rows);B=math.fsum(v['face_area_mm2'] for v in expected.values());assert abs(A-B)<1e-10
 counts=Counter(r['semantic_category'] for r in rows);assert sum(counts.values())==len(rows)
 return {'status':'PASS independent readback of frozen face_registry; does not independently solve CSG','faces':len(rows),'unique_tags':len(set(tags)),'source_area_mm2':B,'registry_area_mm2':A,'difference_mm2':A-B,'orientation_owner_errors':0,'semantic_counts':dict(counts),'unresolved_semantic_faces':counts['unresolved'],'implemented_gas_face_BCs':0}
def main():
 p=D/'nominal_gas_face_ports.json';meta=json.loads((R/'data/v3_r32_global_surface_20261103/source_metadata.json').read_text());r=check(json.loads(p.read_text()),meta);r['registry_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();q=D/'independent_ports_audit.json';assert not q.exists();q.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
