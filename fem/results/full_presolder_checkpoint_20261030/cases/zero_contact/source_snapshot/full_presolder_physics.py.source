"""Versioned explicit-joint coupling, unchanged cavity/gas/radiation/wire laws."""
import json
from .g2d_data import dump
from .full_presolder_reference import write_case as reference_case
from .fem_g3b_physics import payload,compile_exchange,GASES
import numpy as np


def write_case(operator,case,current=.1,pbias=.0015,poptical=.0005,gas='N2',pressure=0.,radiation=True,window_eps=.1,gold_scale=1.,lead_scale=1.,sigma=1e-12,restart=None):
    if gas not in GASES or pressure<0 or not np.isfinite(pressure) or not 0<=window_eps<=1 or lead_scale not in (0.,1.):raise ValueError('Invalid declared enclosure case')
    config={'current_a':current,'pbias_w':pbias,'poptical_thermal_w':poptical,'gas':gas,'pressure_pa':pressure,'radiation_on':bool(radiation),'window_emissivity':window_eps,'accommodation':.8,'gold_scale':gold_scale,'lead_scale':lead_scale,'package_sigma_s_m':sigma,'operator_path':str(operator)}
    reference_case(operator,case,current,pbias,poptical,wire_scale=gold_scale,sigma=sigma,restart=restart);hashes=payload(operator,case,config);library=compile_exchange(operator,case/'exchange_library');text=(case/'case.sif').read_text();text=text[:text.index('Boundary Condition 1\n')];text+='Boundary Condition 1\n Target Boundaries(1) = 101\n Temperature = Real 300\nEnd\n';m=json.loads((operator/'manifest.json').read_text());patches=json.loads((operator/'patches.json').read_text())
    for i,p in enumerate(patches,2):
        text+=f'Boundary Condition {i}\n Target Boundaries(1) = {p["solver_boundary"]}\n Heat Flux = Variable Temperature\n  Real Procedure "{library.resolve()}" "Flux{p["solver_boundary"]}"\n'
        if p['original_boundary']==103:text+=f' Electric Flux = Real {current/m["terminal_planes"]["103"]["area_m2"]:.17g}\n'
        if p['original_boundary']==104:text+=' Potential = Real 0\n'
        text+='End\n'
    (case/'case.sif').write_text(text);meta=json.loads((case/'case.json').read_text());meta.update(config,exchange_input_sha256=hashes,enclosure_model='3D solids + nonlocal gray radiosity, rarefied gas films, gold/TEC supply leads; no gas CFD',nonlocal_iteration='depth4 regularized Anderson on boundary powers; same physical fixed point, independently checked by final unaccelerated field residuals',lead_electrical_model='imposed module series I; lumped Cu lead resistance/Joule, not spatial detector/lead current transport');dump(case/'case.json',meta);return config
