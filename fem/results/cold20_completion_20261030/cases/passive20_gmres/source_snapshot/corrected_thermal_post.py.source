"""Independent actual-field current/heat/work checks for corrected solid assembly."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import ROOT,sha,write
from .fem_g1 import tetra_geometry
from .fem_g2a import mesh_adjacency
from .fem_g2c_post import cut_triangles
from .corrected_thermal import material,endpoint_weights,link_powers


def postprocess(mesh,case):
    import meshio
    d=np.load(mesh/'mesh.npz');p,c,b,f,bt=(d[k] for k in ('points','cells','bodies','faces','boundaries'))
    m=json.loads((mesh/'manifest.json').read_text());meta=json.loads((case/'case.json').read_text());by={r['id']:r for r in m['bodies']}
    source=sorted(case.rglob('fields*.vtu'))[-1];field=meshio.read(source);dist,ix=cKDTree(field.points).query(p)
    if dist.max()>1e-12 or len(np.unique(ix))!=len(p) or len(field.get_cells_type('tetra'))!=len(c):raise ValueError('Actual T/phi field does not map to exact corrected mesh')
    t=field.point_data['temperature'].ravel()[ix];phi=field.point_data['potential'].ravel()[ix]
    vol,g=tetra_geometry(p,c);gt=np.einsum('ei,eij->ej',t[c],g);E=-np.einsum('ei,eij->ej',phi[c],g)
    props=np.empty((len(c),4,3))
    for row in m['bodies']:
        sel=b==row['id'];props[sel]=np.stack(material(row['material'],t[c[sel]],meta['package_sigma_s_m']),axis=-1)
    def quantities(bary,ids=None):
        if ids is None:ids=np.arange(len(c))
        pp=np.einsum('i,eij->ej',bary,props[ids]);temp=t[c[ids]]@bary
        j=pp[:,1,None]*(E[ids]-pp[:,2,None]*gt[ids]);fourier=-pp[:,0,None]*gt[ids];peltier=(temp*pp[:,2])[:,None]*j
        return j,fourier+peltier,np.sum(j*E[ids],axis=1),np.sum(j*j,axis=1)/pp[:,1],fourier,peltier
    rt=np.zeros(len(p));rp=np.zeros(len(p));work=np.zeros(len(c));joule=np.zeros(len(c));J=np.zeros_like(gt);Q=np.zeros_like(gt);Fourier=np.zeros_like(gt);Peltier=np.zeros_like(gt)
    for i in range(4):
        bary=np.full(4,.1381966011250105);bary[i]=.5854101966249685
        j,q,w,jj,qf,qp=quantities(bary)
        np.add.at(rt,c.ravel(),(-vol[:,None]/4*(np.einsum('eij,ej->ei',g,q)+w[:,None]*bary)).ravel())
        np.add.at(rp,c.ravel(),(-vol[:,None]/4*np.einsum('eij,ej->ei',g,j)).ravel())
        work+=vol*w/4;joule+=vol*jj/4;J+=j/4;Q+=q/4;Fourier+=qf/4;Peltier+=qp/4
    ep=endpoint_weights(mesh)
    def avg(values,tag):return float(np.dot(ep[str(tag)]['weights'],values[ep[str(tag)]['indices']]))
    bath=np.array(ep['101']['indices']);ground=np.array(ep['104']['indices']);hot=-float(rt[bath].sum());ret=-float(rp[ground].sum())
    V=avg(phi,103)-avg(phi,104);I=meta['current_a'];P=meta['deposited_power_w'];Pin=I*V
    detector_node=np.zeros(len(p));mct=b==303;np.add.at(detector_node,c[mct].ravel(),np.repeat(vol[mct]*P/vol[mct].sum()/4,4));rt-=detector_node
    boundary,links,mechanisms=link_powers(mesh,t,meta,ep);rt-=boundary;lead_joule=sum(row['joule_w'] for row in links);external=Pin+P+lead_joule;scale=max(abs(Pin)+P+lead_joule,1e-4)
    for node,weight in zip(ep['103']['indices'],ep['103']['weights']):rp[node]-=I*weight
    freeT=np.ones(len(p),bool);freeT[bath]=False;freeP=np.ones(len(p),bool);freeP[ground]=False
    adj=mesh_adjacency(c);bathfaces=f[bt==101];owner=np.array([adj[tuple(sorted(face))][0] for face in bathfaces]);xyz=p[bathfaces]
    av=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])/2
    av[np.einsum('ij,ij->i',av,xyz.mean(1)-p[c[owner]].mean(1))<0]*=-1
    if set(b[owner])!={300}:raise ValueError('Raw bath faces are not exclusively Kovar')
    raw=float(np.einsum('ij,ij->',Q[owner],av))
    # Actual177 conductor cuts; no averaging or equilibrated-current substitution.
    cuts={};legheat={stage:{'fourier_down_w':0.,'peltier_down_w':0.,'total_down_w':0.} for stage in range(3)}
    for row in m['bodies']:
        if 'cut_axis' not in row:continue
        ids=np.flatnonzero(b==row['id']);area=total=heat=qfour=qpel=0.
        for ci,tri in cut_triangles(p,c[ids],row['cut_axis'],row['cut_coordinate_m']):
            da=np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))/2;elem=ids[ci];axis=row['cut_axis']
            # P1 constant sigma/S gives constant J; Peltier heat is linear in T.
            bary=np.r_[1.,tri.mean(0)]@np.linalg.inv(np.c_[np.ones(4),p[c[elem]]])
            jj,qq,_,_,qf,qp=quantities(bary,np.array([elem]))
            area+=da;total+=da*jj[0,axis];heat+=da*qq[0,axis];qfour+=da*qf[0,axis];qpel+=da*qp[0,axis]
        measured=row['current_sign']*total;err=abs(measured-I)
        cuts[row['name']]={'body':row['id'],'current_a':measured,'error_a':err,'relative_error':err/abs(I) if I else None,
             'area_m2':area,'expected_area_m2':row['cut_area_m2'],'heat_positive_axis_w':heat,
             'fourier_positive_axis_w':qfour,'peltier_positive_axis_w':qpel}
        if row['kind']=='leg':
            target=legheat[row['stage']];target['fourier_down_w']-=qfour;target['peltier_down_w']-=qpel;target['total_down_w']-=heat
    stats={}
    for row in m['bodies']:
        sel=b==row['id'];tt=t[c[sel]];stats[str(row['id'])]={'name':row['name'],'volume_mean_k':float(vol[sel]@tt.mean(1)/vol[sel].sum()),
             'min_k':float(tt.min()),'max_k':float(tt.max()),'mean_potential_v':float(vol[sel]@phi[c[sel]].mean(1)/vol[sel].sum())}
    interfaces=[]
    for pair in ((300,301),(1,301),(4,302),(302,303)):
        pair=tuple(sorted(pair));tag=next(v['boundary_id'] for v in m['contacts'] if tuple(v['bodies'])==pair)
        ff=f[bt==tag];xx=p[ff];a=np.linalg.norm(np.cross(xx[:,1]-xx[:,0],xx[:,2]-xx[:,0]),axis=1)/2;powers=[]
        for body in pair:
            cell=np.array([next(e for e in adj[tuple(sorted(face))] if b[e]==body) for face in ff]);normal=np.cross(xx[:,1]-xx[:,0],xx[:,2]-xx[:,0])/2
            normal[np.einsum('ij,ij->i',normal,xx.mean(1)-p[c[cell]].mean(1))<0]*=-1
            powers.append(float(np.einsum('ij,ij->',Q[cell],normal)))
        mismatch=sum(powers)/max(sum(map(abs,powers))/2,1e-4)
        interfaces.append({'bodies':list(pair),'tag':tag,'area_m2':float(a.sum()),'temperature_area_mean_k':float(a@t[ff].mean(1)/a.sum()),
             'raw_one_sided_outward_w':powers,'raw_sum_outward_w':sum(powers),'raw_relative_mismatch':mismatch,
             'extra_5percent_diagnostic_passed':abs(mismatch)<.05})
    # Whole-assembly P1 indicator control-volume budgets. All new return/support
    # and pin heat paths are retained; these are not raw sharp-interface fluxes.
    mechanisms['detector']=detector_node;flows=[hot];cumulative=[0.];cums=[{k:0. for k in mechanisms}]
    for bid in (2,3):
        box=by[bid]['boxes_m'][0];weight=(p[:,2]<=box[2]+.2*box[5]).astype(float);gw=np.einsum('ei,eij->ej',weight[c],g)
        flows.append(float(vol@np.sum(gw*Q,axis=1)));cumulative.append(float(work@weight[c].mean(1)))
        cums.append({key:float(weight@node) for key,node in mechanisms.items()})
    flows.append(0.);cumulative.append(float(work.sum()));cums.append({key:float(node.sum()) for key,node in mechanisms.items()});bands=[]
    for i in range(3):
        terms={key:cums[i+1][key]-cums[i][key] for key in mechanisms};ww=cumulative[i+1]-cumulative[i]
        bands.append({'band':i,'hot_out_w':flows[i],'cold_out_downward_w':flows[i+1],'electrical_work_w':ww,
             'sources_w':terms,'energy_error_w':flows[i]-flows[i+1]-ww-sum(terms.values())})
    stages=[]
    for stage in range(3):
        sel=np.isin(b,[row['id'] for row in m['bodies'] if row.get('stage')==stage and row['material'] in ('Cu','P','N')])
        stages.append({'stage':stage,**legheat[stage],'group_Joule_w':float(joule[sel].sum()),'group_electrical_work_w':float(work[sel].sum()),
             'group_Seebeck_reversible_work_w':float((work[sel]-joule[sel]).sum()),'scope':'stage-local P/N+original Cu; separate routes/supports remain in global/control-volume budgets'})
    passive=~np.isin(b,m['conductor_path']);pkgjoule=float(joule[passive].sum());maxpkg=float(np.linalg.norm(J[passive],axis=1).max())
    pins=[]
    for bid in range(501,510):
        ids=np.flatnonzero(b==bid);total=area=0.
        for ci,tri in cut_triangles(p,c[ids],2,.00175):
            da=np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))/2;area+=da;total+=da*J[ids[ci],2]
        pins.append({'pin':bid-500,'computational_cut_current_a':total,'area_m2':area,'scope':'tiny-sigma passive extension; not physical TEC/detector electrical transport'})
    worst=max(v['relative_error'] or 0. for v in cuts.values());absolute=max(v['error_a'] for v in cuts.values())
    freet=float(abs(rt[freeT]).sum());freep=float(abs(rp[freeP]).sum());worktotal=float(work.sum());energy=hot-external;rawerror=(raw-external)/scale
    r={**meta,'nodes':len(p),'tetrahedra':len(c),'die_mean_k':stats['303']['volume_mean_k'],'cold_ceramic_k':stats['4']['volume_mean_k'],
       'hot_ceramic_k':stats['1']['volume_mean_k'],'temperature_min_k':float(t.min()),'temperature_max_k':float(t.max()),'voltage_v':V,
       'external_source_voltage_v':V+lead_joule/I if I else V,'TEC_input_w':Pin,'wire_Joule_w':lead_joule,'external_total_power_w':external,
       'hot_out_reaction_w':hot,'hot_out_raw_gradient_w':raw,'bath_area_m2':ep['101']['area_m2'],'bath_owner_body':300,
       'direct_bath_relative_error':rawerror,'global_energy_error_w':energy,'work_w':worktotal,'Joule_w':float(joule.sum()),
       'free_thermal_residual_L1_w':freet,'free_current_residual_L1_a':freep,'return_current_a':ret,'current_error_a':abs(ret-I),
       'worst_raw_cut_relative_error':worst,'worst_raw_cut_absolute_a':absolute,'cuts':cuts,'domain_temperatures':stats,
       'interfaces':interfaces,'wire_links':links,'passive_Joule_w':pkgjoule,'max_passive_J_A_m2':maxpkg,'pin_cuts':pins,
       'stage_control_volumes':bands,'stage_thermoelectric_decomposition':stages,'field_source':str(source.relative_to(case)),
       'mesh_sha256':sha(mesh/'mesh.npz'),'sif_sha256':sha(case/'case.sif'),'vtu_sha256':sha(source),'postprocessor_sha256':sha(Path(__file__)),
       'spatial_convergence':'NOT RUN; one exact corrected source mesh','full_device_qualification':False,
       'scope':'solid-only synthetic composite reference; no enclosure, radiation/gas, optical transmission or OEM validation'}
    checks={'all177_cut_areas':len(cuts)==177 and all(abs(v['area_m2']/v['expected_area_m2']-1)<1e-7 for v in cuts.values()),
            'all177_current_half_percent_or_1uA_at_zero':worst<.005 if I else absolute<1e-6,
            'return_current_1uA':abs(ret-I)<1e-6,'free_thermal_1uW':freet<1e-6,'free_current_1uA':freep<1e-6,
            'global_energy_1uW':abs(energy)<1e-6,'work_1percent':abs(worktotal-Pin)/scale<.01,'raw_bath_1percent':abs(rawerror)<.01,
            'stage_energy_1uW':all(abs(v['energy_error_w'])<1e-6 for v in bands),'passive_Joule_1nW':pkgjoule<1e-9,
            'passive_pin_currents_1pA':max(abs(v['computational_cut_current_a']) for v in pins)<1e-12,
            'wire_conduction_conservative':abs(mechanisms['wire_conduction'].sum())<1e-12,
            'wire_Joule_source_balance':abs(mechanisms['wire_joule'].sum()-lead_joule)<1e-12,
            'uniform_passive_1uK':True if I or P else float(abs(t-300).max())<1e-6,
            'positive_drive_cools_cold_plate':True if I<=0 else stats['4']['volume_mean_k']<stats['1']['volume_mean_k']}
    r['checks']={k:bool(v) for k,v in checks.items()};r['passed']=all(checks.values());write(case/'metrics.json',r)
    meshio.write(case/'derived.vtu',meshio.Mesh(p,[('tetra',c)],point_data={'Temperature_K':t,'Potential_V':phi},
        cell_data={'body_id':[b],'J_A_m2':[J],'q_W_m2':[Q],'Fourier_q_W_m2':[Fourier],'Peltier_q_W_m2':[Peltier],
                   'Joule_W_m3':[joule/vol],'electric_work_W_m3':[work/vol]}))
    return r
