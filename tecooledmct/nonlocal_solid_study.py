"""Registered, target-blind solid-port construction followed by archival comparison.

No mesher, Elmer execution, optimization, fitting or legacy-model mutation.
"""
import argparse
import json
from pathlib import Path
import tempfile

import numpy as np

from .nonlocal_solid_network import (ROOT,GEOM,SELECTED,THERMAL_PORT,PORT_NAMES,
    inputs,build,coupled,finite_die_readout,record,read,sha)
from .solid_model_diagnostic import CASE,ARCHIVE,load_fields,linear_control
from .integrated_reference import geometry
from reports.field_geometry import plane_section

NOTE=ROOT/'docs/NONLOCAL_PORT_NETWORK_20261031.md'
LEVELS=(160e-6,80e-6,40e-6)


def write(path,data):
    def native(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        raise TypeError(type(x).__name__)
    path.write_text(json.dumps(data,indent=2,default=native,allow_nan=False)+'\n')


def planes(manifest):
    return [next(b['boxes_m'][0][2]+b['boxes_m'][0][5]/2 for b in manifest['bodies']
                 if b.get('stage')==s and b['kind']=='leg') for s in range(3)]


def cuts(operator,delta,coordinates):
    """Positive upward (+z), exact common finite-volume face; no weak indicators."""
    ei,ej=operator['edge_i'],operator['edge_j'];out=[]
    for st,z in enumerate(coordinates):
        select=(operator['edge_axis']==2)&np.isclose(operator['edge_plane'],z,rtol=0,atol=1e-12)
        if np.any(operator['body'][ei[select]]!=operator['body'][ej[select]]):
            raise ValueError('Cut coincides with a material interface')
        flux=operator['edge_G'][select]*(delta[ei[select]]-delta[ej[select]])
        bodies=operator['body'][ei[select]];area=operator['edge_area'][select]
        out.append({'stage_gap':st+1,'z_m':z,'bodies':{str(b):{
            'area_m2':float(area[bodies==b].sum()),'up_w':float(flux[bodies==b].sum())}
            for b in SELECTED if np.any(bodies==b)}})
    return out


def archived_comparison(manifest,coordinates,cache):
    """Read solved data ONLY after frozen_operators.json exists."""
    ledger=read(ARCHIVE/'checksums.json')['artifact_sha256']
    names=('metrics.json','case.sif','fields_t0001.vtu.gz','derived.vtu.gz')
    for name in names:
        if sha(CASE/name)!=ledger['cases/cu_off/'+name]:raise ValueError('Reference archive changed')
    metrics=read(CASE/'metrics.json')
    if metrics['cu_leads_on'] or metrics['au_bonds_on'] or metrics['current_a']!=.1:
        raise ValueError('Unmatched reference physics')
    if abs(metrics['deposited_power_w']-.002)>1e-12:raise ValueError('Reference source differs')
    d,t,_,fields,dist=load_fields(cache);p,c,body=(d[k] for k in ('points','cells','bodies'))
    if sha(GEOM/'mesh.npz')!=metrics['mesh_sha256']:raise ValueError('Reference mesh differs')
    ceramic=[metrics['domain_temperatures'][str(i)]['volume_mean_k'] for i in (1,2,3,4)]
    if abs(ceramic[0]-300.1148977882757)>1e-10:raise ValueError('Hot boundary control differs')
    out=[]
    for st,z in enumerate(coordinates):
        select=np.flatnonzero(np.isin(body,SELECTED)&(p[c,2].min(1)<z+1e-12)&(p[c,2].max(1)>z-1e-12))
        rows={}
        if len(select):
            sec=plane_section(p,c[select],axis=2,coordinate=z);tri=sec['xyz'];owners=select[sec['cells']]
            area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
            flux=area*fields['q_W_m2'][owners,2]
            for bid in SELECTED:
                mask=body[owners]==bid
                if np.any(mask):rows[str(bid)]={'area_m2':float(area[mask].sum()),'up_w':float(flux[mask].sum())}
        out.append({'stage_gap':st+1,'z_m':z,'bodies':rows})
    contacts=[]
    for row in manifest['contacts']:
        selected=[bid for bid in row['bodies'] if bid in SELECTED]
        others=[bid for bid in row['bodies'] if bid not in SELECTED]
        if not selected or not others:continue
        port=THERMAL_PORT[others[0]];f=d['faces'][d['boundaries']==row['boundary_id']];xyz=p[f]
        a=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
        mean=float(a@t[f].mean(1)/a.sum())
        contacts.append({'bodies':row['bodies'],'port':PORT_NAMES[port],'area_m2':float(a.sum()),
            'FEM_face_mean_k':mean,'FEM_face_min_k':float(t[f].min()),'FEM_face_max_k':float(t[f].max()),
            'ceramic_volume_mean_k':ceramic[port] if port<3 else None,
            'face_minus_ceramic_mean_k':mean-ceramic[port] if port<3 else None})
    m1=read(ROOT/'data/solid_model_diagnostic_20261031/diagnostic.json')
    by=m1['field_accounting']['body_integrals'] if 'body_integrals' in m1['field_accounting'] else None
    # Contact observations and raw gradients are diagnostics, never coefficients.
    return {'ceramic_means_k':ceramic,'die_mean_k':metrics['die_mean_k'],'voltage_v':metrics['voltage_v'],
        'sharp_cuts':out,'contacts':contacts,'node_map_max_distance_m':dist,
        'historical_full_device_qualification':metrics['full_device_qualification'],
        'M1_voltage_accounting_v':m1['field_accounting']['voltage_decomposition_v'],
        'input_sha256':{str((CASE/name).relative_to(ROOT)):sha(CASE/name) for name in (*names,'uncompressed_sha256.json')}}


def figures(manifest,operators,result,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    plt.rcParams.update({'font.size':9,'savefig.dpi':210,'axes.spines.top':False,'axes.spines.right':False})
    by={r['id']:r for r in manifest['bodies']};fig=plt.figure(figsize=(12,5.6))
    ax=fig.add_subplot(121,projection='3d')
    def box_faces(box):
        lo=np.array(box[:3])*1e3;hi=lo+np.array(box[3:])*1e3
        pts=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
        return [pts[ix] for ix in ([0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5])]
    for bid in (*SELECTED,174):
        for box in by[bid]['boxes_m']:
            mat=by[bid]['material'];color='#bb6a1f' if mat=='Cu' else '#b4bad4' if mat=='Alumina' else '#268075'
            ax.add_collection3d(Poly3DCollection(box_faces(box),facecolor=color,edgecolor=color,
                linewidth=.35,alpha=.90 if mat=='Cu' else .18 if mat=='Alumina' else .8))
    for bid,label in ((1,'T0'),(2,'T1'),(3,'T2')):
        faces=box_faces(by[bid]['boxes_m'][0]);ax.add_collection3d(Poly3DCollection(faces,facecolor='#c3cbd7',alpha=.07,edgecolor='#536078',linewidth=.5))
        box=by[bid]['boxes_m'][0];ax.text((box[0]+box[3])*1e3,(box[1]+box[4])*1e3,(box[2]+box[5])*1e3,label,size=9)
    for bid in (184,185,191):
        box=by[bid]['boxes_m'][1 if bid!=191 else 2]
        point=(np.array(box[:3])+np.array(box[3:])/2)*1e3
        ax.text(*point,str(bid),color='#773300',size=8)
    box=by[174]['boxes_m'][0];ax.text(box[0]*1e3,box[1]*1e3,(box[2]+box[5])*1e3,'P174 / X',size=8)
    ax.set(xlim=(-3.5,3.5),ylim=(-3.5,3.5),zlim=(1.4,5.4),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',title='Actual registered route/support coordinates')
    ax.set_box_aspect((1,1,.85));ax.view_init(elev=23,azim=-55)
    ax=fig.add_subplot(122);xy=np.array([[-1,1],[1,1],[1,-1],[-1,-1]])
    K=operators[-1]['K']
    for i in range(4):
        for j in range(i+1,4):
            g=-K[i,j]
            if g<1e-10:continue
            ax.plot(xy[[i,j],0],xy[[i,j],1],color='#607a91',lw=1+g*300)
            p=xy[[i,j]].mean(0);ax.text(*p,f'{g*1e3:.4g}',ha='center',va='center',bbox=dict(fc='white',ec='none',pad=2))
    for point,label in zip(xy,('T0: hot','T1: plate 2','T2: plate 3','X: P174 side')):
        ax.scatter(*point,s=500,color='#dce8ee',edgecolor='#334c61',zorder=3)
        ax.annotate(label,point,xytext=(0,19 if point[1]>0 else -27),textcoords='offset points',ha='center')
    ax.set(xlim=(-1.65,1.65),ylim=(-1.6,1.6),title='Condensed reciprocal thermal ports\nedge conductance (mW/K), 40 µm level')
    ax.axis('off');fig.text(.51,.07,'Cu and alumina share distributed interfaces.\nX is a side contact, not the cold ceramic.\nIsothermal plate/pad ports are an unqualified closure.',size=9)
    fig.text(.03,.015,'Geometry fixture only; plates shown as outlines. Raw support boxes are Cu-cut in the numerical operator.',size=8)
    fig.subplots_adjust(left=.01,right=.99,bottom=.13,top=.91,wspace=.16)
    for ext in ('png','pdf'):fig.savefig(out/f'geometry_and_ports.{ext}')
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4.8));ax=axes[0]
    ax.plot(range(4),result['off']['temperatures_k'][:4],'o--',label='Original reduced / network OFF')
    for level in result['levels']:
        ax.plot(range(4),level['temperatures_k'][:4],'.-',alpha=.65,label=f"Network {level['h_m']*1e6:.0f} µm")
    ax.plot(range(4),result['reference']['ceramic_means_k'],'s-',color='black',label='Archived 3D volume means')
    ax.set(xticks=range(4),xticklabels=['Hot','Plate 2','Plate 3','Cold'],ylabel='Temperature (K)',title='Fixed geometry-only model, no fitted parameters')
    ax.grid(alpha=.2);ax.legend(fontsize=8)
    ax=axes[1];rows=result['path_comparison'];x=np.arange(len(rows));w=.38
    ax.bar(x-w/2,[r['predicted_up_w']*1e3 for r in rows],w,label='40 µm network')
    ax.bar(x+w/2,[r['FEM_raw_up_w']*1e3 for r in rows],w,label='Archived raw gradient')
    ax.set(xticks=x,xticklabels=[f"{r['body']}\nGap {r['stage_gap']}" for r in rows],ylabel='Upward heat flow (mW)',title='Identical geometric midplanes; S = 0 paths')
    ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
    fig.text(.04,.015,'Conditional reduced prediction versus an unqualified coarse FEM comparator. Raw flux release failures remain; no causal accuracy claim.',size=8)
    fig.tight_layout(rect=(0,.05,1,1))
    for ext in ('png','pdf'):fig.savefig(out/f'prediction_and_sharp_paths.{ext}')
    plt.close(fig)


def run(out):
    out=Path(out)
    if out.exists():raise ValueError('Use a new output directory; evidence is append-only')
    manifest,audit=inputs();registration=NOTE.read_text().split('## Results')[0]
    out.mkdir(parents=True);ops=[];frozen={}
    # No solved metrics, M1 results or reference fields are opened in this loop.
    for h in LEVELS:
        op=build(manifest,h);ops.append(op);stem=f'operator_{round(h*1e6)}um'
        write(out/(stem+'.json'),record(op))
        arrays={k:op[k] for k in ('center','width','body','edge_i','edge_j','edge_G','edge_axis',
            'edge_plane','edge_area','H','K','source_per_A2','port_source_per_A2','u_per_A2',
            'electrical_cell_potential_per_A','joule_port_per_A2')}
        np.savez_compressed(out/(stem+'.npz'),**arrays)
        for ext in ('json','npz'):frozen[stem+'.'+ext]=sha(out/(stem+'.'+ext))
    sources=('tecooledmct/nonlocal_solid_network.py','tecooledmct/nonlocal_solid_study.py',
             'tecooledmct/integrated_reference.py','tecooledmct/fem_g2a.py','reports/field_geometry.py')
    write(out/'frozen_operators.json',{'registration':registration,'geometry_audit':audit,
        'source_sha256':{name:sha(ROOT/name) for name in sources},'operator_sha256':frozen,
        'ordering':'All three operators frozen before reference data or nonzero ON comparisons'})
    off=coupled(ops[0],on=False);old=linear_control(geometry(),300.1148977882757)
    if max(abs(np.array(off['temperatures_k'][:5])-old['temperatures_k']))>2e-6 or abs(off['module_voltage_v']-old['voltage_v'])>2e-8:
        raise ValueError('Original baseline control failed')
    coords=planes(manifest);levels=[]
    by={b['id']:b for b in manifest['bodies']};die=next(b for b in manifest['bodies'] if b['material']=='MCT')['boxes_m'][0]
    for op in ops:
        case=coupled(op);delta=case.pop('cell_temperature_delta_k');tp=np.array(case['temperatures_k'])[[0,1,2,5]]-case['temperatures_k'][0]
        residual=op['L'][:op['nodes'],:op['nodes']]@delta+op['B']@tp-op['source_per_A2']*.1**2
        if np.max(abs(residual))>1e-9:raise ValueError('Internal local heat balance failed')
        case.update({'h_m':op['h_m'],'nodes':op['nodes'],'sharp_cuts':cuts(op,delta,coords),
            'max_internal_heat_residual_w':float(np.max(abs(residual))),
            'finite_die_readout':finite_die_readout(case['temperatures_k'][4],.002,die[3]*die[4],die[5])})
        np.savez_compressed(out/f"prediction_{round(op['h_m']*1e6)}um.npz",temperature_k=delta+case['temperatures_k'][0])
        levels.append(case)
    off.pop('cell_temperature_delta_k')
    # This is the first comparison-data access, after fixed operators and solves.
    with tempfile.TemporaryDirectory(dir=out) as tmp:ref=archived_comparison(manifest,coords,Path(tmp))
    fine=levels[-1];rows=[];sensitivity=[]
    for k in range(3):
        a=fine['sharp_cuts'][k]['bodies'];b=ref['sharp_cuts'][k]['bodies'];coarse=levels[0]['sharp_cuts'][k]['bodies']
        if set(a)!=set(b):raise ValueError('Reference/prediction cut ownership differs')
        for bid in a:
            if not np.isclose(a[bid]['area_m2'],b[bid]['area_m2'],rtol=1e-8,atol=1e-18):raise ValueError('Cut area differs')
            rows.append({'stage_gap':k+1,'body':int(bid),'name':by[int(bid)]['name'],'z_m':coords[k],
                'area_m2':a[bid]['area_m2'],'predicted_up_w':a[bid]['up_w'],'FEM_raw_up_w':b[bid]['up_w'],
                'prediction_minus_FEM_w':a[bid]['up_w']-b[bid]['up_w']})
            rel=abs(coarse[bid]['up_w']-a[bid]['up_w'])/max(abs(a[bid]['up_w']),1e-12)
            sensitivity.append({'stage_gap':k+1,'body':int(bid),'coarse_fine_relative_power_change':rel})
    tc_change=abs(levels[0]['temperatures_k'][3]-fine['temperatures_k'][3]);flag=tc_change>.1 or any(r['coarse_fine_relative_power_change']>.05 for r in sensitivity)
    before=ref['ceramic_means_k'][3]-off['temperatures_k'][3];after=ref['ceramic_means_k'][3]-fine['temperatures_k'][3]
    result={'scope':'Geometry-derived local multiport plus unchanged affine P/N stages; not full-device FEM or physical validation',
        'registration_file':'frozen_operators.json','off':off,'levels':levels,'reference':ref,'path_comparison':rows,
        'residuals':{'FEM_minus_OFF_cold_k':before,'FEM_minus_ON_cold_k':after,
            'predicted_cold_warming_k':fine['temperatures_k'][3]-off['temperatures_k'][3],
            'FEM_minus_ON_isothermal_die_k':ref['die_mean_k']-fine['temperatures_k'][4],
            'FEM_minus_ON_finite_die_mean_k':ref['die_mean_k']-fine['finite_die_readout']['mean_k'],
            'FEM_minus_OFF_voltage_v':ref['voltage_v']-off['module_voltage_v'],
            'FEM_minus_ON_voltage_v':ref['voltage_v']-fine['module_voltage_v']},
        'discretization':{'coarse_fine_cold_change_k':tc_change,'path_changes':sensitivity,'unresolved_flag':flag,
            'meaning':'Registered sensitivity flag, not a discretization error estimate or physical uncertainty'},
        'identifiability':{'unique_mean_to_interface_mapping':False,'causal_attribution_complete':False,
            'limitations':['Isothermal ceramic/pad port closure omits lateral spreading and finite pad resistance',
                'A centroid node replaces the finite P174 side contact; current/temperature localization is omitted',
                'Other original Cu bridges/pads, finite ceramic thicknesses and attach spreading are absent',
                'Archived sharp raw gradients remain unqualified; this comparison cannot release the original mesh'],
            'one_next_experiment':'A bounded passive constant-k fixture of the retained routes plus original ceramic plates/pads; unit-temperature face ports at P/N attachment footprints, no Peltier/Joule or whole-device solve. Compare port reactions and plate mean-to-face offsets with this isothermal closure; pre-register a small cell cap before execution.'},
        'new_numerical_release':False,'Rev3_modified':False}
    for name,digest in frozen.items():
        if sha(out/name)!=digest:raise ValueError('Frozen operator changed')
    write(out/'diagnostic.json',result);figures(manifest,ops,result,out)
    write(out/'checksums.json',{'artifact_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    r=run(args.out);print(json.dumps({'residuals':r['residuals'],'discretization':r['discretization']},indent=2))


if __name__=='__main__':main()
