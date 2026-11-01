"""Fail-closed native gas-domain prerequisite: independent STEP/SI audit.

No old cavity geometry, ray operator, comparative fields or PDE is imported.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import time

import numpy as np

from .exchange_geometry import read_msh
from .fem_g3b_exchange import gas_properties

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'fem/results/geometry_complete_checkpoint_20261030'
CAP=ROOT/'fem/results/corrected_enclosure_geometry_20261030'
NOTE=ROOT/'docs/NATIVE_GAS_DOMAIN_AUDIT_20261101.md'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def write(p,obj):
    def native(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        raise TypeError(type(x).__name__)
    Path(p).write_text(json.dumps(obj,indent=2,default=native,allow_nan=False)+'\n')


def step_units(text):
    prefixes=re.findall(r'LENGTH_UNIT\(\)\s+NAMED_UNIT\(\*\)\s+SI_UNIT\(([^,]+),\.METRE\.\)',text)
    if not prefixes or len(set(prefixes))!=1:raise ValueError('Missing or mixed STEP length units')
    factors={'.MILLI.':1e-3,'$':1.}
    if prefixes[0] not in factors:raise ValueError('Unsupported STEP length unit')
    radii=[float(x) for x in re.findall(r"CYLINDRICAL_SURFACE\('[^']*',#\d+,([^\)]+)\)",text)]
    return {'length_prefix':prefixes[0],'length_contexts':len(prefixes),
            'metres_per_coordinate_unit':factors[prefixes[0]],
            'cylinder_radii_declared_m':sorted(set(x*factors[prefixes[0]] for x in radii))}


def interleg_gaps(manifest):
    result=[]
    for stage in range(3):
        rows=[b['boxes_m'][0] for b in manifest['bodies'] if b['kind']=='leg' and b['stage']==stage]
        distances=[]
        for i,a in enumerate(rows):
            for b in rows[i+1:]:
                delta=np.maximum(np.maximum(np.array(a[:2])-np.array(b[:2])-b[3:5],
                                             np.array(b[:2])-np.array(a[:2])-a[3:5]),0.)
                distance=float(np.linalg.norm(delta))
                if distance>1e-12:distances.append(distance)
        if not distances:raise ValueError('No positive native interleg gap')
        result.append({'stage':stage+1,'legs':len(rows),'minimum_xy_surface_gap_m':min(distances)})
    return result


def regime(gap,height,pressure,temperature=300.,contrast=50.):
    if not np.isfinite([gap,height,pressure,temperature,contrast]).all() or min(gap,height,pressure)<=0 or contrast<0:
        raise ValueError('Finite positive geometry/pressure required')
    p=gas_properties('N2',temperature,pressure);rho=float(p['rho']);nu=float(p['mu'])/rho;alpha=float(p['k'])/(rho*p['cp'])
    def ra(length):return 9.80665/temperature*contrast*length**3/(nu*alpha)
    return {'gas':'N2','pressure_pa':pressure,'T_k':temperature,'contrast_k':contrast,
        'k_w_mk':float(p['k']),'lambda_m':float(p['lambda_m']),
        'Kn_interleg':float(p['lambda_m'])/gap,'Kn_cavity_height':float(p['lambda_m'])/height,
        'Ra_interleg':ra(gap),'Ra_nominal_cavity_height':ra(height),
        'interleg_continuum_screen_Kn_below_001':float(p['lambda_m'])/gap<.01,
        'nominal_cavity_buoyancy_flag':ra(height)>1708.,
        'orientation':'z vertical, header below cap; 1708 is a heated-below slab flag, not a universal cavity threshold',
        'closure':'Registered NIST k(200..400 K); ideal gas and Eucken viscosity estimate, not measured viscosity or rarefied validation',
        'scope':'Conditional nominal SI-geometry scales only; no admitted gas domain or selected operating case'}


def import_record(gmsh,path):
    gmsh.clear();gmsh.model.add(path.stem);gmsh.option.setString('Geometry.OCCTargetUnit','M')
    volumes=gmsh.model.occ.importShapes(str(path),highestDimOnly=True);gmsh.model.occ.synchronize()
    rows=[]
    for dim,tag in volumes:
        if dim!=3:continue
        rows.append({'tag':tag,'volume_m3':gmsh.model.occ.getMass(3,tag),
                     'bbox_m':gmsh.model.occ.getBoundingBox(3,tag)})
    return rows


def gate(expected_cap_volumes,imported_cap,package_ok):
    ratios=sorted(r['volume_m3'] for r in imported_cap)/np.array(sorted(expected_cap_volumes.values()))
    consistent=len(imported_cap)==3 and np.allclose(ratios,1.,rtol=1e-6,atol=0.)
    return {'source_units_admissible':bool(package_ok and consistent),'cap_import_to_SI_registry_volume_ratios':ratios.tolist(),
            'Boolean_void_extractions':0,'gas_cells':0,'gas_PDE_solves':0,'comparative_fields_read':False,
            'reason':'STOP: unit-aware cap STEP disagrees with its SI registry/native mesh' if not consistent else 'Unit gate passed only; void not yet qualified'}


def run(out):
    start=time.monotonic();out=Path(out)
    if out.exists():raise ValueError('Use an absent output directory')
    registry=ROOT/'data/corrected_enclosure/geometry_hypothesis_v1.json'
    ledger=read(PACKAGE/'checksums.json')['artifact_sha256'];cap_ledger=read(ROOT/'data/corrected_enclosure/exchange_sources_v1.json')['fixture_sha256']
    for name in ('manifest.json','mesh.npz','reference.step.gz','wire_routes.json'):
        if sha(PACKAGE/name)!=ledger[name]:raise ValueError('Package archive identity changed')
    for name,h in cap_ledger.items():
        if sha(CAP/name)!=h:raise ValueError('Cap archive identity changed')
    m=read(PACKAGE/'manifest.json');cap=read(CAP/'geometry_audit.json');cfg=read(registry)
    if sha(registry)!=cap['assumptions_sha256']:raise ValueError('Cap hypotheses changed')
    step_package=gzip.decompress((PACKAGE/'reference.step.gz').read_bytes()).decode()
    step_cap=(CAP/'corrected_cap_window.step').read_text()
    parsed={'package':step_units(step_package),'cap':step_units(step_cap)}
    nodes,tets,_=read_msh(CAP/'cap_window_only.msh');native={};counts={}
    for body,ids in tets:
        xyz=np.array([nodes[i] for i in ids]);v=float(np.linalg.det((xyz[1:]-xyz[0]).T)/6)
        if v<=0:raise ValueError('Invalid native cap tetrahedron')
        native[body]=native.get(body,0.)+v;counts[body]=counts.get(body,0)+1
    for name,tag in cap['volume_physical_groups'].items():
        if not np.isclose(native[tag],cap['actual_volumes_m3'][name],rtol=.01):raise ValueError('Cap mesh/registry volume mismatch')
    out.mkdir(parents=True);work=out/'reader_controls';work.mkdir()
    package_file=work/'package.step';package_file.write_text(step_package)
    import gmsh
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
    try:
        gmsh.model.add('one_mm_cube');gmsh.model.occ.addBox(0,0,0,1,1,1);gmsh.model.occ.synchronize()
        cube=work/'one_mm_cube.step';gmsh.write(str(cube));cube_units=step_units(cube.read_text())
        if cube_units['metres_per_coordinate_unit']!=1e-3:raise ValueError('Analytic cube writer did not declare mm')
        cube_read=import_record(gmsh,cube)
        if len(cube_read)!=1 or not np.isclose(cube_read[0]['volume_m3'],1e-9,rtol=1e-8):raise ValueError('Independent SI reader control failed')
        package_read=import_record(gmsh,package_file)
        expected=sum(b['expected_volume_m3'] for b in m['bodies']);header=max(package_read,key=lambda x:x['volume_m3'])
        expected_header=next(b['expected_volume_m3'] for b in m['bodies'] if b['id']==300)
        package_ok=(len(package_read)==len(m['bodies']) and np.isclose(sum(r['volume_m3'] for r in package_read),expected,rtol=2e-7)
                    and np.isclose(header['volume_m3'],expected_header,rtol=2e-7))
        if not package_ok:raise ValueError('Unit-aware corrected package disagrees with native source volumes')
        cap_read=import_record(gmsh,CAP/'corrected_cap_window.step');version=gmsh.__version__
    finally:gmsh.finalize()
    # The decompressed package reader input is identical source data, not a new CAD edition.
    package_file.unlink()
    decision=gate(cap['actual_volumes_m3'],cap_read,package_ok)
    declared_ro=max(parsed['cap']['cylinder_radii_declared_m']);header_h=m['registry']['dimensions']['header_thickness']['simulated']*.001
    bb=np.array([r['bbox_m'] for r in cap_read]);cap_low=bb[:,:3].min(0);cap_high=bb[:,3:].max(0)
    d=m['registry']['dimensions'];bore_min=d['pin_pcd']['simulated']*.0005-d['glass_od']['simulated']*.0005
    hole_min=d['hole_pitch']['simulated']*.0005-d['hole_diameter']['simulated']*.0005
    radial_bound=float(np.linalg.norm(np.maximum(abs(cap_low[:2]),abs(cap_high[:2]))))
    inside_header=(cap_low[2]>0 and cap_high[2]<header_h and radial_bound<min(bore_min,hole_min,d['central_radius']['simulated']*.001))
    gaps=interleg_gaps(m);smallest=min(x['minimum_xy_surface_gap_m'] for x in gaps)
    result={'scope':'Source-only native gas geometry prerequisite and conditional N2 scales; no gas field',
        'registration':NOTE.read_text().split('## Results')[0],'parsed_STEP_units':parsed,
        'gmsh_version':version,'reader_target_unit':'M','analytic_cube':{'units':cube_units,'actual':cube_read,'expected_volume_m3':1e-9,'passed':True},
        'package_CAD':{'volumes':len(package_read),'total_volume_m3':sum(r['volume_m3'] for r in package_read),'expected_total_m3':expected,'header':header,'SI_source_volumes_consistent':bool(package_ok)},
        'cap_CAD_import':cap_read,'native_cap_mesh':{'tetrahedra':sum(counts.values()),'counts':counts,'volumes_m3':native,'SI_registry_consistent_within_1_percent':True},
        'cap_intended_outer_radius_m':cap['outer_radius_m'],'cap_STEP_declared_outer_radius_m':declared_ro,
        'cap_STEP_to_intended_length_ratio':declared_ro/cap['outer_radius_m'],
        'cap_import_bbox_m':{'low':cap_low,'high':cap_high,'note':'OpenCASCADE bounding boxes include kernel tolerance padding'},
        'as_imported_cap_inside_Kovar_core':bool(inside_header),'header_top_m':header_h,
        'containment_proof':{'cap_radial_bbox_bound_m':radial_bound,'nearest_feedthrough_bore_radius_from_origin_m':bore_min,
            'nearest_mounting_hole_radius_from_origin_m':hole_min,'central_header_disk_radius_m':d['central_radius']['simulated']*.001,
            'meaning':'Entire as-declared cap lies between header planes, inside central disk, outside all bores; cap interior minus header has no gas volume'},
        'native_counts':{'package_solid_bodies':len(m['bodies']),'legs':sum(b['kind']=='leg' for b in m['bodies']),
            'pins':sum(b['kind']=='pin' for b in m['bodies']),'glass_seals':sum(b['kind']=='glass' for b in m['bodies']),
            'cap_solids':len(cap_read),'hybrid_wires_without_native_3D_volume':len(read(PACKAGE/'wire_routes.json')['wires'])},
        'interleg_source_gaps':gaps,'conditional_N2_regime_screens':[regime(smallest,cap['cavity_height_m'],p) for p in (100.,101325.)],
        'decision':decision,'gas_domain_checks':{'connectivity':None,'watertight_manifold_boundary':None,'gas_solid_ownership_normals_areas':None,'gas_mesh_quality':None},
        'gas_heat_budgets_w':None,'gas_temperature_field':None,'selected_operating_pressure_pa':None,
        'minimum_next_fix':'Publish a separate unit-correct cap/window STEP derivative with explicit physical units and SI round-trip bbox/volume checks against registry and native mesh; preserve the original archived bytes. Then resume the registered void geometry gate.',
        'Rev3_modified':False,'original_solid_stops_and_raw_release_failures_retained':True,
        'elapsed_seconds':time.monotonic()-start,
        'source_sha256':{n:sha(ROOT/n) for n in ('tecooledmct/native_gas_audit.py','tecooledmct/exchange_geometry.py','tecooledmct/fem_g3b_exchange.py')},
        'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (PACKAGE/'manifest.json',PACKAGE/'mesh.npz',PACKAGE/'reference.step.gz',PACKAGE/'wire_routes.json',CAP/'corrected_cap_window.step',CAP/'cap_window_only.msh',CAP/'geometry_audit.json',registry)}}
    if decision['source_units_admissible']:raise RuntimeError('No unit defect confirmed; do not claim a gas stop from this audit')
    if not inside_header:raise RuntimeError('Source containment implication not confirmed')
    write(out/'audit.json',result)
    write(out/'checksums.json',{'artifact_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    r=run(args.out);print(json.dumps({'decision':r['decision'],'length_ratio':r['cap_STEP_to_intended_length_ratio'],
        'inside_header':r['as_imported_cap_inside_Kovar_core'],'regimes':r['conditional_N2_regime_screens']},indent=2))
