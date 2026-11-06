#!/usr/bin/env python3
"""One preregistered original Gate-B coupon P2 raw-gradient comparator.

Source is the immutable 2026-11-02 original fine 28691-TET4 coupon.
Same 12 material domains, SI geometry, NOM anisotropic conductivity,
1e-11 ohm.m^2 contact law, true CAD internal electrodes and 16 cuts.
P2 global field edge DOFs are separate per-material; only raw P2 gradients
are used for prospective gate. No additional numerical method or meshing.
"""
from pathlib import Path
from collections import defaultdict
import argparse,hashlib,json,math,resource,time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import gmres,spilu,LinearOperator
from tecooledmct.v3_et_fem import tensors,connectivity,SCENARIOS
from tecooledmct.flux_presolder_common import affine_geometry
from tecooledmct.candidate_cu_fem import plane_current

P=Path('/work/data/v3_interconnect_et_20261102/B')
R=Path('/out')
M=np.load(P/'fine_mesh/mesh.npz')
rj=json.loads((P/'fine_mesh/registry.json').read_text())
orig=json.loads((P/'fine_field/result.json').read_text())
oldgate=json.loads((P/'gate_B.json').read_text())
points=M['points'];cells=M['cells'];regions=M['regions']
tris=M['triangles'];faceids=M['faceids']
assert cells.shape==(28691,4)
assert len(rj['groups'])==12 and len(rj['faces'])==105
assert oldgate['status']=='FAIL/STOP'
sigma=tensors(rj['groups'],mode='electric',scenario='NOM')
RCONTACT=SCENARIOS['NOM']['re']
assert RCONTACT==1e-11
assert np.all(np.linalg.eigvalsh(sigma)>0)
N=len(cells)
vol,grad=affine_geometry(points,cells)
assert np.all(vol>0)
# exact original P1 region DOF arrangement
pair=np.stack((np.repeat(regions,4),cells.ravel()),axis=1)
uni,iv=np.unique(pair,axis=0,return_inverse=True)
t4=iv.reshape(-1,4)
assert len(t4)==N
n=len(uni)
node_to_dof={(int(r),int(node)):i for i,(r,node) in enumerate(uni)}
edgepairs=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
edge_rows=np.concatenate([np.sort(t4[:,[a,b]],axis=1) for a,b in edgepairs])
edges,iv2=np.unique(edge_rows,axis=0,return_inverse=True)
t10=np.column_stack((t4,iv2.reshape(6,N).T+n))
ne=n+len(edges)
edtype=np.dtype([('a','<i4'),('b','<i4')])
def edgekeys(x):return np.ascontiguousarray(x,dtype=np.int32).view(edtype).reshape(-1)
edge_tokens=edgekeys(edges)
def with_edges(f3):
    stack=np.concatenate([np.sort(f3[:,[a,b]],axis=1) for a,b in ((0,1),(0,2),(1,2))])
    ix=np.searchsorted(edge_tokens,edgekeys(stack))
    assert np.all(ix<len(edges)) and np.array_equal(edge_tokens[ix],edgekeys(stack))
    return np.column_stack((f3,ix.reshape(3,len(f3)).T+n))
owners,normals,tagmap=connectivity(points,cells,regions,tris,faceids,rj)
assert len(owners)==len(tris)
faceA=np.linalg.norm(normals,axis=1)
f3=np.asarray([[node_to_dof[(int(tagmap[int(tag)]['owners'][0]),int(node))] for node in tri]
 for tri,tag in zip(tris,faceids)],dtype=np.int32)
contacts=np.array([len(tagmap[int(t)]['owners'])==2 for t in faceids],bool)
bfaces=~contacts
# region B P2 trace at the actual same physical face, not welded to A
second_f3=np.asarray([[node_to_dof[(int(tagmap[int(tag)]['owners'][1]),int(node))] for node in tri]
 for tri,tag in zip(tris[contacts],faceids[contacts])],dtype=np.int32)
f6=with_edges(f3)
ctA=f6[contacts];ctB=with_edges(second_f3)
assert not np.intersect1d(ctA.ravel(),ctB.ravel()).size
boundary=np.zeros(ne,bool)
value=np.zeros(ne)
src=set();dst=set()
for ix in np.flatnonzero(bfaces):
    ep=int(tagmap[int(faceids[ix])]['electrical_port'])
    if ep<0:continue
    fs=f6[ix];old=boundary[fs]
    if ep==0:src.update(int(x) for x in fs)
    elif ep==1:dst.update(int(x) for x in fs)
    else:raise ValueError("Unknown electrical port")
    assert np.all(~old | (value[fs]==(1.0 if ep==0 else 0.0)))
    boundary[fs]=True;value[fs]=1. if ep==0 else 0.
src=np.asarray(sorted(src),np.int32);dst=np.asarray(sorted(dst),np.int32)
assert len(src)>0 and len(dst)>0 and not np.intersect1d(src,dst).size
assert np.all(boundary[src]) and np.all(boundary[dst])
fixed=np.flatnonzero(boundary);free=np.flatnonzero(~boundary)
# exact degree-4 Keast volume, degree-5 Dunavant face.
vquad=[(np.full(4,.25),-.07893333333333333)]
for i in range(4):
    q=np.full(4,1/14.);q[i]=11/14.;vquad.append((q,.04573333333333333))
import itertools
for a,b in itertools.combinations(range(4),2):
    q=np.full(4,.1005964238332008);q[[a,b]]=.3994035761667992;vquad.append((q,.14933333333333335))
fquad=[(np.full(3,1/3),.225)]
for a,b,w in ((.05971587178977,.470142064105115,.132394152788506),
              (.797426985353087,.101286507323456,.125939180544827)):
    for i in range(3):
        q=np.full(3,b);q[i]=a;fquad.append((q,w))
def basis(l,g):
    vals=np.concatenate((l*(2*l-1),np.stack([4*l[...,a]*l[...,b] for a,b in edgepairs],axis=-1)),axis=-1)
    ders=np.concatenate(((4*l-1)[...,None]*g,np.stack(
        [4*(l[...,a,None]*g[...,b,:]+l[...,b,None]*g[...,a,:]) for a,b in edgepairs],axis=1)),axis=1)
    return vals,ders
def facephi(l):
    return np.r_[[l[i]*(2*l[i]-1) for i in range(3)],
                 [4*l[i]*l[j] for i,j in ((0,1),(0,2),(1,2))]]
faceint=np.zeros(6)
facemass=np.zeros((6,6))
for l,w in fquad:
    q=facephi(l);faceint+=w*q;facemass+=w*np.outer(q,q)
assert abs(sum(faceint)-1)<1e-13
assert max(abs(faceint[:3]))<1e-13
assert np.max(abs(faceint[3:]-1/3))<1e-13
assert np.min(np.linalg.eigvalsh(facemass))>0
# Face ownership preflight and exact source port count.
assert len(tris[contacts])>1000
assert len(fixed)>1000
def hashes():
    source=(P/'fine_mesh/mesh.npz',P/'fine_mesh/registry.json',
            P/'fine_field/fields.npz',P/'fine_field/result.json',P/'gate_B.json')
    return {str(p.relative_to(Path('/work'))):hashlib.sha256(p.read_bytes()).hexdigest() for p in source}
pre={'status':'PASS static original source P2 DOF topology (no PDE)',
 'original_tetrahedra':N,'source_original_p1_scalar_DOFS':n,
 'prospective_p2_scalar_DOFS':ne,
 'P2_shared_undirected_edges':len(edges),
 'fixed_DOF':len(fixed),'free_DOF':len(free),
 'source_DOF':len(src),'drain_DOF':len(dst),
 'native_contact_TRI3':int(contacts.sum()),'native_external_TRI3':int(bfaces.sum()),
 'original_conductivity_S_m':{g['name']:sigma[i].diagonal().tolist() for i,g in enumerate(rj['groups'])},
 'contact_r_ohm_m2':RCONTACT,
 'source_file_sha256':hashes()}
def write_json(filename,obj):
    with (R/filename).open('x') as h:
        json.dump(obj,h,indent=2)
        h.write('\n')
parser=argparse.ArgumentParser()
parser.add_argument('--preflight-only',action='store_true')
args=parser.parse_args()
if args.preflight_only:
    print('P2_PREFLIGHT',json.dumps(pre),flush=True)
    raise SystemExit(0)
R.mkdir(parents=True,exist_ok=True)
registration=json.loads((R/'preregistration.json').read_text())
self_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
assert self_sha==registration['source_script_sha256']
assert pre['source_file_sha256']==registration['source_file_sha256']
assert registration['original_gate_current_limit_rel']==.001
assert registration['original_gate_boundedness_tolerance_V']==1e-8
assert registration['original_gate_power_limit_rel']==.005
assert registration['P2_method']=='original coupon fixed-mesh P2 raw-gradient'
write_json('source_preflight.json',pre)
print('P2_COUPON_REGISTERED_START',json.dumps({k:pre[k] for k in ('original_tetrahedra','source_original_p1_scalar_DOFS','prospective_p2_scalar_DOFS','native_contact_TRI3','free_DOF')}),flush=True)
tic=time.monotonic()
# One assembly of the original 12-physical-region coupon.
rows=[];cols=[];data=[]
for lo in range(0,N,240):
    hi=min(lo+240,N)
    gc=grad[lo:hi]
    loc=np.zeros((hi-lo,10,10))
    for l,w in vquad:
        L=np.broadcast_to(l,(hi-lo,4))
        _,dphi=basis(L,gc)
        loc+=w*vol[lo:hi,None,None]*np.einsum(
             'eia,eab,ejb->eij',dphi,sigma[regions[lo:hi]],dphi,optimize=True)
    idx=t10[lo:hi]
    rows.append(np.broadcast_to(idx[:,:,None],loc.shape).ravel().copy())
    cols.append(np.broadcast_to(idx[:,None,:],loc.shape).ravel().copy())
    data.append(loc.ravel())
# Original intermaterial contact R'' and source original triangle area.
# Vectorized source contact matrix assembly (the 1574 face elements).
ids=np.column_stack((ctA,ctB))
m0=np.block([[facemass,-facemass],[-facemass,facemass]])
for lo in range(0,len(ids),300):
    hi=min(lo+300,len(ids))
    local=m0[None,:,:]*(faceA[contacts][lo:hi,None,None]/RCONTACT)
    q=ids[lo:hi]
    rows.append(np.broadcast_to(q[:,:,None],local.shape).ravel().copy())
    cols.append(np.broadcast_to(q[:,None,:],local.shape).ravel().copy())
    data.append(local.ravel())
K=coo_matrix((np.concatenate(data),(np.concatenate(rows),np.concatenate(cols))),
             shape=(ne,ne)).tocsr()
K.sum_duplicates()
assert np.all(np.isfinite(K.data))
del rows,cols,data
asym=float(np.linalg.norm((K-K.T).data)/np.linalg.norm(K.data))
assert asym<1e-12
F=K[free,:][:,free].tocsr()
rhs=-K[free,:][:,fixed]@value[fixed]
diag=F.diagonal()
assert np.all(diag>0)
scale=1/np.sqrt(diag)
A=F.multiply(scale[:,None]).multiply(scale[None,:]).tocsr()
b=scale*rhs
print('P2_ASSEMBLED',json.dumps({'DOF':ne,'NNZ':int(F.nnz),'symmetry_error':asym,'seconds':time.monotonic()-tic}),flush=True)
# One factorization and one P2 solve; no automated retries/tuning.
factor_start=time.monotonic()
ilu=spilu(A.tocsc(),drop_tol=1e-5,fill_factor=14)
precon=LinearOperator(A.shape,matvec=ilu.solve,dtype=float)
count=[0]
def callback(_):count[0]+=1
z,info=gmres(A,b,M=precon,restart=60,maxiter=50,rtol=1e-10,
             atol=0.,callback=callback,callback_type='pr_norm')
u=value.copy();u[free]=scale*z
reduced_relative=float(np.linalg.norm(F@u[free]-rhs)/max(np.linalg.norm(rhs),1e-30))
totalres=K@u
sourceI=float(totalres[src].sum())
drainI=-float(totalres[dst].sum())
solver={'GMRES_info':int(info),'GMRES_iterations':count[0],
        'ILU_factor_nnz':int(ilu.L.nnz+ilu.U.nnz),
        'true_reduced_relative_residual':reduced_relative,
        'factor_and_solve_seconds':time.monotonic()-factor_start,
        'source_current_unitV_A':sourceI,
        'drain_current_unitV_A':drainI}
print('P2_SOLVER',json.dumps(solver),flush=True)
if info!=0 or reduced_relative>1e-8 or not np.isfinite(sourceI) or sourceI<=0:
    write_json('stopped_solver.json',{'status':'STOP P2 original coupon solver failed',
      'solver':solver,'original_Gate_B':'FAIL/STOP unchanged'})
    raise SystemExit(12)
np.savez_compressed(R/'P2_original_coupon_field.npz',field=u)
# Compute P2 raw one-sided surface currents as exact integral of linear gradient
# on each unchanged triangle, centroid point exact for linear current.
cent=points[cells].mean(axis=1)
def grad_at(tid,x):
    ll=np.full((len(tid),4),.25)
    delta=x-cent[tid]
    ll+=np.einsum('eia,ea->ei',grad[tid],delta)
    _,GG=basis(ll,grad[tid])
    return np.einsum('ei,eia->ea',u[t10[tid]],GG)
def Jat(tid,x):
    return -np.einsum('eij,ej->ei',sigma[regions[tid]],grad_at(tid,x))
positions=points[tris].mean(axis=1)
rawA=np.einsum('ei,ei->e',Jat(owners[:,0],positions),normals)
rawB=-np.einsum('ei,ei->e',Jat(owners[contacts,1],positions[contacts]),normals[contacts])
# Exact contact flux integral of quadratic P2 trace, signed from owner lower material to higher.
jump=u[ctA]-u[ctB]
natural=(faceA[contacts]/RCONTACT)*np.einsum('fi,i->f',jump,faceint)
flux_by_pair=defaultdict(lambda:dict(natural=0.,raw_a=0.,raw_b=0.,area=0.,triangles=0))
for idx,j in enumerate(np.flatnonzero(contacts)):
    a,b=tagmap[int(faceids[j])]['owners']
    g=flux_by_pair[(int(a),int(b))]
    g['natural']+=float(natural[idx])
    g['raw_a']+=float(rawA[j])
    g['raw_b']+=float(rawB[idx])
    g['area']+=float(faceA[j])
    g['triangles']+=1
# exact original net topology sign/expected drive fraction.
graph=defaultdict(set)
for a,b in flux_by_pair:
    graph[a].add(b);graph[b].add(a)
inlet=next(i for i,g in enumerate(rj['groups']) if g['name']=='pn87_solder')
outlet=int(uni[dst[0],0])
cuts=[]
for (a,b),g in flux_by_pair.items():
    seen={a};stack=[a]
    while stack:
        x=stack.pop()
        for y in graph[x]:
            if {x,y}=={a,b}:continue
            if y not in seen:seen.add(y);stack.append(y)
    sign=int(inlet in seen)-int(outlet in seen)
    expected=sign*sourceI
    errors=[abs(g['natural']-expected)/sourceI,abs(g['raw_a']-expected)/sourceI,
            abs(g['raw_b']+expected)/sourceI]
    cuts.append({'pair':[rj['groups'][a]['name'],rj['groups'][b]['name']],
        'expected_fraction':sign,'natural_A':g['natural'],
        'raw_a_A':g['raw_a'],'raw_b_A':g['raw_b'],
        'area_m2':g['area'],'triangles':g['triangles'],
        'natural_relative_error':errors[0],
        'raw_relative_error':max(errors[1:]),
        'gate_error':max(errors)})
for ep,terminal,expected in ((0,src,-sourceI),(1,dst,sourceI)):
    ix=np.array([j for j,t in enumerate(faceids) if not contacts[j] and
                int(tagmap[int(t)]['electrical_port'])==ep],np.int32)
    assert len(ix)>0
    rraw=float(rawA[ix].sum())
    cuts.append({'terminal':ep,'raw_out_A':rraw,'expected_out_A':expected,
                 'gate_error':abs(rraw-expected)/sourceI})
# Integral of P2 linear current on an exact planar cut of each tet:
# original polygon construction, area-weighted polygon centroid of flux.
def p2_plane_current(regionid,axis,zcut):
    filt=np.flatnonzero(regions==regionid)
    x=points[cells[filt]]
    dist=x[:,:,axis]-zcut;eps=1e-13
    inds=np.flatnonzero((dist.min(axis=1)<-eps)&(dist.max(axis=1)>=-eps))
    other=[j for j in range(3) if j!=axis]
    flow=0.;totalarea=0.
    for e in inds:
        loc=x[e];dd=dist[e]
        poly=[loc[i] for i in range(4) if abs(dd[i])<=eps]
        for i in range(4):
            for j in range(i+1,4):
                if dd[i]*dd[j]<0 and abs(dd[i])>eps and abs(dd[j])>eps:
                    poly.append(loc[i]+(loc[j]-loc[i])*dd[i]/(dd[i]-dd[j]))
        if len(poly)<3:continue
        pp=np.unique(np.round(np.array(poly),14),axis=0)
        if len(pp)<3:continue
        projection=pp[:,other]
        mid=projection.mean(axis=0)
        order=np.argsort(np.arctan2(projection[:,1]-mid[1],projection[:,0]-mid[0]))
        pp=pp[order]
        area=0.;weighted=0.
        # Triangulate 2D convex intersection polygon, each current exact
        # as J(x triangle centroid) dot unit plane normal * area.
        for j in range(1,len(pp)-1):
            pa,pb,pc=pp[0],pp[j],pp[j+1]
            v1=pb[other]-pa[other];v2=pc[other]-pa[other]
            aa=abs(np.linalg.det(np.stack((v1,v2),axis=1)))/2
            xyz=(pa+pb+pc)/3
            density=Jat(np.array([filt[e]],np.int32),xyz[None,:])[0,axis]
            weighted+=aa*float(density)
            area+=aa
        flow+=weighted;totalarea+=area
    return float(flow),float(totalarea)
if any(x['name']=='tab88' for x in rj['groups']):
    ti=next(i for i,x in enumerate(rj['groups']) if x['name']=='tab88')
    li=next(i for i,x in enumerate(rj['groups']) if x['name']=='lead9')
    for name,r,axis,z in (('tab88_lower',ti,2,.00268425),
        ('tab88_upper',ti,2,.00378425),
        ('lead9_mid',li,0,(-.5-4.368691769624716)*.0005)):
        raw,area=p2_plane_current(r,axis,z)
        if area<=0:raise ValueError('Registered interior cut has zero area')
        cuts.append({'interior':name,'axis':axis,'position_m':z,
          'raw_A':raw,'expected_A':-sourceI,'area_m2':area,
          'gate_error':abs(raw+sourceI)/sourceI})
assert len(cuts)==16
# Original unchanged P1 nominal law and exact original triangles.
reference={tuple(x['pair']):x for x in orig['cuts'] if 'pair' in x}
assert set(reference)=={tuple(x['pair']) for x in cuts if 'pair' in x}
# Independent P2 bulk/contact energy identity, same operator as algebraic solve
bulk=0.
for lo in range(0,N,240):
    hi=min(lo+240,N);g=grad[lo:hi];coeff=u[t10[lo:hi]]
    for l,w in vquad:
        _,D=basis(np.broadcast_to(l,(hi-lo,4)),g)
        GG=np.einsum('ei,eia->ea',coeff,D)
        bulk+=float(np.sum(w*vol[lo:hi]*np.einsum(
           'ei,eij,ej->e',GG,sigma[regions[lo:hi]],GG)))
contact_loss=float(np.dot(faceA[contacts]/RCONTACT,
       np.einsum('fi,ij,fj->f',jump,facemass,jump,optimize=True)))
powrel=abs(bulk+contact_loss-sourceI)/sourceI
worst=max(c['gate_error'] for c in cuts)
res={'status':'PASS prospective P2 coupon raw current gate' if
     worst<=.001 and u.min()>=-1e-8 and u.max()<=1+1e-8 and powrel<=.005
     else 'STOP prospective P2 original coupon raw current gate',
     'original_P1_Gate_B':'FAIL/STOP remains unchanged',
     'physical_material_properties':'unchanged original NOM assumptions, not measured',
     'current_gate_limit':.001,'voltage_bound_tolerance_V':1e-8,
     'power_gate_limit':.005,'solver':solver,
     'P2_unit_potential_current_A':sourceI,
     'P2_R_coupon_ohm':1/sourceI,'relative_change_to_original_P1_R':abs((1/sourceI)/orig['R_coupon_ohm']-1),
     'P2_minimum_voltage_V':float(u.min()),
     'P2_maximum_voltage_V':float(u.max()),
     'P2_current_opposite_terminal_relative_error':abs(sourceI-drainI)/sourceI,
     'P2_raw_cut_max_relative_error':worst,
     'P2_raw_cuts_passing_count':sum(c['gate_error']<=.001 for c in cuts),
     'P2_raw_cuts_failing_count':sum(c['gate_error']>.001 for c in cuts),
     'P2_bulk_loss_unitV_W':bulk,'P2_contact_loss_unitV_W':contact_loss,
     'P2_IV_minus_losses_relative':powrel,
     'original_P1_worst_cut_relative_error':orig['worst_cut_relative_error'],
     'original_P1_minimum_voltage_V':orig['minimum_voltage'],
     'source_geometry_nodes_unchanged':True,'source_materials_and_contact_law_unchanged':True,
     'P2_geometry_linear_TET4_unchanged':True,
     'P2_potential_solution_coefficient_file':'P2_original_coupon_field.npz',
     'source_original_mesh_SHA256':pre['source_file_sha256'],
     'P2_cuts':cuts,'wall_seconds':time.monotonic()-tic,
     'max_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
write_json('P2_coupon_result.json',res)
print('P2_COUPON_FINAL',json.dumps({k:res[k] for k in
 ('status','P2_unit_potential_current_A','P2_minimum_voltage_V',
 'P2_raw_cut_max_relative_error','P2_raw_cuts_passing_count',
 'P2_raw_cuts_failing_count','P2_IV_minus_losses_relative','wall_seconds','max_RSS_MiB')}),flush=True)
for row in sorted(cuts,key=lambda x:x['gate_error'],reverse=True)[:10]:
    name='->'.join(row['pair']) if 'pair' in row else ('terminal_'+str(row['terminal']) if 'terminal' in row else row['interior'])
    print('P2_CUT',name,round(100*row['gate_error'],6),'pct',flush=True)
