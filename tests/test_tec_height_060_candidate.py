"""Actual source solid construction and conservative contact controls; no PDE."""
import copy,json,math
from pathlib import Path
import pytest
from tecooledmct.tec_height_060_candidate import build
from tecooledmct.tec_assembly_v3_audit import audit
from scripts.tec_height_060_contact_audit import audit as rectangle_audit
ROOT=Path(__file__).resolve().parents[1]
SRC=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
OUT=json.loads((ROOT/'data/tec_height_060_cad_20261110/source_candidate/design.json').read_text())

def test_saved_reproducible_actual_geometry_and_identity():
 d,changed=build(SRC)
 assert d==OUT and len(d['bodies'])==824 and len(changed)==556
 for old,new in zip(SRC['bodies'],d['bodies']):
  assert (old['id'],old['name'],old['material'],old['group'])==(new['id'],new['name'],new['material'],new['group'])
 assert d['legs']==SRC['legs']

def test_independent_352_rectangular_interfaces():
 a=rectangle_audit(OUT)
 assert a['leg_solder_contacts']==a['solder_gold_contacts']==176
 assert a['minimum_leg_solder_area_mm2']==pytest.approx(.16)
 assert a['minimum_solder_gold_area_mm2']==pytest.approx(.16)
 assert a['foot_counts']=={58:2,80:2,88:3}

def test_source_graph_contact_ownership_and_box_exclusivity():
 a=audit(OUT)
 assert a['P_N_contacts']==176 and a['net_count']==89 and a['metal_components']==98
 # a['tolerances'] is a hard-coded baseline table; do not claim taller design validation.

def test_wrong_joint_alignment_is_rejected():
 d=copy.deepcopy(OUT);b=next(x for x in d['bodies'] if x['name']=='solder0_cold');b['boxes_mm'][0][2]+=.01
 with pytest.raises(AssertionError):rectangle_audit(d)

def test_missing_solder_metal_area_is_rejected():
 d=copy.deepcopy(OUT);c=next(c for c in d['explicit_contacts'] if c['scope']=='PN_metal');b=next(b for b in d['bodies'] if b['name']==c['b'])
 for q in b['boxes_mm']:q[0]+=5
 with pytest.raises(AssertionError):rectangle_audit(d)

def test_original_and_custom_plane_locations_and_bond_paths():
 by={x['name']:x for x in OUT['bodies']};old={x['name']:x for x in SRC['bodies']}
 for j in range(4):assert by[f'ceramic{j}']['boxes_mm'][0][2]-old[f'ceramic{j}']['boxes_mm'][0][2]==pytest.approx(j*.1)
 for n in (7,8):
  p=by[f'detector_bond{n}']['points'];q=old[f'detector_bond{n}']['points']
  assert [p[k][2]-q[k][2] for k in range(4)]==pytest.approx([.3,.3,.3,0])
 for n,delta in ((58,.1),(80,.1),(88,.2)):
  a=by[f'formed_tab{n}'];b=old[f'formed_tab{n}'];assert sum(x['length'] for x in a['parts'])-sum(x['length'] for x in b['parts'])==pytest.approx(delta)
 assert by['pin1']['radius']==by['pin9']['radius']==pytest.approx(.38)

def test_clearance_lower_bounds_and_negative_controls():
 from scripts.tec_height_060_clearance_audit import audit as check
 a=check(OUT)
 assert a['radial_shell_clearance_lower_bound_mm']>0 and a['roof_clearance_lower_bound_mm']>0
 assert a['unrelated_pin_wire_pair_count']==48 and a['min_unrelated_pin_wire_clearance_lower_bound_mm']>0
 assert a['min_interleg_gap_per_stage_mm']==pytest.approx([.18,.18,.18])
 q=copy.deepcopy(OUT);next(b for b in q['bodies'] if b['name']=='cap_shell')['inner_radius']=6.
 with pytest.raises(AssertionError):check(q)
 q=copy.deepcopy(OUT);l=next(b for b in q['bodies'] if b['name']=='leg1_P');l['boxes_mm'][0][0]-=.10
 with pytest.raises(AssertionError):check(q)

def test_actual_step_independent_si_and_boundary_audits():
 import hashlib
 d=ROOT/'data/tec_height_060_cad_20261110';reader=json.loads((d/'cad_attempt01/si_reader.json').read_text());auth=json.loads((d/'cad_attempt01/writer.json').read_text());brep=json.loads((d/'imported_contact_audit_attempt01.json').read_text())
 step=d/'cad_attempt01/synthetic_v3_mm.step';digest=hashlib.sha256(step.read_bytes()).hexdigest()
 assert reader['status']=='PASS separate SI import' and reader['body_count']==824
 assert reader['cube_volume_m3']==pytest.approx(1e-9,rel=1e-7)
 assert reader['max_relative_volume_error']<=1e-7 and reader['max_bbox_error_m']<=2.1e-7
 assert digest==reader['STEP_sha256']==auth['STEP_sha256']==brep['SI_STEP_sha256']
 assert brep['status']=='PASS imported boundary witnesses and curved-body exclusivity'
 assert brep['independent_contacts']==923 and brep['curved_overlap_pairs']==58
 assert all(x['volume_mm3']<=1e-12 for x in brep['overlap_tests'])
