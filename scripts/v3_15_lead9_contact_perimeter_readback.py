#!/usr/bin/env python3
"""No-solve original Gate B P2 raw-gradient vs native contact-law consistency.

Read-only: original 28,691-TET4 P1 geometry/J and preregistered P2 field.
Exactly reproduce both P1 and P2 material-side currents on two original
lead9 interfaces, then attribute local side-to-side mismatch to geometric
element-quality strata. Never claim causality from correlations.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from tecooledmct.v3_et_fem import tensors,SCENARIOS
ROOT=Path('/work')
B=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/fine35'
P2=ROOT/'data/v3_14_native_net88_perimeter_resolution_20261109/attempt01'
def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
def score(v):
 # Normalized mean ratio: regular TET4 = 1, zero volume = 0.
 ec=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
 e2=sum(np.einsum('ti,ti->t',v[:,a]-v[:,b],v[:,a]-v[:,b]) for a,b in ec)
 d=np.linalg.det(np.stack((v[:,1]-v[:,0],v[:,2]-v[:,0],v[:,3]-v[:,0]),axis=2))
 vol=np.abs(d)/6
 q=12*(3*vol)**(2/3)/e2
 # Longest edge divided by minimum altitude of tetrahedron.
 emax=np.sqrt(np.maximum.reduce([np.sum((v[:,a]-v[:,b])**2,axis=1) for a,b in ec]))
 af=np.stack([.5*np.linalg.norm(np.cross(v[:,b]-v[:,a],v[:,c]-v[:,a]),axis=1)
              for a,b,c in ((1,2,3),(0,2,3),(0,1,3),(0,1,2))],axis=1)
 altitude=3*vol/np.max(af,axis=1)
 assert np.all(q>0) and np.all(altitude>0)
 return q,emax/altitude,altitude,vol
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--out',type=Path)
 parser.add_argument('--verify-only',action='store_true',help='Reconstruct and compare exact archived receipt without writing')
 args=parser.parse_args()
 inp=(B/'mesh.npz',B/'registry.json',ROOT/'data/v3_interconnect_et_20261102/B/fine_field/fields.npz',
     ROOT/'data/v3_interconnect_et_20261102/B/fine_field/result.json',ROOT/'data/v3_interconnect_et_20261102/B/gate_B.json',
     P2/'P2_candidate_h035_result.json',P2/'P2_candidate_h035_field.npz',
     P2/'independent_readback.json')
 g=np.load(inp[0]);metadata=json.loads(inp[1].read_text());j1=np.zeros((len(g['cells']),3))
 p1=json.loads(inp[3].read_text());gstatus=json.loads(inp[4].read_text())
 p2=json.loads(inp[5].read_text());coef=np.load(inp[6])['field']
 verified=json.loads(inp[7].read_text())
 assert p2['status']=='STOP prospective new-h P2 raw current gate'
 assert gstatus['status']=='FAIL/STOP'
 xyz=g['points'];tet=g['cells'];material=g['regions'];tri=g['triangles'];tags=g['faceids']
 assert (len(tet),len(tri),len(coef))==(47277,25890,92495)
 sigma=tensors(metadata['groups'],mode='electric',scenario='NOM')
 owners={int(f['tag']):f for f in metadata['faces']}
 ii=next(k for k,x in enumerate(metadata['groups']) if x['name']=='lead9')
 ll=next(k for k,x in enumerate(metadata['groups']) if x['name']=='lead_land')
 lp=next(k for k,x in enumerate(metadata['groups']) if x['name']=='lead_pin')
 assert len({ii,ll,lp})==3
 sel=np.array([len(owners[int(t)]['owners'])==2 and
              set(owners[int(t)]['owners']) in ({ii,ll},{ii,lp}) for t in tags],bool)
 native=tri[sel];facetag=tags[sel]
 assert len(native)>318
 # Reconstruct original face-side tet indices, no trust of producer incidence.
 faceall=np.vstack((tet[:,[1,2,3]],tet[:,[0,2,3]],
                    tet[:,[0,1,3]],tet[:,[0,1,2]]))
 faceall.sort(axis=1)
 tids=np.tile(np.arange(len(tet),dtype=np.int32),4)
 dt=np.dtype([('a','<i4'),('b','<i4'),('c','<i4')])
 tokey=lambda v:np.ascontiguousarray(v,dtype=np.int32).view(dt).reshape(-1)
 order=np.argsort(tokey(faceall))
 fkeys,start,count=np.unique(tokey(faceall[order]),return_index=True,return_counts=True)
 lookup=np.searchsorted(fkeys,tokey(np.sort(native,axis=1)))
 assert np.all(lookup<len(fkeys))
 assert np.array_equal(fkeys[lookup],tokey(np.sort(native,axis=1)))
 assert np.all(count[lookup]==2)
 t0=tids[order][start[lookup]];t1=tids[order][start[lookup]+1]
 flip=material[t0]!=ii
 a=np.where(flip,t1,t0);b=np.where(flip,t0,t1)
 assert np.all(material[a]==ii)
 assert all(material[e] in (ll,lp) for e in b)
 fxyz=xyz[native]
 face_area=.5*np.linalg.norm(np.cross(fxyz[:,1]-fxyz[:,0],fxyz[:,2]-fxyz[:,0]),axis=1)
 area_vec=.5*np.cross(fxyz[:,1]-fxyz[:,0],fxyz[:,2]-fxyz[:,0])
 ctr=fxyz.mean(axis=1)
 orientation=np.einsum('fi,fi->f',area_vec,ctr-xyz[tet[a]].mean(axis=1))
 assert np.all(np.abs(orientation)>0)
 area_vec[orientation<0]*=-1
 coords=xyz[tet]
 quality,aspect,alt,vol=score(coords)
 # Original P1 independently face-integrated raw fields.
 p1a=np.einsum('fi,fi->f',j1[a],area_vec)
 p1b=-np.einsum('fi,fi->f',j1[b],area_vec)
 # Original P2 coefficient vector, registered region-separated edge numbering.
 pairs=np.column_stack((np.repeat(material,4),tet.ravel()))
 node_tag,back=np.unique(pairs,axis=0,return_inverse=True)
 conn4=back.reshape(-1,4)
 ep=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
 all_edges=np.vstack([np.sort(conn4[:,[i,j]],axis=1) for i,j in ep])
 edges,rev=np.unique(all_edges,axis=0,return_inverse=True)
 conn10=np.column_stack((conn4,rev.reshape(6,len(tet)).T+len(node_tag)))
 assert len(node_tag)+len(edges)==len(coef)
 def p2current(tindices):
  # Inverse Jacobian barycentric derivatives for each real saved TET4.
  v=coords[tindices];e=np.stack((v[:,1]-v[:,0],v[:,2]-v[:,0],v[:,3]-v[:,0]),axis=2)
  inv=np.linalg.inv(e)
  zz=np.einsum('fij,fj->fi',inv,ctr-v[:,0])
  lamb=np.column_stack((1-zz.sum(axis=1),zz))
  ref=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
  gradlam=np.einsum('aj,fji->fai',ref,inv)
  gvert=(4*lamb-1)[:,:,None]*gradlam
  gedge=np.stack([4*(lamb[:,i,None]*gradlam[:,j,:]+lamb[:,j,None]*gradlam[:,i,:])
          for i,j in ep],axis=1)
  gradv=np.einsum('fi,fij->fj',coef[conn10[tindices]],np.concatenate((gvert,gedge),axis=1))
  return -np.einsum('fij,fj->fi',sigma[material[tindices]],gradv)
 v2a=p2current(a);v2b=p2current(b)
 p2a=np.einsum('fi,fi->f',v2a,area_vec)
 p2b=-np.einsum('fi,fi->f',v2b,area_vec)
 # Independent material-edge polynomial face flux integral using three
 # edge midpoint potential jump values (vertex quadratic shape integrals=0).
 keytype=np.dtype([('i','<i4'),('j','<i4')])
 ek=lambda x:np.ascontiguousarray(x,dtype=np.int32).view(keytype).reshape(-1)
 sortedek=ek(edges)
 nodemap={(int(r),int(v)):idx for idx,(r,v) in enumerate(node_tag)}
 P2contact=[]
 for i,f in enumerate(native):
  mat_a=ii;mat_b=int(material[b[i]])
  verts_a=np.array([nodemap[(mat_a,int(v))] for v in f],np.int32)
  verts_b=np.array([nodemap[(mat_b,int(v))] for v in f],np.int32)
  def mids(v):
   ps=np.array([sorted((int(v[x]),int(v[y]))) for x,y in ((0,1),(0,2),(1,2))],np.int32)
   idx=np.searchsorted(sortedek,ek(ps))
   assert np.array_equal(sortedek[idx],ek(ps))
   return coef[len(node_tag)+idx]
  P2contact.append(face_area[i]*float(np.mean(mids(verts_a)-mids(verts_b)))/SCENARIOS['NOM']['re'])
 p2contact=np.asarray(P2contact)
 # Face signed mismatch, do not confuse with actual charge source.
 mismatch1=p1a+p1b;mismatch2=p2a+p2b
 unit1=p1['unit_potential_current_A'];unit2=p2['P2_unit_potential_current_A']
 original1={tuple(x['pair']):x for x in p1['cuts'] if 'pair' in x}
 original2={tuple(x['pair']):x for x in p2['P2_cuts'] if 'pair' in x}
 result={}
 for bname,regid in (('lead_land',ll),('lead_pin',lp)):
  mask=material[b]==regid
  x=(metadata['groups'][ii]['name'],bname)
  assert x in original1 and x in original2
  x1=original1[x];x2=original2[x]
  assert abs(p2a[mask].sum()-x2['raw_a_A'])/unit2<1e-11
  assert abs(p2b[mask].sum()-x2['raw_b_A'])/unit2<1e-11
  assert abs(p2contact[mask].sum()-x2['natural_A'])/unit2<1e-11
  areas=face_area[mask]
  # Original candidate errors are topological current witness errors, not
  # equal to sum |side-to-side jumps| at a local face.
  score1=np.maximum(np.abs(p1a[mask]+p1b[mask]),0)
  score2=np.maximum(np.abs(p2a[mask]+p2b[mask]),0)
  metrics=[]
  q=np.minimum(quality[a[mask]],quality[b[mask]])
  aratio=np.maximum(aspect[a[mask]],aspect[b[mask]])
  contact=np.abs(p2contact[mask])
  # Diagnostic relative local mismatch normalized by reference contact
  # current density, uses abs current as scale for robust face ranking.
  rel_local=score2/(np.abs(p2a[mask])+np.abs(p2b[mask])+contact+1e-30)
  for threshold in (.01,.05,.1,.2):
   low=q<threshold
   metrics.append({'q_cut':threshold,'fraction_of_face_count':float(low.mean()),
         'fraction_of_contact_area':float(areas[low].sum()/areas.sum()),
         'fraction_of_absolute_P2_two_side_mismatch':float(score2[low].sum()/max(score2.sum(),1e-30)),
         'mean_local_relative_jump_low_quality':float(np.average(rel_local[low],weights=areas[low])) if low.any() else None,
         'mean_local_relative_jump_other':float(np.average(rel_local[~low],weights=areas[~low])) if (~low).any() else None})
  sorting=np.argsort(score2)[::-1]
  top=max(1,int(np.ceil(.1*len(sorting))))
  # no changes to mesh; see whether errors cluster spatially on source faces
  high=sorting[:top]
  xyzcent=ctr[mask]
  qarea=lambda arr:float(np.quantile(arr,q))
  share=np.sort(score2)[-top:].sum()/score2.sum()
  record={
   'interface':'lead9 → '+bname,'source_registered_triangles':int(mask.sum()),
   'source_registered_face_tags':list(map(int,np.unique(facetag[mask]))),
   'source_interface_area_m2':float(areas.sum()),
   'original_P1_gate_error_rel':None,
   'prospective_P2_gate_error_rel':x2['gate_error'],
   'original_P1_raw_a_A':None,
   'original_P1_raw_b_out_A':None,
   'prospective_P2_raw_a_A':float(p2a[mask].sum()),
   'prospective_P2_raw_b_out_A':float(p2b[mask].sum()),
   'prospective_P2_contact_integral_A':float(p2contact[mask].sum()),
   'P1_signed_two_side_raw_mismatch_A':None,
   'P2_signed_two_side_raw_mismatch_A':float(mismatch2[mask].sum()),
   'P1_gross_abs_two_side_raw_mismatch_A':None,
   'P2_gross_abs_two_side_raw_mismatch_A':float(score2.sum()),
   'gross_abs_mismatch_P1_over_P2_ratio':None,
   'P2_face_abs_mismatch_top10pct_share':float(share),
   'P2_face_abs_mismatch_top10pct_center_bbox_m':[xyzcent[high].min(axis=0).tolist(),xyzcent[high].max(axis=0).tolist()],
   'source_triangle_area_m2_p01_p50_p99':list(map(float,np.quantile(areas,[.01,.5,.99]))),
   'adjacent_worst_tetra_meanratio_quality_min_p01_median_p99':list(map(float,[q.min(),*np.quantile(q,[.01,.5,.99])])),
   'adjacent_worst_tetra_aspect_max_p50_p95':list(map(float,[aratio.max(),*np.quantile(aratio,[.5,.95])])),
   'adjacent_minimum_tetra_altitude_m_p01':float(np.quantile(np.minimum(alt[a[mask]],alt[b[mask]]),.01)),
   'adjacent_q_strata':metrics,
   'P2_local_jump_median':float(np.median(rel_local)),
   'P2_local_jump_p95':float(np.quantile(rel_local,.95)),
   'P2_face_quality_mismatch_correlation_log10_q':float(np.corrcoef(np.log10(q),np.log10(score2+1e-15))[0,1]),
   'correlation_is_not_causation':True}
  # Independently reconstructed current density on exactly the same saved
  # native face. Contact-law traction uses the per-face integrated P2
  # jump: equal/opposite weak current, not a replacement for raw J.
  weak=p2contact[mask]
  a_current=p2a[mask]          # outward from lead9
  b_current=-p2b[mask]         # oriented lead9 -> second owner
  normalizer=abs(unit2)
  assert abs(weak.sum()-x2['natural_A'])/normalizer<1e-11
  assert abs(a_current.sum()-x2['raw_a_A'])/normalizer<1e-11
  assert abs(b_current.sum()+x2['raw_b_A'])/normalizer<1e-11
  assert abs(weak.sum())>1
  # L2 is evaluated on per-triangle integrated currents with area
  # weighting, which equals an L2 face-current-DENSITY discrepancy
  # for a piecewise constant average face flux.
  # Uniform multiplicative bias from least squares of raw against weak
  # is only a diagnostic, not a fitted/validated contact coefficient.
  def owner_diagnostic(raw):
   diff=raw-weak
   net=float(diff.sum())
   abs_sum=float(np.abs(diff).sum())
   same=np.sign(diff)==np.sign(net)
   weighted=np.sum(np.abs(diff[same]))/abs_sum if abs_sum>0 else 0.
   alpha=float(np.sum(raw*weak/areas)/np.sum(weak*weak/areas))
   original_sq=float(np.sum(diff*diff/areas))
   scaled_sq=float(np.sum((raw-alpha*weak)**2/areas))
   assert scaled_sq<=original_sq*(1+1e-10)
   cv=lambda v:float(np.sqrt(np.sum(v*v/areas)/np.sum(weak*weak/areas)))
   return {'signed_bias_A':net,
      'signed_bias_relative_to_unit_drive':net/normalizer,
      'sum_absolute_face_bias_A':abs_sum,
      'gross_to_signed_bias_ratio':abs_sum/max(abs(net),1e-20),
      'area_share_with_same_signed_bias_as_net':float(areas[same].sum()/areas.sum()),
      'absolute_residual_share_aligned_with_net_bias':float(weighted),
      'raw_to_contact_integrated_current_ratio':float(raw.sum()/weak.sum()),
      'uniform_contact_multiplicative_least_square_alpha':alpha,
      'fraction_of_density_L2_residual_explained_by_single_scale':float(1-scaled_sq/original_sq) if original_sq>0 else 0.,
      'RMS_density_error_relative_to_weak_contact_density_RMS':cv(diff),
      'max_absolute_face_mismatch_A':float(np.max(np.abs(diff))),
      'median_local_abs_flux_discrepancy_relative':float(np.median(abs(diff)/(np.maximum(np.abs(weak),normalizer*1e-12)))),
      'P95_local_abs_flux_discrepancy_relative':float(np.quantile(abs(diff)/(np.maximum(np.abs(weak),normalizer*1e-12)),.95)),
      }
  da=owner_diagnostic(a_current)
  db=owner_diagnostic(b_current)
  # Triangle-centroid radial bins on each registered circular metal
  # contact; not an exact clipping/intersection of curved circle arcs.
  regtag=int(np.unique(facetag[mask])[0])
  cad=owners[regtag]
  bb=cad['bbox_mm']
  ctr_xy=np.array([(bb[0]+bb[3])/2,(bb[1]+bb[4])/2])*1e-3
  rad=np.sqrt(float(cad['area_m2'])/np.pi)
  local_r=np.linalg.norm(xyzcent[:,:2]-ctr_xy,axis=1)/rad
  assert local_r.max()<=1.05
  bands=[]
  for lower,upper in ((0.,.5),(.5,.75),(.75,.9),(.9,1.05)):
   selected=(local_r>=lower)&(local_r<upper)
   frac=float(areas[selected].sum()/areas.sum())
   aa=abs(a_current[selected]-weak[selected])
   bbv=abs(b_current[selected]-weak[selected])
   bands.append({'radius_over_CAD_radius_range':[lower,upper],
       'triangle_count':int(selected.sum()),
       'area_fraction':frac,
       'fraction_of_abs_mismatch_on_lead9_side':float(aa.sum()/max(np.abs(a_current-weak).sum(),1e-30)),
       'fraction_of_abs_mismatch_on_second_material_side':float(bbv.sum()/max(np.abs(b_current-weak).sum(),1e-30)),
       'signed_lead9_bias_A':float(np.sum(a_current[selected]-weak[selected])),
       'signed_other_side_bias_A':float(np.sum(b_current[selected]-weak[selected]))})
  assert sum(x['triangle_count'] for x in bands)==int(mask.sum())
  assert abs(sum(x['area_fraction'] for x in bands)-1)<1e-12
  # Signed mismatch split exactly by side; no false "current source".
  assert abs((a_current-b_current).sum()-(netval:=float(p2a[mask].sum()+p2b[mask].sum())))<1e-11
  assert abs((da['signed_bias_A']-db['signed_bias_A'])-netval)<1e-11
  record['contact_operator_consistency']={
    'weak_contact_current_A':float(weak.sum()),
    'raw_lead9_oriented_current_A':float(a_current.sum()),
    'raw_other_side_oriented_current_A':float(b_current.sum()),
    'mean_contact_flux_density_A_per_m2':float(weak.sum()/areas.sum()),
    'P2_contact_density_sign_consistent_area_fraction':float(areas[weak*weak.sum()>0].sum()/areas.sum()),
    'raw_lead9_side':da,
    'raw_other_material_side':db,
    'signed_two_side_raw_difference_from_side_bias_A':netval,
    'CAD_contact_radius_m':rad,
    'saved_triangle_centroid_radius_over_CAD_radius_min_max':[float(local_r.min()),float(local_r.max())],
    'radial_triangle_centroid_bins':bands,
    'method':'No fit; P2 full element gradient integrated exactly on each flat triangle centroid; contact P2 potential jump integrated by 3 globally unique edge mids',
    'nonconforming_raw_gradient_is_not_contact_traction':True}
  result[bname]=record
 assert len(result)==2
 output={
  'status':'PASS no-solve V3.14 new h035 P2 lead9 native contact-law/element-gradient comparison; physical electrical gate FAIL/STOP',
  'original_P1_gate_B':'FAIL/STOP',
  'prospective_P2_gate_B':'FAIL/STOP h035',
  'new_coupon_source_tets':len(tet),
  'source_P2_field_DOFS':len(coef),
  'native_lead9_triangles':len(native),
  'source_fixed_original_geometry':True,
  'physical_laws_unchanged':True,
  'original_0p1pct_gate_unchanged':True,
  'metrics_interpretation':'Normalized mean-ratio q=12*(3*V)^(2/3)/sum_e(edge_length^2); q regular tetra=1, small q indicates poor shape. Local two-sided raw mismatch is nonconforming numerical trace, NOT a charge source or certified independent residual.',
  'lead_interfaces':result,
  'input_sha256':{str(x.relative_to(ROOT)):hashfile(x) for x in inp},
  'independent_original_current_integrals_reproduced':True,
  'P2_saved_field_unchanged':True,
  'no_PDE_or_mesh_changes':True}
 if args.verify_only:
  assert args.out is not None and args.out.is_file(), 'Need existing --out archived receipt for read-only verification'
  assert json.loads(args.out.read_text())==output,'Archived receipt differs from reconstructed original sources'
 elif args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  with args.out.open('x') as handle:
   json.dump(output,handle,indent=2)
   handle.write('\n')
 print('LEAD9_CONTACT_OPERATOR_AUDIT_PASS')
 for label,x in result.items():
  op=x['contact_operator_consistency']
  print('CONTACT_BIAS',label,'weak_A',op['weak_contact_current_A'],'raw_lead_A',op['raw_lead9_oriented_current_A'],'raw_other_A',op['raw_other_side_oriented_current_A'],'lead_alpha',op['raw_lead9_side']['uniform_contact_multiplicative_least_square_alpha'],'other_alpha',op['raw_other_material_side']['uniform_contact_multiplicative_least_square_alpha'],'lead_scale_explained',op['raw_lead9_side']['fraction_of_density_L2_residual_explained_by_single_scale'],'other_scale_explained',op['raw_other_material_side']['fraction_of_density_L2_residual_explained_by_single_scale'])
  print(label,'P2_GATE_PCT',100*x['prospective_P2_gate_error_rel'],
        'NTRI',x['source_registered_triangles'],'qMED',x['adjacent_worst_tetra_meanratio_quality_min_p01_median_p99'][2],
        'q<0.05',x['adjacent_q_strata'][1]['fraction_of_contact_area'],
        'top10_absjump',x['P2_face_abs_mismatch_top10pct_share'])
if __name__=='__main__':main()
