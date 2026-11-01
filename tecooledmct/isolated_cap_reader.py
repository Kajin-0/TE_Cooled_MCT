"""Fresh SI-reader qualification; never authors or exports geometry."""
import argparse
import gzip
import os
from pathlib import Path
import tempfile
import time

import numpy as np

from .native_gas_audit import ROOT,PACKAGE,CAP,sha,read,write,step_units,import_record
from .corrected_enclosure import assumptions
from .cap_export_validation import classify_physical_scale
from .exchange_geometry import verify_sources,read_msh


def expected_boxes(a):
    ro,rw=a['outer_radius_m'],a['window_radius_m'];z0,zr,zt=[a[k] for k in ('header_top_z_m','cavity_roof_z_m','roof_top_z_m')]
    return {'shell':[-ro,-ro,z0,ro,ro,zr],'roof':[-ro,-ro,zr,ro,ro,zt],'window':[-rw,-rw,zr,rw,rw,zt]}


def cap_roles(rows,a):
    expected=a['expected_solid_volumes_m3'];boxes=expected_boxes(a);roles={}
    for row in rows:
        names=[name for name,v in expected.items() if np.isclose(row['volume_m3'],v,rtol=1e-8,atol=1e-20)
               and np.max(abs(np.array(row['bbox_m'])-boxes[name]))<=2.1e-7]
        if len(names)!=1 or names[0] in roles:raise ValueError('Ambiguous cap role, scale or datum')
        roles[names[0]]=row
    if set(roles)!=set(expected):raise ValueError('Missing cap solid')
    return roles


def run(folder):
    start=time.monotonic();folder=Path(folder).resolve();out=folder/'qualification.json'
    if out.exists():raise ValueError('Do not overwrite qualification')
    source_hashes=verify_sources();a=assumptions();writer=read(folder/'writer.json')
    if writer['writer_pid']==os.getpid() or writer['CAD_imports']!=0:raise ValueError('Writer/reader process isolation failed')
    cube=folder/'one_mm_cube.step';target=folder/'cap_window_mm_derivative.step'
    if sha(cube)!=writer['cube_STEP_sha256'] or sha(target)!=writer['derivative_STEP_sha256']:raise ValueError('Export changed before read')
    parsed=step_units(target.read_text());m=read(PACKAGE/'manifest.json');d=m['registry']['dimensions']
    import gmsh
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4)
    def forbidden(*args,**kwargs):raise RuntimeError('No exports permitted in SI reader')
    gmsh.write=forbidden
    try:
        cube_rows=import_record(gmsh,cube)
        if len(cube_rows)!=1 or not np.isclose(cube_rows[0]['volume_m3'],1e-9,rtol=1e-8):raise ValueError('Cube SI control failed')
        rows=import_record(gmsh,target);roles=cap_roles(rows,a)
        if not classify_physical_scale(rows,a['expected_solid_volumes_m3'])['physical_scale_qualified']:raise ValueError('Unit scale failed')
        tag_role={v['tag']:k for k,v in roles.items()};faces=[]
        for _,face in gmsh.model.getEntities(2):
            up,_=gmsh.model.getAdjacencies(2,face)
            if not 1<=len(up)<=2:raise ValueError('Nonmanifold reader face')
            faces.append({'tag':face,'owners':[tag_role[int(v)] for v in up],
                'area_m2':gmsh.model.occ.getMass(2,face),'bbox_m':gmsh.model.occ.getBoundingBox(2,face),
                'centroid_m':gmsh.model.occ.getCenterOfMass(2,face)})
        interfaces={}
        for f in faces:
            if len(f['owners'])==2:
                key='_'.join(sorted(f['owners']));interfaces[key]=interfaces.get(key,0.)+f['area_m2']
        # STEP products can retain separate, coincident faces. Count each
        # geometric mating once; B will require actual conformal incidence.
        if not interfaces:
            for i,f in enumerate(faces):
                for g in faces[i+1:]:
                    if f['owners']==g['owners']:continue
                    if (np.isclose(f['area_m2'],g['area_m2'],rtol=1e-8,atol=1e-18)
                        and np.max(abs(np.array(f['bbox_m'])-g['bbox_m']))<1e-10
                        and np.linalg.norm(np.array(f['centroid_m'])-g['centroid_m'])<1e-10):
                        key='_'.join(sorted(f['owners']+g['owners']));interfaces[key]=interfaces.get(key,0.)+f['area_m2']
        expected={'roof_shell':np.pi*(a['outer_radius_m']**2-a['inner_radius_m']**2),
                  'roof_window':2*np.pi*a['window_radius_m']*(a['roof_top_z_m']-a['cavity_roof_z_m'])}
        if set(interfaces)!=set(expected) or any(not np.isclose(interfaces[k],v,rtol=1e-8,atol=1e-18) for k,v in expected.items()):raise ValueError('Reader cap mating failed')
        with tempfile.TemporaryDirectory(dir=folder) as tmp:
            path=Path(tmp)/'source_package.step';path.write_bytes(gzip.decompress((PACKAGE/'reference.step.gz').read_bytes()))
            package=import_record(gmsh,path)
        header=max(package,key=lambda r:r['volume_m3']);expected_header=next(b['expected_volume_m3'] for b in m['bodies'] if b['id']==300)
        if len(package)!=216 or not np.isclose(header['volume_m3'],expected_header,rtol=2e-7):raise ValueError('Source header import differs')
        if max(abs(np.array(header['bbox_m'])-[-.01575,-.00875,0,.01575,.00875,.0015]))>2.1e-7:raise ValueError('Header frame differs')
    finally:gmsh.finalize()
    # Exact source header construction: its central disk covers this complete
    # annulus, and every bore/hole lies strictly outside the mating annulus.
    R=d['central_radius']['simulated']*.001
    bore_outer=(d['pin_pcd']['simulated']+d['glass_od']['simulated'])*.0005
    mounting_inner=(d['hole_pitch']['simulated']-d['hole_diameter']['simulated'])*.0005
    ro,ri=a['outer_radius_m'],a['inner_radius_m'];z0=a['header_top_z_m']
    if not bore_outer<ri<ro<R or mounting_inner<=ro or z0!=d['header_thickness']['simulated']*.001:raise ValueError('Incomplete source header seal')
    nodes,tets,_=read_msh(CAP/'cap_window_only.msh');native={}
    for group,ids in tets:
        xyz=np.array([nodes[i] for i in ids]);v=float(np.linalg.det((xyz[1:]-xyz[0]).T)/6)
        if v<=0:raise ValueError('Native cap tetrahedron sign')
        native[group]=native.get(group,0.)+v
    old=read(CAP/'geometry_audit.json');mesh_error={n:native[t]/roles[n]['volume_m3']-1 for n,t in old['volume_physical_groups'].items()}
    if max(abs(v) for v in mesh_error.values())>.01:raise ValueError('Native cap mesh mismatch')
    failed=ROOT/'data/unit_correct_cap_native_gas_20261101/unaccepted_phase_A_attempt/cap_window_unit_correct.step'
    result={'phase_A_qualified':True,'writer_pid':writer['writer_pid'],'reader_pid':os.getpid(),
        'writer_CAD_imports':0,'reader_exports':0,'reader_target_unit':'M','cube_control':cube_rows,
        'parsed_derivative_units':parsed,'cap_roles':roles,'reader_faces':faces,'interfaces_m2':interfaces,
        'expected_bbox_m':expected_boxes(a),'expected_volumes_m3':a['expected_solid_volumes_m3'],
        'native_mesh_volume_relative_errors':mesh_error,
        'source_header':header,'header_seal':{'complete_annulus':True,'area_m2':expected['roof_shell'],
             'inner_radius_m':ri,'outer_radius_m':ro,'header_central_radius_m':R,'feedthrough_outer_radius_m':bore_outer,
             'mounting_hole_inner_radius_m':mounting_inner,'z_m':z0,'positive_volume_header_intrusion':False,
             'proof':'Cap support z>=header top; full annulus inside source central disk, outside all holes; exact nominal contact assumed impermeable'},
        'derivative_path':str(target.relative_to(ROOT)),'derivative_sha256':sha(target),
        'original_bad_STEP_sha256':sha(CAP/'corrected_cap_window.step'),'historical_rejected_STEP_sha256':sha(failed),
        'input_sha256':source_hashes,'source_sha256':{n:sha(ROOT/n) for n in ('tecooledmct/isolated_cap_writer.py','tecooledmct/isolated_cap_reader.py')},
        'elapsed_seconds':time.monotonic()-start,'physical_geometry_changed':False,'gas_field':None}
    write(out,result);print('Phase A PASS: isolated writer and SI reader; cap radius 7.6 mm')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);args=p.parse_args();run(args.data)
