"""Hard-sphere Kr screening, not a validated rarefied gas solution."""
from pathlib import Path
import json,math,shutil
from tecooledmct.integrated_reference import Scenario,gas_transport
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_ports_20261110';KB=1.380649e-23

def mean_free_path(T,p,d):
 if not all(math.isfinite(x) and x>0 for x in (T,p,d)):raise ValueError('T, p, d must be positive finite')
 return KB*T/(math.sqrt(2)*math.pi*d*d*p)
def ra(T,p,L,dt):
 # Ideal Kr, Eucken mu and NIST-derived k; formal continuum screening only.
 if min(T,p,L,dt)<=0:raise ValueError('invalid positive inputs')
 Rgas=99.218;gamma=5/3;cp=gamma/(gamma-1)*Rgas
 k,_,_=gas_transport(Scenario(gas='Kr',cavity_pressure_pa=p),T);mu=k/(cp+1.25*Rgas);rho=p/(Rgas*T);nu=mu/rho;alpha=k/(rho*cp)
 return {'Ra':9.81/T*dt*L**3/(nu*alpha),'k_W_mK':k,'mu_Pas':mu,'rho_kg_m3':rho,'nu_m2_s':nu,'alpha_m2_s':alpha}
def main():
 p=D/'regime.json';assert not p.exists();rows=[]
 for pressure in (100.,1000.,30000.,101325.):
  for L in (.00018,.00057,.003,.0142):
   values=[mean_free_path(t,pressure,d)/L for t in (200.,300.) for d in (.34e-9,.40e-9)]
   rows.append({'pressure_Pa':pressure,'length_m':L,'Kn_at_250K_d036nm':mean_free_path(250,pressure,.36e-9)/L,'Kn_bounded_200_300K_d034_040nm':[min(values),max(values)]})
 out={'status':'engineering screening only; no CFD and no rarefied-flow solution','diameter_assumption_m':.36e-9,'diameter_interpretation':'hard-sphere effective diameter, inferred from published kinetic-diameter scale; not a measured Kr-Kr scattering cross-section','source':'https://www.osti.gov/servlets/purl/1356958','temperature_assumption_K':[200,300],'diameter_scenario_m':[.34e-9,.40e-9],'hard_sphere_mean_free_path_at_250K_100Pa_m':mean_free_path(250,100,.36e-9),'knudsen_rows':rows,'rayleigh_at_101325Pa_250K_80K_delta':{str(L):ra(250,101325,L,80) for L in (.00057,.003)},'rayleigh_scope':'illustrative continuum screening at 101325Pa, 80K imposed scale and ideal properties; not valid for 100Pa transitional gaps or universal onset threshold','no_CFD':'At 100Pa, narrow-gap Kn is transitional; standard continuum CFD without suitable rarefied treatment is not justified.'}
 p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
