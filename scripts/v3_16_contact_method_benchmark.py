#!/usr/bin/env python3
"""V3.16 reproducible independent 2D P2 imperfect-electrical-contact benchmark.

Mathematical verification coupon only: two conductivity domains, separated
potential traces, positive finite interface resistivity. In the smooth case
an exact harmonic polynomial gives BOTH one-sided raw normal fluxes and the
contact-law flux. In the finite patch case the same formulation has physical
contact tips, no analytic global solution: compare convergence and local
residual concentration only. Nothing herein qualifies original 3D net88.
"""
from pathlib import Path
import hashlib,json,time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/v3_16_contact_method_benchmark_20261110'
OUT.mkdir(parents=True,exist_ok=True)
S=(1.,3.)  # nondimensional, explicitly NOT real Cu or solder conductivities
RC=.2       # nondimensional interface areal resistance
Q0=1.;Q1=.35; TAU=.2
QS=lambda y:Q0+Q1*(y-.5)
QPOINTS=(.1127016653792583,.5,.8872983346207417)
QWEIGHTS=(5/18,8/18,5/18)
ELOCAL=((0,1),(1,2),(2,0))
REFL=np.array([[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]])
REFLINE_M=np.array([[4,-1,2],[-1,4,2],[2,2,16]],dtype=float)/30


def analytic(region,x,y):
    sigma=S[region]
    return (-QS(y)*x/sigma + TAU*y + (1 if region==0 else -1)*RC*QS(y)/2)


def basis(lam,gradlam):
    values=np.array([a*(2*a-1) for a in lam]+[4*lam[i]*lam[j] for i,j in ELOCAL])
    grad=np.array([(4*lam[i]-1)*gradlam[i] for i in range(3)]+[4*(lam[i]*gradlam[j]+lam[j]*gradlam[i]) for i,j in ELOCAL])
    return values,grad


def gradlam_triangle(pts):
    a,b,c=pts
    jac=np.linalg.det(np.stack((b-a,c-a),axis=1))
    assert jac>0
    grad=np.array([[b[1]-c[1],c[0]-b[0]],
                   [c[1]-a[1],a[0]-c[0]],
                   [a[1]-b[1],b[0]-a[0]]])/jac
    return grad,jac/2


def make_region(n,r,off):
    x0,x1=(-1.,0.) if r==0 else (0.,1.)
    vert=np.array([(x0+(x1-x0)*i/n,j/n) for j in range(n+1) for i in range(n+1)])
    def ix(i,j):return j*(n+1)+i
    tris=[]
    for j in range(n):
        for i in range(n):
            p00=ix(i,j);p10=ix(i+1,j);p01=ix(i,j+1);p11=ix(i+1,j+1)
            tris.extend([(p00,p10,p11),(p00,p11,p01)])
    tris=np.array(tris,dtype=np.int32)
    edge_pairs=np.vstack([np.sort(tris[:,[a,b]],axis=1) for a,b in ELOCAL])
    unique,reverse=np.unique(edge_pairs,axis=0,return_inverse=True)
    edgeid={tuple(v):int(k) for k,v in enumerate(unique)}
    allcoord=np.vstack((vert,(vert[unique[:,0]]+vert[unique[:,1]])/2))
    conn=np.column_stack((tris,reverse.reshape(3,len(tris)).T+len(vert)))+off
    iface={}
    for j in range(n):
        a=ix(n if r==0 else 0,j);b=ix(n if r==0 else 0,j+1)
        edge=tuple(sorted((a,b)))
        iface[j]=np.array((a,b,len(vert)+edgeid[edge]),int)+off
    neumann=[]
    for iy,sign in ((0,-1),(n,1)):
        for i in range(n):
            a=ix(i,iy);b=ix(i+1,iy);edge=tuple(sorted((a,b)))
            neumann.append((np.array((a,b,len(vert)+edgeid[edge]),int)+off,sign))
    on_outer=np.isclose(allcoord[:,0],x0 if r==0 else x1,rtol=0,atol=1e-12)
    dirichlet=np.flatnonzero(on_outer)+off
    return dict(sigma=S[r],region=r,nodes=allcoord,conn=conn,ifaces=iface,
                neumann=neumann,dirichlet=dirichlet,offset=off)


def solve(n,patch):
    tic=time.monotonic()
    regions=[make_region(n,0,0)]
    regions.append(make_region(n,1,len(regions[0]['nodes'])))
    nd=sum(len(r['nodes']) for r in regions)
    coords=np.vstack([r['nodes'] for r in regions]); rows=[];cols=[];values=[];forcing=np.zeros(nd)
    local_bulk=[]
    for region in regions:
        sigma=region['sigma']
        for dofs in region['conn']:
            xyz=coords[dofs[:3]];g,area=gradlam_triangle(xyz)
            grads=np.array([basis(lam,g)[1] for lam in REFL])
            ke=area*sigma/3*np.einsum('qai,qbi->ab',grads,grads)
            local_bulk.append((dofs,ke))
            for a in range(6):
                for b in range(6):
                    rows.append(int(dofs[a]));cols.append(int(dofs[b]));values.append(float(ke[a,b]))
        # y=0 and y=1 use exact outward normal flux of smooth solution,
        # held fixed even in the later finite-patch numerical stress test.
        for dofs,ny in region['neumann']:
            endcoords=coords[dofs[:2]];dx=endcoords[1,0]-endcoords[0,0]
            assert dx>0
            for t,w in zip(QPOINTS,QWEIGHTS):
                x=endcoords[0,0]+t*dx
                dydv=TAU-Q1*x/sigma+(1 if region['region']==0 else -1)*RC*Q1/2
                normal_out_sigma_grad=ny*sigma*dydv
                N=np.array(((1-t)*(1-2*t),t*(2*t-1),4*t*(1-t)))
                forcing[dofs]+=dx*w*normal_out_sigma_grad*N
    thermal_interface_blocks=[]
    for j in range(n):
        if patch and not (.25<=j/n+1e-10 and (j+1)/n<=.75+1e-10):continue
        l=regions[0]['ifaces'][j];r=regions[1]['ifaces'][j]
        dofs=np.r_[l,r];M=(1/(n*RC))*REFLINE_M
        B=np.block([[M,-M],[-M,M]])
        thermal_interface_blocks.append((dofs,B,j))
        for a in range(6):
            for b in range(6):
                rows.append(int(dofs[a]));cols.append(int(dofs[b]));values.append(float(B[a,b]))
    assert len(thermal_interface_blocks)==(n//2 if patch else n)
    K=coo_matrix((values,(rows,cols)),shape=(nd,nd)).tocsr()
    dirichlet=np.r_[regions[0]['dirichlet'],regions[1]['dirichlet']]
    allidx=np.arange(nd);fixed=np.zeros(nd,bool);fixed[dirichlet]=True
    free=allidx[~fixed]
    u=np.zeros(nd)
    for region in regions:
        ids=region['dirichlet'];u[ids]=analytic(region['region'],coords[ids,0],coords[ids,1])
    u[free]=spsolve(K[free][:,free],forcing[free]-K[free][:,dirichlet]@u[dirichlet])
    residual=np.linalg.norm((K@u-forcing)[free])/max(np.linalg.norm(forcing[free]-K[free][:,dirichlet]@u[dirichlet]),1e-30)
    assert residual<1e-8,residual
    energy_bulk=sum(float(u[dofs]@ke@u[dofs]) for dofs,ke in local_bulk)
    energy_interface=sum(float(u[dofs]@mat@u[dofs]) for dofs,mat,_ in thermal_interface_blocks)
    matrix_energy=float(u@K@u)
    assert abs(matrix_energy-energy_bulk-energy_interface)/max(matrix_energy,1e-30)<1e-10
    reaction=K@u-forcing
    power_work=float(u[dirichlet]@reaction[dirichlet]+u@forcing)
    assert abs(matrix_energy-power_work)/matrix_energy<1e-10
    # Separate analytical reference and independent face-normal calculation:
    # retrieve P2 field traces from each adjacent triangle; do NOT borrow
    # contact-matrix reactions as one-sided raw fluxes.
    boundary_pair=[]
    tri_maps=[]
    for region in regions:
        tri_map={}
        for dofs in region['conn']:
            # triangle corner IDs define physical boundary face
            c=dofs[:3]
            for a,b in ELOCAL:
                key=tuple(sorted((int(c[a]),int(c[b]))))
                if key in tri_map:tri_map[key]=None
                else:tri_map[key]=dofs
        tri_maps.append(tri_map)
    all_sample=[];currents=[]
    for j in range(n):
        if patch and not (.25<=j/n+1e-10 and (j+1)/n<=.75+1e-10):continue
        L=regions[0]['ifaces'][j];R=regions[1]['ifaces'][j]
        jl=[]
        for region,face,lookup in zip(regions,(L,R),tri_maps):
            e=tuple(sorted((int(face[0]),int(face[1]))))
            elem=lookup[e];assert elem is not None
            jl.append(elem)
        for t,w in zip(QPOINTS,QWEIGHTS):
            y=(j+t)/n
            q=[]
            for region,elem in zip(regions,jl):
                abc=coords[elem[:3]];g,_=gradlam_triangle(abc)
                # robust standard barycentrics via barycentric inverse:
                X=np.column_stack((abc,np.ones(3)))
                l=np.linalg.solve(X.T,np.array([0.,y,1.]))
                _,gr=basis(l,g)
                jx=-region['sigma']*float(u[elem]@gr[:,0])
                q.append(jx)
            N=np.array(((1-t)*(1-2*t),t*(2*t-1),4*t*(1-t)))
            qjump=float((u[L]-u[R])@N/RC)
            currents.append((w/n,y,q[0],q[1],qjump,QS(y)))
    cur=np.asarray(currents)
    integrated=np.sum(cur[:,0,None]*cur[:,2:],axis=0)
    q_ref=QS(cur[:,1]); weights=cur[:,0]
    norm=float(np.dot(weights,np.abs(q_ref)))
    abs_errors={f'{q}':float(np.dot(weights,np.abs(cur[:,k]-q_ref))/norm) for k,q in ((2,'left_raw_exact'),(3,'right_raw_exact'),(4,'contact_exact'))}
    side_to_contact={s:float(np.dot(weights,np.abs(cur[:,k]-cur[:,4]))/max(np.dot(weights,np.abs(cur[:,4])),1e-30)) for s,k in (('left',2),('right',3))}
    if not patch:
        exact=np.concatenate([analytic(reg['region'],reg['nodes'][:,0],reg['nodes'][:,1]) for reg in regions]);maxv=float(np.max(np.abs(u-exact)))
        assert maxv<1e-8,maxv
        assert max(abs_errors.values())<1e-8,abs_errors
        assert max(side_to_contact.values())<1e-8,side_to_contact
    else:maxv=None
    rec={'n':n,'finite_contact_patch':patch,'cells':sum(len(r['conn']) for r in regions),'dofs':nd,
         'interface_segments':len(thermal_interface_blocks),'max_potential_vs_exact':maxv,
         'raw_flux_error_vs_smooth_exact_normalized':abs_errors if not patch else None,
         'integral_current_left_right_contact_and_smooth_ref':integrated.tolist(),
         'raw_vs_contact_abs_relative':side_to_contact,
         'free_equation_residual':float(residual),
         'relative_power_identity_error':float(abs(matrix_energy-power_work)/matrix_energy),
         'numerical_bulk_power':energy_bulk,'numerical_contact_power':energy_interface,
         'max_V':float(np.max(u)),'min_V':float(np.min(u)),
         'seconds':time.monotonic()-tic,
         'limitation':'2D nondimensional mathematical coupon; no source CAD, no semiconductor physics, no qualified original 3D interface'}
    if patch:
        # Optional local bins for field-edge indicator, at interior quadrature points.
        inner=(cur[:,1]>=.30)&(cur[:,1]<=.70)
        rim=~inner
        rec['diagnostic_edge_fraction_abs_mismatch']={side:float(np.sum(cur[rim,0]*abs(cur[rim,k]-cur[rim,4]))/max(np.sum(cur[:,0]*abs(cur[:,k]-cur[:,4])),1e-30)) for side,k in (('left',2),('right',3))}
    return rec


def main():
    # Bounded benchmark: 2 exact-solution + 3 physical-tip solves, no iterative tuning.
    configs=[(8,False),(16,False),(8,True),(16,True),(24,True)]
    out=[]
    for n,patch in configs:
        rec=solve(n,patch);out.append(rec)
        print('CASE',n,'patch',patch,'NDOF',rec['dofs'],'RAWvsCONTACT',rec['raw_vs_contact_abs_relative'],'time',round(rec['seconds'],2),flush=True)
    smooth=[x for x in out if not x['finite_contact_patch']];edge=[x for x in out if x['finite_contact_patch']]
    assert len(smooth)==2 and len(edge)==3
    assert all(max(x['raw_vs_contact_abs_relative'].values())<1e-8 for x in smooth)
    assert all(x['relative_power_identity_error']<1e-10 for x in out)
    result={'name':'V3.16 independent 2D polynomial-contact manufactured solution and sharp-ended finite patch stress case',
       'scope':'Proof of planar P2 contact variational formulation on smooth polynomial exact solution; stress test without exact solution on finite contact tip',
       'benchmark_only_no_source_3D_qualification':True,
       'source_3D_electrical_gate_B':'FAIL/STOP; V3.14 11/16 raw cuts fail 0.1%',
       'source_3D_thermal_gate_C':'NOT RUN','source_3D_Joule_gate_D':'NOT RUN',
       'material_model':'dimensionless left conductivity 1, right 3, contact r=0.2. Not HgCdTe or TEC metal.',
       'reference':'Exact harmonic bilinear Vleft/Vright; independent Q(y)=1+0.35(y-.5), interface jump rQ(y). Mixed natural y boundaries and x-end Dirichlet.',
       'patch_coverage':'contact only y in [0.25,0.75], remaining interface insulated, same exterior boundary data; no analytic exact patch solution',
       'predefined_cases':configs,'results':out,
       'scientific_decision':'Smooth exact interface can satisfy raw/weak flux gate; presence of a finite contact termination requires independent sharp-edge reference and refinement verification. This does NOT imply existing 3D model passed.'}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(8.4,4.5));fig.subplots_adjust(left=.15,right=.96,top=.73,bottom=.19)
    for side,color,mark in [('left','#3f758e','o'),('right','#b57848','s')]:
        ax.semilogy([x['n'] for x in edge],[100*x['raw_vs_contact_abs_relative'][side] for x in edge],mark+'-',lw=2,color=color,label=side+' one-sided raw current')
    ax.axhline(.1,color='#a94a4a',ls='--',label='Source 3D gate threshold (comparison only)')
    ax.set_xticks([8,16,24]);ax.set_xlabel('Uniform subdivision count per axis (2D mathematical coupon)');ax.set_ylabel('Integrated absolute raw–contact flux mismatch (%)')
    ax.grid(alpha=.17,which='both');fig.text(.06,.95,'Smooth polynomial contact passes; finite tips challenge raw gradients',fontsize=13.2,weight='bold',color='#22374c')
    fig.text(.06,.89,'Dimensionless 2D method benchmark — not the source-native 3D TEC geometry',fontsize=9,color='#53677a')
    fig.legend(loc='upper left',bbox_to_anchor=(.14,.84),frameon=False,ncol=2,fontsize=8.5)
    for ext in ('pdf','png'):
        p=OUT/f'v316_sharp_contact_raw_flux.{ext}'
        kw={'metadata':{'Creator':'V3.16 manufactured solution benchmark','CreationDate':None,'ModDate':None}} if ext=='pdf' else {'dpi':190}
        fig.savefig(p,bbox_inches='tight',**kw)
    plt.close(fig)
    result['figure_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'v316_sharp_contact_raw_flux.pdf',OUT/'v316_sharp_contact_raw_flux.png')}
    (OUT/'benchmark_results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
