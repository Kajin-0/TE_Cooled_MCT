# Graded TEC analog and corrected-geometry enclosure CAD — 2026-10-30

**Status: new opt-in engineering variants and a geometry-only 3D fixture.**
This is a development milestone for the **plausible synthetic** HgCdTe
reference article. It is **not OEM validation**, not a newly solved
88-leg enclosed-package Elmer field, and not numerical-release qualification.

## Audit of prior work

The source-based corrected TO-66/88-leg assembly has a 1.5 mm Kovar
header, source 15.2 mm cap outside diameter, 28/12/4 inferred thermocouple
allocation, inferred stage pellet geometry, 0.2 mm MCT die, 30 µm die
attach, four audited Cu/Au lumped wire paths. Previous G3b gas/radiosity
algorithms are reusable only after rebuilding their original obsolete
package geometry and surfaces. Previous constant-property model results
and all sealed Elmer runs are retained unchanged.

Two additions close important preparatory gaps without claiming more
physical accuracy than the available input information supports.

## A. Source-backed, temperature-dependent P/N analog grade

New `tecooledmct/graded_tec.py` reads the unmodified and source-traced
`data/g2c/zhang2025_he_40_300_v2.json`. Its source is Zhang et al.
(2025), DOI 10.1088/0256-307X/42/5/056304. Both P and N specimens have
measured/digitized `S(T),rho(T),k(T)` only over **40–300 K**. They are
**different laboratory specimens, not identified P/N elements from the
commercial three-stage TEC**.

For the synthetic reference, the reduced model uses 180–390 K nominal
domain. For **300–390 K only**, each property is extended with a
slope equal to **25% of its final measured-interval tangent**. This is
an explicit, adjustable *engineering hypothesis*, not experimental
measurements, and not evidence that real P/N pellets behave this way.
The temperatures 180–300 K use the sourced table without alteration.
Outside 180–390 K a physical-state or property evaluation fails closed.

The steady single-stage analog avoids fixed-grid quadrature across
table breakpoints: temperatures along the leg are assumed affine with
axial distance, and the 1D transport integrals are evaluated separately
on every source-table temperature interval. Two-point Gauss integration
on each interval resolves the resulting piecewise polynomial integrands
to round-off. The volume-averaged voltage and cold-side heat flux are:

```text
s = 0 cold junction → 1 hot junction;  T(s) = Tc + s(Th−Tc)
α(T) = N [S_P(T)−S_N(T)]
R(T) = N L/A [ρ_P(T)+ρ_N(T)]
K(T) = N A/L [k_P(T)+k_N(T)]

V = ∫₀¹ [I R(T)+α(T) (Th−Tc)] ds
Qavg = ∫₀¹ [I α(T)T−K(T)(Th−Tc)] ds
Qc = Qavg − ∫₀¹ (1−s)[I² R(T)+I α(T)(Th−Tc)] ds − K_bypass (Th−Tc)
Qh = Qc + I V
```

These equations reproduce the constant `S,rho,k` limit exactly and
enforce the first law `Qh−Qc=I V`, including temperature-dependent
thermopower work. **They are approximate** for a real leg because they
assume an affine axial temperature field, rather than solving the
Joule/Thomson-driven nonlinear profile. They do not include contact
resistances, internal 3D current spreading, pellet grade distributions
or thermo-mechanical effects.

**Independent axial BVP check:** The earlier bounded 1D leg solver was
run at a fixed 295 K hot-side / 250 K cold-side temperature difference,
0.1 A and the corrected source first-stage pellet geometry, using
exactly the same Zhang source curves, with 32 intervals per leg.
The graded affine-profile approximation yielded Qc=−0.24265145 W,
V=0.79740608 V; the independent non-affine BVP yielded
Qc=−0.24279309 W, V=0.79687462 V. Their differences are
**0.14164 mW** (0.0583% of BVP |Qc|) and
**0.53146 mV** (0.0667% of BVP V). Both satisfy energy conservation.
This supports the reduced integration at that boundary-value point;
it does **not** bound the error at arbitrary temperature, large
load, high current or unknown pellet grades. The negative Qc
indicates back-conduction exceeds cooling at that imposed 45 K
stage temperature difference.

The preexisting `g1_constant` path remains the default, so prior
63-point results and user-facing CLI behavior remain backward compatible.
The analog is enabled explicitly with
`--material zhang2025_analog`; it is not applied to the protected 3D
Elmer material-law files.

### Source-transport comparison at 300 K ambient, 0.15 A and 2 mW MCT load

| Scenario | G1 constant die K | Zhang-analog die K | Zhang-analog terminal V |
| --- | ---: | ---: | ---: |
| Vacuum low parasitic | 242.055 | 229.797 | 1.15825 |
| Nominal Kr 30 kPa | 243.280 | 231.202 | 1.15539 |
| High-parasitic N2 | 247.615 | 236.264 | 1.14090 |

At the nominal Kr point, the analog predicts **12.078 K lower**
die temperature than the original model, but its terminal voltage
increases from **0.84437 V** to **1.15539 V** (about +36.8%).
This large grade sensitivity **does not establish that either
variant is more accurate** for an unknown OEM assembly.

The broad 0–1 A grid contains **49 accepted / 14
failed-closed** analog cases. The corrective checkpoint below records that
all 14 rejected candidates reach the lower temperature bound and retain
unacceptable residuals. That does not prove an out-of-domain physical
solution or physical infeasibility. Their temperatures must not be
clamped, interpolated across, or treated as physically successful
operating points. The summary JSON records every failure and warns
when a grid minimum is not a qualified optimum. The plotted curves
retain gaps instead of connecting across failures.

The default constant-property baseline continues to have 63/63
accepted source-domain runs as previously reported.

## B. Corrected-source-aligned 3D cap/window geometry fixture

New `tecooledmct/corrected_enclosure.py` constructs an OCC/Gmsh
cap shell, annular roof and candidate optical window. The **only
manufacturer-documented cap input** is its 15.2 mm outside diameter.
The original corrected VIGO 1.5 mm header datum and actual internal
die/ceramic/pin/wire positions are imported from the protected source
manifest, with SHA-256 ledger verification.

Additional geometry inputs are explicit **engineering assumptions**
in `data/corrected_enclosure/geometry_hypothesis_v1.json`:

| Quantity | Used hypothesis |
| --- | ---: |
| Cap height above header | 8.60 mm |
| Cap radial wall thickness | 0.50 mm |
| Cap roof thickness | 0.45 mm |
| Window diameter | 5.90 mm |
| Window thickness | 0.45 mm |
| Roof interior Z above original header underside | 9.65 mm |
| Window underside to original MCT die top | 4.07 mm |
| Roof underside clearance to highest resolved solid | 4.06 mm |

The CAD model consists of **three distinct conformally contacting
solids** (not a remesh of the actual existing package):

| Body | Analytical and Gmsh volume |
| --- | ---: |
| Cap side shell | 188.189 mm³ |
| Cap roof | 69.353 mm³ |
| Candidate window | 12.303 mm³ |

Nine explicit physical surface groups include cavity-facing cap wall,
cavity roof, cavity window, cap-header foot, shell/roof interface and
roof/window interface. Native 3D physical volume IDs **7301–7303**
and surface IDs **7401–7409** are reserved to avoid collisions with
existing corrected Elmer body and boundary tags. The standalone
native mesh has **8,143 tetrahedra**.

The independent audit verifies the analytic volume and interface-area
identities, source cap outside diameter, header datum, cap clearance
to original ceramic, die, pins and routed Cu/Au wires, 3D CAD
incidence, and presence of all required boundary groups.

**Crucial scope limit:** `corrected_cap_window.step` and
`cap_window_only.msh` are a separately meshed geometry fixture.
They do not yet comprise a single conformal complete package model.
The gas interior is not meshed, no corrected optical through-window
transmission is computed, and no new enclosed-package coupled
thermal field has been solved. Neither thermal-contact conditions
nor surface-to-surface view factors are yet assembled from this
new geometry. The old G3b view-factor geometry is not silently reused.

## Reproduce

```bash
# Recompute opt-in source analog without changing prior constant baseline
./fem/run.sh python -m tecooledmct.integrated_reference \
  --material zhang2025_analog --out data/integrated_graded_20261030
./fem/run.sh python -m tecooledmct.integrated_reference_figures \
  --from-dir data/integrated_graded_20261030

# Choose a NEW output directory: builder refuses overwrites
./fem/run.sh python -m tecooledmct.corrected_enclosure \
  --out outputs/cap-window-reproduction --mesh

./fem/run.sh python -m pytest -q tests/test_graded_tec.py \
  tests/test_corrected_enclosure.py tests/test_integrated_reference.py
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python fem/archive_bath_spatial_device.py --verify
```

Artifacts: `data/integrated_graded_20261030` includes source provenance,
full scenario heat budgets, rejected-case reasons, sensitivity CSV, sweep CSV
and PNG figures. The cap/window fixture is under
`fem/results/corrected_enclosure_geometry_20261030` with native STEP,
mesh and `geometry_audit.json`.

## Next milestones and engineering gates

1. Integrate the **new** cap/window BREP into a conformal full
   package mesh without changing the protected earlier geometry
   artifacts. Keep steel/window material domains and actual cavity
   interface surfaces auditably distinct.
2. Compute a new geometry-specific gas and diffuse-gray radiation
   operator with closed-surface visibility, reciprocal/closed
   view factors, gas accommodation and exact surface energy balance.
   Avoid old G3b geometry and unphysical radiation across opaque solids.
3. Implement a bounded analog P/N transport option in the *full
   Elmer solve*, including coupled Seebeck/Joule/Peltier/Thomson
   source semantics, and independently verify the 1D affine
   approximation against bounded leg BVP results.
4. Run paired physical-mechanism tests (solid baseline, gas only,
   radiation only, Au/Cu parasitics, heat sink), with proper hot
   spreading and mesh sensitivity, then produce updated engineering
   heat budgets and temperature-field visualizations.
5. OEM curves remain optional plausibility checks. No claim of
   numerical release while original raw bath 1% and cold-face
   5% criteria remain unresolved. Historical FEM sources/fields,
   old failed gates and approved Rev3 are preserved.

## Small corrective checkpoint — 2026-10-30

This increment was executed through the existing `sim:0.0` Codex session.
It preserves the original source tables, standalone CAD/mesh archive,
previous scenario artifacts and approved Rev2/Rev3. It adds no full-device
3D solve and makes no OEM identification or numerical-release claim.

### Active-law consistency and geometry guards

`graded_tec.props()` now derives `sigma = 1/rho` after the assumed
continuation, and returns `thomson_v_k = T*dS/dT` for the actual active
law. Interior measured-table knots use the source's **right derivative**.
At exactly **300 K**, use the final measured segment's **left derivative**;
at temperatures strictly above 300 K use 0.25 times that slope. At exactly
**390 K**, use the continuation's **left derivative**. No two-sided
derivative is asserted at 300 K. Evaluations outside 180–390 K fail closed.
The measured 40–300 K table is unchanged; the selected analog domain remains
180–390 K. Tests cover scalar/vector evaluation, reciprocal identity,
one-sided finite differences and strict domain boundaries. `S/rho/k` used by
the existing stage calculations are unchanged; all 49 prior accepted
analog points retain temperature, voltage and stage heat results within
1e-9 K / 1e-11 V or W regression tolerances.

The enclosure builder rejects missing, nonnumeric, Boolean, nonfinite,
zero or negative dimensions before constructing CAD. It checks
`0 < window_radius < inner_cap_radius < outer_cap_radius`, a positive
cavity and solid volumes, roof clearance to internals and pins, and wire
clearance including wire radius. This fixture still requires equal window
and roof thickness; unequal thickness needs a separately designed seat.
No protected geometry archive was rebuilt.

### Rejected-current diagnostics

New scenario output is in
`data/graded_corrective_20261030/scenarios/summary.json`; prior
`data/integrated_graded_20261030` files are retained. Each rejected case
records its scenario, last candidate temperatures, four physical node
residuals in W, separate hot-sink residual in K, optimizer-scaled residuals,
optimizer success/status/message/evaluation count/active mask, model and
measured P/N domains, active bounds and an explicit failure classification.
Unavailable values after an evaluation error are `null`, never invented.

All 14 actual rejected grid cases classify as
`active_bound_residual_failure`: optimizer termination reports success,
but the cold ceramic is at 180.000001 K and physical residuals fail the
unchanged acceptance gate. For example, nominal Kr at 0.65 A has a maximum
node residual **4.582915 mW**, far above the 1e-8 W gate. Its stored
temperatures are **rejected candidates**, not operating predictions.
An active bound does not establish that a solution exists below the bound.
Optimizer failure and material/evaluation failure are separately tested.
Failed cases remain absent from accepted sweep CSV rows; existing plots
retain gaps and the optimum warnings remain intact.

The optimizer's last residual row remains the hot-sink temperature residual
divided by 2, as before. Diagnostics label this scaling explicitly rather
than interpreting that row as a physical W balance. Accepted calculations
and their historical residual gate have not been changed.

### Broader independent nonlinear leg comparison

`tecooledmct.graded_tec_checks` compares the affine stage against the
independent conservative `oem_phase_a.bounded_leg` solver, using both
16 and 32 intervals per P/N leg and corrected stage dimensions. Stage
indices 0/1/2 run from hot to cold. All boundary and solved interior
temperatures in these six cases lie **strictly inside 40–300 K**.
These are approximation checks using the same research-specimen transport,
not measurements of the synthetic device.

| Stage | Th / Tc (K) | I (A) | abs Qc error (mW) | relative Qc error (%) | abs V error (mV) | relative V error (%) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 295 / 250 | 0.10 | 0.141640 | 0.058338 | 0.531456 | 0.066693 |
| 0 | 295 / 285 | 0.15 | 0.332227 | 0.101261 | 1.825869 | 0.287575 |
| 1 | 280 / 250 | 0.15 | 0.005985 | 0.020888 | 0.016015 | 0.005634 |
| 2 | 250 / 230 | 0.15 | 0.002096 | 0.021038 | 0.002052 | 0.003340 |
| 2 | 230 / 190 | 0.50 | 0.115150 | 0.551612 | 0.235985 | 0.166319 |
| 0 | 260 / 240 | 0.70 | 7.986864 | 0.972654 | 147.220545 | 6.481337 |

Errors are `abs(affine - BVP32)`; relative errors divide by `abs(BVP32)`.
Signed values, BVP results, source provenance, local conservation and
16-to-32 changes are in
`data/graded_corrective_20261030/bvp_comparison.json`.
At 0.70 A, the nonlinear leg interior reaches **273.178856 K**, above both
boundary temperatures; the affine profile cannot represent this Joule-driven
curvature. The 16-to-32 changes there are 0.026965 mW and 0.517298 mV,
considerably smaller than the affine discrepancies. This is evidence of a
high-current approximation limitation, not a rigorous continuum error bound.
Relative cooling errors also become unstable near zero cooling. No global
error bound or extrapolation to untested operating points is established.

The assumed **300–390 K** law is tested for internal consistency and guards
only. This measured-domain BVP study does **not validate** that continuation.
For high-current quantitative budgets, prefer the bounded nonlinear leg
reduction in a future scoped checkpoint before spending resources on a
new full-package FEM solve. The immediate scope remains a plausible
synthetic reference, with OEM comparison optional.

Reproduce into new/local output locations:

```bash
./fem/run.sh python -m tecooledmct.graded_tec_checks \
  --out outputs/graded-corrective/bvp_comparison.json
./fem/run.sh python -m tecooledmct.integrated_reference \
  --material zhang2025_analog --out outputs/graded-corrective/scenarios
./fem/run.sh python -m pytest -q tests/test_graded_tec.py \
  tests/test_corrected_enclosure.py tests/test_integrated_reference.py
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q --ignore=outputs
./fem/run.sh python fem/archive_bath_spatial_device.py --verify
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/graded-corrective/cli
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/graded-corrective/geometry
```

Focused verification: **98 tests passed**, including the native standalone
Gmsh fixture, six nonlinear BVP comparisons and diagnostic failure branches.
Full opt-in regression: **253 passed** in 339.94 s, including genuine Elmer
smoke checks (14 third-party matplotlib/pyparsing deprecation warnings).
The complete archive verifier passed, preserving all historical failed gates
and approved Rev3. Legacy CLI and geometry-demo commands also passed.
