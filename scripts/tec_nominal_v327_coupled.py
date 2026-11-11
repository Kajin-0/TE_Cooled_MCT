"""One original-only die-window P1 partial-gas coupled solve, if preflight passes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,types,numpy as np
from scripts.tec_nominal_v325_coupled import transformed as base_source
from tecooledmct.nominal_gas_p1_coupler_v325 import SourceP1Gas
from tecooledmct.nominal_gas_visibility_v327 import die_window_exchange
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_visibility_v327_20261111';BASE=R/'scripts/tec_height_v320_coupled.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def transformed():
 s=base_source();old='  return qgas,qrad,area,g_conductance';assert s.count(old)==1
 new="  extra=die_window_exchange(reg['ambient_K'],float(temps[7]),DIE_WINDOW_AREA_MM2,DIE_WINDOW_GAP_M,reg['gas_pressure_Pa'],reg['gas_accommodation'])\n  qgas[3]=extra['die_load_W'];g_conductance[3]=extra['conductance_W_K']\n  return qgas,qrad,area,g_conductance"
 return s.replace(old,new)
def main():
 p=argparse.ArgumentParser();p.add_argument('--seal',action='store_true');p.add_argument('--run',action='store_true');a=p.parse_args();assert a.seal!=a.run;src=transformed();digest=hashlib.sha256(src.encode()).hexdigest();files=['scripts/tec_nominal_v327_coupled.py','scripts/tec_nominal_v325_coupled.py','tecooledmct/nominal_gas_visibility_v327.py','data/nominal_gas_visibility_v327_20261111/die_window_visibility.json','data/nominal_gas_visibility_v327_20261111/independent_readback.json','data/nominal_gas_p1_20261111/p1_operator.json','data/nominal_gas_visibility_v327_20261111/focused_tests_initial.log'];contract=D/'coupled_contract.json'
 if a.seal:
  assert not contract.exists();v={'observed_utc':datetime.now(timezone.utc).isoformat(),'executed_source_sha256':digest,'inputs_sha256':{f:sha(R/f) for f in files},'scenario':'nominal original only; V325 752 ceramic P1 patches PLUS geometric die/window 2335/2410 area; 300K window assumption; all other gas surfaces adiabatic; old gas proxies OFF; unchanged gray radiation','physical_scope':'Maxwell jump columns not full gas physics or device validation','attempts':1,'limit':'300s 4CPU 8GiB','gates':'source visibility, P1 and port/gas/global balance <1e-8 W, max spatial update <1e-6 K, matched input power 1e-8 W'};contract.write_text(json.dumps(v,indent=2)+'\n');(D/'executed_solver.py.source').write_text(src);print('SEALED',digest);return
 c=json.loads(contract.read_text());assert sha(D/'executed_solver.py.source')==digest==c['executed_source_sha256'] and all(sha(R/f)==h for f,h in c['inputs_sha256'].items());geom=json.loads((D/'die_window_visibility.json').read_text());ind=json.loads((D/'independent_readback.json').read_text());assert ind['source_visibility_sha256']==sha(D/'die_window_visibility.json') and ind['status'].startswith('PASS') and geom['V325_face_ids_disjoint'] and '27 passed' in (D/'focused_tests_initial.log').read_text();out=D/'coupled_attempt01';out.mkdir(exist_ok=False)
 try:
  p1=json.loads((R/'data/nominal_gas_p1_20261111/p1_operator.json').read_text());runtime=types.ModuleType('nominal_v327_executed');runtime.__file__=str(BASE);runtime.SourceP1Gas=SourceP1Gas;runtime.GAS_PAIRS=p1['pairs'];runtime.die_window_exchange=die_window_exchange;runtime.DIE_WINDOW_AREA_MM2=geom['paired_area_mm2'];runtime.DIE_WINDOW_GAP_M=geom['gap_mm']*1e-3;exec(compile(src,str(BASE)+':v327','exec'),runtime.__dict__)
  reg=runtime.expected('copper',1.,1e-6,.4,.002,'Kr',100.);result,arrays=runtime.solve(reg,'nominal');ids=[arrays[f'ceramic{i}_source_node_id_1based'] for i in range(4)];temp=[arrays[f'ceramic{i}_temperature_K'] for i in range(4)];g=SourceP1Gas(p1['pairs'],ids).evaluate(temp);extra=die_window_exchange(300.,result['calculated_detector_temperature_K'],geom['paired_area_mm2'],geom['gap_mm']*1e-3,100.,.8);q=result['cavity_gas_heat_into_three_ceramics_and_die_W'];assert max(abs(x) for x in q[:3])==0 and abs(q[3]-extra['die_load_W'])<1e-12 and abs(sum(g['loads'][i].sum() for i in range(4)))<1e-12
  result.update(status='CONDITIONAL original-only P1 ceramic + die/window gas subset; all other gas surfaces adiabatic',solver_source_sha256=digest,old_gas_proxies='OFF; gray radiation retained',gas_boundary_scope='752 ceramic columns plus source TRI3 die/window direct columns; other gas surfaces adiabatic',die_window_gas=extra,die_window_visibility_sha256=sha(D/'die_window_visibility.json'),gas_final_links_W=g['links_W'],gas_entropy_W_K=g['entropy_W_K'],external_enclosure_model='source die/window subset and unchanged gray radiation; all remaining gas boundaries adiabatic')
  (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');np.savez_compressed(out/'ceramic_fields.npz',**arrays,**{f'ceramic{i}_gas_nodal_load_W':g['loads'][i] for i in range(4)});print('COUPLED_SUCCESS',result['calculated_detector_temperature_K'],result['electrical_power_W'],extra['die_load_W'],flush=True)
 except BaseException as e:
  (out/'failure.json').write_text(json.dumps({'status':'STOP','error':repr(e)},indent=2)+'\n');raise
if __name__=='__main__':main()
