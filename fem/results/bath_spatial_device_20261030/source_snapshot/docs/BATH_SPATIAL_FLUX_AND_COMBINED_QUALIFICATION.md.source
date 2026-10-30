# Spatial bath raw-flux investigation: verified checkpoint

**Numerical release remains incomplete.** Four independent archived-field audits,
five completed manufactured 3D HeatSolver cases and two new full 88-leg coupled
Elmer runs establish a controlled negative result: boundary-owner transverse and
volume refinement does not resolve the original raw bath1% gate. The new pair
has1.288505% and1.290712% errors. Combined and qualified-comparator runs are
NOT RUN because their independent bath prerequisite is unmet. No additional large
parameter campaign or threshold fitting is performed.

The approved15-page Rev3 review PDF, both sealed review editions, historical
Rev2 and every previous accepted/failed source and field remain unchanged.
This technical checkpoint and its actual-field figures carry the new evidence;
the approved report is not redesigned or silently updated.

## Unchanged physical problem and source status

The VIGO ZTM-TO66-Z030 Rev9 source housing plus independent TEC Microsystems
3MC04-044-05 candidate is an unverified synthetic assembly. Internal routing,
materials and contacts remain hypotheses; no OEM thermal calibration is claimed.
The model retains216 domains/88legs,0.1A,2mW MCT volumetric heat,300K on actual
Kovar underside only, Cu/Au links OFF and identical material laws. There is no
cap/window/gas/radiation, carrier PDE or optical-window transport.

Original limits remain raw bathabs<1%, ceramic/attachabs<5%, every177current
cut<0.5%, global/stage/free heat residuals<1microW, free current<1microA and
nonlinear relative change<1e-9. A later release needs both raw gates on one
production mesh AND a systematically refined comparator, with the remaining
baseline/reproducibility and output-sensitivity checks. Preferred0.9%/4.5%
margins are targets, not alternative acceptance criteria.

## Independent signed spatial audit

Geometry partitions are registered before results in
`data/bath_spatial/diagnostic_plan.json`: radial/quadrant/angular groups,
source-positioned glass annuli, mounting-hole neighborhoods, actual outer rim,
ear lobes, hot footprint and projected hot-route boxes. Bins classify actual
triangle centroids; patch areas and counts are retained, so cross-mesh bin
sampling is visible. No post-solve error-quantile mask selects refinements.

A cross-product affine-gradient reconstruction reproduces four archived raw bath
powers and independently maps native nodes AND tetrahedra. The bath is exactly
all external Kovar z=0 triangles,333.919817mm2; normals point -z. All bath nodes
are300K within5.7e-14K. The actual SIF has only thermal Dirichlet tag101.
Glass has7.812665mm2 external z=0 area and is intentionally adiabatic, as are
exposed pin surfaces. This is a specified TEST boundary model, not an OEM sink
validation. Adding glass to the bath would change the physical problem and was
not used to improve a numerical gate.

For the prior821458-tet case, signed bath powers are+59.276068mW and
-2.708095mW, net56.567973mW and absolute61.984164mW; cancellation is8.738%.
A full passive bath-node P1 test-function identity closes at7e-18W:
reaction = raw bath + weighted other exterior + weighted internal jumps +
passive electrical work. Its net625.048microW discrepancy consists of
617.301microW internal jumps and7.747microW other exterior flux; electrical
work is9.1e-18W. Thus weighted internal jumps dominate the discrepancy.

Those jumps have large opposing contributions in the hot footprint and broad
remaining Kovar, with all nine seal neighborhoods represented. Absolute weighted
internal jumps total49.033mW; the largest single support face contributes0.524%
of that absolute total. The most concentrated1% of faces contributes64.6%, but
this is a diagnostic rank only. No single physical source is invented.
Local continuum flux is unknown: the identity, reaction comparison and field
changes are NOT independent local physical error or qualified recovered flux.

Median maximum bath-face edge remains413.942micrometers while normal-owner
height medians halve295.961->147.981->73.990micrometers. Apex transverse-offset/
height medians grow0.602->1.203->2.940. From the last matched-face change,
positive raw power falls70.116microW while the negative contribution changes
+56.261microW, giving a13.855microW net worsening. Per-triangle quantiles are
unweighted; actual integrals and separate cumulative-area plots use SI areas.

Actual-field figures: [signed bath maps](../fem/results/bath_spatial_diagnosis_20261030/figures/signed_raw_bath.png),
[owner sampling](../fem/results/bath_spatial_diagnosis_20261030/figures/owner_sampling.png),
[matched triangle change](../fem/results/bath_spatial_diagnosis_20261030/figures/matched_face_change.png).

## Independent manufactured operator check

Five genuine3D HeatSolver cases use an independently meshed two-ear, perforated,
Kovar-like extrusion. The exact field is
T=300+z(10+2000x-1500y)-200z^2, k17.3W/m/K, source6920W/m3; bottom
Dirichlet300K, exact top incoming Neumann flux and analytic side Dirichlet values.
The affine case is300+10z. Exact source/top/bath powers balance to roundoff.
The reference integrates each actual polygonal footprint; changing curved-skin
approximation and the deliberately different side BC are separate benchmark
geometry/model limitations. This is not the coupled device or a recovery method.

Affine relative bath error is3.8e-12. Full-refinement raw errors are
1.427310% FAIL,0.441175% PASS,0.375721% PASS against the unchanged1% target.
The finest free residual is1.68e-10W. A coarse-transverse/normal-only case gives
0.326463%, also passing. Hence the benchmark validates this operator/reference;
it does not prove universal transverse improvement, asymptotic device GCI or
actual device-field accuracy. Mean-temperature and nodal errors are archived.

The initial Elmer body-index setup failure and an original300000-tet preflight
rejection are preserved. A prospective resource-only amendment allows the
323352-tet/63036-node scalar solve under350000tets/100000nodes/300s. Equations,
geometry, loads and the1% target were unchanged.

## Controlled transverse and volume pair

The registered first level splits all six edges of every actual Kovar bath-owner
tetrahedron, propagating complete tetrahedral/physical-face stars. The second
level repeats this operation within the source8.75mm central-header circle;
that mask is fixed before either new field. No boundary triangle-only or
post-solve selective refinement is used. Both alter only Kovar and glass;
every cold, TEC, pin and other cell is byte-identical. Original points, each
material volume and every contact/exterior area are preserved to roundoff.
Actual geometry,216body/88leg graph and Elmer mapping audits pass; minSICN is
0.0423065/0.0183512, above the original0.01 bound.

Both use body-aware convex P1 guesses from the genuine675496-tet case, then
execute the unchanged coupled ThermoElectricSolver with current-matrix/current-LU
residual refinement. Bounds are3000s,4CPU,12GiB per solve; no timeout/physics
relaxation or final-field substitution occurs.

| Case | Tetrahedra | Die mean K | Terminal V | Raw bath | Solver s |
|---|---:|---:|---:|---:|---:|
| transverse1 | 784,696 | 265.616562905 | 0.551929952831 | -1.288505% FAIL | 911.084 |
| transverse2 | 1,099,293 | 265.616573870 | 0.551930033606 | -1.290712% FAIL | 999.154 |

Both complete in3 nonlinear iterations; final relative changes are8.73155e-10
and8.06024e-10. Peak RSS is5734800/6680832KiB, within12GiB. All177 current
cuts and all nonraw current, work, global/stage/free heat checks pass.
The independent raw and signed identity audits reproduce the native postprocessor.
No reaction/recovered quantity replaces the raw criterion.

Actual new figures: [signed coupled bath maps](../fem/results/bath_spatial_device_20261030/figures/coupled_signed_bath.png) and
[plateau versus geometry-only sampling](../fem/results/bath_spatial_device_20261030/figures/coupled_plateau_and_sampling.png).

The pair changes die mean+10.965microK and voltage+0.080775microV. Its raw bath
error barely changes and slightly worsens. Small output changes therefore do
not establish raw flux convergence. No GCI is fitted to this local nonuniform
pair, and no separate passing cold mesh is combined with failed bath evidence.

| Numerical item | Status | Evidence |
|---|---|---|
| Source geometry/BC/physical invariance | PASS | Actual audits, source/SIF/mesh/field hashes |
| Independent manufactured fine raw1% | PASS |0.375721%; coarse failure retained |
| Two new coupled executions | PASS | Actual native fields;911.084/999.154s |
| All177 cuts and nonraw conservation | PASS | Both new cases |
| Raw bath1% | FAIL |1.288505%,1.290712% |
| Existing independent cold5% result | PASS, preserved |4.795425% on earlier cold-normal mesh |
| Cold5% on these independent bath meshes | FAIL, expected baseline |6.476541%; cold mesh deliberately fixed |
| Combined same-mesh gate case | NOT RUN | Independent bath prerequisite unmet |
| Qualified refined combined comparator | NOT RUN | Same prerequisite |
| Full numerical/OEM release | INCOMPLETE | No waiver or assembly-validation claim |

## What the failed pair identifies and the next bounded experiment

The exact preregistered benchmark polynomial, evaluated ONLY as a geometry-based
nodal P1 interpolant on these meshes, has trace errors0.679239%,0.334147%,
0.215901% for the675496-parent and two new levels. A unit test independently
matches the closed-form transverse/normal sampling terms to a direct P1 gradient.
These values are NOT Elmer device solutions or local device-error estimates.
They show the sampling operator responds to refinement while the actual coupled
bath error plateaus; they do not alone identify the cause of the device defect.

The retained-cell inventory gives a concrete limitation: all11582parent Kovar
tetrahedra whose centroids lie above1.0mm are unchanged in both new meshes, as
are every hot Kovar/presolder contact triangle. Boundary-owner refinement has
not systematically refined the full through-thickness heat path. This motivates
an untested hypothesis about remaining volume/interface resolution; it does not
prove the upper region uniquely causes the discrepancy.

The next experiment should preregister a full1.5mm-thickness Kovar volume mask
under/around the hot footprint, with controlled interior and transverse
resolution, preserving physical volumes/BCs. If shared hot-interface edges are
split, include the conformal presolder discretization explicitly while preserving
its physical50micrometer thickness/material and the cold/electrical-TEC mesh.
Compare the raw signed integral and weighted-jump map on a controlled pair before
any combined solve. A higher-order formulation is an alternative requiring its
own independent gradient/cut/source verification, not a recovered-flux waiver.
No further large solve is attempted in this checkpoint after the failed pair.

## Evidence, reproduction and preserved report

The diagnosis/benchmark/geometry archive is
`fem/results/bath_spatial_diagnosis_20261030`; the actual coupled pair and final
comparisons are `fem/results/bath_spatial_device_20261030`. Their verifiers chain
to every earlier ledger and protect the approved Rev3 edition. See
[BATH_SPATIAL_DEVICE_REPRODUCIBILITY.md](BATH_SPATIAL_DEVICE_REPRODUCIBILITY.md).
New native T/potential fields, SIFs, timed source, libraries, initial guesses,
independent face/volume audits, explicit failures and comparisons are preserved.
The approved Rev3 public PDF remains byte-identical; this checkpoint adds no
reader-facing PDF or changes to its aesthetics, details or source provenance.
