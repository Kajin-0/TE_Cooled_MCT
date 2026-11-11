"""Independent centered-difference check of hypothetical uniform gas load."""
from pathlib import Path
from datetime import datetime,timezone
import json,numpy as np
from scipy.linalg import solve_banded
from tecooledmct.nominal_cavity_metal_v326 import segment_with_uniform_bath
R=Path(__file__).resolve().parents[1];D=R/'data/nominal_cavity_metal_v326_20261111'
def main():
 t0,t1,bath,G,H,I,Re=300.,250.,280.,.002,.0001,.4,.003;P=I*I*Re;levels=[]
 for n in (41,81,161):
  h=1/(n-1);ab=np.zeros((3,n-2));ab[0,1:]=-G/h**2;ab[1,:]=2*G/h**2+H;ab[2,:-1]=-G/h**2;rhs=np.full(n-2,P+H*bath);rhs[0]+=G/h**2*t0;rhs[-1]+=G/h**2*t1;T=np.r_[t0,solve_banded((1,1),ab,rhs),t1];u=np.linspace(0,1,n);exact=np.array([segment_with_uniform_bath(x,t0,t1,Re,G,I,bath,H)[0] for x in u]);qgas=H*np.trapz(T-bath,u); q0=-G*(-3*T[0]+4*T[1]-T[2])/(2*h);q1=G*(3*T[-1]-4*T[-2]+T[-3])/(2*h);levels.append({'nodes':n,'max_temperature_error_K':float(max(abs(T-exact))),'independent_gas_out_W':float(qgas),'independent_global_energy_residual_W':float(q0+q1+P-qgas)})
 assert levels[-1]['max_temperature_error_K']<levels[0]['max_temperature_error_K']/10 and abs(levels[-1]['independent_global_energy_residual_W'])<1e-8
 out={'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS analytic 1D uniform-bath operator against independent centered-difference refinement; hypothetical benchmark only','benchmarks':levels,'scenario':'fixed synthetic temperatures/coefficients; no source cavity gas area or physical gas path inferred'};(D/'independent_bath_control.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
