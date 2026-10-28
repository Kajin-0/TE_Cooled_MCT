"""Bounded source-backed 88-leg runs on independently re-audited G2b meshes.

295 K bath stays inside the measured 200--300 K profile interval. This is NOT
an OEM 300 K panel comparison; no extrapolated or grade-matched claim.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
import numpy as np
from .material_profiles import DATA,load_profile
from .fem_g2c import compile_profile,intact_checkpoints
from .fem_g2c_run import solve,sha,save
from .fem_g1_run import execute
from .fem_g2b_connected import audit_mesh
from .fem_g2b_connectivity import connectivity


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=Path('outputs/fem-g2c-stack'));args=p.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parents[1]
    paths=[*root.glob('tecooledmct/*g2c*.py'),root/'tecooledmct/material_profiles.py',*root.glob('data/g2c/*.json'),*root.glob('tests/test_*g2c*.py')]
    hashes={str(f.relative_to(root)):sha(f) for f in paths};protected=intact_checkpoints();profile=load_profile(DATA/'zhang2025_he_40_300_v2.json');lib=compile_profile(out/'library',profile)
    prior=root/'fem/results/g2b_two_terminal_20261028';index=json.loads((prior/'checksums.json').read_text());audits=[];cases={}
    for label,i in (('coarse',0),('fine',2)):
        source=prior/'meshes'/f'mesh_{i}';mesh=out/('mesh_'+label);mesh.mkdir(exist_ok=True)
        expected=index['artifacts_sha256'][f'meshes/mesh_{i}/mesh.npz']
        if sha(source/'mesh.npz')!=expected:raise ValueError('Original mesh no longer matches protected evidence')
        for name in ('mesh.npz','manifest.json'):shutil.copy2(source/name,mesh/name)
        m=json.loads((mesh/'manifest.json').read_text());d=np.load(mesh/'mesh.npz')
        if (source/'connected.msh').exists():shutil.copy2(source/'connected.msh',mesh/'connected.msh')
        else:
            import meshio
            meshio.write(mesh/'connected.msh',meshio.Mesh(d['points'],[('tetra',d['cells']),('triangle',d['faces'])],cell_data={
                'gmsh:physical':[d['bodies'],d['boundaries']],'gmsh:geometrical':[d['bodies'],d['boundaries']]}),file_format='gmsh22',binary=False)
        import gmsh
        gmsh.initialize()
        try:
            gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(mesh/'connected.msh'));_,tt,_=gmsh.model.mesh.getElements(3)
            quality=np.concatenate([gmsh.model.mesh.getElementQualities(t,'minSICN') for t in tt])
        finally:gmsh.finalize()
        a=audit_mesh(m,*(d[k] for k in ('points','cells','bodies','faces','boundaries')),quality)
        a['actual_tetra_connectivity']=connectivity(d['cells'],d['bodies'],{b['id'] for b in m['bodies'] if b['material']!='Alumina'})
        a.update(mesh_npz_sha256=sha(mesh/'mesh.npz'),gmsh_mesh_sha256=sha(mesh/'connected.msh'));save(mesh/'audit.json',a);audits.append(a)
        execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],mesh,'grid')
        from .fem_g2c_mesh import verify_elmer_tetra_mapping
        a['elmer_tetra_mapping']=verify_elmer_tetra_mapping(mesh);save(mesh/'audit.json',a)
        cases[label]=solve(out,label,mesh,profile,lib,.1,0,hot=295.,stack=True)
    c,f=cases['coarse'],cases['fine'];checks={
        'two_meshes_actual_audit':all(a['passed'] for a in audits),
        'all_actual_solver_exits_zero':all(r['solver_status']['exit_code']==0 for r in cases.values()),
        'all_actual_local_temperatures_in_source_range':all(r['actual_material_interval_passed'] for r in cases.values()),
        'cold_mesh_change_below_1pct_lift':abs(f['cold_mean_k']-c['cold_mean_k'])/(295-f['cold_mean_k'])<.01,
        'voltage_mesh_change_below_1pct':abs(f['voltage_v']/c['voltage_v']-1)<.01,
        'fine_all_175_currents_below_0p5pct':len(f['cuts'])==175 and f['max_cut_relative_error']<.005,
        'fine_direct_bath_energy_below_1pct':abs(f['bath_gradient_energy_relative_residual'])<.01,
        'global_energy_work':all(max(abs(r['energy_relative_residual']),abs(r['power_work_relative_residual']))<.01 for r in cases.values()),
        'positive_current_cools_consumes_power':f['cold_mean_k']<295 and f['electrical_input_w']>0,
        'source_hashes_unchanged':all(sha(root/n)==h for n,h in hashes.items())}
    checks={k:bool(v) for k,v in checks.items()}
    result={'passed':all(checks.values()),'checks':checks,'source_sha256':hashes,'protected_integrity':protected,'cases':cases,'audits':audits,
        'status':'Numerical source-profile test, 295 K bath, no OEM comparison at mismatched conditions','contact_status':'ideal interfaces, separate stage transition model tested independently'}
    save(out/'summary.json',result);print(json.dumps(checks,indent=2),flush=True)
    if not result['passed']:raise SystemExit('Source-backed full-stack numerical gates FAILED')

if __name__=='__main__':main()
