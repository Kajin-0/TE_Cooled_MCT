# V2 — First working source-CAD spatial 3D ceramic / nonlinear 29/11/4 TEC integrated hybrid

**Date:** November 7, 2026. **Parent:** [V1 working coarse end-to-end baseline](V1_INTEGRATED_FULL_PACKAGE_20261107.md), commit \`350d8c60f6accaa7acdacb64b4783e6e7e01ddd0\`.

**Outcome:** **V2 integrated one-condition numerical PASS** at the same 0.40 A input as V1. Four original 3D ceramic plates are spatially solved, their actual geometric response is **coupled back to** the existing 29/11/4 nonlinear 1D thermoelectric stages, and final detector, terminal I/V/P, heat-sink and energy outputs are obtained in one complete operating-point solve. **This is a spatial 3D/reduced-transport hybrid; it is NOT a full 430-domain 3D electrical/thermal FEM, mesh-converged model, actual OEM device, or validated detector-temperature prediction.**

## Reproducible code and saved outputs

[Original-mesh ceramic FEM operator](../scripts/v2_source_ceramic_spatial.py), [ceramic source-hashed preregistration](../data/v2_integrated_spatial_20261107/attempt01/ceramic_registration.json), [four actual-mesh ceramic response operators](../data/v2_integrated_spatial_20261107/attempt01/ceramic_spatial_operators.json), [original-node 3D response profiles](../data/v2_integrated_spatial_20261107/attempt01/ceramic_spatial_profiles.npz), [V2 one-case nonlinear spatial-coupling driver](../scripts/v2_integrated_spatial_hybrid.py), [integrated source-hashed preregistration](../data/v2_integrated_spatial_20261107/attempt02/v2_registration.json), [full V2 terminal, stage, detector and four-plate result](../data/v2_integrated_spatial_20261107/attempt02/v2_integrated_result.json), [four spatial absolute temperature fields](../data/v2_integrated_spatial_20261107/attempt02/spatial_3D_ceramics_at_V2_point.npz), [hash manifest](../data/v2_integrated_spatial_20261107/manifest.json).

The previous V1 code and outputs are unchanged and remain runnable. No new global remesh, no Codex, no new independent thermoelectric solver.

## Method: spatial geometry coupled into working system

Four original accepted R3.9 tetrahedral regions **1, 2, 3, 4** (ceramic0–3), not artificial rectangles. Native original CAD triangular *metal contact* surfaces define each plate's top and bottom. For each isolated plate, assume constant **30 W/(m·K)** AD995-family alumina analog (actual ceramic grade unknown, temperature dependence unverified); impose a **balanced 1 W Neumann flux** distributed uniformly by actual contact area on the top and extracted from the bottom. All other ceramic surfaces are insulating. Resolve the temperature field with original P1 tetrahedra and subtract the bottom area-weighted mean as a pure-temperature gauge. The resulting top-minus-bottom \(\Delta T/Q\) is a real-mesh **conditional effective spreading resistance**, not just \(L/(kA)\). Exact source nodal response profiles are retained.

| Original source ceramic | TET4 / used nodes | Source 3D effective thermal resistance (K/W) |
| --- | ---: | ---: |
| ceramic0, hot | 4,936 / 1,682 | **1.175880** |
| ceramic1, intermediate | 4,085 / 1,363 | **2.444299** |
| ceramic2, intermediate | 1,986 / 683 | **3.998256** |
| ceramic3, cold | 784 / 280 | **4.649599** |
| **Total spatial ceramic FEM work** | **11,791 original TET4** | Four physically distinct thermal contact responses |

Unit-flux FEM charge-free thermal energy residuals were \(<4\times10^{-13}\) W on free nodes, and exact discrete energy-work identities were checked. The four Neumann problems are **single original-mesh only, not h-converged**; resolution, contact uniformity and source ceramics at their operating temperatures still require assessment in later fidelity iterations.

Unlike a detached thermal-map analysis, the four effective 3D thermal responses are then inserted into the **nonlinear thermoelectric conservation equations** and solved together with eight independent temperatures:

1. TEC0 hot-side ceramic0 upper pad contact
2. TEC0 cold-side ceramic1 bottom contact
3. TEC1 hot-side ceramic1 upper contact
4. TEC1 cold-side ceramic2 bottom contact
5. TEC2 hot-side ceramic2 upper contact
6. TEC2 cold-side ceramic3 bottom contact
7. Ceramic3 upper detector-carrier contact
8. HgCdTe die temperature

For each stage, solve the *existing* source nonlinear conservative 32-interval 1D P/N transport at its new hot/cold contact temperature pair. Enforce stage-to-stage total heat conservation and \(T_\mathrm{top}-T_\mathrm{bottom}=Q R_\mathrm{plate,3D}\), with the die attach and Au bond-wire heat paths. Close the hot side against the same V1 source Kovar/TIM, solder and manufacturer-reference radiator pathway, **replacing** V1's one-dimensional ceramic0 estimate with its native 3D ceramic0 result.

**Source lead accounting limitation:** Cu power-lead thermal conduction and half lead Joule remain lumped as in V1. The top ceramic0 source pad distribution carries the *net* hot-sink heat rejection, not individually spatially mapped copper lead and pad Joule pathways. P/N legs, solder junctions, gas, detector and full metal geometry remain reduced, not newly 3D-meshed/electrically solved.

## V1 versus V2 under the same one current and conditional material inputs

| Output | V1 | V2 |
| --- | ---: | ---: |
| Current | 0.400 A | 0.400 A |
| HgCdTe die temperature | 209.0599 K | **209.6582 K** |
| Terminal voltage | 1.506395 V | **1.511212 V** |
| Electrical input | 0.602558 W | **0.604485 W** |
| Heat rejected to ambient | 0.586574 W | **0.585882 W** |
| Hot-side full equivalent R (with hot ceramic0) | 5.281295 K/W | **6.009267 K/W** |
| Stage heat-flow accounting | Pass | **Pass** |

The **+0.598364 K** V2-minus-V1 die delta is a *model change under stated assumptions*, **not** a finite-element error bound or as-built forecast.

At the operating point, the source temperature results are:

| Location | V2 temperature (K) |
| --- | ---: |
| TEC hot ceramic0 upper source pads | 303.5207 |
| Ceramic1 bottom / TEC0 cold pad | 265.4327 |
| Ceramic1 top / TEC1 hot pad | 265.8536 |
| Ceramic2 bottom / TEC1 cold pad | 235.2331 |
| Ceramic2 top / TEC2 hot pad | 235.4009 |
| Ceramic3 bottom / TEC2 cold pad | 209.5721 |
| Ceramic3 upper carrier pad | 209.5883 |
| **HgCdTe die** | **209.6582** |

All four source-geometry ceramic temperature fields are archived, including original global source node identifiers and XYZ coordinates. At this operating point the hot ceramic0 nodal field spans **301.22–304.25 K** (3.03 K spread), ceramic1 264.79–266.15 K (1.36 K), ceramic2 235.07–235.52 K (0.45 K), and ceramic3 209.569–209.593 K (0.024 K). The V2 nonlinear stage system uses **flux-weighted mean pad temperatures**, not every spatial node as a local P/N contact transport unknown.

**Solver stability and conservation:** A single prospective operating-point nonlinear solve converged in **six optimizer evaluations**. Maximum unscaled interstage/detector heat imbalance \(3.89\times10^{-15}\) W; maximum plate-junction temperature discrepancy \(1.38\times10^{-14}\) K; full terminal-power/pin/TEC/detector/sink heat accounting residual \(1.42\times10^{-13}\) W. Read-only replay reproduced the operating point and all saved spatial arrays exactly.

## Critical physical qualifications

- **Existing research P/N transport is grade-unmatched and requires an explicitly assumed continuation above 300 K** for the 303.52 K hot stage.
- The alumina thermal conductivity is **constant 30 W/(m·K) across all plates from 209 to 304 K**, a room-temperature AD995 analog and **not** an independently measured law for actual plates or this temperature interval.
- Copper contacts, solder joints, electron/heat-current crowding, contact Peltier/Joule heat, 3D spatial temperature variation along the P/N legs, ceramic/metal thermal boundary discontinuities, gas and radiation are not full 3D fields. No manufacturer product grade or actual mounting-contact characterization is available.
- The 3D thermal operators have a fixed source-mesh P1 response; energy conservation does **not** establish spatial h-convergence or raw original interface-current precision.
- **Historical old electrical P1 Gate B FAIL/STOP, first coupled original-CAD P1 pair raw-contact current FAIL 8/8, P2 prospective STOP, full original 430-domain coupled thermal C/D NOT RUN** remain untouched. No physical as-built detector-temperature qualification.

## Iterative-development decision

**V2 is an actual running, integrated improvement**, with quantitatively observable impact on the same V1 terminal and detector metrics. We should keep both V1 and V2 runnable. **Do not churn on isolated microcontact audits.** The next V3 candidate should be chosen only after considering what is likely to change the entire device response: for example a coarse source-geometry spatial P/N + ceramic coupling, while preserving the same \(.4\) A test case, honest material hypotheses and full I/V/P/T_die/energy comparison. Resolve full spatial current conservation as a separate qualification; do not relabel the historical failed raw-current gate.

### Preserved failed setup attempts

The [manifest](../data/v2_integrated_spatial_20261107/manifest.json) records an attempt01 completed four-ceramic 3D solve followed by an initial integrated-result reporting-key error (no result saved). The first attempt02 invocation was rejected before a solve because a descriptive narrative field had been added to an exact registration; that field was moved to a separate failure note. The successful second attempt02 invocation used the **same source geometry, model parameters, and registered physical assumptions**, with only reporting/registration bookkeeping repaired. No parameter search was done.
