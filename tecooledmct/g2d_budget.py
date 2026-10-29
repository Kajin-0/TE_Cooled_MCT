"""Independent constant-law P1 control-volume budgets from genuine G2d fields."""
import json
import numpy as np
from scipy.spatial import cKDTree
from .g2d_data import ROOT,sha,dump
from .fem_g1 import tetra_geometry
from .fem_g2a import PROPERTIES


def reconstruct(mesh,case):
    import meshio
    r=json.loads((case/'metrics.json').read_text());source=case/r['field_source']
    if sha(source)!=r['vtu_sha256'] or sha(case/'case.sif')!=r['sif_sha256']:raise ValueError('Changed executed fields/SIF')
    m=json.loads((mesh/'manifest.json').read_text());a=np.load(mesh/'mesh.npz');points,cells,bodies=(a[k] for k in ('points','cells','bodies'))
    field=meshio.read(source);dist,mapping=cKDTree(field.points).query(points)
    if dist.max()>1e-12 or len(np.unique(mapping))!=len(points):raise ValueError('VTU/mesh mismatch')
    f={k.lower():v.ravel()[mapping] for k,v in field.point_data.items()};t,phi=f['temperature'],f['potential'];vol,g=tetra_geometry(points,cells)
    by_id={b['id']:b for b in m['bodies']};props=np.array([PROPERTIES[by_id[int(b)]['material']][:3] for b in bodies])
    for p in ('P','N'):
        sel=np.isin(bodies,[b['id'] for b in m['bodies'] if b['material']==p]);props[sel,0]*=r['k_scale'];props[sel,2]*=r['seebeck_scale']
    k,sigma,s=props.T;grad=np.einsum('ei,eij->ej',t[cells],g);electric=-np.einsum('ei,eij->ej',phi[cells],g)
    current=sigma[:,None]*(electric-s[:,None]*grad);heat=-k[:,None]*grad+(t[cells].mean(axis=1)*s)[:,None]*current
    density=np.sum(current*electric,axis=1);work=float(vol@density);interfaces=[]
    for bid in (2,3):
        box=by_id[bid]['box_m'];z=box[2]+.2*box[5];weight=(points[:,2]<=z).astype(float)
        gw=np.einsum('ei,eij->ej',weight[cells],g);up=-float(vol@np.sum(gw*heat,axis=1));below=float(vol@(weight[cells].mean(axis=1)*density))
        interfaces.append({'z_m':z,'upward_weak_w':up,'below_work_w':below,'below_energy_error_w':r['hot_out_w']+up-below})
    flows=[-r['hot_out_w'],*(v['upward_weak_w'] for v in interfaces),-r['load_w']]
    cumulative=[0.,*(v['below_work_w'] for v in interfaces),work];budgets=[]
    for i in range(3):
        hot,cold=-flows[i],-flows[i+1];power=cumulative[i+1]-cumulative[i]
        budgets.append({'stage':i,'hot_out_w':hot,'cold_absorbed_w':cold,'electrical_work_w':power,'energy_error_w':hot-cold-power})
    plates=[]
    for b in m['bodies']:
        if b['kind']!='ceramic':continue
        sel=bodies==b['id'];v=vol[sel];tt=t[cells[sel]]
        plates.append({'name':b['name'],'mean_k':float(v@tt.mean(axis=1)/v.sum()),'min_k':float(tt.min()),'max_k':float(tt.max())})
    checks={'matches_independent_postprocessor_work':abs(work-r['volume_j_dot_e_w'])<1e-10,
        'all_stage_energy_errors_below_1uW':all(abs(b['energy_error_w'])<1e-6 for b in budgets),
        'interfaces_below_1uW':all(abs(b['below_energy_error_w'])<1e-6 for b in interfaces)}
    return {'passed':all(checks.values()),'checks':checks,'stages':budgets,'interfaces':interfaces,'plates':plates,
        'scope':'P1 nodal control volumes through shared plates, including intersected routing and dielectric; not isolated leg textbook stages. Actual phi/T, no imposed intermediate temperatures.',
        'sif_sha256':r['sif_sha256'],'vtu_sha256':r['vtu_sha256'],'postprocessor_sha256':sha(ROOT/'tecooledmct/g2d_budget.py')}


def main():
    out=ROOT/'outputs/fem-g2d';s=json.loads((out/'summary.json').read_text())
    if not s['passed']:raise SystemExit('Only verified actual fields')
    results={k:reconstruct(out/'mesh',out/k) for k in s['cases']}
    dump(out/'budgets.json',results)
    if not all(r['passed'] for r in results.values()):raise SystemExit('Stage heat budget failure')
    print(json.dumps({k:r['checks'] for k,r in results.items()},indent=2))

if __name__=='__main__':main()
