"""Collect actual normal-volume studies with explicit cross-mesh region proofs."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import ROOT,sha,write
from .cold20_analysis import accepted_nonraw
RAW=ROOT/'outputs/gate-refinement'
def read(p):return json.loads(p.read_text())
def canonical(c):
    c=np.sort(c,axis=1);return c[np.lexsort(c.T[::-1])]
def same_region(a,z,bodies):
    """Compare actual body tetrahedra across different appended-node numbering."""
    ix=cKDTree(z['points']).query(a['points'])[1]
    for bid in bodies:
        ac=a['cells'][a['bodies']==bid];zc=z['cells'][z['bodies']==bid]
        if not len(ac) or not len(zc):return False
        if not np.allclose(a['points'][np.unique(ac)],z['points'][ix[np.unique(ac)]],atol=1e-13,rtol=0):return False
        if not np.array_equal(canonical(ix[ac]),canonical(zc)):return False
    return True
def collect():
    trials={};primary=read(ROOT/'fem/results/cold20_completion_20261030/cases/loaded20_refined_replay/metrics.json')
    for label in ['cold1','bath2','bath3','combined']:
        case=RAW/(label+'_case')
        if not case.exists():continue
        mesh=RAW/(label+'_mesh');proof=read(mesh/'audit.json');e=read(case/'execution.json') if (case/'execution.json').exists() else None
        row={'completed':False,'mesh_sha256':sha(mesh/'mesh.npz'),'geometry_passed':proof['passed'],'status':read(case/'solver-status.json')}
        if e:
            accepted_nonraw(case);a=read(RAW/(label+'_audit')/'summary.json')
            if a['mesh_sha256']!=e['mesh_sha256'] or a['field_sha256']!=e['vtu_sha256'] or a['source_sha256']!=sha(ROOT/'tecooledmct/gate_refinement_analysis.py'):raise ValueError('Stale actual-field audit')
            row.update(completed=True,all_nonraw_gates_passed=True,cold_mismatches=a['cold_mismatches'],bath_relative_error=a['bath_relative_error'],
                die_delta_from_initial_K=a['die_mean_K']-primary['die_mean_k'],voltage_delta_from_initial_V=a['voltage_V']-primary['voltage_v'],
                same_case_raw_gates_passed=a['same_case_raw_gates_passed'])
        trials[label]=row
    combined_proof=None
    if trials.get('combined',{}).get('completed'):
        cold=np.load(RAW/'cold1_mesh/mesh.npz');mix=np.load(RAW/'combined_mesh/mesh.npz');hot=np.load(RAW/'bath3_mesh/mesh.npz')
        combined_proof={'cold_tets_match_independent_cold1_up_to_node_numbering':same_region(cold,mix,[4,302,303]),
            'bath_tets_match_independent_bath3_up_to_node_numbering':same_region(hot,mix,[300,*range(401,410),*range(501,510)])}
        if not all(combined_proof.values()):raise ValueError('Combined mesh does not retain actual independent refined regions')
    result={'trials':trials,'combined_region_proof':combined_proof,'full_numerical_release':False,'passing_refined_combined_comparator':False,
        'combined_decision':'not run: both independent bath levels fail the unchanged1% gate' if 'combined' not in trials else 'actual trial retained; no release without refined passing comparator',
        'OEM_validated':False,'whole_device_GCI_qualified':False,'original_failed_bath_criteria':'UNCHANGED FAILED; no retroactive relabeling',
        'old15_page_report':'UNCHANGED','source_sha256':sha(Path(__file__)),
        'scope':'actual independent cold-normal and bath-normal volume studies; same-case raw pass alone is not release',
        'gates':{'cold':.05,'bath':.01,'current_cuts':.005,'heat_W':1e-6,'current_A':1e-6,'nonlinear':1e-9}}
    write(RAW/'summary.json',result);return result
if __name__=='__main__':collect()
