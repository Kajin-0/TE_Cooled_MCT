"""V3.8 original-source TEC material/sink transfer: independent archived physics gates."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/v3_8_rev3_transport_and_sink_20261109'
BASE=('base_I040','S090_I040','S110_I040','rho080_I040','rho120_I040',
      'k080_I040','k120_I040','sink_plus05_I040','sink_plus10_I040',
      'sink_plus05_I055','sink_plus10_I055')
INTERMEDIATE=('sink_plus05_near_target','sink_plus10_near_target')
MATCHED=('sink_plus05_matched_refined','sink_plus10_matched_refined')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):
 p=D/n
 return [json.loads((p/f).read_text()) for f in ('registration.json','result.json','independent_energy_audit.json')]
def test_accepted_complete_source_system():
 for n in (*BASE,*INTERMEDIATE,*MATCHED):
  reg,d,a=read(n)
  assert a['verdict'].startswith('PASS V3.8')
  assert a['result_sha256']==sha(D/n/'result.json')
  assert a['registration_sha256']==sha(D/n/'registration.json')
  assert d['status'].startswith('V3.8 CONDITIONAL')
  assert abs(a['global_energy_residual_W'])<2e-9
  assert a['max_stage_energy_residual_W']<2e-9
  assert abs(a['independent_sink_T_closure_K'])<4e-7
  assert type(a['base_R_sink_K_W']) is float
  assert type(a['added_R_sink_K_W']) is float
  assert abs(a['base_R_sink_K_W']+a['added_R_sink_K_W']-a['total_sink_R_K_W'])<1e-12
  assert d['max_last_spatial_temperature_update_K']<3e-7
  assert d['original_ceramic_TET4']==11791
  assert len(d['source_individual_leg_flux_and_electric_results'])==88
  assert d['source_thermoelectric_scale_S_rho_k']==reg['P_N_scale_tuple']
  assert d['source_HgCdTe_bias_heat_W']>0
def test_base_reproduces_exact_existing_V37():
 d=read('base_I040')[1]
 b=json.loads((ROOT/'data/v3_7_hgcdte_electrothermal_20261109/reference_match/result.json').read_text())
 for key in ('calculated_detector_temperature_K','terminal_voltage_V','electrical_power_W','bath_heat_rejected_W'):
  assert abs(d[key]-b[key])<1e-10,(key,d[key]-b[key])
 assert d['source_thermoelectric_scale_S_rho_k']==[1,1,1]
 assert d['additional_external_sink_R_K_W']==0
def test_one_factor_material_screen_and_sink_monotonic():
 assert all(read(n)[0]['additional_external_mounting_sink_R_K_W']==0 for n in BASE[:7])
 for a,b in [('S090_I040','S110_I040'),('rho080_I040','rho120_I040'),('k080_I040','k120_I040')]:
  p=read(a)[0]['P_N_scale_tuple'];q=read(b)[0]['P_N_scale_tuple']
  assert sum(x!=y for x,y in zip(p,q))==1
 for current in ('.4','.55'):
  lo='base_I040' if current=='.4' else None
  l='sink_plus05_I040' if current=='.4' else 'sink_plus05_I055'
  h='sink_plus10_I040' if current=='.4' else 'sink_plus10_I055'
  assert read(h)[1]['calculated_detector_temperature_K']>read(l)[1]['calculated_detector_temperature_K']
  if lo:assert read(l)[1]['calculated_detector_temperature_K']>read(lo)[1]['calculated_detector_temperature_K']
def test_frozen_history_unchanged():
 assert sha(ROOT/'reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf')=='a017bdfd614e34c8fa8ae5b410862c9bdb24be681163f7408ebe018c153a0168'
 assert sha(ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf')=='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
 assert sha(ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json')=='023d8b26931fcb758d379a4150470305f4f613bf3543aae3065a98bc5be762c8'



def test_actual_matched_temperature_power_cost_and_intentional_refinement():
 base=read('base_I040')[1]
 target=base['calculated_detector_temperature_K']
 assert abs(target-218.90002402868413)<1e-10
 for extra,old,final in ((5,INTERMEDIATE[0],MATCHED[0]),(10,INTERMEDIATE[1],MATCHED[1])):
  a=read(old)[1];d=read(final)[1]
  assert abs(d['calculated_detector_temperature_K']-target)<.05
  assert abs(d['calculated_detector_temperature_K']-target)<abs(a['calculated_detector_temperature_K']-target)
  assert d['additional_external_sink_R_K_W']==extra
  assert .4<d['operating_current_A']<.55
  assert d['electrical_power_W']>base['electrical_power_W']
 assert read(MATCHED[1])[1]['electrical_power_W']>read(MATCHED[0])[1]['electrical_power_W']

def test_material_endpoint_ranking_under_selected_factor_widths():
 span=[]
 for a,b in [('k080_I040','k120_I040'),('S090_I040','S110_I040'),('rho080_I040','rho120_I040')]:
  x=read(a)[1];y=read(b)[1]
  span.append(abs(x['calculated_detector_temperature_K']-y['calculated_detector_temperature_K']))
 assert span[0]>span[1]>span[2]>0
 assert 19.8<span[0]<19.9
 assert 13.3<span[1]<13.4
 assert 4.7<span[2]<4.8

if __name__=='__main__':
 for n,f in sorted(globals().items()):
  if n.startswith('test_') and callable(f):f();print(n,'PASS')
