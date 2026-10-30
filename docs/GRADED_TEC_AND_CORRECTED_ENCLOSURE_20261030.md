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

The broad 0–1 A grid contains **49 accepted / 14 deliberately
failed-closed** analog cases. Several high-current states are below
the deliberately restricted 180 K lower modeling boundary or are
infeasible under the restricted model. Their temperatures must not be
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
