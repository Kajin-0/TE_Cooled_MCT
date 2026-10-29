"""Independent actual-field nodal-law heat/current verification of hybrid G3a."""
import json
import numpy as np
from scipy.spatial import cKDTree
from .g2d_data import ROOT,sha,dump
from .fem_g3b_data import registry
from .fem_g3a_data import wire_conductance
from .fem_g3b_reference import material_properties,endpoint_weights
from .fem_g1 import tetra_geometry
from .fem_g2a import mesh_adjacency
from .fem_g2c_post import cut_triangles


def postprocess(mesh,case,export=True):
    import meshio
    d=np.load(mesh/'mesh.npz');p,c,b,f,bt=(d[k] for k in ('points','cells','bodies','faces','boundaries'));m=json.loads((mesh/'manifest.json').read_text());meta=json.loads((case/'case.json').read_text());source=sorted(case.glob('fields*.vtu'))[-1];field=meshio.read(source)
    dist,ix=cKDTree(field.points).query(p)
    if dist.max()>1e-12 or len(np.unique(ix))!=len(p):raise ValueError('Actual VTU/mesh mismatch')
    ff={k.lower():v.ravel()[ix] for k,v in field.point_data.items()};t,phi=ff['temperature'],ff['potential'];vol,g=tetra_geometry(p,c);gt=np.einsum('ei,eij->ej',t[c],g);electric=-np.einsum('ei,eij->ej',phi[c],g);props=np.empty((len(c),4,3));by={v['id']:v for v in m['bodies']}
    for body in m['bodies']:
        sel=b==body['id'];props[sel]=np.stack(material_properties(body['material'],t[c[sel]],meta['package_sigma_s_m'],meta['attach_k_scale'],meta['mount_k_scale']),axis=-1)
    def quantities(bary,ids=None):
        if ids is None:ids=np.arange(len(c))
        pp=np.einsum('i,eij->ej',bary,props[ids]);temp=np.sum(t[c[ids]]*bary,axis=1);j=pp[:,1,None]*(electric[ids]-pp[:,2,None]*gt[ids]);q=-pp[:,0,None]*gt[ids]+(temp*pp[:,2])[:,None]*j
        return j,q,np.sum(j*electric[ids],axis=1),np.sum(j*j,axis=1)/pp[:,1]
    rt=np.zeros(len(p));rp=np.zeros(len(p));work_e=np.zeros(len(c));joule_e=np.zeros(len(c));jm=np.zeros_like(gt);qm=np.zeros_like(gt)
    aa=.5854101966249685;bb=.1381966011250105
    for i in range(4):
        bary=np.full(4,bb);bary[i]=aa;j,q,w,jj=quantities(bary);np.add.at(rt,c.ravel(),(-vol[:,None]/4*(np.einsum('eij,ej->ei',g,q)+w[:,None]*bary)).ravel());np.add.at(rp,c.ravel(),(-vol[:,None]/4*np.einsum('eij,ej->ei',g,j)).ravel());work_e+=vol*w/4;joule_e+=vol*jj/4;jm+=j/4;qm+=q/4
    xyz=p[f];areas=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
    def avg(values,tag):
        sel=bt==tag;return float(areas[sel]@values[f[sel]].mean(axis=1)/areas[sel].sum())
    bath=np.unique(f[bt==101]);ground=np.unique(f[bt==104]);hotout=-float(rt[bath].sum());ret=-float(rp[ground].sum());voltage=avg(phi,103)-avg(phi,104);pin=meta['current_a']*voltage;P=meta['deposited_power_w'];scale=max(abs(pin)+P,1e-4)
    mct=b==m['mct_body'];pvolume=float(vol[mct].sum());density=P/pvolume;np.add.at(rt,c[mct].ravel(),-np.repeat(vol[mct]*density/4,4))
    ep=endpoint_weights(mesh);wires=[]
    for i in (0,1):
        warm,cold=200+2*i,201+2*i;tw=avg(t,warm);tc=avg(t,cold);q=wire_conductance(1)*meta['wire_scale']*(tw-tc)
        for tag,power in ((warm,-q),(cold,q)):
            e=ep[tag];rt[e['indices']]-=power*np.asarray(e['weights'])
        wires.append({'wire':i,'warm_pin_patch_k':tw,'cold_pad_patch_k':tc,'heat_into_die_w':q,'conductance_w_k':wire_conductance(1)*meta['wire_scale'],'equal_opposite_endpoint_powers_w':[-q,q]})
    sel=bt==103;np.add.at(rp,f[sel].ravel(),-np.repeat(areas[sel]*meta['current_a']/areas[sel].sum()/3,3));freeT=np.ones(len(p),bool);freeT[bath]=False;freeP=np.ones(len(p),bool);freeP[ground]=False
    adj=mesh_adjacency(c);bathfaces=f[bt==101];facecells=np.array([adj[tuple(sorted(a))][0] for a in bathfaces]);xx=p[bathfaces];av=np.cross(xx[:,1]-xx[:,0],xx[:,2]-xx[:,0])/2;sign=np.einsum('ij,ij->i',av,xx.mean(axis=1)-p[c[facecells]].mean(axis=1));av[sign<0]*=-1;direct=float(np.einsum('ij,ij->',qm[facecells],av))
    # Current is exactly constant inside P1 constant-coefficient TEC tetrahedra.
    cuts={}
    for body in m['bodies'][:m['original_TEC_domains']]:
        if body['kind'] not in ('leg','bridge','interstage_link'):continue
        ids=np.flatnonzero(b==body['id']);total=0.;area=0.
        for ci,tri in cut_triangles(p,c[ids],body['cut_axis'],body['cut_coordinate_m']):
            da=np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))/2;area+=da;total+=da*jm[ids[ci],body['cut_axis']]
        measured=total*body['current_sign'];error=abs(measured-meta['current_a']);cuts[body['name']]={'current_a':measured,'error_a':error,'relative_error':error/abs(meta['current_a']) if meta['current_a'] else None,'area_m2':area,'expected_area_m2':body['cut_area_m2']}
    stats={}
    for body in m['bodies']:
        if body['kind'] not in ('ceramic','header','hot_mount','die_attach','die','glass','pin','bond_pad','cap','window'):continue
        sel=b==body['id'];tt=t[c[sel]];stats[body['name']]={'mean_k':float(vol[sel]@tt.mean(axis=1)/vol[sel].sum()),'min_k':float(tt.min()),'max_k':float(tt.max())}
    da=next(v for v in m['bodies'] if v['kind']=='die_attach');box=da['box_m'];faces_areas={}
    for zlabel,z in [('attach_bottom_k',box[2]),('attach_top_k',box[2]+box[5])]:
        selected=[]
        for pair,neighbors in adj.items():
            if len(neighbors)==2 and any(b[a]==da['id'] for a in neighbors) and np.all(np.abs(p[list(pair),2]-z)<1e-11):selected.append(pair)
        ft=np.array(selected);xx=p[ft];a=np.linalg.norm(np.cross(xx[:,1]-xx[:,0],xx[:,2]-xx[:,0]),axis=1)/2;faces_areas[zlabel]=float(a@t[ft].mean(axis=1)/a.sum())
    attachflow=0.;ids=np.flatnonzero(b==da['id']);z=box[2]+.5*box[5]
    for ci,tri in cut_triangles(p,c[ids],2,z):attachflow-=float(np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))/2*qm[ids[ci],2])
    package=b>m['original_TEC_domains'];package_joule=float(joule_e[package].sum());pkgcurrent=float(np.linalg.norm(jm[package],axis=1).max());work=float(work_e.sum());joule=float(joule_e.sum());wireheat=sum(q['heat_into_die_w'] for q in wires);interface_error=attachflow-P-wireheat
    # Cumulative actual P1 nodal control-volume transfers, including package sources.
    stages=[];flows=[hotout];cumulative=[0.]
    for bid in (2,3):
        bbx=by[bid]['box_m'];weight=(p[:,2]<=bbx[2]+.2*bbx[5]).astype(float);gw=np.einsum('ei,eij->ej',weight[c],g);up=-float(vol@np.sum(gw*qm,axis=1));flows.append(-up);cumulative.append(float(work_e@weight[c].mean(axis=1)))
    flows.append(P+wireheat);cumulative.append(work)
    # First CV includes header/mount and warm wire endpoints; last contains cold sources.
    for i in range(3):
        correction=-wireheat if i==0 else 0.;stages.append({'stage':i,'hot_out_w':flows[i],'cold_absorbed_w':flows[i+1],'electrical_work_w':cumulative[i+1]-cumulative[i],'warm_wire_endpoint_sink_w':correction,'energy_error_w':flows[i]-flows[i+1]-(cumulative[i+1]-cumulative[i])-correction})
    worst=max(x['relative_error'] or 0. for x in cuts.values());absolute=max(x['error_a'] for x in cuts.values());freeTnorm=float(np.abs(rt[freeT]).sum());freePnorm=float(np.abs(rp[freeP]).sum())
    r={**meta,'nodes':len(p),'tetrahedra':len(c),'cold_ceramic_k':stats['ceramic_3']['mean_k'],'die_mean_k':stats['MCT_x029']['mean_k'],'die_min_k':stats['MCT_x029']['min_k'],'die_max_k':stats['MCT_x029']['max_k'],'die_to_cold_k':stats['MCT_x029']['mean_k']-stats['ceramic_3']['mean_k'],'temperature_min_k':float(t.min()),'temperature_max_k':float(t.max()),'voltage_v':voltage,'tec_input_w':pin,'hot_out_reaction_w':hotout,'hot_out_direct_w':direct,'work_w':work,'joule_w':joule,'global_energy_error_w':hotout-pin-P,'direct_bath_relative_error':(direct-pin-P)/scale,'power_work_relative_error':(work-pin)/scale,'free_thermal_residual_l1_w':freeTnorm,'free_current_residual_l1_a':freePnorm,'return_current_a':ret,'current_error_a':abs(ret-meta['current_a']),'component_cuts':cuts,'worst_cut_relative_error':worst,'worst_cut_absolute_a':absolute,'domain_temperatures':stats,**faces_areas,'wires':wires,'wire_heat_into_die_w':wireheat,'attach_midplane_down_w':attachflow,'attach_direct_energy_error_w':interface_error,'attach_direct_energy_relative_error':interface_error/max(abs(P+wireheat),1e-4),'package_joule_w':package_joule,'max_package_current_density_a_m2':pkgcurrent,'stage_control_volume_budgets':stages,'stage_scope':'nodal planes through plates; bottom volume includes header/mount and warm-wire sink; cold external deposition and cold wire endpoints excluded above TEC plane','field_source':source.name,'vtu_sha256':sha(source),'sif_sha256':sha(case/'case.sif'),'postprocessor_sha256':sha(ROOT/'tecooledmct/fem_g3b_reference_post.py')}
    checks={'all_175_cut_areas':len(cuts)==175 and all(abs(x['area_m2']/x['expected_area_m2']-1)<1e-7 for x in cuts.values()),'driven_half_pct_or_zero_1uA_cuts':worst<.005 if meta['current_a'] else absolute<1e-6,'current_1uA':r['current_error_a']<1e-6,'free_thermal_1uW':freeTnorm<1e-6,'free_current_1uA':freePnorm<1e-6,'global_energy_1uW':abs(r['global_energy_error_w'])<1e-6,'independent_work_1pct':abs(r['power_work_relative_error'])<.01,'direct_bath_1pct':abs(r['direct_bath_relative_error'])<.01,'direct_attach_5pct':abs(r['attach_direct_energy_relative_error'])<.05,'package_spurious_joule_1nW':package_joule<1e-9,'passive_uniform_if_no_sources':True if meta['current_a'] or P else float(np.max(np.abs(t-300)))<1e-6,'stage_budget_1uW':all(abs(s['energy_error_w'])<1e-6 for s in stages)}
    r['checks']={k:bool(v) for k,v in checks.items()};r['passed']=all(checks.values());dump(case/'metrics.json',r)
    if export:meshio.write(case/'derived.vtu',meshio.Mesh(p,[('tetra',c)],point_data={'Temperature_K':t,'Potential_V':phi},cell_data={'body_id':[b],'J_A_m2':[jm],'q_W_m2':[qm],'Joule_W_m3':[joule_e/vol]}))
    print(case.name,'Tc/die/V',r['cold_ceramic_k'],r['die_mean_k'],voltage,'checks',r['checks'],flush=True);return r
