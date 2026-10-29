"""Read only immutable FEM archives; verify provenance and actual solved arrays."""
import gzip,hashlib,json,tempfile
from pathlib import Path
import numpy as np
from .field_geometry import node_map,cell_map

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'fem/results/g3b_checkpoint_20261029'
BASELINE='52b30c0f4f92580394fb7b51bcd95a56ebd5d2e4'
CASE='nitrogen_patch1'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())


def verify_baseline():
    from tecooledmct.fem_g3b_data import preserve
    prior=preserve();ledger=read(ARCHIVE/'checksums.json');checked=0
    for section,base in [('source_sha256',ROOT),('document_sha256',ROOT),('artifact_sha256',ARCHIVE)]:
        for name,digest in ledger[section].items():
            if sha(base/name)!=digest:raise ValueError('Baseline changed: '+name)
            checked+=1
    if ledger['full_g3b_qualified'] or ledger['unique_package_solver_executions']!=10:raise ValueError('Unexpected qualification scope')
    return {'passed':True,'g1_through_g3a':prior,'g3b_entries_checked':checked,'g3b_ledger_sha256':sha(ARCHIVE/'checksums.json'),'baseline_commit':BASELINE}


def load_fields(cache):
    import meshio
    from tecooledmct.fem_g1 import tetra_geometry
    from tecooledmct.fem_g3b_reference import material_properties
    integrity=verify_baseline();operator=ARCHIVE/'operators/operator_h0p1';data=np.load(operator/'mesh.npz');m=read(operator/'manifest.json');r=read(ARCHIVE/'cases'/CASE/'metrics.json');ex=read(ARCHIVE/'cases'/CASE/'execution.json')
    if not r['passed'] or not all(r['checks'].values()) or ex['solver_status']['exit_code']:raise ValueError('Report case is unaccepted')
    if sha(operator/'mesh.npz')!=ex['mesh_sha256']:raise ValueError('Wrong actual execution mesh')
    p,c,b,f,tags=[data[k] for k in ('points','cells','bodies','faces','boundaries')];expected=read(ARCHIVE/'fields'/CASE/'uncompressed_sha256.json');fields={};hashes={}
    cache.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        for name in ('fields_t0001.vtu','derived.vtu'):
            path=Path(tmp)/name;compressed=ARCHIVE/'fields'/CASE/(name+'.gz')
            with gzip.open(compressed,'rb') as inp,path.open('wb') as out:
                import shutil
                shutil.copyfileobj(inp,out)
            if sha(path)!=expected[name]:raise ValueError('Decompressed actual field hash differs')
            fields[name]=meshio.read(path);hashes[name]={'uncompressed_sha256':expected[name],'compressed_sha256':sha(compressed)}
    raw,derived=fields['fields_t0001.vtu'],fields['derived.vtu'];ir,dr=node_map(p,raw.points);idv,dd=node_map(p,derived.points)
    temp=np.asarray(raw.point_data['temperature']).ravel()[ir];phi=np.asarray(raw.point_data['potential']).ravel()[ir]
    if not np.isfinite(temp).all() or not np.isfinite(phi).all():raise ValueError('Nonfinite solved fields')
    np.testing.assert_allclose(temp,derived.point_data['Temperature_K'][idv],atol=1e-10,rtol=0);np.testing.assert_allclose(phi,derived.point_data['Potential_V'][idv],atol=1e-12,rtol=0)
    raw_inverse=np.empty(len(p),dtype=int);raw_inverse[ir]=np.arange(len(p));raw_tetra=np.concatenate([x.data for x in raw.cells if x.type=='tetra']);raw_mapping=cell_map(c,raw_inverse[raw_tetra])
    if 'GeometryIds' in raw.cell_data:
        raw_bodies=np.concatenate([v for block,v in zip(raw.cells,raw.cell_data['GeometryIds']) if block.type=='tetra'])[raw_mapping]
        if not np.array_equal(raw_bodies,b):raise ValueError('Raw VTU material/body mapping differs')
    inverse=np.empty(len(p),dtype=int);inverse[idv]=np.arange(len(p));dt=np.concatenate([x.data for x in derived.cells if x.type=='tetra']);mapping=cell_map(c,inverse[dt])
    cell={k:np.concatenate([v for block,v in zip(derived.cells,values) if block.type=='tetra'])[mapping] for k,values in derived.cell_data.items()}
    if not np.array_equal(cell['body_id'],b):raise ValueError('Derived body mapping differs')
    # Independently reconstruct mean J and q from raw T/phi, using audited laws.
    volume,gradient=tetra_geometry(p,c);gt=np.einsum('ei,eij->ej',temp[c],gradient);electric=-np.einsum('ei,eij->ej',phi[c],gradient);j=np.empty_like(gt);q=np.empty_like(gt)
    for body in m['bodies']:
        sel=b==body['id'];kn,sn,an=material_properties(body['material'],temp[c[sel]],r['package_sigma_s_m'],r['attach_k_scale'],r['mount_k_scale']);k=kn.mean(1);sigma=sn.mean(1);alpha=an.mean(1);j[sel]=sigma[:,None]*(electric[sel]-alpha[:,None]*gt[sel]);q[sel]=-k[:,None]*gt[sel]+(temp[c[sel]].mean(1)*alpha)[:,None]*j[sel]
    errors={}
    for name,actual in [('J_A_m2',j),('q_W_m2',q)]:
        errors[name]=float(np.max(np.linalg.norm(actual-cell[name],axis=1)/(1+np.linalg.norm(cell[name],axis=1))))
        if errors[name]>1e-8:raise ValueError('Archived derived vector does not match raw field: '+name)
    values={}
    for label in ('MCT_x029','ceramic_3'):
        bid=next(x['id'] for x in m['bodies'] if x['name']==label);sel=b==bid;values[label]=float(volume[sel]@temp[c[sel]].mean(1)/volume[sel].sum())
    if abs(values['MCT_x029']-r['die_mean_k'])>1e-8 or abs(values['ceramic_3']-r['cold_ceramic_k'])>1e-8:raise ValueError('Volume means do not reproduce archived metrics')
    x=p[f];area=np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1)/2
    def avg(tag):
        sel=tags==tag;return float(area[sel]@phi[f[sel]].mean(1)/area[sel].sum())
    voltage=avg(103)-avg(104)
    if abs(voltage-r['voltage_v'])>1e-11:raise ValueError('Terminal voltage differs')
    audit={'passed':True,'integrity':integrity,'case':CASE,'mesh_sha256':sha(operator/'mesh.npz'),'fields':hashes,'raw_node_mapping_max_m':dr,'derived_node_mapping_max_m':dd,'derived_vectors_normalized_max_error':errors,'volume_means_k':values,'terminal_voltage_v':voltage,'nodes':len(p),'tetrahedra':len(c),'domains':len(np.unique(b)),'solver_executed_by_report':False}
    return {'points':p,'cells':c,'bodies':b,'faces':f,'tags':tags,'temperature':temp,'potential':phi,'J':cell['J_A_m2'],'q':cell['q_W_m2'],'manifest':m,'metrics':r,'audit':audit}
