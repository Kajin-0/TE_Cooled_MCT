"""V3.9 above-published-range continuation gate and full-source evidence."""
from pathlib import Path
from math import sqrt
import hashlib,json
import numpy as np
from tecooledmct import nonlinear_tec
from tecooledmct.nonlinear_tec_v39 import leg,properties
from scripts.v3_9_highT_source_qualification import expected
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_9_highT_source_qualification_20261109'
CASES=('sink00_factor000','sink00_factor025','sink00_factor100',
       'sink10_factor000','sink10_factor025','sink10_factor100')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def get(n):
 p=D/n
 return [json.loads((p/f).read_text()) for f in
  ('registration.json','result.json','independent_energy_audit.json')]
def test_high_T_variants_identical_below_300_and_nominal_old_law():
 for pol in ('P','N'):
  for T in (190.,230.,275.,299.,300.):
   orig=nonlinear_tec.properties(pol,np.array([T]),(1.,1.,1.))
   for factor in (0.,.25,1.):
    new=properties(pol,np.array([T]),(1.,1.,1.),factor)
    for field in ('S','rho','k','S_prime','rho_prime','k_prime'):
     assert np.array_equal(new[field],orig[field]),(pol,T,factor,field)
  for f in (0.,.25,1.):
   case=leg(pol,295.,245.,(-1 if pol=='P' else 1)*.4/1.6e-7,.0005,high_T_slope_factor=f)
   orig=nonlinear_tec.leg(pol,295.,245.,(-1 if pol=='P' else 1)*.4/1.6e-7,.0005)
   for field in ('q_hot_w_m2','q_cold_w_m2','electric_integral_v','joule_w_m2'):
    assert case[field]==orig[field],(pol,f,field)
def test_high_T_variants_positive_and_energy_conservative():
 for pol in ('P','N'):
  for factor in (0.,.25,1.):
   for T in (300.001,310.,350.,389.):
    x=properties(pol,np.array([T]),(1.,1.,1.),factor)
    assert x['rho']>0 and x['k']>0
    assert x['S']*(1 if pol=='P' else -1)>0
   state=leg(pol,310.,245.,(-1 if pol=='P' else 1)*.4/1.6e-7,.0005,high_T_slope_factor=factor)
   assert abs(state['energy_error_w_m2'])<1e-6
   assert state['axial_nodes_above_source_300K']>0
def test_registration_rejects_unregistered_factors():
 # GitHub Actions does not mount the external original 430-domain geometry
 # at /var/tmp. The full registration hashes that mesh BEFORE validating
 # inputs, so expected() cannot serve as a portable negative-input test.
 # Check the registration's literal fail-closed factor guard, and exercise
 # the real independent transport law on unsupported factors without FEM.
 import inspect
 from tecooledmct.nonlinear_tec_v39 import properties as source_props
 assert 'assert high_T_slope_factor in (0.,.25,1.)' in inspect.getsource(expected)
 for factor in (-1.,.1,.5,2.,float('nan')):
  try:
   source_props('P',__import__('numpy').array([305.]),(1.,1.,1.),factor)
  except ValueError:
   continue
  raise AssertionError('invalid high-T factor accepted: '+str(factor))
def test_original_reference_and_new_scenarios():
 v8=json.loads((ROOT/'data/v3_8_rev3_transport_and_sink_20261109/base_I040/result.json').read_text())
 for n in CASES:
  reg,d,a=get(n)
  assert d['status'].startswith('V3.9')
  assert a['verdict'].startswith('PASS V3.9')
  assert reg['script_SHA256']==sha(ROOT/'scripts/v3_9_highT_source_qualification.py')
  assert d['solver_source_sha256']==reg['script_SHA256']
  assert a['result_sha256']==sha(D/n/'result.json')
  assert abs(a['global_energy_residual_W'])<2e-9
  assert abs(a['independent_sink_T_closure_K'])<4e-7
  assert d['original_ceramic_TET4']==11791
  assert len(d['source_individual_leg_flux_and_electric_results'])==88
  assert d['source_legs_with_hot_boundary_above_300K']>=1
  assert d['source_axial_nodes_above_300K_sum']>0
 for n,old in (('sink00_factor025',v8),('sink10_factor025',
   json.loads((ROOT/'data/v3_8_rev3_transport_and_sink_20261109/sink_plus10_I040/result.json').read_text()))):
  d=get(n)[1]
  for k in ('calculated_detector_temperature_K','terminal_voltage_V',
            'electrical_power_W','bath_heat_rejected_W'):
   assert abs(d[k]-old[k])<1e-10,(n,k,d[k]-old[k])
def test_original_CAD_previous_report_and_transport_unchanged():
 assert (ROOT/'tecooledmct/nonlinear_tec.py').read_bytes()==__import__('subprocess').check_output(['git','show','HEAD:tecooledmct/nonlinear_tec.py'],cwd=ROOT)
 assert sha(ROOT/'reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf')=='a017bdfd614e34c8fa8ae5b410862c9bdb24be681163f7408ebe018c153a0168'
 assert sha(ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json')=='023d8b26931fcb758d379a4150470305f4f613bf3543aae3065a98bc5be762c8'
if __name__=='__main__':
 for n,v in sorted(globals().items()):
  if n.startswith('test_') and callable(v):
   v();print('PASS',n)
