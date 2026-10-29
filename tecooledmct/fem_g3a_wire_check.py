"""Independent genuine 1D Elmer Neumann rod check of the hybrid gold-wire law."""
from pathlib import Path
import json,math
import numpy as np
from .g2d_data import ROOT,sha,dump
from .fem_g1_run import execute


def main():
    import meshio
    out=ROOT/'outputs/fem-g3a/wire_reference';out.mkdir(parents=True,exist_ok=True)
    length=.007;diameter=25e-6;ka=315*math.pi*diameter**2/4;heat=.001;nodes=11
    (out/'mesh.header').write_text(f'{nodes} {nodes-1} 2\n2\n202 {nodes-1}\n101 2\n')
    (out/'mesh.nodes').write_text(''.join(f'{i+1} -1 {length*i/(nodes-1):.17g} 0 0\n' for i in range(nodes)))
    (out/'mesh.elements').write_text(''.join(f'{i+1} 1 202 {i+1} {i+2}\n' for i in range(nodes-1)))
    (out/'mesh.boundary').write_text(f'1 1 1 0 101 1\n2 2 {nodes-1} 0 101 {nodes}\n')
    sif=f'''Check Keywords Warn
Header
 Mesh DB "{out.resolve()}" "."
End
Simulation
 Coordinate System = Cartesian 1D
 Simulation Type = Steady State
 Steady State Max Iterations = 1
 Post File = "fields.vtu"
End
Body 1
 Equation = 1
 Material = 1
End
Equation 1
 Active Solvers(1) = 1
End
Solver 1
 Equation = "Heat Equation"
 Variable = Temperature
 Procedure = "HeatSolve" "HeatSolver"
 Linear System Solver = Direct
 Linear System Direct Method = UMFPACK
End
Material 1
 Heat Conductivity = Real {ka:.17g}
End
Boundary Condition 1
 Target Boundaries(1) = 1
 Heat Flux = Real {heat}
End
Boundary Condition 2
 Target Boundaries(1) = 2
 Temperature = Real 260
End
'''
    (out/'case.sif').write_text(sif);status=execute(['ElmerSolver','case.sif'],out,'solver');source=sorted(out.glob('fields*.vtu'))[-1];f=meshio.read(source);t=np.asarray(next(v for k,v in f.point_data.items() if k.lower()=='temperature')).ravel();x=f.points[:,0];expected=260+heat*(length-x)/ka;conductance=heat/(float(t[np.argmin(x)])-260)
    result={'passed':float(np.max(np.abs(t-expected)))<1e-7,'actual_hot_k':float(t[np.argmin(x)]),'actual_conductance_w_k':conductance,'analytical_conductance_w_k':ka/length,'max_temperature_error_k':float(np.max(np.abs(t-expected))),'source_power_w':heat,'actual_hot_to_cold_powers_w':[heat,-heat],'solver_status':status,'sif_sha256':sha(out/'case.sif'),'vtu_sha256':sha(source),'source_sha256':sha(Path(__file__)),'note':'Actual 1D Fourier rod, effective coefficient k*A; imposed hot power1mW and cold260K, hot temperature solved. No all-3D wire claim.'};dump(out/'verification.json',result);print(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit('Independent wire FEM check failed')

if __name__=='__main__':main()
