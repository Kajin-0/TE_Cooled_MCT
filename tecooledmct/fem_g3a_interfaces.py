"""Independent source-free interior cuts through mount and each 3D pin."""
import json
from pathlib import Path
import numpy as np
from .g2d_data import ROOT,sha,dump
from .fem_g2c_post import cut_triangles


def verify(mesh,case):
    import meshio
    a=np.load(mesh/'mesh.npz');p,c,b=(a[k] for k in ('points','cells','bodies'));m=json.loads((mesh/'manifest.json').read_text());r=json.loads((case/'metrics.json').read_text());field=meshio.read(case/'derived.vtu')
    if not np.array_equal(field.points,p):raise ValueError('Derived field mapping changed')
    q=field.cell_data_dict['q_W_m2']['tetra'];results=[]
    mount=next(x for x in m['bodies'] if x['kind']=='hot_mount');checks=[(mount['id'],mount['box_m'][2]+mount['box_m'][5]/2,-1,r['tec_input_w']+r['deposited_power_w']+r['wire_heat_into_die_w'],'mount downward to header')]
    for i,e in enumerate(m['wire_endpoints']):checks.append((e['pin_body'],m['header_top_m']+.5*m['package_registry']['feedthroughs']['pin_above_header_m'],1,r['wires'][i]['heat_into_die_w'],f'pin {i} upward from glass/header'))
    for bid,z,sign,expected,label in checks:
        ids=np.flatnonzero(b==bid);flow=0.;area=0.
        for local,tri in cut_triangles(p,c[ids],2,z):
            da=np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))/2;area+=da;flow+=sign*da*q[ids[local],2]
        error=(flow-expected)/max(abs(expected),1e-4);results.append({'label':label,'measured_flow_w':float(flow),'expected_independent_energy_w':expected,'relative_error':float(error),'cut_area_m2':float(area),'passed':bool(abs(error)<.05)})
    result={'passed':all(x['passed'] for x in results),'cuts':results,'source_sha256':sha(Path(__file__)),'raw_vtu_sha256':r['vtu_sha256'],'scope':'Actual independent interior gradient fluxes;5% tolerance, separate from nodal conservative budgets. No local corner convergence claim.'};dump(case/'interface_cuts.json',result);return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--mesh',type=Path,default=Path('outputs/fem-g3a/mesh_0'));p.add_argument('--case',type=Path,default=Path('outputs/fem-g3a/loaded_0'));a=p.parse_args();r=verify(a.mesh.resolve(),a.case.resolve());print(json.dumps(r,indent=2))
    if not r['passed']:raise SystemExit('Independent package interface cuts failed')
