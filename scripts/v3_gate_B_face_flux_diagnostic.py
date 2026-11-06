#!/usr/bin/env python3
"""No-solve original Gate B per-triangle raw current flux pathology ledger.
Uses only archived tetrahedral mesh, reconstructed original J and registered
face owners; does NOT replace original contact reactions or claim conservation.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/v3_interconnect_et_20261102/B'
mesh=BASE/'fine_mesh/mesh.npz'
field=BASE/'fine_field/fields.npz'
registry=BASE/'fine_mesh/registry.json'
original=BASE/'fine_field/result.json'
coarse=BASE/'coarse_field/result.json'
gate=BASE/'gate_B.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=np.load(mesh);f=np.load(field)
reg=json.loads(registry.read_text())
original_report=json.loads(original.read_text())
old=json.loads(coarse.read_text())
gate_report=json.loads(gate.read_text())
p=a['points'];tet=a['cells'];regions=a['regions'];triangles=a['triangles'];tags=a['faceids']
J=f['J_unitV_A_m2']
assert len(tet)==28691 and len(J)==28691
names={i:x['name'] for i,x in enumerate(reg['groups'])}
d={int(x['tag']):x for x in reg['faces']}
# The 3 geometric coordinates in every original triangle are same physical face.
# Rebuild a sorted vectorized tetrahedron face registry and exact interior owner.
allfaces=np.vstack((tet[:,[1,2,3]],tet[:,[0,2,3]],tet[:,[0,1,3]],tet[:,[0,1,2]]))
allfaces.sort(axis=1)
cellidx=np.tile(np.arange(len(tet),dtype=np.int32),4)
dt=np.dtype([('a','<i4'),('b','<i4'),('c','<i4')])
key=lambda x:np.ascontiguousarray(x,dtype=np.int32).view(dt).reshape(-1)
order=np.argsort(key(allfaces))
sorted_faces=key(allfaces)[order]
sorted_cells=cellidx[order]
unique,start,count=np.unique(sorted_faces,return_index=True,return_counts=True)
assert np.max(count)<=2
sel=np.array([len(d[int(tag)]['owners'])==2 for tag in tags])
facets=triangles[sel]
ftags=tags[sel]
assert len(facets)>0
fkey=key(np.sort(facets,axis=1))
loc=np.searchsorted(unique,fkey)
assert np.all(loc<len(unique)) and np.array_equal(unique[loc],fkey)
assert np.all(count[loc]==2)
idx0=sorted_cells[start[loc]]
idx1=sorted_cells[start[loc]+1]
# Registered source owners ordered by numeric ID.
r0=np.array([d[int(t)]['owners'][0] for t in ftags])
r1=np.array([d[int(t)]['owners'][1] for t in ftags])
swap=regions[idx0]!=r0
assert np.all(np.where(swap,regions[idx1],regions[idx0])==r0)
assert np.all(np.where(swap,regions[idx0],regions[idx1])==r1)
ca=np.where(swap,idx1,idx0);cb=np.where(swap,idx0,idx1)
pos=p[facets]
norm=np.cross(pos[:,1]-pos[:,0],pos[:,2]-pos[:,0])*.5
bary=pos.mean(axis=1)
centerA=p[tet[ca]].mean(axis=1)
reversed_normal=np.einsum('ij,ij->i',norm,bary-centerA)<0
norm[reversed_normal]*=-1
ar=np.linalg.norm(norm,axis=1)
assert np.all(ar>0)
rawA=np.einsum('ij,ij->i',J[ca],norm)
rawB=-np.einsum('ij,ij->i',J[cb],norm)
# Cross-check signed per-cut integration against existing independent saved field.
reference={tuple(x['pair']):x for x in original_report['cuts'] if 'pair' in x}
groups={}
current=float(original_report['unit_potential_current_A'])
for pair,stored in reference.items():
  ra=next(i for i,n in names.items() if n==pair[0])
  rb=next(i for i,n in names.items() if n==pair[1])
  mask=(r0==ra)&(r1==rb)
  assert mask.any(),pair
  # Contact tags can have either global owner order; original pair follows
  # integer-ID order by original operator convention.
  I1=float(np.sum(rawA[mask]));I2=float(np.sum(rawB[mask]))
  assert abs(I1-stored['raw_a_A'])/current<4e-13,(pair,I1,stored['raw_a_A'])
  assert abs(I2-stored['raw_b_A'])/current<4e-13,(pair,I2,stored['raw_b_A'])
  t=ftags[mask]
  abs1=np.abs(rawA[mask]);abs2=np.abs(rawB[mask])
  denom=max(abs(I1),current*1e-15)
  # Natural integrated contact flux is from original independent conserved weak form.
  natural=float(stored['natural_A'])
  # Face-scale raw "error" distribution is diagnostic only: contact forces are
  # NOT represented by a single natural face flux here.
  near=((rawA[mask]+rawB[mask])) # signed outward mismatch per triangle
  groups[' → '.join(pair)]={
   'registered_contact_faces':int(mask.sum()),
   'contact_tag_count':int(len(np.unique(t))),
   'registered_contact_tags':list(map(int,np.unique(t))),
   'area_m2':float(ar[mask].sum()),
   'J_raw_a_sum_A':I1,'J_raw_b_sum_outward_A':I2,
   'registered_contact_weak_current_A':natural,
   'sum_abs_raw_a_A':float(abs1.sum()),
   'sum_abs_raw_b_A':float(abs2.sum()),
   'cancellation_factor_a':float(abs1.sum()/denom),
   'raw_a_triangle_sign_opposition_fraction':float(np.mean(np.sign(rawA[mask])!=np.sign(I1))) if I1!=0 else None,
   'raw_a_area_weighted_opposite_flow_fraction':float(ar[mask][rawA[mask]*I1<0].sum()/ar[mask].sum()) if I1!=0 else None,
   'absolute_two_side_face_flux_disagreement_A':float(np.sum(np.abs(near))),
   'net_two_side_outward_mismatch_A':float(np.sum(near)),
   'RMS_one_triangle_raw_a_A':float(np.sqrt(np.mean(rawA[mask]**2))),
   'largest_one_triangle_raw_a_A':float(abs1.max()),
   'share_of_absolute_raw_a_flux_in_top_10pct_triangles':float(np.sort(abs1)[-max(1,int(np.ceil(.1*len(abs1)))):].sum()/abs1.sum()) if abs1.sum() else None,
   'original_registered_gate_relative_error':stored['gate_error'],
   'observed_maximum_causal_attribution':'NOT IDENTIFIED',
  }
# Rank by original gate error rather than inventing a new gate.
ranked=dict(sorted(groups.items(),key=lambda x:x[1]['original_registered_gate_relative_error'],reverse=True))
receipt={
 'status':'SOURCE-RECONSTRUCTED: 11 fine-mesh original contact faces, raw-current pathology preserved; Gate B remains FAIL/STOP',
 'scope':'NO PDE; original fine tetra/cell J, 2-sided geometric face areas and CAD ownership, original unchanged contact reactions',
 'original_current_A':current,'original_cut_threshold':.001,
 'interface_count':len(ranked),
 'total_registered_contact_triangles':int(len(facets)),
 'face_flux_comparison_caveat':'Elementwise raw P1 current normal is nonconforming; per-triangle signed outward mismatch is NOT physical charge creation or a source term. Original weak natural contact law is only available here as registered aggregate by pair.',
 'face_results':ranked,
 'original_Gate_B_status':gate_report['status'],
 'all_eleven_stored_raw_contact_currents_reconstructed':True,
 'original_weak_contact_currents_not_modified':True,
 'source_sha256':{str(x.relative_to(ROOT)):sha(x) for x in (mesh,field,registry,original,coarse,gate)}
}
parser=argparse.ArgumentParser()
parser.add_argument('--verify-only',action='store_true',help='Verify archived receipt exactly without writing')
parser.add_argument('--out',type=Path,default=ROOT/'data/v3_physical_blocker_closure_20261106/attempt01/gate_B_face_flux_diagnostic.json')
args=parser.parse_args()
out=args.out
if args.verify_only:
    assert out.is_file(),f'Archived receipt missing: {out}'
    assert json.loads(out.read_text())==receipt,'Reconstruction differs from archived evidence'
else:
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as fh:
        json.dump(receipt,fh,indent=2)
        fh.write('\n')
print('FACE_LEDGER',len(ranked),'interfaces',len(facets),'CAD source triangles')
for label,row in list(ranked.items())[:11]:
 print(label,'t=',row['registered_contact_faces'],'error=',round(100*row['original_registered_gate_relative_error'],3),
      '%','cancellation=',round(row['cancellation_factor_a'],3),
      'signopp_area=',round(100*row['raw_a_area_weighted_opposite_flow_fraction'],2),
      '%','top10_flux=',round(100*row['share_of_absolute_raw_a_flux_in_top_10pct_triangles'],2),'%')
