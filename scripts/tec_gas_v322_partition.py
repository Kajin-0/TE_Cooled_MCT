"""Rectangular source-solid ceramic face partition; no PDE or simulated heat flow."""
from pathlib import Path
from collections import Counter
import json,hashlib,math
R=Path(__file__).resolve().parents[1];D=R/'data/tec_gas_partition_20261110'
S={'nominal':R/'data/synthetic_v3_assembly_20261102/source_final/design.json','custom':R/'data/tec_height_060_cad_20261110/source_candidate/design.json'}
META=R/'data/v3_r32_global_surface_20261103/source_metadata.json'
TOL=1e-8

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def intersect(a,b):
 x,y=max(a[0],b[0]),max(a[1],b[1]);u,v=min(a[2],b[2]),min(a[3],b[3]);return (x,y,u,v) if u-x>TOL and v-y>TOL else None

def partition(face,contacts,facing):
 """Return disjoint rectangle-ownership cells; source rectangles overlap within a film."""
 rects=[q for _,q in contacts];cut=[face]+rects+([facing] if facing else [])
 xs=sorted(set([face[0],face[2]]+[x for q in cut for x in (q[0],q[2]) if face[0]<x<face[2]]));ys=sorted(set([face[1],face[3]]+[y for q in cut for y in (q[1],q[3]) if face[1]<y<face[3]]))
 out={'solid_contact':0.,'facing_gap_unblocked_at_face':0.,'outer_unblocked_at_face':0.};owners={}
 for x,X in zip(xs,xs[1:]):
  for y,Y in zip(ys,ys[1:]):
   if X-x<TOL or Y-y<TOL:continue
   a=(x+X)/2;b=(y+Y)/2;hits=sorted({n for n,q in contacts if q[0]<a<q[2] and q[1]<b<q[3]});area=(X-x)*(Y-y)
   if len(hits)>1:raise ValueError(('overlapping physical solid contacts',hits))
   if hits:out['solid_contact']+=area;owners[hits[0]]=owners.get(hits[0],0.)+area
   elif facing and facing[0]<a<facing[2] and facing[1]<b<facing[3]:out['facing_gap_unblocked_at_face']+=area
   else:out['outer_unblocked_at_face']+=area
 assert abs(sum(out.values())-(face[2]-face[0])*(face[3]-face[1]))<1e-8
 return out,owners

def audit(design,meta):
 bodies=design['bodies'];by={x['name']:x for x in bodies};rows=[]
 for stage in range(4):
  c=by[f'ceramic{stage}'];x,y,z,w,h,t=c['boxes_mm'][0]
  for axis,edge in [(2,0),(2,1),(0,0),(0,1),(1,0),(1,1)]:
   lo=[x,y,z];hi=[x+w,y+h,z+t];plane=(lo,hi)[edge][axis];axes=[a for a in range(3) if a!=axis];face=(lo[axes[0]],lo[axes[1]],hi[axes[0]],hi[axes[1]])
   contacts=[];uncertain=[]
   for b in bodies:
    if b['id']==c['id']:continue
    if b['shape']=='boxes':
     for q in b['boxes_mm']:
      b0=q[:3];b1=[q[i]+q[i+3] for i in range(3)]
      if abs((b0 if edge else b1)[axis]-plane)>TOL:continue
      rect=intersect(face,(b0[axes[0]],b0[axes[1]],b1[axes[0]],b1[axes[1]]))
      if rect:contacts.append((b['name'],rect))
    else:
     q=b['bbox_mm'];b0=q[:3];b1=q[3:]
     if b0[axis]-TOL<=plane<=b1[axis]+TOL and intersect(face,(b0[axes[0]],b0[axes[1]],b1[axes[0]],b1[axes[1]])):uncertain.append(b['name'])
   facing=None
   if axis==2:
    other=stage+(1 if edge else -1)
    if 0<=other<4:
     q=by[f'ceramic{other}']['boxes_mm'][0];facing=intersect(face,(q[0],q[1],q[0]+q[3],q[1]+q[4]))
   areas,owners=partition(face,contacts,facing)
   original_z=plane-(0 if design['id']!='synthetic_architecture_B_custom_height_060' else stage*.1) if axis==2 else None
   # R3 analysis replaces source thin films by thicker effective Cu; tags describe derived CAD, not original layer material.
   faces=[]
   for tag,f in meta.items():
    if c['name'] not in f['owners']:continue
    bb=f['bbox_mm'];coord=f['center_mm'][axis];origin=original_z if axis==2 else plane
    if abs(coord-origin)<1e-6 and abs(bb[axis+3]-bb[axis])<1e-5:faces.append({'tag':int(tag),'owners':f['owners'],'area_mm2':f['face_area_mm2'],'class':f['class_']})
   gas=sum(f['area_mm2'] for f in faces if f['class']=='GAS_SOLID');solid=sum(f['area_mm2'] for f in faces if f['class']=='SOLID_SOLID')
   rows.append({'ceramic':c['name'],'face':f'{"xyz"[axis]}{"+" if edge else "-"}','plane_mm':plane,'area_mm2':(face[2]-face[0])*(face[3]-face[1]),'partition_mm2':areas,'source_contact_owners_mm2':owners,'source_nonbox_bbox_candidates':uncertain,'derived_R3_faces':faces,'derived_R3_gas_mm2':gas,'derived_R3_solid_mm2':solid,'source_vs_R3_contact_difference_mm2':areas['solid_contact']-solid})
 gaps=[]
 for i in range(3):
  a=by[f'ceramic{i}']['boxes_mm'][0];b=by[f'ceramic{i+1}']['boxes_mm'][0];gaps.append(b[2]-a[2]-a[5])
 return {'id':design['id'],'body_count':len(bodies),'shape_counts':dict(Counter(x['shape'] for x in bodies)),'material_counts':dict(Counter(x['material'] for x in bodies)),'substrate_gaps_mm':gaps,'faces':rows,'source_nonbox_uncertain_count':sum(len(r['source_nonbox_bbox_candidates']) for r in rows)}

def main():
 reg=json.loads((D/'registration.json').read_text())
 for p,h in reg['sources_sha256'].items():assert digest(R/p)==h,p
 meta=json.loads(META.read_text())['faces'];out={k:audit(json.loads(p.read_text()),meta) for k,p in S.items()}
 for variant in out.values():assert variant['body_count']==824 and len(variant['faces'])==24
 result={'status':'SOURCE RECTANGLE PARTITION; physical void/transport NOT QUALIFIED','scope':'direct-contact rectangle partition; projected facing is not a visibility/connected-void solution; nonbox bbox candidates unresolved','designs':out}
 p=D/'source_partition.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 for k,v in out.items():
  print(k,'gaps',v['substrate_gaps_mm'],'nonbox',v['source_nonbox_uncertain_count'])
  for row in v['faces']:
   print(row['ceramic'],row['face'],{z:round(x,5) for z,x in row['partition_mm2'].items()},'CAD Δ',round(row['source_vs_R3_contact_difference_mm2'],6),'uncertain',row['source_nonbox_bbox_candidates'])
if __name__=='__main__':main()
