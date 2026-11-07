#!/usr/bin/env python3
"""Read-only fixed-field independent conservation audit for original CAD first couple.

Reassembles source mesh and bulk/interface operators at SAVED V/T values
but never performs a PDE solve or changes the registered material/BC.
Tests charge conservation by region, independent physical electric-work
and TEC-side plus cold-side total energy reaction. Historical raw
one-sided gradients are explicitly a separate FAILED acceptance test.
"""
from pathlib import Path
import argparse,json,hashlib,numpy as np
from scripts.v3_first_couple_coupled_3d import Assembly,IDS,CONTACT_TAGS,HOT_TAGS,COLD_TAG,PORT_TAGS
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/v3_first_couple_coupled_20261107/attempt04'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit():
 reg=read(BASE/'registration.json');saved=read(BASE/'result.json')
 assert saved['script_SHA256']==reg['script_SHA256']
 a=Assembly(reg)
 V=np.asarray(saved['field_potential_V'],float)
 T=np.asarray(saved['field_temperature_K'],float)
 assert V.shape==T.shape==(a.ndof,)
 assert np.array_equal(np.asarray(saved['field_region_and_original_global_node'],dtype=int),a.trace)
 assert abs(V[a.gauge])<1e-14
 assert max(abs(T[i]-v) for i,v in a.fixed_temp.items())<1e-12
 assert len(a.contact)==112
 sigma,k,S,te=a.fields(T)
 J,gV,gT=a.current(V,T,sigma,S)
 # Electrical weak residual WITHOUT invoking an electrical solve.
 gb=np.einsum('ei,eij->ej',T[a.dof],a.grad)
 btherm=a.accumulate_cells(a.volume[:,None]*
  np.einsum('eia,ea->ei',a.grad,np.einsum('eab,eb->ea',sigma,S[:,None]*gb)))
 A=a.bulk(sigma)+a.Kce
 er=A@V-(a.source_load(reg['current_A'])-btherm)
 electric_max=float(np.max(abs(er[a.vfree])))
 assert electric_max<reg['electrical_residual_gate_A']
 # Exact face contact integral for LINEAR independent material traces;
 # use CAD native fixed owner order, not tetra iteration sign.
 weak={}
 joule=0.
 for tag in CONTACT_TAGS:
  q=0.
  for f in a.faces_by_tag[tag]:
   jump=V[f['da']]-V[f['db']]
   jn=float(f['area']/3*jump.sum()/reg['r_e_ohm_m2'])
   q+=jn
   # Exact integral quadratic P1 jump² over original TRI3.
   M=f['area']/12*(np.ones((3,3))+np.eye(3))
   joule+=float(jump@(M@jump)/reg['r_e_ohm_m2'])
  weak[str(tag)]=q
 weakerr=max(abs(abs(q)-reg['current_A'])/reg['current_A'] for q in weak.values())
 assert weakerr<reg['weak_interface_series_current_relative_gate']
 ohm=float(np.sum(a.volume*np.einsum('ei,eij,ej->e',J,np.linalg.inv(sigma),J)))
 seeb=float(np.sum(a.volume*S*np.einsum('ei,ei->e',J,gT)))
 # Reconstruct boundary electrical work independently from saved traces.
 portmeans={}
 for tag in PORT_TAGS:
  portmeans[str(tag)]=float(sum(f['area']*V[f['da']].mean()
    for f in a.faces_by_tag[tag])/a.port_areas[tag])
 IV=reg['current_A']*(portmeans['1531']-portmeans['162'])
 powererr=abs((ohm+seeb+joule)-IV)/abs(IV)
 assert powererr<reg['independent_electrical_work_relative_gate']
 # Reassemble total-energy finite-trace operator and reaction; NO solve.
 K=a.bulk(k)+a.Kct
 br,pcontact,pboundary=a.energy_rhs(V,T,J,S)
 energyres=K@T-br
 maxfree=float(np.max(abs(energyres[a.free])))
 hotidx=set(int(i) for tag in HOT_TAGS for f in a.faces_by_tag[tag] for i in f['da'])
 coldidx=set(int(i) for f in a.faces_by_tag[COLD_TAG] for i in f['da'])
 Qhot=float(np.sum((br-K@T)[list(hotidx)]))
 Qcold=float(np.sum((br-K@T)[list(coldidx)]))
 energyerr=abs(Qhot+Qcold-IV)/abs(IV)
 assert maxfree<reg['energy_residual_gate_W']
 assert energyerr<reg['energy_global_gate_relative']
 assert abs(pcontact-joule)<1e-12
 assert abs(-pboundary-IV)<1e-12
 assert abs(Qhot-saved['total_energy_thermal_reaction_hot_W'])<1e-12
 assert abs(Qcold-saved['total_energy_thermal_reaction_cold_W'])<1e-12
 assert abs(ohm-saved['bulk_positive_Joule_power_W'])<1e-12
 assert abs(seeb-saved['bulk_signed_Seebeck_conversion_work_W'])<1e-12
 assert abs(joule-saved['interface_electrical_Joule_power_W'])<1e-12
 # Independently reconstruct original raw gradient contact currents
 # and retain unqualified giant interface mismatch.
 raw=[]
 for tag in CONTACT_TAGS:
  aout=bout=0.
  for f in a.faces_by_tag[tag]:
   tri=f['global_nodes'];p=a.xyz[tri]
   na=np.cross(p[1]-p[0],p[2]-p[0])*.5
   e0,e1=f['owner_elements']
   if float(na@(p.mean(0)-a.coord[e0].mean(0)))<0:na=-na
   aout+=float(J[e0]@na)
   bout+=float(J[e1]@(-na))
  q=weak[str(tag)]
  mismatch=max(abs(aout-q),abs(bout+q))/reg['current_A']
  raw.append({'source_tag':tag,'native_weak_contact_current_A':q,
    'raw_side0_A':aout,'raw_side1_A':bout,
    'raw_vs_weak_fraction':mismatch,'raw_0p1pct_FAIL':mismatch>.001})
 assert all(row['raw_0p1pct_FAIL'] for row in raw)
 assert abs(max(row['raw_vs_weak_fraction'] for row in raw)-saved['worst_native_raw_current_discrepancy_fraction'])<1e-9
 assert saved['original_historical_Gate_B']=='FAIL/STOP'
 return {
  'status':'INDEPENDENT SAVED-FIELD weak charge, electrical work, full energy PASS; original native raw one-sided gradient FAIL 8/8',
  'audited_source_3D_CAD_region_volumes':list(IDS),
  'original_mesh_tetrahedra':len(a.cells),
  'region_disjoint_trace_DOF_each_field':a.ndof,
  'native_112_TRI3_contacts':len(a.contact),
  'current_A':reg['current_A'],
  'weak_native_per_contact_A':weak,
  'weak_series_worst_rel_error':weakerr,
  'electric_free_weak_node_max_residual_A':electric_max,
  'bulk_electrical_ohmic_W':ohm,
  'bulk_signed_Seebeck_work_W':seeb,
  'all_eight_interface_Joule_W':joule,
  'independent_terminal_IV_W':IV,
  'independent_electric_work_relative_error':powererr,
  'hot_temperature_fixed_port_energy_reaction_W':Qhot,
  'cold_temperature_fixed_port_energy_reaction_W':Qcold,
  'total_energy_relative_error':energyerr,
  'energy_free_node_max_residual_W':maxfree,
  'native_contact_raw_flux_cut_rows':raw,
  'raw_original_contact_gate_0p1pct_PASS':False,
  'raw_original_contact_faces_failed':sum(x['raw_0p1pct_FAIL'] for x in raw),
  'historical_original_P1_Gate_B':'FAIL/STOP',
  'as_built_transport_and_contact_laws':'UNRELEASED',
  'full_430_domain_C_D':'NOT RUN',
  'new_numerical_PDE_solves':0,
  'geometry_or_saved_solution_modified':False,
  'registered_result_SHA256':sha(BASE/'result.json'),
  'registration_SHA256':sha(BASE/'registration.json'),
  'reused_original_source_mesh_sha256':reg['source_original_mesh_SHA256']
 }
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 a=p.parse_args();j=audit()
 if a.verify_only:
  z=read(a.out)
  assert j==z
 else:
  assert not a.out.exists()
  a.out.write_text(json.dumps(j,indent=2)+'\n')
 print('3D_COUPLE_SAVED_FIELD_AUDIT',json.dumps({
  k:j[k] for k in ('status','independent_electric_work_relative_error',
 'total_energy_relative_error','weak_series_worst_rel_error',
 'raw_original_contact_faces_failed','new_numerical_PDE_solves')},indent=2))
if __name__=='__main__':main()
