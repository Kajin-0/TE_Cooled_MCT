#!/usr/bin/env python3
"""Immutable source/mesh/DC evidence; explicitly excludes coupled thermal claims."""
import argparse,gzip,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tecooledmct.geometry_rebaseline import sha,write
from tecooledmct.geometry_complete import audit,manifest,wire_routes,REGISTRY
from tecooledmct.geometry_complete_measure import measure
from tecooledmct.full_presolder_guard import preserve

DEST=ROOT/'fem/results/geometry_complete_checkpoint_20261030'
MESH=ROOT/'outputs/geometry-complete-v4';DC=ROOT/'outputs/geometry-complete-dc-v3'
SOURCES=['tecooledmct/geometry_complete.py','tecooledmct/geometry_complete_electrical.py',
         'tecooledmct/geometry_complete_views.py','tecooledmct/geometry_complete_measure.py',
         'tests/test_geometry_complete.py','data/geometry_complete/reference_v2.json',
         'docs/GEOMETRY_COMPLETE_TEC_CHECKPOINT.md','NEXT_GEOMETRY_COMPLETION_WORK_ORDER.md',
         'fem/archive_geometry_complete.py']


def read(p):return json.loads(Path(p).read_text())


def old_guard():
    subprocess.run([sys.executable,str(ROOT/'fem/archive_full_presolder_checkpoint.py'),'--verify'],check=True)
    return preserve()


def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)


def zipped(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with src.open('rb') as inp,dst.open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as out:shutil.copyfileobj(inp,out)


def verify():
    ledger=read(DEST/'checksums.json')
    for group,parent in [('source_sha256',ROOT),('artifact_sha256',DEST)]:
        for name,digest in ledger[group].items():
            if sha(parent/name)!=digest:raise ValueError('Changed geometry-completion evidence: '+name)
    if old_guard()!=ledger['preserved']:raise ValueError('Changed historical evidence')
    result=read(DEST/'qualification.json')
    if not result['solid_and_hybrid_topology_passed'] or result['coupled_thermal_qualification'] or result['OEM_validation']:
        raise ValueError('Incorrect scope/qualification claim')
    print('Verified new source88-leg solid/hybrid topology and genuine DC evidence; thermal/OEM qualification NOT RUN')


def publish():
    import numpy as np
    import meshio
    if DEST.exists():raise ValueError('Immutable archive exists; use --verify')
    integrity=old_guard();a=read(MESH/'audit.json');e=read(DC/'verification.json');dims=read(MESH/'measured_dimensions.json');views=read(MESH/'view_provenance.json')
    for result in (a,e):
        for name,digest in result['source_sha256'].items():
            if sha(ROOT/name)!=digest:raise ValueError('Changed execution source: '+name)
    if not a['passed'] or not e['passed'] or not all(e['checks'].values()):raise ValueError('Geometry or DC gates failed')
    if a['mesh_sha256']!=sha(MESH/'mesh.npz') or e['full_mesh_sha256']!=a['mesh_sha256']:raise ValueError('Changed actual mesh')
    if e['sif_sha256']!=sha(DC/'case.sif') or e['vtu_sha256']!=sha(DC/e['field_source']):raise ValueError('Changed actual electrical field')
    if e['solver_status']['exit_code']!=0 or not e['solver_executed'] or 'StatCurrentSolver' not in (DC/'solver.log').read_text():raise ValueError('No genuine Elmer DC solve')
    if dims['source_sha256']!=sha(ROOT/'tecooledmct/geometry_complete_measure.py') or dims['mesh_sha256']!=a['mesh_sha256']:raise ValueError('Changed dimensional measurements')
    if views['source_sha256']!=sha(ROOT/'tecooledmct/geometry_complete_views.py') or views['mesh_sha256']!=a['mesh_sha256']:raise ValueError('Changed views')
    for n,digest in read(REGISTRY)['stack_source_sha256'].items():
        if sha(ROOT/'tecooledmct'/n)!=digest:raise ValueError('Changed protected internal template')
    # Reaudit the actual tetrahedra independently of the stored booleans.
    data=np.load(MESH/'mesh.npz');m=read(MESH/'manifest.json')
    fresh=audit(m,*[data[n] for n in ('points','cells','bodies','faces','boundaries','quality')]);w=wire_routes(m)
    if fresh['nodes']!=a['nodes'] or fresh['tetrahedra']!=a['tetrahedra']:raise ValueError('Mesh proof differs')
    field=meshio.read(DC/e['field_source'])
    if not np.isfinite(field.point_data['potential']).all():raise ValueError('Invalid DC field')
    testlog=ROOT/'outputs/geometry-complete-all-tests.log'
    if '114 passed' not in testlog.read_text() or ' failed' in testlog.read_text():raise ValueError('Full regression tests incomplete')
    for name in ('geometry-complete-cli.log','geometry-complete-pellet.log'):
        if 'Traceback' in (ROOT/'outputs'/name).read_text():raise ValueError('CLI/geometry demo failed')
    stage=ROOT/'outputs'/('geometry-complete-publication-'+str(time.time_ns()));stage.mkdir()
    for name in ('mesh.npz','manifest.json','audit.json','wire_routes.json','measured_dimensions.json','view_provenance.json',
                 'source_overlay.png','pin_views.png','actual_stack_mesh.png','return_route_projection.png','gmsh.log','grid.log','grid-status.json'):
        copy(MESH/name,stage/name)
    for name in ('reference.step','geometry_only.vtu'):zipped(MESH/name,stage/(name+'.gz'))
    dc=stage/'electrical'
    for name in ('case.sif','electrical_mesh.npz','verification.json','solver.log','solver-status.json','grid.log','grid-status.json'):copy(DC/name,dc/name)
    for name in (e['field_source'],'derived_current.vtu'):zipped(DC/name,dc/(Path(name).name+'.gz'))
    write(dc/'uncompressed_sha256.json',{Path(n).name:sha(DC/n) for n in (e['field_source'],'derived_current.vtu')})
    copy(testlog,stage/'verification'/testlog.name)
    for name in ('geometry-complete-unit.log','geometry-complete-measurements.log','geometry-complete-views.log',
                 'geometry-complete-cli.log','geometry-complete-pellet.log','geometry-complete-runtime-image.txt','geometry-complete-v4.log'):
        copy(ROOT/'outputs'/name,stage/'verification'/name)
    for label in ('geometry-complete-v2','geometry-complete-v3','geometry-complete-dc-v1','geometry-complete-dc-v2'):
        source=ROOT/'outputs'/label;target=stage/'unaccepted_development'/label
        for path in source.iterdir():
            if path.is_file() and path.suffix in ('.source','.json','.sif','.log'):copy(path,target/path.name)
        if (ROOT/'outputs'/(label+'.log')).exists():copy(ROOT/'outputs'/(label+'.log'),target/'runner.log')
    copy(ROOT/'outputs/geometry-complete-v1.log',stage/'unaccepted_development/endpoint_capsule_false_collision.log')
    write(stage/'independent_reaudit.json',fresh)
    result={'status':'Milestone A solid geometry + explicitly hybrid wiring and DC topology verified',
            'solid_and_hybrid_topology_passed':True,'coupled_thermal_qualification':False,'OEM_validation':False,
            'resolved_3D_wire_arcs':False,'resolved_88leg_module':True,'cap_window_gas_radiation':'not implemented for new geometry; no old operator reused',
            'original_raw_bath_1percent_gate':'unchanged FAILED historical fine points; no new thermal gate result',
            'source_header_mesh_and_module_graph':{'nodes':a['nodes'],'tets':a['tetrahedra'],'domains':a['domains'],'module183_182':True,'hybrid187_186':True},
            'genuine_DC_all175_plus2_cuts':e['checks'],'DC_worst_raw_cut_relative_error':e['worst_raw_cut_relative_error'],
            'signal_pin_current_scope':'structural zero for ideal-insulator hybrid topology; no signal or feedthrough potential PDE solved',
            'image_id':(ROOT/'outputs/geometry-complete-runtime-image.txt').read_text().strip(),
            'execution_resources':'existing network-none Docker4CPU/12GiB; no installation or other session',
            'development_failures_retained':['endpoint spherical capsule too conservative','HXT volume recovery','curvature-disabled interface area failure','SIF body index failure','DC postprocessor field-directory failure']}
    write(stage/'qualification.json',result)
    ledger={'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
            'artifact_sha256':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'preserved':integrity}
    write(stage/'checksums.json',ledger);stage.rename(DEST);verify()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args();verify() if args.verify else publish()
