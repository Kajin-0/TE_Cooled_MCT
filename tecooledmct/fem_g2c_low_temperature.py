"""Actual 190--200 K four-couple source-profile adapter check, not OEM prediction."""
from pathlib import Path
import json,hashlib
from .material_profiles import DATA,load_profile
from .fem_g2c import compile_profile,intact_checkpoints
from .fem_g2c_run import solve,save,sha
from .fem_g2a import generate_mesh
from .fem_g1_run import execute
from .fem_g2c_mesh import verify_elmer_tetra_mapping


def main():
    root=Path(__file__).resolve().parents[1];out=root/'outputs/fem-g2c-low-temperature';out.mkdir(exist_ok=True)
    paths=[*root.glob('tecooledmct/*g2c*.py'),root/'tecooledmct/material_profiles.py',*root.glob('data/g2c/*.json'),root/'tests/test_material_profiles_low.py']
    hashes={str(f.relative_to(root)):sha(f) for f in paths};profile=load_profile(DATA/'zhang2025_he_40_300_v2.json');protected=intact_checkpoints()
    mesh=out/'mesh';audit=generate_mesh(mesh,.12e-3);execute(['ElmerGrid','14','2','stage.msh','-out','elmer'],mesh,'grid');audit['elmer_tetra_mapping']=verify_elmer_tetra_mapping(mesh);save(mesh/'audit.json',audit)
    lib=compile_profile(out/'library',profile);r=solve(out,'source_low_temperature',mesh,profile,lib,.02,0.,hot=200.,cold=190.)
    checks={'real_Elmer_exit_zero':r['solver_status']['exit_code']==0,'actual_local_T_in_40_300K_source_interval':r['actual_material_interval_passed'],
        'actual_BiTe_below_200K_exercised':min(v[0] for v in r['profile_body_temperature_ranges_k'].values())<195,
        'all_15_currents_below_0p5pct':len(r['cuts'])==15 and r['max_cut_relative_error']<.005,
        'global_energy_and_work_below_1pct':max(abs(r['energy_relative_residual']),abs(r['power_work_relative_residual']))<.01,
        'sources_unchanged':all(sha(root/n)==h for n,h in hashes.items())}
    checks={k:bool(v) for k,v in checks.items()};result={'passed':all(checks.values()),'checks':checks,'cases':{'source_low_temperature':r},'source_sha256':hashes,'mesh_audits':[audit],'protected_integrity':protected,
        'scope':'200 K / 190 K fixed ceramic faces, +0.02 A; local source interpolation genuinely exercised below 200 K. Not a predicted device cold temperature or an OEM fit.'}
    save(out/'summary.json',result);print(json.dumps(checks,indent=2),flush=True)
    if not result['passed']:raise SystemExit('Low-temperature numerical qualification FAILED')

if __name__=='__main__':main()
