# P/N transport and corrected-source enclosure exchange

This guide covers the current opt-in implementations and their limits. The
[package guide](INTEGRATED_REFERENCE_THERMAL_20261030.md) defines the five-node
balances, scenarios, sources/assumptions and CLI. The objective is a plausible
synthetic reference device; numerical checks do not establish device accuracy.

## Coverage and implementation choices

| Capability | Module | Evidence / scope |
| --- | --- | --- |
| Original affine-T analog | `graded_tec.py` | Preserved model identifier and 49/63 accepted historical snapshot |
| Nonlinear bounded legs | `nonlinear_tec.py` | Direct 32-interval banded Newton, independent old BVP comparisons, 16/32/64 checks |
| Independent reference | Unmodified `oem_phase_a.bounded_leg` | Conservative midpoint equations solved by bounded least-squares; not an OEM fit |
| Actual cap/window fixture | `corrected_enclosure.py` | Protected STEP + 8,143-tet standalone mesh, three domains and nine physical groups |
| Native source-face audit | `exchange_geometry.py` | Exact package/fixture hashes, ownership, areas, interface incidence and positive cap tets |
| Preliminary exchange | `corrected_exchange.py` | Closed analytic cylinder with a filled stepped-core proxy, 14 surfaces / 8 effective nodes |
| Package coupling | `integrated_reference.py` | Opt-in nonlinear transport and exchange; no new enclosed-package 3D field |

## Material provenance and active-law semantics

The unmodified `data/g2c/zhang2025_he_40_300_v2.json` contains source-traced
S(T), rho(T), k(T) for different P/N research specimens from Zhang et al.
(2025), DOI 10.1088/0256-307X/42/5/056304. Their complete source domain is
40–300 K. These are analogs, not an identified commercial matched pair.

The selected synthetic model uses 180–390 K. Between 180 and 300 K it
retains the measured-table interpolation. Above 300 K, each property uses
**0.25 times the final measured-interval tangent**, through 390 K. This is a
bounded engineering hypothesis, not measured transport. Every nonlinear
interior node and property evaluation must respect the active domain;
Joule overshoot may use the assumed law even with both endpoints below 300 K.

| Quantity | Units | Definition / one-sided rule |
| --- | --- | --- |
| S | V/K | Piecewise source interpolation / explicit continuation; P positive, N negative |
| rho | ohm m | Positive active resistivity |
| sigma | S/m | Identically 1/rho after continuation |
| k | W/(m K) | Positive active conductivity |
| Thomson coefficient | V/K | T*dS/dT of the active law |
| Derivative at interior source knots | Property/K | Right derivative |
| At exactly 300 K | Property/K | Final measured segment left derivative; no two-sided derivative asserted |
| Strictly above 300 K / exactly 390 K | Property/K | Quarter tangent / its left limit at 390 K |

Out-of-domain, nonfinite and nonpassive evaluations fail closed. Positive
material scaling factors apply to the laws and their derivatives together.
The recent consistency correction leaves all stage S/rho/k inputs exactly
unchanged. Snapshot comparisons use 1e-7 K and 1e-9 V/W numerical tolerances
across optimizer/BLAS versions; these are not physical acceptance gates.

## Nonlinear leg equations and conservative discretization

Use z from hot to cold, length L in m, current density j in A/m²:

```text
q = S(T)*T*j - k(T)*dT/dz                         [W/m²]
dq/dz = j*(rho(T)*j + S(T)*dT/dz)                 [W/m³]
```

At each segment midpoint, dx=L/n and dT=T_right-T_left:

```text
v_s = j*rho(T_mid)*dx + S(T_mid)*dT               [V]
w_s = j*v_s                                     [W/m²]
r_i = q_(i+1/2)-q_(i-1/2) - (w_left+w_right)/2   [W/m²]
q_hot = q_first-w_first/2; q_cold=q_last+w_last/2
```

The direct implementation computes an analytic tridiagonal Jacobian of these
residuals, solves with a banded linear solve, then uses a bounded residual-
decreasing line search. It never clips an accepted profile or substitutes an
affine profile on failure. No separate Thomson source is added: variable
thermopower work is already present in the conservative flux/work equations.

For N pairs with leg area A, jN=I/A and jP=-I/A:

```text
Qc = -N*A*(q_cold_P+q_cold_N) - K_bypass*(Th-Tc)
Qh = -N*A*(q_hot_P+q_hot_N)   - K_bypass*(Th-Tc)
V  = N*(v_N-v_P)
```

Both endpoint heats are independently computed; `Qh-Qc=I*V` is audited to
1e-9 W. Inner maximum control-volume residual is <=1e-4 W/m², and total
endpoint/work mismatch <=1e-6 W/m². The extra integral check prevents small
per-cell errors accumulating into a false zero-current stage-energy failure.
The initial unaccepted development failures are retained separately in the
new evidence folder, not reclassified as physical infeasibility.

Each package solve owns an exact-key stage cache. Keys include boundary
T, current, dimensions and all transport/bypass multipliers. No rounding,
persistent stale lookup table or surrogate interpolation is used. Repeated
stages under finite-difference package Jacobians can therefore reuse exact
results. A constant-law package result is used only as an initial iterate;
the accepted result still passes the full nonlinear equations and gates.

## Transport accuracy, cost and unresolved states

Versioned evidence: `data/nonlinear_exchange_20261030/transport/comparison.json`.
Ten boundary-value points span all three stage geometries, 0.1–0.9 A and
16/32/64 intervals. Eight cases have all reference temperatures strictly
40<T<300 K; the other two are labeled **assumed-continuation consistency
checks only**. They do not validate the extension experimentally.

| Stage; Th/Tc K; I A | Nonlinear32 vs reference64 abs Qc | Relative Qc | Abs V | Relative V |
| --- | ---: | ---: | ---: | ---: |
| 0; 295/250; .1 | 0.589 µW | 0.000243% | 0.436 µV | 0.0000548% |
| 0; 260/240; .7 | 6.762 µW | 0.000823% | 0.129404 mV | 0.00570% |
| 0; 230/210; .9 | 15.398 µW | 0.00246% | 0.199649 mV | 0.00823% |
| 2; 230/190; .5 | 0.871 µW | 0.00417% | 0.277 µV | 0.000195% |

Relative errors divide by absolute BVP64 values; near zero cooling, absolute
errors matter more. All points and signed reference results are in JSON.
At the earlier 0.7 A test, affine-vs-BVP32 voltage error was 147.221 mV
(6.48%); direct nonlinear32 reduces it to 0.129404 mV vsBVP64. Identical-grid
new/old implementations agree within tested 2 nW / 20 nV bounds. This verifies
implementation and discrete refinement, not material-grade/device accuracy.

On this pinned execution the median independent-reference64/direct-Newton64
wall-time ratio was about 24; this is a measured timing, not a portable speed
guarantee. Across accepted old-reservoir package points, median inner-stage
compute time was 0.52 s, with 64.5 stage solves and 66 exact cache hits. Timings
exclude some outer/initial-guess overhead. At nominal 0.9 A, nonlinear32→64
changes die T by 0.000350 K and terminal V by 0.1643 mV. Knot crossings can
produce nonmonotonic small changes; no GCI or continuum error bound is claimed.

The final old-reservoir nonlinear sweep accepts 50/63 cases and retains 13
rejections; the proxy sweep accepts 52/63 and retains 11. Some are lower-bound
residual failures; the high-parasitic 1 A case rejects a nonlinear leg profile.
A failure at an optimizer candidate does not prove that no physical root exists.
No rejected candidate is a measured or accepted operating point, and plots do
not bridge failures. Previous affine data and all original FEM failures remain.

## Corrected-source native geometry audit

The immutable source package has 216 material bodies and 88 legs. The standalone
cap/window BREP uses documented 15.2 mm cap OD and 1.5 mm header datum;
height 8.6 mm, wall 0.5 mm, roof/window 0.45 mm and window OD 5.9 mm are assumed.
The builder rejects nonfinite/nonpositive dimensions, impossible voids and
collisions, including wire radius. Window thickness currently equals roof
thickness; a different seat needs new geometry.

`data/corrected_enclosure/exchange_sources_v1.json` pins the existing STEP,
MSH and geometry-audit SHA-256 values. Package manifest/mesh/wires are checked
against their protected archive ledger. The new audit independently verifies:

- all 8,143 native cap tets have positive signed volumes;
- physical volumes 7301–7303, all nine face groups 7401–7409, unique exterior
  ownership, and 156/100 shared shell-roof/roof-window interface triangles;
- facet areas against BREP areas, with tessellation errors reported;
- unique ownership of every declared native package exterior triangle and
  actual exposed top facets on ceramic bodies 1–4 and MCT body 303.

Native exposed top areas are 29.964,16.1295,8.9375,4.760 and0.955 mm².
They are recorded independently of the proxy areas below. This is not a
conformal cap-to-package merge, and no gas volume is meshed.

## Preliminary closed exchange proxy

The cavity is an analytic inner cylinder, radius 7.1 mm, z=1.5..9.65 mm,
with the current candidate window. A filled stepped opaque core uses corrected
ceramic and die widths/top-plane heights. It **fills actual interleg voids**,
omits pin/wire/metallization occlusion and replaces exposed native surfaces.
Therefore its areas differ materially from the native areas above. It is a
bounded engineering closure, not an actual-face 88-leg visibility solution.

Fourteen surface groups comprise five upward top bands, five four-sided
vertical groups, header floor, cap wall, cap roof and window. Their temperatures
map conservatively to five package nodes and three prescribed reservoirs.
Vertical core groups use the mean of neighboring node temperatures; this is
another explicit reduction. All surfaces are gray and opaque, including the
window. Optical transmission and optical absorbed loads remain separate.

Deterministic scrambled Sobol area/cosine-hemisphere rays hit the **first**
opaque proxy surface. Closed rays establish row closure; analytic blocked
pairs (parallel upward tops, coplanar roof/window, convex self-view) remain zero.
The concave cap wall can see itself. Raw exchange areas are symmetrized, then
symmetrically balanced to satisfy reciprocity and closure while retaining pairs
unseen in both directions as zero. Raw and corrected matrices are both saved.

```text
A_i F_ij = A_j F_ji                    [m²]     sum_j F_ij = 1
J_i = epsilon_i*sigma*T_i^4 + (1-epsilon_i)*sum_j F_ij*J_j  [W/m²]
Qrad_into_i = A_i*(sum_j F_ij*J_j-J_i) [W]
Ggas_ij = k(T_mean)*W_ij/(mean_chord_ij+2*jump_ij) [W/K]
Qgas_into_i = sum_j Ggas_ij*(T_j-T_i)  [W]
```

W=A_iF_ij. Mean chords are symmetric area-weighted ray lengths. Gas k is the
registered N2/Ar/Kr table, 200–400 K; 180–200 K uses a flagged T^0.75 engineering
extension. The Eucken/jump accommodation closure is inherited as an algorithm,
**not old G3b geometry**. A chord graph is not an accurate solution of continuum
diffusion or rarefied-gas transport; accommodation and model-form error remain
unqualified. It is passive, reciprocal, exactly zero in vacuum and linear in
pressure in the free-molecular limiting check. High-pressure conductances recover
the stated Fourier-network limit. Convection, mixtures and Xe are absent.

## Ray refinement and energy checks

At fixed node temperatures 300/270/240/220/221 K and 300 K reservoirs:

| Rays per surface | Largest absolute F correction | Gas into die mW | Radiation into die mW |
| --- | ---: | ---: | ---: |
| 4,096 | .07335 | .136161 | .289628 |
| 16,384 | .05292 | .139590 | .293933 |
| 65,536 | .04043 | .140812 | .293511 |

Last-level die changes are 0.88% gas and 0.14% radiation relative to the preceding
level. The remaining 4.04-percentage-point maximum F correction is visible,
not hidden by energy conservation. This is not a qualified spatial view-factor
solution, statistical confidence interval or native-cavity accuracy estimate.
Surface and node radiation/gas balances are audited below 1e-10 W. Independent
two-plate gray radiation, equal-T, vacuum, zero-emissivity, low-pressure scaling,
high-pressure Fourier-network, invalid-input, corrupted-payload/source-hash and
blocked-ray tests accompany package hot/cold/reservoir conservation checks.

## Reproduce, inspect and continue

| Verification layer | Actual result | What it establishes |
| --- | --- | --- |
| Focused transport/exchange/compatibility suite | 131 passed | Analytic limits, independent BVP and ray/heat/domain/negative controls |
| Full pinned opt-in regression | 286 passed in 340.38 s; 14 third-party deprecation warnings | Existing genuine Elmer smoke plus all current tests |
| Full archive verifier | Passed | Historical source/field ledgers, original failures and approved Rev3 preserved |
| Legacy CLI and geometry demo | Passed | Existing demonstration workflows remain runnable |
| Documentation links and new figures | Checked | Current local links resolve; figures retain failed-interval gaps |
| Current proxy/package global balance | Maximum 1.41e-11 W over accepted grid cases | Conservative reduced implementation, not device accuracy |
| Actual native full-cavity visibility / gas diffusion | Not implemented | Filled-core chord model remains a preliminary proxy |
| Experiment / OEM accuracy / numerical release | Not established | Original material/model uncertainty and raw-flux requirements remain |

Use the exact commands in the [package guide](INTEGRATED_REFERENCE_THERMAL_20261030.md).
New evidence is under `data/nonlinear_exchange_20261030`; old affine,
constant, corrective-checkpoint and sealed FEM data are untouched. Full verification:

```bash
./fem/run.sh python -m pytest -q tests/test_nonlinear_tec.py   tests/test_corrected_exchange.py tests/test_graded_tec.py   tests/test_corrected_enclosure.py tests/test_integrated_reference.py
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q --ignore=outputs
./fem/run.sh python fem/archive_bath_spatial_device.py --verify
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/current-model/legacy-cli
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/current-model/legacy-geometry
```

Next priorities are native-surface exchange without filled interstage voids,
paired mechanism tests and contact/bypass/reservoir sensitivity. Keep improving
these current guides and README with each increment. Preserve all frozen source,
actual fields, original raw 1% bath / 5% interface failures and approved Rev2/Rev3;
no reduced-model milestone constitutes numerical-release or OEM validation.
