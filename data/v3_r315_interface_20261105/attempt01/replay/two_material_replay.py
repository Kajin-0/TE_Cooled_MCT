#!/usr/bin/env python3
"""R3.15 two-real-region P1/P2 C0 diffusion transmission.
Actual shared CAD face2349, volume410 composite wedge foot & volume420 Au bond.
Artificial k410=1,k420=10; manufactured continuous piecewise quadratic
with nonzero exact normal flux across planar shared interface.
Analytical Neumann on *other* registered exterior region facets, Dirichlet
on face2399, unchanged shared geometric mesh; source CAD/mesh read-only.
"""
import time,json,hashlib,resource,math,itertools
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spilu,gmres,LinearOperator
P=Path('/input');O=Path('/replay');tic=time.monotonic()
tag=2349;dirtag=2399;regions=(410,420);K={410:1.,420:10.}
x0=-.35;y0=0.;z0=5.7849;A=.025;B=.05;Q=1.0
def hashfile(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
metadata=json.loads((P/'source_metadata.json').read_text())
node=np.loadtxt(P/'R38_430_domains.1.node',dtype=float,skiprows=1)
elem=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
fac=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
assert metadata['faces'][str(tag)]['owner_volume_ids']==[410,420]
selected=elem[np.isin(elem[:,5],regions)]
globtet=selected[:,1:5]
material=selected[:,5]
original_nodes=np.unique(globtet)
xyz=node[original_nodes-1,1:4]
tet=np.searchsorted(original_nodes,globtet)
n=len(xyz);nt=len(tet)
assert (nt,n)==(26053,6908)
# Registered native surface for this TWO-material union.
facet_tags=[]
for row in fac:
 owners=metadata['faces'][str(row[4])]['owner_volume_ids']
 if bool(set(owners).intersection(regions)):
  facet_tags.append(row)
native=np.asarray(facet_tags,dtype=np.int32)
internal=native[native[:,4]==tag]
outer=native[native[:,4]!=tag]
assert len(internal)==48 and len(outer)==13586
assert all(len(set(metadata['faces'][str(int(r[4]))]['owner_volume_ids']).intersection(regions))==1 for r in outer)
sf=np.searchsorted(original_nodes,outer[:,1:4])
iface=np.searchsorted(original_nodes,internal[:,1:4])
# Independently establish the exact region interface and exterior side,
# then retain per-face opposite tetrahedron and its material region.
facelocal=((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3))
face_incidence={}
for idx,t in enumerate(tet):
 for a,b,c,o in facelocal:
  tri=(int(t[a]),int(t[b]),int(t[c]))
  key=tuple(sorted(tri))
  face_incidence.setdefault(key,[]).append((idx,tri,int(t[o]),int(material[idx])))
iface_keys={tuple(sorted(x)) for x in iface}
outer_keys={tuple(sorted(x)) for x in sf}
assert len(iface_keys)==48 and len(outer_keys)==13586
assert not iface_keys.intersection(outer_keys)
for key in iface_keys:
 adj=face_incidence[key]
 assert len(adj)==2 and {p[3] for p in adj}==set(regions)
for key in outer_keys:
 adj=face_incidence[key]
 assert len(adj)==1
assert {k for k,v in face_incidence.items() if len(v)==1}==outer_keys
assert {k for k,v in face_incidence.items() if len(v)==2 and v[0][3]!=v[1][3]}==iface_keys
assert max(len(v) for v in face_incidence.values())==2
# Detect other boundary faces grouped by source face ID, and enforce
# shared original global vertex/edge DOFs for both material regions.
face_ids=np.array([int(r[4]) for r in outer],np.int32)
fixed_faces=outer[face_ids==dirtag]
fixedtri=np.searchsorted(original_nodes,fixed_faces[:,1:4])
assert len(fixedtri)==6048
edge_pairs=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
ep=np.concatenate([np.sort(tet[:,[a,b]],axis=1) for a,b in edge_pairs])
edges,inv=np.unique(ep,axis=0,return_inverse=True)
edge_to_elem=inv.reshape(6,nt).T+n
t10=np.column_stack((tet,edge_to_elem)).astype(np.int32)
edge_key_type=np.dtype([('a','<i4'),('b','<i4')])
def edgekey(e):return np.ascontiguousarray(e,dtype=np.int32).view(edge_key_type).reshape(-1)
keys2=edgekey(edges)
def face6(tri):
 pairs=((0,1),(0,2),(1,2))
 e=np.concatenate([np.sort(tri[:,[a,b]],axis=1) for a,b in pairs])
 idx=np.searchsorted(keys2,edgekey(e))
 assert np.all(idx<len(edges)) and np.array_equal(keys2[idx],edgekey(e))
 return np.column_stack((tri,idx.reshape(3,len(tri)).T+n)).astype(np.int32)
surf6=face6(sf)
fix1=np.unique(fixedtri)
fix2=np.unique(face6(fixedtri))
# A single shared global P2 DOF tag across same triangular interface
assert len(np.unique(face6(iface)))>len(np.unique(iface))
# Manufactured u has SAME value at z0, and k*du/dz=Q either side.
def uval(p,mat):
 d=p[...,2]-z0
 return A*((p[...,0]-x0)**2+(p[...,1]-y0)**2)+B*d*d+(Q/mat)*d
def deriv(p,mat):
 v=np.empty_like(p,dtype=float)
 v[...,0]=2*A*(p[...,0]-x0)
 v[...,1]=2*A*(p[...,1]-y0)
 v[...,2]=2*B*(p[...,2]-z0)+Q/mat
 return v
def forc(mat):
 return -mat*(4*A+2*B)
refgrad=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
def shape(l,gl,order):
 if order==1:return l,gl
 vertex=l*(2*l-1)
 gvertex=(4*l-1)[...,None]*gl
 edge=np.stack([4*l[...,i]*l[...,j] for i,j in edge_pairs],axis=-1)
 gedge=np.stack([4*(l[...,i,None]*gl[...,j,:]+l[...,j,None]*gl[...,i,:]) for i,j in edge_pairs],axis=1)
 return np.concatenate((vertex,edge),axis=-1),np.concatenate((gvertex,gedge),axis=1)
def facebasis(l,order):
 if order==1:return l
 return np.array([*([l[i]*(2*l[i]-1) for i in range(3)]),
                   *([4*l[i]*l[j] for i,j in ((0,1),(0,2),(1,2))])])
# Degree-4 Keast tetra integration exact for stiffness polynomial degree 2 and constant forcing
QL=[(np.array([.25]*4),-.07893333333333333)]
for i in range(4):
 x=np.array([1/14.]*4);x[i]=11/14.;QL.append((x,.04573333333333333))
for a,b in itertools.combinations(range(4),2):
 x=np.array([.1005964238332008]*4);x[a]=x[b]=.3994035761667992;QL.append((x,.14933333333333335))
# 7-point Dunavant face integration
FL=[(np.array([1/3.]*3),.225)]
for val,rest,w in ((.05971587178977,.470142064105115,.132394152788506),
                   (.797426985353087,.101286507323456,.125939180544827)):
 for i in range(3):
  x=np.array([rest]*3);x[i]=val;FL.append((x,w))
# Separate 4-point positive degree2 tetra H1 gradient error integration
four=[]
for i in range(4):
 q=np.array([.1381966011250105]*4)
 q[i]=.5854101966249685
 four.append((q,.25))
# Analytic preflight: any of 48 face points from 410 & 420 have exactly common field and flux.
p_if=node[np.unique(internal[:,1:4])-1,1:4]
assert np.max(np.abs(p_if[:,2]-z0))<1e-12
assert np.max(np.abs(uval(p_if,K[410])-uval(p_if,K[420])))<1e-12
assert np.max(np.abs(K[410]*deriv(p_if,K[410])[:,2]-K[420]*deriv(p_if,K[420])[:,2]))<1e-12
print('R315_TRANSMISSION_PREFLIGHT',json.dumps({
 'materials':{'410':'COMPOSITE_MULTILAYER','420':'Au'},'artificial_K':K,
 'cells':nt,'geometric_nodes':n,'registered_shared_TRI3':len(iface),'native_outer_TRI3':len(sf),
 'P2_edges':len(edges),'P2_total_DOF':n+len(edges),'P1_fixed':len(fix1),'P2_fixed':len(fix2),
 'P2_interface_trace_shared':True}),flush=True)
# Separate mathematical model on the same physical mesh (shared C0 vertices/edges)
def solve(order):
 start=time.monotonic()
 nd=n if order==1 else n+len(edges)
 fix=fix1 if order==1 else fix2
 free=np.setdiff1d(np.arange(nd,dtype=np.int32),fix)
 allpts=xyz if order==1 else np.vstack((xyz,(xyz[edges[:,0]]+xyz[edges[:,1]])*.5))
 # Since all fixed DOFs lie on native face 2399 in region 420, k420 exact trace
 bc=uval(allpts[fix],K[420])
 rhs=np.zeros(nd)
 # Each source exterior face must use its own material owner,
 # outward area is explicitly oriented with real incident opposite tetra vertex.
 for lo in range(0,len(sf),450):
  hi=min(lo+450,len(sf))
  cellids=sf[lo:hi];tags=face_ids[lo:hi]
  selectedmask=tags!=dirtag
  if not np.any(selectedmask):continue
  rows=cellids[selectedmask]
  dofrows=(rows if order==1 else surf6[lo:hi][selectedmask])
  pts=xyz[rows]
  kval=np.empty(len(rows))
  normals=np.empty((len(rows),3))
  for j,tri in enumerate(rows):
   key=tuple(sorted(map(int,tri)))
   idx,oriented,op,mat=face_incidence[key][0]
   p0,p1,p2=xyz[list(oriented)]
   area=.5*np.cross(p1-p0,p2-p0)
   if np.dot(area,xyz[op]-p0)>0:area=-area
   normals[j]=area
   kval[j]=K[mat]
  load=np.zeros((len(rows),3 if order==1 else 6))
  for l,w in FL:
   xx=np.einsum('a,tac->tc',l,pts)
   matarr=kval
   gradient=np.empty_like(xx)
   gradient[:,0]=2*A*(xx[:,0]-x0)
   gradient[:,1]=2*A*(xx[:,1]-y0)
   gradient[:,2]=2*B*(xx[:,2]-z0)+Q/matarr
   qn=matarr*np.einsum('ti,ti->t',gradient,normals)
   load+=w*qn[:,None]*facebasis(l,order)[None,:]
  np.add.at(rhs,dofrows.ravel(),load.ravel())
 # FEM elemental P1/P2 stiffness with artificial per-material coefficient.
 rowblk=[];colblk=[];datablk=[]
 indices=tet if order==1 else t10
 localnd=4 if order==1 else 10
 for lo in range(0,nt,300):
  hi=min(nt,lo+300)
  vert=xyz[tet[lo:hi]]
  j=np.stack((vert[:,1]-vert[:,0],vert[:,2]-vert[:,0],vert[:,3]-vert[:,0]),axis=2)
  det=np.linalg.det(j);assert np.all(det>0)
  vv=det/6
  gl=np.einsum('tji,aj->tai',np.linalg.inv(j),refgrad)
  mat=np.where(material[lo:hi]==410,K[410],K[420])
  loc=np.zeros((hi-lo,localnd,localnd))
  load=np.zeros((hi-lo,localnd))
  for lamb,w in QL:
   l=np.broadcast_to(lamb,(hi-lo,4))
   Ns,G=shape(l,gl,order)
   loc+=w*(vv*mat)[:,None,None]*np.einsum('tai,tbi->tab',G,G)
   load+=w*(vv*np.array([forc(k) for k in mat]))[:,None]*Ns
  ix=indices[lo:hi]
  rowblk.append(np.broadcast_to(ix[:,:,None],loc.shape).ravel().copy())
  colblk.append(np.broadcast_to(ix[:,None,:],loc.shape).ravel().copy())
  datablk.append(loc.ravel())
  np.add.at(rhs,ix.ravel(),load.ravel())
 S=coo_matrix((np.concatenate(datablk),(np.concatenate(rowblk),np.concatenate(colblk))),shape=(nd,nd)).tocsr()
 S.sum_duplicates()
 F=S[free,:][:,free].tocsr()
 b=rhs[free]-S[free,:][:,fix]@bc
 nb=np.linalg.norm(b)
 count=[0]
 def cb(_):count[0]+=1
 factor_start=time.monotonic()
 try:
  ilu=spilu(F.tocsc(),drop_tol=1e-5,fill_factor=16)
  M=LinearOperator(F.shape,matvec=ilu.solve,dtype=float)
  sol,info=gmres(F,b,M=M,restart=60,maxiter=65,rtol=1e-9,atol=0,callback=cb,callback_type='pr_norm')
  res=float(np.linalg.norm(F@sol-b)/nb)
 except Exception as ex:
  return {'status':'FACTOR_STOP','error':str(ex),'order':order}
 report={'order':order,'status':'PASS' if info==0 and res<1e-8 else 'SOLVER_STOP',
  'free_DOFS':len(free),'total_DOFS':nd,'fixed_DOFS':len(fix),
  'P1_TET_geometry_unchanged':True,'symmetric_relative':float(np.linalg.norm((F-F.T).data)/np.linalg.norm(F.data)),
  'matrix_NNZ':int(F.nnz),'ILU_nnz':int(ilu.L.nnz+ilu.U.nnz),
  'ILU_GMRES_iterations':count[0],'ILU_GMRES_info':int(info),
  'original_operator_true_relative_residual':res,'factor_and_solve_seconds':round(time.monotonic()-factor_start,3)}
 print('R315_SOLVE',json.dumps(report),flush=True)
 if report['status']!='PASS':return report
 coeff=np.empty(nd)
 coeff[fix]=bc;coeff[free]=sol
 np.savez_compressed(O/f'P{order}_coefficients.npz',coefficients=coeff)
 # Interface P2 trace continuity is a *single shared* global coefficient.
 # Evaluate pointwise normal flux of each adjacent material at each face centroid
 # (linear P2 gradient over each planar face, so integral is exact).
 jumps=[];flux_abs=[];iface_area=[]
 for tri_g in iface:
  key=tuple(sorted(map(int,tri_g)))
  inds=face_incidence[key]
  tri_pts=xyz[list(key)]
  area=float(np.linalg.norm(np.cross(tri_pts[1]-tri_pts[0],tri_pts[2]-tri_pts[0]))/2)
  total_flux=0.
  for idx,tri,op,mat in inds:
   t=tet[idx]
   p=xyz[t]
   jj=np.stack((p[1]-p[0],p[2]-p[0],p[3]-p[0]),axis=1)
   gl=np.einsum('ji,aj->ai',np.linalg.inv(jj),refgrad)
   mid=tri_pts.mean(axis=0)
   lamb=np.r_[1-np.sum(np.linalg.solve(jj,mid-p[0])),np.linalg.solve(jj,mid-p[0])]
   _,G=shape(lamb[None,:],gl[None,:,:],order)
   gr=np.einsum('i,ij->j',coeff[(tet if order==1 else t10)[idx]],G[0])
   p0,p1,p2=xyz[list(tri)]
   outward=np.cross(p1-p0,p2-p0)*.5
   if np.dot(outward,xyz[op]-p0)>0:outward=-outward
   total_flux+=K[mat]*np.dot(gr,outward)/area
  jumps.append(total_flux);iface_area.append(area)
 # true contact conservation: numerical normal flux jump integrated across shared interface
 jumps=np.array(jumps);areas=np.array(iface_area)
 ref_flux=np.abs(Q)
 report['interface_normal_flux_jump_relative_L2']=float(np.sqrt(np.dot(areas,jumps*jumps)/sum(areas))/ref_flux)
 report['interface_normal_flux_jump_max_rel']=float(np.max(np.abs(jumps))/ref_flux)
 report['signed_net_internal_face_flux_integral']=float(np.dot(areas,jumps))
 report['interface_area_mm2']=float(areas.sum())
 report['P2_trace_C0_by_shared_node_edge_tags']=True
 # Global H1 gradient error using exact positive degree2 tetra quadrature,
 # gradient polynomial degree1 P2 and exact quadratic analytic field.
 err=0.;refnorm=0.
 for lo in range(0,nt,180):
  hi=min(lo+180,nt)
  p=xyz[tet[lo:hi]]
  j=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
  vv=np.linalg.det(j)/6
  gl=np.einsum('tji,aj->tai',np.linalg.inv(j),refgrad)
  mat=np.where(material[lo:hi]==410,K[410],K[420])
  cl=coeff[(tet if order==1 else t10)[lo:hi]]
  for lam,w in four:
   l=np.broadcast_to(lam,(hi-lo,4))
   _,G=shape(l,gl,order)
   appro=np.einsum('ti,tij->tj',cl,G)
   xx=np.einsum('a,tai->ti',lam,p)
   exact=np.empty_like(xx)
   exact[:,0]=2*A*(xx[:,0]-x0)
   exact[:,1]=2*A*(xx[:,1]-y0)
   exact[:,2]=2*B*(xx[:,2]-z0)+Q/mat
   err+=float(np.dot(vv,w*np.einsum('ti,ti->t',appro-exact,appro-exact)))
   refnorm+=float(np.dot(vv,w*np.einsum('ti,ti->t',exact,exact)))
 report['H1_relative_error']=math.sqrt(err/refnorm)
 report['H1_absolute_error']=math.sqrt(err)
 report['full_computation_seconds']=round(time.monotonic()-start,3)
 print('R315_CONSERVATION',order,'H1',report['H1_relative_error'],'flux_jump_L2',report['interface_normal_flux_jump_relative_L2'],flush=True)
 return report
runs=[]
for order in (1,2):
 if time.monotonic()-tic>190:break
 r=solve(order);runs.append(r)
 O.mkdir(exist_ok=True)
 (O/f'P{order}_result.json').write_text(json.dumps(r,indent=2)+'\n')
 if r['status']!='PASS':break
status='PASS TWO-MATERIAL CONTINUOUS-FLUX P1/P2 BENCHMARK' if len(runs)==2 and all(r['status']=='PASS' for r in runs) and runs[1]['H1_relative_error']<runs[0]['H1_relative_error']/1000 and runs[1]['interface_normal_flux_jump_relative_L2']<1e-7 else 'STOP OR PARTIAL TWO-MATERIAL BENCHMARK'
report={'status':status,
 'synthetic_coefficients':{'410':1,'420':10},
 'constitutive_interpretation':'PURELY MATHEMATICAL; not physical gold or composite multilayer conductivity',
 'two_native_CAD_material_regions':[410,420],
 'source_interface_face_tag':2349,'interface_face_z_mm':z0,
 'registered_shared_TRI3':48,'registered_outer_TRI3':len(sf),
 'native_CAD_interface_area_mm2':metadata['faces']['2349']['face_area_mm2'],
 'saved_mesh_interface_area_mm2':runs[0].get('interface_area_mm2') if runs else None,
 'manufactured_piecewise_quadratic':'u=A*((x-x0)^2+(y-y0)^2)+B*(z-z0)^2+Q/k_r*(z-z0), k_410=1,k_420=10; normal flux k du/dz=Q at z=z0; f_r=-k_r*(4A+2B)',
 'A':A,'B':B,'Q':Q,'no_geometric_or_material_identity_changes':True,
 'Dirichlet_native_CAD_face':dirtag,
 'P2_global_edge_mids_shared':True,
 'source_files_SHA256':{p.name:hashfile(p) for p in (P/'R38_430_domains.1.node',P/'R39_430_domains.1.ele',P/'R38_430_domains.1.face')},
 'no_real_physical_electrothermal_PDE':True,'no_mesh_convergence':'single fixed mesh',
 'P1_P2_runs':runs,'elapsed_seconds':round(time.monotonic()-tic,3),
 'max_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
(O/'two_material_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print('R315_FINAL',json.dumps({'status':status,'runs':runs,'sec':report['elapsed_seconds']},indent=2),flush=True)
