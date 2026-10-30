# OEM-first physical-validation track (prospective, 2026-10-30)

## Decision and scope

Physical predictive accuracy now has priority over additional expensive bath-gradient
refinement. This is a **prospective prioritization decision**. Historical archived
bath and cold-face gates, failed results, raw fields, source snapshots, Revision 2
and the approved 15-page Revision 3 REVIEW DRAFT retain their original status and
are not reinterpreted or modified. The engineering numerical-release criteria in
`docs/REPORT_REVISION3_REVIEW_CRITERIA.md` remain in force for a numerical release;
a separate scientific screening calculation does not bypass them.

The immediate question is whether this model can predict *measured* TEC lift
and terminal voltage over multiple currents and thermal loads, not whether a
synthetic-geometry 300 K / 0.1 A bath-gradient error can be reduced another
fraction of one percentage point.

## Evidence baseline and strict distinctions

- The VIGO ZTM-TO66-Z030 Rev9 TO-66 source housing and independent TEC
  Microsystems 3MC04-044-05 candidate form a hypothetical reference assembly.
  The 28/12/4 split, leg heights, routing, P/N grades and contacts are inferred.
- The historical G2d actual 88-leg constant-law FEM at 0.2 A, nominal 300 K,
  vacuum, zero load predicts 65.854321 K lift and 1.074811711 V versus
  digitized OEM 54.967287 K and 0.869116 V. Lift residual +10.887033 K;
  voltage residual +0.205696 V. This predates corrected package geometry and
  must not be represented as a Rev3 validation discrepancy.
- G2d's calibration-only reduced network has Jacobian rank 8/9, including an
  exact bulk/geometry scaling degeneracy. Its fit reaches a conductivity bound
  and fails to uniquely identify a manufacturer's leg grade or dimensions.
- A source-backed Zhang et al. (2025) P/N transport-profile dataset covers
  40–300 K, but its P and N legs are separately characterized specimens and
  **not a matched commercial TEC module**. Its published 300 K upper endpoint
  does not license evaluation of actual temperatures above 300 K.
- The nominal 300 K OEM chart is digitized from a literal 27 C panel, adding
  a 0.15 K bath-reference caveat. Chart reading bounds are not manufacturer
  measurement uncertainties.
- The corrected source-geometry coupled FEM remains solid-only, fixed
  300 K Kovar underside, 0.1 A and 2 mW detector heating, Cu/Au links OFF
  for the principal spatial studies. It does not model gas, cap, window,
  carrier transport or optical signal transmission.

## Phase A0: independent bounded material/transport screening

The new **opt-in** `tecooledmct/oem_phase_a.py` models each P and N thermoelectric
leg by a one-dimensional conservative, temperature-dependent finite-volume
boundary-value problem. Nodal unknowns are constrained to the actual 40–300 K
intersection of measured `S(T)`, `rho(T)`, and `k(T)`. Every nonlinear
material evaluation is in-domain. No extrapolation, coefficient clamping,
source-table edits or post hoc correction of archived Elmer fields is permitted.

The model aggregates 28/12/4 inferred isothermal stages with schematic Cu
resistance and thermal routing already registered for G2d; it omits spreading,
real interface contacts, package gas/radiation and module-specific grades.
The reported lift and voltage are **screening predictions**, never FEM fields,
OEM validation, or fitted detector results.

Acceptance for the *solver verification* portion:
1. Independent constant-property analytic leg solution, voltage identity and
   nodal conservation must pass, including at a source-domain boundary.
2. All accepted nodal and midpoint property evaluations remain inside the
   source interval; invalid boundary inputs fail closed.
3. Compare at least two axial discretizations for representative 295 K and
   300 K screening points; record whether each run actually converges.
4. Every accepted stage and full-cascade heat/electrical work balance must be
   checked. A source-coverage failure remains FAILED, not a new data point.
5. Do **not** use the historical calibration/validation_holdout values to
   tune this prospective solver's coefficients, stage topology, tolerances,
   discretization, or acceptance limits.

Reproduce the computational screen (no new Elmer runs):

```bash
./fem/run.sh python -m tecooledmct.oem_phase_a --out outputs/oem-phase-a
./fem/run.sh python -m pytest -q tests/test_oem_phase_a.py
```

The `outputs/oem-phase-a` generated JSON is a local diagnostic, not a sealed
historical archive. Any 300 K run that converges is still *unqualified* for OEM
prediction because the assumed P/N material grades and leg geometry are not
manufacturer identified.

## Phase A1: real OEM performance cross-validation

Maintain separate reserved calibration and withheld evaluation sets, preserving
the original 0.2/0.6/1.0 A versus 0.1/0.4/0.8 A split. Do not reuse the
already examined withheld data as an independent blind test for a newly tuned
model. Additional truly independent OEM/experiment measurements are necessary
for an honest prospective validation claim.

Required observables are `T_hot, T_cold, I, V, Q_c`, ambient gas/pressure,
mounting and contact condition, plus measured uncertainty. Avoid equating the
published 2.9 ohm **AC** resistance with `V/I` under a thermoelectric gradient.
Obtain additional temperatures and loads where possible and hold out entire
device conditions rather than isolated plot points.

Proposed *engineering design targets*, NOT attained:
- Mean detector or cooler cold-side temperature residual ≤2 K over qualified
  operating conditions, with maximum error also reported.
- Terminal voltage residual ≤5% over the matched current/load family.
- Cooling capacity residual ≤10% at comparable conditions.
- No numerical conservation regressions; source coverage and measurement
  uncertainty explicitly recorded.

Calibration without independent geometry/grade/contact evidence is an
**effective model**, not proof of the true internal construction.

## Phase A2: uncertainty and identifiability

Use the existing inexpensive G2d network for priors/sensitivity. Treat
rank deficiency as structural: reduce aliased degrees of freedom, or request
independent dimensions and transport measurements. Report scenario envelopes
as assumption-conditioned, not empirical 95% confidence intervals.
Prioritize actual stage pellet aspect ratios, P/N `S(T),rho(T),k(T)`,
electrical contact resistance, TEC ceramic-to-header joint, cold-stage
thermistor correspondence, and independently monitored heat sinking.

## Phase B/C: physical packaging and MCT system physics

Reintroduce 3D where it adds distinctive information: header spreading,
resolved joint geometry, bond-wire parasitics, sealed-cavity heat loads,
local detector temperature gradients. The manufacturer-supported gas,
cap/window, anti-convection shield, heat-sink interface and optical source
are **separate physics increments** subject to verified geometry and source
registry updates. No old-geometry cavity operator reuse.

For later detector performance, add `E_g(x,T)`, `R(T,V)`, radiation/window
transmission, responsivity, NEP/noise spectral density and `D*(lambda,T)`
only with appropriate material/device evidence. Temperature prediction alone
does not qualify a photodetector electro-optical digital twin.

## Explicit stop conditions

Do not launch further million-element bath campaigns by default. The recorded
full-thickness Kovar hypothesis is available as a bounded separate numerical
experiment if a future design decision specifically needs local bath flux.
Do not change raw1% or cold5% archived criteria, their failures, the approved
Rev3 PDF, pinned solver installation, other repositories or existing tmux
sessions. In particular, do not import or modify LSDDTS.

The next substantial milestone is not a larger mesh; it is a scientifically
supported, quantitatively scored, **matched-material and matched-boundary**
TEC benchmark against independent device evidence.

## Completed bounded material screening (first prospective step, 2026-10-30)

`tecooledmct/oem_phase_a.py` provides an opt-in, **non-FEM**, conservative 1D
finite-volume P/N-leg cascade with bound-constrained nonlinear material evaluations.
The code uses the *same unmodified* source-traced Zhang 2025 40–300 K material
profile and assumed G2d stage geometry. All material evaluations remain inside
measured coverage; no extrapolation or temperature clamping is used.

Reproduce with:

```bash
./fem/run.sh python -m tecooledmct.oem_phase_a --out outputs/oem-phase-a
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q tests/test_oem_phase_a.py
```

| Hot-side K | I A | Load W | Axial intervals | Predicted lift K | Predicted terminal V |
|---:|---:|---:|---:|---:|---:|
| 295 | 0.1 | 0 | 16 | 49.284480 | 0.7922663 |
| 295 | 0.1 | 0 | 32 | 49.284604 | 0.7922678 |
| 300 | 0.1 | 0 | 16 | 50.822869 | 0.8173031 |
| 300 | 0.1 | 0 | 32 | 50.823022 | 0.8173050 |
| 300 | 0.2 | 0 | 16 | 79.878848 | 1.4316793 |
| 300 | 0.2 | 0 | 32 | 79.879548 | 1.4316914 |

These are **screening calculations**, not a fitted/commercial TEC prediction.
Small axial discretization changes do not demonstrate independent material-grade
accuracy or overall engineering uncertainty. The model retains hypothetical
28/12/4 staging, simplified copper routing and ideal contacts, with no package
spreading. The original 300 K OEM 0.2 A datum (54.967 K / 0.8691 V) therefore
must **not** be represented as validated by this source-profile calculation;
there is a large discrepancy and the P/N literature grades are not OEM matched.
All published G2d curve data and earlier archived Elmer results are preserved.
