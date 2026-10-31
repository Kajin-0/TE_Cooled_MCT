"""Geometry-only positive resistor-cell multiport; no archived field input.

This local Cartesian conduction fixture has declared isothermal surface ports.
It is not a full-device 3D FEM or a calibrated map from ceramic volume means.
"""
from pathlib import Path
import hashlib
import json
import re
import time

import numpy as np
from scipy.sparse import coo_matrix,triu
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu

from .integrated_reference import ROOT, Scenario, geometry, coefficients,stage_thermoelectric
from .fem_g1 import tetra_geometry
from .fem_g2a import PROPERTIES

GEOM=ROOT/'fem/results/geometry_complete_checkpoint_20261030'
SIF=ROOT/'fem/results/corrected_coupled_thermal_20261030/cases/cu_off/case.sif'
SELECTED=(184,185,186,187,188,189,190,191,192)
PORT_BODIES=(1,2,3,116,117,165,166,182,183,174)
THERMAL_PORT={1:0,116:0,117:0,2:1,165:1,166:1,3:2,182:2,183:2,174:3}
ROUTES=((184,117,165),(185,166,182),(190,None,116),(191,183,None))
PORT_NAMES=('hot','intermediate_1','intermediate_2','P174_side_contact')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def inputs():
    """Audit source geometry/SIF only; neither metrics nor solved fields read."""
    ledger=read(GEOM/'checksums.json')['artifact_sha256']
    for name in ('manifest.json','mesh.npz'):
        if sha(GEOM/name)!=ledger[name]:raise ValueError('Geometry archive changed')
    sifledger=read(SIF.parents[2]/'checksums.json')['artifact_sha256']
    if sha(SIF)!=sifledger['cases/cu_off/case.sif']:raise ValueError('SIF changed')
    m=read(GEOM/'manifest.json');by={b['id']:b for b in m['bodies']}
    names=sorted({b['material'] for b in by.values()});text=SIF.read_text()
    for name in ('P','N','Cu','Alumina'):
        n=names.index(name)+1
        block=re.search(r'^Material '+str(n)+r'\n(.*?)^End',text,re.M|re.S).group(1)
        for label,value in zip(('Heat Conductivity','Electric Conductivity','Seebeck Coefficient'),PROPERTIES[name][:3]):
            actual=float(re.search(label+r' = Real ([^\n]+)',block).group(1))
            if not np.isclose(actual,value,rtol=1e-14,atol=1e-20):raise ValueError('Material mismatch')
    d=np.load(GEOM/'mesh.npz');p,c,b=(d[k] for k in ('points','cells','bodies'))
    vol,_=tetra_geometry(p,c);native={str(i):float(vol[b==i].sum()) for i in SELECTED}
    for i in SELECTED:
        if not np.isclose(native[str(i)],by[i]['expected_volume_m3'],rtol=1e-8,atol=1e-20):
            raise ValueError('Native body volume differs')
    for contact in m['contacts']:
        if not any(i in SELECTED for i in contact['bodies']):continue
        f=d['faces'][d['boundaries']==contact['boundary_id']];xyz=p[f]
        a=float(np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1).sum()/2)
        if not np.isclose(a,contact['area_m2'],rtol=1e-8,atol=1e-18):raise ValueError('Native contact area differs')
    return m,{'input_sha256':{str(x.relative_to(ROOT)):sha(x) for x in (GEOM/'manifest.json',GEOM/'mesh.npz',SIF)},
              'native_volumes_m3':native,'native_contacts_verified':True}


def inside(points,boxes):
    mask=np.zeros(len(points),bool)
    for box in boxes:
        lo=np.array(box[:3]);hi=lo+box[3:]
        mask|=np.all((points>lo-1e-14)&(points<hi+1e-14),axis=1)
    return mask


def axes_for(by,h):
    if not np.isfinite(h) or h<=0:raise ValueError('Positive grid spacing required')
    axes=[]
    for a in range(3):
        values=[]
        for bid in (*SELECTED,*PORT_BODIES):
            for box in by[bid]['boxes_m']:values.extend([box[a],box[a]+box[a+3]])
        if a==2:
            for st in range(3):
                box=next(b for b in by.values() if b.get('stage')==st and b['kind']=='leg')['boxes_m'][0]
                values.append(box[2]+box[5]/2)
        knots=np.unique(np.round(values,13));grid=[]
        for lo,hi in zip(knots,knots[1:]):grid.extend(np.linspace(lo,hi,int(np.ceil((hi-lo)/h))+1))
        axes.append(np.unique(np.round(grid,13)))
    return axes


def cells_from_boxes(by,axes):
    shape=tuple(len(a)-1 for a in axes);keys=[]
    for bid in SELECTED:
        for box in by[bid]['boxes_m']:
            low=np.round(box[:3],13);high=np.round(np.array(box[:3])+box[3:],13)
            ranges=[np.arange(np.searchsorted(axes[a],low[a]),np.searchsorted(axes[a],high[a])) for a in range(3)]
            ijk=np.array(np.meshgrid(*ranges,indexing='ij')).reshape(3,-1)
            keys.append(np.ravel_multi_index(ijk,shape))
    keys=np.unique(np.concatenate(keys));indices=np.array(np.unravel_index(keys,shape)).T
    center=np.column_stack([(axes[a][indices[:,a]]+axes[a][indices[:,a]+1])/2 for a in range(3)])
    widths=np.column_stack([np.diff(axes[a])[indices[:,a]] for a in range(3)])
    owner=np.full(len(keys),-1,int)
    # Copper cuts the raw alumina support boxes, as in the actual source CSG.
    for material in ('Alumina','Cu'):
        used=np.zeros(len(keys),bool)
        for bid in SELECTED:
            if by[bid]['material']!=material:continue
            mask=inside(center,by[bid]['boxes_m'])
            if np.any(mask&used):raise ValueError('Overlapping distinct same-material bodies')
            used|=mask;owner[mask]=bid
    if np.any(owner<0):raise ValueError('Unassigned active geometry')
    if len(keys)>60000:raise ValueError('Active-cell bound exceeded')
    return keys,indices,center,widths,owner,shape


def laplacian(n,ports,edge_i,edge_j,g,bcells,bports,bg):
    ei=np.asarray(edge_i,int);ej=np.asarray(edge_j,int);g=np.asarray(g,float)
    bcells=np.asarray(bcells,int);bports=np.asarray(bports,int);bg=np.asarray(bg,float)
    if np.any(~np.isfinite(g)) or np.any(g<=0) or np.any(~np.isfinite(bg)) or np.any(bg<=0):
        raise ValueError('Nonpositive/nonfinite face conductance')
    if len(g)>200000:raise ValueError('Edge bound exceeded')
    ii=np.r_[ei,ej,ei,ej,bcells,n+bports,bcells,n+bports]
    jj=np.r_[ei,ej,ej,ei,bcells,n+bports,n+bports,bcells]
    vv=np.r_[g,g,-g,-g,bg,bg,-bg,-bg]
    L=coo_matrix((vv,(ii,jj)),shape=(n+ports,n+ports)).tocsr()
    _,component=connected_components(L,directed=False)
    if not set(component[:n]).issubset(set(component[n:])):raise ValueError('Unanchored internal component')
    return L


def condense(L,n):
    A=L[:n,:n].tocsc();B=L[:n,n:].toarray();D=L[n:,n:].toarray()
    factor=splu(A);ports=B.shape[1];H=np.empty_like(B)
    H[:,:-1]=-factor.solve(B[:,:-1]);H[:,-1]=1-H[:,:-1].sum(1)
    # Partition of unity defines the final harmonic basis. Edge-energy assembly
    # avoids subtracting large boundary diagonals in the Schur complement.
    U=np.vstack([H,np.eye(ports)]);upper=triu(L,k=1).tocoo();delta=U[upper.row]-U[upper.col]
    K=(delta.T*(-upper.data))@delta
    scale=max(np.max(abs(K)),1e-12)
    if (np.max(abs(K-K.T))>1e-10*scale or np.max(abs(K.sum(1)))>1e-10 or
        np.min(np.linalg.eigvalsh((K+K.T)/2))< -1e-10*scale or
        np.max(K-np.diag(np.diag(K)))>1e-10*scale or np.min(H)<-1e-9):
        raise ValueError('Passive reciprocity/positivity/closure check failed')
    return factor,B,H,K


def build(manifest,h):
    """Only manifest and material constants determine every coefficient."""
    start=time.monotonic();by={b['id']:b for b in manifest['bodies']};axes=axes_for(by,h)
    keys,ijk,center,width,body,shape=cells_from_boxes(by,axes);n=len(keys)
    kval=np.array([PROPERTIES[by[int(b)]['material']][0] for b in body]);cu=np.array([by[int(b)]['material']=='Cu' for b in body])
    sigma=np.where(cu,PROPERTIES['Cu'][1],0.);volume=np.prod(width,axis=1)
    ei=[];ej=[];gg=[];eg=[];edge_axis=[];edge_plane=[];edge_area=[]
    bc=[];bp=[];bg=[];boundary=[];contacts={}
    def area_add(a,b,area):
        if a!=b:
            pair=tuple(sorted((int(a),int(b))));contacts[pair]=contacts.get(pair,0.)+float(area)
    for a in range(3):
        stride=int(np.prod(shape[a+1:]));area=np.prod(np.delete(width,a,axis=1),axis=1)
        for direction in (-1,1):
            valid=(ijk[:,a]+direction>=0)&(ijk[:,a]+direction<shape[a]);neighbor_key=keys+direction*stride
            ix=np.searchsorted(keys,neighbor_key);near=np.minimum(ix,n-1)
            exists=valid&(ix<n)&(keys[near]==neighbor_key)
            if direction==1:
                ids=np.flatnonzero(exists);js=ix[ids]
                conductance=area[ids]/(.5*width[ids,a]/kval[ids]+.5*width[js,a]/kval[js])
                electric=np.zeros(len(ids));both=cu[ids]&cu[js]
                electric[both]=area[ids[both]]/(.5*width[ids[both],a]/sigma[ids[both]]+.5*width[js[both],a]/sigma[js[both]])
                ei.extend(ids);ej.extend(js);gg.extend(conductance);eg.extend(electric)
                edge_axis.extend([a]*len(ids));edge_plane.extend(axes[a][ijk[ids,a]+1]);edge_area.extend(area[ids])
                for i,j,ar in zip(ids,js,area[ids]):area_add(body[i],body[j],ar)
            ids=np.flatnonzero(~exists);face=center[ids].copy();face[:,a]+=direction*width[ids,a]/2
            probe=face.copy();probe[:,a]+=direction*1e-10;target=np.full(len(ids),-1,int)
            for bid in PORT_BODIES:
                mask=inside(probe,by[bid]['boxes_m'])
                if np.any((target>=0)&mask):raise ValueError('Ambiguous external material contact')
                target[mask]=bid
            for q,i in enumerate(ids):
                bid=int(target[q]);port=THERMAL_PORT.get(bid,-1);ar=float(area[i])
                if bid>=0:area_add(body[i],bid,ar)
                eport=-1
                for ri,(route,left,right) in enumerate(ROUTES):
                    if body[i]!=route:continue
                    if bid==left:eport=2*ri
                    if bid==right:eport=2*ri+1
                    if route in (190,191):
                        # First source box is the external hot pad. None denotes
                        # its actual top surface, never an unrelated body ID.
                        pad=by[route]['boxes_m'][0]
                        if a==2 and direction==1 and abs(face[q,a]-(pad[2]+pad[5]))<1e-12:
                            eport=2*ri if left is None else 2*ri+1
                if port>=0:
                    bc.append(i);bp.append(port);bg.append(kval[i]*ar/(width[i,a]/2))
                if port>=0 or eport>=0:
                    boundary.append({'cell':int(i),'body':int(body[i]),'neighbor_body':bid,'thermal_port':port,
                        'electrical_port':eport,'axis':a,'sign':direction,'area_m2':ar,'center_m':face[q].tolist(),
                        'thermal_G':kval[i]*ar/(width[i,a]/2),'electrical_G':sigma[i]*ar/(width[i,a]/2) if eport>=0 else 0.})
    expected={tuple(x['bodies']):x['area_m2'] for x in manifest['contacts'] if any(i in SELECTED for i in x['bodies'])}
    if set(contacts)!=set(expected):raise ValueError('Unmapped/missing source material contacts: '+str(set(contacts)^set(expected)))
    for pair,wanted in expected.items():
        if not np.isclose(contacts[pair],wanted,rtol=1e-8,atol=1e-18):raise ValueError('Contact area mismatch '+str(pair))
    for bid in SELECTED:
        if not np.isclose(volume[body==bid].sum(),by[bid]['expected_volume_m3'],rtol=1e-8,atol=1e-20):raise ValueError('CSG body volume differs '+str(bid))
    ei=np.array(ei,int);ej=np.array(ej,int);gg=np.array(gg);eg=np.array(eg)
    L=laplacian(n,4,ei,ej,gg,bc,bp,bg);factor,B,H,K=condense(L,n)
    cids=np.flatnonzero(cu);emap=np.full(n,-1,int);emap[cids]=np.arange(len(cids));mask=eg>0
    eb=[x for x in boundary if x['electrical_port']>=0]
    EL=laplacian(len(cids),8,emap[ei[mask]],emap[ej[mask]],eg[mask],
        [emap[x['cell']] for x in eb],[x['electrical_port'] for x in eb],[x['electrical_G'] for x in eb])
    _,_,EH,EK=condense(EL,len(cids));portv=np.zeros(8);resistances=[]
    for route in range(4):
        G=EK[2*route,2*route];R=1/G
        if G<=0 or abs(EK[2*route,2*route+1]+G)>1e-8*G:raise ValueError('Electrical two-port mismatch')
        resistances.append(float(R));portv[2*route]=R # per ampere
    phi=np.zeros(n);phi[cids]=EH@portv;current_ports=EK@portv
    if np.max(abs(current_ports-np.tile([1.,-1.],4)))>1e-8:raise ValueError('Electrical series-current closure')
    source=np.zeros(n);port_source=np.zeros(4);loss=eg*(phi[ei]-phi[ej])**2
    np.add.at(source,ei,loss/2);np.add.at(source,ej,loss/2)
    for row in eb:
        power=row['electrical_G']*(phi[row['cell']]-portv[row['electrical_port']])**2
        if row['thermal_port']>=0:
            source[row['cell']]+=power/2;port_source[row['thermal_port']]+=power/2
        else:source[row['cell']]+=power
    if abs(source.sum()+port_source.sum()-sum(resistances))>1e-9:raise ValueError('Electrical IV/Joule mismatch')
    u=factor.solve(source);jport=port_source-B.T@u
    if np.min(jport)<-1e-10 or abs(jport.sum()-sum(resistances))>1e-9:raise ValueError('Condensed Joule source not conservative')
    p174=[r for r in boundary if r['neighbor_body']==174];a174=sum(r['area_m2'] for r in p174)
    z174=sum(r['area_m2']*r['center_m'][2] for r in p174)/a174
    leg=by[174]['boxes_m'][0];distance=z174-leg[2]
    if not 0<distance<leg[5]:raise ValueError('Side contact outside P174')
    if time.monotonic()-start>180:raise ValueError('Geometry operator exceeded registered time bound')
    return {'h_m':h,'nodes':n,'center':center,'width':width,'body':body,'volume':volume,
        'edge_i':ei,'edge_j':ej,'edge_G':gg,'edge_axis':np.array(edge_axis),'edge_plane':np.array(edge_plane),
        'edge_area':np.array(edge_area),
        'boundary':boundary,'L':L,'factor':factor,'B':B,'H':H,'K':K,'source_per_A2':source,
        'port_source_per_A2':port_source,'u_per_A2':u,'joule_port_per_A2':jport,
        'Cu_R_ohm':resistances,'electrical_cell_potential_per_A':phi,
        'P174_contact_area_m2':a174,'P174_distance_m':distance,'P174_length_m':leg[5],
        'P174_area_m2':leg[3]*leg[4],'contacts_m2':{str(k):v for k,v in contacts.items()},
        'build_seconds':time.monotonic()-start}


def coupled(operator,current=.1,load=.002,hot=300.1148977882757,on=True):
    """Fixed-I affine energy equations, including a split side-contact P leg."""
    if not np.isfinite([current,load,hot]).all() or not 0<=current<=1 or load<0:raise ValueError('Invalid coupled inputs')
    g=geometry();cs=coefficients(Scenario(current_a=current),g);n=6;A=np.zeros((n,n));source=np.zeros(n)
    def edge(i,j,G):
        A[i,i]+=G;A[j,j]+=G;A[i,j]-=G;A[j,i]-=G
    legG=PROPERTIES['P'][0]*operator['P174_area_m2']/operator['P174_length_m']
    legR=operator['P174_length_m']/(PROPERTIES['P'][1]*operator['P174_area_m2'])
    for i,st in enumerate(cs):
        edge(i,i+1,st['k_w_k']-(legG if i==2 else 0))
        A[i,i]-=st['alpha_v_k']*current;A[i+1,i+1]+=st['alpha_v_k']*current
        j=current**2*(st['r_ohm']-(legR if i==2 else 0))/2;source[i]+=j;source[i+1]+=j
    fraction=operator['P174_distance_m']/operator['P174_length_m'];area=operator['P174_area_m2'];k=PROPERTIES['P'][0]
    edge(2,5,k*area/operator['P174_distance_m']);edge(5,3,k*area/(operator['P174_length_m']-operator['P174_distance_m']))
    source[2]+=.5*current**2*legR*fraction;source[5]+=.5*current**2*legR
    source[3]+=.5*current**2*legR*(1-fraction)
    edge(3,4,1/g['die_attach_thickness_over_area_m_inverse']);source[4]+=load
    indices=[0,1,2,5]
    if on:
        A[np.ix_(indices,indices)]+=operator['K'];source[indices]+=operator['joule_port_per_A2']*current**2
    # Work around a fixed physical reference to avoid large uniform-T cancellation.
    rhs=source-A@np.full(n,hot);theta=np.zeros(n);free=np.arange(1,n)
    theta[free]=np.linalg.solve(A[np.ix_(free,free)],rhs[free]);temperature=theta+hot
    if min(temperature)<180 or max(temperature)>390 or not np.isfinite(temperature).all():raise ValueError('Temperature domain rejected')
    residual=A@temperature-source;stageV=[current*st['r_ohm']+st['alpha_v_k']*(temperature[i]-temperature[i+1]) for i,st in enumerate(cs)]
    voltage=sum(stageV)+(current*sum(operator['Cu_R_ohm']) if on else 0)
    bath=-float(residual[0]);energy=bath-load-current*voltage
    if max(abs(residual[free]))>1e-9 or abs(energy)>1e-9:raise ValueError('Coupled node/global energy failed')
    tp=theta[indices];cell_delta=operator['H']@tp+operator['u_per_A2']*current**2 if on else None
    network_into= -operator['K']@tp+operator['joule_port_per_A2']*current**2 if on else np.zeros(4)
    if cell_delta is not None and (min(cell_delta+hot)<180 or max(cell_delta+hot)>390):raise ValueError('Internal cell temperature domain rejected')
    stages=[stage_thermoelectric(st,temperature[i],temperature[i+1],current) for i,st in enumerate(cs)]
    jleg=current**2*legR;gh=k*area/operator['P174_distance_m'];gc=k*area/(operator['P174_length_m']-operator['P174_distance_m'])
    old_hot=-legG*(temperature[2]-temperature[3])+jleg/2
    old_cold=-legG*(temperature[2]-temperature[3])-jleg/2
    stages[2]['qh_w']+=gh*(temperature[5]-temperature[2])+jleg*fraction/2-old_hot
    stages[2]['qc_w']+=-gc*(temperature[5]-temperature[3])-jleg*(1-fraction)/2-old_cold
    for i,st in enumerate(stages):
        st['unsplit_reference_conduction_w']=st.pop('conduction_w')
        st['fourier_from_hot_w']=st['unsplit_reference_conduction_w']
        st['fourier_to_cold_w']=st['unsplit_reference_conduction_w']
        if i==2:
            rest=(cs[2]['k_w_k']-legG)*(temperature[2]-temperature[3])
            st['fourier_from_hot_w']=rest+gh*(temperature[2]-temperature[5])
            st['fourier_to_cold_w']=rest+gc*(temperature[5]-temperature[3])
        st['side_contact_in_w']=float(network_into[3]) if i==2 else 0.
        st['energy_residual_w']=st['qh_w']-st['qc_w']-current*st['voltage_v']
        st['energy_residual_including_side_w']=st['energy_residual_w']-st['side_contact_in_w']
        if abs(st['energy_residual_including_side_w'])>1e-9:raise ValueError('Stage/side-contact work mismatch')
    return {'temperatures_k':temperature.tolist(),'stage_lifts_k':(temperature[:3]-temperature[1:4]).tolist(),
        'stage_budget':stages,
        'PN_stage_voltage_v':stageV,'Cu_voltage_v':current*sum(operator['Cu_R_ohm']) if on else 0.,
        'module_voltage_v':voltage,'bath_out_w':bath,'global_energy_residual_w':energy,
        'free_node_residuals_w':residual[free].tolist(),'network_into_ports_w':network_into.tolist(),
        'route_Joule_w':(current**2*np.array(operator['Cu_R_ohm'])).tolist() if on else [0.]*4,
        'cell_temperature_delta_k':cell_delta}


def finite_die_readout(bottom_k,load,area,thickness):
    """1D uniform heating / adiabatic top, exact Kirchhoff k(T) transform."""
    if not np.isfinite([bottom_k,load,area,thickness]).all() or load<0 or area<=0 or thickness<=0:
        raise ValueError('Invalid finite-die readout')
    knots=np.array([90.,148.,298.,400.]);ks=np.array([2.41,1.61,.973,.790])
    if not 90<=bottom_k<=400:raise ValueError('MCT source domain')
    base=np.r_[0.,np.cumsum(np.diff(knots)*(ks[1:]+ks[:-1])/2)]
    def transform(t):
        i=min(np.searchsorted(knots,t,side='right')-1,2);u=t-knots[i]
        return base[i]+ks[i]*u+.5*(ks[i+1]-ks[i])/np.diff(knots)[i]*u*u
    def invert(value):
        if value>base[-1]+1e-12:raise ValueError('MCT profile exceeds source domain')
        i=min(np.searchsorted(base,value,side='right')-1,2);q=value-base[i];s=(ks[i+1]-ks[i])/np.diff(knots)[i]
        u=2*q/(ks[i]+np.sqrt(ks[i]**2+2*s*q));return knots[i]+u
    u0=transform(bottom_k);z,w=np.polynomial.legendre.leggauss(16);z=(z+1)*thickness/2
    profile=np.array([invert(u0+load/area*(v-v*v/(2*thickness))) for v in z])
    return {'mean_k':float(w@profile/2),'top_k':float(invert(u0+load*thickness/(2*area))),
            'method':'1D Kirchhoff transform; not actual 3D die fields or a fitted correction'}


def record(operator):
    """Serializable target-blind coefficient audit."""
    return {'schema':'geometry-derived-solid-multiport-v1','h_m':operator['h_m'],'nodes':operator['nodes'],
        'edges':len(operator['edge_i']),'port_names':list(PORT_NAMES),'K_W_K':operator['K'].tolist(),
        'joule_port_per_A2':operator['joule_port_per_A2'].tolist(),'Cu_R_ohm':operator['Cu_R_ohm'],
        'P174_contact_area_m2':operator['P174_contact_area_m2'],'P174_distance_m':operator['P174_distance_m'],
        'body_volumes_m3':{str(bid):float(operator['volume'][operator['body']==bid].sum()) for bid in SELECTED},
        'contacts_m2':operator['contacts_m2'],'build_seconds':operator['build_seconds'],
        'port_closure':'isothermal original ceramic/pad interfaces; lumped side-contact centroid',
        'no_reference_field_or_power_inputs':True,'source_sha256':sha(Path(__file__))}
