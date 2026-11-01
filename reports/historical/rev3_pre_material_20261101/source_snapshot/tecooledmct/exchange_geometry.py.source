"""Corrected-source face audit and a closed, explicitly simplified ray cavity.

Native mesh surfaces are audited, never presented as a joined full-package
mesh. The optical obstacle is a stepped opaque core filled between ceramics:
actual interleg voids, exposed metallization and pin/wire occlusion are omitted.
"""
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import qmc

from .corrected_enclosure import assumptions,REGISTRY
from .integrated_reference import GEOMETRY,geometry

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'fem/results/corrected_enclosure_geometry_20261030'
LEDGER=ROOT/'data/corrected_enclosure/exchange_sources_v1.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources():
    geometry()
    ledger=json.loads(LEDGER.read_text())
    hashes={str((FIXTURE/name).relative_to(ROOT)):sha(FIXTURE/name)
            for name in ledger['fixture_sha256']}
    if any(hashes[str((FIXTURE/name).relative_to(ROOT))]!=want
           for name,want in ledger['fixture_sha256'].items()):
        raise ValueError('Corrected enclosure fixture source hash mismatch')
    package=json.loads((GEOMETRY/'checksums.json').read_text())['artifact_sha256']
    if sha(GEOMETRY/'mesh.npz')!=package['mesh.npz']:
        raise ValueError('Corrected package mesh hash mismatch')
    audit=json.loads((FIXTURE/'geometry_audit.json').read_text())
    if audit['assumptions_sha256']!=sha(REGISTRY):raise ValueError('Cap configuration changed')
    hashes.update({str((GEOMETRY/name).relative_to(ROOT)):sha(GEOMETRY/name)
                   for name in ('manifest.json','mesh.npz','wire_routes.json')})
    hashes[str(REGISTRY.relative_to(ROOT))]=sha(REGISTRY)
    return hashes


def read_msh(path):
    nodes={};tets=[];triangles=[]
    lines=iter(path.read_text().splitlines())
    for line in lines:
        if line=='$Nodes':
            for _ in range(int(next(lines))):
                r=next(lines).split();nodes[int(r[0])]=list(map(float,r[1:]))
        elif line=='$Elements':
            for _ in range(int(next(lines))):
                r=list(map(int,next(lines).split()));kind,nt=r[1:3]
                if kind==4:tets.append((r[3],r[3+nt:]))
                elif kind==2:triangles.append((r[3],r[3+nt:]))
    return nodes,tets,triangles


@lru_cache(maxsize=2)
def _native_audit(source_key):
    # Cache only after recomputing and verifying all input hashes.
    nodes,tets,triangles=read_msh(FIXTURE/'cap_window_only.msh')
    faces={};volumes={};counts={}
    for body,v in tets:
        xyz=np.array([nodes[i] for i in v]);volume=np.linalg.det((xyz[1:]-xyz[0]).T)/6
        if volume<=0:raise ValueError('Nonpositive cap tetrahedron')
        volumes[body]=volumes.get(body,0.)+volume;counts[body]=counts.get(body,0)+1
        for ids in ((0,1,2),(0,1,3),(0,2,3),(1,2,3)):
            faces.setdefault(tuple(sorted(v[i] for i in ids)),[]).append(body)
    if set(volumes)!={7301,7302,7303} or any(len(v)>2 for v in faces.values()):
        raise ValueError('Invalid cap volume topology')
    area={};interface_counts={}
    for group,v in triangles:
        owners=faces.get(tuple(sorted(v)),[])
        expected={7301,7302} if group==7403 else {7302,7303}
        if group in (7403,7404):
            if len(owners)!=2 or set(owners)!=expected:raise ValueError('Cap interface ownership')
            interface_counts[group]=interface_counts.get(group,0)+1
        elif len(owners)!=1:raise ValueError('Cap exterior face ownership')
        xyz=np.array([nodes[i] for i in v])
        area[group]=area.get(group,0.)+np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2
    if set(area)!=set(range(7401,7410)):raise ValueError('Cap physical faces missing')
    native=json.loads((FIXTURE/'geometry_audit.json').read_text())
    relative={name:float(area[row['physical_group_id']]/row['area_m2']-1)
              for name,row in native['face_groups'].items()}
    if max(abs(v) for v in relative.values())>.02:raise ValueError('Cap facet areas disagree with BREP')
    d=np.load(GEOMETRY/'mesh.npz');points=d['points'];cells=d['cells'];bodies=d['bodies']
    exterior=d['faces'][d['boundaries']<10001]
    owners={tuple(sorted(f)):[] for f in exterior}
    for c,b in zip(cells,bodies):
        for ids in ((0,1,2),(0,1,3),(0,2,3),(1,2,3)):
            key=tuple(sorted(int(c[i]) for i in ids))
            if key in owners:owners[key].append(int(b))
    if any(len(v)!=1 for v in owners.values()):raise ValueError('Native exterior ownership is not unique')
    m=json.loads((GEOMETRY/'manifest.json').read_text());native_tops={}
    for body in m['bodies']:
        if body['id'] not in (1,2,3,4,303):continue
        box=body['boxes_m'][0];top=box[2]+box[5];total=0.;number=0
        for f in exterior:
            if owners[tuple(sorted(f))][0]!=body['id']:continue
            xyz=points[f]
            if np.max(np.abs(xyz[:,2]-top))<1e-10:
                total+=np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2;number+=1
        if total<=0:raise ValueError('Missing actual exposed top: '+body['name'])
        native_tops[body['name']]={'body_id':body['id'],'z_m':top,
            'native_exposed_area_m2':float(total),'native_triangles':number}
    return {'native_cap_tet_counts':counts,'native_cap_interface_triangle_counts':interface_counts,
            'native_cap_face_area_relative_to_BREP':relative,
            'native_package_exterior_triangles':len(exterior),'native_top_faces':native_tops,
            'all_audited_exterior_faces_have_one_owner':True}


def specification():
    hashes=verify_sources();audit=_native_audit(tuple(sorted(hashes.items())))
    cap=assumptions();m=json.loads((GEOMETRY/'manifest.json').read_text())
    byid={b['id']:b for b in m['bodies']}
    levels=[]
    for i,bid in enumerate((1,2,3,4,303)):
        box=byid[bid]['boxes_m'][0]
        levels.append({'side_m':box[3],'top_z_m':box[2]+box[5],
                       'source_body':bid,'temperature_node':i})
    return {'source_sha256':hashes,'native_audit':audit,'levels':levels,
        'radius_m':cap['inner_radius_m'],'window_radius_m':cap['window_radius_m'],
        'floor_z_m':cap['header_top_z_m'],'roof_z_m':cap['cavity_roof_z_m'],
        'scope':'Closed stepped opaque core proxy derived from corrected dimensions; NOT actual interleg/pin/wire visibility or a conformal full-device mesh.'}


def surfaces(spec):
    levels=spec['levels'];r=spec['radius_m'];rw=spec['window_radius_m']
    z0=spec['floor_z_m'];zr=spec['roof_z_m'];rows=[]
    for i,level in enumerate(levels):
        outer=level['side_m'];inner=levels[i+1]['side_m'] if i<4 else 0.
        weights=np.zeros(8);weights[i]=1.
        rows.append({'name':('hot','stage1','stage2','cold','die')[i]+'_top',
            'kind':'top','level':i,'outer_m':outer,'inner_m':inner,'z_m':level['top_z_m'],
            'area_m2':outer**2-inner**2,'weights':weights.tolist()})
        bottom=z0 if i==0 else levels[i-1]['top_z_m']
        if i>0:weights[i]=.5;weights[i-1]=.5
        rows.append({'name':'core_side_'+str(i),'kind':'side','level':i,
            'outer_m':outer,'bottom_z_m':bottom,'z_m':level['top_z_m'],
            'area_m2':4*outer*(level['top_z_m']-bottom),'weights':weights.tolist()})
    for name,kind,node,area in (
        ('header_floor','floor',5,math.pi*r*r-levels[0]['side_m']**2),
        ('cap_wall','wall',6,2*math.pi*r*(zr-z0)),
        ('cap_roof','roof',6,math.pi*(r*r-rw*rw)),
        ('window','window',7,math.pi*rw*rw)):
        weights=np.zeros(8);weights[node]=1.
        rows.append({'name':name,'kind':kind,'area_m2':area,'weights':weights.tolist()})
    if any(v['area_m2']<=0 for v in rows):raise ValueError('Nonpositive proxy surface')
    return rows


def emit(surface,spec,n,seed):
    # Low-discrepancy 4D area/direction samples; rejected floor samples retain
    # their independent direction coordinates. Seed is explicit and fixed.
    factor=4 if surface['kind']=='floor' else 1
    u=qmc.Sobol(4,scramble=True,seed=seed).random_base2(int(math.log2(n*factor)))
    x=np.zeros((len(u),3));normal=np.zeros_like(x);kind=surface['kind']
    if kind in ('top','side'):
        side=surface['outer_m'];half=side/2
        if kind=='top':
            inner=surface['inner_m'];h=inner/2
            rectangles=[(-half,-half,side,(side-inner)/2),(-half,h,side,(side-inner)/2),
                        (-half,-h,(side-inner)/2,inner),(h,-h,(side-inner)/2,inner)] if inner else [(-half,-half,side,side)]
            area=np.array([a*b for _,_,a,b in rectangles]);cdf=np.r_[0.,np.cumsum(area)/area.sum()]
            component=np.minimum(np.searchsorted(cdf,u[:,0],side='right')-1,len(area)-1)
            for j,(a,b,dx,dy) in enumerate(rectangles):
                use=component==j
                if not np.any(use):continue
                x[use,0]=a+dx*(u[use,0]-cdf[j])/(cdf[j+1]-cdf[j]);x[use,1]=b+dy*u[use,1]
            x[:,2]=surface['z_m'];normal[:,2]=1.
        else:
            v=4*u[:,0];face=v.astype(int);along=(v-face-.5)*side
            for j in range(4):
                use=face==j;axis=j//2
                x[use,axis]=half*(1 if j%2 else -1);x[use,1-axis]=along[use]
                normal[use,axis]=(1 if j%2 else -1)
            x[:,2]=surface['bottom_z_m']+u[:,1]*(surface['z_m']-surface['bottom_z_m'])
    elif kind=='wall':
        theta=2*np.pi*u[:,0];x[:,0]=spec['radius_m']*np.cos(theta);x[:,1]=spec['radius_m']*np.sin(theta)
        x[:,2]=spec['floor_z_m']+u[:,1]*(spec['roof_z_m']-spec['floor_z_m'])
        normal[:,:2]=-x[:,:2]/spec['radius_m']
    else:
        inner=spec['window_radius_m'] if kind=='roof' else 0.
        outer=spec['window_radius_m'] if kind=='window' else spec['radius_m']
        radius=np.sqrt(inner*inner+u[:,0]*(outer*outer-inner*inner));theta=2*np.pi*u[:,1]
        x[:,0]=radius*np.cos(theta);x[:,1]=radius*np.sin(theta)
        x[:,2]=spec['floor_z_m'] if kind=='floor' else spec['roof_z_m']
        normal[:,2]=1 if kind=='floor' else -1
        if kind=='floor':
            keep=np.any(np.abs(x[:,:2])>spec['levels'][0]['side_m']/2,axis=1)
            x=x[keep];normal=normal[keep];u=u[keep]
    if len(x)<n:raise ValueError('Insufficient accepted floor samples')
    x=x[:n];normal=normal[:n];u=u[:n]
    auxiliary=np.tile([0.,0.,1.],(n,1));auxiliary[np.abs(normal[:,2])>.9]=[1.,0.,0.]
    tangent=np.cross(normal,auxiliary);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    second=np.cross(normal,tangent);phi=2*np.pi*u[:,3];rad=np.sqrt(u[:,2])
    direction=(normal*np.sqrt(1-u[:,2])[:,None]+tangent*(rad*np.cos(phi))[:,None]
               +second*(rad*np.sin(phi))[:,None])
    return x+normal*1e-10,direction


def first_hit(start,direction,spec):
    n=len(start);distance=np.full(n,np.inf);owner=np.full(n,-1,dtype=int)
    def update(t,ids,valid):
        use=valid&(t>1e-12)&(t<distance)
        distance[use]=t[use];owner[use]=np.broadcast_to(ids,(n,))[use]
    # Cylinder sides and two circular lids.
    a=np.sum(direction[:,:2]**2,axis=1);b=2*np.sum(start[:,:2]*direction[:,:2],axis=1)
    c=np.sum(start[:,:2]**2,axis=1)-spec['radius_m']**2
    t=(-b+np.sqrt(np.maximum(b*b-4*a*c,0)))/(2*np.maximum(a,1e-30))
    z=start[:,2]+t*direction[:,2]
    update(t,11,(z>=spec['floor_z_m'])&(z<=spec['roof_z_m']))
    dz=direction[:,2];safe=np.where(abs(dz)>1e-30,dz,1.)
    for plane,is_roof in ((spec['floor_z_m'],False),(spec['roof_z_m'],True)):
        t=(plane-start[:,2])/safe;xy=start[:,:2]+t[:,None]*direction[:,:2]
        radius2=np.sum(xy*xy,axis=1)
        ids=np.where(radius2<=spec['window_radius_m']**2,13,12) if is_roof else 10
        update(t,ids,(abs(dz)>1e-30)&(radius2<=spec['radius_m']**2*(1+1e-12)))
    # Ray/AABB first intersections against the closed stepped core.
    for i,level in enumerate(spec['levels']):
        half=level['side_m']/2;bottom=spec['floor_z_m'] if i==0 else spec['levels'][i-1]['top_z_m']
        low=np.array([-half,-half,bottom]);high=np.array([half,half,level['top_z_m']])
        parallel=np.abs(direction)<1e-30;safe=np.where(parallel,1.,direction)
        t0=(low-start)/safe;t1=(high-start)/safe
        near=np.where(parallel,-np.inf,np.minimum(t0,t1));far=np.where(parallel,np.inf,np.maximum(t0,t1))
        axis=near.argmax(axis=1);enter=near.max(axis=1);leave=far.min(axis=1)
        valid=(enter<leave)&~np.any(parallel&((start<low)|(start>high)),axis=1)
        ids=np.where(axis==2,2*i,2*i+1)
        underside=(axis==2)&(dz>0)&valid&(enter>1e-12)&(enter<distance)
        if np.any(underside):raise ValueError('Accessible proxy underside: closure construction is wrong')
        update(enter,ids,valid)
    if np.any(owner<0) or not np.isfinite(distance).all():raise ValueError('Unclosed ray cavity')
    return owner,distance
