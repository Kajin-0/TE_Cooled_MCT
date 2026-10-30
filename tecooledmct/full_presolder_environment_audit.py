"""Fixed-actual-field environmental sensitivity screen, not additional PDEs."""
import json
from pathlib import Path
import numpy as np
from .g2d_data import ROOT,dump
from .fem_g3b_exchange import gas_conductances,gas_power
from .full_presolder_guard import preserve


def run(out):
    preserve();base=ROOT/'fem/results/g3b_checkpoint_20261029';operator=base/'operators/operator_h0p1';r=json.loads((base/'cases/nitrogen_patch1/metrics.json').read_text());patches=json.loads((operator/'patches.json').read_text());data=np.load(operator/'operators.npz');t=np.array(r['patch_temperature_k']);cold=np.array([p['owner'] in (4,192,193,196,199) for p in patches]);rows=[]
    for pressure in (0.,1.,100.,10000.,101325.):
        q=gas_power(gas_conductances(data['exchange_m2'],data['distance_m'],t,'N2',pressure,.8),t)
        rows.append({'pressure_pa':pressure,'cold_group_gas_in_w':float(q[cold].sum()),'net_gas_w':float(q.sum()),'scope':'temperatures fixed to actual archived907patch field; not recoupled detector-temperature predictions; high pressure requires convection screening'})
    if rows[0]['cold_group_gas_in_w']!=0 or max(abs(row['net_gas_w']) for row in rows)>1e-12:raise ValueError('Fixed-field gas balance/vacuum check failed')
    audit=json.loads((operator/'audit.json').read_text());out.mkdir(parents=True,exist_ok=False)
    dump(out/'environment_screen.json',{'solver_executed':False,'manufactured_device_validated':False,'pressure_screen':rows,'raw_ray_area_reciprocity_l1':audit['raw_ray_area_reciprocity_l1'],'raw_ray_row_max_error':audit['raw_ray_row_max_error'],'closure':audit['closure'],'assumptions':'gas pressure/species,alpha0.8,gray emissivities and opaque thermal window unvalidated; balancing view factors enforces conservation, not geometrical accuracy'})
    print(rows,flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.out.resolve())
