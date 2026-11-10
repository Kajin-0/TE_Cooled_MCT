"""Independent incidence-matrix Cu sensitivity reconstruction."""
from pathlib import Path
import json,numpy as np
from tecooledmct.height_coupling_v320 import ORIGINAL,CANDIDATE,read,copper_specs,STAGES
R=Path(__file__).resolve().parents[1];D=R/'data/tec_height_robustness_20261110';data=read(D/'copper_fixed_sensitivity.json');checks=[]
for row in data['cases']:
 case=row['case'];source=read(R/'data/tec_height_coupling_20261110'/case/'result.json');spec=copper_specs(read(ORIGINAL if case=='nominal' else CANDIDATE));I=source['operating_current_A'];stage=np.zeros(3)
 for net,s in spec.items():
  z=source['Cu_form_tab_electrothermal_result']['net_details'][str(net)];T=np.array(z['plate_temperature_K']);L=np.array(s['segments_m']);A=s['cross_section_m2'];Ac=np.array(s['contact_area_m2']);G=385*A/L;Gc=Ac/row['thermal_contact_Rarea_m2K_W'];Re=1e-11/Ac
  if net==88:Re[1]=0
  Rseg=1.724e-8*(1+.0039*((T[:-1]+T[1:])/2-293.15))*L/A;J=I*I*Rseg;S=np.zeros(len(T));S[:-1]+=J/2;S[1:]+=J/2
  B=np.zeros((len(T),len(L)))
  for j in range(len(L)):B[j,j]=1;B[j+1,j]=-1
  K=np.diag(Gc)+(B*G)@B.T;tf=np.linalg.solve(K,Gc*T+S);q=Gc*(tf-T)+I*I*Re
  assert np.max(abs(K-K.T))<1e-14 and np.linalg.eigvalsh(K).min()>0 and abs(sum(q)-I*I*(sum(Rseg)+sum(Re)))<1e-11
  for tag,v in zip(s['faces'],q):stage[STAGES[tag]]+=v
 assert np.allclose(stage,row['stage_heat_W'],atol=1e-12,rtol=0)
 checks.append({'case':case,'thermal_contact_Rarea_m2K_W':row['thermal_contact_Rarea_m2K_W'],'max_stage_diff_W':float(max(abs(stage-row['stage_heat_W'])))})
out={'status':'PASS independent incidence-matrix reconstruction; fixed temperature only','checks':checks};(D/'copper_fixed_independent_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
