"""Derive original source columns and evaluate on saved nominal solver states."""
from pathlib import Path
import json,hashlib
from tecooledmct.nominal_gas_v324 import columns,stage_loads
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_gas_coupler_20261110'
def read(p):return json.loads(p.read_text())
def main():
 reg=read(D/'registration.json')
 for f,h in reg['source_sha256'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h,f
 design=read(R/'data/synthetic_v3_assembly_20261102/source_final/design.json');faces=read(R/'data/nominal_cavity_ports_20261110/nominal_gas_face_ports.json')['faces'];base=read(R/'data/tec_height_coupling_20261110/nominal/result.json');patches=[]
 for stage in range(3):
  p=columns(design,stage)
  for key,name,z in [('hot_gas_face_tag',f'ceramic{stage}',p['z0_mm']),('cold_gas_face_tag',f'ceramic{stage+1}',p['z1_mm'])]:
   found=[f['face_tag'] for f in faces if f['solid_domain']==name and abs(f['centre_mm'][2]-z)<1e-6 and f['cad_surface_type']=='Plane' and abs(f['bbox_mm'][5]-f['bbox_mm'][2])<1e-5];assert len(found)==1,(name,found);p[key]=found[0]
  patches.append(p)
 n=base['source_full_temperature_nodes_K'];temps=[(n[f'stage{j}_hot'],n[f'stage{j}_cold']) for j in range(3)];results={}
 for alpha in (.5,.8,1.):
  loads,q=stage_loads(temps,patches,100.,alpha);results[str(alpha)]={'stage_loads_W':loads,'links':q,'net_W':sum(loads)}
 out={'status':'CONDITIONAL unobstructed bare-face gas subset at saved source stage temperatures; not a solved full gas field, physical lower bound or new detector temperature','source_result_sha256':hashlib.sha256((R/'data/tec_height_coupling_20261110/nominal/result.json').read_bytes()).hexdigest(),'patches':patches,'temperatures_K':temps,'pressure_Pa':100.,'results':results,'excluded_paths':'all other cavity surfaces adiabatic for this subset diagnostic only; existing package external and interstage proxies NOT replaced; not a total gas prediction'}
 p=D/'source_bare_column_subset.json';assert not p.exists();p.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
 print('areas mm2',[x['unobstructed_column_area_mm2'] for x in patches]);print('cells',[len(x['cells_xy_mm']) for x in patches]);print('tags',[(x['hot_gas_face_tag'],x['cold_gas_face_tag']) for x in patches]);print('alpha 0.8 W',[x['Q_hot_to_cold_W'] for x in results['0.8']['links']]);print('stage loads',results['0.8']['stage_loads_W'])
if __name__=='__main__':main()
