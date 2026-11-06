#!/usr/bin/env python3
"""R3.17 three-region finite-contact P1/P2 scalar network, native R3.9 CAD.
HgCdTe 408 -> composite 410 -> Au 420 through source faces2336,2349.
Separate field traces on each material. Synthetic coefficient ratios and
Robin interfaces, analytically varying q_z(x,y), sin-tangential field.
No physical material parameters, no geometry mutation, no full-device PDE.
"""
from pathlib import Path
from collections import defaultdict
import json,hashlib,itertools,math,time,resource
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import gmres,spilu,LinearOperator
P=Path('/input');O=Path('/out'); START=time.monotonic()
meta=json.loads((P/'source_metadata.json').read_text())
global_nodes=np.loadtxt(P/'R38_430_domains.1.node',skiprows=1)
global_elements=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
global_faces=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
REG=(408,410,420);CONTACT=((408,410,2336),(410,420,2349))
K={408:2.,410:1.,420:10.};G={2336:4.,2349:5.}
Z1=float(meta['faces']['2336']['center_mm'][2])
Z2=float(meta['faces']['2349']['center_mm'][2])
assert Z1<Z2
Q0=1.;qx=1.8;qy=2.5;A=.025;beta=.15;XC=-.35
selection=global_elements[np.isin(global_elements[:,5],REG)]
orig_tet=selection[:,1:5]
mat=selection[:,5]
T=len(orig_tet)
MULT=1000000
encoded=mat[:,None]*MULT+orig_tet
encoded_unique=np.unique(encoded)
tet=np.searchsorted(encoded_unique,encoded)
nv=len(encoded_unique)
xyz=global_nodes[encoded_unique%MULT-1,1:4]
vertex_lookup={(int(v//MULT),int(v%MULT)):i for i,v in enumerate(encoded_unique)}
EDGE_PAIRS=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
all_edges=np.concatenate([np.sort(tet[:,[a,b]],axis=1) for a,b in EDGE_PAIRS])
edges,edge_index=np.unique(all_edges,axis=0,return_inverse=True)
ten=np.column_stack((tet,edge_index.reshape(6,T).T+nv))
n2=nv+len(edges)
etype=np.dtype([('a','<i4'),('b','<i4')])
def ekey(x):return np.ascontiguousarray(x,dtype=np.int32).view(etype).reshape(-1)
indexed_edges=ekey(edges)
def add_face_edges(face3):
    ff=np.concatenate([np.sort(face3[:,[a,b]],axis=1) for a,b in ((0,1),(0,2),(1,2))])
    at=np.searchsorted(indexed_edges,ekey(ff))
    assert np.all(at<len(edges)) and np.array_equal(indexed_edges[at],ekey(ff))
    return np.column_stack((face3,at.reshape(3,len(face3)).T+nv))
# Native CAD registry: every actual 2-sided face of three-region selection,
# and every external face touching exactly one selected region.
iface={};inside={};site_faces={}
for ra,rb,tag in CONTACT:
    assert set(meta['faces'][str(tag)]['owner_volume_ids'])=={ra,rb}
    faces=global_faces[global_faces[:,4]==tag]
    assert len(faces)>0
    site_faces[tag]=faces
    sides={}
    for r in (ra,rb):
        sides[r]=np.asarray([[vertex_lookup[(r,int(n))] for n in f[1:4]] for f in faces],dtype=np.int32)
    inside[tag]=sides
    iface[tag]=faces
# Restrict exterior to faces with exactly one CAD owner among REG, but exclude
# registered pair internal interfaces; includes omitted material as outside.
surface=[]
for f in global_faces:
    owners=set(meta['faces'][str(int(f[4]))]['owner_volume_ids'])
    common=owners.intersection(REG)
    if len(common)==1:
        r=next(iter(common))
        surface.append((np.array([vertex_lookup[(r,int(v))] for v in f[1:4]],dtype=np.int32),r,int(f[4])))
# Reconstruct exact genuine CAD material interfaces independently of source-face registry.
INCIDENCE=defaultdict(list)
for ti,orig in enumerate(orig_tet):
    for a,b,c,o in ((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3)):
        key=tuple(sorted((int(orig[a]),int(orig[b]),int(orig[c]))))
        INCIDENCE[key].append((ti,int(mat[ti]),tet[ti,[a,b,c]],int(tet[ti,o])))
actual={key:{entry[1] for entry in incid} for key,incid in INCIDENCE.items() if len({a[1] for a in incid})==2}
for ra,rb,tag in CONTACT:
    expected={tuple(sorted(map(int,f[1:4]))) for f in iface[tag]}
    found={key for key,r in actual.items() if r=={ra,rb}}
    assert expected==found and len(found)==len(iface[tag])
assert all(set(v) in ({408,410},{410,420}) for v in actual.values()) and len(actual)==sum(len(v) for v in iface.values())
# Reconstruct complete external CAD faces as exact native source TRI3.
outer_native=set()
for f,r,tag in surface:
    key=tuple(sorted(int(encoded_unique[v]%MULT) for v in f))
    outer_native.add(key)
actual_exterior={key for key,items in INCIDENCE.items() if len(items)==1}
assert actual_exterior==outer_native
assert max(len(v) for v in INCIDENCE.values())==2
fixed_tag=2399
fixed_tri=np.asarray([f for f,r,t in surface if t==fixed_tag],dtype=np.int32)
assert len(fixed_tri)==6048
fixed={1:np.unique(fixed_tri),2:np.unique(add_face_edges(fixed_tri))}
yrange=float(np.ptp(xyz[:,1]));YMIN=float(np.min(xyz[:,1]));WAVE=math.pi/max(yrange,.05)
def qvar(x):return Q0+qx*(x[...,0]-XC)+qy*x[...,1]
def sfun(x,r):
 z=x[...,2]
 if r==408:return (z-Z1)/K[408]-1/G[2336]
 if r==410:return (z-Z1)/K[410]
 if r==420:return (z-Z2)/K[420]+(Z2-Z1)/K[410]+1/G[2349]
 raise ValueError(r)
def exact(x,r,nonlinear):
 v=A*((x[...,0]-XC)**2+x[...,1]**2)+qvar(x)*sfun(x,r)
 if nonlinear:v+=beta*np.sin(WAVE*(x[...,1]-YMIN))
 return v
def grad(x,r,nonlinear):
 s=sfun(x,r)
 g=np.empty_like(x)
 g[...,0]=2*A*(x[...,0]-XC)+qx*s
 g[...,1]=2*A*x[...,1]+qy*s
 if nonlinear:g[...,1]+=beta*WAVE*np.cos(WAVE*(x[...,1]-YMIN))
 g[...,2]=qvar(x)/K[r]
 return g
def forcing(x,r,nonlinear):
 # Delta(q_xy*s(z))=0 because q_xy affine, s(z) affine: mixed
 # derivatives do not enter scalar Laplacian. Delta F =4A - beta W^2 sin.
 v=-K[r]*4*A
 if nonlinear:v+=K[r]*beta*WAVE**2*np.sin(WAVE*(x[...,1]-YMIN))
 return v+np.zeros(x.shape[:-1])
# Exact two contact conditions must vary tangentially, not constant Q.
for ra,rb,tag in CONTACT:
    geometric=np.unique(iface[tag][:,1:4])
    x=global_nodes[geometric-1,1:4]
    assert float(np.std(qvar(x)))>1e-4
    assert np.max(abs(x[:,2]-meta['faces'][str(tag)]['center_mm'][2]))<1e-12
    assert np.max(abs(exact(x,ra,False)-exact(x,rb,False)+qvar(x)/G[tag]))<1e-11
    assert np.max(abs(K[ra]*grad(x,ra,False)[:,2]-qvar(x)))<1e-11
    assert np.max(abs(K[rb]*grad(x,rb,False)[:,2]-qvar(x)))<1e-11
Q4=[(np.array([.25]*4),-.07893333333333333)]
for i in range(4):
    l=np.array([1/14.]*4);l[i]=11/14.;Q4.append((l,.04573333333333333))
for a,b in itertools.combinations(range(4),2):
    l=np.array([.1005964238332008]*4);l[[a,b]]=.3994035761667992;Q4.append((l,.14933333333333335))
QF=[(np.array([1/3.]*3),.225)]
for a,b,w in ((.05971587178977,.470142064105115,.132394152788506),(.797426985353087,.101286507323456,.125939180544827)):
    for i in range(3):
        l=np.array([b]*3);l[i]=a;QF.append((l,w))
QERR=[]
for i in range(4):
    l=np.array([.1381966011250105]*4);l[i]=.5854101966249685;QERR.append((l,.25))
REF=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
def shape(l,gl,order):
    if order==1:return l,gl
    vertex=l*(2*l-1);gvert=(4*l-1)[...,None]*gl
    edge=np.stack([4*l[...,a]*l[...,b] for a,b in EDGE_PAIRS],axis=-1)
    ge=np.stack([4*(l[...,a,None]*gl[...,b,:]+l[...,b,None]*gl[...,a,:]) for a,b in EDGE_PAIRS],axis=1)
    return np.concatenate((vertex,edge),axis=-1),np.concatenate((gvert,ge),axis=1)
def face_shape(l,order):
    if order==1:return l
    return np.r_[[l[a]*(2*l[a]-1) for a in range(3)],[4*l[a]*l[b] for a,b in ((0,1),(0,2),(1,2))]]
def contact_matrix(order):
    N=nv if order==1 else n2
    rows=[];cols=[];vals=[]
    for ra,rb,tag in CONTACT:
        af=inside[tag][ra] if order==1 else add_face_edges(inside[tag][ra])
        bf=inside[tag][rb] if order==1 else add_face_edges(inside[tag][rb])
        native=iface[tag]
        for idx,f in enumerate(native):
            p=global_nodes[f[1:4]-1,1:4]
            area=.5*np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))
            ids=np.r_[af[idx],bf[idx]]
            loc=np.zeros((len(ids),len(ids)))
            for l,w in QF:
                b=face_shape(l,order)
                v=np.r_[b,-b]
                loc+=w*G[tag]*area*np.outer(v,v)
            rows.append(np.broadcast_to(ids[:,None],loc.shape).ravel().copy())
            cols.append(np.broadcast_to(ids[None,:],loc.shape).ravel().copy())
            vals.append(loc.ravel())
    return coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(N,N)).tocsr()
def solve(order,nonlinear):
    start=time.monotonic()
    N=nv if order==1 else n2
    ixs=tet if order==1 else ten
    full_coords=xyz if order==1 else np.vstack((xyz,(xyz[edges[:,0]]+xyz[edges[:,1]])*.5))
    fix=fixed[order]
    free=np.setdiff1d(np.arange(N,dtype=np.int32),fix)
    # Native face 2399 is contained only in region420.
    bc=exact(full_coords[fix],420,nonlinear)
    rhs=np.zeros(N)
    # Neumann on ALL native *exterior* faces except face2399; only proper
    # material-owner region outward normal, never contact as exterior.
    for lo in range(0,len(surface),360):
        bunch=surface[lo:lo+360]
        ff=np.asarray([x[0] for x in bunch],np.int32)
        rr=np.asarray([x[1] for x in bunch],np.int32)
        tt=np.asarray([x[2] for x in bunch],np.int32)
        ok=tt!=fixed_tag
        if not np.any(ok):continue
        ff=ff[ok];rr=rr[ok]
        ids=ff if order==1 else add_face_edges(ff)
        pt=xyz[ff]
        normal=np.empty((len(ff),3))
        for i,tri in enumerate(ff):
            key=tuple(sorted(int(encoded_unique[j]%MULT) for j in tri))
            entries=INCIDENCE[key]
            assert len(entries)==1
            ti,r,source_tri,op=entries[0]
            assert r==rr[i]
            p0,p1,p2=xyz[source_tri]
            n=.5*np.cross(p1-p0,p2-p0)
            if np.dot(n,xyz[op]-p0)>0:n=-n
            normal[i]=n
        loads=np.zeros((len(ff),3 if order==1 else 6))
        for l,w in QF:
            x=np.einsum('a,tai->ti',l,pt)
            grads=np.empty_like(x)
            sx=np.select([rr==408,rr==410,rr==420],
                [(x[:,2]-Z1)/K[408]-1/G[2336],
                 (x[:,2]-Z1)/K[410],
                 (x[:,2]-Z2)/K[420]+(Z2-Z1)/K[410]+1/G[2349]])
            grads[:,0]=2*A*(x[:,0]-XC)+qx*sx
            grads[:,1]=2*A*x[:,1]+qy*sx
            if nonlinear:grads[:,1]+=beta*WAVE*np.cos(WAVE*(x[:,1]-YMIN))
            kk=np.select([rr==408,rr==410,rr==420],[K[r] for r in REG])
            grads[:,2]=qvar(x)/kk
            flux=kk*np.einsum('ti,ti->t',grads,normal)
            loads+=w*flux[:,None]*face_shape(l,order)[None,:]
        np.add.at(rhs,ids.ravel(),loads.ravel())
    # Assemble actual TET4 stiffness and exact polynomial/sine body sources
    rows=[];cols=[];vals=[]
    for lo in range(0,T,300):
        hi=min(lo+300,T)
        p=xyz[tet[lo:hi]]
        J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
        det=np.linalg.det(J)
        assert np.all(det>0)
        v=det/6
        gl=np.einsum('tji,aj->tai',np.linalg.inv(J),REF)
        kk=np.select([mat[lo:hi]==r for r in REG],[K[r] for r in REG])
        nloc=4 if order==1 else 10
        local=np.zeros((hi-lo,nloc,nloc));load=np.zeros((hi-lo,nloc))
        for l,w in Q4:
            lamb=np.broadcast_to(l,(hi-lo,4))
            Nloc,Grad=shape(lamb,gl,order)
            local+=w*(v*kk)[:,None,None]*np.einsum('tai,tbi->tab',Grad,Grad)
            x=np.einsum('a,tai->ti',l,p)
            f=-4*A*kk
            if nonlinear:f+=kk*beta*WAVE**2*np.sin(WAVE*(x[:,1]-YMIN))
            load+=w*(v*f)[:,None]*Nloc
        conn=ixs[lo:hi]
        rows.append(np.broadcast_to(conn[:,:,None],local.shape).ravel().copy())
        cols.append(np.broadcast_to(conn[:,None,:],local.shape).ravel().copy())
        vals.append(local.ravel())
        np.add.at(rhs,conn.ravel(),load.ravel())
    Kbulk=coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(N,N)).tocsr()
    Kwhole=(Kbulk+contact_matrix(order)).tocsr()
    Ared=Kwhole[free,:][:,free].tocsr()
    b=rhs[free]-Kwhole[free,:][:,fix]@bc
    nb=np.linalg.norm(b)
    count=[0]
    def callback(_):count[0]+=1
    try:
        ilu=spilu(Ared.tocsc(),drop_tol=1e-5,fill_factor=16)
        M=LinearOperator(Ared.shape,matvec=ilu.solve,dtype=float)
        u,info=gmres(Ared,b,M=M,restart=60,maxiter=65,rtol=1e-9,atol=0,callback=callback,callback_type='pr_norm')
        residue=float(np.linalg.norm(Ared@u-b)/nb)
    except Exception as exc:
        return {'status':'SOLVER_EXCEPTION','exception':str(exc)[:350],'order':order,'nonlinear':nonlinear}
    summary={'order':order,'nonlinear':nonlinear,'status':'PASS' if info==0 and residue<1e-8 else 'SOLVER_STOP',
      'source_tetrahedra':T,'total_DOF':N,'free_DOF':len(free),
      'fixed_DOF':len(fix),'ILU_GMRES_iterations':count[0],
      'ILU_GMRES_info':int(info),'true_residual':residue,
      'matrix_NNZ':int(Ared.nnz),
      'symmetric_relative':float(np.linalg.norm((Ared-Ared.T).data)/np.linalg.norm(Ared.data))}
    print('R317_SOLVE',json.dumps(summary),flush=True)
    if summary['status']!='PASS':return summary
    field=np.empty(N);field[free]=u;field[fix]=bc
    np.savez_compressed(O/f'P{order}_nonlin{int(nonlinear)}_field.npz',field=field)
    # Regional field H1 on the original signed tetrahedra.
    square=0.;reference=0.
    for lo in range(0,T,200):
        hi=min(lo+200,T)
        p=xyz[tet[lo:hi]]
        J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
        v=np.linalg.det(J)/6
        gl=np.einsum('tji,aj->tai',np.linalg.inv(J),REF)
        coeff=field[ixs[lo:hi]]
        for lam,w in QERR:
            L=np.broadcast_to(lam,(hi-lo,4))
            _,Gshape=shape(L,gl,order)
            computed=np.einsum('ti,tij->tj',coeff,Gshape)
            point=np.einsum('a,tai->ti',lam,p)
            expected=np.empty_like(point)
            rr=mat[lo:hi]
            s=np.select([rr==408,rr==410,rr==420],[(point[:,2]-Z1)/K[408]-1/G[2336],
                     (point[:,2]-Z1)/K[410],
                     (point[:,2]-Z2)/K[420]+(Z2-Z1)/K[410]+1/G[2349]])
            expected[:,0]=2*A*(point[:,0]-XC)+qx*s
            expected[:,1]=2*A*point[:,1]+qy*s
            if nonlinear:expected[:,1]+=beta*WAVE*np.cos(WAVE*(point[:,1]-YMIN))
            kk=np.select([rr==408,rr==410,rr==420],[K[r] for r in REG])
            expected[:,2]=qvar(point)/kk
            square+=float(np.dot(w*v,np.sum((computed-expected)**2,axis=1)))
            reference+=float(np.dot(w*v,np.sum(expected**2,axis=1)))
    summary['H1_relative_4pt']=math.sqrt(square/reference)
    network={}
    for ra,rb,tag in CONTACT:
        jumps=[];conservation=[];robin=[];aweights=[];q_targets=[]
        for f in iface[tag]:
            p=global_nodes[f[1:4]-1,1:4]
            pt=p.mean(axis=0)
            Aface=.5*np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))
            key=tuple(sorted(map(int,f[1:4])))
            side={}
            for ti,r,tri,opp in INCIDENCE[key]:
                P4=xyz[tet[ti]]
                J=np.column_stack((P4[1]-P4[0],P4[2]-P4[0],P4[3]-P4[0]))
                baryp=np.linalg.solve(J,pt-P4[0])
                L=np.r_[1-baryp.sum(),baryp]
                gl=REF@np.linalg.inv(J)
                Nval,Gval=shape(L[None,:],gl[None,:,:],order)
                uu=float(field[ixs[ti]]@Nval[0])
                gg=field[ixs[ti]]@Gval[0]
                p0,p1,p2=xyz[tri]
                area_normal=.5*np.cross(p1-p0,p2-p0)
                if np.dot(area_normal,xyz[opp]-p0)>0:area_normal=-area_normal
                q=float(K[r]*np.dot(gg,area_normal)/Aface)
                side[r]=(uu,q)
            jump=side[ra][0]-side[rb][0]
            # outward gradient flux = +q on lower material side
            q_a=side[ra][1];q_b=side[rb][1]
            jumps.append(jump)
            conservation.append(q_a+q_b)
            robin.append(q_a+G[tag]*jump)
            q_targets.append(qvar(pt))
            aweights.append(Aface)
        aweights=np.asarray(aweights)
        q_targets=np.asarray(q_targets)
        jumps=np.asarray(jumps);conservation=np.asarray(conservation);robin=np.asarray(robin)
        wtot=aweights.sum()
        rms=lambda f:float(np.sqrt(np.dot(aweights,f*f)/wtot))
        network[str(tag)]={
          'volume_pair':[ra,rb],
          'source_shared_triangles':len(iface[tag]),
          'source_face_area_mm2':float(wtot),
          'analytic_variable_q_RMS':rms(q_targets),
          'analytic_q_range':[float(q_targets.min()),float(q_targets.max())],
          'contact_jump_RMS_err_relative_to_q':rms(jumps+q_targets/G[tag])/rms(q_targets),
          'flux_balance_RMS_rel':rms(conservation)/rms(q_targets),
          'Robin_RMS_rel':rms(robin)/rms(q_targets),
          'signed_net_flux_mismatch_integral':float(np.dot(aweights,conservation)),
          'mean_manufactured_contact_jump':float(np.dot(aweights,-q_targets/G[tag])/wtot),
          'mean_computed_contact_jump':float(np.dot(aweights,jumps)/wtot)}
    summary['contacts']=network
    summary['wall_seconds']=round(time.monotonic()-start,3)
    print('R317_DIAGNOSTICS',json.dumps({'order':order,'nonlinear':nonlinear,'H1':summary['H1_relative_4pt'],'network':network,'elapsed':summary['wall_seconds']}),flush=True)
    return summary
print('R317_NETWORK',json.dumps({'registered_interfaces':{str(t):len(iface[t]) for *_,t in CONTACT},
      'source_material_regions':REG,'native_TET4':T,'native_union_vertices':len(np.unique(orig_tet)),
      'split_P1_field_vertices':nv,'split_P2_total_DOF':n2,
      'artificial_k':K,'artificial_G':G,'face_z':[Z1,Z2],
      'two_interface_varying_flux':True,'exterior_TRI3':len(surface)}),flush=True)
O.mkdir(exist_ok=True)
runs=[]
for nonlinear in (False,True):
 for order in (1,2):
    if time.monotonic()-START>220:break
    r=solve(order,nonlinear);runs.append(r)
    (O/f'P{order}_nonlin{int(nonlinear)}_result.json').write_text(json.dumps(r,indent=2)+'\n')
    if r['status']!='PASS':break
 if runs[-1]['status']!='PASS':break
passed=len(runs)==4 and all(r['status']=='PASS' for r in runs)
if passed:
 for r in runs:
    if r['order']==2:
      passed&=all(x['Robin_RMS_rel']<1e-5 and x['flux_balance_RMS_rel']<1e-5
             for x in r['contacts'].values())
 passed &=runs[1]['H1_relative_4pt']<runs[0]['H1_relative_4pt']/1000
 passed &=runs[3]['H1_relative_4pt']<runs[2]['H1_relative_4pt']/50
status='PASS R3.17 SYNTHETIC THREE-REGION TWO-CONTACT NETWORK' if passed else 'STOP/PARTIAL R3.17 NETWORK'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for part in iter(lambda:f.read(4<<20),b''):h.update(part)
 return h.hexdigest()
result={'status':status,'source_CAD_regions':REG,'source_CAD_contact_faces':[2336,2349],
 'contact_pairs':[[ra,rb] for ra,rb,tag in CONTACT],
 'artificial_k':K,'artificial_G':G,'manufactured_variable_normal_flux_q':'1 + 1.8 (x+0.35) + 2.5 y',
 'manufactured_field':'A*((x+0.35)^2+y^2)+q(x,y)*s_r(z)+ beta sin(W(y-y_min)), piecewise affine s with nonzero contact jump',
 'source_mesh_geometry_modified':False,'two_contact_source_facets_exact':True,
 'true_physical_electrothermal_model':'NOT RUN','mesh_convergence':'NOT RUN',
 'input_source_SHA256':{p.name:sha(p) for p in (P/'R38_430_domains.1.node',P/'R38_430_domains.1.face',P/'R39_430_domains.1.ele')},
 'results':runs,'elapsed_seconds':round(time.monotonic()-START,3),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
(O/'network_summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('R317_FINAL',status,'RUNTIME',result['elapsed_seconds'],'RSS',result['peak_RSS_MiB'],flush=True)
