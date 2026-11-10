"""Conditional geometry-to-solver mapping and conservative reduced operators."""
import copy,json
import numpy as np
import pytest
from tecooledmct import height_coupling_v320 as h
from scripts.v3_4_source_copper_multiport import SPEC,evaluate,PORTS

def test_source_faces_translated_with_candidate_ownership():
 m=h.mapping();assert len(m['faces'])==95 and len(m['leg_faces'])==176
 assert m['plate_shifts_mm']==pytest.approx([0,.1,.2,.3])
 for x in m['faces'].values():
  assert x['candidate_face_tag'].startswith('NOT ASSIGNED')
  assert np.allclose(np.array(x['candidate_center_mm'])-x['original_center_mm'],[0,0,x['translated_z_mm']],atol=1e-10)

def test_faulty_candidate_face_shift_is_rejected(tmp_path,monkeypatch):
 d=h.read(h.CANDIDATE);next(b for b in d['bodies'] if b['name']=='ceramic2')['boxes_mm'][0][2]+=.01
 p=tmp_path/'bad.json';p.write_text(json.dumps(d));monkeypatch.setattr(h,'CANDIDATE',p)
 with pytest.raises(AssertionError):h.mapping()

def test_tet_stiffness_translation_invariant():
 t=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],float)*1e-3
 def K(p):
  D=np.stack((p[1]-p[0],p[2]-p[0],p[3]-p[0]),axis=-1);v=np.linalg.det(D)/6;g=np.empty((4,3));g[1:]=np.linalg.inv(D);g[0]=-g[1:].sum(axis=0);return v*g@g.T
 assert np.allclose(K(t),K(t+[0,0,.0003]),rtol=1e-12,atol=1e-15)

def test_copper_nominal_replay_and_correct_middle_electrical_contact():
 s=h.copper_specs(h.read(h.ORIGINAL));c=h.copper_specs(h.read(h.CANDIDATE));temps={t:300.-j*5 for j,t in enumerate(sorted({t for v in PORTS.values() for t in v}))}
 for n in s:
  assert s[n]['segments_m']==pytest.approx(SPEC[n]['segments_m'],abs=1e-15)
  assert np.array(c[n]['segments_m'])-s[n]['segments_m']==pytest.approx([.0001]*len(s[n]['segments_m']),abs=1e-15)
 expected=evaluate(.4,temps);legacy=h.copper_eval(s,.4,temps,legacy_middle_electric=True)
 assert legacy['total_electrical_R_ohm']==pytest.approx(expected['total_electrical_R_ohm'],abs=1e-14)
 assert list(legacy['heat_into_face_W'].values())==pytest.approx(list(expected['heat_into_face_W'].values()),abs=1e-13)
 corrected=h.copper_eval(s,.4,temps)
 assert corrected['net_details']['88']['contact_electrical_R_ohm'][1]==0
 assert corrected['net_details']['88']['face_heat_into_ceramic_W'][1]!=0
 assert sum(corrected['heat_into_face_W'].values())==pytest.approx(corrected['total_electrical_power_W'],abs=1e-12)

def test_copper_thermal_symmetry_passivity_and_zero_controls():
 spec=h.copper_specs(h.read(h.CANDIDATE));tags=sorted({t for p in PORTS.values() for t in p});T0={t:280. for t in tags};z=h.copper_eval(spec,0,T0)
 assert max(abs(x) for x in z['heat_into_face_W'].values())<1e-12
 columns=[]
 for t in tags:
  T=dict(T0);T[t]+=1.;q=h.copper_eval(spec,0,T)['heat_into_face_W'];columns.append([-q[k] for k in tags])
 G=np.array(columns).T
 assert np.allclose(G,G.T,atol=1e-12) and np.max(abs(G.sum(axis=1)))<1e-12
 assert np.linalg.eigvalsh(G).min()>-1e-12

def test_geometry_gap_gas_and_wires():
 a=h.read(h.ORIGINAL);b=h.read(h.CANDIDATE);ga=h.interstage_gas_geometry(a);gb=h.interstage_gas_geometry(b)
 assert [g['gap_m'] for g in ga]==pytest.approx([.00057]*3)
 assert [g['gap_m'] for g in gb]==pytest.approx([.00067]*3)
 assert [g['area_m2']*1e6 for g in gb]==pytest.approx([17.76,10.92,4.48])
 for z in gb:
  u=h.interstage_gas(300,280,z['gap_m'],z['area_m2']);v=h.interstage_gas(280,300,z['gap_m'],z['area_m2'])
  assert u['Q_W']==pytest.approx(-v['Q_W']) and u['Q_W']>0
  assert h.interstage_gas(280,280,z['gap_m'],z['area_m2'])['Q_W']==0
  assert h.interstage_gas(300,280,z['gap_m'],z['area_m2'],0)['Q_W']==0
 wa=h.wire_geometry(a);wb=h.wire_geometry(b)
 assert [wb[i]['length_m']-wa[i]['length_m'] for i in range(4)]==pytest.approx([0,0,.0003,.0003],abs=1e-12)

def test_internal_gas_exchange_is_pairwise_conservative():
 q=np.array([.003,.002,.001]);into_plate=np.array([-q[0],q[0]-q[1],q[1]-q[2],q[2]])
 assert abs(into_plate.sum())<1e-15
 assert into_plate.tolist()==pytest.approx([-.003,.001,.001,.001])
