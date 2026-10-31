"""Read-only cross-model accounting; no mesher, compiler or FEM execution.

The original reduced solver is a control, not a calibrated replacement for FEM.
All additional field quantities retain explicit surfaces and sign conventions.
"""
import argparse
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
import re
import tempfile

import numpy as np

from .integrated_reference import (ROOT, Scenario, geometry, coefficients, solve,
                                   stage_thermoelectric)
from .fem_g1 import tetra_geometry
from .fem_g2a import PROPERTIES
from .corrected_thermal import material
from reports.field_geometry import node_map, cell_map

GEOM=ROOT/'fem/results/geometry_complete_checkpoint_20261030'
ARCHIVE=ROOT/'fem/results/corrected_coupled_thermal_20261030'
CASE=ARCHIVE/'cases/cu_off'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def linear_control(g, hot=300., current=.1, load=.002):
    """Independent explicit affine node equations, fixed hot ceramic, no wires."""
    if not np.isfinite([hot,current,load]).all() or load<0 or not 0<=current<=1:
        raise ValueError('Invalid bounded control')
    cs=coefficients(Scenario(current_a=current),g)
    a,r,k=np.array([[v[n] for v in cs] for n in ('alpha_v_k','r_ohm','k_w_k')])
    ga=1/g['die_attach_thickness_over_area_m_inverse']
    matrix=np.array([[-k[0],a[0]*current+k[0]-a[1]*current+k[1],-k[1],0,0],
        [0,-k[1],a[1]*current+k[1]-a[2]*current+k[2],-k[2],0],
        [0,0,-k[2],a[2]*current+k[2]+ga,-ga],
        [0,0,0,-ga,ga],[1,0,0,0,0]],float)
    rhs=np.r_[.5*current**2*(r[0]+r[1]),.5*current**2*(r[1]+r[2]),
              .5*current**2*r[2],load,hot]
    x=np.linalg.solve(matrix,rhs)
    if not np.isfinite(x).all() or min(x)<180 or max(x)>390:raise ValueError('Control outside domain')
    stages=[stage_thermoelectric(c,h,t,current) for c,h,t in zip(cs,x[:3],x[1:4])]
    residual=matrix@x-rhs
    derivative=np.linalg.solve(matrix,np.array([0,0,0,0,1.]))
    return {'temperatures_k':x.tolist(),'voltage_v':sum(v['voltage_v'] for v in stages),
            'stages':stages,'residuals_first_four_w_last_k':residual.tolist(),
            'd_temperatures_d_hot':derivative.tolist()}


def original_control(g, hot=300., current=.1, load=.002):
    clean={**g,'wires':[]}  # Disable series I*R/I²R as well as wire conduction.
    scenario=Scenario(ambient_k=hot,current_a=current,heat_sink_k_w=0.,
        detector_bias_w=.75*load,detector_absorbed_w=.25*load,cavity_pressure_pa=0.,
        cap_emissivity=0.,window_thermal_emissivity=0.,au_wire_conductance_scale=0.,
        cu_wire_conductance_scale=0.)
    result=solve(scenario,clean)
    independent=linear_control(g,hot,current,load)
    values=list(result['temperatures_k'].values())
    if max(abs(np.array(values)-independent['temperatures_k']))>2e-6 or abs(
            result['module_voltage_v']-independent['voltage_v'])>2e-8:
        raise ValueError('Original solver and independent linear equations disagree')
    if abs(result['global_energy_residual_w'])>1e-9 or max(abs(np.array(
            independent['residuals_first_four_w_last_k'])))>1e-9:
        raise ValueError('Reduced control energy gate failed')
    return {'original':result,'independent':independent}


def weak_channels(p,c,b,vol,grad,q,work,plane,hot,load):
    """Downward P1 indicator flow, NOT a sharp-face raw-gradient recovery."""
    w=(p[:,2]<=plane).astype(float);dw=np.einsum('ei,eij->ej',w[c],grad)
    cell=vol*np.einsum('ei,ei->e',dw,q)
    channels={str(int(bid)):float(cell[b==bid].sum()) for bid in np.unique(b) if np.any(cell[b==bid])}
    prefix=float(work@w[c].mean(1));mct=b==303
    source=float(load*(vol[mct]@w[c[mct]].mean(1))/vol[mct].sum()) if np.any(mct) else 0.
    total=float(cell.sum())
    return {'plane_m':plane,'positive_direction':'downward toward hot bath',
        'operator':'P1 nodal indicator; not geometrically sharp or raw bath flux',
        'body_down_w':channels,'total_down_w':total,'work_below_w':prefix,
        'source_below_w':source,'balance_residual_w':hot-total-prefix-source}


def load_fields(cache):
    import meshio
    d=np.load(GEOM/'mesh.npz');p,c,b=(d[k] for k in ('points','cells','bodies'))
    uncompressed=read(CASE/'uncompressed_sha256.json');fields=[]
    for name in ('fields_t0001.vtu','derived.vtu'):
        raw=gzip.decompress((CASE/(name+'.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=uncompressed[name]:raise ValueError('Field checksum mismatch')
        target=cache/name;target.write_bytes(raw);fields.append(meshio.read(target))
    native,derived=fields;ix,dist=node_map(p,native.points)
    cell_map(c,np.argsort(ix)[native.cells_dict['tetra']])
    dx,_=node_map(p,derived.points);dc=cell_map(c,np.argsort(dx)[derived.cells_dict['tetra']])
    data={name:values['tetra'][dc] for name,values in derived.cell_data_dict.items()}
    if not np.array_equal(data['body_id'],b):raise ValueError('Derived body IDs differ')
    t=native.point_data['temperature'].ravel()[ix];phi=native.point_data['potential'].ravel()[ix]
    if not np.array_equal(t,derived.point_data['Temperature_K'].ravel()[dx]):raise ValueError('Field T differs')
    if not np.array_equal(phi,derived.point_data['Potential_V'].ravel()[dx]):raise ValueError('Field potential differs')
    return d,t,phi,data,dist


def field_audit(metrics,g,cache):
    d,t,phi,data,dist=load_fields(cache);p,c,b=(d[k] for k in ('points','cells','bodies'))
    m=read(GEOM/'manifest.json');by={r['id']:r for r in m['bodies']};vol,grad=tetra_geometry(p,c)
    gt=np.einsum('ei,eij->ej',t[c],grad);ef=-np.einsum('ei,eij->ej',phi[c],grad)
    props=np.empty((len(c),3))
    for bid,row in by.items():
        select=b==bid;props[select]=np.array(material(row['material'],t[c[select]])).mean(2).T
    k,sigma,seebeck=props.T;j=sigma[:,None]*(ef-seebeck[:,None]*gt)
    q=-k[:,None]*gt+(seebeck*t[c].mean(1))[:,None]*j
    for value,name in ((j,'J_A_m2'),(q,'q_W_m2')):
        if np.max(abs(value-data[name]))/max(np.max(abs(value)),1e-30)>1e-11:
            raise ValueError('Raw/derived constitutive reconstruction failed: '+name)
    work=vol*np.einsum('ei,ei->e',j,ef);joule=vol*np.einsum('ei,ei->e',j,j)/sigma
    if abs(work.sum()-metrics['work_w'])>2e-9 or abs(joule.sum()-metrics['Joule_w'])>2e-9:
        raise ValueError('Archived electrical integrals differ')
    body={str(bid):{'name':row['name'],'kind':row['kind'],'material':row['material'],
        'volume_m3':float(vol[b==bid].sum()),'work_w':float(work[b==bid].sum()),
        'joule_w':float(joule[b==bid].sum())} for bid,row in by.items()}
    # Geometry/material correspondence is checked against actual positive-volume cells and SIF.
    sif=(CASE/'case.sif').read_text();names=sorted({row['material'] for row in by.values()})
    for name in ('P','N','Cu'):
        number=names.index(name)+1;block=re.search(r'^Material '+str(number)+r'\n(.*?)^End',sif,re.M|re.S).group(1)
        for label,expected in zip(('Heat Conductivity','Electric Conductivity','Seebeck Coefficient'),PROPERTIES[name][:3]):
            value=float(re.search(label+r' = Real ([^\n]+)',block).group(1))
            if not np.isclose(value,expected,rtol=1e-14,atol=1e-20):raise ValueError('Material correspondence failed')
    stage_rows=[];means=[metrics['domain_temperatures'][str(i)]['volume_mean_k'] for i in (1,2,3,4)]
    cs=coefficients(Scenario(current_a=.1),g);current=metrics['current_a']
    for st,coeff in enumerate(cs):
        rows=[r for r in by.values() if r.get('stage')==st and r['kind']=='leg']
        if len(rows)!=2*g['stages'][st]['couples']:raise ValueError('Wrong leg count')
        for row in rows:
            box=row['boxes_m'][0];v=box[3]*box[4]*box[5]
            if abs(body[str(row['id'])]['volume_m3']/v-1)>1e-7:raise ValueError('Leg volume mismatch')
        sel=np.isin(b,[r['id'] for r in rows]);reversible=float((work[sel]-joule[sel]).sum())
        stage_rows.append({'stage':st,**g['stages'][st],**coeff,
            'ceramic_hot_k':means[st],'ceramic_cold_k':means[st+1],
            'PN_dissipative_resistance_ohm':float(joule[sel].sum())/current**2,
            'raw_midleg_apparent_PN_conductance_w_k':-metrics['stage_thermoelectric_decomposition'][st]['fourier_down_w']/(means[st]-means[st+1]),
            'current_weighted_effective_drop_k':reversible/(current*coeff['alpha_v_k']),
            'ideal_at_ceramic_means':stage_thermoelectric(coeff,means[st],means[st+1],current)})
    hot=metrics['hot_out_reaction_w'];load=metrics['deposited_power_w'];weak=[]
    for st in range(3):
        leg=next(r for r in by.values() if r.get('stage')==st and r['kind']=='leg')
        z=leg['cut_coordinate_m'];row=weak_channels(p,c,b,vol,grad,q,work,z,hot,load)
        if abs(row['balance_residual_w'])>1e-6:raise ValueError('Same-surface control-volume closure failed')
        weak.append(row)
    registered=[]
    for bid,expected in zip((2,3),metrics['stage_control_volumes'][1:]):
        box=by[bid]['boxes_m'][0];row=weak_channels(p,c,b,vol,grad,q,work,box[2]+.2*box[5],hot,load)
        if abs(row['total_down_w']-expected['hot_out_w'])>2e-9:raise ValueError('Registered band transfer differs')
        registered.append(row)
    masks={name:np.isin(b,[bid for bid,row in by.items() if row['material'] in materials])
           for name,materials in [('PN',('P','N')),('Cu',('Cu',)),('passive',tuple(
               name for name in names if name not in ('P','N','Cu')))]}
    losses={name:float(joule[mask].sum()) for name,mask in masks.items()}
    ideal_r=sum(row['r_ohm'] for row in cs);ideal_s=sum(row['alpha_v_k']*(h-tc) for row,h,tc in zip(cs,means,means[1:]))
    decomposition={'ideal_PN_ohmic_v':current*ideal_r,'Cu_ohmic_v':losses['Cu']/current,
        'PN_nonuniform_current_extra_v':losses['PN']/current-current*ideal_r,
        'passive_ohmic_v':losses['passive']/current,'ceramic_mean_Seebeck_v':ideal_s,
        'nonisothermal_reversible_correction_v':float((work-joule).sum())/current-ideal_s,
        'terminal_vs_integrated_work_v':metrics['voltage_v']-float(work.sum())/current}
    if abs(sum(decomposition.values())-metrics['voltage_v'])>2e-9:raise ValueError('Voltage accounting does not close')
    ideal=[row['ideal_at_ceramic_means'] for row in stage_rows]
    mismatch=[ideal[0]['qc_w']-ideal[1]['qh_w'],ideal[1]['qc_w']-ideal[2]['qh_w'],ideal[2]['qc_w']-load]
    interfaces={tuple(row['bodies']):row for row in metrics['interfaces']}
    bottom=interfaces[(4,302)]['temperature_area_mean_k'];top=interfaces[(302,303)]['temperature_area_mean_k']
    die=metrics['die_mean_k'];cold=metrics['cold_ceramic_k'];attach=load*g['die_attach_thickness_over_area_m_inverse']
    return {'body_integrals':body,'stages':stage_rows,'node_residuals_at_archived_means_w':mismatch,
        'same_indicator_midleg_channels':weak,'registered_band_replay':registered,
        'voltage_decomposition_v':decomposition,'reconstructed_work_w':float(work.sum()),
        'reconstructed_joule_w':float(joule.sum()),'bijective_node_max_distance_m':dist,
        'die_readout':{'ceramic_mean_to_attach_bottom_k':bottom-cold,
            'attach_face_drop_k':top-bottom,'attach_1D_drop_k':attach,
            'die_bottom_to_volume_mean_k':die-top,'isothermal_reduced_attach_drop_k':attach,
            'total_FEM_die_minus_ceramic_k':die-cold,
            'extra_volume_readout_and_spreading_k':die-cold-attach,
            'uniform_heated_adiabatic_top_1D_die_offset_k':load*by[303]['boxes_m'][0][5]/(3*float(material('MCT',die)[0])*g['die_area_m2']),
            'scope':'Observed face/volume differences; not a calibrated correction or a converged physical resistance'}}


def legacy_review():
    """Hash-checked historic observations; no import of their geometric operator."""
    from .fem_g3b_run import verify_used_source
    old=ROOT/'fem/results/g3b_checkpoint_20261029';ledger=read(old/'checksums.json');paths=[];rows=[]
    for case in ('solid_reference_h0','lead_only_0','vacuum_a0','nitrogen_0','argon_0','krypton_0'):
        p=old/'cases'/case/'metrics.json';paths.append(p)
        if sha(p)!=ledger['artifact_sha256'][str(p.relative_to(old))]:raise ValueError('Historical G3b observation changed')
        d=read(p);rows.append({'case':case,'die_k':d['die_mean_k'],'voltage_v':d['voltage_v']})
    for case in ('nitrogen_0','lead_only_0'):
        p=old/'cases'/case/'execution.json';paths.append(p)
        for name,h in read(p)['source_sha256'].items():verify_used_source(p.parent,name,h)
    paths.extend([old/'checksums.json',old/'meshes/mesh_h0/manifest.json',
        ROOT/'reports/generated/HgCdTe_Engineering_Assessment.pdf',
        ROOT/'docs/PHASE1_G3B_RESULT.md',ROOT/'docs/G3B_REPRODUCIBILITY.md',ROOT/'docs/OPENFOAM_FEASIBILITY.md'])
    return {'historical_only':True,'new_OpenFOAM_execution':False,'observations':rows,
        'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths}}


def figures(result,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'serif','font.size':10,'mathtext.fontset':'dejavuserif','pdf.fonttype':42})
    def save(fig,name):
        for ext in ('png','pdf'):
            fig.savefig(out/(name+'.'+ext),dpi=350,bbox_inches='tight',pad_inches=.08,
                **({'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}))
        plt.close(fig)
    f=result['field_accounting'];fig,axs=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    for name,label,color in [('hot300','Reduced: hot 300 K','#578d9b'),('matched_hot','Reduced: matched hot','#b78849')]:
        axs[0].plot(range(5),list(result['controls'][name]['original']['temperatures_k'].values()),'o--',label=label,color=color)
    actual=[row['ceramic_hot_k'] for row in f['stages']]+[result['FEM_summary']['cold_ceramic_k'],result['FEM_summary']['die_mean_k']]
    axs[0].plot(range(5),actual,'s-',label='Archived 3D volume means',color='#8e554f')
    axs[0].set_xticks(range(5),['Hot','Interm. 1','Interm. 2','Cold','Die']);axs[0].set_ylabel('Temperature (K)')
    axs[0].legend(fontsize=8);axs[0].grid(alpha=.2);axs[0].set_title('Node observations; lines guide the eye')
    decomp=f['voltage_decomposition_v'];matched=result['controls']['matched_hot']['original']
    values=[decomp['ceramic_mean_Seebeck_v']-(matched['module_voltage_v']-decomp['ideal_PN_ohmic_v']),
            decomp['Cu_ohmic_v'],decomp['nonisothermal_reversible_correction_v'],decomp['PN_nonuniform_current_extra_v']]
    axs[1].barh(range(4),np.array(values)*1000,color=['#578d9b','#b78849','#8e554f','#759064'])
    axs[1].set_yticks(range(4),['Ceramic-mean lift','All internal Cu','Reversible weighting','P/N current crowding']);axs[1].invert_yaxis()
    axs[1].set_xlabel('Voltage contribution: FEM minus matched reduced (mV)');axs[1].axvline(0,color='black',lw=.6);axs[1].grid(axis='x',alpha=.2)
    axs[1].set_title('Volume-work accounting, not a fitted voltage')
    save(fig,'matched_controls')
    fig,ax=plt.subplots(figsize=(8,4.2),layout='constrained');x=np.arange(3);pos=np.zeros(3);neg=np.zeros(3)
    groups=[('P/N net pump',lambda bid,row:row['material'] in ('P','N'),'#578d9b'),
        ('Cu links 184/185',lambda bid,row:bid in ('184','185'),'#b78849'),
        ('Cu return 191',lambda bid,row:bid=='191','#8e554f'),
        ('Alumina supports',lambda bid,row:row['material']=='Alumina','#759064')]
    for label,predicate,color in groups:
        values=np.array([sum(v for bid,v in c['body_down_w'].items() if predicate(bid,f['body_integrals'][bid])) for c in f['same_indicator_midleg_channels']])*1000
        ax.bar(x,values,bottom=np.where(values>=0,pos,neg),label=label,color=color)
        pos+=np.maximum(values,0);neg+=np.minimum(values,0)
    total=[row['total_down_w']*1000 for row in f['same_indicator_midleg_channels']]
    ax.plot(x,total,'ko',label='All-solid net');ax.axhline(0,color='black',lw=.6)
    ax.set_xticks(x,['Stage 1 gap','Stage 2 gap','Stage 3 gap']);ax.set_ylabel('Downward P1-indicator heat flow (mW)')
    ax.set_title('Common indicator in each gap; negative = warm-to-cold leakage')
    ax.legend(ncol=2,fontsize=9);ax.grid(axis='y',alpha=.2);save(fig,'same_surface_heat_paths')


def run(out):
    out=Path(out)
    if out.exists():raise ValueError('Use a new diagnostic output directory')
    metrics=read(CASE/'metrics.json');g=geometry()
    if metrics['cu_leads_on'] or metrics['au_bonds_on'] or metrics['enclosure']!='absent; no radiation/gas imported or executed':
        raise ValueError('Unmatched archive physics')
    if sha(GEOM/'mesh.npz')!=metrics['mesh_sha256']:raise ValueError('Wrong actual mesh')
    for name in ('metrics.json','case.sif','fields_t0001.vtu.gz','derived.vtu.gz'):
        relative='cases/cu_off/'+name
        if sha(CASE/name)!=read(ARCHIVE/'checksums.json')['artifact_sha256'][relative]:raise ValueError('Archived evidence changed')
    controls={name:original_control(g,h,i,p) for name,h,i,p in (
        ('hot300',300.,.1,.002),('matched_hot',metrics['hot_ceramic_k'],.1,.002),
        ('passive_uniform',300.,0.,0.),('passive_loaded',300.,0.,.002))}
    baseline=controls['hot300']['original']
    if abs(baseline['MCT_die_k']-257.756276)>2e-6 or abs(baseline['module_voltage_v']-.585608855)>2e-8:
        raise ValueError('Quoted reduced baseline not reproduced')
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(dir=out) as tmp:fields=field_audit(metrics,g,Path(tmp))
    matched=controls['matched_hot']['original'];residual={
        'original_FEM_minus_reduced_die_k':metrics['die_mean_k']-baseline['MCT_die_k'],
        'hot_boundary_effect_die_k':matched['MCT_die_k']-baseline['MCT_die_k'],
        'after_hot_match_die_residual_k':metrics['die_mean_k']-matched['MCT_die_k'],
        'observed_die_readout_difference_k':fields['die_readout']['extra_volume_readout_and_spreading_k'],
        'remaining_cold_ceramic_residual_k':metrics['cold_ceramic_k']-matched['temperatures_k']['cold_ceramic'],
        'FEM_minus_matched_module_voltage_v':metrics['voltage_v']-matched['module_voltage_v']}
    paths=[GEOM/'mesh.npz',GEOM/'manifest.json',GEOM/'checksums.json',ARCHIVE/'checksums.json',
        CASE/'metrics.json',CASE/'case.sif',CASE/'fields_t0001.vtu.gz',CASE/'derived.vtu.gz',
        CASE/'uncompressed_sha256.json',ROOT/'docs/MATCHED_SOLID_MODEL_DIAGNOSTIC_20261031.md']
    # The registration text is included verbatim; later results prose is not an input.
    registration=(ROOT/'docs/MATCHED_SOLID_MODEL_DIAGNOSTIC_20261031.md').read_text().split('## Results')[0]
    legacy=legacy_review()
    result={'scope':'Archived-field accounting and four small original reduced solves; NO new FEM or fitted bypass',
        'controls':controls,'FEM_summary':{k:metrics[k] for k in ('current_a','deposited_power_w','nodes','tetrahedra','die_mean_k','cold_ceramic_k','hot_ceramic_k','voltage_v','full_device_qualification')},
        'geometry_inputs':g,'constant_materials':{name:{'k_w_mk':PROPERTIES[name][0],
            'rho_ohm_m':1/PROPERTIES[name][1],'Seebeck_v_k':PROPERTIES[name][2]} for name in ('P','N','Cu')},
        'field_accounting':fields,'residuals':residual,'registration':registration,
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ROOT/'tecooledmct/integrated_reference.py',
            ROOT/'tecooledmct/fem_g1.py',ROOT/'tecooledmct/fem_g2a.py',ROOT/'tecooledmct/corrected_thermal.py',ROOT/'reports/field_geometry.py')},
        'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths if p.suffix!='.md'},
        'legacy_review':legacy,'new_numerical_release':False,'causal_temperature_attribution_complete':False}
    (out/'diagnostic.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    figures(result,out)
    print(json.dumps(residual,indent=2));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
