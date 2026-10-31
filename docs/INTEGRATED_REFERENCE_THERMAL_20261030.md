# Integrated synthetic-reference thermal model

Internal implementation/source notes. The single current scientific document is the
[Revision 3 master](../reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf).
The authoritative [current project contract](../AGENTS.md) defines read-first order,
execution ownership and next milestones. The live master is continuously updated;
sealed historical PDF bytes, numerical archives and original gates remain immutable.

This is the current operating guide for the corrected-geometry **five-node
reduced model**. It complements archived genuine Elmer fields; it does not
produce a new enclosed-package 3D field or identify an OEM assembly.
[Controlling policy](PLAUSIBLE_REFERENCE_MODEL_POLICY_20261030.md).

## Model and implementation map

Unknown temperatures are `hot_ceramic`, `stage1`, `stage2`, `cold_ceramic`,
`MCT_die`, all in K. Stage numbering runs hot to cold. A common prescribed
current flows through 28/12/4 inferred series thermocouples, 88 legs total.

| Module / option | Implemented calculation | Domain / boundary |
| --- | --- | --- |
| `integrated_reference.geometry()` | Reads protected manifest/wire routes; checks SHA-256 | Corrected 216-body synthetic construction |
| `g1_constant` (default) | Constant P/N TEC equations | Verification proxies, not measured commercial transport |
| `zhang2025_analog` | Source-knot integration with affine axial T | 180–390 K; assumed continuation above 300 K |
| `zhang2025_nonlinear` | Conservative nonlinear 1D profiles, banded Newton, exact per-solve cache | Every evaluated leg temperature 180–390 K; no rounded/interpolated surrogate |
| Default reservoir exchange | Effective area/gap gas and gray reservoir radiation | Old reduced-budget compatibility; no spatial visibility |
| Optional `--exchange` JSON | Corrected-source cap/window plus closed stepped-core proxy | Preliminary geometry-derived exchange, not native full-package visibility |
| Cu/Au paths | Corrected 1D routes, conduction and Cu Joule | Cu reaches **hot** pads; Au reaches detector |
| Die and sink | Attach conductance, prescribed bias/absorbed heat, effective hot-side sink R | Lumped die; ambient cap/window/pin/header reservoirs |

The [transport/enclosure guide](GRADED_TEC_AND_CORRECTED_ENCLOSURE_20261030.md)
derives the new operators and their verification. The original affine and
constant identifiers retain their previous behavior when no operator is supplied.

## Sources, assumptions and scenario ranges

| Input | Category and nominal value | Alternatives / limit |
| --- | --- | --- |
| VIGO housing reference | Documented two-ear flange and nine-pin source profile; cap OD 15.2 mm, header 1.5 mm | Not proof of a manufactured housing-plus-TEC assembly |
| TEC outer envelope | Independently selected TEC Microsystems reference, 6.4 / 2.4 mm hot/cold widths, 3.8 mm stack | Internals are inferred, not vendor artwork |
| Stage construction | Inferred 28/12/4 couples; leg lengths 1.07/0.82/0.64 mm, area 0.16 mm² | Fixed geometry here; contact/spreading and buried-route losses remain simplified |
| P/N properties | Zhang2025 dissimilar research specimens, sourced 40–300 K | Chosen active interval 180–390 K; explicit quarter-tangent continuation above 300 K |
| Stage bypass | Assumed zero by default; nonnegative per-stage W/K input | Not a qualified model of actual ceramic/Cu shunts |
| Cap/window | OD source; height 8.6 mm, wall 0.5 mm, roof/window 0.45 mm, window OD 5.9 mm assumed | Full declared geometric ranges in corrected-enclosure registry |
| Gas | Registered N2/Ar/Kr k(T), 200–400 K; 180–200 K assumed T^0.75 extension | Vacuum–101325 Pa scenarios; accommodation 0.8 assumed; no Xe/mixture accuracy claim |
| Emissivity | Nominal cap 0.2, effective ceramic/core 0.8, opaque gray window 0.1 | Low/high cap 0.08/0.65, window 0.05/0.6; not optical transmission |
| Die attach | Assumed 30 µm, 1 mm², k=1 W/(m K), R=30 K/W | k sweep 0.5–3 W/(m K) |
| Loads | Scenario bias 1.5 mW + absorbed 0.5 mW | Bias sweep 0.5–5 mW; no detector R(T,V) or optical transport calculation |
| Hot sink | Effective hot-ceramic-to-ambient R=2 K/W | 0.5–5 K/W; not resolved Kovar/joint spreading |
| Wires | Corrected archived endpoints, G=kA/L, R=rho L/A | Au conductance ×0.75–1.25; Cu Joule split equally at endpoints |

Material multipliers span Seebeck ×0.9–1.1 and resistivity/conductivity ×0.8–1.2.
These engineering ranges are selectable hypotheses, not statistical confidence
intervals. Unknown contacts remain ideal; neither transport refinement nor
conservation makes the material grade or package assumptions experimentally valid.

## Governing balances and units

For constant stage properties, alpha has units V/K, R has ohm, K has W/K:

```text
Qc = alpha*I*Tc - I²R/2 - K*(Th-Tc)             [W]
Qh = alpha*I*Th + I²R/2 - K*(Th-Tc)             [W]
V  = I*R + alpha*(Th-Tc)                       [V]
Qh - Qc = I*V                                 [W]
```

For nonlinear transport the same energy identity is checked using independently
computed endpoint fluxes; it is not imposed by overwriting an endpoint.
Let E1/E2/E3/Ed be net external heat into intermediate/cold/die nodes, including
Au heat at the die, and Qattach=Gattach*(Tdie-Tcold). The solved residuals are:

```text
Qc0-Qh1-E1 = 0;  Qc1-Qh2-E2 = 0
Qc2-E3-Qattach = 0;  Qattach-Ed-Qbias-Qabsorbed = 0    [W]
Th-Tambient = R_sink*(Qh0+Qcu_cond+Qcu_Joule/2+Ehot)  [K]
```

`Ehot=0` for the old reservoir model; the new proxy also exchanges with the
hot node. Its three warm reservoirs are header/cap/window at ambient. All
surface powers, including warm-reservoir powers, are retained and sum to zero.
The source terminal voltage includes Cu electrical resistance. The global balance
includes terminal electrical power, imposed die heat, reservoir exchanges,
Cu heat flow and bath rejection.

No accepted package result may exceed the unchanged 1e-8 residual gate or the
1e-8 W global-energy gate. Stage energy must be below 1e-9 W. The optimizer's
fifth row is a K residual divided by 2 for scaling; failure diagnostics keep
that row separate from the four physical W node residuals. This historical
optimizer scaling is not itself a physical W balance.

## Reproduce and interpret outputs

Run from the repository with the existing pinned FEM image:

```bash
./fem/run.sh python -m tecooledmct.nonlinear_tec_study   --out outputs/current-model/transport
./fem/run.sh python -m tecooledmct.corrected_exchange   --out outputs/current-model/exchange
./fem/run.sh python -m tecooledmct.integrated_reference   --material zhang2025_nonlinear   --exchange outputs/current-model/exchange/operator_65536.json   --out outputs/current-model/scenarios
./fem/run.sh python -m tecooledmct.integrated_reference_figures   --from-dir outputs/current-model/scenarios
```

Use new output locations. The operator/study builders refuse existing output
directories. The legacy scenario CLI can overwrite its chosen directory, so do
not target sealed archives or earlier versioned data.

| Output | Contents |
| --- | --- |
| `summary.json` | All 63 attempts, accepted budgets, model/source identity, full rejection diagnostics, sensitivity and grid-minimum warnings |
| `sweep.csv` | Accepted current points only; never inferred observations across failed intervals |
| `sensitivity.csv` | One-factor endpoint spans, not probability intervals |
| `transport/comparison.json` | Ten independent BVP checks, 16/32/64 leg levels, timings and three package-current convergence sequences |
| `operator_N.json` | Source hashes, native face audit, 14 proxy surfaces, raw/balanced view factors and geometric chords |
| `exchange/summary.json` | Three ray levels at fixed temperatures, pressure sweep and all surface/node powers |
| `development_failures.json` | Explicitly unaccepted initial zero-current energy/initialization failures, retained separately from final results |

When `--exchange` is used, `gas_gap_m`, `cold_surface_factor`,
`cap_view_factor` and `window_die_view_factor` are inactive legacy controls.
Actual proxy geometry sets areas, chords and view factors. `gas_area_factor`
remains an explicitly effective gas-conductance multiplier; it does not change
geometry. The nonlinear leg solver uses a constant-law package result only as
an initial iterate; all reported final temperatures satisfy the nonlinear laws.

## Current results and numerical evidence

At 300 K ambient, 0.15 A, 2 mW imposed die heating:

| Scenario | Constant / old reservoir die K | Nonlinear / old reservoir die K | Nonlinear / new proxy die K | New proxy terminal V / W |
| --- | ---: | ---: | ---: | --- |
| Low-parasitic vacuum | 242.055 | 229.787 | 230.975 | 1.15443 / 0.173164 |
| Nominal Kr 30 kPa | 243.280 | 231.192 | 232.209 | 1.15193 / 0.172790 |
| High-parasitic N2 | 247.615 | 236.253 | 235.031 | 1.14554 / 0.171830 |

The proxy nominal bath rejects 0.182196 W; warm-reservoir exchanges account
for the difference from source power plus die heat. These comparisons change
material and/or package approximations; they do not isolate manufactured-device
accuracy. The versioned 0–1 A grids have 63/63 accepted for the original constant
model, 49/63 for affine analog, **50/63 nonlinear with old reservoirs**, and
**52/63 nonlinear with the proxy**. Different current acceptance is not a
retroactive pass for any archived failure. Every rejected attempt remains visible.

At 0.9 A, nominal old-reservoir nonlinear32→64 changes die temperature by
0.000350 K and terminal voltage by 0.1643 mV. No continuum error bound or
GCI is inferred from these three levels. At low current, knot crossings produce
small nonmonotonic refinement differences. Source/geometry uncertainties still
exceed the demonstrated discretization changes.

## Limits and next work

1. The enclosure is a closed **proxy**: filled interstage core, omitted pins,
   wires, exposed copper and interleg gas voids. Native areas and proxy areas
   differ; neither native full-surface visibility nor gas diffusion is qualified.
2. Cap/window/header reservoirs are prescribed, die is isothermal, contacts
   ideal and bypasses simplified. There is no new 3D field, spectral window,
   electro-optical detector or convection solution.
3. The assumed high-T P/N and low-T gas continuations are internally checked,
   not experimentally validated. Low/nominal/high runs are not confidence bounds.
4. Existing bath <1% and cold-interface <5% criteria remain unmet in preserved
   historical production evidence. Reduced-model conservation does not replace
   them. Update the live Rev3 master in place while preserving its sealed original bytes.
5. Next bounded work should improve native-surface exchange and contact/bypass/
   reservoir sensitivity, with paired mechanism tests. Do not force a large
   conformal gas/TEC remesh or a proprietary OEM fit to complete useful studies.

The [matched solid-model diagnostic](MATCHED_SOLID_MODEL_DIAGNOSTIC_20261031.md)
now quantifies the 0.1 A/2 mW discrepancy. The constant reduced case gives
257.756276 K / 0.585608855 V at a 300 K hot ceramic; the actual corrected Elmer
case gives 265.592524 K / 0.551939871 V with its 300 K Kovar underside.
Matching the archived hot ceramic (300.114898 K) changes the reduced die by
only 0.097305 K. Observed die/readout differences account for another 0.108477 K;
7.630466 K remains between cold-ceramic means. Same-indicator field accounting
finds 41.392/36.293 mW parallel Cu/alumina leakage in the lower two gaps,
and volume-work accounting closes the voltage difference. These identify omitted
paths, not unique causal kelvins per path. The subsequent
[geometry-derived nonlocal control](NONLOCAL_PORT_NETWORK_20261031.md) retains
these paths without fitting and predicts 8.412629 K warming: the cold residual
becomes FEM minus prediction −0.782163 K. Its original five-node baseline is
unchanged. Actual ceramic/pad contacts are nonisothermal and the P174 side heat
changes 7.277% across registered grids, so this is a conditional mechanism test,
not a qualified cross-model reconciliation. One bounded passive plate/pad port
fixture is specified next; no new FEM or Rev3 change is claimed here.
