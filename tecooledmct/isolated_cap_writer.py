"""Fresh-process millimetre author/export only: imports are forbidden."""
import argparse
import os
from pathlib import Path
import time

import numpy as np

from .corrected_enclosure import assumptions
from .native_gas_audit import ROOT,sha,write,step_units


def run(out):
    start=time.monotonic();out=Path(out)
    if out.exists():raise ValueError('Use an absent writer directory')
    a=assumptions();out.mkdir(parents=True)
    import gmsh
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4)
    gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    def forbidden(*args,**kwargs):raise RuntimeError('Import/open/merge forbidden in the author process')
    gmsh.model.occ.importShapes=forbidden;gmsh.open=forbidden;gmsh.merge=forbidden
    try:
        gmsh.model.add('analytic_cube_mm');occ=gmsh.model.occ
        occ.addBox(0,0,0,1,1,1);occ.synchronize()
        cube=out/'one_mm_cube.step';gmsh.write(str(cube))
        gmsh.clear();gmsh.model.add('registered_cap_mm')
        ro,ri,rw=[a[k]*1000 for k in ('outer_radius_m','inner_radius_m','window_radius_m')]
        z0,zr,zt=[a[k]*1000 for k in ('header_top_z_m','cavity_roof_z_m','roof_top_z_m')]
        outer=occ.addCylinder(0,0,z0,0,0,zr-z0,ro);inner=occ.addCylinder(0,0,z0,0,0,zr-z0,ri)
        shell=occ.cut([(3,outer)],[(3,inner)])[0]
        outer=occ.addCylinder(0,0,zr,0,0,zt-zr,ro);inner=occ.addCylinder(0,0,zr,0,0,zt-zr,rw)
        roof=occ.cut([(3,outer)],[(3,inner)])[0]
        window=[(3,occ.addCylinder(0,0,zr,0,0,zt-zr,rw))]
        _,mapping=occ.fragment(shell,roof+window);occ.synchronize();owners={};volumes={}
        for label,entities in zip(('shell','roof','window'),mapping):
            tags=[tag for dim,tag in entities if dim==3]
            if len(tags)!=1:raise ValueError('Unexpected cap fragments')
            tag=tags[0];owners[tag]=label;gmsh.model.setEntityName(3,tag,'registered_'+label)
            volumes[label]=occ.getMass(3,tag)*1e-9
            if not np.isclose(volumes[label],a['expected_solid_volumes_m3'][label],rtol=1e-8,atol=1e-20):raise ValueError('Author volume differs')
        interfaces={}
        for _,face in gmsh.model.getEntities(2):
            up,_=gmsh.model.getAdjacencies(2,face)
            if len(up)==2:
                key='_'.join(sorted(owners[int(v)] for v in up));interfaces[key]=interfaces.get(key,0.)+occ.getMass(2,face)*1e-6
            elif len(up)!=1:raise ValueError('Author nonmanifold face')
        target=out/'cap_window_mm_derivative.step';gmsh.write(str(target))
        # Text parsing only, after BOTH exports. No CAD import occurs here.
        parsed=step_units(target.read_text());parsed_cube=step_units(cube.read_text())
        if parsed['metres_per_coordinate_unit']!=1e-3 or parsed_cube['metres_per_coordinate_unit']!=1e-3:raise ValueError('Writer did not declare mm')
        if not np.allclose(parsed['cylinder_radii_declared_m'],sorted([a['outer_radius_m'],a['inner_radius_m'],a['window_radius_m']]),rtol=1e-12,atol=1e-15):
            raise ValueError('Exported physical radii differ')
        version=gmsh.__version__
    finally:gmsh.finalize()
    result={'writer_pid':os.getpid(),'process_role':'fresh author/export ONLY','CAD_imports':0,
        'numerical_coordinate_unit':'mm','import_target_option':'MM; never used for an import',
        'cube_STEP_sha256':sha(cube),'derivative_STEP_sha256':sha(target),
        'parsed_derivative':parsed,'author_volumes_m3':volumes,'author_interfaces_m2':interfaces,
        'physical_geometry_changed':False,'attempts':1,'gmsh_version':version,
        'source_sha256':sha(Path(__file__)),'elapsed_seconds':time.monotonic()-start}
    write(out/'writer.json',result);print('Writer exported cube and cap; CAD imports = 0')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();run(args.out)
