"""Independent archived-field bath flux/reaction localization, not a new solve."""
import argparse, csv, gzip, json, tempfile
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from .g2d_data import ROOT, sha, dump
from .flux_presolder_common import affine_geometry, boundary_owners, outward_vectors, guard, node_map, cell_map

ARCHIVE = ROOT/'fem/results/g3b_checkpoint_20261029'
CASES = [('nitrogen_patch1','operator_h0p1'), ('nitrogen_fine_verified','operator_h1'),
         ('nitrogen_bath','operator_bath'), ('nitrogen_feedthrough','operator_feedthrough')]


def residual_identity(p,c,faces,tags,support,q,vol,work,bath_nodes):
    """Discrete integration by parts: expose jumps and other exterior flux.

    This identity checks assembly/signs, not independent continuum accuracy.
    w is the P1 indicator of bath nodes, zero at every other global node.
    """
    local=c[support];ff=np.concatenate([np.delete(local,i,axis=1) for i in range(4)])
    owners=np.tile(np.arange(len(support)),4)
    av=outward_vectors(p,local,ff,owners)
    indicator=np.zeros(len(p));indicator[bath_nodes]=1
    trace=indicator[ff].mean(1);power=np.einsum('ij,ij->i',q[owners],av)*trace
    keys=np.sort(ff,axis=1);_,inverse,counts=np.unique(keys,axis=0,return_inverse=True,return_counts=True)
    interior=counts[inverse]==2
    exterior_set={tuple(sorted(row)) for row,tag in zip(faces,tags) if tag<1000}
    bath_set={tuple(sorted(row)) for row,tag in zip(faces,tags) if tag==101}
    is_bath=np.zeros(len(ff),bool);other=np.zeros(len(ff),bool)
    for i in np.flatnonzero(~interior & (trace>0)):
        key=tuple(keys[i])
        if key not in exterior_set:raise ValueError('Incomplete nodal support for residual identity')
        if key in bath_set:is_bath[i]=True
        else:other[i]=True
    return {'raw_bath_out_w':float(power[is_bath].sum()),
            'other_exterior_weighted_raw_out_w':float(power[other].sum()),
            'internal_face_weighted_jump_w':float(power[interior].sum()),
            'weighted_electrical_volume_work_w':float(vol@(work*indicator[local].mean(1))),
            'identity':'reaction_out = raw_bath_out + other_exterior_weighted_raw_out + internal_face_weighted_jump + weighted_electrical_volume_work; sources at bath nodes are zero',
            'scope':'Exact discrete P1 integration-by-parts check, not a recovered flux or an independent physical reference'}


def partition(centres, owner_material, registry):
    """Disjoint physical regions, with empty non-bath material regions explicit."""
    regions = np.full(len(centres), 'distant_Kovar_bulk', dtype=object)
    pins = np.array(registry['feedthroughs']['centers_xy_m'])
    dist = np.linalg.norm(centres[:,None,:2]-pins[None,:,:],axis=2)
    for i in range(9):
        regions[(dist[:,i]<.0011)&(owner_material=='Kovar')] = f'seal_adjacent_Kovar_{i}'
        regions[(dist[:,i]<.0011)&(owner_material=='Glass')] = f'glass_annulus_{i}'
        regions[(dist[:,i]<.0011)&(owner_material=='Pin')] = f'pin_root_{i}'
    unused = regions=='distant_Kovar_bulk'
    regions[unused&(abs(centres[:,0])<=.0032)&(abs(centres[:,1])<=.0032)] = 'mount_footprint'
    header=registry['header']
    for i,x in enumerate(header['mount_hole_centers_x_m']):
        near=np.linalg.norm(centres[:,:2]-[x,0],axis=1)<header['mount_hole_radius_m']+.0006
        regions[(regions=='distant_Kovar_bulk')&near] = f'mount_hole_edge_{i}'
    a,bb=header['ellipse_semiaxes_m']
    edge=(centres[:,0]/a)**2+(centres[:,1]/bb)**2>.90**2
    regions[(regions=='distant_Kovar_bulk')&edge] = 'outer_flange_edge'
    names=['distant_Kovar_bulk','mount_footprint','outer_flange_edge','mount_hole_edge_0','mount_hole_edge_1']
    names += [f'{kind}_{i}' for i in range(9) for kind in ('seal_adjacent_Kovar','glass_annulus','pin_root')]
    return regions,names


def diagnose(label, operator, out):
    import meshio
    base=ARCHIVE/('cases' if label=='nitrogen_patch1' else 'unaccepted_development')/label
    r=json.loads((base/'metrics.json').read_text()); mesh=ARCHIVE/'operators'/operator
    d=np.load(mesh/'mesh.npz');p,c,b,f,tags=[d[k] for k in ('points','cells','bodies','faces','boundaries')]
    manifest=json.loads((mesh/'manifest.json').read_text());registry=manifest['package_registry']
    fields=ARCHIVE/'fields'/label if label=='nitrogen_patch1' else base
    source=fields/'fields_t0001.vtu.gz'
    cache=ROOT/'outputs/flux_presolder_cache';cache.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        raw=Path(tmp)/'fields.vtu'
        with gzip.open(source,'rb') as stream,raw.open('wb') as target:
            import shutil
            shutil.copyfileobj(stream,target)
        expected=json.loads((fields/'uncompressed_sha256.json').read_text())['fields_t0001.vtu']
        if sha(raw)!=expected:raise ValueError('Actual archived field changed')
        field=meshio.read(raw)
    index,distance=node_map(p,field.points);inverse=np.empty(len(p),int);inverse[index]=np.arange(len(p))
    ft=np.concatenate([x.data for x in field.cells if x.type=='tetra']);cell_map(c,inverse[ft])
    temp=np.asarray(field.point_data['temperature']).ravel()[index];phi=np.asarray(field.point_data['potential']).ravel()[index]
    if not np.isfinite(temp).all() or not np.isfinite(phi).all():raise ValueError('Nonfinite actual field')
    bath=f[tags==101];nodes=np.unique(bath);support=np.flatnonzero(np.isin(c,nodes).any(1))
    by={body['id']:body for body in manifest['bodies']}
    material=np.array([by[int(v)]['material'] for v in b[support]])
    if not set(material)<=set(('Kovar','Glass','Pin')):raise ValueError('Unexpected bath-node material/source support')
    # This bath star contains no detector source or thermoelectric Seebeck term.
    weights=load_npz(mesh/'weights.npz')
    if weights[:,nodes].nnz:raise ValueError('Nonlocal source at bath nodes requires explicit reconstruction')
    k=np.array([{'Kovar':17.3,'Glass':1.,'Pin':17.3}[v] for v in material])
    vol,g=affine_geometry(p,c[support]);gt=np.einsum('ei,eij->ej',temp[c[support]],g);gp=np.einsum('ei,eij->ej',phi[c[support]],g)
    q=-k[:,None]*gt;work=r['package_sigma_s_m']*np.sum(gp*gp,axis=1)
    rt=np.zeros(len(p));local=vol[:,None]*(k[:,None]*np.einsum('eij,ej->ei',g,gt)-work[:,None]/4)
    np.add.at(rt,c[support].ravel(),local.ravel())
    owners=boundary_owners(c,bath);lookup=np.full(len(c),-1,int);lookup[support]=np.arange(len(support))
    av=outward_vectors(p,c,bath,owners);areas=np.linalg.norm(av,axis=1);centres=p[bath].mean(1)
    if np.max(abs(av[:,:2]))>1e-18 or np.any(av[:,2]>=0) or np.ptp(centres[:,2])>1e-12:raise ValueError('Bath normal/tag/plane defect')
    direct=np.einsum('ij,ij->i',q[lookup[owners]],av)
    # Area-partition the actual nodal reaction without double counting boundary nodes.
    nodal_area=np.zeros(len(p));np.add.at(nodal_area,bath.ravel(),np.repeat(areas/3,3))
    weak=np.sum((-rt[bath])*areas[:,None]/(3*nodal_area[bath]),axis=1)
    identity=residual_identity(p,c,f,tags,support,q,vol,work,nodes)
    terms=[identity[k] for k in ('raw_bath_out_w','other_exterior_weighted_raw_out_w','internal_face_weighted_jump_w','weighted_electrical_volume_work_w')]
    identity['closure_error_w']=float(weak.sum()-sum(terms))
    if abs(identity['closure_error_w'])>1e-10:raise ValueError('Independent discrete residual identity failed')
    def face_mean(tag):
        faces=f[tags==tag];x=p[faces];a=np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1)/2
        return float(a@phi[faces].mean(1)/a.sum())
    current=r['current_a'];voltage=face_mean(103)-face_mean(104);lead=registry['supply_leads']
    lead_joule=lead['count']*current**2*lead['rho_ohm_m']*lead['length_m']/(np.pi*(lead['diameter_m']/2)**2)*r['lead_scale']
    external=current*voltage+r['pbias_w']+r['poptical_thermal_w']+lead_joule
    if abs(float(direct.sum())-r['hot_out_direct_w'])>1e-9 or abs(float(weak.sum())-r['hot_out_reaction_w'])>1e-9 or abs(external-r['external_total_power_w'])>1e-10:raise ValueError('Independent flux/reaction/input reproduction failed')
    materials=np.array([by[int(v)]['material'] for v in b[owners]])
    region,names=partition(centres,materials,registry);rows=[]
    for name in names:
        mask=region==name;delta=float((direct[mask]-weak[mask]).sum())
        rows.append({'region':name,'faces':int(mask.sum()),'area_m2':float(areas[mask].sum()),'direct_out_w':float(direct[mask].sum()),'allocated_reaction_out_w':float(weak[mask].sum()),'direct_minus_reaction_w':delta,'signed_error_over_external_input':delta/external})
    target=out/label;target.mkdir(parents=True,exist_ok=True)
    with (target/'regions.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    np.savez_compressed(target/'bath_faces.npz',centres_m=centres,area_m2=areas,direct_out_w=direct,reaction_allocated_w=weak,regions=region.astype(str))
    result={'case':label,'solver_executed':False,'source_accepted':bool(r['passed']),'mesh_sha256':sha(mesh/'mesh.npz'),'compressed_vtu_sha256':sha(source),'vtu_sha256':expected,'node_mapping_max_m':distance,'bath_materials':sorted(set(materials)),'bath_area_m2':float(areas.sum()),'direct_out_w':float(direct.sum()),'reaction_out_w':float(weak.sum()),'external_input_w':external,'direct_error_w':float(direct.sum()-external),'direct_relative_error':float((direct.sum()-external)/external),'reaction_error_w':float(weak.sum()-external),'gate':.01,'original_raw_gate_passed':bool(abs(direct.sum()/external-1)<.01),'regions':rows,'reaction_partition':'P1 boundary nodal reactions distributed to incident bath triangles by area/3; descriptive allocation, not exact local continuum flux','normal_check':'all outward -z, actual one-sided tetrahedral owners, only Kovar underside','source_check':'bath nodal support Kovar/glass/pin only, S=0, no detector or nonlocal source support; tiny sigma electrical work retained'}
    result['discrete_residual_identity']=identity
    dump(target/'diagnosis.json',result)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,4));v=(direct-weak)/areas;lim=max(abs(v));pic=ax.scatter(centres[:,0]*1e3,centres[:,1]*1e3,c=v,s=4,cmap='coolwarm',vmin=-lim,vmax=lim);ax.set(xlabel='x (mm)',ylabel='y (mm)',title=label+': raw flux minus allocated FE reaction');ax.set_aspect('equal');fig.colorbar(pic,ax=ax,label='Local difference (W/m²)');fig.tight_layout();fig.savefig(target/'localization.png',dpi=250);plt.close(fig)
    print(label,'raw error %',100*result['direct_relative_error'],'weak error W',result['reaction_error_w'],flush=True)
    return result


def main(out):
    out.mkdir(parents=True,exist_ok=False);integrity=guard()
    import shutil
    sources=[Path(__file__),ROOT/'tecooledmct/flux_presolder_common.py']
    hashes={str(path.relative_to(ROOT)):sha(path) for path in sources}
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for path in sources:shutil.copy2(path,snapshot/path.name)
    results=[diagnose(label,op,out) for label,op in CASES]
    if any(sha(ROOT/name)!=value for name,value in hashes.items()):raise ValueError('Diagnostic source changed')
    dump(out/'summary.json',{'diagnostics_verified':True,'full_package_qualified':False,'diagnostic_source_sha256':hashes,'baseline_integrity':integrity,'cases':results})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'outputs/flux-presolder-diagnosis');args=parser.parse_args();main(args.out.resolve())
