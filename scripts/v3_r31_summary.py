"""Summarize measured local cases and author an UNEXECUTED prospective plan."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v3_r31_local_mesh_20261103'
R3 = ROOT/'data/v3_analysis_r3_20261103'


def read(path):
    return json.loads(path.read_text())


def main():
    out = DATA/'summary.json'
    assert not out.exists()
    inv = read(DATA/'inventory.json')
    reg = read(R3/'audit_v2/registry.json')
    plan = read(R3/'surface/surface_0/size_plan.json')
    cases = {}
    for path in sorted((DATA/'cases').glob('*/resources.json')):
        q = read(path)
        worker = path.parent/'worker/result.json'
        if worker.exists():
            result = read(worker)
            q.update(worker_status=result['status'], phases=result['phases'],
                triangles=result.get('triangles'), nodes=result.get('nodes'),
                max_area_error=result.get('max_area_error'), worker_wall_seconds=result['wall_seconds'],
                callback=result['callback'], API_profile=result['API_profile'], error=result.get('error'))
        else:
            result = read(path.parent/'worker/progress.json')
            q.update(worker_status='STOP180s; censored', callback=result['callback'], phases=result['phases'])
        cases[path.parent.name] = q
    comparisons = {}
    for fixture in inv['groups']:
        a = cases['A_callback_all__'+fixture]
        b = cases['B_native_all__'+fixture]
        s = cases['B_native_selective__'+fixture]
        value = dict(A_to_native_all_end_to_end_ratio=a['wall_seconds']/b['wall_seconds'],
            A_ratio_type='LOWER BOUND censored A' if a['timeout'] else 'MEASURED LOCAL',
            native_all_to_selective_end_to_end_ratio=b['wall_seconds']/s['wall_seconds'],
            native_all_accepted=b['worker_status'].startswith('PASS'),
            native_selective_accepted=s['worker_status'].startswith('PASS'),
            not_a_global_speedup=True)
        comparisons[fixture] = value
    corrected = cases['C_directional_corrected__detector_bonds']
    comparisons['detector_bonds'].update(
        censored_A_to_corrected_C_end_to_end_lower_bound=180/corrected['wall_seconds'],
        rejected_native_all_to_C_triangle_ratio=cases['B_native_all__detector_bonds']['triangles']/corrected['triangles'],
        rejected_native_selective_to_C_triangle_ratio=cases['B_native_selective__detector_bonds']['triangles']/corrected['triangles'])
    mismatch = []
    for f in inv['groups']['detector_bonds']:
        q = inv['faces'][str(f)]
        for edge, c in q['curves'].items():
            n = plan['shared_edge_counts'][edge]
            mismatch.append(dict(face=f, curve=int(edge), type=c['type'], length_mm=c['length_mm'],
                original_segments=n, face_target_h_mm=plan['face_h_mm'][str(f)],
                average_segment_mm=c['length_mm']/n,
                segment_to_face_h=c['length_mm']/n/plan['face_h_mm'][str(f)]))
    summary = dict(status='MEASURED LOCAL EVIDENCE ONLY; GLOBAL NOT RUN', cases=cases,
        comparisons=comparisons, boundary_size_mismatch=mismatch,
        accepted_cases=sum(q['worker_status'].startswith('PASS') for q in cases.values()),
        rejected_or_censored_cases=sum(not q['worker_status'].startswith('PASS') for q in cases.values()),
        C_leads_jackets='NOT RUN after original C STOP; not replayed',
        no_global_mesh=True, no_PDE=True, original_source_bodies=824, original_contacts=378,
        actual_local_face_coverage=54, no_global_speedup_prediction=True)
    out.write_text(json.dumps(summary, indent=2)+'\n')
    corrected_result = read(DATA/'cases/C_directional_corrected__detector_bonds/worker/result.json')
    directional = set(map(int, corrected_result['directional_patches']))
    # A future operator, never invoked here: exact tested bond patches only.
    prospective = dict(status='PROPOSED UNEXECUTED GLOBAL ALGORITHM; SEPARATE AUTHORIZATION REQUIRED',
        source_BREP_SHA256=hashlib.sha256((R3/'geometry_restored/R3_conformal_mm.brep').read_bytes()).hexdigest(),
        source_registry_SHA256=hashlib.sha256((R3/'audit_v2/registry.json').read_bytes()).hexdigest(),
        domains=430, faces=2440, source_bodies=824, finite_contacts=378,
        all_laws='UNSET', global_trial_executed=False, source_geometry_changes=False,
        native_operator='Cached face h; MathEval/Restrict/Min, IncludeBoundary=1; selective curved/quad constraints',
        directional_operator='v3_r31_worker_v2.seed_periodic; exact source boundary IDs and UV; native seam IDs shared',
        directional_faces=sorted(directional),
        fixed_directional_counts='ceil(length/80um or turning_angle/(pi/24));48 interior circumferential divisions',
        scheduling='1D source curves first; seed approved periodic faces; MeshOnlyEmpty native2D on remainder',
        gates='Every native face and complete R2 ancestor strictly<1%; ownership, edge incidence, no missing faces',
        unbenchmarked_global_faces=2440-54,
        global_runtime_or_triangle_prediction='NOT AVAILABLE',
        global_hard_budget='MUST BE PREREGISTERED UNDER A FUTURE AUTHORIZATION',
        face_plan={str(f): dict(method='SOURCE_BOUNDARY_UV_DIRECTIONAL' if f in directional else 'NATIVE_RESTRICT',
            h_mm=plan['face_h_mm'][str(f)], owners=q['owners'], owner_volume_ids=q['owner_volume_ids'],
            local_evidence='BENCHMARKED LOCAL FAMILY' if str(f) in inv['faces'] else 'NOT BENCHMARKED')
            for f, q in ((int(k), q) for k, q in reg['face_registry'].items())})
    (DATA/'prospective_global_algorithm_NOT_RUN.json').write_text(json.dumps(prospective, indent=2)+'\n')
    print('Accepted local cases',summary['accepted_cases'],'rejected/censored',summary['rejected_or_censored_cases'])
    for fixture, values in comparisons.items():
        print(fixture, values)


if __name__ == '__main__':
    main()
