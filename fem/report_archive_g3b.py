#!/usr/bin/env python3
"""Fail-closed evidence/report builder for actual G3b coupled enclosure solves."""
import csv,gzip,json,os,re,shutil,subprocess
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors,cm
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from tecooledmct.g2d_data import ROOT,sha,dump
from tecooledmct.fem_g3b_data import preserve
from tecooledmct.fem_g3b_run import verify_used_source
from tecooledmct.fem_g3b_physics import payload
from tecooledmct.fem_g3b_exchange import gas_properties,gas_conductances,rayleigh_screen

CONTROLS=['passive_h0','solid_reference_h0']
COUPLED=['lead_only_0','vacuum_a0','nitrogen_0','argon_0','krypton_0','window_high_0','nitrogen_patch1','nitrogen_feedthrough','package_sigma_100']
OPERATORS=['operator_h0','operator_h0p1','operator_h1','operator_bath','operator_feedthrough']


def read(p):return json.loads(p.read_text())


def csvwrite(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def refinement(a,b):
    r={k:abs(a[k]-b[k]) for k in ('die_mean_k','die_max_k','cold_ceramic_k')}
    r['reference_lift_k']=300-b['cold_ceramic_k'];r['max_change_over_lift']=max(r[k] for k in ('die_mean_k','die_max_k','cold_ceramic_k'))/r['reference_lift_k']
    r['voltage_relative_change']=abs(a['voltage_v']/b['voltage_v']-1)
    r['passed']=r['max_change_over_lift']<.01 and r['voltage_relative_change']<.01
    return r


def validate(raw,checkpoint=False):
    integrity=preserve();cases={};resources=[];execution_hashes={};payload_verification={}
    labels=CONTROLS+[n for n in COUPLED if not(checkpoint and n=='nitrogen_feedthrough')]
    for label in labels:
        case=raw/label;r=read(case/'metrics.json');ex=read(case/'execution.json');s=ex['solver_status']
        mesh=raw/'mesh_h0' if label in CONTROLS else raw/Path(r['operator_path']).name
        if not r['passed'] or not all(r['checks'].values()) or s['exit_code'] or s['nonlinear_last_relative_change']>=1e-9:raise ValueError('Unaccepted actual execution '+label)
        if sha(case/'case.sif')!=ex['sif_sha256'] or sha(case/r['field_source'])!=ex['vtu_sha256'] or ex['vtu_sha256']!=r['vtu_sha256'] or ex['mesh_sha256']!=sha(mesh/'mesh.npz'):raise ValueError('Changed actual fields/SIF/mesh '+label)
        post='reference_post' if label in CONTROLS else 'post'
        if r['postprocessor_sha256']!=sha(ROOT/f'tecooledmct/fem_g3b_{post}.py'):raise ValueError('Changed postprocessor '+label)
        for n,h in ex['source_sha256'].items():verify_used_source(case,n,h)
        if label in COUPLED:
            if not r['checks']['immutable_operator_inputs'] or any(sha(case/n)!=h for n,h in r['exchange_input_sha256'].items()):raise ValueError('Changed exchange payload '+label)
            audit_dir=ROOT/'outputs/g3b-payload-audit'/label;audit_dir.mkdir(parents=True,exist_ok=True)
            regenerated=payload(mesh,audit_dir,r)
            if regenerated!=r['exchange_input_sha256']:raise ValueError('Archived operator/configuration does not regenerate actual executed payload '+label)
            payload_verification[label]=regenerated
        cases[label]=r;execution_hashes[label]=ex['source_sha256']
        resources.append({'case':label,'nodes':r['nodes'],'tetrahedra':r['tetrahedra'],**{k:s[k] for k in ('exit_code','elapsed_s','peak_rss_kib','nonlinear_iterations','nonlinear_last_relative_change')}})
    meshes={n:read(raw/n/'audit.json') for n in ('mesh_h0','mesh_h1','mesh_bath','mesh_feedthrough')}
    for n,a in meshes.items():
        if not(a['passed'] and a['connectivity']['passed'] and a['elmer_mapping']['passed'] and a['domains']==215 and a['graph']['unique_path'] and a['graph']['nodes']==181 and a['graph']['edges']==180):raise ValueError('Mesh topology failure '+n)
        if a['mesh_npz_sha256']!=sha(raw/n/'mesh.npz'):raise ValueError('Changed mesh '+n)
    operators={n:read(raw/n/'audit.json') for n in OPERATORS};operator_checks={}
    for n,a in operators.items():
        op=raw/n;d=np.load(op/'operators.npz');area,F,W,gap=(d[k] for k in ('areas','view_factors','exchange_m2','distance_m'));weights=load_npz(op/'weights.npz')
        if not(a['passed'] and a['closed_skin_all_edge_incidence_two'] and a['actual_boundary_mapping_verified'] and a['elmer_mapping']['passed'] and a['mesh_sha256']==sha(op/'mesh.npz')):raise ValueError('Operator geometry failure '+n)
        for name,h in a['source_sha256'].items():
            if sha(ROOT/name)!=h:raise ValueError('Changed operator source '+name)
        bulk=raw/{'operator_h0':'mesh_h0','operator_h0p1':'mesh_h0','operator_h1':'mesh_h1','operator_bath':'mesh_bath','operator_feedthrough':'mesh_feedthrough'}[n]
        if a['source_mesh_sha256']!=sha(bulk/'mesh.npz'):raise ValueError('Changed operator input mesh')
        operator_checks[n]={'closure_max_error':float(abs(F.sum(axis=1)-1).max()),'reciprocity_max_m2':float(abs(W-W.T).max()),'nonnegative':bool(np.all(F>=0) and np.all(W>=0) and np.all(gap>0)),'patch_weight_sum_error':float(abs(np.asarray(weights.sum(axis=1)).ravel()-1).max()),'no_filled_visibility_zeros':bool(np.all(W[(d['raw_ray_view_factors']+d['raw_ray_view_factors'].T)==0]==0))}
        ch=operator_checks[n]
        if ch['closure_max_error']>1e-10 or ch['reciprocity_max_m2']>1e-15 or ch['patch_weight_sum_error']>1e-12 or not(ch['nonnegative'] and ch['no_filled_visibility_zeros']):raise ValueError('Independent operator algebra failure '+n)
    patch=refinement(cases['nitrogen_0'],cases['nitrogen_patch1']);bulk=({'passed':False,'status':'NOT QUALIFIED: all three integrated fine points fail the independent direct-bath1% gate'} if checkpoint else refinement(cases['nitrogen_patch1'],cases['nitrogen_feedthrough']))
    a,b=cases['nitrogen_0'],cases['package_sigma_100'];isolation={'die_change_k':abs(a['die_mean_k']-b['die_mean_k']),'voltage_change_v':abs(a['voltage_v']-b['voltage_v'])};isolation['passed']=isolation['die_change_k']<1e-4 and isolation['voltage_change_v']<1e-6
    if not(patch['passed'] and (checkpoint or bulk['passed']) and isolation['passed']):raise ValueError('Refinement or electrical isolation gate')
    rejected={}
    for label in ('nitrogen_fine_verified','nitrogen_bath')+(('nitrogen_feedthrough',) if checkpoint else ()):
        case=raw/label;r=read(case/'metrics.json');ex=read(case/'execution.json');operator=raw/Path(r['operator_path']).name
        if r['passed'] or {k for k,v in r['checks'].items() if not v}!={'direct_bath_1pct'} or ex['solver_status']['exit_code'] or ex['solver_status']['nonlinear_last_relative_change']>=1e-9:raise ValueError('Unexpected rejected-case status '+label)
        if sha(case/'case.sif')!=ex['sif_sha256'] or sha(case/r['field_source'])!=ex['vtu_sha256'] or sha(operator/'mesh.npz')!=ex['mesh_sha256']:raise ValueError('Changed rejected actual execution')
        for name,digest in ex['source_sha256'].items():verify_used_source(case,name,digest)
        rejected[label]={'accepted':False,'solver_status':ex['solver_status'],'nodes':r['nodes'],'tetrahedra':r['tetrahedra'],'direct_bath_relative_error':r['direct_bath_relative_error'],'global_energy_error_w':r['global_energy_error_w'],'free_thermal_residual_l1_w':r['free_thermal_residual_l1_w'],'worst_cut_relative_error':r['worst_cut_relative_error'],'temperature_voltage_sensitivity_only':{k:v for k,v in refinement(cases['nitrogen_patch1'],r).items() if k!='passed'},'all_other_checks_pass':True}
    plates={n:read(raw/n/'verification.json') for n in ('radiation_plates_v2','gas_radiation_plates_v2')}
    for n,r in plates.items():
        case=raw/n
        if not r['passed'] or r['solver_status']['exit_code'] or sha(case/'case.sif')!=r['sif_sha256'] or sha(sorted(case.glob('fields*.vtu'))[-1])!=r['vtu_sha256']:raise ValueError('Independent Elmer plate failure '+n)
    testlog=(ROOT/'logs/pytest-g3b-final.log').read_text();test=re.search(r'(?m)^(\d+) passed(?:,.*)? in ',testlog)
    if not test or re.search(r'\b(?:FAILED|ERROR|failed)\b',testlog):raise ValueError('Completed full passing tests required')
    for n,f in [('check','summary.json'),('pellet','pellet_geometry_study.json')]:read(ROOT/f'outputs/{n}-g3b'/f)
    for n in ('cli','geometry'):
        if not (ROOT/f'logs/{n}-g3b.log').exists():raise ValueError('Missing required check')
    return cases,resources,{'passed':True,'qualified_scope':'verified coarse integrated checkpoint' if checkpoint else 'full G3b','full_g3b_qualified':not checkpoint,'unaccepted_fine_cases':rejected,'protected_integrity':integrity,'mesh_audits':meshes,'operator_audits':operators,'operator_algebra':operator_checks,'surface_refinement':patch,'bulk_refinement':bulk,'electrical_regularization_sensitivity':isolation,'independent_plate_checks':plates,'execution_source_sha256':execution_hashes,'regenerated_payload_matches_actual_execution':payload_verification,'tests_passed':int(test.group(1))}


def field_plots(raw,case,out):
    import meshio
    operator=raw/Path(read(case/'case.json')['operator_path']).name;d=np.load(operator/'mesh.npz');p,f,bt=(d[k] for k in ('points','faces','boundaries'));m=read(operator/'manifest.json');field=meshio.read(case/'derived.vtu');t=field.point_data['Temperature_K'];phi=field.point_data['Potential_V'];c=d['cells'];b=d['bodies'];by={x['id']:x for x in m['bodies']}
    xyz=p[f]*1e3;center=xyz.mean(axis=1);norm=colors.Normalize(float(t.min()),float(t.max()));cmap=plt.get_cmap('inferno');ex=bt<1000
    # Only visibility is changed for the cutaway view; all solids remained in the PDE.
    cap=m['cavity']['cap_body'];window=m['cavity']['window_body'];hidden=set(np.unique(c[np.isin(b,[cap,window])]))
    inner=ex & ~np.all(np.isin(f,list(hidden)),axis=1)
    fig=plt.figure(figsize=(13,5.4))
    for i,sel in enumerate((ex,inner),1):
        ax=fig.add_subplot(1,2,i,projection='3d');poly=Poly3DCollection(xyz[sel],facecolors=cmap(norm(t[f[sel]].mean(axis=1))),edgecolors='none',rasterized=True);ax.add_collection3d(poly);ax.set(xlim=(-16,16),ylim=(-9,9),zlim=(-3.5,9),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',title='Full solved exterior' if i==1 else 'Display cutaway: cap/window hidden');ax.set_box_aspect((32,18,15));ax.view_init(27,-58)
        if i==2:
            patches=read(operator/'patches.json')
            def endpoint(tag):
                rows=[v for v in patches if v['original_boundary']==tag];areas=np.array([v['area_m2'] for v in rows]);return areas@np.array([v['center_m'] for v in rows])/areas.sum()*1e3
            for warm,cold,color in ((200,201,'#60dbff'),(202,203,'#60dbff'),(204,103,'#9bef88'),(206,104,'#9bef88')):
                u=np.linspace(0,1,30);a,b0=endpoint(warm),endpoint(cold);line=a[None,:]*(1-u[:,None])+b0[None,:]*u[:,None];line[:,2]+=.7*np.sin(np.pi*u);ax.plot(*line.T,'--',color=color,lw=1)
    fig.subplots_adjust(left=.01,right=.88,top=.82,bottom=.05,wspace=.03);fig.colorbar(cm.ScalarMappable(norm=norm,cmap=cmap),ax=fig.axes,shrink=.65,label='Actual T (K)');fig.suptitle('N2 100 Pa, .1 A, 2 mW; dashed Au/Cu links are schematic 1D thermal paths');fig.savefig(out/'actual_enclosure_temperature.png',dpi=170,bbox_inches='tight');plt.close(fig)
    # Actual interior current/heat flux fields on a narrow section of the TEC.
    cc=p[c].mean(axis=1)*1e3;tec=b<=m['original_TEC_domains'];sel=tec&(abs(cc[:,1])<.22);q=field.cell_data['q_W_m2'][0];j=field.cell_data['J_A_m2'][0];fig,axs=plt.subplots(1,3,figsize=(13,4.2))
    for ax,values,title,unit in [(axs[0],phi[c].mean(axis=1),'Potential','V'),(axs[1],np.linalg.norm(j,axis=1),'Current density','A/m²'),(axs[2],np.linalg.norm(q,axis=1),'Heat flux','W/m²')]:
        plot=ax.scatter(cc[sel,0],cc[sel,2],c=values[sel],s=2,cmap='viridis',rasterized=True);ax.set(xlabel='x (mm)',ylabel='z (mm)',title=title);fig.colorbar(plot,ax=ax,label=unit,shrink=.8)
    fig.suptitle('Actual tetrahedral fields, |y| < .22 mm; local peaks are not convergence claims');fig.tight_layout();fig.savefig(out/'actual_tec_flux_section.png',dpi=180);plt.close(fig)
    from tecooledmct.fem_g3b_physics import powers
    cfg=read(case/'case.json');boundary=powers(operator,t,cfg);patches=read(operator/'patches.json');cent=np.array([x['center_m'] for x in patches])*1e3;areas=np.array([x['area_m2'] for x in patches]);rows=[]
    for i,patch in enumerate(patches):rows.append({'patch':i,'owner':patch['owner_name'],'area_m2':areas[i],'temperature_k':float(boundary['patch_temperature_k'][i]),**{key+'_in_w':float(value[i]) for key,value in boundary['mechanisms'].items()}})
    csvwrite(out/'actual_patch_exchange.csv',rows)
    fig=plt.figure(figsize=(11,4.8))
    for j,key in enumerate(('radiation','gas'),1):
        ax=fig.add_subplot(1,2,j,projection='3d');flux=boundary['mechanisms'][key]/areas;lim=max(abs(flux).max(),1e-9);plot=ax.scatter(*cent.T,c=flux,s=4,cmap='coolwarm',vmin=-lim,vmax=lim);ax.set(xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',title=key.capitalize()+' inward patch-average flux');ax.view_init(22,-58);fig.colorbar(plot,ax=ax,shrink=.65,label='W/m²')
    fig.suptitle('Actual final N2 field: positive heats the solid; reduced surface operators');fig.tight_layout();fig.savefig(out/'actual_surface_exchange.png',dpi=170);plt.close(fig)
    xy=np.array(m['package_registry']['feedthroughs']['centers_xy_m'])*1e3;fig,ax=plt.subplots(figsize=(6,5));theta=np.linspace(0,2*np.pi,150);ax.plot(7.1*np.cos(theta),7.1*np.sin(theta),label='Assumed cap interior')
    for i,(x,y) in enumerate(xy):
        ax.add_patch(plt.Circle((x,y),.55,color='gray',alpha=.3));ax.add_patch(plt.Circle((x,y),.22,color='goldenrod'));ax.text(x,y+.7,f'instance {i}',ha='center',fontsize=8)
    ax.add_patch(plt.Rectangle((-3.2,-3.2),6.4,6.4,fill=False,color='k'));ax.set(xlim=(-8,8),ylim=(-8,8),xlabel='x (mm)',ylabel='y (mm)',title='Nine meshed glass/pin instances; no OEM numbering');ax.set_aspect('equal');fig.tight_layout();fig.savefig(out/'nine_feedthrough_layout.png',dpi=160);plt.close(fig)


def charts(raw,out,cases,summary):
    field_label='nitrogen_feedthrough' if 'nitrogen_feedthrough' in cases else 'nitrogen_patch1'
    field_plots(raw,raw/field_label,out)
    labels=['solid_reference_h0','lead_only_0','vacuum_a0','nitrogen_0','argon_0','krypton_0','window_high_0'];names=['Solids + Au','+ Cu leads','Vacuum + rad','N2 100 Pa','Ar 100 Pa','Kr 100 Pa','Vac, window ε=.8']
    fig,axs=plt.subplots(1,2,figsize=(12,4.3));axs[0].barh(names,[cases[n]['die_mean_k'] for n in labels]);axs[0].set(xlim=(260,272),xlabel='Actual MCT mean (K)',title='Matched header bath / .1 A / 2 mW')
    cool=['ceramic_3','die_attach','MCT_x029','Au_die_pad_0','Au_die_pad_1']
    def heat(r,key,owners):return sum(v[key] for n,v in r['exchange_by_body_w'].items() if n in owners)
    vals=[]
    for n in labels[2:6]:
        r=cases[n];vals.append([1e3*heat(r,k,cool) for k in ('radiation','gas','gold')])
    vals=np.array(vals);x=np.arange(4)
    for k,title in enumerate(('Radiation','Gas film','Gold bonds')):axs[1].bar(x+(k-1)*.24,vals[:,k],.24,label=title)
    axs[1].set(xticks=x,xticklabels=['Vacuum','N2','Ar','Kr'],ylabel='Net heat into die / attach / cold ceramic (mW)',title='Signed internal transfers; excludes other TEC surfaces');axs[1].legend(fontsize=8);fig.tight_layout();fig.savefig(out/'environment_comparison.png',dpi=170);plt.close(fig)
    r=cases[field_label];by=r['exchange_by_body_w'];fig,axs=plt.subplots(1,2,figsize=(12,4.5));axs[0].bar(['TEC IV','Die load','Cu lead I²R','Header out'],[1e3*r['tec_input_w'],2.,1e3*r['lead_joule_w'],1e3*r['hot_out_reaction_w']]);axs[0].set(ylabel='Power (mW)',title='External energy: header out = all electrical/deposited power')
    terms=['radiation','gas','gold','lead_conduction','lead_joule'];groups={'Die + pads + attach':['MCT_x029','Au_die_pad_0','Au_die_pad_1','die_attach'],'Cold ceramic':['ceramic_3'],'Cap + window':[n for n in by if 'cap' in n.lower() or 'window' in n.lower()],'Pins':[n for n in by if n.startswith('pin_')]};x=np.arange(len(groups))
    for i,key in enumerate(terms):axs[1].bar(x+(i-2)*.15,[1e3*heat(r,key,v) for v in groups.values()],.15,label=key)
    axs[1].set(xticks=x,xticklabels=list(groups),ylabel='Power into solids (mW)',title='Separate internal exchange paths; negative = heat supplied');axs[1].tick_params(axis='x',rotation=14);axs[1].legend(fontsize=7);fig.tight_layout();fig.savefig(out/'heat_paths.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4));labels=['nitrogen_0','nitrogen_patch1']+(['nitrogen_feedthrough'] if 'nitrogen_feedthrough' in cases else []);x=np.arange(len(labels))
    axs[0].plot(x,[cases[n]['die_mean_k'] for n in labels],'o-',label='Die mean');axs[0].plot(x,[cases[n]['cold_ceramic_k'] for n in labels],'s-',label='Cold ceramic');axs[0].set(xticks=x,xticklabels=(['Coarse / 442 patches','Coarse / 907 patches','Fine / 908 patches'][:len(labels)]),ylabel='Actual temperature (K)',title='Surface refinement; full bulk qualification pending' if len(labels)==2 else 'Surface then bulk refinement');axs[0].legend()
    d=np.load(raw/('operator_h1' if len(labels)==3 else 'operator_h0p1')/'operators.npz');a=d['areas'];im=axs[1].imshow(d['view_factors'],aspect='auto',norm=colors.LogNorm(vmin=1e-5,vmax=1));fig.colorbar(im,ax=axs[1],label='Reciprocal closed Fij');axs[1].set(xlabel='Receiving patch',ylabel='Emitting patch',title='Deterministic occluded surface operator');fig.tight_layout();fig.savefig(out/'refinement_view_factors.png',dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4));pressures=np.logspace(-5,5,150)
    for gas in ('N2','Ar','Kr'):ax.loglog(pressures,[float(gas_conductances(np.array([[0.,1e-6],[1e-6,0.]]),np.full((2,2),.003),np.array([275.,275.]),gas,p)[0,1]) for p in pressures],label=gas)
    ax.set(xlabel='Pressure (Pa)',ylabel='Conductance (W/K)',title='Reduced gas law only: 1 mm² parallel surfaces, 3 mm gap, 275 K');ax.axvline(100,color='gray',ls='--',lw=1);ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'gas_pressure_law.png',dpi=170);plt.close(fig)


def checkpoint_text(cases,s,code,link):
    n=cases['nitrogen_patch1'];rows='\n'.join(f"| {label} | {r['cold_ceramic_k']:.6f} | {r['die_mean_k']:.6f} | {r['die_max_k']:.6f} | {r['voltage_v']:.9f} | {100*r['direct_bath_relative_error']:+.5f} |" for label,r in cases.items())
    failed='\n'.join(f"| {label} | {r['nodes']:,} | {r['tetrahedra']:,} | {100*r['direct_bath_relative_error']:+.6f} | FAIL |" for label,r in s['unaccepted_fine_cases'].items())
    meshrows='\n'.join(f"| {name} | {r['nodes']:,} | {r['tetrahedra']:,} | {r['min_sicn']:.6f} |" for name,r in s['mesh_audits'].items())
    op='\n'.join(f"| {name} | {r['patches']} | {r['rays']:,} | {r['raw_ray_area_reciprocity_l1']:.6f} | {r['closure']['raw_area_weighted_closure_error']:.6f} |" for name,r in s['operator_audits'].items())
    patch=s['surface_refinement'];iso=s['electrical_regularization_sensitivity'];plates=s['independent_plate_checks']
    return f"""# G3b verified scoped checkpoint — full qualification incomplete

**Full G3b gate D is NOT QUALIFIED.** Three genuine converged fine-mesh executions
fail the independent direct-bath-gradient1% gate. Their fields remain explicitly
unaccepted. This publication uses the work order's narrower-checkpoint provision;
it does not declare G3b complete or lower a failed numerical tolerance.

Ten selected coarse-mesh integrated package executions pass every per-case gate,
along with two independent genuine1D Elmer exchange references and
{s['tests_passed']} full TE_FEM_SMOKE=1 tests. CLI quick and geometry_demo pass.
Protected G1–G3a source/data/evidence remain byte-identical. Existing sim session,
pinned Docker Elmer26.2.1/Gmsh4.13.1 and unchanged wrappers were reused; no LSDDTS,
host package installation or OpenFOAM. Code checkpoint: `{code}`.

## Qualified scope

The new conformal215-domain enclosure contains the original88-leg TEC, Kovar
header/mount, attach/MCT/Au pads, nine actual glass/pin pairs, attached cap and
ZnSe-candidate window. The conductor remains a unique181-vertex/180-edge path
with two external terminals; all175 cut areas are independently checked.
OCC/mesh volumes, shared contact areas, positive tetrahedra, per-body and global
face connectivity and actual ElmerGrid body/boundary mappings pass.
The **only bath is the external header underside at300 K**. Internal ceramics,
pin tops, cap and window temperatures are solved unknowns. Exterior cap/window
and isolated pin ends are adiabatic. Contacts at cap/header and window/rim are
ideal; unmeasured contact resistances are not identified.

The [VIGO family drawing](https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf)
supports the TO66 nine-pin family envelope, not the exact construction. Header,
cap, seals and generic unnumbered pin layout are hypotheses. Chosen .44mm pins
differ from the drawing's .76mm pins. No OEM electrical pinout is fabricated.
Thermistor, additional carrier/absorber parts and exact manufactured grades are
omitted. Data registry/source review distinguish sourced, inherited and assumed inputs.

| Geometry audit | Nodes | Tetrahedra | Min SICN |
|---|---:|---:|---:|
{meshrows}

Geometry audit success does not qualify a failed fine-mesh physics point.

## Real physics and independent exchange tests

Actual Elmer ThermoElectricSolver solves common spatial T/phi on all solids,
retaining TEC Seebeck/Peltier/Joule physics. Detector deposition is exactly
1.5mW prescribed bias heat plus .5mW absorbed optical thermal heat in the MCT
volume. It is one bias-power representation, not added again as detector Joule.
MCT is the inherited x=.29 primary-table local k(T),90..400 K, with fail-closed
callbacks. TEC coefficients remain constant mixed verification proxies, not
identified OEM BiTe. Package S=0 and computational sigma1e-12 S/m give a passive
potential extension, not physical metal electrical transport. Package Joule
is below1nW; lowering sigma100-fold changes die mean by{iso['die_change_k']:.3g}K
and TEC voltage by{iso['voltage_change_v']:.3g}V. Density/Cp placeholders are steady-only.

Two conservative massless Au bonds retain25um diameter,7mm length,k315 W/m/K.
Two hybrid Cu TEC supply leads use assumed .202mm diameter,8mm length,k400 and
rho1.72e-8 ohm m, coupled to generic pin instances2/3 and the existing actual TEC
terminals. End temperatures update from current3D fields. Conduction powers are
equal/opposite; total lead I²R={n['lead_joule_w']:.12g}W is split equally at endpoints.
Lead electrical resistance/current are lumped. No3D wire arcs, distributed
wire gas/radiation exchange, detector carrier transport or transient solve is claimed.

Deterministic Sobol cosine/area rays trace the first opaque hit in the orthogonal
solid union, cylindrical pins and closed cap/floor/roof/window. Hits map to actual
audited same-owner/orientation facets. The cavity skin has edge incidence two
and volume agrees within1%. Raw directed exchange estimates are symmetrized and
diagonally balanced, retaining blocked-pair zeros. Radiosity solves
J=epsilon*sigma*T^4+(1-epsilon)*F*J and inward power=-A*(I-F)*J.
Surface temperatures update in the global nonlinear iteration; final independent
postprocessing reconstructs the unmixed physical sources and free-node residual.
Depth-four regularized Anderson mixing stabilizes boundary powers without
changing the physical fixed point.

| Operator | Patches | Original rays | Raw reciprocity L1/area | Raw weighted closure error |
|---|---:|---:|---:|---:|
{op}

Bath/feedthrough operators inherit exactly the operator_h1 cavity triangles,
F/gaps and patch weights, adding zero surface-weight columns for new interior
nodes; no additional rays are claimed. Balanced closure is below1e-10 and
reciprocity error below1e-15m². Raw errors and balancing scales are retained;
conservation does not prove exact view factors. Hit-mapping distances and finite
patch/ray errors limit accuracy. Coarse442-to907-patch refinement at identical
bulk mesh changes die mean by{patch['die_mean_k']:.7f}K and maximum temperature
change by{100*patch['max_change_over_lift']:.6f}% of lift; voltage changes
{100*patch['voltage_relative_change']:.6f}%. This surface-resolution check passes.

Gray emissivities are declared hypotheses: .3 BiTe,.8 alumina/MCT/attach/mount/glass,
.05 Cu/Au,.1 Kovar/pins/window,.2 cap. Window epsilon .8 is a sensitivity.
ZnSe k18 W/m/K at298 K is a [vendor proxy](https://www.crystran.co.uk/optical-materials/zinc-selenide-znse/).
**The thermal window is opaque gray (tau=0); external ambient radiance and spectral
LWIR transmission are absent.** Prescribed .5mW absorbed optical heat is not a
window transmission calculation. No measured spectral coating properties are claimed.

[NIST Huber2019](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=926438)
supplies dilute k at200/300/400 K: N2 .0183/.0259/.0326,Ar .0124/.0177/.0224,
Kr .0064/.0095/.0122 W/m/K. Interpolation fails outside200..400 K.
Eucken viscosity, ideal-gas Cp/gamma and accommodation .8 are declared closures.
lambda=mu/p*sqrt(pi*R*T/2); each wall jump is
((2-alpha)/alpha)*(2*gamma/(gamma+1))*lambda/Pr. Symmetric gas conductance is
k(Tmean)*Wij/(harmonic projected flight gap+2*jump), exactly zero at p=0.
The [INL gap theory](https://mooseframework.inl.gov/bison/theory/gap_plenum_models.html)
supports temperature-jump/accommodation modeling; the Kennard free-molecular
limit and continuum kA/L are independently tested. This is a reduced gas-film
network, not a gas-volume Laplace/CFD solution. Actual matrices are nonnegative
and pair powers equal/opposite. At100 Pa the bounding Ra screen remains below1
for1/3/8/14.2mm gaps,250 K and100 K delta. Atmospheric Kr at3mm exceeds1708,
flagging future convection assessment;1708 is not a universal cavity criterion.

Analytic gray plates, epsilon0/uniform-T limits, balance/entropy and occlusion
checks pass. Genuine1D conducting-plate Elmer references use the same compiled
exchange routine: radiation-only maximum temperature error
{plates['radiation_plates_v2']['max_temperature_error_k']:.3g}K; N2 100Pa plus radiation
{plates['gas_radiation_plates_v2']['max_temperature_error_k']:.3g}K. The first zero-flux
startup benchmark failed and remains unaccepted; corrected startup excludes the
arbitrary initial state from Anderson response history. Two Elmer regressions
exercise that fix. Earlier vacuum/N2 executions retain exact old source/Fortran;
only the exact three startup edits are allowed by the byte-comparison validator.
Their unmixed physical residuals have been freshly reverified.

## Accepted coarse integrated cases

All driven cases: .1A,2mW deposition,300 K header bath. Solid control disables
gas/radiation/Cu leads and retains Au bonds; lead-only adds Cu conduction/Joule;
vacuum adds radiation; pure gas cases add100 Pa. High-window case is vacuum.

| Accepted case | Cold ceramic K | Die mean K | Die max K | TEC V | Direct-bath error % |
|---|---:|---:|---:|---:|---:|
{rows}

All accepted cases pass175 driven cuts <.5% (zero drive uses1uA), current/free
current1uA, global/free heat1uW, direct bath1%, work1%, attach cut5%, package
Joule1nW and separate internal-mechanism balances1nW. No tolerance was lowered.
Source voltage includes Cu series resistance separately from the TEC voltage.
Coarse same-header control isolates enclosure/nine-pin construction and
spatial discretization relative to preserved G3a; it is not OEM validation.
Fixed-current results do not establish minimum power at a fixed detector target.

![Actual accepted N2 fields and explicitly schematic hybrid links]({link}/actual_enclosure_temperature.png)
![Actual accepted potential/current/heat flux section]({link}/actual_tec_flux_section.png)
![Actual accepted gas/window/lead comparisons]({link}/environment_comparison.png)
![Separate cap, bond, gas and lead paths]({link}/heat_paths.png)
![Actual accepted surface exchange]({link}/actual_surface_exchange.png)
![Surface resolution and operator]({link}/refinement_view_factors.png)
![Reduced pressure law, not a PDE sweep]({link}/gas_pressure_law.png)

The representative accepted907-patch N2 case has header reaction out
{n['hot_out_reaction_w']:.12g}W = TEC IV{n['tec_input_w']:.12g}W + detector .002W
+ lead Joule{n['lead_joule_w']:.12g}W, error{n['global_energy_error_w']:+.3g}W.
Radiation/gas/Au/Cu conduction are internal transfers, not extra external power.
CSV/JSON retain all175 cuts, domain temperatures, patch/body mechanism powers,
wire/lead endpoints and whole-package horizontal control-volume budgets. Bands
include cap/pins/nonlocal sources and are not isolated textbook TEC stages.
Cap/flange transfer inferred from its signed surface budget is conservative,
not an independent cap-gradient cut. Raw/derived actual fields are compressed
with compressed and uncompressed hashes; no prescribed network field is substituted.

## Failed full-refinement qualification and preserved evidence

| Unaccepted converged case | Nodes | Tetrahedra | Direct-bath error % | Gate <=1% |
|---|---:|---:|---:|---|
{failed}

These genuine spatial Elmer executions have zero solver exits and relative
nonlinear change <1e-9. All other numerical gates pass, but the independent
external-bath raw-gradient gate fails. Temperature/voltage insensitivity alone
is insufficient to qualify them. Full G3b remains incomplete.

Localization found the largest discrepancy near the cold-return feedthrough.
Two bath-edge refinement rounds and a separate glass/pin/header-junction study
were insufficient to resolve it. The cause is not fully established. Future
work must resolve independent bath flux with systematic boundary/interface
resolution or another independently verified discretization; conservative weak
reactions must not be used to override the failed gradient check.

The initial coarse driven bath error1.85079%, divergent unaccelerated lead
iteration, failed plate-startup benchmark, cross-mesh potential interpolation
(81.44W artificial initial Joule),900s fine timeout and over-budget mesh proposal
are also retained explicitly unaccepted. The later converged fine fields serve
only as hashed P1 initial guesses for separately executed refined PDEs. Their
raw fields are quarantined, not included among the ten accepted cases.

This is a **verified scoped engineering checkpoint**, not completed G3b gate D,
OEM/device accuracy, production-gas optimization or full CFD. All prior accepted
evidence remains intact. See [reproduction](G3B_REPRODUCIBILITY.md) and the
machine-readable ledger for exact source, field and failure provenance.
"""


def main(archive_dir=None,checkpoint=False):
    if not checkpoint:raise SystemExit('Full G3b is unqualified. Use --coarse-checkpoint only for the explicitly scoped verified publication.')
    raw=ROOT/'outputs/fem-g3b';target=ROOT/('fem/results/g3b_checkpoint_20261029' if checkpoint else 'fem/results/g3b_20261029') if archive_dir is None else Path(archive_dir).resolve();out=ROOT/'outputs/g3b-report';out.mkdir(exist_ok=True)
    if not target.is_relative_to(ROOT):raise ValueError('Archive must remain inside this project')
    if subprocess.run(['git','ls-files','--error-unmatch',str(target.relative_to(ROOT)/'checksums.json')],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:raise ValueError('Published evidence immutable; use --out for a new archive')
    cases,resources,summary=validate(raw,checkpoint);code=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();rows=[];temps=[];cuts=[];bands=[];exchange=[];links=[];bonds=[];kn=[]
    for label,r in cases.items():
        rows.append({'case':label,**{k:r[k] for k in ('current_a','deposited_power_w','cold_ceramic_k','die_mean_k','die_max_k','die_to_cold_k','voltage_v','tec_input_w','hot_out_reaction_w','hot_out_direct_w','global_energy_error_w','direct_bath_relative_error','worst_cut_relative_error','free_thermal_residual_l1_w','free_current_residual_l1_a','package_joule_w')},'gas':r.get('gas','off'),'pressure_pa':r.get('pressure_pa',0),'radiation_on':r.get('radiation_on',False),'lead_joule_w':r.get('lead_joule_w',0),'source_voltage_v':r.get('tec_source_voltage_v',r['voltage_v'])})
        for name,t in r['domain_temperatures'].items():temps.append({'case':label,'body':name,**t})
        for name,t in r['component_cuts'].items():cuts.append({'case':label,'body':name,**t})
        for wire in r['wires']:bonds.append({'case':label,**wire})
        for t in r['stage_control_volume_budgets']:bands.append({'case':label,'budget_json':json.dumps(t,sort_keys=True)})
        if label in COUPLED:
            for name,t in r['exchange_by_body_w'].items():exchange.append({'case':label,'body':name,**t})
            for i,t in enumerate(r['supply_leads']):links.append({'case':label,'lead':i,**t})
            if r['pressure_pa']:
                d=np.load(raw/Path(r['operator_path']).name/'operators.npz');t=np.array(r['patch_temperature_k']);gap=d['distance_m'];sel=(d['exchange_m2']>0)&(~np.eye(len(t),dtype=bool));props=gas_properties(r['gas'],(t[:,None]+t[None,:])/2,r['pressure_pa']);g=gas_conductances(d['exchange_m2'],gap,t,r['gas'],r['pressure_pa']);kn.append({'case':label,'gas':r['gas'],'pressure_pa':r['pressure_pa'],'min_pair_T_k':float(((t[:,None]+t[None,:])/2)[sel].min()),'max_pair_T_k':float(((t[:,None]+t[None,:])/2)[sel].max()),'gap_min_m':float(gap[sel].min()),'gap_max_m':float(gap[sel].max()),'Kn_min':float((props['lambda_m']/gap)[sel].min()),'Kn_max':float((props['lambda_m']/gap)[sel].max()),'negative_conductances':int(np.sum(g<0))})
    for name,data in [('operating_points',rows),('domain_temperatures',temps),('current_cuts',cuts),('whole_package_band_budgets',bands),('exchange_by_body',exchange),('lead_endpoints',links),('gold_bond_endpoints',bonds),('gas_actual_field_regimes',kn),('resource_usage',resources),('rayleigh_screen',rayleigh_screen())]:csvwrite(out/(name+'.csv'),data)
    summary.update(cases=cases,unique_package_solver_executions=len(cases),independent_plate_solver_executions=2,device_validated=False,code_checkpoint=code,qualification='Scoped coarse numerical checkpoint; full G3b bath-gradient/refinement qualification FAILED' if checkpoint else 'numerical hybrid3D solid FEM / conservative gray surface radiation / rarefied gas films /1D Au and Cu leads');dump(out/'summary.json',summary);charts(raw,out,cases,summary)
    report_path=ROOT/'docs/PHASE1_G3B_RESULT.md' if archive_dir is None else target/'PHASE1_G3B_RESULT.md';report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(checkpoint_text(cases,summary,code,os.path.relpath(target/'charts',report_path.parent)))
    target.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'docs/G3B_REPRODUCIBILITY.md',target/'G3B_REPRODUCIBILITY.md')
    def copy(src,rel):
        dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    for p in out.iterdir():
        if p.is_file():copy(p,Path('charts')/p.name)
    for name in ('mesh_h0','mesh_h1','mesh_bath','mesh_feedthrough'):
        for n in ('audit.json','manifest.json','mesh.npz','grid.log','grid-status.json','gmsh.log'):copy(raw/name/n,Path('meshes')/name/n)
    for name in OPERATORS:
        for n in ('audit.json','manifest.json','patches.json','operators.npz','weights.npz','mesh.npz','grid.log','grid-status.json','prolongation.npz'):
            if (raw/name/n).exists():copy(raw/name/n,Path('operators')/name/n)
    compiled={}
    for label in cases:
        case=raw/label
        for n in ('case.sif','case.json','metrics.json','execution.json','solver.log','solver-status.json','exchange-history.txt'):
            if (case/n).exists():copy(case/n,Path('cases')/label/n)
        for directory in ('library','exchange_library','initial_library','source_snapshot'):
            if not (case/directory).exists():continue
            for p in (case/directory).iterdir():
                if p.is_file():
                    compiled[str(p.relative_to(ROOT))]=sha(p)
                    if p.suffix in ('.F90','.json','.log','.source'):copy(p,Path('cases')/label/directory/p.name)
        names=[cases[label]['field_source']]+(['derived.vtu'] if label==('nitrogen_patch1' if checkpoint else 'nitrogen_feedthrough') else [])
        for name in names:
            dest=target/'fields'/label/(name+'.gz');dest.parent.mkdir(parents=True,exist_ok=True)
            with (case/name).open('rb') as src,dest.open('wb') as dst,gzip.GzipFile(fileobj=dst,mode='wb',filename='',mtime=0) as z:shutil.copyfileobj(src,z)
        dump(target/'fields'/label/'uncompressed_sha256.json',{n:sha(case/n) for n in names})
    for name in ('radiation_plates_v2','gas_radiation_plates_v2'):
        case=raw/name
        for p in case.rglob('*'):
            if p.is_file() and (p.suffix in ('.F90','.json','.log','.sif','.vtu','.dat','.bin','.txt') or p.name.startswith('mesh.')):copy(p,Path('plate_checks')/name/p.relative_to(case))
    # Rejected evidence remains explicitly rejected, with original diagnostics/source.
    for name in ('solid_reference','vacuum_0','radiation_plates','nitrogen_fine','nitrogen_fine_tonly','nitrogen_fine_verified','nitrogen_bath','nitrogen_feedthrough','operator_0-unaccepted-cost','operator_0-unaccepted-quadrature','development-sources'):
        case=raw/name
        for p in case.rglob('*'):
            if p.is_file() and not p.is_symlink() and p.stat().st_size<3_000_000 and (p.suffix in ('.source','.json','.log','.txt','.F90','.sif','.vtu','.dat','.bin') or p.name.startswith('UNACCEPTED')):copy(p,Path('unaccepted_development')/name/p.relative_to(case))
    for rejected in ('nitrogen_fine_verified','nitrogen_bath','nitrogen_feedthrough'):
        failed=raw/rejected;name=read(failed/'metrics.json')['field_source'];dest=target/'unaccepted_development'/rejected/(name+'.gz')
        with (failed/name).open('rb') as src,dest.open('wb') as dst,gzip.GzipFile(fileobj=dst,mode='wb',filename='',mtime=0) as z:shutil.copyfileobj(src,z)
        dump(dest.parent/'uncompressed_sha256.json',{name:sha(failed/name)})
    for p in (ROOT/'data/g3b').glob('*.json'):copy(p,Path('sources')/p.name)
    for p in (ROOT/'logs').glob('g3b-*.log'):copy(p,Path('provenance')/p.name)
    for n in ('pytest-g3b-final.log','cli-g3b.log','geometry-g3b.log'):copy(ROOT/'logs'/n,Path('provenance')/n)
    dump(target/'provenance/compiled-library-hashes.json',compiled)
    sources={str(p.relative_to(ROOT)):sha(p) for p in [*(ROOT/'tecooledmct').glob('fem_g3b_*.py'),ROOT/'tests/test_fem_g3b.py',ROOT/'fem/report_archive_g3b.py',*(ROOT/'data/g3b').glob('*.json')]}
    dump(target/'checksums.json',{'code_checkpoint':code,'source_sha256':sources,'document_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (report_path,ROOT/'docs/G3B_REPRODUCIBILITY.md',ROOT/'G3B_ENCLOSURE_HEAT_TRANSFER_WORK_ORDER_20261029.md')},'artifact_sha256':{str(p.relative_to(target)):sha(p) for p in sorted(target.rglob('*')) if p.is_file() and p.name!='checksums.json'},'protected_integrity':summary['protected_integrity'],'unique_package_solver_executions':len(cases),'full_g3b_qualified':not checkpoint,'qualified_scope':'coarse integrated checkpoint' if checkpoint else 'full G3b','independent_plate_solver_executions':2,'test_count':summary['tests_passed'],'device_validated':False})
    print('G3b SCOPED checkpoint PASS; full G3b NOT QUALIFIED:' if checkpoint else 'G3b archive PASS:',len(cases),'actual3D coupled executions +2 independent1D plate checks;',summary['tests_passed'],'tests')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);p.add_argument('--coarse-checkpoint',action='store_true');a=p.parse_args();main(a.out,a.coarse_checkpoint)
