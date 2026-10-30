"""Independent field/BC and material-specific underside inventory."""
import argparse,json,re
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .bath_spatial_audit import CASES
def check(audit,out):
    import meshio
    from reports.field_geometry import node_map
    if out.exists():raise ValueError('New boundary audit path required')
    rows=[]
    for label,mesh,case in CASES:
        d=np.load(mesh/'mesh.npz');p,c,b,f,tags=[d[x] for x in ['points','cells','bodies','faces','boundaries']];m=json.loads((mesh/'manifest.json').read_text());by={x['id']:x for x in m['bodies']};e=json.loads((case/'execution.json').read_text());raw=audit/label/'actual_fields.vtu'
        if sha(raw)!=e['vtu_sha256']:raise ValueError('Changed cached actual field')
        field=meshio.read(raw);ix,_=node_map(p,field.points);T=field.point_data['temperature'].ravel()[ix];nodes=np.unique(f[tags==101]);error=float(abs(T[nodes]-300).max())
        if error>1e-8:raise ValueError('Actual bath not300K')
        selected=f[(tags<1000)&np.all(abs(p[f,2])<1e-12,axis=1)];iszero=abs(p[c,2])<1e-12;candidate=np.flatnonzero(iszero.sum(1)==3);owners={}
        for ci in candidate:owners.setdefault(tuple(sorted(c[ci][iszero[ci]])),[]).append(int(b[ci]))
        inventory={};kovar=set()
        for face in selected:
            own=owners[tuple(sorted(face))]
            if len(own)!=1:raise ValueError('External underside has multiple owners')
            material=by[own[0]]['material'];xyz=p[face];area=float(np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2);inventory[material]=inventory.get(material,0)+area
            if material=='Kovar':kovar.add(tuple(sorted(face)))
        if kovar!={tuple(sorted(face)) for face in f[tags==101]}:raise ValueError('Missing/extra Kovar bath triangles')
        text=(case/'case.sif').read_text();blocks=re.findall(r'^Boundary Condition\s+\d+\s*\n(.*?)^End\s*$',text,re.M|re.S);fixed=[]
        for block in blocks:
            if re.search(r'^\s*Temperature\s*=',block,re.M):fixed.append(block)
        if len(fixed)!=1 or not re.search(r'Target Boundaries\(1\)\s*=\s*101\b',fixed[0]) or not re.search(r'Temperature\s*=\s*Real\s+300\b',fixed[0]):raise ValueError('Unexpected thermal Dirichlet boundaries')
        rows.append({'case':label,'field_sha256':e['vtu_sha256'],'sif_sha256':sha(case/'case.sif'),'bath_T_min_K':float(T[nodes].min()),'bath_T_max_K':float(T[nodes].max()),'bath_maxabs300_error_K':error,
            'all_external_z0_area_by_material_m2':inventory,'bath_is_exactly_all_external_Kovar_z0_faces':True,'only_temperature_Dirichlet_tag':101,
            'model_form':'glass underside and exposed pin surfaces are natural adiabatic TEST boundaries; excluding them from bath is deliberate, not OEM validated'})
    result={'cases':rows,'passed':True,'source_sha256':sha(Path(__file__)),'new_solver_run':False};write(out,result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();check(a.audit.resolve(),a.out.resolve())
