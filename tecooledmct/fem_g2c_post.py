"""Actual-field verification with nodal variable coefficients, matching Elmer.

Elmer evaluates properties at local nodes, then interpolates them to tetrahedron
Gauss points. This is distinct from evaluating a stage-average property or from
assuming constant J inside a variable-coefficient element.
"""
from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree
from .fem_g1 import tetra_geometry
from .fem_g2a import PROPERTIES,mesh_adjacency


def cut_triangles(points,cells,axis,coordinate):
    edges=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3));other=[d for d in range(3) if d!=axis]
    dd=points[cells,axis]-coordinate
    for ci in np.flatnonzero((dd.min(axis=1)<0)&(dd.max(axis=1)>0)):
        v=points[cells[ci]];d=dd[ci];poly=[]
        for a,b in edges:
            if d[a]*d[b]<0:poly.append(v[a]+d[a]/(d[a]-d[b])*(v[b]-v[a]))
        poly=np.asarray(poly);rel=poly[:,other]-poly[:,other].mean(axis=0)
        poly=poly[np.argsort(np.arctan2(rel[:,1],rel[:,0]))]
        for i in range(1,len(poly)-1):yield int(ci),poly[[0,i,i+1]]


def postprocess(mesh,case,profile,freeze=None,export=False,contact_profile=None):
    import meshio
    d=np.load(mesh/'mesh.npz');points,cells,bodies,faces,tags=(d[k] for k in ('points','cells','bodies','faces','boundaries'))
    manifest=json.loads((mesh/'manifest.json').read_text());meta=json.loads((case/'case.json').read_text())
    field=sorted(case.glob('fields*.vtu'))[-1];vtu=meshio.read(field)
    dist,mapping=cKDTree(vtu.points).query(points)
    if dist.max()>1e-12 or len(np.unique(mapping))!=len(points):raise ValueError('VTU/mesh mismatch')
    ff={n.lower():np.asarray(v).ravel()[mapping] for n,v in vtu.point_data.items()}
    t,phi=ff['temperature'],ff['potential'];vol,g=tetra_geometry(points,cells)
    gt=np.einsum('ei,eij->ej',t[cells],g);ef=-np.einsum('ei,eij->ej',phi[cells],g)
    # Nodal property functions on each material, exactly as InputTensor in Elmer.
    prop=np.empty((len(cells),4,3));ranges={}
    for b in manifest['bodies']:
        sel=bodies==b['id'];temp=t[cells[sel]];mat=b['material']
        if mat in ('P','N') or mat.endswith('_contact'):
            active=contact_profile if mat.endswith('_contact') else profile
            polarity=mat[0]
            if active is None:raise ValueError('Contact material requires explicit profile')
            active.properties(polarity,temp)  # reject unsupported ACTUAL local T, even for frozen tests
            ev=active.properties(polarity,temp if freeze is None else np.full_like(temp,freeze))
            prop[sel]=np.stack([ev[k] for k in ('k','sigma','S')],axis=-1)
            ranges[b['name']]=[float(temp.min()),float(temp.max())]
        else:prop[sel]=np.array(PROPERTIES[mat][:3])
    def quantities(bary,indices=None):
        ids=np.arange(len(cells)) if indices is None else indices
        pp=np.einsum('ei,eij->ej',bary,prop[ids]) if bary.ndim==2 else np.einsum('i,eij->ej',bary,prop[ids])
        tq=np.sum(t[cells[ids]]*bary,axis=1)
        j=pp[:,1,None]*(ef[ids]-pp[:,2,None]*gt[ids])
        q=-pp[:,0,None]*gt[ids]+(tq*pp[:,2])[:,None]*j
        return j,q,np.sum(j*ef[ids],axis=1),np.sum(j*j,axis=1)/pp[:,1]
    # Default P1 tetrahedron quadrature used by the pinned Elmer source.
    a=.5854101966249685;b=.1381966011250105
    rt=np.zeros(len(points));rp=np.zeros(len(points));work=0.;joule=0.;body_joule=np.zeros(len(cells));extra_contact=0.;jmean=np.zeros_like(gt);qmean=np.zeros_like(gt)
    for i in range(4):
        bary=np.full(4,b);bary[i]=a
        j,q,w,h=quantities(bary)
        lt=-vol[:,None]/4*(np.einsum('eij,ej->ei',g,q)+w[:,None]*bary)
        lp=-vol[:,None]/4*np.einsum('eij,ej->ei',g,j)
        np.add.at(rt,cells.ravel(),lt.ravel());np.add.at(rp,cells.ravel(),lp.ravel())
        work+=float(vol@w)/4;joule+=float(vol@h)/4;body_joule+=vol*h/4;jmean+=j/4;qmean+=q/4
        if contact_profile is not None:
            for domain in manifest['bodies']:
                if domain['kind']!='contact_layer':continue
                sel=bodies==domain['id'];extra_contact+=float(np.sum(vol[sel]*np.sum(j[sel]**2,axis=1)))/4*meta['contact']['electrical_ohm_m2']/manifest['transition_model']['thickness_m']
    adj=mesh_adjacency(cells);fc=np.array([adj[tuple(sorted(f))][0] for f in faces])
    xyz=points[faces];av=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2;area=np.linalg.norm(av,axis=1);norm=av/area[:,None]
    norm[np.einsum('ij,ij->i',norm,xyz.mean(axis=1)-points[cells[fc]].mean(axis=1))<0]*=-1
    def nodes(tag):return np.unique(faces[tags==tag])
    def avg(values,tag):
        s=tags==tag;return float(area[s]@values[faces[s]].mean(axis=1)/area[s].sum())
    hot,cold,ground=nodes(101),nodes(102),nodes(104)
    hotout=-float(rt[hot].sum());coldout=-float(rt[cold].sum()) if meta['fixed_cold_k'] is not None else -meta['load_w']
    ret=-float(rp[ground].sum());voltage=avg(phi,103);pin=meta['current_a']*voltage;scale=max(abs(pin),abs(coldout),1e-4)
    free_t=np.ones(len(points),bool);free_t[hot]=False
    if meta['fixed_cold_k'] is not None:free_t[cold]=False
    else:
        s=tags==102;np.add.at(rt,faces[s].ravel(),-np.repeat(area[s]*meta['load_w']/area[s].sum()/3,3))
    s=tags==103;np.add.at(rp,faces[s].ravel(),-np.repeat(area[s]*meta['current_a']/area[s].sum()/3,3))
    free_p=np.ones(len(points),bool);free_p[ground]=False
    # Six-point degree-four triangle quadrature; exact current (degree two) cuts.
    triq=[]
    for aa,bb,ww in ((.445948490915965,.108103018168070,.223381589678011),(.091576213509771,.816847572980459,.109951743655322)):
        for i in range(3):
            wv=np.full(3,aa);wv[i]=bb;triq.append((wv,ww))
    cuts={}
    for body in manifest['bodies']:
        if body['kind'] not in ('leg','bridge','interstage_link','contact_layer'):continue
        indices=np.flatnonzero(bodies==body['id']);axis=body['cut_axis'];coord=body['cut_coordinate_m'];total=0.;cut_area=0.
        for li,tri in cut_triangles(points,cells[indices],axis,coord):
            ci=indices[li];da=np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))/2;cut_area+=da
            for wv,ww in triq:
                pos=wv@tri;bar=np.einsum('ij,j->i',g[ci],pos-points[cells[ci,0]]);bar[0]+=1
                j,_,_,_=quantities(bar,np.array([ci]));total+=ww*da*j[0,axis]
        signed=body['current_sign']*total
        cuts[body['name']]={'current_a':signed,'relative_error':abs(signed-meta['current_a'])/abs(meta['current_a']) if meta['current_a'] else None,'absolute_error_a':abs(signed-meta['current_a']),
            'area_m2':cut_area,'expected_area_m2':body['cut_area_m2'],'kind':body['kind']}
    bath=tags==101;gradient=float(np.sum(area[bath]*np.einsum('ij,ij->i',qmean[fc[bath]],norm[bath])))
    result={**meta,'nodes':len(points),'tetrahedra':len(cells),'dofs':2*len(points),'cold_mean_k':avg(t,102),'cold_min_k':float(t[cold].min()),'cold_max_k':float(t[cold].max()),
        'temperature_min_k':float(t.min()),'temperature_max_k':float(t.max()),'profile_body_temperature_ranges_k':ranges,
        'voltage_v':voltage,'electrical_input_w':pin,'volume_j_dot_e_w':work,'joule_w':joule,'hot_out_w':hotout,'cold_out_w':coldout,
        'energy_relative_residual':(hotout+coldout-pin)/scale,'power_work_relative_residual':(work-pin)/scale,
        'bath_gradient_energy_relative_residual':(gradient+coldout-pin)/scale,'return_current_a':ret,'current_absolute_error_a':abs(ret-meta['current_a']),
        'free_thermal_residual_l1_w':float(np.abs(rt[free_t]).sum()),'free_current_residual_l1_a':float(np.abs(rp[free_p]).sum()),'cuts':cuts,
        'max_cut_relative_error':max(v['relative_error'] for v in cuts.values()) if meta['current_a'] else None,
        'field_source':field.name,'actual_material_interval_passed':True,
        'joule_by_domain_w':{domain['name']:float(body_joule[bodies==domain['id']].sum()) for domain in manifest['bodies']},
        'contact_joule_w':float(body_joule[np.isin(bodies,[d['id'] for d in manifest['bodies'] if d['kind']=='contact_layer'])].sum()),'extra_contact_joule_w':extra_contact}
    if export:
        meshio.write(case/'derived.vtu',meshio.Mesh(points,[('tetra',cells)],point_data={'Temperature_K':t,'Potential_V':phi},
            cell_data={'Body_ID':[bodies],'E_V_m':[ef],'J_A_m2':[jmean],'q_W_m2':[qmean],'Joule_W_m3':[body_joule/vol]}))
        if manifest.get('config',{}).get('couples',0)>1 or len(manifest['bodies'])>40:
            from .fem_g2a_post import field_plot
            field_plot(case,points,cells,bodies,faces,tags,t,phi)
    (case/'metrics.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result
