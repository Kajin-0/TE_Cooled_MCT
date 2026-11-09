"""V3.10 semiconductor carrier/bandgap and full-system source evidence tests."""
from pathlib import Path
from math import isclose
import hashlib,json,subprocess
from tecooledmct.hgcdte_carrier_transport_v310 import (
    bandgap_eV,intrinsic_cm3,intrinsic_log_slope_per_K,state,Q_C)
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_10_hgcdte_carrier_20261109'
NAMES=('off_x020','lw_x020','x022','x024','mw_x029','lw_x020_highbias','lw_x020_lowdoping')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
 p=D/name
 return (json.loads((p/'registration.json').read_text()),json.loads((p/'result.json').read_text()),
         json.loads((p/'independent_energy_audit.json').read_text()))
def test_banded_gap_intrinsic_density_physical_domains():
 for x in (.20,.22,.24,.29):
  T=218.9
  Eg=bandgap_eV(x,T)
  assert .10<Eg<.28
  assert 4.0<1.2398419843/Eg<13.
  assert intrinsic_cm3(x,T)>0
  h=.0005
  d=(__import__('math').log(intrinsic_cm3(x,T+h))-__import__('math').log(intrinsic_cm3(x,T-h)))/(2*h)
  assert abs(d-intrinsic_log_slope_per_K(x,T))<2e-9
 for x,T in ((.1,219),(.55,219),(.2,400)):
  try:bandgap_eV(x,T)
  except ValueError:continue
  raise AssertionError('invalid material bounds accepted')
def test_state_charge_neutrality_and_ohmic_joule_and_Johnson():
 from math import sqrt
 for x,mob in ((.20,450),(.22,450),(.24,400),(.29,220)):
  for dop in (1e15,1e16):
   for T in (204.,219.,238.):
    z=state(T,.35,.0005,x,dop,.0004,.0001,.00001,mob,100)
    assert abs(z['hole_carriers_cm3']-z['electron_carriers_cm3']-dop)<1e-5*dop
    assert abs(z['electron_carriers_cm3']*z['hole_carriers_cm3']-z['intrinsic_carriers_cm3']**2)<1e-9*z['intrinsic_carriers_cm3']**2
    assert abs(z['detector_bias_Joule_W']-.35**2/z['dark_resistance_ohm'])<1e-15
    assert abs(z['johnson_voltage_V_sqrtHz']**2-4*1.380649e-23*T*z['dark_resistance_ohm'])<1e-27
    dt=.001
    aa=state(T+dt,.35,.0005,x,dop,.0004,.0001,.00001,mob,100)
    bb=state(T-dt,.35,.0005,x,dop,.0004,.0001,.00001,mob,100)
    derivative=(aa['detector_bias_Joule_W']-bb['detector_bias_Joule_W'])/(2*dt)
    assert abs(derivative-z['d_bias_Joule_dT_W_K_at_constant_V'])<3e-10
def test_full_case_independent_source_cad_energy():
 for name in NAMES:
  reg,d,a=read(name)
  assert d['status'].startswith('V3.10 CONDITIONAL')
  assert a['verdict'].startswith('PASS V3.10')
  assert reg['script_SHA256']==sha(ROOT/'scripts/v3_10_hgcdte_carrier_coupled.py')
  assert a['result_sha256']==sha(D/name/'result.json')
  assert a['registration_sha256']==sha(D/name/'registration.json')
  assert abs(a['global_energy_residual_W'])<2e-9
  assert a['max_stage_energy_residual_W']<2e-9
  assert abs(a['independent_sink_T_closure_K'])<4e-7
  assert d['original_ceramic_TET4']==11791
  assert len(d['source_individual_leg_flux_and_electric_results'])==88
  assert d['max_last_spatial_temperature_update_K']<3e-7
  assert not d['source_HgCdTe_electrothermal_at_T']['independent_resistance_calibration']
def test_zero_bias_and_compositional_temperature_order():
 z=read('off_x020')[1];a=read('lw_x020')[1]
 assert z['source_HgCdTe_bias_heat_W']==0
 assert a['calculated_detector_temperature_K']>z['calculated_detector_temperature_K']
 h=read('lw_x020_highbias')[1]
 assert h['calculated_detector_temperature_K']>a['calculated_detector_temperature_K']
 assert h['source_HgCdTe_bias_heat_W']>a['source_HgCdTe_bias_heat_W']
 bands=[read(n)[1]['source_HgCdTe_electrothermal_at_T']['idealized_Eg_cutoff_um'] for n in ('lw_x020','x022','x024','mw_x029')]
 assert all(a>b for a,b in zip(bands,bands[1:]))
def test_frozen_source_previous_reports():
 for name in ('tecooledmct/nonlinear_tec.py','tecooledmct/graded_tec.py',
              'scripts/v3_9_highT_source_qualification.py'):
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)
 assert sha(ROOT/'reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf')=='a017bdfd614e34c8fa8ae5b410862c9bdb24be681163f7408ebe018c153a0168'
 assert sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf')=='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
if __name__=='__main__':
 for n,f in sorted(globals().items()):
  if n.startswith('test_') and callable(f):
   f();print('PASS',n)
