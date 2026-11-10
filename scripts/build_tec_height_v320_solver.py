"""Generate an auditable static derivative from the sealed V3.11 source."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
s=(R/'scripts/v3_11_package_gas_pressure.py').read_text()
def replace(old,new,count=1):
 global s
 n=s.count(old)
 if n!=count:raise ValueError(f'Expected {count} occurrences, found {n}: {old[:90]!r}')
 s=s.replace(old,new)
replace('from tecooledmct.nonlinear_tec import leg','''from tecooledmct.nonlinear_tec import leg
from tecooledmct.height_coupling_v320 import (mapping,read as geometry_read,ORIGINAL,CANDIDATE,copper_specs,copper_eval,wire_geometry,interstage_gas_geometry,interstage_gas)''')
replace('def solve(reg):\n assert reg==expected', 'def solve(reg,variant):\n assert variant in ("nominal","custom_060")\n assert reg==expected')
replace(' spatial=OriginalPlates(legs)\n previous=', ''' proof=mapping()
 spatial=OriginalPlates(legs)
 design=geometry_read(ORIGINAL if variant=='nominal' else CANDIDATE)
 shifts=[0.,0.,0.,0.] if variant=='nominal' else proof['plate_shifts_mm']
 for i,p in enumerate(spatial.plates):
  p['xyz_mm']=p['xyz_mm'].copy();p['xyz_mm'][:,2]+=shifts[i]
 tab_spec=copper_specs(design);gas_spec=interstage_gas_geometry(design)
 wire_spec={v['name']:v for v in wire_geometry(design)}
 previous=''')
replace(" geo=original_geometry()\n cu=", " geo=original_geometry()\n for w in geo['wires']:\n  v=wire_spec[w['name']];w['length_m']=v['length_m'];w['G_W_K']=v['G_W_K'];w['R_ohm']=v['R_ohm']\n cu=")
replace(" A=geo['stages'][0]['leg_area_m2'];L=geo['stages'][0]['leg_length_m']", " A=geo['stages'][0]['leg_area_m2'];L=.0005 if variant=='nominal' else .0006")
replace("  return qgas,qrad,area,g_conductance\n def plus_solder_into_ceramic(rows, joint_joule_W=None):", """  return qgas,qrad,area,g_conductance
 def internal_gas(y):
  return np.array([interstage_gas(y[2*j],y[2*j+1],g['gap_m'],g['area_m2'],reg['gas_pressure_Pa'])['Q_W'] for j,g in enumerate(gas_spec)])
 def plus_solder_into_ceramic(rows, joint_joule_W=None, gas_W=None):""")
replace("  j=P_joint if joint_joule_W is None else float(joint_joule_W)","  j=P_joint if joint_joule_W is None else float(joint_joule_W)\n  gas=np.zeros(3) if gas_W is None else np.asarray(gas_W)")
replace("return [{**r,'Qhot_W':r['Qhot_W']+j,\n           'Qcold_W':r['Qcold_W']-j} for r in rows]", "return [{**r,'Qhot_W':r['Qhot_W']+j-gas[r['stage']]/stage_joints[r['stage']],\n           'Qcold_W':r['Qcold_W']-j-gas[r['stage']]/stage_joints[r['stage']]} for r in rows]")
replace(' def powerleads(y):',' def powerleads(y,current):')
replace("                   I,reg['ambient_K'])", "                   current,reg['ambient_K'])")
replace(' def copper(y):',' def copper(y,current):')
replace("  return copper_evaluate(I,Tface,\n    thermal_area_resistance=reg['Cu_port_thermal_Rarea_m2K_W'],\n    electrical_area_resistance=reg['Cu_port_electrical_Rarea_ohm_m2'])","  return copper_eval(tab_spec,current,Tface,\n    thermal_Rarea=reg['Cu_port_thermal_Rarea_m2K_W'],\n    electrical_Rarea=reg['Cu_port_electrical_Rarea_ohm_m2'])")
replace(" 'stage2_hot','stage2_cold','carrier','die')],float)"," 'stage2_hot','stage2_cold','carrier','die')]+[I],float)")
replace('  def model(y,include=False):\n   stag=', '  def model(y,include=False):\n   I=float(y[8]); joint=I*I*R_joint\n   stag=')
replace('   lead=powerleads(y);qcu=', '   lead=powerleads(y,I);qcu=')
replace("   cm=copper(y)\n   bath=stag[0]['qh_w']+lead['total_pad_heat_W']+stage_joints[0]*P_joint+cm['heat_into_ceramic_by_stage_W'][0]", "   cm=copper(y,I)\n   gas=internal_gas(y)\n   bath=stag[0]['qh_w']+lead['total_pad_heat_W']+stage_joints[0]*joint+cm['heat_into_ceramic_by_stage_W'][0]-gas[0]")
replace("   qext=qgas+qrad\n   return np.array([", "   qext=qgas+qrad\n   ig=internal_gas(y);joint=y[8]**2*R_joint\n   return np.array([")
replace("-(stage_joints[0]+stage_joints[1])*P_joint-qext[0]-cm['heat_into_ceramic_by_stage_W'][1],", "-(stage_joints[0]+stage_joints[1])*joint-qext[0]-cm['heat_into_ceramic_by_stage_W'][1]-ig[0]+ig[1],")
replace("-(stage_joints[1]+stage_joints[2])*P_joint-qext[1]-cm['heat_into_ceramic_by_stage_W'][2],", "-(stage_joints[1]+stage_joints[2])*joint-qext[1]-cm['heat_into_ceramic_by_stage_W'][2]-ig[1]+ig[2],")
replace("st[2]['qc_w']-Qa-stage_joints[2]*P_joint-qext[2],", "st[2]['qc_w']-Qa-stage_joints[2]*joint-qext[2]-ig[2],")
replace("    y[0]-300-Rext*bath-gaps[0]])", "    y[0]-300-Rext*bath-gaps[0],\n    y[8]*(sum(z['voltage_v'] for z in st)+y[8]*(lead['total_R_ohm']+R_added+cm['total_electrical_R_ohm']))-0.5956680349614825])")
replace('weights=np.array([10.,10.,100.,100.,.1,.1,.1,.5])','weights=np.array([10.,10.,100.,100.,.1,.1,.1,.5,10.])')
replace("bounds=(np.full(8,180.00001),np.full(8,389.99999)),\n       x_scale=np.full(8,10.)", "bounds=(np.r_[np.full(8,180.00001),.25],np.r_[np.full(8,389.99999),.55]),\n       x_scale=np.r_[np.full(8,10.),.1]")
replace("  x=sol.x\n  st,rows,Qa,Qd,qcu,CuJoule,Qbath,cm,lead=model(x,True)","  x=sol.x\n  I=float(x[8]);P_joint=I*I*R_joint;P_added=176*P_joint\n  st,rows,Qa,Qd,qcu,CuJoule,Qbath,cm,lead=model(x,True)")
replace('local_fields,new_offsets=spatial.solve(plus_solder_into_ceramic(rows),st,CuJoule,qcu,Qbath,Qa,', 'local_fields,new_offsets=spatial.solve(plus_solder_into_ceramic(rows,gas_W=internal_gas(x)),st,CuJoule,qcu,Qbath,Qa,')
replace("assert max(abs(err[4:]))<reg['outer_thermal_field_tolerance_K']", "assert max(abs(err[4:8]))<reg['outer_thermal_field_tolerance_K']\n assert abs(err[8])<1e-8,('matched_power',float(err[8]))")
replace("'max_mean_plate_temperature_residual_K':float(max(abs(err[4:]))),", "'max_mean_plate_temperature_residual_K':float(max(abs(err[4:8]))),")
replace(" return out,arrays\n\ndef main():", """ out.update({'status':'CONDITIONAL matched-power 88-leg / four translated spatial ceramics; reduced copper and gas proxies, NOT 3D coupled metal or native gas PDE',
  'variant':variant,'leg_length_m':L,'candidate_ceramic_translation_mm':shifts,
  'source_face_lineage':'95 original TRI3 tags mapped by rigid translation and checked candidate solid ownership; not new candidate mesh tags',
  'internal_interstage_gas_heat_hot_to_cold_W':internal_gas(x).tolist(),
  'internal_gas_geometry_proxy':gas_spec,
  'external_enclosure_model':'3mm effective gap held fixed; not native gas geometry; sensitivity must be considered separately',
  'Cu_net88_middle_electrical_contact':'removed from series electrical path; retained as thermal foot',
  'wire_geometry_used':list(wire_spec.values()),
  'matched_electrical_power_target_W':.5956680349614825,'matched_power_residual_W':float(err[8]),
  'model_version_vs_material_physics':'v320 changed height, translated ceramics, candidate Cu and Au lengths, internal gas proxy; external gas/radiation proxy held fixed',
  'max_mean_plate_temperature_residual_K':float(max(abs(err[4:8])))})
 return out,arrays

def main():""")
replace("    'terminal_contribution_V':float(vol),'energy_residual_W':float(qh-qc-I*vol)})", "    'terminal_contribution_V':float(vol),'energy_residual_W':float(qh-qc-I*vol),\n    'leg_min_K':float(min(r['temperatures_k'])),'leg_max_K':float(max(r['temperatures_k'])),\n    'assumed_above_300K':bool(r['assumed_high_T_continuation_used'])})")
# Replace original CLI, keeping static physics derivation visible above.
pos=s.index('def main():\n p=argparse.ArgumentParser()');s=s[:pos]+'''def main():
 p=argparse.ArgumentParser();p.add_argument('--variant',required=True,choices=('nominal','custom_060'));p.add_argument('--outputdir',type=Path,required=True);a=p.parse_args()
 a.outputdir.mkdir(parents=True,exist_ok=False)
 try:
  reg=expected('copper',1.,1e-6,.4,.002,'Kr',100.)
  (a.outputdir/'executed_registration.json').write_text(json.dumps(reg,indent=2)+'\\n')
  contract=read(ROOT/'data/tec_height_coupling_20261110/solver_contract.json')
  for name,expected_hash in contract['execution_source_sha256'].items():assert sha(ROOT/name)==expected_hash,name
  result,arrays=solve(reg,a.variant)
  (a.outputdir/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\\n')
  np.savez_compressed(a.outputdir/'ceramic_fields.npz',**arrays)
  print('CONDITIONAL_MATCHED_SOLVE',a.variant,result['calculated_detector_temperature_K'],result['electrical_power_W'],flush=True)
 except BaseException as e:
  (a.outputdir/'failure.json').write_text(json.dumps({'status':'STOP','variant':a.variant,'error':repr(e)},indent=2)+'\\n');raise
if __name__=='__main__':main()
'''
out=Path(sys.argv[1]) if len(sys.argv)>1 else R/'scripts/tec_height_v320_coupled.py';assert not out.exists();out.write_text(s)
print('Wrote static source derivative',out)
