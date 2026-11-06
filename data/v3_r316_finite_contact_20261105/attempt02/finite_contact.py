#!/usr/bin/env python3
"""R3.16 finite-contact two-material P1/P2 manufactured scalar diffusion.
Actual R3.9 interface CAD2349 connects volume410/420.
Split interface traces by duplicating all region node/edge solution DOFs;
couple using positive Robin interface conductance G*int(u410-u420)(v410-v420).
Analytic jump Q/G and continuous oriented flux Q.
Quadratic and sinusoidal+quadratic cases; original geometric mesh immutable.
"""
import json,hashlib,itertools,math,resource,time
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import gmres,spilu,LinearOperator
P=Path('/input'); O=Path('/out'); BEGIN=time.monotonic()
m=json.loads((P/'source_metadata.json').read_text())
node=np.loadtxt(P/'R38_430_domains.1.node',skiprows=1)
ele=np.loadtxt(P/'R39_430_domains.1.ele',dtype=np.int32,skiprows=1)
face=np.loadtxt(P/'R38_430_domains.1.face',dtype=np.int32,skiprows=1)
regions=(410,420); interface_tag=2349; fixed_tag=2399
kmap={410:1.,420:10.};conductance=5.
Q=1.;B=.05;A=.025;beta=.25
x0=-.35;y0=0.;z0=5.7849
selected=ele[np.isin(ele[:,5],regions)]
g_tets=selected[:,1:5]
region=selected[:,5]
assert len(g_tets)==26053
# Encode each material's field-node identity separately, even for a
# physical coordinate/mesh vertex shared across native interface2349.
MULT=1000000
encoded=region[:,None]*MULT+g_tets
unique_ids=np.unique(encoded)
tet=np.searchsorted(unique_ids,encoded)
n=len(unique_ids);T=len(tet)
xyz=node[unique_ids%MULT-1,1:4]
assert n==6957
vertex_idmap={r:{} for r in regions}
for t,key in enumerate(unique_ids):
 vertex_idmap[int(key//MULT)][int(key%MULT)]=t
# P2 solution edges are globally shared WITHIN a material, and
# intentionally disconnected between materials at contact face.
pairs=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
edgearray=np.concatenate([np.sort(tet[:,[a,b]],axis=1) for a,b in pairs])
edges,inv=np.unique(edgearray,axis=0,return_inverse=True)
t10=np.column_stack((tet,inv.reshape(6,T).T+n)).astype(np.int32)
n2=n+len(edges)
edge_struct=np.dtype([('x','<i4'),('y','<i4')])
def edge_key(rows):return np.ascontiguousarray(rows,dtype=np.int32).view(edge_struct).reshape(-1)
keyed_edges=edge_key(edges)
def f6(tri):
    p=((0,1),(0,2),(1,2))
    ed=np.concatenate([np.sort(tri[:,[a,b]],axis=1) for a,b in p])
    at=np.searchsorted(keyed_edges,edge_key(ed))
    assert np.all(at<len(edges)) and np.array_equal(keyed_edges[at],edge_key(ed))
    return np.column_stack((tri,at.reshape(3,len(tri)).T+n))
# Native TRI3 face registry for actual regions and exact interface.
iface=face[face[:,4]==interface_tag]
assert len(iface)==48 and m['faces'][str(interface_tag)]['owner_volume_ids']==[410,420]
source_other=[]
for f in face:
    owners=m['faces'][str(int(f[4]))]['owner_volume_ids']
    if int(f[4])!=interface_tag and len(set(owners).intersection(regions))==1:
        source_other.append((f,next(r for r in owners if r in regions)))
assert len(source_other)==13586
# Region-side local physical vertex IDs; no welded interface trace.
iside={}
for r in regions:
    entries=np.array([[vertex_idmap[r][int(i)] for i in f[1:4]] for f in iface],dtype=np.int32)
    assert entries.shape==(48,3)
    iside[r]=entries
assert not np.intersect1d(iside[410].ravel(),iside[420].ravel()).size
assert len(np.unique(iface[:,1:4]))==49
surface=[]
for f,r in source_other:
    t=np.array([vertex_idmap[r][int(i)] for i in f[1:4]],dtype=np.int32)
    surface.append((t,r,int(f[4])))
fixedtri=np.array([t for t,r,tag in surface if tag==fixed_tag],dtype=np.int32)
assert len(fixedtri)==6048
fixed={1:np.unique(fixedtri),2:np.unique(f6(fixedtri))}
# Independently reconstruct tetrahedron boundary ownership by ORIGINAL nodes.
fdefs=((1,2,3,0),(0,2,3,1),(0,1,3,2),(0,1,2,3))
incidence=defaultdict(list)
for idx,t in enumerate(tet):
    orig=g_tets[idx]
    for a,b,c,o in fdefs:
        tri=(int(orig[a]),int(orig[b]),int(orig[c]))
        incidence[tuple(sorted(tri))].append((idx,int(region[idx]),t[[a,b,c]],int(t[o])))
native_ifacekeys={tuple(sorted(f[1:4])) for f in iface}
assert len(native_ifacekeys)==48
assert all(len(incidence[key])==2 and {p[1] for p in incidence[key]}==set(regions) for key in native_ifacekeys)
assert all(len(incidence[tuple(sorted(f[1:4]))])==1 for f,r in source_other)
assert {key for key,items in incidence.items() if len(items)==2 and items[0][1]!=items[1][1]}==native_ifacekeys
# Separate physical geometric mesh and interface area.
area=np.array([np.linalg.norm(np.cross(node[f[2]-1,1:4]-node[f[1]-1,1:4],
                  node[f[3]-1,1:4]-node[f[1]-1,1:4]))/2 for f in iface])
assert abs(area.sum()/m['faces'][str(interface_tag)]['face_area_mm2']-1)<.01
p_if=node[np.unique(iface[:,1:4])-1,1:4]
assert np.max(np.abs(p_if[:,2]-z0))<1e-12
# P2 edge traces require separate material side edge tags on same physical face.
assert np.intersect1d(f6(iside[410]).ravel(),f6(iside[420]).ravel()).size==0
# synthetic smooth piecewise field with contact jump -Q/G on 410 side,
# and continuous k du/dz=Q in the 410->420 +z direction; physical diffusive flux -k du/dn.
yrange=np.ptp(xyz[:,1])
freq=math.pi/max(yrange,.05)
ymin=float(xyz[:,1].min())
def value(p,r,nonlinear):
    dz=p[...,2]-z0
    ret=A*((p[...,0]-x0)**2+(p[...,1]-y0)**2)+B*dz**2+Q/kmap[r]*dz
    if r==410:ret-=Q/conductance
    if nonlinear:ret+=beta*np.sin(freq*(p[...,1]-ymin))
    return ret
def grad(p,r,nonlinear):
    ret=np.empty_like(p)
    ret[...,0]=2*A*(p[...,0]-x0)
    ret[...,1]=2*A*(p[...,1]-y0)
    if nonlinear:ret[...,1]+=beta*freq*np.cos(freq*(p[...,1]-ymin))
    ret[...,2]=2*B*(p[...,2]-z0)+Q/kmap[r]
    return ret
def forcing(p,r,nonlinear):
    ret=-kmap[r]*(4*A+2*B)
    if nonlinear:ret+=kmap[r]*beta*freq**2*np.sin(freq*(p[...,1]-ymin))
    return ret+np.zeros(p.shape[:-1])
# native face exact transition Q/G and +z flux Q
assert np.max(np.abs(value(p_if,410,False)-value(p_if,420,False)+Q/conductance))<1e-12
for r in regions:
    assert np.max(abs(kmap[r]*grad(p_if,r,False)[:,2]-Q))<1e-12
# Quadrature R3.14 proven simplex moments.
tetQ=[(np.array([.25]*4),-.07893333333333333)]
for i in range(4):
    l=np.array([1/14.]*4);l[i]=11/14.;tetQ.append((l,.04573333333333333))
for i,j in itertools.combinations(range(4),2):
    l=np.array([.1005964238332008]*4);l[[i,j]]=.3994035761667992
    tetQ.append((l,.14933333333333335))
faceQ=[(np.array([1/3.]*3),.225)]
for a,b,w in ((.059715871789770,.470142064105115,.132394152788506),
              (.797426985353087,.101286507323456,.125939180544827)):
    for i in range(3):
        l=np.array([b]*3);l[i]=a;faceQ.append((l,w))
ERRQ=[]
for i in range(4):
    l=np.full(4,.1381966011250105);l[i]=.5854101966249685
    ERRQ.append((l,.25))
REF=np.array([[-1.,-1.,-1.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
def shape(l,gr,order):
    if order==1:return l,gr
    N=np.concatenate((l*(2*l-1),np.stack([4*l[...,a]*l[...,b] for a,b in pairs],axis=-1)),axis=-1)
    G=np.concatenate(((4*l-1)[...,None]*gr,np.stack([4*(l[...,a,None]*gr[...,b,:]+l[...,b,None]*gr[...,a,:]) for a,b in pairs],axis=1)),axis=1)
    return N,G
def trace(l,order):
    if order==1:return l
    return np.r_[[l[i]*(2*l[i]-1) for i in range(3)],
                 [4*l[i]*l[j] for i,j in ((0,1),(0,2),(1,2))]]
def build_contact(order):
    nd=n if order==1 else n2
    idx0=iside[410] if order==1 else f6(iside[410])
    idx1=iside[420] if order==1 else f6(iside[420])
    num=3 if order==1 else 6
    row=[];col=[];dat=[]
    # ∫_Γ G (u410-u420)(v410-v420): positive form
    for i in range(48):
        ids=np.r_[idx0[i],idx1[i]]
        Kloc=np.zeros((2*num,2*num))
        for l,w in faceQ:
            phi=trace(l,order)
            v=np.r_[phi,-phi]
            Kloc+=conductance*area[i]*w*np.outer(v,v)
        row.append(np.broadcast_to(ids[:,None],Kloc.shape).ravel().copy())
        col.append(np.broadcast_to(ids[None,:],Kloc.shape).ravel().copy())
        dat.append(Kloc.ravel())
    return coo_matrix((np.concatenate(dat),(np.concatenate(row),np.concatenate(col))),shape=(nd,nd)).tocsr()
def solve(order,nonlinear):
    st=time.monotonic();nd=n if order==1 else n2
    index=tet if order==1 else t10
    pts=xyz if order==1 else np.vstack((xyz,(xyz[edges[:,0]]+xyz[edges[:,1]])*.5))
    fixedids=fixed[order]
    free=np.setdiff1d(np.arange(nd,dtype=np.int32),fixedids)
    bc=value(pts[fixedids],420,nonlinear)
    source=np.zeros(nd)
    # Exterior flux, per region, excludes internal registered CAD2349.
    for lo in range(0,len(surface),400):
        entries=surface[lo:lo+400]
        tface=np.array([x[0] for x in entries],np.int32)
        mat=np.array([x[1] for x in entries],np.int32)
        tags=np.array([x[2] for x in entries],np.int32)
        valid=(tags!=fixed_tag)
        if not np.any(valid):continue
        faces=tface[valid];mats=mat[valid]
        fidx=faces if order==1 else f6(faces)
        normals=np.empty((len(faces),3))
        for i,faceids in enumerate(faces):
            orig_key=tuple(sorted(int(unique_ids[j]%MULT) for j in faceids))
            owner=incidence[orig_key][0]
            _,r,oriented,op=owner
            assert r==mats[i]
            p0,p1,p2=xyz[oriented]
            narea=.5*np.cross(p1-p0,p2-p0)
            if np.dot(narea,xyz[op]-p0)>0:narea=-narea
            normals[i]=narea
        vals=np.zeros((len(faces),3 if order==1 else 6))
        coord=xyz[faces]
        for l,w in faceQ:
            loc=np.einsum('a,tai->ti',l,coord)
            gg=np.empty_like(loc)
            gg[:,0]=2*A*(loc[:,0]-x0)
            gg[:,1]=2*A*(loc[:,1]-y0)
            if nonlinear:gg[:,1]+=beta*freq*np.cos(freq*(loc[:,1]-ymin))
            gg[:,2]=2*B*(loc[:,2]-z0)+Q/np.where(mats==410,kmap[410],kmap[420])
            kk=np.where(mats==410,kmap[410],kmap[420])
            flux=kk*np.einsum('ti,ti->t',gg,normals)
            vals+=w*flux[:,None]*trace(l,order)[None,:]
        np.add.at(source,fidx.ravel(),vals.ravel())
    # Actual native tetra stiffness and source, with continuous material DOFs
    # except interface 2349 (doubled nodal/edge traces).
    arow=[];acol=[];adata=[]
    for lo in range(0,T,300):
        hi=min(T,lo+300);p=xyz[tet[lo:hi]]
        J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
        det=np.linalg.det(J);assert np.all(det>0)
        vol=det/6
        gradlam=np.einsum('tji,aj->tai',np.linalg.inv(J),REF)
        kk=np.where(region[lo:hi]==410,kmap[410],kmap[420])
        nb=4 if order==1 else 10
        matloc=np.zeros((hi-lo,nb,nb));rhs=np.zeros((hi-lo,nb))
        for l,w in tetQ:
            L=np.broadcast_to(l,(hi-lo,4))
            N,G=shape(L,gradlam,order)
            matloc+=w*(vol*kk)[:,None,None]*np.einsum('tai,tbi->tab',G,G)
            point=np.einsum('a,tai->ti',l,p)
            exactf=-kk*(4*A+2*B)
            if nonlinear:exactf+=kk*beta*freq**2*np.sin(freq*(point[:,1]-ymin))
            rhs+=w*(vol*exactf)[:,None]*N
        ids=index[lo:hi]
        arow.append(np.broadcast_to(ids[:,:,None],matloc.shape).ravel().copy())
        acol.append(np.broadcast_to(ids[:,None,:],matloc.shape).ravel().copy())
        adata.append(matloc.ravel())
        np.add.at(source,ids.ravel(),rhs.ravel())
    bulk=coo_matrix((np.concatenate(adata),(np.concatenate(arow),np.concatenate(acol))),shape=(nd,nd)).tocsr()
    A_full=bulk+build_contact(order)
    reduced=A_full[free,:][:,free].tocsr()
    b=source[free]-A_full[free,:][:,fixedids]@bc
    count=[0]
    def cb(_):count[0]+=1
    try:
        ilu=spilu(reduced.tocsc(),drop_tol=1e-5,fill_factor=16)
        M=LinearOperator(reduced.shape,matvec=ilu.solve,dtype=float)
        x,info=gmres(reduced,b,M=M,restart=60,maxiter=70,rtol=1e-9,atol=0,callback=cb,callback_type='pr_norm')
        res=float(np.linalg.norm(reduced@x-b)/np.linalg.norm(b))
    except Exception as exc:
        return {'status':'PRECONDITIONER_EXCEPTION','reason':str(exc),'order':order,'nonlinear':nonlinear}
    result={'order':order,'nonlinear':nonlinear,'status':'PASS' if info==0 and res<1e-8 else 'STOP_SOLVER',
      'source_tetrahedra':T,'total_DOFS':nd,'free_DOFS':len(free),'Dirichlet_DOFS':len(fixedids),
      'contact_conductance_synthetic':conductance,'contact_faces':48,
      'contact_C0_nodes_shared':False,'matrix_NNZ':int(reduced.nnz),
      'matrix_symmetry_relative':float(np.linalg.norm((reduced-reduced.T).data)/np.linalg.norm(reduced.data)),
      'ILU_GMRES_iterations':count[0],'ILU_GMRES_info':int(info),'true_algebraic_relative_residual':res}
    print('R316_SOLVE',json.dumps(result),flush=True)
    if result['status']!='PASS':return result
    coef=np.empty(nd);coef[free]=x;coef[fixedids]=bc
    np.savez_compressed(O/f'P{order}_nonlinear{int(nonlinear)}_coefficients.npz',coefficient=coef)
    # independent diagnostics: non-welded two side potential trace + signed flux
    # at interface triangle centroids, per-side recovered element gradient.
    contact_jumps=[];flux_out=[];condition=[];faceweight=[]
    for f in iface:
        key=tuple(sorted(map(int,f[1:4])))
        adjacent=incidence[key]
        pp=node[f[1:4]-1,1:4]
        ct=pp.mean(axis=0)
        area_f=.5*np.linalg.norm(np.cross(pp[1]-pp[0],pp[2]-pp[0]))
        sides={}
        for ti,r,inds,op in adjacent:
            p=xyz[tet[ti]]
            J=np.column_stack((p[1]-p[0],p[2]-p[0],p[3]-p[0]))
            abc=np.linalg.solve(J,ct-p[0])
            lam=np.r_[1-abc.sum(),abc]
            gradl=REF@np.linalg.inv(J)
            N,G=shape(lam[None,:],gradl[None,:,:],order)
            ids=index[ti]
            val=float(coef[ids]@N[0]);gr=coef[ids]@G[0]
            p0,p1,p2=xyz[inds]
            outward=.5*np.cross(p1-p0,p2-p0)
            if np.dot(outward,xyz[op]-p0)>0:outward=-outward
            flux=float(kmap[r]*np.dot(gr,outward)/area_f)
            sides[r]=(val,flux)
        jump=sides[410][0]-sides[420][0]
        # for outward 410 +z, gradient normal flux is +Q=-G jump; outward420=-z is -Q
        contact_jumps.append(jump);flux_out.append(sides[410][1]+sides[420][1])
        condition.append(sides[410][1]+conductance*jump)
        faceweight.append(area_f)
    ww=np.asarray(faceweight);flux_out=np.asarray(flux_out);condition=np.asarray(condition)
    contact_jumps=np.asarray(contact_jumps)
    result['saved_interface_area_mm2']=float(ww.sum())
    result['manufactured_target_potential_jump']=-Q/conductance
    result['interface_mean_potential_jump']=float(np.dot(ww,contact_jumps)/ww.sum())
    result['interface_potential_jump_RMS_abs_error']=float(np.sqrt(np.dot(ww,(contact_jumps+Q/conductance)**2)/ww.sum()))
    result['flux_balance_RMS_rel']=float(np.sqrt(np.dot(ww,flux_out**2)/ww.sum())/Q)
    result['contact_Robin_condition_RMS_rel']=float(np.sqrt(np.dot(ww,condition**2)/ww.sum())/Q)
    result['interface_net_flux_imbalance_integral']=float(np.dot(ww,flux_out))
    # Independent element quadrature H1 energy error for piecewise field.
    numerator=0.;denominator=0.
    for lo in range(0,T,170):
        hi=min(lo+170,T)
        p=xyz[tet[lo:hi]]
        J=np.stack((p[:,1]-p[:,0],p[:,2]-p[:,0],p[:,3]-p[:,0]),axis=2)
        vol=np.linalg.det(J)/6
        gl=np.einsum('tji,aj->tai',np.linalg.inv(J),REF)
        rr=region[lo:hi]
        coeff=coef[index[lo:hi]]
        for lam,w in ERRQ:
            N,G=shape(np.broadcast_to(lam,(hi-lo,4)),gl,order)
            actual=np.einsum('ti,tij->tj',coeff,G)
            pt=np.einsum('a,tai->ti',lam,p)
            exact=np.empty_like(pt)
            exact[:,0]=2*A*(pt[:,0]-x0)
            exact[:,1]=2*A*(pt[:,1]-y0)
            if nonlinear:exact[:,1]+=beta*freq*np.cos(freq*(pt[:,1]-ymin))
            exact[:,2]=2*B*(pt[:,2]-z0)+Q/np.where(rr==410,kmap[410],kmap[420])
            numerator+=float(np.dot(w*vol,np.sum((actual-exact)**2,axis=1)))
            denominator+=float(np.dot(w*vol,np.sum(exact*exact,axis=1)))
    result['H1_relative_error']=math.sqrt(numerator/denominator)
    result['wall_seconds']=round(time.monotonic()-st,3)
    print('R316_QUALITY',json.dumps({k:result[k] for k in ('order','nonlinear','interface_mean_potential_jump','interface_potential_jump_RMS_abs_error','flux_balance_RMS_rel','contact_Robin_condition_RMS_rel','H1_relative_error','wall_seconds')}),flush=True)
    return result
# Basic face Q checks by source geometry and material trace:
print('R316_NATIVE_REGISTERED',json.dumps({'region_pair':regions,'source_interface_face':interface_tag,
   'native_interface_TRI3':48,'native_tets':T,'native_unique_geometric_nodes':len(np.unique(g_tets)),
   'doubled_P1_field_nodes':n,'P2_field_nodes':n2,'P1_fixed':len(fixed[1]),'P2_fixed':len(fixed[2]),
   'synthetic_contact_G':conductance,'synthetic_k':kmap,'expected_contact_jump':-Q/conductance}),flush=True)
O.mkdir(exist_ok=True)
runs=[]
for nonlinear in (False,True):
    for order in (1,2):
        if time.monotonic()-BEGIN>220:break
        item=solve(order,nonlinear)
        runs.append(item)
        (O/f'P{order}_nonlinear{int(nonlinear)}_result.json').write_text(json.dumps(item,indent=2)+'\n')
        if item['status']!='PASS':break
    if runs[-1]['status']!='PASS':break
passall=(len(runs)==4 and all(x['status']=='PASS' for x in runs))
if passall:
    for item in runs:
        if item['order']==2:
            passall &= item['flux_balance_RMS_rel']<1e-6 and item['contact_Robin_condition_RMS_rel']<1e-6
    passall &= runs[1]['H1_relative_error']<runs[0]['H1_relative_error']/1000
    passall &= runs[3]['H1_relative_error']<runs[2]['H1_relative_error']/100
status='PASS SYNTHETIC FINITE-CONTACT TRANSMISSION AND NONPOLYNOMIAL P2 BENCHMARK' if passall else 'STOP/PARTIAL FINITE-CONTACT BENCHMARK'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
    for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
report={'status':status,'source_CAD_interface':interface_tag,'source_material_volume_ids':[410,420],
 'source_material_names':['COMPOSITE_MULTILAYER','Au'],
 'synthetic_mathematical_conductivities':kmap,'synthetic_contact_G':conductance,
 'exact_Robin_transmission':'-k410 ∂n410 u410 = G(u410-u420) = k420 ∂n420 u420; k410 ∂n410 u410=Q=1',
 'interface_jump_exact':-Q/conductance,'native_interface_triangles_exact':48,
 'native_original_geometry_changed':False,'contact_model_uses_doubled_field_traces':True,
 'mesh_h_convergence':'NOT RUN','whole_device_electrothermal_PDE':'NOT RUN',
 'source_input_SHA256':{f.name:sha(f) for f in (P/'R38_430_domains.1.node',P/'R38_430_domains.1.face',P/'R39_430_domains.1.ele')},
 'results':runs,'elapsed_seconds':round(time.monotonic()-BEGIN,3),
 'peak_RSS_MiB':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}
(O/'finite_contact_summary.json').write_text(json.dumps(report,indent=2)+'\n')
print('R316_COMPLETE',status,'TIME',report['elapsed_seconds'],'RSS',report['peak_RSS_MiB'],flush=True)
