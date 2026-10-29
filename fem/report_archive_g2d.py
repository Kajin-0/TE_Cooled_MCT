#!/usr/bin/env python3
"""Fail-closed G2d report/archive: screening, actual PDE and blocked gates distinct."""
from pathlib import Path
import csv,gzip,json,re,shutil,subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tecooledmct.g2d_data import ROOT,DATA,sha,dump,preserve,points,residual


def csvwrite(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    published=subprocess.run(['git','ls-files','--error-unmatch','fem/results/g2d_20261029/checksums.json'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if published.returncode==0:raise SystemExit('Published G2d evidence is immutable; use a new version/path')
    integrity=preserve();analysis=ROOT/'outputs/g2d-analysis';actual=ROOT/'outputs/fem-g2d'
    a=json.loads((analysis/'summary.json').read_text());f=json.loads((actual/'summary.json').read_text());bud=json.loads((actual/'budgets.json').read_text());audit=json.loads((ROOT/'outputs/g2d-source-audit.json').read_text())
    if not(a['passed'] and f['passed'] and audit['passed'] and all(b['passed'] for b in bud.values())):raise ValueError('Failed numerical/source gate')
    sources={}
    for result in (a,f,audit):
        for n,h in result['source_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('Changed source: '+n)
            sources[n]=h
    if sha(analysis/'frozen_fit.json')!=a['frozen_fit_sha256']:raise ValueError('Frozen fit changed')
    testlog=(ROOT/'logs/pytest-g2d-full.log').read_text();test=re.search(r'(?m)^(\d+) passed(?:,.*)? in ',testlog)
    if not test or re.search(r'\b(?:FAILED|ERROR|failed)\b',testlog):raise ValueError('Full completed passing regression required')
    for label in ('cli','geometry'):
        if not (ROOT/f'outputs/{"check" if label=="cli" else "pellet"}-g2d').exists() or not (ROOT/f'logs/{label}-g2d.log').exists():raise ValueError('Required CLI/demo evidence missing')
    for label,r in f['cases'].items():
        case=actual/label
        if sha(case/'case.sif')!=r['sif_sha256'] or sha(case/r['field_source'])!=r['vtu_sha256']:raise ValueError('Changed actual fields/SIF')
        if bud[label]['postprocessor_sha256']!=sha(ROOT/'tecooledmct/g2d_budget.py'):raise ValueError('Changed budget reconstruction')
    out=ROOT/'outputs/g2d-report';out.mkdir(exist_ok=True);observed=points('calibration_reserved')+points('validation_holdout');comparisons=[]
    oldpath=ROOT/'fem/results/g2b_two_terminal_20261028/summary.json';old=json.loads(oldpath.read_text())['cases']['zero_load_positive']
    models=[('preserved_G2b_holdout',old,'preserved actual G2b solve, reused without new execution')]+[(label,r,'new genuine coupled 3D Elmer constant-law diagnostic') for label,r in f['cases'].items()]
    for label,r,origin in models:
        prediction={'hot_k':300,'ambient':'vacuum','current_a':r['current_a'],'load_w':r['load_w'],'delta_t_k':300-r['cold_mean_k'],'voltage_v':r['voltage_v']}
        for row in observed:
            if all(row[k]==prediction[k] for k in ('hot_k','ambient','current_a','load_w')):comparisons.append({'case':label,'origin':origin,'current_a':r['current_a'],'load_w':r['load_w'],**residual(row,prediction)})
    csvwrite(out/'actual_OEM_residuals.csv',comparisons);dump(out/'actual_OEM_residuals.json',comparisons)
    scalars=[];resources=[];cuts=[];stages=[]
    for label,r in f['cases'].items():
        scalars.append({'case':label,**{k:r[k] for k in ('current_a','load_w','hot_k','cold_mean_k','voltage_v','electrical_input_w','joule_w','hot_out_w','cold_out_w','volume_j_dot_e_w','bath_gradient_energy_relative_residual','energy_relative_residual','power_work_relative_residual','max_cut_relative_error','free_thermal_residual_l1_w','free_current_residual_l1_a')}})
        resources.append({'case':label,'accepted_performance_point':True,**{k:r['solver_status'][k] for k in ('exit_code','elapsed_s','peak_rss_kib','nonlinear_iterations','nonlinear_last_relative_change')}})
        for name,c in r['cuts'].items():cuts.append({'case':label,'body':name,**c})
        for b in bud[label]['stages']:stages.append({'case':label,**b})
    probe=f['source_domain_probe'];ps=probe['solver_status'];resources.append({'case':'source_300K_probe','accepted_performance_point':False,**{k:ps.get(k) for k in ('exit_code','elapsed_s','peak_rss_kib','nonlinear_iterations','nonlinear_last_relative_change')}})
    for filename,rows in [('operating_points.csv',scalars),('resource_usage.csv',resources),('stage_heat_budgets.csv',stages)]:csvwrite(out/filename,rows)
    # Cut dictionaries have common actual-field keys; no textbook currents inserted.
    csvwrite(out/'component_cuts.csv',cuts)
    j=a['jacobian'];names=j['parameter_names'];sv=np.asarray(j['singular_values']);matrix=np.asarray(j['matrix'])
    fig,ax=plt.subplots(figsize=(10,6));im=ax.imshow(matrix,aspect='auto',cmap='coolwarm',vmin=-3,vmax=3);ax.set_xticks(range(len(names)),names,rotation=55,ha='right');ax.set_yticks(range(len(j['observable_ids'])),j['observable_ids'],fontsize=6);fig.colorbar(im,ax=ax,label='Normalized screening derivative (color clipped +/-3)');ax.set_title('Calibration-only reduced network Jacobian; no PDE sensitivities');fig.tight_layout();fig.savefig(out/'jacobian.png',dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,3.5));ax.semilogy(range(1,len(sv)+1),sv,'o-');ax.axhline(sv[0]*j['relative_rank_threshold'],ls='--',color='gray',label='Declared relative rank threshold');ax.set(xlabel='Singular value index',ylabel='Singular value',title=f'Network rank {j["rank"]}/{j["columns"]}; exact structural null demonstrated');ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'singular_values.png',dpi=170);plt.close(fig)
    from tecooledmct.g2d_network import constant,baseline,coefficients
    b=constant(.2,0);screen_directions=[]
    for label,params in [('seebeck_minus10',{**baseline(),'seebeck_scale':.9}),('k_plus10',{**baseline(),'k_scale':1.1})]:
        screen=constant(.2,0,parameters=params);effect=f['effects'][label]
        screen_directions.append({'direction':label,'network_delta_cold_k':b['delta_t_k']-screen['delta_t_k'],'actual_PDE_delta_cold_k':effect['delta_cold_k'],'network_delta_V':screen['voltage_v']-b['voltage_v'],'actual_PDE_delta_V':effect['delta_voltage_v']})
    csvwrite(out/'network_vs_actual_directions.csv',screen_directions)
    direction_table='\n'.join(f"| {v['direction']} | {v['network_delta_cold_k']:+.6f} | {v['actual_PDE_delta_cold_k']:+.6f} | {v['network_delta_V']:+.8f} | {v['actual_PDE_delta_V']:+.8f} |" for v in screen_directions)
    ohmic_reference=sum(v[1] for v in coefficients(baseline(),(28,12,4)))
    fig,axs=plt.subplots(1,2,figsize=(11,5))
    for ax,key,unit in zip(axs,('delta_t_k','voltage_v'),('K','V')):
        for idx,n in enumerate(names):
            values=[r[key]-b[key] for r in a['one_at_a_time'] if r['parameter']==n];ax.plot(values,[idx,idx],'o-',lw=5,alpha=.7)
        ax.axvline(0,color='gray');ax.set(yticks=range(len(names)),yticklabels=names,xlabel=f'Change ({unit})',title='Network OAT over hypothesis bounds')
    fig.suptitle('300 K, .2 A, zero applied load; not measurement confidence or FEM');fig.tight_layout();fig.savefig(out/'tornado.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for ax,field,label in zip(axs,('delta_t_k','voltage_v'),('Temperature lift (K)','Voltage (V)')):
        loads=sorted(set(r['load_w'] for r in observed))
        for load in loads:
            rows=sorted([r for r in observed if r['field']==field and r['load_w']==load],key=lambda r:r['current_a']);line=ax.plot([r['current_a'] for r in rows],[r['value'] for r in rows],alpha=.55,label=f'OEM {load:g} W')[0]
            for split,marker in [('calibration_reserved','s'),('validation_holdout','o')]:
                selected=[r for r in rows if r['split']==split];ax.errorbar([r['current_a'] for r in selected],[r['value'] for r in selected],yerr=[r['value_reading_bound'] for r in selected],fmt=marker,ms=3,color=line.get_color())
        for idx,(name,r,_) in enumerate(models):ax.scatter([r['current_a']],[300-r['cold_mean_k'] if field=='delta_t_k' else r['voltage_v']],marker=['x','+','1','2'][idx],s=100,c='black',label=name)
        ax.set(xlabel='Module current (A)',ylabel=label);ax.grid(alpha=.2)
    axs[1].legend(fontsize=6);fig.suptitle('Observed OEM nominal-300 K vacuum: squares calibration, circles holdout\nActual constant-law Elmer points ONLY; missing source-backed family remains blocked');fig.tight_layout();fig.savefig(out/'oem_actual_overlay.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    means=[]
    for ax,field,unit in zip(axs,('delta_t_k','voltage_v'),('K','V')):
        for idx,(split,model) in enumerate([(s,m) for s in ('calibration_reserved','validation_holdout') for m in ('baseline','frozen_diagnostic_fit')]):
            rows=[r for r in a['residuals'] if r['split']==split and r['model']==model and r['field']==field];mean=float(np.mean([r['absolute_residual'] for r in rows]));means.append({'split':split,'model':model,'field':field,'points':len(rows),'mean_absolute_residual':mean});ax.bar(idx,mean)
        ax.set(xticks=range(4),xticklabels=['cal base','cal fit','hold base','hold fit'],ylabel=f'Mean absolute residual ({unit})')
    fig.suptitle('Reduced-network diagnostics only; frozen calibration fit then holdout score');fig.tight_layout();fig.savefig(out/'network_residuals.png',dpi=170);plt.close(fig);csvwrite(out/'network_residual_summary.csv',means)
    table='\n'.join(f"| {r['case']} | {r['field']} | {r['observed']:.6f} | {r['predicted']:.6f} | {r['signed_residual']:+.6f} | {100*r['relative_residual']:+.2f}% | {r['reading_bound']:.4f} |" for r in comparisons)
    op='\n'.join(f"| {k} | {r['cold_mean_k']:.7f} | {r['voltage_v']:.9f} | {r['electrical_input_w']:.8f} | {100*r['max_cut_relative_error']:.5f}% | {100*r['bath_gradient_energy_relative_residual']:+.5f}% |" for k,r in f['cases'].items())
    effects='\n'.join(f"- {k}: actual cold mean changes {v['delta_cold_k']:+.6f} K, voltage {v['delta_voltage_v']:+.9f} V, input {v['delta_input_w']:+.8f} W." for k,v in f['effects'].items())
    heat='\n'.join(f"| {k} | {r['hot_out_w']:.9f} | {r['cold_out_w']:.9f} | {r['electrical_input_w']:.9f} | {r['joule_w']:.9f} |" for k,r in f['cases'].items())
    stage_table='\n'.join(f"| {r['case']} / {r['stage']} | {r['hot_out_w']:.9f} | {r['cold_absorbed_w']:.9f} | {r['electrical_work_w']:.9f} | {r['energy_error_w']:+.2g} |" for r in stages)
    best=a['fit']['selected'];code=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report=f'''# G2d: OEM discrepancy and identification audit

Verified scoped D1/D2 checkpoint, 2026-10-29. **OEM/device qualification: FAILED / NOT ESTABLISHED.**
{test.group(1)} full tests passed with TE_FEM_SMOKE=1, existing CLI quick and geometry_demo completed.
Three new genuine coupled 3D 88-leg Elmer diagnostic solves passed; one additional actual source-profile
300 K execution failed closed and is not a performance point. Earlier G1/G2a/G2b/G2c accepted source,
tests and evidence are byte-identical. Existing attached sim session, original pinned image and
four-CPU/12-GiB serial wrapper reused; no host install or other repository operations.
Evidence generation code checkpoint: `{code}`; exact source/SIF/VTU hashes take precedence.

## Preregistered data and independent comparisons

Original TEC Microsystems 2019 vector curves: 160 scalar readings over four bath/environment panels,
all rechecked against preserved original vector paths and source PDF SHA256. New source audit retains
PDF coordinates, +/-1 PDF-point reading bounds, units, color/load mapping and numerical conversion.
These are existing independently digitized source readings, **not new OEM measurements**.
`data/g2d/preregistration.json` preserves .2/.6/1.0 A calibration versus .1/.4/.8 A holdouts.
Only nominal-300 K vacuum is compared: 22 calibration / 18 withheld scalar values. Dry-N2 data are
excluded because the solid-only model has no gas/environment heat path. No 295 K point is compared.

The literal source panel says **27 C** (300.15 K); the preserved G2c canonical panel is 300 K.
Matching here means that nominal panel. The 0.15 K rounding is an additional unquantified systematic,
not an assertion that the OEM experimentally held exactly 300.000 K. The source footnote stabilizes
the hot side at ambient; vacuum pressure, mounting resistance and precise measurement uncertainty
are not supplied. Module current, inward cold load, terminal V and DeltaT=Th-Tc are used.
Qmax .51 W, DeltaTmax113 K, 44 couples and2.9 ohm ACR are documentation, not simultaneous fit targets.

Fit objective uses **calibration vertical reading bounds only**, not neighboring slopes. A preliminary
attempt used full-curve slope weights and was discarded for leakage risk; it remains explicitly
unaccepted. The model, bounds and PDE directions were not selected from holdout residuals.
A SHA256-frozen calibration-only fit is written before held-out numeric scoring in the replacement
runner. Independence here means algorithmic separation: prior G2c comparisons and the discarded
attempt were already available, so this is not a newly blinded experimental validation. Reported residual
bounds combine horizontal chart-reading error with same-curve slope, strictly for reporting/scoring,
not fit weights. Those bounds are not experimental standard deviations or confidence intervals.
Broad-bound agreement does not establish device accuracy. See source, residual and frozen-fit JSON/CSV.

## Screening and identifiability, separate from FEM

The independent network solves linear constant-law cascades with exact per-stage Qh-Qc=I*V and
external energy closure, dimensional leg/Cu resistances, approximate Cu/rib shunts and optional
area-specific electrical/thermal contact, mounting and added-load nuisance parameters. All nine
parameter bounds are declared hypotheses, not inferred confidence. Width varies with fixed stage
heights: A=A0/aspect; actual changed geometry would require a new audited mesh. Integer allocations
28/12/4,26/12/6,24/12/8,30/10/4 all sum44; none is a continuously fitted or actually remeshed topology.
Measured v2r1 curves are separately evaluated in local-T 1D leg BVPs at295 K,.05/.1 A, using
q'=J.E and k*T'=S*T*J-q with exact signed P/N currents and implicit Thomson conversion.
Those are **network** exercises, not new 3D solves or OEM comparisons.

Normalized calibration Jacobian: **rank {j['rank']}/{j['columns']}**, threshold1e-7 relative to
largest singular value; full inverse condition is unbounded. Largest/smallest finite-difference
singular values {sv[0]:.8g}/{sv[-1]:.8g}; tiny nonzero null value is differencing error.
The rank is stable when the step is halved. Normalization uses declared parameter scales and
max(abs(base observable),1 K/.01 V), not a Fisher likelihood. Weak retained directions are also
poorly conditioned: largest/smallest retained ratio {sv[0]/sv[j['rank']-1]:.4g}.

**Exact structural degeneracy:** at zero added contacts, aspect*c,rho/c,k*c preserve every stage
R and K, with S and topology fixed. Two distinct admissible fitted parameter sets, c=1.02,
have maximum calibration difference {a['fit']['maximum_calibration_prediction_difference']:.3g}
and withheld difference {a['equivalent_holdout_prediction_difference']:.3g}. Hence grade and width
cannot be separately identified by these steady curves, even with perfect numerical precision.
Routing versus thermal contacts, added loads and bath resistance create further weak directions;
finite-difference rank does not establish unique physical parameters.

Calibration-only three-scale fit selected {best['counts']}, rho={best['parameters']['rho_scale']:.7f},
S={best['parameters']['seebeck_scale']:.7f}, k={best['parameters']['k_scale']:.7f} times constant reference.
k reaches its predeclared fit bound1.25. This fit does not identify a measured grade or repair the
3D model. Across all matched loads, network held-out mean absolute residual changes from13.4916 to
4.9683 K and .333223 to .057957 V. These improvements are **screening evidence only**; no fitted
network point is labeled Elmer and no fitted FEM curve family is claimed.

![Network OAT hypothesis bounds](../fem/results/g2d_20261029/charts/tornado.png)
![Calibration network Jacobian](../fem/results/g2d_20261029/charts/jacobian.png)
![Network singular values](../fem/results/g2d_20261029/charts/singular_values.png)
![Frozen network diagnostic residuals](../fem/results/g2d_20261029/charts/network_residuals.png)

## Bounded genuine Elmer checks

Preregistered directions: original constant reference, both P/N S reduced10%, both P/N k increased10%.
All three execute actual ThermoElectricSolver for T and phi at300 K bottom bath,.2 A total module
series current,zero applied top load, adiabatic sides,ideal contacts and no fixed intermediate T.
These constant laws are mathematical diagnostics, **not measured wide-temperature OEM profiles**.
The generic postprocessor's1..1500 K computational interval is not measured material coverage.

Re-audited preserved fine G2b mesh:91,538 nodes,384,121 tetrahedra,183,076 DOFs,189 material domains,
181 conductor vertices/180 graph edges,exactly two terminals,all88 legs once. Actual tetrahedral
face connectivity, domain volume/contact area, SICN and ElmerGrid node/tetra/body mapping pass.
No topology alternative or full-stack contact mesh is claimed. The existing mesh was reused;
current/energy gates are checked at each new point, but **new direction-specific mesh convergence
and raw terminal-corner flux convergence are not established**.

| Actual case | Cold mean K | Terminal V | Input W | Worst175cut error | Direct bath mismatch |
|---|---:|---:|---:|---:|---:|
{op}

{effects}

| Direction | Screening delta Tc K | Actual PDE delta Tc K | Screening delta V | Actual PDE delta V |
|---|---:|---:|---:|---:|
{direction_table}

The independent network reproduces the signs and approximate magnitudes, not the exact3D response.
At this calibration point, S minus10% reduces the absolute lift residual by57.9% and voltage
residual by33.4%; k plus10% reduces them by41.0% and11.9%. These are finite diagnostic perturbations,
not fitted OEM coefficients. The fixed-reference dimensional ohmic network estimate is
{ohmic_reference:.6f} ohm versus documented2.9 ohm ACR; it excludes the finite-DeltaT Seebeck voltage
and is not a direct resistance measurement. Together these checks support material/geometry/routing
ambiguity as a credible explanation, without assigning a unique physical cause.

All accepted exits zero; nonlinear relative change <1e-9,all175 interior cuts <.5%,global/free-node
current and energy gates pass. Direct bath gradient check <1%; conservative heat/work checks are
independent of it. Solver wall/RSS/iterations plus actual SIF/VTU hashes are archived per execution.
Perturbed cases use a hashed actual baseline solution as a warm start and still execute full PDEs.

| Nominal300K vacuum case | Observable | OEM | Actual FEM | Signed residual | Relative | Reading bound +/- |
|---|---|---:|---:|---:|---:|---:|
{table}

The .1 A row is a **preserved G2b actual holdout execution**, reused without claiming another solve.
The .2 A rows are new calibration comparisons. No interpolation creates PDE points. The observed
residual direction can improve under diagnostic material changes; that does not show which OEM
parameter is wrong, uniquely identify it, or validate a family of source-backed predictions.

![Observed OEM versus actual matched Elmer only](../fem/results/g2d_20261029/charts/oem_actual_overlay.png)
![Representative actual baseline fields](../fem/results/g2d_20261029/fields/baseline/fields.png)

## Actual heat budgets

| Actual case | Hot out W | Cold out W | I*V W | Irreversible Joule W |
|---|---:|---:|---:|---:|
{heat}

Hot out+cold out=I*V; Joule and electrical work differ through thermoelectric reversible conversion.
An additional independent P1 reconstruction integrates actual q and J.E through nodal plane control
volumes in the shared plates. These stages include intersected routing/dielectric portions;
they are not leg-only textbook budgets and prescribe no intermediate temperatures.

| Actual case / stage bottom0 | Hot out W | Cold absorbed W | J.E work W | Balance error W |
|---|---:|---:|---:|---:|
{stage_table}

## Source-domain failure and independent material review

The genuine 88-leg v2r1 probe at300 K,.1 A,zero top load terminated on local BiTe evaluation at
**{probe.get('rejected_temperature_k')} K**, beyond the strict40..300 K source. It is an actual rejected
iterate, not a converged maximum or proof that no mathematical in-range solution exists. No clamp,
extrapolation or performance prediction is accepted. Its real nonzero exit/log/compiled callbacks
and source hashes are retained separately. Earlier295 K result247.304696 K/.78633050 V is unchanged
and remains outside the OEM nominal300 K comparison.

An independent above300 K source exists: [Kumari et al., DOI10.1080/27660400.2025.2586299](https://doi.org/10.1080/27660400.2025.2586299),
primary institutional PDF SHA256a8d37fb8e6b69ccd0665ae24fe0f0a67909f00c8b582e768a897941c9648138a.
Verified HP A-axis P Bi0.46Sb1.54Te3/N Bi2Te2.7Se0.3 tables span298.15..573.15 K.
S/sigma are simultaneous bar measurements; diffusivity uses separate cuts, and total k is calculated
with assumed Dulong-Petit Cp. They are composition/process/direction matched, not all the same
physical specimen. N sign,SI conversion,reciprocal rho and independently tabulated PF/ZT agree within
propagated printed-digit rounding. Original table screenshots and source review JSON are archived.
This source does not cover the cold legs and is not the Zhang HE or OEM grade. It is not stitched
to unrelated low-T data or used in any fit/PDE. Its own module extrapolation policy is not adopted.
The bounded review found no verified single-grade P/N dataset spanning the needed full local range;
this is not a claim that none exists. Cai stays quarantined; no guessed missing properties.

## Engineering verdict and minimum new evidence

D1/D2 and three scoped diagnostic PDE directions are numerically verified. **D3 source-backed
OEM family fit/independent FEM holdout qualification remains FAILED / BLOCKED** by local-T coverage,
unidentified grade/geometry/routing and finite computational scope. Full88-leg contact transitions,
solder chemistry,contact mesh/refinement,grade tensors,alternate topology meshes,loaded/high-current
FEM family,hot-mount calibration and package/radiation/gas are pending. Four-couple G2c contacts
never qualify the full stack. Nothing here establishes production accuracy.

Request the smallest evidence set that breaks the ambiguity:

1. Actual leg width/height by stage,couple counts and buried metallization/contact dimensions;
   at least one measured dimensional ratio is required to break the demonstrated exact null.
2. Directional P/N S(T),rho(T),total k(T) for the actual grade across the entire local range,
   with specimen/process IDs and uncertainty; measure beyond300 K rather than splice other grades.
3. Area-specific electrical and thermal contact data plus solder thickness/thermopower; hot ceramic
   versus controlled-bath temperatures at known heat flux to separate mounting resistance.
4. Independent simultaneous I,V,Th,Tc,Qc points at zero and at least two known loads,with raw uncertainty,
   pressure and parasitic lead/radiation accounting. Freeze calibration,then reserve different currents
   and loads for genuine OEM-matched FEM validation. The existing digitized curves alone cannot
   replace independent geometry/material/thermal-boundary measurements.
'''
    (ROOT/'docs/PHASE1_G2D_RESULT.md').write_text(report)
    # Archive only after all acceptance checks above. Originals are never rewritten.
    target=ROOT/'fem/results/g2d_20261029';target.mkdir(parents=True,exist_ok=True)
    def copy(src,rel):
        p=target/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,p)
    copy(actual/'summary.json','actual/summary.json');copy(actual/'budgets.json','actual/budgets.json');copy(ROOT/'outputs/g2d-source-audit.json','sources/vector_and_table_audit.json')
    for p in analysis.iterdir():
        if p.is_file():copy(p,Path('screening')/p.name)
    for p in (analysis/'preliminary_unaccepted').iterdir():copy(p,Path('provenance/preliminary_unaccepted')/p.name)
    for p in DATA.glob('*.json'):copy(p,Path('sources')/p.name)
    for p in out.iterdir():
        if p.is_file():copy(p,Path('charts')/p.name)
    for name in ('audit.json','manifest.json','grid-status.json','grid.log'):copy(actual/'mesh'/name,Path('mesh')/name)
    # Immutable mesh arrays/file already published in G2b; hash/reference avoids a duplicate.
    dump(target/'mesh/reference.json',{'path':'fem/results/g2b_two_terminal_20261028/meshes/mesh_2','mesh_npz_sha256':sha(actual/'mesh/mesh.npz'),'connected_msh_sha256':sha(actual/'mesh/connected.msh')})
    for label,r in f['cases'].items():
        case=actual/label
        for name in ('case.sif','case.json','metrics.json','solver.log','solver-status.json'):copy(case/name,Path('actual/cases')/label/name)
        copy(case/'fields.png',Path('fields')/label/'fields.png')
        # Retain all three actual raw T/phi fields; deterministic compression only.
        dest=target/'fields'/label/(r['field_source']+'.gz');dest.parent.mkdir(parents=True,exist_ok=True)
        with (case/r['field_source']).open('rb') as src,dest.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as zipped:shutil.copyfileobj(src,zipped)
        dump(target/'fields'/label/'uncompressed_sha256.json',{r['field_source']:r['vtu_sha256']})
    for name in ('case.sif','case.json','solver.log','solver-status.json','probe.json'):copy(actual/'source_300K_probe'/name,Path('blocked_source_probe')/name)
    runtime={}
    for p in (actual/'probe_library').rglob('*'):
        if p.is_file():
            runtime[str(p.relative_to(ROOT))]=sha(p)
            if p.suffix!='.so':copy(p,Path('blocked_source_probe/library')/p.relative_to(actual/'probe_library'))
    dump(target/'blocked_source_probe/library_hashes.json',runtime)
    for n in ('kumari-p31.png','kumari-p32.png'):copy(ROOT/'outputs/g2d-sources'/n,Path('sources')/n)
    for n in ('g2d-preregistration.log','g2d-analysis.log','g2d-analysis-calibration-only.log','g2d-fem.log','g2d-budgets.log','g2d-source-audit.log','pytest-g2d-targeted.log','pytest-g2d-full.log','cli-g2d.log','geometry-g2d.log'):copy(ROOT/'logs'/n,Path('provenance')/n)
    for p in [*(ROOT/'tecooledmct').glob('g2d*.py'),ROOT/'scripts/audit_g2d_sources.py',ROOT/'fem/report_archive_g2d.py',ROOT/'tests/test_g2d.py',*DATA.glob('*.json')]:sources[str(p.relative_to(ROOT))]=sha(p)
    image=json.loads((ROOT/'outputs/g2d-image.json').read_text())[0];dump(target/'provenance/image.json',{'Id':image['Id'],'RepoTags':image['RepoTags']})
    dump(target/'checksums.json',{'code_checkpoint':code,'source_sha256':sources,'protected_integrity':integrity,'unique_new_accepted_solver_executions':3,'rejected_source_probe_executions':1,'reused_G2b_holdout_executions':1,'device_qualification_passed':False,'test_count':int(test.group(1)),'artifact_sha256':{str(p.relative_to(target)):sha(p) for p in sorted(target.rglob('*')) if p.is_file() and p.name!='checksums.json'}})
    print('Verified G2d archive: 3 new accepted actual PDEs, 1 rejected source probe, 1 reused actual holdout; OEM qualification FAILED')

if __name__=='__main__':main()
