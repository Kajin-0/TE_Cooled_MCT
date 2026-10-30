"""Independent actual joint-plane temperatures and one-sided material fluxes."""
import json
from pathlib import Path
import numpy as np
from .g2d_data import ROOT,sha,dump
from .flux_presolder_common import node_map,affine_geometry,boundary_owners,outward_vectors


def audit(operator,case):
    import meshio
    mesh=np.load(operator/'mesh.npz');p,c,b,f,tags=[mesh[k] for k in ('points','cells','bodies','faces','boundaries')];m=json.loads((operator/'manifest.json').read_text());r=json.loads((case/'metrics.json').read_text());ex=json.loads((case/'execution.json').read_text());field=meshio.read(case/r['field_source']);ix,_=node_map(p,field.points);t=field.point_data['temperature'].ravel()[ix]
    if sha(case/r['field_source'])!=ex['vtu_sha256']:raise ValueError('Changed actual coupled field')
    law=m['presolder_config'];k={1:30.,190:17.3,191:law['k_w_mk'],216:law['lower_k_w_mk'],217:law['upper_k_w_mk']};joint={191,216,217}&set(b);interfaces=[]
    for contact in m['contacts']:
        if not any(v in joint for v in contact['bodies']):continue
        faces=f[tags==contact['boundary_id']];x=p[faces];areas=np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1)/2;flows=[]
        for bid in contact['bodies']:
            ids=np.flatnonzero(b==bid);owner=boundary_owners(c[ids],faces);v,g=affine_geometry(p,c[ids]);grad=np.einsum('ei,eij->ej',t[c[ids]],g);q=-k[bid]*grad;av=outward_vectors(p,c[ids],faces,owner);flows.append(float(np.einsum('ij,ij->',q[owner],av)))
        mismatch=sum(flows);scale=max(np.mean(abs(np.array(flows))),1e-4)
        interfaces.append({'bodies':contact['bodies'],'boundary_id':contact['boundary_id'],'area_m2':float(areas.sum()),'z_m':float(np.mean(x[:,:,2])),'temperature_area_mean_k':float(areas@t[faces].mean(1)/areas.sum()),'one_sided_outward_powers_w':flows,'sum_outward_powers_w':mismatch,'raw_interface_relative_mismatch':float(mismatch/scale),'extra_5percent_diagnostic_passed':bool(abs(mismatch)/scale<.05)})
    layers=[]
    for bid in sorted(joint):
        row=next(v for v in m['bodies'] if v['id']==bid);ends=[v for v in interfaces if bid in v['bodies']];ends.sort(key=lambda v:v['z_m']);layers.append({'body':bid,'name':row['name'],'k_w_mk':k[bid],'bottom_k':ends[0]['temperature_area_mean_k'],'top_k':ends[-1]['temperature_area_mean_k'],'area_mean_temperature_drop_k':ends[-1]['temperature_area_mean_k']-ends[0]['temperature_area_mean_k']})
    result={'actual_vtu_sha256':ex['vtu_sha256'],'mesh_sha256':sha(operator/'mesh.npz'),'independent_affine_gradients':True,'interfaces':interfaces,'layers':layers,'all_extra_interface_diagnostics_passed':all(v['extra_5percent_diagnostic_passed'] for v in interfaces),'scope':'assumed-geometry sandbox; shared-temperature conformal interfaces, raw one-sided gradient diagnostics only; no metallurgical/device qualification','original_historical_raw_1percent_gate_remains_failed':True}
    dump(case/'joint_interface_audit.json',result);return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--operator',type=Path,required=True);parser.add_argument('--case',type=Path,required=True);a=parser.parse_args();print(audit(a.operator.resolve(),a.case.resolve()))
