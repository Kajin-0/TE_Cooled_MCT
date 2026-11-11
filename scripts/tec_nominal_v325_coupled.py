"""One pre-registered nominal partial-gas matched-power solve; source stays frozen."""
from pathlib import Path
import hashlib,json,types,argparse,numpy as np
from tecooledmct.nominal_gas_p1_coupler_v325 import SourceP1Gas
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_p1_20261111';BASE=R/'scripts/tec_height_v320_coupled.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def transformed():
 s=BASE.read_text()
 def sub(old,new):
  nonlocal s
  assert s.count(old)==1,(old[:100],s.count(old));s=s.replace(old,new)
 sub("previous=read(ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json')", "previous=read(ROOT/'data/tec_height_coupling_20261110/nominal/result.json')")
 sub('proof=mapping()',"proof={'plate_shifts_mm':[0.,0.,0.,0.]}")
 sub("design=geometry_read(ORIGINAL if variant=='nominal' else CANDIDATE)","assert variant=='nominal';design=geometry_read(ORIGINAL)")
 sub("I=reg['current_A']\n A_joint=", "I=float(previous['operating_current_A'])\n A_joint=")
 sub("warm_start_I=0.4", "warm_start_I=float(previous['operating_current_A'])")
 sub("K=K,taglist=taglist", "K=K,gas_lu=lu,taglist=taglist")
 sub("metal_face_heat_W=None,lead_face_heat_W=None):", "metal_face_heat_W=None,lead_face_heat_W=None,gas_node_load_W=None):")
 sub("   loads=inputs[i]\n   assert set(loads).issubset(p['tagindex'])", "   loads=inputs[i]\n   gas_extra=np.zeros(len(p['node_ids'])) if gas_node_load_W is None else np.asarray(gas_node_load_W[i]);assert gas_extra.shape==(len(p['node_ids']),)\n   assert set(loads).issubset(p['tagindex'])")
 sub("   imbalance=float(currents.sum())", "   imbalance=float(currents.sum()+gas_extra.sum())")
 sub("   u=p['basis']@currents\n", "   u=p['basis']@currents\n   if gas_node_load_W is not None:\n    du=np.r_[0.,p['gas_lu'].solve(gas_extra[1:])];du-=p['bweight']@du;u+=du\n")
 sub("nodal=sum((p['tagloads'][z]*q for z,q in loads.items()),np.zeros(len(p['node_ids'])))", "nodal=sum((p['tagloads'][z]*q for z,q in loads.items()),np.zeros(len(p['node_ids'])))+gas_extra")
 sub("   patchvals=p['patch_response']@currents", "   patchvals=np.array([p['tagloads'][z]@u for z in p['taglist']])")
 sub(" spatial=OriginalPlates(legs)\n", " spatial=OriginalPlates(legs)\n gas_operator=SourceP1Gas(GAS_PAIRS,[p['node_ids'] for p in spatial.plates])\n")
 sub("   if reg['gas_pressure_Pa']>0:\n", "   if False:  # old exterior gas disabled; gray radiation retained\n")
 old=" def internal_gas(y):\n  return np.array([interstage_gas(y[2*j],y[2*j+1],g['gap_m'],g['area_m2'],reg['gas_pressure_Pa'])['Q_W'] for j,g in enumerate(gas_spec)])"
 new=" def gas_eval(y):\n  bases=[y[0]-fields[0]['top_minus_bottom_K'],y[1],y[3],y[5]]\n  return gas_operator.evaluate([bases[i]+fields[i]['u'] for i in range(4)],reg['gas_pressure_Pa'],reg['gas_accommodation'])\n def internal_gas(y):\n  return np.array(gas_eval(y)['links_W'])"
 sub(old,new)
 sub("spatial.solve(plus_solder_into_ceramic(init_rows,warm_start_I**2*R_joint),s3,CuJoule,qcu,Qbath,Qa,", "spatial.solve(plus_solder_into_ceramic(init_rows,warm_start_I**2*R_joint,gas_W=previous['internal_interstage_gas_heat_hot_to_cold_W']),s3,CuJoule,qcu,Qbath,Qa,")
 sub("external_ceramic_W=[0.]+[a+b for a,b in zip(previous['cavity_gas_heat_into_three_ceramics_and_die_W'][:3],previous['gray_radiation_heat_into_three_ceramics_and_die_W'][:3])])", "external_ceramic_W=[0.]+[a+b for a,b in zip(previous['cavity_gas_heat_into_three_ceramics_and_die_W'][:3],previous['gray_radiation_heat_into_three_ceramics_and_die_W'][:3])],lead_face_heat_W={int(k):v for k,v in previous['source_power_lead_native_faces_W'].items()})")
 sub("local_fields,new_offsets=spatial.solve(plus_solder_into_ceramic(rows,gas_W=internal_gas(x)),st,CuJoule,qcu,Qbath,Qa,", "local_fields,new_offsets=spatial.solve(plus_solder_into_ceramic(rows),st,CuJoule,qcu,Qbath,Qa,gas_node_load_W=gas_eval(x)['loads'],")
 sub("  max_delta=max(max_offset,max_gaps)", "  max_nodal=max(float(np.max(np.abs(local_fields[i]['u']-fields[i]['u']))) for i in range(4))\n  max_delta=max(max_offset,max_gaps,max_nodal)")
 sub("'ceramic_total_Tdrop_K_max_change':float(max_gaps),", "'ceramic_total_Tdrop_K_max_change':float(max_gaps),'max_nodal_update_K':max_nodal,")
 sub("   fields[i]['top_minus_bottom_K']=fields[i]['top_minus_bottom_K']*(1-relax)+new_gaps[i]*relax", "   fields[i]['top_minus_bottom_K']=fields[i]['top_minus_bottom_K']*(1-relax)+new_gaps[i]*relax\n   fields[i]['u']=fields[i]['u']*(1-relax)+local_fields[i]['u']*relax")
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--seal',action='store_true');p.add_argument('--run',action='store_true');a=p.parse_args();assert a.seal!=a.run
 source=transformed();digest=hashlib.sha256(source.encode()).hexdigest();files=['scripts/tec_nominal_v325_coupled.py','tecooledmct/nominal_gas_p1_coupler_v325.py','tecooledmct/nominal_gas_p1_v325.py','data/nominal_gas_p1_20261111/p1_operator.json','data/nominal_gas_p1_20261111/independent_readback.json','scripts/tec_height_v320_coupled.py','tests/test_nominal_gas_p1_coupler_v325.py']
 contract=D/'coupled_contract.json'
 if a.seal:
  assert not contract.exists();from datetime import datetime,timezone
  v={'observed_UTC':datetime.now(timezone.utc).isoformat(),'executed_source_sha256':digest,'inputs_sha256':{f:sha(R/f) for f in files},'scenario':'original only; selected 752 bare gas columns at 100Pa Kr alpha .8; all other gas surfaces adiabatic; previous gas proxies OFF; existing gray radiation unchanged','full_coupled_attempts':1,'max_wall_s':300,'cpus':4,'memory_GiB':8,'energy_W':1e-8,'power_W':1e-8,'spatial_K':3e-7,'gas_model':'conditional reduced column/Maxwell, not validated complete gas domain'};contract.write_text(json.dumps(v,indent=2)+'\n');(D/'executed_solver.py.source').write_text(source);print('SEALED',digest);return
 c=json.loads(contract.read_text());assert digest==c['executed_source_sha256'] and all(sha(R/f)==h for f,h in c['inputs_sha256'].items());out=D/'coupled_attempt01';out.mkdir(exist_ok=False)
 try:
  obj=json.loads((D/'p1_operator.json').read_text());runtime=types.ModuleType('nominal_v325_executed');runtime.__file__=str(BASE);runtime.SourceP1Gas=SourceP1Gas;runtime.GAS_PAIRS=obj['pairs'];exec(compile(source,str(BASE)+':v325','exec'),runtime.__dict__)
  reg=runtime.expected('copper',1.,1e-6,.4,.002,'Kr',100.);result,arrays=runtime.solve(reg,'nominal')
  ids=[arrays[f'ceramic{i}_source_node_id_1based'] for i in range(4)];temp=[arrays[f'ceramic{i}_temperature_K'] for i in range(4)];g=SourceP1Gas(obj['pairs'],ids).evaluate(temp);assert np.allclose(g['links_W'],result['internal_interstage_gas_heat_hot_to_cold_W'],rtol=0,atol=1e-8)
  assert max(abs(v) for v in result['cavity_gas_heat_into_three_ceramics_and_die_W'])==0
  result.update(status='CONDITIONAL partial-cavity P1 coupled nominal; other gas boundaries adiabatic, not complete cavity',solver_source_sha256=digest,old_gas_proxies='OFF; gray radiation retained',gas_boundary_scope='only 752 source bare-ceramic columns',gas_final_links_W=g['links_W'],gas_entropy_W_K=g['entropy_W_K'],external_enclosure_model='external GAS disabled; gray radiation unchanged',internal_gas_geometry_proxy='752 source-column rectangles, P1 common refinement, 0.600 mm bare-plane gap',source_3D_ceramic_gas_radiation_heat_spread='P1 subface gas nodal loads; radiation retains original pad-weighted approximation',model_version_vs_material_physics='V325 nominal P1 partial-gas only; other gas faces adiabatic; no complete native gas PDE')
  (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');np.savez_compressed(out/'ceramic_fields.npz',**arrays,**{f'ceramic{i}_gas_nodal_load_W':g['loads'][i] for i in range(4)});print('COUPLED_SUCCESS',result['calculated_detector_temperature_K'],result['electrical_power_W'],flush=True)
 except BaseException as e:
  (out/'failure.json').write_text(json.dumps({'status':'STOP','error':repr(e)},indent=2)+'\n');raise
if __name__=='__main__':main()
