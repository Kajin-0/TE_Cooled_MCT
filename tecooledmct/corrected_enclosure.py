"""Standalone source-aligned cap/window CAD fixture for corrected TO-66.

The corrected full package remains a *separate existing 3D mesh*. This
fixture is NOT a conforming extension of its tetrahedra, does not mesh
internal gas, and performs no thermal/electrical solve. Cap construction
is hypothetical except externally documented VIGO cap OD.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np

from .geometry_rebaseline import ROOT
from .integrated_reference import GEOMETRY, geometry

REGISTRY=ROOT/'data/corrected_enclosure/geometry_hypothesis_v1.json'


def assumptions():
    source=geometry() # validates corrected archive manifest and wire hashes
    m=json.loads((GEOMETRY/'manifest.json').read_text())
    hsource=m['registry']['dimensions']
    outer=hsource['cap_od']
    if outer['source']!='vigo' or abs(outer['simulated']-15.2)>1e-9:
        raise ValueError('Changed source cap diameter')
    header=hsource['header_thickness']
    if header['source']!='vigo' or abs(header['simulated']-1.5)>1e-9:
        raise ValueError('Changed header datum')
    cfg=json.loads(REGISTRY.read_text())
    if cfg['schema']!='corrected-enclosure-cad-hypothesis-v1':
        raise ValueError('Unknown enclosure assumptions schema')
    for name in ('cap_height_above_header_m','cap_wall_thickness_m',
                 'cap_roof_thickness_m','window_diameter_m','window_thickness_m'):
        value=cfg.get(name)
        if (isinstance(value,bool) or not isinstance(value,(int,float))
                or not math.isfinite(value) or value<=0):
            raise ValueError('Finite positive enclosure dimension required: '+name)
    ro=outer['simulated']*.0005
    ri=ro-cfg['cap_wall_thickness_m']
    rw=.5*cfg['window_diameter_m']
    z0=header['simulated']*.001
    ztop=z0+cfg['cap_height_above_header_m']
    zr=ztop-cfg['cap_roof_thickness_m']
    if (0<rw<ri<ro and math.isfinite(ztop) and math.isfinite(zr) and z0<zr
            and cfg['window_thickness_m']==cfg['cap_roof_thickness_m']):
        pass
    else:raise ValueError('Nonphysical enclosure assumption')
    if cfg['cap_height_above_header_m']<=cfg['cap_roof_thickness_m']:
        raise ValueError('Cap has no cavity')
    die_body=next(b for b in m['bodies'] if b['id']==303)
    die_box=die_body['boxes_m'][0]
    die_top_z=die_box[2]+die_box[5]
    internal_top_z=float('-inf')
    # All corrected stack solids must sit within the inner wall and below
    # the cavity roof. Exclude the resolved header and external pin tails.
    for body in m['bodies']:
        if body['kind'] in ('header','pin','glass'):continue
        for box in body.get('boxes_m',[]):
            x,y,z,dx,dy,dz=box
            if z>=z0-1e-12:
                far=max(math.hypot(xx,yy) for xx in (x,x+dx) for yy in (y,y+dy))
                internal_top_z=max(internal_top_z,z+dz)
                if far>ri-1e-6 or z+dz>=zr-1e-6:
                    raise ValueError('Corrected internal solid collides with hypothetical cap: '+body['name'])
    for pin in m['pin_tops']:
        if math.hypot(*pin['center_xy_m'])+.00055>=ri:
            raise ValueError('Feedthrough cap clearance failed')
        if pin['z_m']>=zr:raise ValueError('Feedthrough reaches roof')
    for w in source['wires']:
        points=np.asarray(w['polyline_m'])
        radial=np.sqrt((points[:,:2]**2).sum(axis=1)).max()+w['diameter_m']/2
        if radial>=ri or points[:,2].max()+w['diameter_m']/2>=zr:
            raise ValueError('Hybrid wire cap clearance failed')
    shell_h=zr-z0
    expected={'shell':math.pi*(ro**2-ri**2)*shell_h,
              'roof':math.pi*(ro**2-rw**2)*cfg['cap_roof_thickness_m'],
              'window':math.pi*rw**2*cfg['window_thickness_m']}
    if any(not math.isfinite(v) or v<=0 for v in expected.values()):
        raise ValueError('Nonphysical enclosure volume')
    return {'config':cfg,'outer_radius_m':ro,'inner_radius_m':ri,'window_radius_m':rw,
            'header_top_z_m':z0,'cavity_roof_z_m':zr,'roof_top_z_m':ztop,
            'cavity_height_m':shell_h,'window_to_die_top_min_m':zr-die_top_z,
            'roof_to_highest_resolved_solid_clearance_m':zr-internal_top_z,
            'expected_solid_volumes_m3':expected,'parent_source_sha256':source['source_sha256'],
            'assumptions_sha256':hashlib.sha256(REGISTRY.read_bytes()).hexdigest(),
            'safety':'geometry fixture only: no cavity gas volume, optical window law, or new full-assembly FEM'}


def build(out,*,mesh=False):
    data=assumptions()
    out=Path(out)
    if out.exists():raise ValueError('Do not overwrite an existing CAD checkpoint')
    out.mkdir(parents=True)
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal',0)
    try:
        gmsh.model.add('corrected_TO66_enclosure_reference')
        occ=gmsh.model.occ
        ro=data['outer_radius_m'];ri=data['inner_radius_m'];rw=data['window_radius_m']
        z0=data['header_top_z_m'];zr=data['cavity_roof_z_m'];ztop=data['roof_top_z_m']
        h=zr-z0;t=ztop-zr
        shell_outer=occ.addCylinder(0,0,z0,0,0,h,ro)
        shell_inner=occ.addCylinder(0,0,z0,0,0,h,ri)
        shell=occ.cut([(3,shell_outer)],[(3,shell_inner)],removeObject=True,removeTool=True)[0][0]
        roof_outer=occ.addCylinder(0,0,zr,0,0,t,ro)
        roof_bore=occ.addCylinder(0,0,zr,0,0,t,rw)
        roof=occ.cut([(3,roof_outer)],[(3,roof_bore)],removeObject=True,removeTool=True)[0][0]
        window=(3,occ.addCylinder(0,0,zr,0,0,t,rw))
        fragments,mapping=occ.fragment([shell],[roof,window],removeObject=True,removeTool=True)
        occ.synchronize()
        owners={}
        for label,objects in zip(('shell','roof','window'),mapping):
            for dim,tag in objects:
                if dim!=3:continue
                if tag in owners and owners[tag]!=label:
                    raise ValueError('Coincident or penetrating CAD solid')
                owners[tag]=label
        if set(owners)!=set(tag for dim,tag in fragments if dim==3):
            raise ValueError('Fragmented body ownership incomplete')
        if sorted(owners.values())!=['roof','shell','window']:
            raise ValueError('Unexpected cap fragment count/identity')
        volume={};volumetric_physical_groups={}
        for idx,label in enumerate(('shell','roof','window'),7301):
            tags=[tag for tag,owner in owners.items() if owner==label]
            gmsh.model.addPhysicalGroup(3,tags,idx,label)
            volumetric_physical_groups[label]=idx
            actual=sum(occ.getMass(3,tag) for tag in tags)
            expected=data['expected_solid_volumes_m3'][label]
            if abs(actual/expected-1)>1e-8:raise ValueError('CAD volume mismatch '+label)
            volume[label]=actual
        faces={}
        for _,tag in gmsh.model.getEntities(2):
            adjacent,_=gmsh.model.getAdjacencies(2,tag)
            labels=tuple(sorted(owners[int(v)] for v in adjacent))
            mass=occ.getMass(2,tag)
            if len(labels)==2:
                key='_'.join(labels)+'_interface'
            elif len(labels)==1:
                label=labels[0]
                zcenter=occ.getCenterOfMass(2,tag)[2]
                if label=='shell':
                    if abs(zcenter-z0)<1e-8:key='shell_header_mating_foot'
                    else:
                        ri_area=2*math.pi*ri*h;ro_area=2*math.pi*ro*h
                        key='shell_cavity_side' if abs(mass-ri_area)<abs(mass-ro_area) else 'shell_outside'
                elif label=='roof':
                    key='roof_cavity_underside' if abs(zcenter-zr)<1e-8 else 'roof_outside_top'
                elif label=='window':
                    key='window_cavity_underside' if abs(zcenter-zr)<1e-8 else 'window_outside_top'
                else:raise ValueError('Unknown boundary owner')
            else:raise ValueError('Nonmanifold cap surface')
            faces.setdefault(key,[]).append((tag,mass))
        required={'shell_header_mating_foot','shell_cavity_side','shell_outside',
                  'roof_cavity_underside','roof_outside_top',
                  'window_cavity_underside','window_outside_top',
                  'roof_shell_interface','roof_window_interface'}
        if set(faces)!=required:
            print('CAP FACE CLASSIFICATION',[(k,[(t,round(a,10)) for t,a in v]) for k,v in faces.items()])
            raise ValueError('Missing or unexpected cap surfaces: '+repr(set(faces)^required))
        face_audits={}
        # Reserve 7400-series face tags, avoiding the corrected FEM's 101/103/etc.
        for i,(name,rows) in enumerate(sorted(faces.items()),7401):
            gmsh.model.addPhysicalGroup(2,[tag for tag,_ in rows],i,name)
            face_audits[name]={'physical_group_id':i,'area_m2':sum(a for _,a in rows),
                               'surface_entity_tags':[tag for tag,_ in rows]}
        shell_roof=math.pi*(ro**2-ri**2)
        window_contact=2*math.pi*rw*t
        for key,expected in [('roof_shell_interface',shell_roof),('roof_window_interface',window_contact)]:
            if abs(face_audits[key]['area_m2']/expected-1)>1e-6:
                raise ValueError('Cap interface surface area disagrees with analytic geometry: '+key)
        gmsh.write(str(out/'corrected_cap_window.step'))
        if mesh:
            gmsh.option.setNumber('Mesh.MeshSizeMin',.00020)
            gmsh.option.setNumber('Mesh.MeshSizeMax',.00075)
            gmsh.option.setNumber('Mesh.CharacteristicLengthFromCurvature',12)
            gmsh.option.setNumber('Mesh.Algorithm3D',1)
            gmsh.model.mesh.generate(3)
            gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
            gmsh.write(str(out/'cap_window_only.msh'))
            types,entity_tags,_=gmsh.model.mesh.getElements(3)
            count=sum(len(x) for x in entity_tags)
        else:count=0
        result={**data,'actual_volumes_m3':volume,'face_groups':face_audits,
                'volume_physical_groups':volumetric_physical_groups,
                'groups_3d':owners,'meshed_tetrahedra':count,
                'cap_window_only_mesh':bool(mesh),
                'no_conformal_interface_to_corrected_88leg_mesh':True,
                'conservative_thermal_3d_solution':False}
        (out/'geometry_audit.json').write_text(json.dumps(result,indent=2)+'\n')
        print('Corrected-geometry cap/window fixture PASSED:',out,'volume',volume,
              'surface_groups',len(faces),'tetrahedra',count)
        return result
    finally:
        gmsh.finalize()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mesh',action='store_true')
    a=p.parse_args()
    build(a.out,mesh=a.mesh)
