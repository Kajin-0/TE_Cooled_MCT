import json,math
from pathlib import Path
import pytest
from tecooledmct.nominal_cavity_metal_v326 import project_yz,segment_profile
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_metal_v326_20261111'

def test_projection_analytic_line_arc_and_invalid():
 line={'type':'line','a':[0.,0.],'b':[1.,0.],'length':1.}
 arc={'type':'arc','a':[1.,0.],'b':[0.,1.],'c':[0.,0.],'r':1.,'length':math.pi/2}
 assert project_yz([line],[.25,.3])==pytest.approx((.3,.25))
 assert project_yz([arc],[math.sqrt(.5),math.sqrt(.5)])==pytest.approx((0.,math.pi/4),abs=1e-14)
 assert project_yz([line],[3.,0.])==pytest.approx((2.,1.))
 with pytest.raises(ValueError):project_yz([], [0.,0.])
 with pytest.raises(ValueError):project_yz([{'type':'arc',**{k:v for k,v in arc.items() if k not in ('type','length')},'length':1.}], [0.,0.])

def test_passive_uniform_joule_segment_exact_and_negative():
 g=.002;res=.003;I=.4;P=I*I*res;t0=300.;t1=250.
 for u in (0.,.17,.5,.9,1.):
  T,q0,q1=segment_profile(u,t0,t1,res,g,I)
  assert T==pytest.approx((1-u)*t0+u*t1+P/(2*g)*u*(1-u),abs=1e-12)
  assert q0+q1==pytest.approx(-P,abs=1e-15)
 assert segment_profile(0.,t0,t1,res,g,I)[0]==t0
 assert segment_profile(1.,t0,t1,res,g,I)[0]==t1
 assert segment_profile(.5,275,275,0,g,0)==(275.,0.,0.)
 for args in [(-.1,t0,t1,res,g,I),(1.1,t0,t1,res,g,I),(.5,t0,t1,res,0,I),(.5,t0,t1,-1,g,I),(.5,t0,t1,res,g,float('nan'))]:
  with pytest.raises(ValueError):segment_profile(*args)

def test_original_face_accounting_and_nonisothermal_net88():
 g=json.loads((D/'face_temperature_graph.json').read_text());faces=g['entries']; assert len(faces)==1840 and len({x['face_tag'] for x in faces})==1840
 assert sum(x['area_mm2'] for x in faces)==pytest.approx(903.2150497910573,abs=1e-9)
 assert g['groups']['CONDITIONAL_DISTRIBUTED_TAB_CENTERLINE']['faces']==39
 assert g['groups']['UNRESOLVED']['faces']==134
 mapped=[f for f in faces if f['mapping']['status']=='CONDITIONAL_DISTRIBUTED_TAB_CENTERLINE']
 for f in mapped:
  m=f['mapping'];assert sum(m['endpoint_weights'])==pytest.approx(1,abs=1e-14) and min(m['endpoint_weights'])>=0 and m['centroid_to_centerline_mm']<=.0250000001
  assert m['temperature_K']==pytest.approx(sum(t*w for t,w in zip(m['foil_endpoint_temperature_K'],m['endpoint_weights']))+m['joule_rise_K'],abs=1e-12)
 n=[f['mapping'] for f in mapped if f['mapping']['net']==88];assert set(f['segment'] for f in n)=={0,1};assert max(f['temperature_K'] for f in n)-min(f['temperature_K'] for f in n)>40
 # No broad concave side-face centroid is silently accepted.
 for tag in (2090,2093,2112,2115,2144,2148): assert next(x for x in faces if x['face_tag']==tag)['mapping']['status']=='UNRESOLVED'

def test_distributed_uniform_bath_analytic_balance_and_limits():
 from tecooledmct.nominal_cavity_metal_v326 import segment_with_uniform_bath as f
 G=.002;R=.003;I=.4;H=.0001;B=280.;a=300.;b=250.
 for u in (0.,.2,.5,.8,1.):
  T,q0,q1,qg=f(u,a,b,R,G,I,B,H);assert qg==pytest.approx(q0+q1+I*I*R,abs=1e-14)
  if 0<u<1:
   h=1e-4;left=f(u-h,a,b,R,G,I,B,H)[0];right=f(u+h,a,b,R,G,I,B,H)[0];d2=(left-2*T+right)/h**2
   assert -G*d2+H*(T-B)==pytest.approx(I*I*R,abs=8e-8)
 assert f(0,a,b,R,G,I,B,H)[0]==pytest.approx(a,abs=1e-12)
 assert f(1,a,b,R,G,I,B,H)[0]==pytest.approx(b,abs=1e-12)
 assert f(.5,275,275,0,G,0,275,H)==pytest.approx((275.,0.,0.,0.))
 assert f(.37,a,b,R,G,I,B,0)==pytest.approx((*segment_profile(.37,a,b,R,G,I),0.))
 assert f(.37,a,b,R,G,I,B,G*1e-12) == pytest.approx(f(.37,a,b,R,G,I,B,0),abs=1e-10)
 with pytest.raises(ValueError):f(.5,a,b,R,G,I,B,-1.)
 with pytest.raises(ValueError):f(.5,a,b,R,G,I,B,G*2601.)
