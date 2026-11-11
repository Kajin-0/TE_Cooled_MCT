"""Frozen-field Cu-path and hypothetical film resistance diagnostics, no PDE."""
from pathlib import Path
from datetime import datetime,timezone
import json,math,hashlib
from tecooledmct.nominal_cavity_metal_v326 import segment_profile
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_metal_v326_20261111'
def main():
 g=json.loads((D/'face_temperature_graph.json').read_text());r=json.loads((R/'data/nominal_gas_p1_20261111/coupled_attempt01/result.json').read_text());I=r['operating_current_A'];detail=r['Cu_form_tab_electrothermal_result']['net_details'];segments=[]
 for net,n in detail.items():
  for j,(k,res) in enumerate(zip(n['thermal_segment_conductance_W_K'],n['metal_electrical_segment_R_ohm'])):
   T,q0,q1=segment_profile(.5,*n['foil_node_temperature_K'][j:j+2],res,k,I);P=I*I*res;assert abs(q0+q1+P)<1e-14
   segments.append({'net':int(net),'segment':j,'R_ohm':res,'G_W_K':k,'endpoint_temperature_K':n['foil_node_temperature_K'][j:j+2],'joule_W':P,'midpoint_temperature_K':T,'midpoint_joule_rise_K':P/(8*k),'conditional_temperature_bounds_K':[min(n['foil_node_temperature_K'][j:j+2]),max(n['foil_node_temperature_K'][j:j+2])+P/(8*k)],'net_heat_into_conductor_W':[q0,q1],'energy_residual_W':q0+q1+P})
 # Stated engineering range, not measured film/contact properties.
 k=[200.,385.,400.];t=15e-6;flux=1000.;film=[{'k_W_mK':x,'thickness_m':t,'thermal_resistance_area_m2K_W':t/x,'assumed_normal_flux_W_m2':flux,'temperature_drop_K':flux*t/x} for x in k]
 sizes={key:val for key,val in g['groups'].items()};q={'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS 1D analytic reconstruction; supplemental gas geometry STOP, no full solve','face_status':sizes,'segments':segments,'film_assumption':'15um Cu only; k=200-400 W/mK assumed illustrative, q=1000 W/m2 selected, no metal-ceramic contact resistance or lateral spreading included','film':film,'total_qualified_gas_boundary_area_mm2':0,'P1_paired_area_mm2':29.810036281777183,'new_supplemental_gas_pairs':0,'new_coupled_solves':0,'gas_path_stop':'source-face centroid alone does not establish a finite co-facing area, blocking-free straight columns, or disjointness from existing 752 cells; broad tab faces cannot be projected as local points. No new thermal exchange assigned.','old_raw_gate':'3D electrical and raw gas FAIL/STOP unchanged'};p=D/'conditional_metal_physics.json';assert not p.exists();p.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
if __name__=='__main__':main()
