import json,os
from pathlib import Path
import pytest
from tecooledmct.fem_g2a import audit_boxes
from tecooledmct.fem_g2c_contact import manifest,transition_profile
from tecooledmct.g2c_qualification import Contact
from tecooledmct.material_profiles import synthetic_profile


def test_explicit_transition_domains_keep_zero_limit_and_single_path():
    m=manifest();audit_boxes(m)
    assert len([b for b in m['bodies'] if b['kind']=='contact_layer'])==16
    assert m['graph']['unique_path'] and m['graph']['nodes']==33
    base=synthetic_profile(False);zero=transition_profile(base,Contact())
    for p in ('P','N'):
        for key in ('k','sigma','S'):assert zero.properties(p,280)[key]==pytest.approx(base.properties(p,280)[key])
    finite=transition_profile(base,Contact(1e-9,1e-5,20e-6))
    assert finite.properties('P',280)['rho']-base.properties('P',280)['rho']==pytest.approx(1e-9/20e-6)
    assert 1/finite.properties('P',280)['k']-1/base.properties('P',280)['k']==pytest.approx(1e-5/20e-6)


@pytest.mark.skipif(os.environ.get('TE_FEM_SMOKE')!='1',reason='requires real Elmer/Gmsh and compiled local-T material functions')
def test_real_local_temperature_adapter_and_runtime_guard(tmp_path):
    from tecooledmct.fem_g2a import generate_mesh
    from tecooledmct.fem_g1_run import execute
    from tecooledmct.fem_g2c import compile_profile,write_case
    from tecooledmct.fem_g2b_physics import execute_solver
    from tecooledmct.fem_g2c_post import postprocess
    from tecooledmct.material_profiles import load_profile
    mesh=tmp_path/'mesh';generate_mesh(mesh,.12e-3);execute(['ElmerGrid','14','2','stage.msh','-out','elmer'],mesh,'grid')
    profile=load_profile();lib=compile_profile(tmp_path/'library',profile)
    case=tmp_path/'case';write_case(case,mesh,profile,lib,hot=295.)
    assert execute_solver(case)['exit_code']==0
    r=postprocess(mesh,case,profile)
    assert r['actual_material_interval_passed'] and abs(r['energy_relative_residual'])<1e-5
    assert r['max_cut_relative_error']<.005
    bad=tmp_path/'rejected';write_case(bad,mesh,profile,lib,hot=295.)
    text=(bad/'case.sif').read_text().replace('Temperature = Real 295','Temperature = Real 301')
    (bad/'case.sif').write_text(text)
    with pytest.raises(RuntimeError):execute_solver(bad)
    status=json.loads((bad/'solver-status.json').read_text());assert status['exit_code']!=0
    assert 'extrapolation refused' in (bad/'solver.log').read_text()
