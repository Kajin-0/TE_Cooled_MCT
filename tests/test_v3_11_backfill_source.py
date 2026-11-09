"""V3.11 regenerated Rev3 gas/pressure effects on source-based TEC + TO package."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_11_rev3_backfill_source_20261109'
CASES=('vacuum_I040','Kr100_I040','Kr30k_I040','Kr101k_I040','Ar30k_I040','N2_30k_I040','N2_101k_I040','Kr30k_I055')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def case(n):
 p=D/n
 return [json.loads((p/f).read_text()) for f in ('registration.json','result.json','independent_energy_audit.json')]
def test_registered_source_inputs_and_full_energy():
 for n in CASES:
  reg,d,a=case(n)
  assert d['status'].startswith('V3.11 CONDITIONAL')
  assert a['verdict'].startswith('PASS V3.11')
  assert d['original_ceramic_TET4']==11791
  assert len(d['source_individual_leg_flux_and_electric_results'])==88
  assert a['result_sha256']==sha(D/n/'result.json')
  assert a['registration_sha256']==sha(D/n/'registration.json')
  assert d['solver_source_sha256']==reg['script_SHA256']==sha(ROOT/'scripts/v3_11_package_gas_pressure.py')
  assert abs(a['global_energy_residual_W'])<1e-8
  assert a['max_stage_energy_residual_W']<1e-8
  assert d['max_last_spatial_temperature_update_K']<3e-7
  assert d['cavity_gas_species']==reg['gas_species']
  assert d['cavity_pressure_Pa']==reg['gas_pressure_Pa']
  assert reg['detector_heat_W']==.002
def test_vacuum_and_actual_source_0p4A_reference():
 vacuum=case('vacuum_I040')[1]
 assert vacuum['cavity_pressure_Pa']==0
 assert vacuum['cavity_gas_heat_into_three_ceramics_and_die_W']==[0.,0.,0.,0.]
 assert vacuum['gas_effective_conductance_W_K']==[0.,0.,0.,0.]
 nominal=case('Kr100_I040')[1]
 original=json.loads((ROOT/'data/v3_6_operating_envelope_20261109/I040_Q002/result.json').read_text())
 for k in ('calculated_detector_temperature_K','terminal_voltage_V','electrical_power_W','bath_heat_rejected_W'):
  assert abs(nominal[k]-original[k])<1e-10,k
def test_pressure_and_gas_under_same_0p4A():
 v=case('vacuum_I040')[1];kr=case('Kr100_I040')[1];k30=case('Kr30k_I040')[1];k101=case('Kr101k_I040')[1]
 assert v['calculated_detector_temperature_K']<kr['calculated_detector_temperature_K']<k30['calculated_detector_temperature_K']<k101['calculated_detector_temperature_K']
 assert sum(k101['cavity_gas_heat_into_three_ceramics_and_die_W'])>sum(k30['cavity_gas_heat_into_three_ceramics_and_die_W'])
 a=case('Ar30k_I040')[1];n=case('N2_30k_I040')[1]
 assert k30['calculated_detector_temperature_K']<a['calculated_detector_temperature_K']<n['calculated_detector_temperature_K']
def test_current_crosscheck_0p55A_is_not_global_optimum_claim():
 d=case('Kr30k_I055')[1]
 original=json.loads((ROOT/'data/v3_6_operating_envelope_20261109/I055_Q002_corrected/result.json').read_text())
 baseline=case('Kr30k_I040')[1]
 assert abs(d['operating_current_A']-.55)<1e-13
 assert d['calculated_detector_temperature_K']<baseline['calculated_detector_temperature_K']
 assert d['electrical_power_W']>baseline['electrical_power_W']
 assert 0<d['calculated_detector_temperature_K']-original['calculated_detector_temperature_K']<.05

def test_unchanged_original_sources_and_Rev3():
 for file in ('scripts/v3_6_current_heatload_envelope.py','tecooledmct/integrated_reference.py','tecooledmct/nonlinear_tec.py'):
  assert (ROOT/file).read_bytes()==subprocess.check_output(['git','show','HEAD:'+file],cwd=ROOT)
 assert sha(ROOT/'reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf')=='a017bdfd614e34c8fa8ae5b410862c9bdb24be681163f7408ebe018c153a0168'
 assert sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf')=='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
if __name__=='__main__':
 for k,v in sorted(globals().items()):
  if k.startswith('test_') and callable(v):v();print(k,'PASS')
