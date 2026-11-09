"""V3.7 bias/heating coupling, source provenance, independent heat-energy and Rev3 transfer."""
from pathlib import Path
from math import isclose,sqrt
import hashlib,json
from tecooledmct.hgcdte_bias_proxy import photoconductor_at_T,hsc_bandgap_eV,HC_EV_UM
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_7_hgcdte_electrothermal_20261109'
CASES=('zero_bias','reference_match','bias_1p2V','bias_1p5V','bias_1p2V_high_activation')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(case):
 p=D/case
 return (json.loads((p/'registration.json').read_text()),
         json.loads((p/'result.json').read_text()),
         json.loads((p/'independent_energy_audit.json').read_text()))
def test_reference_0p4A_and_split_reproduces_V36_without_replacing_it():
 a=json.loads((ROOT/'data/v3_6_operating_envelope_20261109/I040_Q002/result.json').read_text())
 r,d,ind=load('reference_match')
 assert r['current_A']==.4 and r['absorbed_optical_W']==.0005
 for k in ('calculated_detector_temperature_K','terminal_voltage_V',
           'electrical_power_W','bath_heat_rejected_W'):
    assert abs(d[k]-a[k])<1e-10,(k,d[k],a[k])
 assert abs(d['source_HgCdTe_bias_heat_W']-.0015)<1e-12
 assert abs(d['detector_imposed_heat_W']-.002)<1e-12
 assert a['source_3D_ceramic_gas_radiation_heat_spread']==d['source_3D_ceramic_gas_radiation_heat_spread']
def test_five_independently_accepted_real_thermal_solves():
 for name in CASES:
  r,d,a=load(name)
  assert d['status'].startswith('V3.7')
  assert a['verdict'].startswith('PASS V3.7')
  assert a['result_sha256']==sha(D/name/'result.json')
  assert a['registration_sha256']==sha(D/name/'registration.json')
  assert abs(a['global_energy_residual_W'])<2e-9
  assert a['max_stage_energy_residual_W']<2e-9
  assert d['max_last_spatial_temperature_update_K']<3e-7
  assert d['original_ceramic_TET4']==11791
  assert len(d['source_individual_leg_flux_and_electric_results'])==88
  assert d['source_HgCdTe_electrothermal_at_T']['voltage_V']==r['detector_bias_V']
  assert d['solver_source_sha256']==r['script_SHA256']
def test_bias_and_resistance_hypotheses():
 z=[load(c)[1] for c in CASES[:4]]
 assert all(b['calculated_detector_temperature_K']>a['calculated_detector_temperature_K'] for a,b in zip(z,z[1:]))
 assert all(b['source_HgCdTe_bias_heat_W']>a['source_HgCdTe_bias_heat_W'] for a,b in zip(z,z[1:]))
 assert z[0]['source_HgCdTe_bias_heat_W']==0
 v=load('bias_1p2V')[1]
 x=load('bias_1p2V_high_activation')[1]
 assert x['source_HgCdTe_electrothermal_at_T']['effective_activation_eV']==.06
 assert x['calculated_detector_temperature_K']>v['calculated_detector_temperature_K']
 assert abs(x['calculated_detector_temperature_K']-v['calculated_detector_temperature_K'])<.03
def test_bias_law_finite_difference_and_isothermal_energy():
 for E in (0.,.03,.06,.12):
  t=220.;V=1.2
  z=photoconductor_at_T(t,V,.0005,500,218.90002402868413,E)
  dT=.001
  plus=photoconductor_at_T(t+dT,V,.0005,500,218.90002402868413,E)
  minus=photoconductor_at_T(t-dT,V,.0005,500,218.90002402868413,E)
  derivative=(plus['detector_bias_Joule_W']-minus['detector_bias_Joule_W'])/(2*dT)
  assert abs(derivative-z['d_bias_Joule_dT_W_K_at_constant_V'])<2e-12
  assert abs(z['total_applied_detector_heat_W']-V*z['detector_dark_current_A']-.0005)<1e-15
def test_rev3_composition_thermal_only_is_not_LWIR_detector_claim():
 Eg=hsc_bandgap_eV(.29,218.90002402868413)
 cutoff=HC_EV_UM/Eg
 assert .24<Eg<.28 and 4.5<cutoff<5.2
 assert sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf')=='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
def test_original_V36_and_current_pdf_unchanged():
 assert sha(ROOT/'scripts/v3_6_current_heatload_envelope.py')=='086efd90ac603fa90e93def1a066f7fb0c40ab65ac6f0e6969f24596b07dfd51'
 assert sha(ROOT/'reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf')=='a017bdfd614e34c8fa8ae5b410862c9bdb24be681163f7408ebe018c153a0168'
 assert sha(ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json')=='023d8b26931fcb758d379a4150470305f4f613bf3543aae3065a98bc5be762c8'
if __name__=='__main__':
 for key,f in sorted(globals().items()):
  if key.startswith('test_') and callable(f):
   f();print(key,'PASS')
