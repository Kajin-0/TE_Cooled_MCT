"""Real G2c stage/Thomson qualification, with fail-closed source coverage."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from .fem_g1_run import execute
from .fem_g2a import generate_mesh,Stage
from .fem_g2a_post import postprocess as constant_post
from .fem_g2b_physics import execute_solver
from .material_profiles import load_profile,synthetic_profile,Profile,Curve
from .fem_g2c import intact_checkpoints,compile_profile,write_case
from .fem_g2c_post import postprocess
from .g2c_qualification import Contact,holdout_compare


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def rod_mesh(out,size):
    import gmsh,meshio
    out.mkdir(parents=True,exist_ok=True);gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0)
        v=gmsh.model.occ.addBox(0,0,0,.4e-3,.4e-3,1e-3);gmsh.model.occ.synchronize();gmsh.model.addPhysicalGroup(3,[v],1)
        groups={101:[],102:[],105:[]}
        for _,s in gmsh.model.getEntities(2):
            z=gmsh.model.occ.getCenterOfMass(2,s)[2];groups[101 if abs(z)<1e-12 else 102 if abs(z-1e-3)<1e-12 else 105].append(s)
        for tag,ss in groups.items():gmsh.model.addPhysicalGroup(2,ss,tag)
        gmsh.option.setNumber('Mesh.MeshSizeMax',size);gmsh.option.setNumber('Mesh.MeshSizeMin',size);gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
        gmsh.model.mesh.generate(3);gmsh.write(str(out/'stage.msh'))
    finally:gmsh.finalize()
    m=meshio.read(out/'stage.msh');cells=m.cells_dict['tetra'];faces=m.cells_dict['triangle'];tags=m.cell_data_dict['gmsh:physical']['triangle'];aliases=np.concatenate([faces[tags==101],faces[tags==102]])
    np.savez_compressed(out/'mesh.npz',points=m.points,cells=cells,bodies=np.ones(len(cells),int),faces=np.concatenate([faces,aliases]),
        boundaries=np.concatenate([tags,np.full(sum(tags==101),103),np.full(sum(tags==102),104)]))
    manifest={'config':{'couples':1},'bodies':[{'id':1,'name':'manufactured_P_rod','material':'P','kind':'leg','cut_axis':2,'cut_coordinate_m':.000500013,'current_sign':1,'cut_area_m2':.4e-3**2}],
        'cold_area_m2':.4e-3**2,'terminal_planes':{'103':{'area_m2':.4e-3**2}}}
    save(out/'manifest.json',manifest)
    execute(['ElmerGrid','14','2','stage.msh','-out','elmer'],out,'grid')
    from .fem_g2c_mesh import verify_elmer_tetra_mapping
    save(out/'audit.json',verify_elmer_tetra_mapping(out))


def solve(out,label,mesh,profile,library,current=.05,load=.002,freeze=None,hot=295.,cold=None,rod=False,stack=False):
    case=out/label;write_case(case,mesh,profile,library,current,load,freeze,hot,cold,stack)
    if rod:
        sif=(case/'case.sif').read_text()
        # Elmer selects one BC list per physical boundary. Merge both physical
        # conditions in that list instead of duplicating target boundary IDs.
        import re
        sif=re.sub(r'Boundary Condition [34]\n.*?\nEnd\n','',sif,flags=re.S)
        sif=sif.replace('Target Boundaries(1) = 101\n',f'Target Boundaries(1) = 101\n  Electric Flux = Real {current/(.4e-3**2):.16g}\n')
        sif=sif.replace('Target Boundaries(1) = 102\n','Target Boundaries(1) = 102\n  Potential = Real 0\n')
        (case/'case.sif').write_text(sif)
    status=execute_solver(case)
    r=postprocess(mesh,case,profile,freeze,label in ('source_3','fine','thomson_rod'));r.update(solver_status=status,sif_sha256=sha(case/'case.sif'),vtu_sha256=sha(case/r['field_source']),mesh_path=str(mesh),case_path=str(case))
    save(case/'metrics.json',r)
    print(f'{label}: Tc={r["cold_mean_k"]:.7f} V={r["voltage_v"]:.9g} energy={r["energy_relative_residual"]:.3g} cut={r["max_cut_relative_error"]}',flush=True)
    return r


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=Path('outputs/fem-g2c'));parser.add_argument('--stage-only',action='store_true');args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    sources={str(p.relative_to(root)):sha(p) for p in [*root.glob('tecooledmct/*g2c*.py'),root/'tecooledmct/material_profiles.py',*root.glob('data/g2c/*.json'),*root.glob('tests/test_*g2c*.py'),root/'tests/test_material_profiles.py']}
    protected=intact_checkpoints();source=load_profile();constant=synthetic_profile(False);synthetic=synthetic_profile(True)
    libs={k:compile_profile(out/('library_'+k),p) for k,p in [('source',source),('constant',constant),('synthetic',synthetic)]}
    frozen=compile_profile(out/'library_source_frozen',source,300.)
    cases={};audits=[]
    for i,size in enumerate((.22e-3,.12e-3,.08e-3,.06e-3)):
        mesh=out/f'mesh_{i}';audit=generate_mesh(mesh,size,Stage());audits.append(audit)
        execute(['ElmerGrid','14','2','stage.msh','-out','elmer'],mesh,'grid')
        from .fem_g2c_mesh import verify_elmer_tetra_mapping
        audit['elmer_tetra_mapping']=verify_elmer_tetra_mapping(mesh)
        save(mesh/'audit.json',audit)
        cases[f'source_{i}']=solve(out,f'source_{i}',mesh,source,libs['source'])
    fine=out/'mesh_3'
    cases['constant_regression']=solve(out,'constant_regression',fine,constant,libs['constant'])
    prior=constant_post(fine,out/'constant_regression')
    save(out/'constant_regression'/'metrics.json',cases['constant_regression'])
    cases['source_frozen_300']=solve(out,'source_frozen_300',fine,source,frozen,freeze=300.)
    cases['synthetic_variable']=solve(out,'synthetic_variable',fine,synthetic,libs['synthetic'])
    checks={'all_mesh_audits_pass':all(a['passed'] for a in audits),
        'constant_temperature_regression':abs(prior['cold_mean_k']-cases['constant_regression']['cold_mean_k'])<1e-8,
        'constant_voltage_regression':abs(prior['voltage_v']-cases['constant_regression']['voltage_v'])<1e-10,
        'source_cold_mesh_change_below_1pct_lift':abs(cases['source_0']['cold_mean_k']-cases['source_3']['cold_mean_k'])/(295-cases['source_3']['cold_mean_k'])<.01,
        'local_source_temperature_changes_solution':abs(cases['source_3']['cold_mean_k']-cases['source_frozen_300']['cold_mean_k'])>1e-3}
    if not args.stage_only:
        # A genuinely three-dimensional solve whose exact continuum solution is 1D.
        # Synthetic linear S with nonzero slope; k and rho held constant.
        curves={p:dict(cs) for p,cs in constant.curves.items()};curves['P']['S']=Curve((200.,300.),(60e-6,160e-6),'V/K')
        thomson=Profile({'id':'synthetic_Thomson_manufactured_rod','status':'SYNTHETIC FUNCTION TEST ONLY'},curves)
        lib=compile_profile(out/'library_thomson',thomson);mesh=out/'rod_mesh';rod_mesh(mesh,.04e-3)
        cases['thomson_rod']=solve(out,'thomson_rod',mesh,thomson,lib,.1,0,hot=295.,cold=285.,rod=True)
        # Independent nonlinear continuum BVP with k T'' = J T S' T' - J^2/sigma.
        from scipy.integrate import solve_bvp
        import meshio
        j=.1/(.4e-3**2);k=1.5;sigma=140000.;slope=1e-6
        z=np.linspace(0,.001,101)
        ref=solve_bvp(lambda z,y:np.vstack([y[1],(j*slope*y[0]*y[1]-j*j/sigma)/k]),lambda a,b:np.array([a[0]-295,b[0]-285]),z,np.vstack([295-10000*z,np.full_like(z,-10000)]),tol=1e-9)
        if not ref.success:raise RuntimeError('Independent Thomson BVP failed')
        field=meshio.read(out/'thomson_rod'/cases['thomson_rod']['field_source']);values={n.lower():v.ravel() for n,v in field.point_data.items()}
        err=float(np.max(np.abs(values['temperature']-ref.sol(field.points[:,2])[0])))
        voltage=j*.001/sigma-140e-6*(285-295)+.5*slope*(285**2-295**2)
        flat=295-10000*z+j*j/(2*k*sigma)*z*(.001-z)
        cases['thomson_rod']['analytic']={'max_nodal_temperature_error_k':err,'voltage_v':voltage,'voltage_error_v':abs(cases['thomson_rod']['voltage_v']-voltage),
            'nonzero_thomson_effect_vs_constant_S_k':float(np.max(np.abs(ref.sol(z)[0]-flat))), 'bvp_status':int(ref.status),'equation':"k*T''=J*T*dS/dT*T'-J^2/sigma",'thomson_S_slope_v_k2':slope}
        checks.update(thomson_continuum_temperature_below_5mK=err<.005,thomson_continuum_voltage_below_2uV=abs(cases['thomson_rod']['voltage_v']-voltage)<2e-6,
            thomson_not_omitted=cases['thomson_rod']['analytic']['nonzero_thomson_effect_vs_constant_S_k']>.01)
    for label,r in cases.items():
        checks[label+'_actual_solver_zero_exit']=r['solver_status']['exit_code']==0
        checks[label+'_material_range']=r['actual_material_interval_passed']
        checks[label+'_energy_work']=max(abs(r['energy_relative_residual']),abs(r['power_work_relative_residual']))<.01
        checks[label+'_current']=r['current_absolute_error_a']<1e-6
    checks['fine_source_component_currents_below_half_pct']=cases['source_3']['max_cut_relative_error']<.005
    checks['fine_source_bath_energy_below_1pct']=abs(cases['source_3']['bath_gradient_energy_relative_residual'])<.01
    checks['source_hashes_unchanged']=all(sha(root/n)==h for n,h in sources.items())
    baseline=json.loads((root/'fem/results/g2b_two_terminal_20261028/summary.json').read_text())['cases']['zero_load_positive']
    compare=holdout_compare([{'current_a':.1,'load_w':0.,'delta_t_k':300-baseline['cold_mean_k'],'voltage_v':baseline['voltage_v'],'origin':'preserved actual constant G2b zero_load_positive, a7a8991 source/evidence lineage'}])
    checks={k:bool(v) for k,v in checks.items()}
    result={'schema_version':1,'source_sha256':sources,'protected_integrity':protected,'verification':{'passed':all(checks.values()),'checks':checks},'cases':cases,'mesh_audits':audits,'oem_comparison':compare,
        'contact_plan':Contact(1e-9,1e-5).layer_parameters(.4e-3**2),'qualification':{'literature_material_adapter':'VERIFIED' if all(checks.values()) else 'FAILED',
        'oem_grade_match':'NOT QUALIFIED','four_couple_interface_solver':'NOT EXECUTED','oem_family_validation':'NOT QUALIFIED','full_stack_source_profile':'NOT EXECUTED IN THIS RUN; coverage gate required'}}
    save(out/'summary.json',result)
    print(json.dumps(result['verification'],indent=2),flush=True)
    if not all(checks.values()):raise SystemExit('G2c numerical qualification checks failed')

if __name__=='__main__':main()
