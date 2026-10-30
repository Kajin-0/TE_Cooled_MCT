"""Geometry-only polynomial trace truncation; NEVER a solved device field."""
import argparse,json
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
def polynomial_trace(data):
    area=data['areas_m2'];xy=data['centroids_m'][:,:2];offset=data['apex_offset_xy_m'];h=data['normal_height_m'];k=17.3
    reference=float(k*np.sum(area*(10+2000*xy[:,0]-1500*xy[:,1])))
    terms={'x_sampling_W':float(k*2000*np.sum(area*offset[:,0])),'y_sampling_W':float(-k*1500*np.sum(area*offset[:,1])),'normal_curvature_W':float(-k*200*np.sum(area*h))}
    return {'analytic_bath_W':reference,'exact_nodal_P1_trace_W':reference+sum(terms.values()),'relative_interpolant_error':sum(terms.values())/reference,'components':terms,
       'kind':'exact analytic polynomial nodal INTERPOLANT, NOT an Elmer solution or actual device temperature','device_error_estimate':False}
def retained_profile(base,mesh):
    a=np.load(base/'mesh.npz');z=np.load(mesh/'mesh.npz');old=a['cells'][a['bodies']==300];new=z['cells'][z['bodies']==300]
    lookup={tuple(row) for row in np.sort(new,axis=1)};kept=np.array([tuple(row) in lookup for row in np.sort(old,axis=1)])
    zz=a['points'][old,2].mean(1);rows=[]
    for lo,hi in zip(np.arange(0,.0015,.00025),np.arange(.00025,.00175,.00025)):
        use=(zz>=lo)&(zz<hi);rows.append({'z_centroid_low_m':float(lo),'z_centroid_high_m':float(hi),'parent_tetrahedra':int(use.sum()),'parent_tetrahedra_retained':int((use&kept).sum())})
    # Bath edge stars cannot introduce nodes on the hot Kovar/presolder face.
    def top_faces(d):
        ff=d['faces'];tag=d['boundaries'];m=json.loads((base/'manifest.json').read_text());bid=next(v['boundary_id'] for v in m['contacts'] if v['bodies']==[300,301]);return {tuple(row) for row in np.sort(ff[tag==bid],axis=1)}
    return {'Kovar_parent_depth_bins':rows,'hot_Kovar_joint_triangles_byte_identical_up_to_order':top_faces(a)==top_faces(z)}
def run(out):
    if out.exists():raise ValueError('New polynomial diagnostic path required')
    old=ROOT/'outputs/bath-spatial/audit';raw=ROOT/'outputs/bath-spatial';rows=[]
    for label in ['fine647657','previous675496','normal744713','normal821458']:
        data=np.load(old/label/'bath_faces.npz');rows.append({'case':label,**polynomial_trace(data)})
    base=ROOT/'fem/results/cold20_completion_20261030/bath_mesh'
    for label in ['transverse1','transverse2']:
        data=np.load(raw/(label+'_audit')/'bath_faces.npz');rows.append({'case':label,**polynomial_trace(data),'retained_volume_profile':retained_profile(base,raw/(label+'_mesh'))})
    write(out,{'cases':rows,'new_solver_run':False,'source_sha256':sha(Path(__file__)),'polynomial':'same preregistered manufactured polynomial300+z(10+2000x-1500y)-200z^2','scope':'a priori interpolation moments and unchanged-volume inventory only; not local continuum error of the coupled device'})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.out.resolve())
