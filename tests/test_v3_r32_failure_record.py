"""Read-only failure/provenance controls. Never recreates the global mesh."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from tecooledmct.v3_r32_surface_integrity import DIRECTIONAL_FACES,validate_mesh_evidence

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_r32_global_surface_20261103'


def load(name):return json.loads((DATA/name).read_text())


def test_exactly_one_worker_and_honest_unqualified_stop():
    execution=load('execution_receipt.json');result=load('run/result.json')
    assert execution['run']==load('global_run_slot.json')['run_number']==1
    assert execution['wall_seconds']<600 and execution['peak_child_RSS_MiB']<8192
    assert result['status']=='STOP GLOBAL WORKER; NO RETRY'
    assert result['error']=="ValueError('Native fill altered directional seed')"
    assert set(map(int,result['directional_patches']))==DIRECTIONAL_FACES
    assert 'triangles' not in result and not list((DATA/'run').glob('*.msh'))
    assert 'all_face_ancestor_topology_quality_normal_validation' not in result['phases']
    assert not result['PDE_RUN'] and not result['volume_mesh_RUN']
    assert load('failure_inspection.json')['actual_global_triangle_count'] is None
    with pytest.raises((ValueError,KeyError)):validate_mesh_evidence(result)


def test_numeric_tag_guard_can_fail_without_any_geometric_change():
    # Execute the exact frozen guard body with an API stub, not Gmsh/meshing.
    text=(ROOT/'scripts/v3_r32_worker.py').read_text();tree=ast.parse(text)
    function=next(q for q in tree.body if isinstance(q,ast.FunctionDef) and q.name=='face_mesh_hash')
    ids=np.array([10,11],np.int64);nodes=np.array([1,2,3,1,3,4],np.int64)
    values=[np.array([2],np.int32),[ids],[nodes]]
    stub=SimpleNamespace(model=SimpleNamespace(mesh=SimpleNamespace(getElements=lambda dim,tag:values)))
    namespace=dict(np=np,hashlib=hashlib,gmsh=stub)
    exec(compile(ast.Module(body=[function],type_ignores=[]),'frozen_guard','exec'),namespace)
    original=namespace['face_mesh_hash'](1)
    values[1]=[ids+100]
    renumbered=namespace['face_mesh_hash'](1)
    assert original!=renumbered
    # Same triangle connectivity, coordinates and face; only element names differ.
    assert np.array_equal(values[2][0],nodes)


def test_operator_and_input_hashes_still_match_pre_run_seal():
    r=load('registration.json')
    for key in ('sources_sha256','inputs_sha256'):
        for name,h in r[key].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
    assert hashlib.sha256((DATA/'executed_source/preregistered_method.md').read_bytes()).hexdigest()==r['method_document_sha256']
    manifest=load('release_manifest.json')
    assert manifest['status']=='VERIFIED FAILURE EVIDENCE; GLOBAL SURFACE STOP'
    assert manifest['attempts']==1 and manifest['actual_global_triangles'] is None
    assert not manifest['mesh_qualified'] and not manifest['MSH_preserved']
    for name,h in manifest['files_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name


def test_no_hidden_second_global_or_volume_invocation():
    tree=ast.parse((ROOT/'scripts/v3_r32_worker.py').read_text())
    dimensions=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='generate':
            dimensions.append(n.args[0].value)
    assert sorted(dimensions)==[1,2]
    assert load('global_run_slot.json')['NO_RETRY']
    assert not load('failure_inspection.json')['complete_MSH_preserved']
