#!/usr/bin/env python3
"""Generate plots and final report only from accepted real G2c summaries."""
import csv,json,re,subprocess
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]

def main():
    stage=json.loads((ROOT/'outputs/fem-g2c/summary.json').read_text());contact=json.loads((ROOT/'outputs/fem-g2c-contact-fine/summary.json').read_text());stack=json.loads((ROOT/'outputs/fem-g2c-stack/summary.json').read_text())
    low=json.loads((ROOT/'outputs/fem-g2c-low-temperature/summary.json').read_text())
    if not(stage['verification']['passed'] and contact['passed'] and stack['passed'] and low['passed']):raise SystemExit('Refusing success report on failed numerical gates')
    log=(ROOT/'logs/pytest-g2c-final.log').read_text();m=re.search(r'(?m)^(\d+) passed(?:,.*)? in ',log)
    if not m:raise SystemExit('Completed passing full regression required')
    out=ROOT/'outputs/g2c-report';out.mkdir(exist_ok=True)
    profile=json.loads((ROOT/'data/g2c/zhang2025_he_40_300_v2.json').read_text());oem=json.loads((ROOT/'data/g2c/oem2019_curves_v1.json').read_text())
    fig,axs=plt.subplots(1,3,figsize=(12,3.5))
    for polarity,sample in profile['specimens'].items():
        for ax,key,label,factor in zip(axs,('S','rho','k'),('Seebeck (microvolt/K)','Resistivity (micro-ohm m)','Thermal conductivity (W/m/K)'),(1e6,1e6,1)):
            rows=sample['curves'][key]['points'];ax.errorbar([r['temperature_k'] for r in rows],[factor*r['value_si'] for r in rows],yerr=[factor*r['value_reading_bound_si'] for r in rows],xerr=[r['temperature_reading_bound_k'] for r in rows],fmt='o-',label=sample['sample_id']);ax.set(xlabel='Temperature (K)',ylabel=label);ax.grid(alpha=.3)
    axs[0].legend();fig.suptitle('Published HE sample markers, 40–300 K; reading bounds exclude measurement/systematic uncertainty');fig.tight_layout();fig.savefig(out/'material_profiles.png',dpi=170);plt.close(fig)
    from tecooledmct.g2c_qualification import family_objective
    baseline=json.loads((ROOT/'fem/results/g2b_two_terminal_20261028/summary.json').read_text())['cases']['zero_load_positive']
    prediction={'current_a':.1,'load_w':0.,'hot_k':300,'ambient':'vacuum','delta_t_k':300-baseline['cold_mean_k'],'voltage_v':baseline['voltage_v'],'origin':'preserved actual G2b zero-load solve'}
    (out/'oem_objective.json').write_text(json.dumps({'calibration':family_objective([]),'holdout':family_objective([prediction],'validation_holdout')},indent=2)+'\n')
    comparisons=stage['oem_comparison']['comparisons'];fig,axs=plt.subplots(1,2,figsize=(9,3.8))
    for ax,field,label in zip(axs,('delta_t_k','voltage_v'),('Temperature lift (K)','Voltage (V)')):
        for load in oem['panels'][0]['loads_w']:
            rows=sorted([r for r in oem['points'] if r['panel']=='300K_vacuum' and r['field']==field and r['load_w']==load],key=lambda r:r['current_a'])
            ax.plot([r['current_a'] for r in rows],[r['value'] for r in rows],'-',alpha=.6,label=f'OEM {load:g} W')
            withheld=[r for r in rows if r['split']=='validation_holdout'];ax.errorbar([r['current_a'] for r in withheld],[r['value'] for r in withheld],xerr=[r['current_reading_bound_a'] for r in withheld],yerr=[r['value_reading_bound'] for r in withheld],fmt='o',ms=3,alpha=.7)
        r=next(r for r in comparisons if r['field']==field);ax.scatter([r['current_a']],[r['fem_value']],marker='x',s=70,color='black',label='Preserved constant G2b, no load')
        ax.set(xlabel='Current (A)',ylabel=label);ax.grid(alpha=.3)
    axs[1].legend(fontsize=7);fig.suptitle('300 K vacuum holdout comparison; no fit, no grade-matched device validation');fig.tight_layout();fig.savefig(out/'oem_holdouts.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(9,3.5))
    for ax,key,label in zip(axs,('residual','relative_residual'),('FEM minus source','Relative residual (%)')):
        for i,r in enumerate(comparisons):
            if key=='residual':
                value=r[key];bound=r['source_reading_bound']
            else:value=100*r[key];bound=100*r['source_reading_bound']/abs(r['source_value'])
            ax.errorbar([i],[value],yerr=[bound],fmt='o');ax.set_xticks(range(len(comparisons)),[r['field'] for r in comparisons]);ax.axhline(0,color='gray');ax.set(ylabel=label)
    fig.suptitle('Held-out no-load +0.1 A diagnostic; absolute residual axes use K and V respectively');fig.tight_layout();fig.savefig(out/'holdout_residuals.png',dpi=170);plt.close(fig)
    rows=sorted([r for k,r in stage['cases'].items() if k.startswith('source_') and 'frozen' not in k],key=lambda r:r['nodes'])
    fig,axs=plt.subplots(1,2,figsize=(9,3.5));axs[0].plot([r['nodes'] for r in rows],[r['cold_mean_k'] for r in rows],'o-');axs[0].set(xlabel='Nodes',ylabel='Cold mean (K)')
    axs[1].plot([r['nodes'] for r in rows],[100*r['bath_gradient_energy_relative_residual'] for r in rows],'o-');axs[1].axhline(1,color='gray',ls='--');axs[1].axhline(-1,color='gray',ls='--');axs[1].set(xlabel='Nodes',ylabel='Direct bath mismatch (%)');fig.suptitle('Genuine four-couple source-profile mesh study, 295 K bath, +0.05 A / 2 mW');fig.tight_layout();fig.savefig(out/'stage_convergence.png',dpi=170);plt.close(fig)
    c=contact['cases'];fig,axs=plt.subplots(1,2,figsize=(9,3.5));axs[0].bar(['zero added R','electrical R'],[1000*c[k]['voltage_v'] for k in ('fixed_reference','electrical')]);axs[0].set(ylabel='Voltage (mV)',title='295 / 285 K fixed faces, +0.05 A')
    axs[1].bar(['zero added R','thermal R'],[1000*c[k]['cold_out_w'] for k in ('passive_reference','thermal')]);axs[1].set(ylabel='Passive cold heat out (mW)',title='295 / 285 K fixed faces, zero drive');fig.suptitle('Explicit meshed transition zones, assumed law; not measured OEM Sn-Sb solder');fig.tight_layout();fig.savefig(out/'contact_checks.png',dpi=170);plt.close(fig)
    fine=stack['cases']['fine'];s=stage['cases']['source_3'];rod=stage['cases']['thomson_rod']['analytic'];base=stage['cases']['constant_regression'];checks=len(stage['verification']['checks'])+len(contact['checks'])+len(stack['checks'])+len(low['checks'])
    table='\n'.join(f"| {r['field']} | {r['source_value']:.6f} | {r['fem_value']:.6f} | {r['residual']:+.6f} | {100*r['relative_residual']:+.2f}% | ±{r['source_reading_bound']:.4f} | {'PASS' if r['within_nominal_gate'] else 'FAIL'} |" for r in comparisons)
    stage_table='\n'.join(f"| {r['nodes']:,} | {r['tetrahedra']:,} | {r['cold_mean_k']:.7f} | {100*r['bath_gradient_energy_relative_residual']:+.5f}% |" for r in rows)
    # Independently extract original ceramic-domain statistics from actual VTU.
    import meshio
    from scipy.spatial import cKDTree
    from tecooledmct.fem_g1 import tetra_geometry
    field=meshio.read(Path(fine['case_path'])/fine['field_source']);mesh_path=Path(fine['mesh_path']);arrays=np.load(mesh_path/'mesh.npz')
    distance,mapping=cKDTree(field.points).query(arrays['points'])
    if distance.max()>1e-12 or len(np.unique(mapping))!=len(mapping):raise ValueError('Plate diagnostic VTU/mesh mismatch')
    temperatures={n.lower():v.ravel()[mapping] for n,v in field.point_data.items()}['temperature'];volumes,_=tetra_geometry(arrays['points'],arrays['cells'])
    plates=[]
    for body in json.loads((mesh_path/'manifest.json').read_text())['bodies']:
        if body['kind']!='ceramic':continue
        selected=arrays['bodies']==body['id'];cells=arrays['cells'][selected];tt=temperatures[cells]
        plates.append({'domain':body['name'],'mean_k':float(np.dot(volumes[selected],tt.mean(axis=1))/volumes[selected].sum()),'min_k':float(tt.min()),'max_k':float(tt.max())})
    if len(plates)!=4:raise ValueError('Expected four original ceramic plates')
    with (out/'stack_plate_temperatures.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(plates[0]));writer.writeheader();writer.writerows(plates)
    plate_table='\n'.join(f"| {p['domain']} | {p['mean_k']:.6f} | {p['min_k']:.6f} | {p['max_k']:.6f} |" for p in plates)
    contact_min=min(contact['mesh_audit']['min_tetra_sicn'],contact.get('refined_zero_mesh_audit',contact['mesh_audit'])['min_tetra_sicn'])
    code_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report=f'''# G2c: bounded material and contact numerical qualification

**Verified numerical checkpoint, 2026-10-28.** {m.group(1)} tests passed with actual
G1/G2a/G2b and new compiled-material Elmer smoke; all {checks} stage, contact and
source-backed stack checks passed. Prior G1/G2a/G2b source/evidence hashes are
unchanged. Existing `sim` session and pinned Elmer 26.2.1 / Gmsh 4.13.1 image
were reused. No host installation, other repository or LSDDTS operation.
Code baseline for evidence generation: `{code_sha}`; exact execution source,
SIF/VTU/mesh and generated material-library hashes accompany the evidence.

**Device/OEM qualification remains NOT ESTABLISHED.** The material grade,
stage geometry, transition law, package mounting/environment and complete OEM
family have not been independently identified. Numerical gates are not device
accuracy gates. No fitting to 113 K / 0.51 W or freely tuned material curves.

## Traceable material evidence

See [source qualification](G2C_MATERIAL_PROVENANCE.md) for exact sources, sample
IDs, SI conversions, plot coordinates, reading bounds and coverage limitations.
Fourteen original PDF markers per property at 40/60/.../300 K were digitized
for N-HE-1 and P-HE from Zhang et al. (2025), DOI 10.1088/0256-307X/42/5/056304.
Rho, S and k were measured on the same specimen within each polarity. This pair
is not identified as a matched module pair or as TEC Microsystems' proprietary
grade. Sigma is exactly 1/rho in the library; rho, S and k use piecewise-linear
interpolation. The corrected default v1r1 200–300 K subset used by the stage checks
is unchanged. Additive opt-in v2r1 used by the full-stack and low-temperature checks extends
the source markers to 40–300 K, with
an identical v1 subset. Neither profile silently extrapolates outside its own
interval. These longitudinal sample properties are used as isotropic scalars;
OEM texture/orientation/tensor properties are not qualified.
Reading bounds do not include all measurement/systematic/specimen uncertainty.

Goldsmid's Table 1 remains a partial fixed-thermopower conductivity example, not
a full low-temperature triple-property profile. Cai's table remains quarantined
pending original unit/provenance verification and would not cover 262 K anyway.
No missing S(T)/k(T) was inferred from conductivity.

![Measured sample markers and reading bounds](../fem/results/g2c_20261028/charts/material_profiles.png)

The opt-in adapter compiles actual Elmer `Variable Temperature / Procedure`
functions, including a runtime range rejection. The pinned solver evaluates
properties at local nodes, then interpolates them at integration points. The
postprocessor follows that actual discretization and reconstructs E/J/q/Joule
and the nonlinear weak form. This is not a stage-average property substitution.
An intentional 301 K runtime test proves fail-closed behavior. Bounded
performance checks use 295 K baths. Final visual source review corrected the
N-panel negative-axis origin before publication; independent Seebeck and
power-factor anchors now verify the extraction. All affected source-profile
PDEs and full regressions were rerun. Original incorrect-input runs remain
quarantined and unaccepted. Constant-profile contact PDE inputs were unchanged
and their actual fields/callback sources independently reverified.

## Genuine four-couple and Thomson checks

All four meshes were solved at +0.05 A, 2 mW top load, 295 K bottom bath with
no prescribed cold temperature. Current/energy and material-interval checks pass.

| Nodes | Tetrahedra | Cold mean (K) | Direct bath energy mismatch |
|---:|---:|---:|---:|
{stage_table}

The fine source-backed stage gives {s['cold_mean_k']:.7f} K and
{s['voltage_v']:.9f} V. Its worst component-current error is
{100*s['max_cut_relative_error']:.5f}%. Free-node thermal/current residual norms
are {s['free_thermal_residual_l1_w']:.3g} W / {s['free_current_residual_l1_a']:.3g} A.
Freezing the same source profile at 300 K gives
{stage['cases']['source_frozen_300']['cold_mean_k']:.7f} K, demonstrating that the
local-temperature material law changes the actual PDE result. A constant G1
profile agrees with the preserved independent constant-property postprocessor.
Synthetic curves are explicitly tagged as function tests, never measurements.

![Stage mesh study](../fem/results/g2c_20261028/charts/stage_convergence.png)

A synthetic linear-S rod was genuinely solved in 3D and compared with an
independent nonlinear 1D continuum BVP, k T'' = J T(dS/dT) T' − J²/sigma.
Maximum nodal temperature error: **{rod['max_nodal_temperature_error_k']:.7f} K**;
voltage error: **{rod['voltage_error_v']:.3g} V**. Omitting the Thomson term changes
the reference by **{rod['nonzero_thomson_effect_vs_constant_S_k']:.6f} K**. Thomson
conversion is implicit in div(T S(T) J); no duplicate heat source was added.
The final rod BC combines thermal and electrical conditions in each boundary
list. An earlier duplicate-target prototype did not converge and is not accepted.

An additional genuine four-couple check exercised the v2 source law below
200 K with **200 K / 190 K imposed ceramic faces**, +0.02 A. Its terminal voltage
is {low['cases']['source_low_temperature']['voltage_v']:.9f} V; worst interior
current error is {100*low['cases']['source_low_temperature']['max_cut_relative_error']:.5f}%;
weak energy/work residuals are
{low['cases']['source_low_temperature']['energy_relative_residual']:.3g} /
{low['cases']['source_low_temperature']['power_work_relative_residual']:.3g}.
This tests the source-backed low-temperature PDE adapter. The 190 K face is a
controlled boundary condition, **not a predicted attainable cooler temperature**.
Source coverage has improved; OEM-grade/device qualification has not been inferred.

## Explicit transition resistance model

Sixteen **20 micrometre meshed transition domains** occupy the ends of the eight
legs without overlap. The remaining leg cores shorten accordingly. Each zone
has rho_eff = rho_BiTe + r_e/t and 1/k_eff = 1/k_BiTe + r_th/t; its Seebeck law
is assumed equal to the adjacent leg. This is a phenomenological resistive
transition zone, **not a claimed Sn-Sb solder composition or measured contact**.
These contact checks use the original constant verification profile. The
original Cu/BiTe Peltier interfaces remain in the coupled weak form. Added
irreversible heat is integrated within the explicit transition domains.

At r_e=r_th=0 the complete original continuum is recovered: the same S/rho/k
occupy the same envelope. The separately meshed result differs from the original
baseline cold mean by {abs(c['zero_excess']['cold_mean_k']-base['cold_mean_k']):.7f} K.
At fixed 295/285 K faces, adding r_e=1e-9 ohm m² raises voltage from
{c['fixed_reference']['voltage_v']:.9f} to {c['electrical']['voltage_v']:.9f} V.
The additional layer Joule heat is {1000*c['electrical']['extra_contact_joule_w']:.6f} mW,
matching 16 I² r_e/A to the declared 0.5% gate. Independently adding
r_th=1e-5 m² K/W reduces passive heat transfer. Both resistances are also solved
together under a cold heat load: Tc={c['coupled']['cold_mean_k']:.7f} K and
V={c['coupled']['voltage_v']:.9f} V. Global energy/work, driven <0.5% cuts and
zero-drive <1 microamp cuts pass. Minimum tetrahedron SICN is
{contact_min:.5f}; actual body/contact/face-connectivity
checks pass. The initial 0.04 mm passive cases missed the 1 microamp cut gate (worst
1.032 microamp). They were replaced by genuine 0.03 mm passive solves; the four
completed driven cases were independently reverified from their actual fields,
not rerun or attributed to new executions. Original failed-accuracy fields,
logs/statuses and the initial summary remain retained and unaccepted.

![Contact-law verification](../fem/results/g2c_20261028/charts/contact_checks.png)

This verifies this assumed law, not real OEM contacts. Thin-metal solder with
its own thermopower, measured interface data, thickness/contact sensitivity and
full-stack contact qualification remain separate gates.

## Source-backed 88-leg full-stack check

Actual G2b meshes were copied, re-audited (including per-body tetra-face
connectivity), re-converted with ElmerGrid and solved with the local-T source
profile. Geometry and published G2b inputs/evidence are unchanged. No intermediate
plate temperature is fixed; interfaces in this stack check remain ideal.
At **295 K bath, +0.1 A, zero top load**, the fine mesh gives
**{fine['cold_mean_k']:.6f} K / {fine['voltage_v']:.8f} V**,
{fine['nodes']:,} nodes / {fine['tetrahedra']:,} tetrahedra. Coarse-to-fine cold
mean change is {abs(fine['cold_mean_k']-stack['cases']['coarse']['cold_mean_k']):.6f} K;
all 175 fine component cuts meet 0.5%, worst {100*fine['max_cut_relative_error']:.5f}%.
Direct bath energy mismatch is {100*fine['bath_gradient_energy_relative_residual']:+.6f}%;
weak global energy and work errors are {fine['energy_relative_residual']:.3g} /
{fine['power_work_relative_residual']:.3g}. Every actual BiTe nodal temperature
lies in the source interval. This is a 295 K numerical point, not a 300 K OEM
holdout or an absolute cooler prediction. No above-300 K reverse-drive material
extrapolation was performed.

Original ceramic-domain temperatures, excluding routing supports:

| Domain | Volume mean (K) | Min (K) | Max (K) |
|---|---:|---:|---:|
{plate_table}

![Actual source-backed full-stack fields](../fem/results/g2c_20261028/fields/stack_fine/fields.png)

## Manufacturer holdouts and remaining identification

The specific 2019 original datasheet page 2 was inspected and 160 numerical
readings digitized from its original colored vector curves. Four panels retain
hot temperature, vacuum/dry-N2 environment, printed loads, source hash and plot
reading bounds. Currents .2/.6/1.0 A are calibration-reserved; .1/.4/.8 A are
withheld. No calibration points were used and no fit was performed.

Only the preserved actual constant-material G2b +0.1 A / zero-load / 300 K result
is compared with a matching 300 K vacuum source point. The 2 mW prior result
cannot be relabelled no load; the 295 K source-backed run is not compared with
a 300 K panel. Dry-N2 curves are not used to validate a vacuum-only solid model.

| Field | OEM reading | Prior constant FEM | Residual | Relative residual | Combined reading bound | Point gate |
|---|---:|---:|---:|---:|---:|---|
{table}

![Reserved family and actual holdout comparison](../fem/results/g2c_20261028/charts/oem_holdouts.png)

![Absolute/relative holdout residuals](../fem/results/g2c_20261028/charts/holdout_residuals.png)

The temperature holdout fails the declared nominal error-plus-reading-bound
envelope. A point passing a broad digitization bound does not validate a device
or its full performance family.

The family objective is explicitly separated by split and weights residuals by
plot-reading bounds; it is not a statistical likelihood. The full family has
not been fitted or validated. Unknown leg dimensions/stage counts, property
grades, contacts, routing and environment are not uniquely identifiable from
terminal curves alone: R scales as L/(sigma A), K as k A/L and alpha as couple
count times thermopower. No experimental precision or unique parameter set is
claimed. The discrepancy is evidence of missing qualification, not a reason to
freely tune constants to OEM extrema.

## Evidence and reproduction

See [G2c reproduction](G2C_REPRODUCIBILITY.md). Accepted logs, source/mesh/SIF/VTU
hashes, actual representative fields, generated Fortran sources and compilation
records, resource metrics, source registry, plots and raw reading coordinates
are archived under `fem/results/g2c_20261028`. Complete raw runs and failed
attempts remain under ignored `outputs/`; incomplete/failed experiments are
explicitly separate. Serial containers remain capped at four CPUs / 12 GiB.
G1/G2a/G2b protected hashes pass. G2c OEM/device qualification remains open;
TO-66 package/gas/radiation and LSDDTS integration were not added.
'''
    (ROOT/'docs/PHASE1_G2C_RESULT.md').write_text(report)
    (out/'qualification_status.json').write_text(json.dumps({'numerical_checks':checks,'numerical_passed':True,'tests_passed':int(m.group(1)),
        'oem_device_validation':False,'grade_match':False,'default_stage_profile_interval_k':[200,300],'stack_profile_interval_k':[40,300],'opt_in_v2_profile_interval_k':[40,300],'code_commit':code_sha},indent=2)+'\n')

if __name__=='__main__':main()
