"""Read-only reconstruction of archived nominal electrical and heat budgets."""
from pathlib import Path
import json,hashlib,math
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_ports_20261110';P=R/'data/tec_height_coupling_20261110/nominal/result.json'
def check(r):
 I=r['operating_current_A'];power=I*r['terminal_voltage_V'];assert abs(power-r['electrical_power_W'])<1e-10
 stages=r['source_stage_thermoelectric_budget'];legs=r['source_individual_leg_flux_and_electric_results'];assert len(legs)==88
 stage_error=[s['qh_w']-s['qc_w']-I*s['voltage_v'] for s in stages];assert max(map(abs,stage_error))<1e-9
 per_leg=max(abs(q['Qhot_W']-q['Qcold_W']-I*q['terminal_contribution_V']) for q in legs);assert per_leg<1e-9
 gas=r['cavity_gas_heat_into_three_ceramics_and_die_W'];rad=r['gray_radiation_heat_into_three_ceramics_and_die_W'];leads=r['source_tec_power_leads'];detector=r['detector_bond_heat_and_bias_W'];sink=r['bath_heat_rejected_W']
 # detector term already includes die load, gold wires, and die gas/radiation.
 net=power+detector+sum(gas[:3])+sum(rad[:3])+leads['conduction_into_ceramic_W']-.5*leads['joule_W']-sink
 assert abs(net)<1e-8
 return {'status':'PASS independent stored nominal current, stage and package power reconstruction; no new solve','electrical_W':power,'stage_qh_minus_qc_minus_IV_W':stage_error,'max_leg_energy_residual_W':per_leg,'die_inclusive_heat_W':detector,'gas_external_ceramic_W':gas[:3],'gas_external_die_W':gas[3],'radiation_ceramic_W':rad[:3],'radiation_die_W':rad[3],'lead_conduction_into_tec_W':leads['conduction_into_ceramic_W'],'lead_half_joule_to_header_W':.5*leads['joule_W'],'bath_rejection_W':sink,'global_energy_residual_W':net,'interstage_gas_W':r['internal_interstage_gas_heat_hot_to_cold_W'],'source_result_sha256':hashlib.sha256(P.read_bytes()).hexdigest()}
def main():
 q=D/'nominal_budget_audit.json';assert not q.exists();v=check(json.loads(P.read_text()));q.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
if __name__=='__main__':main()
