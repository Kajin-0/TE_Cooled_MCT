#!/usr/bin/env python3
"""Archive only verified actual G3a solid/1D hybrid package evidence."""
import csv,gzip,json,re,shutil,subprocess,os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors,cm
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from tecooledmct.g2d_data import ROOT,sha,dump
from tecooledmct.fem_g3a_data import preserve
from tecooledmct.fem_g3a_interfaces import verify as interfaces

LABELS=['passive_0','loaded_0','loaded_1','no_heat_010','loaded_005','no_heat_005','wires_zero','wires_four','attach_resistance_five','mount_resistance_five','package_sigma_hundredth']


def csvwrite(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def field_plot(mesh,case,out):
    import meshio
    d=np.load(mesh/'mesh.npz');p=d['points'];faces=d['faces'];tags=d['boundaries'];f=meshio.read(case/'derived.vtu');t=f.point_data['Temperature_K'];sel=np.flatnonzero(tags<1000);norm=colors.Normalize(float(t.min()),float(t.max()));cmap=plt.get_cmap('inferno')
    # Render every actual exterior triangle; no removed faces or interpolated geometry.
    tri=p[faces[sel]]*1e3;values=t[faces[sel]].mean(axis=1);facecolors=cmap(norm(values));fig=plt.figure(figsize=(13,5))
    for idx,zoom in enumerate((False,True),1):
        ax=fig.add_subplot(1,2,idx,projection='3d');chosen=np.ones(len(tri),bool)
        if zoom:chosen=(np.abs(tri[:,:,0]).max(axis=1)<3.4)&(np.abs(tri[:,:,1]).max(axis=1)<3.4)&(tri[:,:,2].min(axis=1)>-.3)
        poly=Poly3DCollection(tri[chosen],facecolors=facecolors[chosen],edgecolors='none',alpha=.96,rasterized=True);ax.add_collection3d(poly)
        if zoom:ax.set(xlim=(-3.4,3.4),ylim=(-3.4,3.4),zlim=(-.3,4.1),title='TEC / attach / MCT\nActual exterior temperature field');ax.set_box_aspect((6.8,6.8,4.4))
        else:
            ax.set(xlim=(-16,16),ylim=(-9,9),zlim=(-3.5,5),title='Header + two feedthroughs\nDashed lines: schematic 1D bonds');ax.set_box_aspect((32,18,12))
            for sign in (-1,1):
                u=np.linspace(0,1,40);x=sign*(5.4*(1-u)+.3*u);z=.63*(1-u)+3.8*u+1.0*np.sin(np.pi*u);ax.plot(x,np.zeros_like(x),z,'--',color='#92d8ff',lw=1)
        ax.title.set_fontsize(11);ax.view_init(25,-55);ax.set(xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)')
    fig.subplots_adjust(top=.80,left=.01,right=.88,bottom=.07,wspace=.02);fig.colorbar(cm.ScalarMappable(norm=norm,cmap=cmap),ax=fig.axes,shrink=.65,label='Actual T (K)');fig.suptitle('Actual solid temperature fields: .1 A / 2 mW; dashed lines are hybrid 1D bonds',fontsize=13);fig.savefig(out/'actual_package_fields.png',dpi=175,bbox_inches='tight');plt.close(fig)


def main(archive_dir=None):
    integrity=preserve();raw=ROOT/'outputs/fem-g3a';out=ROOT/'outputs/g3a-report';out.mkdir(exist_ok=True);target=ROOT/'fem/results/g3a_20261029' if archive_dir is None else Path(archive_dir).resolve()
    if not target.is_relative_to(ROOT):raise ValueError('Archive must remain inside project')
    report_path=ROOT/'docs/PHASE1_G3A_RESULT.md' if archive_dir is None else target/'PHASE1_G3A_RESULT.md'
    chart_link=os.path.relpath(target/'charts',report_path.parent)
    if subprocess.run(['git','ls-files','--error-unmatch',str(target.relative_to(ROOT)/'checksums.json')],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:raise SystemExit('Published G3a evidence is immutable; use a new version')
    testlog=(ROOT/'logs/pytest-g3a-full.log').read_text();test=re.search(r'(?m)^(\d+) passed(?:,.*)? in ',testlog)
    if not test or re.search(r'\b(?:FAILED|ERROR|failed)\b',testlog):raise ValueError('Completed passing full regression required')
    cases={};interface={};sources={};resources=[]
    for label in LABELS:
        case=raw/label;r=json.loads((case/'metrics.json').read_text());ex=json.loads((case/'execution.json').read_text());mesh=raw/('mesh_1' if label=='loaded_1' else 'mesh_0')
        if not r['passed'] or ex['status']['exit_code']!=0 or ex['status']['nonlinear_last_relative_change']>=1e-9:raise ValueError('Unaccepted actual case '+label)
        if sha(case/'case.sif')!=r['sif_sha256'] or sha(case/r['field_source'])!=r['vtu_sha256'] or r['postprocessor_sha256']!=sha(ROOT/'tecooledmct/fem_g3a_post.py'):raise ValueError('Changed actual fields/source '+label)
        for n,h in ex['source_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('Actual execution source changed '+n)
            sources[n]=h
        if ex.get('mesh_npz_sha256',sha(mesh/'mesh.npz'))!=sha(mesh/'mesh.npz'):raise ValueError('Changed execution mesh')
        interface[label]=interfaces(mesh,case)
        if not interface[label]['passed']:raise ValueError('Independent interface cut failure '+label)
        cases[label]=r;resources.append({'case':label,'nodes':r['nodes'],'tetrahedra':r['tetrahedra'],**{k:ex['status'][k] for k in ('exit_code','elapsed_s','peak_rss_kib','nonlinear_iterations','nonlinear_last_relative_change')}})
    audits={f'mesh_{i}':json.loads((raw/f'mesh_{i}/audit.json').read_text()) for i in (0,1)}
    if not all(x['passed'] and x['connectivity']['passed'] and x['elmer_mapping']['passed'] for x in audits.values()):raise ValueError('Mesh topology gate')
    base,fine=cases['loaded_0'],cases['loaded_1'];lift=300-fine['cold_ceramic_k'];conv={'die_mean_change_k':abs(base['die_mean_k']-fine['die_mean_k']),'die_max_change_k':abs(base['die_max_k']-fine['die_max_k']),'cold_ceramic_change_k':abs(base['cold_ceramic_k']-fine['cold_ceramic_k']),'voltage_relative_change':abs(base['voltage_v']-fine['voltage_v'])/abs(fine['voltage_v'])}
    conv['passed']=max(conv['die_mean_change_k'],conv['die_max_change_k'],conv['cold_ceramic_change_k'])/lift<.01 and conv['voltage_relative_change']<.01
    sigma=cases['package_sigma_hundredth'];isolation={'die_change_k':abs(sigma['die_mean_k']-base['die_mean_k']),'voltage_change_v':abs(sigma['voltage_v']-base['voltage_v'])};isolation['passed']=isolation['die_change_k']<1e-4 and isolation['voltage_change_v']<1e-6
    wire=json.loads((raw/'wire_reference/verification.json').read_text())
    if not conv['passed'] or not isolation['passed'] or not wire['passed']:raise ValueError('Refinement / isolation / wire law gate')
    for name in ('cli','geometry'):
        if not (ROOT/f'logs/{name}-g3a.log').exists():raise ValueError('Missing required checks')
    for label,prefix in [('check','summary.json'),('pellet','pellet_geometry_study.json')]:json.loads((ROOT/f'outputs/{label}-g3a'/prefix).read_text())
    scalars=[];temperatures=[];cuts=[];stage=[];wires=[];sensitivity=[]
    for label,r in cases.items():
        scalars.append({'case':label,**{k:r[k] for k in ('current_a','pbias_w','poptical_thermal_w','deposited_power_w','cold_ceramic_k','die_mean_k','die_min_k','die_max_k','die_to_cold_k','voltage_v','tec_input_w','hot_out_reaction_w','hot_out_direct_w','global_energy_error_w','direct_bath_relative_error','wire_heat_into_die_w','attach_midplane_down_w','attach_direct_energy_relative_error','worst_cut_relative_error','package_joule_w','free_thermal_residual_l1_w','free_current_residual_l1_a','attach_bottom_k','attach_top_k')}})
        for name,s in r['domain_temperatures'].items():temperatures.append({'case':label,'body':name,**s})
        for name,c in r['component_cuts'].items():cuts.append({'case':label,'body':name,**c})
        for s in r['stage_control_volume_budgets']:stage.append({'case':label,**s})
        for w in r['wires']:wires.append({'case':label,**{k:w[k] for k in ('wire','warm_pin_patch_k','cold_pad_patch_k','heat_into_die_w','conductance_w_k')}})
    for label in ('wires_zero','wires_four','attach_resistance_five','mount_resistance_five','package_sigma_hundredth'):
        r=cases[label];sensitivity.append({'case':label,'delta_die_mean_k':r['die_mean_k']-base['die_mean_k'],'delta_cold_ceramic_k':r['cold_ceramic_k']-base['cold_ceramic_k'],'delta_voltage_v':r['voltage_v']-base['voltage_v'],'wire_heat_w':r['wire_heat_into_die_w'],'method':'actual coupled Elmer at same header bath/current/deposited load'})
    for n,rows in [('operating_points.csv',scalars),('domain_temperatures.csv',temperatures),('component_cuts.csv',cuts),('stage_heat_budgets.csv',stage),('wire_endpoints.csv',wires),('sensitivities.csv',sensitivity),('resource_usage.csv',resources)]:csvwrite(out/n,rows)
    field_plot(raw/'mesh_1',raw/'loaded_1',out)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for labels,title in [(('passive_0','no_heat_005','no_heat_010'),'0 mW deposited'),(('loaded_005','loaded_0'),'2 mW deposited')]:
        rr=[cases[x] for x in labels];axs[0].plot([r['current_a'] for r in rr],[r['die_mean_k'] for r in rr],'o-',label=title);axs[1].plot([r['current_a'] for r in rr],[r['die_to_cold_k'] for r in rr],'o-',label=title)
    for ax,y in zip(axs,('MCT die mean (K)','Die minus cold ceramic (K)')):ax.set(xlabel='TEC current (A)',ylabel=y);ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Actual coarse-mesh package solves; no extrapolated points');fig.tight_layout();fig.savefig(out/'die_vs_current.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4));axs[0].bar(['TEC IV','detector heat','header out'],[base['tec_input_w']*1e3,2,base['hot_out_reaction_w']*1e3]);axs[0].set(ylabel='Power (mW)',title='External energy: header out = TEC IV + detector heat')
    axs[1].bar(['bias','absorbed optical','warm wires','attach cut out'],[base['pbias_w']*1e3,base['poptical_thermal_w']*1e3,base['wire_heat_into_die_w']*1e3,base['attach_midplane_down_w']*1e3]);axs[1].set(ylabel='Power (mW)',title='Die input paths versus independent attach gradient cut');axs[1].tick_params(axis='x',rotation=20)
    fig.suptitle('Wires transfer heat internally from header; they are not an extra external source');fig.tight_layout();fig.savefig(out/'heat_budget.png',dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4));rows=sensitivity[:4];ax.barh([x['case'] for x in rows],[x['delta_die_mean_k'] for x in rows]);ax.axvline(0,color='gray');ax.set(xlabel='Change in die mean (K)',title='Actual package sensitivities: .1 A, 2 mW, same header bath');fig.tight_layout();fig.savefig(out/'sensitivities.png',dpi=170);plt.close(fig)
    result={'passed':True,'qualification':'Numerically qualified hybrid solid-package checkpoint; no OEM/device accuracy claim','cases':cases,'mesh_audits':audits,'refinement':conv,'electrical_regularization_sensitivity':isolation,'independent_wire_reference':wire,'interface_cuts':interface,'sensitivities':sensitivity,'protected_integrity':integrity,'unique_package_solver_executions':len(cases),'independent_1d_solver_executions':1,'tests_passed':int(test.group(1))};dump(out/'summary.json',result)
    ops='\n'.join(f"| {n} | {r['current_a']:.2f} | {1000*r['deposited_power_w']:.1f} | {r['cold_ceramic_k']:.6f} | {r['die_mean_k']:.6f} | {r['die_max_k']:.6f} | {r['die_to_cold_k']:.6f} | {r['voltage_v']:.9f} |" for n,r in cases.items())
    meshes='\n'.join(f"| {n} | {r['nodes']:,} | {r['tetrahedra']:,} | {r['min_sicn']:.6g} |" for n,r in audits.items())
    temp='\n'.join(f"| {n} | {r['mean_k']:.6f} | {r['min_k']:.6f} | {r['max_k']:.6f} |" for n,r in fine['domain_temperatures'].items())
    sens='\n'.join(f"| {r['case']} | {r['delta_die_mean_k']:+.7f} | {r['delta_cold_ceramic_k']:+.7f} | {r['delta_voltage_v']:+.9f} | {r['wire_heat_w']*1e3:.6f} |" for r in sensitivity)
    stages='\n'.join(f"| {s['stage']} | {s['hot_out_w']:.9f} | {s['cold_absorbed_w']:.9f} | {s['electrical_work_w']:.9f} | {s['warm_wire_endpoint_sink_w']:.9f} | {s['energy_error_w']:+.3g} |" for s in fine['stage_control_volume_budgets'])
    code=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();reg=json.loads((ROOT/'data/g3a/package_registry.json').read_text());wire_fraction=base['wire_heat_into_die_w']/base['deposited_power_w'];break_fraction=np.mean([(w['cold_pad_patch_k']-base['cold_ceramic_k'])/(w['warm_pin_patch_k']-base['cold_ceramic_k']) for w in base['wires']])
    report=f'''# G3a: coupled TO-66 solid package with hybrid gold bonds

**Numerically qualified scoped G3a checkpoint, 2026-10-29.** {len(cases)} genuine integrated
3D solid T/phi package solves and one independent genuine1D Elmer wire solve completed.
All declared mesh/current/energy/interface/refinement/isolation gates pass; {test.group(1)} full
TE_FEM_SMOKE=1 tests, CLI quick and geometry_demo pass. All accepted G1/G2a/G2b/G2c/G2d
source/data/evidence remain byte-identical. Existing sim session and pinned image/wrappers reused.
Evidence-generation code checkpoint `{code}`; exact executed source/SIF/mesh/VTU hashes archived.
**This is a hybrid3D-solid/1D-wire model, not an all3D wire model or OEM/device validation.**

## Construction, sources and limits

A new conformal OCC model rebuilds the actual verified G2b189-domain TEC construction without
modifying it:88 legs,85 local Cu bridges,two buried routes and supporting alumina,6.4mm hot /
2.4mm cold envelope,3.8mm total height and inferred28/12/4 couples. The unique181-vertex180-edge
conductor path with exactly two external terminals is preserved. The visual STEP is not imported.
Ten new solids give199 domains:elliptical Kovar header,hot mount,die attach,MCT die,two glass
annuli,two extended Kovar pins and two Au die pads. Only **two feedthroughs are simulated**;
seven of the illustrated nine are omitted, including their holes/seals/thermal effects.

Family envelope31.5x17.5mm,mounting pitch24.4mm and3.7mm mounting holes appear in the
[VIGO primary drawing](https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf).
The ellipse,1.1mm header,chosen symmetric pin locations,.44mm pin diameter,glass geometry,
1mm-square x.12mm die and1.25mm-square x.08mm attach are assumptions, not OEM tooling.
The drawing's .76mm pins are not silently substituted for our reference's assumed .44mm pins.
No numbered OEM pinout or precise package manufacture is claimed. Source review and machine-readable
registry distinguish those facts. No cap/window,gas,radiation,thermistor,TEC supply-lead leakage,
separate sapphire/silicon carrier,POM carrier or humidity absorber is represented.
Their absence matters for absolute temperatures and complete package loads.

Kovar k=17.3 and Au k=315 W/m/K are frozen proxies, not calibrated low-temperature grade laws.
Glass k=1,die attach k=1 and hot mount k=2 W/m/K are unmeasured assumptions. Header and mount
couple thermally to the bottom TEC alumina with actual conformal interfaces; the **only temperature
Dirichlet face is the external header underside at300 K**. No TEC ceramic or pin top is clamped.
Pin lower ends are insulated; heat reaches their tops through glass/header and their3D lead volume.
Hot mount50um gives R''=25e-6m2K/W; die attach80um gives R''=80e-6m2K/W before sensitivity.
A fivefold resistance change reduces the relevant k by5 without changing mesh geometry.

The compact MCT uses the single sourced composition Hg0.71Cd0.29Te, not carrier transport.
[Heckman/Gonzalez/Guha2008, primary Table2](https://opg.optica.org/ao/abstract.cfm?uri=ao-47-4-578)
reports90/148/298/400 K conductivity2.41/1.61/.973/.790 W/m/K. k is derived from measured
rho,Cp and diffusivity; source relative k uncertainty7–14%. Density6830kg/m3 and Cp130/146/176/194
J/kg/K are retained in the registry. Local nodal k is linearly interpolated and compiled callbacks
fail outside90..400 K; no alloy-x interpolation or extrapolation is implemented. x=.29 is a
source-qualified example, not an identified detector composition. Density/Cp do not determine
these steady solutions; SIF heat-capacity placeholders must not be reused as a transient model.

TEC coefficients are the original mixed room-temperature constant **verification** law. G2d's
300 K local-T BiTe coverage failure is unchanged; source-backed40..300 K BiTe is not used here.
No model temperatures are manufacturer-validated predictions. Detector heat is1.5mW from prescribed
Vdet=.5V times Idet=.003A, plus .5mW absorbed optical thermal power. Only this one bias-power
representation is deposited uniformly over the actual MCT volume; no extra V-squared/R or carrier
PDE current is added. `Volumetric Heat Source`, confirmed in pinned solver source, is W/m3 and
avoids multiplying by density as Elmer's per-mass `Heat Source` would.

## Actual coupled physics and conservative hybrid wires

Elmer ThermoElectricSolver solves common spatial T/phi over the conformal model. TEC Peltier,
Seebeck and Joule terms remain active. Package materials have S=0 and computational
sigma=1e-12S/m, defining a passive potential extension—not physical Au/Kovar electrical
conductivity or detector current. Their actual spurious Joule heat is below1nW (baseline
{base['package_joule_w']:.4g}W). A100-fold lower package sigma changes die mean by
{isolation['die_change_k']:.4g}K and voltage by{isolation['voltage_change_v']:.4g}V, below declared
1e-4K/1e-6V gates. Fourier conduction is therefore resolved without a meaningful package
TEC-current path. The original alumina electrical regularization remains unchanged.

Each massless1D Au wire has G=k*pi*d^2/(4L)={wire['analytical_conductance_w_k']:.12g}W/K,
chosen d=25um,L=7mm. Compiled nonlocal callbacks read area-weighted3D pin/pad temperatures
from the current global nonlinear iterate and apply **equal/opposite powers** to the two patches.
Both warm and cold endpoint temperatures remain solved unknowns; this is not a one-way prescribed
heat load. No 3D wire arc is meshed. Callback nodal maps are checked against actual ElmerGrid
node numbering; endpoint areas/weights are archived. Residual reconstruction uses the final
independent actual-field averages, so a frozen or one-way wire coupling would fail the free-node gate.
An independent11-node1D Elmer rod with a1mW Neumann input and260 K cold end solves the hot end
at{wire['actual_hot_k']:.10f}K. Its maximum temperature error is{wire['max_temperature_error_k']:.3g}K
and its conductance agrees with the analytical wire law. This test is separately counted.

## Actual package cases and mesh convergence

| Mesh | Nodes | Tetrahedra | Minimum SICN |
|---|---:|---:|---:|
{meshes}

OCC exact volumes/contact areas,positive tetrahedra,manifold faces,each-body face connectivity,
whole-solid thermal connectivity,TEC conductor graph,all175 current-cut areas and actual ElmerGrid
node/tetra/body mapping pass. Original rectangular TEC volumes/areas use1e-7 relative tolerance;
curved package chordal tetrahedra use a declared1% volume/contact-area tolerance. The initial
coarse-circle mesh failed the pin-volume gate and remains unaccepted; curvature sizing was
increased without lowering that gate. Both final package meshes pass.

| Actual case | TEC A | Die heat mW | Cold ceramic K | Die mean K | Die max K | Die-cold K | Terminal V |
|---|---:|---:|---:|---:|---:|---:|---:|
{ops}

The zero-drive/no-heat case is uniform300 K to1e-6K. All accepted exits are zero and nonlinear
relative change <1e-9. Every driven interior cut passes .5%;zero-drive uses1uA absolute. Global
current/free-node thermal/current residuals pass1uA/1uW,package spurious Joule <1nW,independent
work <1%,direct bath energy <1%,source-free mount/pin and attach-gradient checks <5%.
No gate was relaxed to accept a case.

At.1 A/2mW, refinement changes die mean by{conv['die_mean_change_k']:.7f}K,die max by
{conv['die_max_change_k']:.7f}K and ceramic mean by{conv['cold_ceramic_change_k']:.7f}K,each below1%
of lift. Voltage changes{100*conv['voltage_relative_change']:.6f}%. Fine worst current cut is
{100*fine['worst_cut_relative_error']:.6f}%. Direct bath mismatch is
{100*base['direct_bath_relative_error']:+.5f}% coarse and{100*fine['direct_bath_relative_error']:+.5f}%
fine:both pass1%,but this flux error is not monotonically reduced. Local corner flux peaks and
wire-pad endpoint spreading peaks are not claimed converged. Parameter sensitivities use the same
coarse mesh; only the stated loaded case has a two-resolution study.

![Actual solid fields and explicitly schematic hybrid bonds]({chart_link}/actual_package_fields.png)
![Actual die versus current]({chart_link}/die_vs_current.png)

## Actual temperatures and heat budgets

Fine loaded case,all statistics from actual fields:

| Body | Volume mean K | Min K | Max K |
|---|---:|---:|---:|
{temp}

Fine attach bottom/top area means:{fine['attach_bottom_k']:.7f}/{fine['attach_top_k']:.7f}K.
Fine die-to-cold mean rise:{fine['die_to_cold_k']:.7f}K. Additional domain CSV retains every case.
At the coarse loaded control,wire heat is{1e3*base['wire_heat_into_die_w']:.7f}mW,
{100*wire_fraction:.3f}% of the2mW detector deposition. Its warm pins are cooled by that flow;
no arbitrary pin-top bath supplies it. The cold pads sit above the cold ceramic temperature;
using the ceramic as the wire endpoint would overestimate the wire temperature difference by
about{100*break_fraction:.3f}% relative to the warm-pin-to-ceramic difference. The separate die,
attach and pad fields resolve that thermal break.

Fine external balance:header out{fine['hot_out_reaction_w']:.10f}W = TEC IV
{fine['tec_input_w']:.10f}W + detector deposited .002W,with error
{fine['global_energy_error_w']:+.3g}W. Wire heat is an **internal** header-to-die transfer,
not another external source. Independent direct external-bath and interior attach/mount/pin
fluxes are reported separately from conservative weak reactions; they are not replaced by the
identity Qout=Pin+Pdet. Coarse mount/pin interior-gradient cut mismatches are approximately .05%.

The P1 nodal control volumes include shared ceramic/routing portions;bottom includes header/mount
and the negative warm-wire endpoint power. They are not isolated textbook leg stages.

| Fine stage | Hot out W | Cold absorbed W | J.E W | Warm-wire sink W | Balance error W |
|---|---:|---:|---:|---:|---:|
{stages}

![Actual global and die heat budgets]({chart_link}/heat_budget.png)

## Controlled sensitivities and comparison limits

Same300 K header bath,.1 A and2mW deposited load,relative to coarse loaded control:

| Actual sensitivity | Delta die K | Delta cold ceramic K | Delta V | Wire heat mW |
|---|---:|---:|---:|---:|
{sens}

Four wires mean two parallel1D bonds per existing endpoint pair,not four new3D pads/pins.
Zero wires remove only the1D thermal coupling;all3D package volumes remain. Die-attach and
hot-mount resistance hypotheses are not measured confidence intervals or identified chemistry.
The preserved G2b bath was on the TEC ceramic and its load distributed across the top plate;
G3a moves the bath to the header and heat to the actual die,plus wires. **No comparison between
those different boundary placements is claimed as validation or a uniquely attributed shunt.**
The new same-header-bath wire/attach/mount controls isolate their stated changes instead.

![Actual package sensitivities]({chart_link}/sensitivities.png)

## Verdict

G3a's scoped **genuine thermally coupled hybrid solid-package numerical checkpoint passes**,
including passive test,current/load matrix,refinement,wire law and independent interface/energy
checks. OEM/device absolute accuracy remains unqualified. Full nine-pin layout,real wire geometry,
measured grades/contacts/carriers,package cap/window,radiation/gas,TEC supply-lead heat and
independent device measurements remain pending. There is no transient/carrier-transport/LSDDTS
calculation,no OpenFOAM and no host solver installation. Earlier accepted evidence is unchanged.
'''
    report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(report)
    target.mkdir(parents=True,exist_ok=True)
    def copy(src,rel):
        p=target/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,p)
    for p in out.iterdir():
        if p.is_file():copy(p,Path('charts')/p.name)
    for i in (0,1):
        for n in ('manifest.json','audit.json','mesh.npz','grid.log','grid-status.json','gmsh.log'):copy(raw/f'mesh_{i}'/n,Path('meshes')/f'mesh_{i}'/n)
    runtime={}
    for label,r in cases.items():
        case=raw/label
        for n in ('case.sif','case.json','metrics.json','execution.json','solver.log','solver-status.json','interface_cuts.json'):copy(case/n,Path('cases')/label/n)
        for n in ('Package.F90','compile.log','compile-status.json','endpoint_weights.json'):copy(case/'library'/n,Path('cases')/label/'library'/n)
        for p in (case/'library').iterdir():
            if p.is_file():runtime[str(p.relative_to(ROOT))]=sha(p)
    for label in ('loaded_0','loaded_1','wires_zero','attach_resistance_five'):
        case=raw/label
        names=[cases[label]['field_source']]+(['derived.vtu'] if label=='loaded_1' else [])
        for n in names:
            dest=target/'fields'/label/(n+'.gz');dest.parent.mkdir(parents=True,exist_ok=True)
            with (case/n).open('rb') as src,dest.open('wb') as rawfile,gzip.GzipFile(fileobj=rawfile,mode='wb',filename='',mtime=0) as zipped:shutil.copyfileobj(src,zipped)
        dump(target/'fields'/label/'uncompressed_sha256.json',{n:sha(case/n) for n in names})
    for p in (raw/'wire_reference').iterdir():
        if p.is_file():copy(p,Path('wire_reference')/p.name)
    for p in (ROOT/'data/g3a').glob('*.json'):copy(p,Path('sources')/p.name)
    for p in (ROOT/'logs').glob('g3a-*.log'):copy(p,Path('provenance')/p.name)
    for n in ('pytest-g3a-full.log','cli-g3a.log','geometry-g3a.log'):copy(ROOT/'logs'/n,Path('provenance')/n)
    for n in ('UNACCEPTED.txt','geometry.py.source','gmsh.log'):copy(ROOT/'outputs/fem-g3a/mesh_0-unaccepted-chordal'/n,Path('provenance/rejected-chordal-mesh')/n)
    dump(target/'provenance/compiled-library-hashes.json',runtime)
    for p in [*(ROOT/'tecooledmct').glob('fem_g3a_*.py'),ROOT/'tests/test_fem_g3a.py',ROOT/'fem/report_archive_g3a.py',*(ROOT/'data/g3a').glob('*.json')]:sources[str(p.relative_to(ROOT))]=sha(p)
    dump(target/'checksums.json',{'code_checkpoint':code,'source_sha256':sources,'artifact_sha256':{str(p.relative_to(target)):sha(p) for p in sorted(target.rglob('*')) if p.is_file() and p.name!='checksums.json'},'protected_integrity':integrity,'unique_package_solver_executions':len(cases),'independent_1d_solver_executions':1,'test_count':int(test.group(1)),'device_validated':False,'model':'genuine coupled3D solids plus conservative1D wires,not all3D wire FEM'})
    print('G3a archive PASS:',len(cases),'actual package solves +1 independent wire solve;',test.group(1),'tests; OEM/device accuracy not qualified')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args();main(a.out)
