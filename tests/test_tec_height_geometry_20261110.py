"""Source-only controls: these do not qualify a candidate assembly."""
import copy,json,math
from pathlib import Path
import pytest
from scripts.tec_height_geometry_audit_20261110 import build
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
P=ROOT/'data/tec_height_geometry_20261110'
def test_two_height_analytic_contact_and_volume_controls():
 a,b=build(D,.5),build(D,.6)
 assert a['nominal_leg_contact_pairs']==b['nominal_leg_contact_pairs']==176
 assert b['core_stack_height_mm']==pytest.approx(4.1)
 assert b['die_to_window_mm']==pytest.approx(a['die_to_window_mm']-.3)
 assert b['pn_volume_mm3']-a['pn_volume_mm3']==pytest.approx(1.408)
 assert b['pn_side_area_mm2']-a['pn_side_area_mm2']==pytest.approx(14.08)
 assert b['min_adjacent_pitch_gap_mm']==pytest.approx(.18)
 assert a['naive_bond_bend_gate']=='PASS' and b['naive_bond_bend_gate'].startswith('FAIL')
 assert [r['candidate_z0_mm']-q['candidate_z0_mm'] for q,r in zip(a['plate_rows'],b['plate_rows'])]==pytest.approx([0,.1,.2,.3])
 for row in b['legs']:
  assert row['leg_z1_mm']-row['leg_z0_mm']==pytest.approx(.6)
  assert row['leg_z0_mm']==pytest.approx(row['hot_solder_z1_mm'])
  assert row['leg_z1_mm']==pytest.approx(row['cold_solder_z0_mm'])
  assert row['nominal_contact_area_mm2']==pytest.approx(.16)
def test_wrong_source_joint_rejected():
 bad=copy.deepcopy(D)
 next(b for b in bad['bodies'] if b['name']=='solder0_cold')['boxes_mm'][0][2]+=.01
 with pytest.raises(AssertionError):build(bad,.6)
def test_candidate_tabs_absolute_z_and_bond_rebuild():
 proposal=json.loads((P/'formed_paths_proposal.json').read_text())
 for tab in proposal['tabs']:
  old=next(b for b in D['bodies'] if b['name']==tab['name'])['points']
  levels=sorted(set(round(p[1],9) for p in old))
  for before,after in zip(old,tab['points']):
   idx=min(range(len(levels)),key=lambda i:abs(before[1]-levels[i]))
   expected=(.1 if tab['name']=='formed_tab80' else 0)+.1*idx
   assert after[1]-before[1]==pytest.approx(expected)
 for bond in proposal['detector_bonds']:
  assert bond['naive_preserved_apex'].startswith('FAIL') and bond['proposed_apex_mm']==pytest.approx(6.45)
  assert bond['clearance_contact_and_cad']=='NOT CHECKED'
def test_geometry_is_explicitly_not_promoted():
 d=json.loads((P/'analytic_coordinate_proposal.json').read_text())
 assert d['full_system_solves']==0 and 'STOP' in d['status']
 for c in d['cases'].values():
  assert c['full_cad_geometry']=='NOT RUN' and c['full_system_solve']=='NOT RUN'

def test_source_series_registry_and_missing_joint():
 from scripts.tec_height_series_audit_20261110 import verify
 a=verify(D)
 assert a['source_leg_solder_contacts']==a['source_solder_metal_contacts']==176
 q=copy.deepcopy(D);q['explicit_contacts']=[c for c in q['explicit_contacts'] if not(c['a']=='leg0_N' and c['b']=='solder0_hot')]
 with pytest.raises((AssertionError,KeyError)):verify(q)
 q=copy.deepcopy(D);next(b for b in q['bodies'] if b['name']=='solder0_hot')['group']=88
 with pytest.raises(AssertionError):verify(q)
