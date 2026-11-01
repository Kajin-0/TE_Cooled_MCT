"""Read-only validation of the single unaccepted cap export; no author/retry.

The failed producer is preserved only as a forensic snapshot, not an active
export command. No Boolean, gas mesh or transport solution is constructed.
"""
import argparse
from pathlib import Path
import time

import numpy as np

from .native_gas_audit import ROOT,CAP,PACKAGE,read,write,sha,step_units,import_record
from .corrected_enclosure import assumptions
from .exchange_geometry import verify_sources

NOTE=ROOT/'docs/UNIT_CORRECT_CAP_AND_NATIVE_GAS_20261101.md'


def classify_physical_scale(rows,expected):
    if len(rows)!=len(expected) or len(rows)!=3:raise ValueError('Missing or extra cap solid')
    ratios=np.sort([r['volume_m3'] for r in rows])/np.sort(list(expected.values()))
    if np.any(~np.isfinite(ratios)) or np.any(ratios<=0):raise ValueError('Invalid imported volumes')
    length=np.cbrt(ratios)
    return {'volume_ratios_to_intended':ratios.tolist(),'length_ratios_from_volumes':length.tolist(),
        'physical_scale_qualified':bool(np.allclose(ratios,1.,rtol=1e-8,atol=0.)),
        'uniform_scale_error':bool(np.allclose(length,length[0],rtol=1e-8,atol=0.))}


def run(folder):
    start=time.monotonic();folder=Path(folder);candidate=folder/'cap_window_unit_correct.step';cube=folder/'one_mm_cube.step'
    result_path=folder.parent/'phase_A_validation.json'
    if result_path.exists():raise ValueError('Do not overwrite validation evidence')
    inputs=verify_sources();a=assumptions();candidate_sha=sha(candidate);cube_sha=sha(cube)
    parsed=step_units(candidate.read_text());parsed_cube=step_units(cube.read_text())
    import gmsh
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
    try:
        cube_rows=import_record(gmsh,cube)
        if parsed_cube['metres_per_coordinate_unit']!=1e-3 or len(cube_rows)!=1 or not np.isclose(cube_rows[0]['volume_m3'],1e-9,rtol=1e-8):
            raise ValueError('Independent analytic cube reader check failed')
        rows=import_record(gmsh,candidate);version=gmsh.__version__
    finally:gmsh.finalize()
    scale=classify_physical_scale(rows,a['expected_solid_volumes_m3'])
    ro=max(parsed['cylinder_radii_declared_m']);bbox=np.array([r['bbox_m'] for r in rows])
    low=bbox[:,:3].min(0);high=bbox[:,3:].max(0)
    if sha(candidate)!=candidate_sha or sha(cube)!=cube_sha:raise ValueError('Validation mutated its inputs')
    result={'status':'PHASE A FAILED; source artifact unchanged; candidate explicitly UNACCEPTED',
        'registration':NOTE.read_text().split('## Results')[0],
        'geometry_authoring_attempts':1,'additional_exports_in_validation':0,
        'gmsh_version':version,'reader_target_unit':'M','cube_control':{'parsed':parsed_cube,'imported':cube_rows,'passed':True},
        'candidate_parsed_units':parsed,'candidate_imported_solids':rows,'scale_check':scale,
        'intended_outer_radius_m':a['outer_radius_m'],'candidate_outer_radius_m':ro,
        'outer_radius_ratio_to_intended':ro/a['outer_radius_m'],
        'candidate_bbox_m':{'low':low,'high':high,'kernel_padding_note':'Bounding boxes include 1e-7 m padding'},
        'intended_header_top_m':a['header_top_z_m'],'candidate_foot_minus_header_m':float(low[2]-a['header_top_z_m']),
        'source_original_bad_STEP_sha256':sha(CAP/'corrected_cap_window.step'),'candidate_STEP_sha256':candidate_sha,
        'candidate_classification':'Quarantined failed authoring output; NOT a unit-correct derivative or gas assembly input',
        'verified_observation':'Attempt authored numerical mm dimensions after a metre-target import; exported STEP values acquired another factor 1000. Resetting OCCTargetUnit to empty did not restore the assumed writer context in this run.',
        'root_cause_scope':'Exporter unit-state assumption in new code, not a newly established contradiction in the registered physical assembly',
        'next_implementation':'Isolate authoring/export in a fresh process that performs no SI imports; author both mm cube and mm cap before a separate metre-target reader process. Independently validate units, radii, datums, volumes and seals before Phase B. Not executed under the one-attempt stop.',
        'phase_A_qualified':False,'valid_derivative_published':False,
        'phase_B':{'status':'NOT RUN','Boolean_void_extractions':0,'gas_cells':0,'boundary_qualification':None},
        'phase_C':{'status':'NOT RUN','gas_PDE_solves':0,'gas_heat_budgets_w':None,'temperature_field':None},
        'comparative_fields_read':False,'source_geometry_or_laws_changed':False,'Rev3_modified':False,
        'source_sha256':{n:sha(ROOT/n) for n in ('tecooledmct/cap_export_validation.py','tecooledmct/corrected_enclosure.py','tecooledmct/native_gas_audit.py')},
        'input_sha256':inputs,'failed_author_snapshot_sha256':sha(folder/'author.py.snapshot'),
        'elapsed_seconds':time.monotonic()-start}
    if scale['physical_scale_qualified']:raise RuntimeError('Failure diagnosis not confirmed; do not report an assumed stop')
    write(result_path,result)
    artifacts={str(p.relative_to(folder.parent)):sha(p) for p in sorted(folder.parent.rglob('*')) if p.is_file()}
    write(folder.parent/'checksums.json',{'artifact_sha256':artifacts})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--attempt',type=Path,required=True);args=p.parse_args()
    r=run(args.attempt);print(r['status'],r['scale_check'])
