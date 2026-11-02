"""Independent 3D P1 finite-contact operator. SI only; no TEC law or fitting.

Separate nodal traces at actual material interfaces permit voltage jumps. Contact
bilinear is exact P1 triangle mass. Bulk tensor and contact losses independently
integrate the solved fields; raw gradients are never replaced by reactions.
"""
import itertools,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
from .flux_presolder_common import affine_geometry
from .candidate_cu_fem import plane_current

PROPS={'Cu':(1/58e6,385.),'Ni':(7e-8,90.),'Au':(2.44e-8,317.),'Ti':(4.2e-7,22.),'TiW':(1e-6,10.),'BiSn':(4e-7,20.),'InSn':(1.5e-7,30.),'SnSb':(1.7e-7,45.)}
LAYERS=[('Ti',.075e-6),('TiW',.050e-6),('Cu',13.625e-6),('Ni',1e-6),('Au',.25e-6)]
PINLAYERS=[('Ni',2e-6),('Au',1.5e-6)]
SCENARIOS={'LOW':dict(film_factor=1.,re=1e-12,rt=1e-8,plated_re=0.,plated_rt=1e-9),'NOM':dict(film_factor=2.,re=1e-11,rt=1e-7,plated_re=1e-14,plated_rt=1e-8),'HIGH':dict(film_factor=4.,re=1e-10,rt=1e-6,plated_re=1e-13,plated_rt=1e-7)}

def laminate(layers,mode,scenario):
    s=SCENARIOS[scenario];thick=sum(t for m,t in layers);parallel=0.;normal_R=0.
    for m,t in layers:
        rho,k=PROPS[m];factor=s['film_factor'] if m=='Cu' else 1.
        c=1/(rho*factor) if mode=='electric' else k/factor
        parallel+=c*t;normal_R+=t/c
    normal_R+=(len(layers)-1)*s['plated_re' if mode=='electric' else 'plated_rt']
    return np.diag([parallel/thick,parallel/thick,thick/normal_R])

def tensors(groups,mode='electric',scenario='NOM'):
    if mode not in ('electric','thermal') or scenario not in SCENARIOS:raise ValueError('Registered law only')
    out=[]
    for g in groups:
        m=g['material']
        if m in ('laminate','pin_laminate'):out.append(laminate(LAYERS if m=='laminate' else PINLAYERS,mode,scenario))
        else:
            rho,k=PROPS[m];out.append(np.eye(3)*(1/rho if mode=='electric' else k))
    return np.array(out)

def connectivity(points,cells,regions,triangles,faceids,registry):
    """Independent full tetrahedral face incidence; no missing physical cuts."""
    table=defaultdict(list)
    for e,row in enumerate(cells):
        for k in range(4):table[tuple(sorted(np.delete(row,k)))].append(e)
    required={f for f,ee in table.items() if len(ee)==1 or len({int(regions[e]) for e in ee})==2}
    if any(len(ee)>2 for ee in table.values()):raise ValueError('Nonmanifold volume mesh')
    marked=[tuple(sorted(t)) for t in triangles]
    if len(set(marked))!=len(marked) or set(marked)!=required:raise ValueError('Mesh face coverage missing/duplicate')
    meta={f['tag']:f for f in registry['faces']};owners=[];vectors=[]
    for tri,tag in zip(triangles,faceids):
        ee=table[tuple(sorted(tri))];r=meta[int(tag)];order=sorted(ee,key=lambda e:regions[e])
        if [int(regions[e]) for e in order]!=r['owners']:raise ValueError('CAD/mesh face ownership disagreement')
        a=np.cross(points[tri[1]]-points[tri[0]],points[tri[2]]-points[tri[0]])/2
        if np.dot(a,points[tri].mean(0)-points[cells[order[0]]].mean(0))<0:a=-a
        owners.append(order+[ -1]*(2-len(order)));vectors.append(a)
    return np.array(owners),np.array(vectors),meta

class Operator:
    def __init__(self,points,cells,regions,triangles,faceids,registry,conductivity,contact_r):
        self.p=points;self.t=cells;self.r=regions;self.faces=triangles;self.fid=faceids;self.reg=registry
        self.owners,self.vectors,self.meta=connectivity(points,cells,regions,triangles,faceids,registry)
        self.area=np.linalg.norm(self.vectors,axis=1);self.volume,self.grad=affine_geometry(points,cells)
        self.tensor=np.asarray(conductivity)[regions]
        # One disjoint nodal trace per bulk region; finite contact couples them.
        pair=np.stack([np.repeat(regions,4),cells.ravel()],axis=1);unique,iv=np.unique(pair,axis=0,return_inverse=True)
        self.dofs=iv.reshape(-1,4);self.unique=unique;self.ndof=len(unique);lookup={(int(r),int(n)):i for i,(r,n) in enumerate(unique)}
        ke=self.volume[:,None,None]*np.einsum('eia,eab,ejb->eij',self.grad,self.tensor,self.grad)
        rows=np.repeat(self.dofs,4,axis=1).ravel().tolist();cols=np.tile(self.dofs,(1,4)).ravel().tolist();vals=ke.ravel().tolist();self.contacts=[];self.boundaries=[]
        for j,(tri,tag,own) in enumerate(zip(triangles,faceids,self.owners)):
            f=self.meta[int(tag)];a=f['owners'][0];da=np.array([lookup[(a,int(n))] for n in tri]);M=self.area[j]/12*(np.ones((3,3))+np.eye(3))
            if len(f['owners'])==2:
                b=f['owners'][1];db=np.array([lookup[(b,int(n))] for n in tri]);R=contact_r
                if not np.isfinite(R) or R<=0:raise ValueError('Finite positive specified contactR required')
                C=M/R;ix=np.r_[da,db];mat=np.block([[C,-C],[-C,C]])
                rows.extend(np.repeat(ix,6));cols.extend(np.tile(ix,6));vals.extend(mat.ravel());self.contacts.append((j,a,b,da,db,C))
            else:self.boundaries.append((j,da,f,M))
        self.K=coo_matrix((vals,(rows,cols)),shape=(self.ndof,self.ndof)).tocsr()
        if np.max(abs((self.K-self.K.T).data),initial=0)>1e-8:raise ValueError('Nonreciprocal discretization')

    def electrical(self):
        boundary=np.zeros(self.ndof,bool);u=np.zeros(self.ndof);src=[];dst=[]
        for j,da,f,M in self.boundaries:
            ep=f['electrical_port']
            if ep<0:continue
            boundary[da]=True;u[da]=1. if ep==0 else 0.;(src if ep==0 else dst).extend(da)
        src=np.unique(src);dst=np.unique(dst)
        if len(src)==0 or len(dst)==0 or len(np.intersect1d(src,dst)):raise ValueError('Missing/doubleelectrode')
        free=~boundary;u[free]=splu(self.K[free][:,free].tocsc()).solve(-(self.K@u)[free]);reaction=self.K@u
        I=float(reaction[src].sum());Iout=-float(reaction[dst].sum())
        if not I>0:raise ValueError('Passive input conductance')
        grad=np.einsum('ei,eij->ej',u[self.dofs]-u[self.dofs[:,:1]],self.grad)
        J=-np.einsum('eij,ej->ei',self.tensor,grad);density=-np.einsum('ei,ei->e',J,grad);bulk=self.volume*density
        losses=defaultdict(float)
        for r,p in zip(self.r,bulk):losses[self.reg['groups'][int(r)]['material']]+=float(p)
        cp=defaultdict(float);cuts=defaultdict(lambda:dict(natural=0.,raw_a=0.,raw_b=0.,area=0.))
        for j,a,b,da,db,C in self.contacts:
            jump=u[da]-u[db];q=float(np.sum(C@jump));power=float(jump@C@jump);pair=(a,b)
            cp[str(pair)]+=power;cut=cuts[pair];cut['natural']+=q;cut['raw_a']+=float(J[self.owners[j,0]]@self.vectors[j]);cut['raw_b']+=float(J[self.owners[j,1]]@(-self.vectors[j]));cut['area']+=self.area[j]
        graph=defaultdict(set)
        for a,b in cuts:graph[a].add(b);graph[b].add(a)
        inlet=next(i for i,g in enumerate(self.reg['groups']) if g['name']=='pn87_solder') if any(g['name']=='pn87_solder' for g in self.reg['groups']) else int(self.unique[src[0],0])
        outlet=int(self.unique[dst[0],0]);cutrows=[]
        for (a,b),c in cuts.items():
            seen={a};todo=[a]
            while todo:
                x=todo.pop()
                for y in graph[x]:
                    if {x,y}=={a,b}:continue
                    if y not in seen:seen.add(y);todo.append(y)
            sign=int(inlet in seen)-int(outlet in seen);expected=sign*I
            errors=[abs(c['natural']-expected)/I,abs(c['raw_a']-expected)/I,abs(c['raw_b']+expected)/I]
            cutrows.append(dict(pair=[self.reg['groups'][a]['name'],self.reg['groups'][b]['name']],expected_fraction=sign,natural_A=c['natural'],raw_a_A=c['raw_a'],raw_b_A=c['raw_b'],area_m2=c['area'],natural_relative_error=errors[0],raw_relative_error=max(errors[1:]),gate_error=max(errors)))
        for ep,names,expect in [(0,src,-I),(1,dst,I)]:
            raw=sum(float(J[self.owners[j,0]]@self.vectors[j]) for j,da,f,M in self.boundaries if f['electrical_port']==ep)
            cutrows.append(dict(terminal=ep,raw_out_A=raw,expected_out_A=expect,gate_error=abs(raw-expect)/I))
        # Registered true interior cuts,not selected afterthefield.
        if any(g['name']=='tab88' for g in self.reg['groups']):
            ti=next(i for i,g in enumerate(self.reg['groups']) if g['name']=='tab88');li=next(i for i,g in enumerate(self.reg['groups']) if g['name']=='lead9')
            for name,r,axis,pos in [('tab88_lower',ti,2,.00268425),('tab88_upper',ti,2,.00378425),('lead9_mid',li,0,(-.5-4.368691769624716)*.0005)]:
                use=self.r==r;q,area=plane_current(self.p,self.t[use],J[use],axis,pos)
                if area<=0:raise ValueError('Registered interiorcut haszeroarea')
                cutrows.append(dict(interior=name,axis=axis,position_m=pos,raw_A=q,expected_A=-I,area_m2=area,gate_error=abs(q+I)/I))
        power=float(bulk.sum()+sum(cp.values()));error=abs(power/I-1);gerror=max(c['gate_error'] for c in cutrows)
        per_case=[dict(I_A=i,V_V=i/I,R_coupon_ohm=1/I,P_W=i*i/I,stress_only=abs(i)==1.,linearity='Exact scaling ofpassive linearunit-potentialfield;notindependentnonlinear solve') for i in (0.,.1,.4,1.,-.4)]
        result=dict(unit_potential_current_A=I,R_coupon_ohm=1/I,opposite_terminal_relative_error=abs(Iout/I-1),bulk_loss_W=float(bulk.sum()),interface_loss_W=float(sum(cp.values())),material_losses_unitV_W=dict(losses),interface_losses_unitV_W=dict(cp),IV_W=I,loss_relative_error=error,worst_cut_relative_error=gerror,cuts=cutrows,cases=per_case,minimum_voltage=float(u.min()),maximum_voltage=float(u.max()),peak_J_unitV_A_m2=float(np.linalg.norm(J,axis=1).max()),gates=dict(cuts_0p1pct=gerror<=.001,power_0p5pct=error<=.005))
        return result,u,J,density

def structured(axes,region_for_cell):
    shape=tuple(len(a) for a in axes);points=np.array(np.meshgrid(*axes,indexing='ij')).reshape(3,-1).T;cells=[];regions=[]
    idx=lambda p:np.ravel_multi_index(tuple(p),shape)
    for i,j,k in itertools.product(*(range(n-1) for n in shape)):
        for perm in itertools.permutations(range(3)):
            p=np.array([i,j,k]);row=[idx(p)]
            for axis in perm:p=p.copy();p[axis]+=1;row.append(idx(p))
            cells.append(row);regions.append(region_for_cell(i,j,k))
    return points,np.array(cells),np.array(regions)

def control_faces(points,tets,regions,axis):
    fs=defaultdict(list)
    for e,row in enumerate(tets):
        for j in range(4):fs[tuple(sorted(np.delete(row,j)))].append(e)
    triangles=[];ids=[];rows=[];vmin=points[:,axis].min();vmax=points[:,axis].max()
    for f,ee in fs.items():
        own=sorted({int(regions[e]) for e in ee})
        if len(ee)==2 and len(own)==1:continue
        tri=list(f);ep=-1
        if len(ee)==1 and np.all(abs(points[tri,axis]-vmax)<1e-15):ep=0
        if len(ee)==1 and np.all(abs(points[tri,axis]-vmin)<1e-15):ep=1
        tag=len(rows);triangles.append(tri);ids.append(tag);rows.append(dict(tag=tag,owners=own,electrical_port=ep,thermal_port=-1))
    return np.array(triangles),np.array(ids),rows

def controls():
    results=[]
    for mode in ('electric','thermal'):
        nominal=SCENARIOS['NOM'];r=nominal['plated_re' if mode=='electric' else 'plated_rt'];thick=sum(t for m,t in LAYERS)
        for n in (2,4):
            z=np.array([0.]+list(np.cumsum([t for m,t in LAYERS])));zs=[];kinds=[]
            for j in range(5):zs.extend(np.linspace(z[j],z[j+1],3)[:-1]);kinds.extend([j,j])
            zs.append(z[-1]);axes=[np.linspace(0,.0004,n+1),np.linspace(0,.0003,n+1),np.array(zs)]
            p,t,rg=structured(axes,lambda i,j,k:k//2);gs=[dict(name=m,material=m) for m,th in LAYERS]
            D=[]
            for m,th in LAYERS:
                rho,k=PROPS[m];f=nominal['film_factor'] if m=='Cu' else 1.;D.append(np.eye(3)*(1/(rho*f) if mode=='electric' else k/f))
            hom=laminate(LAYERS,mode,'NOM')
            for axis in (0,2):
                tr,ids,fr=control_faces(p,t,rg,axis);op=Operator(p,t,rg,tr,ids,dict(groups=gs,faces=fr),np.array(D),r)
                rr,u,J,H=op.electrical();expected=(hom[axis,axis]*(.0003*thick)/.0004 if axis==0 else hom[2,2]*.0004*.0003/thick)
                err=abs(rr['unit_potential_current_A']/expected-1)
                if err>1e-7 or rr['loss_relative_error']>1e-7:raise ValueError('Layer/sheet analyticcontrol failed '+str((mode,n,axis,err)))
                zr=np.zeros(len(rg),int);tt,ii,ff=control_faces(p,t,zr,axis)
                hop=Operator(p,t,zr,tt,ii,dict(groups=[dict(name='homogenized',material='effective')],faces=ff),np.array([hom]),r)
                hr,_,_,_=hop.electrical();he=abs(hr['unit_potential_current_A']/expected-1)
                if he>1e-7:raise ValueError('Homogeneous anisotropicgridcontrol failed '+str(he))
                results.append(dict(mode=mode,n=n,axis=axis,explicit_layer_G=rr['unit_potential_current_A'],homogenized_grid_G=hr['unit_potential_current_A'],homogenized_exact_G=expected,relative_error=max(err,he),power_error=rr['loss_relative_error']))
    return dict(status='PASS independent3Dexplicitlayer/contact andanalytic slab/sheet controls',tests=results,max_relative_error=max(q['relative_error'] for q in results),mesh_counts=[2,4],source_domain='Selectedconstantlaws only;notexperimentalvalidation')
