#!/usr/bin/env python3
"""V2 first actual-source-geometry spatial-thermal / nonlinear TE hybrid.

One registered .4A operating point, same original 29/11/4 device as V1.
Four ORIGINAL CAD ceramic volumes (11,791 real R3.9 tetrahedra) supply
exact P1 Neumann source-pad thermal spreading operators; the source-
trusted 1D nonlinear TE stages are solved simultaneously with the
eight distinct ceramic-face and detector temperature unknowns.
Coarse scalar header+TIM and radiator remain from V1, original source
Cu/Au leads and die attach unchanged. No full 430-domain E/T FEM.

IMPORTANT: This is genuine two-way *lumped boundary/3D spatial*
coupling (not four detached maps), but no fully spatial P/N J field.
"""
from pathlib import Path
import argparse,json,hashlib,time
import numpy as np
from scipy.optimize import least_squares
from tecooledmct.nonlinear_tec import Transport
from scripts.v3_r3_sink_wire_sensitivity import geometry as original_geometry

ROOT=Path(__file__).resolve().parents[1]
V1=ROOT/'data/v1_integrated_full_package_20261107/attempt01/result.json'
CER=ROOT/'data/v2_integrated_spatial_20261107/attempt01/ceramic_spatial_operators.json'
CPROFILE=ROOT/'data/v2_integrated_spatial_20261107/attempt01/ceramic_spatial_profiles.npz'
CER_REG=ROOT/'data/v2_integrated_spatial_20261107/attempt01/ceramic_registration.json'
TIM=ROOT/'data/v3_header_tim_robin_20261107/attempt01/result.json'
SOLDER=ROOT/'data/v3_hot_mount_readiness_20261107/attempt01/thermal_path_audit.json'
FILES={
 'V1_result':V1,'ceramic_3D_operators':CER,
 'ceramic_3D_unit_profiles':CPROFILE,
 'ceramic_registration':CER_REG,
 'source_3D_header_and_TIM':TIM,
 'source_solder_bulk':SOLDER,
 'existing_nonlinear_solver':ROOT/'tecooledmct/nonlinear_tec.py',
 'existing_graded_source':ROOT/'tecooledmct/graded_tec.py',
 'source_geometry_helper':ROOT/'scripts/v3_r3_sink_wire_sensitivity.py',
 'source_base_geometry_helper':ROOT/'scripts/v3_reference_29114_reduced_study.py',
 'source_integrated_heat_paths':ROOT/'tecooledmct/integrated_reference.py',
 'source_original_CAD':ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json',
 'original_source_430_domain_register':ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json',
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def expected_reg():
 v1=read(V1);cer=read(CER);header=read(TIM);solder=read(SOLDER)
 R=[x['spatial_T_top_minus_bottom_per_unit_heat_K_W'] for x in cer['source_3D_ceramic_regions']]
 ext=header['radiator_plus_header_plus_TIM_effective_R_K_W']+solder['solder_1D_R_hypothesis_K_W']
 return {
  'milestone':'V2 first original-source spatial plates + unchanged 29/11/4 non-linear TEC and complete 300K ambient/detector path',
  'parent_git_commit':'350d8c60f6accaa7acdacb64b4783e6e7e01ddd0',
  'source_stage_couples':[29,11,4],
  'current_A':.4,'ambient_and_pin_reservoir_K':300.,
  'die_load_W':.002,'optical_load_W':0.,'source_die_attach_k_W_mK':1.,
  'source_nonlinear_PN':'Zhang P-HE/N-HE-1 unmatched research analog nominal 32 axial intervals; >300K engineering extension flagged',
  'source_ceramic_P1_original_regions':[1,2,3,4],
  'original_ceramic_cell_count':11791,
  'ceramic_spatial_R_K_W':R,
  'external_hot_path_without_ceramic0_R_K_W':ext,
  'ceramic_thickness_and_3D_patches':'native R3.9 mesh and original metal contact areas, uniform patch Neumann traction, 30 W/mK constant alumina analog',
  'thermal_Neumann_1W_normalization':'each plate top+1W and bottom-1W, all other boundaries insulated, one gauge fixed; zero bottom area-mean',
  'spatial_coupling':'nonlinear stage heat flux -> 3D ceramic effective R -> distinct junction boundary temperatures -> new nonlinear stage heat flux until fixed point; reconstruct all four original-geometry temperature fields',
  'boundary_copper_lead':'existing Cu thermal bath shunt and half Joule from V1 unchanged, net ceramic0 top heat approximated as bath rejected power, not individual pad resolved metal Joule',
  'boundary_detector':'die conduction through 20um 1mm2 epoxy plus Au wire leak from 300K, cold ceramic3 resolved spreading',
  'cavity_gas_and_radiation':'OFF, same as V1',
  'mesh_convergence':'NOT RUN; single original mesh',
  'as_built_material_grade_and_contact_measurements':'UNAVAILABLE',
  'solve_tolerances':{'max_node_energy_W':1e-8,'max_stage_energy_W':1e-9,
                       'max_interface_T_K':1e-7,'global_energy_W':1e-8},
  'original_B':'FAIL/STOP','new_first_pair_P1_raw_cut':'FAIL 8/8','full_430_C_D':'NOT RUN',
  'source_sha256':{k:sha(p) for k,p in FILES.items()},
  'script_sha256':sha(Path(__file__)),
  'one_operating_point_only':True
 }

def solve_case(reg):
 assert reg==expected_reg()
 start=time.monotonic()
 v1=read(V1)
 cer=read(CER)
 R=np.array(reg['ceramic_spatial_R_K_W'])
 assert len(R)==4 and min(R)>0
 geo=original_geometry()
 assert [v['couples'] for v in geo['stages']]==[29,11,4]
 cu=[a for a in geo['wires'] if a['material']=='Cu']
 au=[a for a in geo['wires'] if a['material']=='Au']
 assert len(cu)==len(au)==2
 Gcu=sum(a['G_W_K'] for a in cu)
 Rau=sum(a['R_ohm'] for a in cu)
 Gau=sum(a['G_W_K'] for a in au)
 ambient=reg['ambient_and_pin_reservoir_K']
 I=reg['current_A']
 Rext=reg['external_hot_path_without_ceramic0_R_K_W']
 die_attach=geo['die_attach_thickness_over_area_m_inverse']/reg['source_die_attach_k_W_mK']
 assert abs(die_attach-20)<1e-10
 transport=Transport(32)
 # 8 independent contact temperatures:
 # [cer0 top = stage0 hot, cer1 bottom=stage0 cold,
 # cer1 top=stage1 hot, cer2 bottom=stage1 cold,
 # cer2 top=stage2 hot, cer3 bottom=stage2 cold,
 # cer3 top = cold carrier, die]
 old=v1['predicted_all_five_thermal_nodes_K']
 Q0=v1['stage_heat_current_and_power_budgets'][1]['qh_w']
 Q1=v1['stage_heat_current_and_power_budgets'][2]['qh_w']
 Q2=v1['detector_die_attach_heat_to_cold_stage_W']
 x0=np.array([old['hot_ceramic'],
 old['stage1'],old['stage1']+R[1]*Q0,
 old['stage2'],old['stage2']+R[2]*Q1,
 old['cold_ceramic'],old['cold_ceramic']+R[3]*Q2,
 old['MCT_die']+R[3]*Q2],float)
 def physical(x):
  h0,c0,h1,c1,h2,c2,carrier,die=map(float,x)
  st=[transport.stage(g,th,tc,I) for g,th,tc in zip(geo['stages'],
          (h0,h1,h2),(c0,c1,c2))]
  # Die-to-carrier attach heat and Au wire parasitic independently.
  Qa=(die-carrier)/die_attach
  Qd=reg['die_load_W']+Gau*(ambient-die)
  # Cu lead conduction from ambient to hot stage + half of lead Joule;
  # negative if hot stage > ambient and power lead cools the hot ceramic.
  q_cu=Gcu*(ambient-h0)
  CuJoule=I*I*Rau
  Qbath=st[0]['qh_w']+q_cu+.5*CuJoule
  return st,Qa,Qd,Qbath,q_cu,CuJoule
 # W constraints are rescaled only to improve least_squares solver
 # condition; final checks use physical W and K, unscaled.
 def physical_residual(x):
  st,Qa,Qd,Qbath,_,_=physical(x)
  return np.array([
   st[0]['qc_w']-st[1]['qh_w'],
   x[2]-x[1]-R[1]*st[1]['qh_w'],
   st[1]['qc_w']-st[2]['qh_w'],
   x[4]-x[3]-R[2]*st[2]['qh_w'],
   st[2]['qc_w']-Qa,
   x[6]-x[5]-R[3]*Qa,
   Qa-Qd,
   x[0]-ambient-(Rext+R[0])*Qbath])
 scale=np.array([10.,.1,10.,.1,100.,.1,100.,.5])
 fit=least_squares(lambda x:scale*physical_residual(x),x0,
   bounds=(np.full(8,180.00001),np.full(8,389.99999)),
   x_scale=np.array([10.]*8),
   max_nfev=80,ftol=1e-12,xtol=1e-12,gtol=1e-12)
 if not fit.success:
  raise RuntimeError('V2 did not converge '+str(fit.message))
 x=fit.x
 st,Qa,Qd,Qbath,q_cu,CuJoule=physical(x)
 residual=physical_residual(x)
 assert np.isfinite(x).all()
 assert max(abs(residual[[0,2,4,6]]))<reg['solve_tolerances']['max_node_energy_W'],('node balance',residual)
 assert max(abs(residual[[1,3,5,7]]))<reg['solve_tolerances']['max_interface_T_K'],('temperature',residual)
 assert max(abs(a['energy_residual_w']) for a in st)<reg['solve_tolerances']['max_stage_energy_W']
 assert min(x)>180 and max(x)<390
 assert Qbath>0
 volt=sum(a['voltage_v'] for a in st)+I*Rau
 termP=I*volt
 # Original V1 global accounting with zero extra gas/radiation:
 # P_term + Q_detector + Au leak + (Cu reservoir into hot -0.5 CuJoule)
 # -Qbath must be zero.
 reservoir_cu=q_cu-.5*CuJoule
 global_error=termP+reg['die_load_W']+Gau*(ambient-x[7])+reservoir_cu-Qbath
 assert abs(global_error)<reg['solve_tolerances']['global_energy_W'],('global energy',global_error)
 assert abs(termP-I*volt)<1e-12
 assert any(a['high_T_assumption_applied'] for a in st)
 Qplates=[Qbath,st[1]['qh_w'],st[2]['qh_w'],Qa]
 bottom_means=[x[0]-R[0]*Qbath,x[1],x[3],x[5]]
 top_means=[x[0],x[2],x[4],x[6]]
 # Verify each original source face flux pressure response gives the
 # same signed contact mean at the independently solved TE junctions.
 for i in range(4):
  assert abs(bottom_means[i]+R[i]*Qplates[i]-top_means[i])<1e-7
 from numpy.lib.npyio import NpzFile
 profiles=np.load(CPROFILE,allow_pickle=False)
 arrays={}
 spans=[]
 for i,source in enumerate(cer['source_3D_ceramic_regions']):
  stem=f'ceramic{i}'
  ids=profiles[stem+'_source_global_node_id_1based']
  rel=profiles[stem+'_temperature_delta_over_bottom_mean_K_per_W']
  xyz=profiles[stem+'_source_xyz_mm']
  absolute=bottom_means[i]+Qplates[i]*rel
  assert abs(absolute.max()-absolute.min())<50
  arrays[stem+'_source_global_node_id_1based']=ids
  arrays[stem+'_xyz_mm']=xyz
  arrays[stem+'_absolute_temperature_K']=absolute
  spans.append({'source_original_ceramic_id':i+1,
   'source_tets':source['original_tets'],'source_nodes':source['source_nodes'],
   'through_ceramic_heat_W':float(Qplates[i]),
   'bottom_patch_area_mean_T_K':float(bottom_means[i]),
   'top_patch_area_mean_T_K':float(top_means[i]),
   'spatial_min_node_T_K':float(absolute.min()),
   'spatial_max_node_T_K':float(absolute.max()),
   'observed_max_min_T_spread_K':float(np.ptp(absolute)),
   'source_3D_operator_R_K_W':float(R[i]),
   'numerical_spatial_boundary_mean_residual_K':
    float((bottom_means[i]+R[i]*Qplates[i])-top_means[i])})
 profiles.close()
 names=['TEC_hot_contact','stage0_cold_ceramic1_lower','stage1_hot_ceramic1_upper',
        'stage1_cold_ceramic2_lower','stage2_hot_ceramic2_upper',
        'stage2_cold_ceramic3_lower','carrier_ceramic3_upper','HgCdTe_die']
 result={
  'status':'V2 COARSE SOURCE-GEOMETRY SPATIAL CERAMICS + NONLINEAR TEC TWO-WAY HYBRID ONE CASE: NUMERICAL PASS, PHYSICAL UNQUALIFIED',
  'original_mesh_total_ceramic_tets':sum(p['source_tets'] for p in spans),
  'source_original_3D_ceramic_count':4,
  'original_source_stage_couples':[29,11,4],
  'source_current_A':I,
  'temperature_interface_nodes_K':dict(zip(names,map(float,x))),
  'full_detector_die_temperature_K':float(x[7]),
  'terminal_voltage_V':float(volt),
  'terminal_electrical_power_W':float(termP),
  'stage_temperature_boundary_pairs_K':[[float(x[2*i]),float(x[2*i+1])] for i in range(3)],
  'stage_budget':st,
  'source_original_four_ceramics_spatial_summaries':spans,
  'source_four_ceramic_heat_W':Qplates,
  'detector_assumed_bias_heat_W':reg['die_load_W'],
  'source_Au_bond_leak_heat_to_die_W':float(Gau*(ambient-x[7])),
  'detector_to_carrier_die_attach_W':float(Qa),
  'bath_sink_rejected_heat_W':float(Qbath),
  'hot_external_R_without_ceramic0_K_W':Rext,
  'hot_full_spatial_effective_R_K_W':float(Rext+R[0]),
  'thermal_reservoir_cu_heat_W':float(reservoir_cu),
  'Cu_lead_total_Joule_W':float(CuJoule),
  'max_unscaled_interstage_energy_residual_W':float(max(abs(residual[[0,2,4,6]]))),
  'max_unscaled_interface_temperature_residual_K':float(max(abs(residual[[1,3,5,7]]))),
  'max_stage_energy_residual_W':float(max(abs(a['energy_residual_w']) for a in st)),
  'global_energy_accounting_residual_W':float(global_error),
  'optimizer_iterations':int(fit.nfev),
  'optimizer_success':bool(fit.success),
  'spatial_ceramic_all_four_original_mesh_temperature_fields':'spatial_3D_ceramics_at_V2_point.npz',
  'source_transport_above_300K_assumed':True,
  'source_transport_temperature_domain_K':[40,300],
  'V1_same_0p4A_comparison':{
   'V1_die_K':v1['predicted_all_five_thermal_nodes_K']['MCT_die'],
   'V1_terminal_voltage_V':v1['terminal_voltage_V'],
   'V1_terminal_electrical_power_W':v1['terminal_electrical_input_W'],
   'V1_bath_W':v1['total_bath_heat_rejected_W'],
   'V2_minus_V1_die_K':float(x[7]-v1['predicted_all_five_thermal_nodes_K']['MCT_die']),
   'V2_minus_V1_terminal_voltage_V':float(volt-v1['terminal_voltage_V']),
   'V2_minus_V1_ambient_heat_W':float(Qbath-v1['total_bath_heat_rejected_W'])},
  'original_gate_B':'FAIL/STOP',
  'first_3D_pair_raw_gradient_contact_gate':'FAIL 8/8',
  'full_original_430_domain_C_D':'NOT RUN',
  'true_as_built_device_validated':False,
  'actual_four_3D_ceramic_domain_material_grade':'UNKNOWN',
  'model_is_all_430_regions_spatial_electrothermal':False,
  'original_CAD_and_mesh_mutated':False,
  'source_input_SHA256':reg['source_sha256'],
  'solver_sha256':reg['script_sha256'],
  'run_wall_time_s':time.monotonic()-start
 }
 return result,arrays
def main():
 a=argparse.ArgumentParser()
 a.add_argument('--registration',type=Path,required=True)
 a.add_argument('--outdir',type=Path,required=True)
 o=a.parse_args();reg=read(o.registration)
 assert reg['script_sha256']==sha(Path(__file__))
 assert reg['one_operating_point_only']
 r,arrays=solve_case(reg)
 assert not (o.outdir/'v2_integrated_result.json').exists()
 assert not (o.outdir/'spatial_3D_ceramics_at_V2_point.npz').exists()
 (o.outdir/'v2_integrated_result.json').write_text(json.dumps(r,indent=2)+'\n')
 np.savez_compressed(o.outdir/'spatial_3D_ceramics_at_V2_point.npz',**arrays)
 print('V2_INTEGRATED_RUNNING',json.dumps({
  k:r[k] for k in ('status','full_detector_die_temperature_K','terminal_voltage_V',
   'terminal_electrical_power_W','bath_sink_rejected_heat_W',
   'hot_full_spatial_effective_R_K_W','max_unscaled_interstage_energy_residual_W',
   'max_unscaled_interface_temperature_residual_K',
   'global_energy_accounting_residual_W','optimizer_iterations','run_wall_time_s')},indent=2))
 print('V2_VS_V1',r['V1_same_0p4A_comparison'])
if __name__=='__main__':main()
