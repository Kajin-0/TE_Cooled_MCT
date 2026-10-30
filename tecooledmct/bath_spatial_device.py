"""Original coupled gates plus independent signed spatial audit of a NEW field."""
import argparse,json
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .gate_refinement_analysis import analyze
from .bath_spatial_audit import geometry_flux,partitions,outer_edges,signed,PLAN
def verify(mesh,case,out):
    import meshio
    from reports.field_geometry import node_map,cell_map
    if out.exists():raise ValueError('New device-audit label required')
    out.mkdir(parents=True);gates=analyze(mesh,case,out/'gates');e=json.loads((case/'execution.json').read_text());r=json.loads((case/'metrics.json').read_text());m=json.loads((mesh/'manifest.json').read_text());d=np.load(mesh/'mesh.npz')
    p,c,b,f,tags,quality=[d[k] for k in ['points','cells','bodies','faces','boundaries','quality']]
    if sha(mesh/'mesh.npz')!=e['mesh_sha256'] or sha(case/e['field_source'])!=e['vtu_sha256']:raise ValueError('Changed actual device mesh/field')
    field=meshio.read(case/e['field_source']);ix,distance=node_map(p,field.points);cell_map(c,np.argsort(ix)[field.cells_dict['tetra']]);T=field.point_data['temperature'].ravel()[ix];phi=field.point_data['potential'].ravel()[ix]
    data,identity,jumps=geometry_flux(p,c,b,f,tags,T,phi,quality,m)
    if abs(identity['raw_bath_W']-r['hot_out_raw_gradient_w'])>5e-10 or abs(identity['independent_reaction_W']-r['hot_out_reaction_w'])>1e-9:raise ValueError('Independent signed device identity differs')
    nodes=np.unique(f[tags==101]);terr=float(abs(T[nodes]-300).max())
    if terr>1e-8 or abs(data['areas_m2'].sum()-.00033391981702842)>1e-14:raise ValueError('Bath model changed')
    plan=json.loads(PLAN.read_text());pins=np.array([x['center_xy_m'] for x in m['bodies'] if x['kind']=='glass']);segments=outer_edges(p,f[tags==101],plan,pins);groups=partitions(data['centroids_m'],m,segments,plan);rows=[]
    for family,labels in groups.items():
        data['partition_'+family]=labels
        for label in sorted(set(labels)):
            sel=labels==label;rows.append({'family':family,'region':label,'triangles':int(sel.sum()),'area_m2':float(data['areas_m2'][sel].sum()),**signed(data['power_W'][sel])})
    np.savez_compressed(out/'bath_faces.npz',**data);np.savez_compressed(out/'support_faces.npz',**jumps)
    result={'gates':gates,'identity':identity,'signed_bath_powers':signed(data['power_W']),'physical_partitions':rows,
        'bath_maxabs300_error_K':terr,'mesh_sha256':e['mesh_sha256'],'field_sha256':e['vtu_sha256'],'node_map_max_m':distance,
        'source_sha256':{str(x.relative_to(ROOT)):sha(x) for x in [Path(__file__),ROOT/'tecooledmct/bath_spatial_audit.py',PLAN]},
        'scope':'actual new coupled Elmer solution; original raw limits unchanged; signed P1 identity is diagnostic only, no recovery or local physical reference'}
    write(out/'summary.json',result);print('New spatial coupled audit',case.name,'raw bath',gates['bath_relative_error'],'cold',gates['cold_mismatches'],flush=True);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,required=True);p.add_argument('--case',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();verify(a.mesh.resolve(),a.case.resolve(),a.out.resolve())
