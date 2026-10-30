"""Independent raw bath extraction and explicit registry for three solved meshes."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import ROOT,sha,write
from .cold_interface_audit import affine,device
from .fem_g2a import mesh_adjacency
from .corrected_thermal import material

RAW=ROOT/'outputs/cold20';PARENT=ROOT/'outputs/cold-convergence/mesh20'


def read(p):return json.loads(p.read_text())


def bath(mesh,case,out):
    import meshio
    if out.exists():raise ValueError('New bath audit label required')
    out.mkdir(parents=True);d=np.load(mesh/'mesh.npz');p,c,b,f,tags=(d[k] for k in ('points','cells','bodies','faces','boundaries'))
    e=read(case/'execution.json');r=read(case/'metrics.json');field=meshio.read(case/e['field_source'])
    if sha(case/e['field_source'])!=e['vtu_sha256'] or sha(mesh/'mesh.npz')!=e['mesh_sha256']:raise ValueError('Changed actual bath field/mesh')
    distance,ix=cKDTree(field.points).query(p)
    if distance.max()>1e-12 or len(np.unique(ix))!=len(p):raise ValueError('Bath field mapping differs')
    T=field.point_data['temperature'].ravel()[ix];vol,grad=affine(p,c,T);faces=f[tags==101];adj=mesh_adjacency(c)
    owner=np.array([adj[tuple(sorted(face))][0] for face in faces])
    if not np.all(b[owner]==300) or any(len(adj[tuple(sorted(face))])!=1 for face in faces):raise ValueError('Bath is not actual external Kovar underside')
    xyz=p[faces];normal=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2;center=xyz.mean(1)
    normal[np.einsum('ij,ij->i',normal,center-p[c[owner]].mean(1))<0]*=-1
    area=np.linalg.norm(normal,axis=1);k=material('Kovar',T[faces],r['package_sigma_s_m'])[0].mean(1)
    power=np.einsum('ij,ij->i',-k[:,None]*grad[owner],normal);total=float(power.sum());external=r['external_total_power_w'];error=(total-external)/max(abs(external),1e-4)
    if abs(total-r['hot_out_raw_gradient_w'])>5e-10:raise ValueError('Independent raw bath does not reproduce frozen postprocessing')
    height=3*vol[owner]/area
    np.savez_compressed(out/'face_data.npz',faces=faces,centroids_m=center,areas_m2=area,power_outward_W=power,
        outward_density_W_m2=power/area,owner_height_m=height,owner=owner,owner_SICN=d['quality'][owner])
    result={'raw_outward_W':total,'known_external_input_W':external,'reaction_outward_W':r['hot_out_reaction_w'],
       'raw_relative_error':error,'one_percent_passed':bool(abs(error)<.01),'triangles':len(faces),'area_m2':float(area.sum()),
       'owner_normal_height_um_quantiles':np.quantile(height*1e6,[0,.25,.5,.75,1]).tolist(),
       'bath_temperature_maxabs_error_K':float(abs(T[np.unique(faces)]-300).max()),'field_sha256':e['vtu_sha256'],'mesh_sha256':e['mesh_sha256'],
       'source_sha256':sha(Path(__file__)),'method':'difference-based3x3 gradients, actual one-owner face normals/material; known I*V+load reference, no reaction/recovered substitution'}
    write(out/'audit.json',result);print('Independent raw bath',case.name,error,'PASS' if result['one_percent_passed'] else 'FAIL',flush=True);return result


def accepted_nonraw(case):
    r=read(case/'metrics.json');e=read(case/'execution.json')
    if e['solver_status']['exit_code'] or e['solver_status']['nonlinear_last_relative_change']>=1e-9:raise ValueError('Unconverged coupled case')
    if not all(v for k,v in r['checks'].items() if k!='raw_bath_1percent'):raise ValueError('Independent nonraw current/energy verification failed')
    return r


def study():
    from . import cold_convergence_summary as summary
    from . import cold_convergence_figures as figures
    primary=RAW/'loaded20_direct_P1';accepted_nonraw(primary)
    refined=RAW/'loaded20_refined_replay'
    if (refined/'same_mesh_agreement.json').exists() and read(refined/'same_mesh_agreement.json')['passed']:
        accepted_nonraw(refined);primary=refined
    diag=RAW/('diagnosis20_refined' if primary==refined else 'diagnosis20')
    if not (diag/'diagnosis.json').exists():device(PARENT,primary,diag)
    if not (RAW/'bath_parent/audit.json').exists():bath(PARENT,primary,RAW/'bath_parent')
    configs=[*summary.CONFIG[:2],('cold20um',PARENT,primary,diag,PARENT)]
    write(RAW/'configuration_registry.json',{'source_sha256':sha(Path(__file__)),'cases':[[str(x) for x in row] for row in configs],
        'primary_case':str(primary),'selection_plan_sha256':sha(ROOT/'data/cold20/result_selection.json'),
        'frozen_summary_source_sha256':sha(ROOT/'tecooledmct/cold_convergence_summary.py'),'frozen_figure_source_sha256':sha(ROOT/'tecooledmct/cold_convergence_figures.py')})
    summary.CONFIG=configs;result=summary.summarize(RAW/'study.json')
    figures.CONFIG=configs;figures.render(RAW/'figures',RAW/'study.json')
    optional=RAW/'bath_coupled'
    if (optional/'scope.json').exists():
        accepted_nonraw(optional)
        if not (RAW/'diagnosis_bath/diagnosis.json').exists():device(RAW/'bath_mesh',optional,RAW/'diagnosis_bath')
        if not (RAW/'bath_refined/audit.json').exists():bath(RAW/'bath_mesh',optional,RAW/'bath_refined')
        a=read(primary/'metrics.json');b=read(optional/'metrics.json');audit=read(RAW/'bath_mesh/audit.json')
        write(RAW/'bath_comparison.json',{'parent_case':str(primary),'parent_uses_same_LU_refinement':primary==refined,
            'cold_cells_byte_identical':audit['cold_cells_byte_identical'],'die_delta_K':b['die_mean_k']-a['die_mean_k'],
            'voltage_delta_V':b['voltage_v']-a['voltage_v'],'parent_bath_relative_error':a['direct_bath_relative_error'],
            'refined_bath_relative_error':b['direct_bath_relative_error'],'parent_cold_jumps':[r['mismatch'] for r in read(diag/'diagnosis.json')['interfaces']],
            'refined_cold_jumps':[r['mismatch'] for r in read(RAW/'diagnosis_bath/diagnosis.json')['interfaces']],
            'qualified_GCI':False,'scope':'one independent conformal bath-volume refinement with exact original cold cells; all raw gates unchanged'})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--study',action='store_true');p.add_argument('--mesh',type=Path);p.add_argument('--case',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    study() if a.study else bath(a.mesh.resolve(),a.case.resolve(),a.out.resolve())
