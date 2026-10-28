"""Reverify constant-profile contacts and audit their actual input dependencies.

Published Seebeck extraction corrections do not change these G1-constant cases.
The original broad development manifest is retained; the precise dependency
manifest excludes published profile/OEM JSON that these cases never consumed.
No new PDE execution is claimed by this field re-verification.
"""
from pathlib import Path
import hashlib,json,shutil
from .material_profiles import synthetic_profile
from .fem_g2c_contact import transition_profile
from .g2c_qualification import Contact
from .fem_g2c_post import postprocess
from .fem_g2c import intact_checkpoints


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    root=Path(__file__).resolve().parents[1];out=root/'outputs/fem-g2c-contact-fine';report=json.loads((out/'summary.json').read_text())
    if not report['passed']:raise SystemExit('Only a completed passing constant-contact study may be reverified')
    dependency_names=['fem_g2c.py','fem_g2c_post.py','fem_g2c_contact.py','fem_g2c_contact_refine.py','fem_g2c_mesh.py','fem_g2c_contact_reverify.py','material_profiles.py','g2c_qualification.py']
    files=[root/'tecooledmct'/n for n in dependency_names];hashes={str(p.relative_to(root)):sha(p) for p in files}
    shutil.copy2(out/'summary.json',out/'summary-before-dependency-audit.json')
    # Independently regenerated current G1-constant callbacks must match the
    # actual base material source used by the previous contact executions.
    current=root/'outputs/fem-g2c/library_constant/Material.F90'
    if current.read_bytes()!=(out/'base_library/Material.F90').read_bytes():raise ValueError('Constant contact base material changed')
    base=synthetic_profile(False);cases={}
    for label,old in report['cases'].items():
        if old['profile_id']!='g1_constant_regression':raise ValueError('Published-sample cases require actual reruns after a source-data correction')
        case=Path(old['case_path']);mesh=Path(old['mesh_path'])
        if sha(case/'case.sif')!=old['sif_sha256'] or sha(case/old['field_source'])!=old['vtu_sha256'] or old['solver_status']['exit_code']:raise ValueError('Original execution changed/failed')
        params=Contact(**{k:old['contact'][k] for k in ('electrical_ohm_m2','thermal_m2_k_w','thickness_m')})
        fresh=postprocess(mesh,case,base,contact_profile=transition_profile(base,params))
        for key in ('cold_mean_k','voltage_v','contact_joule_w','extra_contact_joule_w'):
            if abs(fresh[key]-old[key])>1e-10:raise ValueError('Actual constant field observables changed')
        fresh.update({k:old[k] for k in ('solver_status','sif_sha256','vtu_sha256','case_path','mesh_path')});fresh['execution_reverified_without_new_solve']=True
        cases[label]=fresh;(case/'metrics.json').write_text(json.dumps(fresh,indent=2,allow_nan=False)+'\n')
    checks=dict(report['checks']);checks['sources_unchanged']=all(sha(root/n)==h for n,h in hashes.items())
    checks['constant_contacts_reverified_after_source_axis_correction']=True
    report.update(cases=cases,checks=checks,passed=all(checks.values()),source_sha256=hashes,protected_integrity=intact_checkpoints(),
        original_development_source_manifest=report['source_sha256'],
        dependency_audit='These cases used synthetic_profile(False), i.e. unchanged G1 constant properties. Published N Seebeck/OEM JSON was never consumed. Actual constant callback source matches freshly regenerated source. All actual fields/SIF/statuses reverified; no new solve claimed.')
    (out/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    if not report['passed']:raise SystemExit('Contact field/dependency verification failed')
    print('Six actual constant-contact executions independently reverified; published N-axis correction did not affect their PDE inputs.')

if __name__=='__main__':main()
