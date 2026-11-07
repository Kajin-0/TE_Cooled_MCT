# V3 — Complete conditional TEC with all 88 original P/N legs individually coupled to spatial ceramic-pad temperatures

**Date:** November 7, 2026. **Parent working V2:** commit \`7426b9cda14950a714cea71050bffd81ac81f174\`.

**Qualification: ONE complete 0.400 A source-CAD nonlinear TE + thermal hybrid operating point WORKING and conserved. Local ceramic-pad heat-flux distribution is NOT self-consistent; source original Gate B FAIL/STOP, full 430-domain coupled FEM NOT RUN.**

## Exact executable source and evidence

- [V3 complete integrated driver](../scripts/v3_integrated_leg_resolved.py)
- [Exact one-condition registered inputs](../data/v3_integrated_leg_resolved_20261107/attempt01/registration.json)
- [Saved 88 individual original-source nonlinear P/N leg transport and entire TEC/detector performance](../data/v3_integrated_leg_resolved_20261107/attempt01/result.json)
- [All 88 leg 33-node axial temperature profiles, and all four 3D original ceramic temperature fields](../data/v3_integrated_leg_resolved_20261107/attempt01/v3_source_4_ceramic_and_88_leg_profiles.npz)
- [Read-only independent per-contact source surface-flux discrepancy](../data/v3_integrated_leg_resolved_20261107/attempt01/local_pad_flux_assumption_audit.json)
- [SHA-256 manifest and preserved replay](../data/v3_integrated_leg_resolved_20261107/attempt01/manifest.json)

## What really changed from V2

**Reuse**, rather than rewrite, the 29/11/4 series topology, Cu power leads and Au detector bonds, V2 original 11,791-tetrahedron four-ceramic FEM temperature-response profiles, one-condition 0.4 A/300 K ambient/2 mW detector load, die attach, and V1 original-mesh header/TIM reference.

**New leg-level coupling:** Read the original 430-region/2,440-face source metadata and 824-body source CAD. For each of the **88 original P/N legs** (44 N, 44 P; three stages contain 58, 22, 8 legs), follow its **two exact solder contacts → original metallization net → original ceramic-pad face**. There are **91 distinct source ceramic–metal pad face tags** associated with the 88 legs. These are source CAD graph connections, not approximate nearest-neighbor choices.

For each such contact face, integrate the saved actual 3D ceramic FEM field's temperature over the original source triangular surface mesh with source-area weighting. Subtract its respective mean source ceramic top/bottom contact temperature to obtain a local per-unit-heat temperature offset. At every whole-system nonlinear iteration, apply this offset multiplied by that ceramic plate's current total heat flow to the **actual P or N leg** boundary temperatures, and integrate its **unaltered 32-interval nonlinear research-source P/N constitutive solver**, separately for every one of 88 legs. Sum the individual nonlinear hot/cold heat, series voltage and Joule loss, enforce the 3 interstage heat balances, 4 original-ceramic mean \(Q R_\mathrm{plate}\) relations, hot reservoir, detector carrier/epoxy and Au bond-leak equations. This is a working **leg-specific axial TE and original-geometry 3D ceramic / coarse-network hybrid**. Neither 3D P/N PDE nor original 430-region electrothermal FEM has been solved.

The spatial ceramic source profiles are still the **frozen V2 unit-power profiles**, from an initially **uniform heat distribution by original metal-pad area**. Thus spatial leg temperatures affect mean stage heat and through-plate heat in V3, but local per-pad heat redistributions are **not fed back into the 3D ceramic Neumann source terms**. The energy equations are balanced **globally**, not as a locally conservative fully spatial interface system. This is the next fidelity limit to address, rather than refine raw current microdetails on the old P1 contact mesh.

## V2 versus V3: same conditions

| Quantity | Working V2 | Working V3 | V3 minus V2 |
| --- | ---: | ---: | ---: |
| Source TEC current | 0.4000 A | **0.4000 A** | unchanged |
| Calculated HgCdTe die T | 209.658243 K | **209.688407 K** | **+0.030164 K** |
| Terminal voltage | 1.511212 V | **1.511733 V** | **+0.000520 V** |
| Terminal electrical power | 0.604485 W | **0.604693 W** | **+0.000208 W** |
| Heat rejected to ambient | 0.585882 W | **0.586082 W** | **+0.000200 W** |

The full nonlinear system reached convergence in **5 optimizer evaluations** (17.64 seconds in the source container); saved-field replay passed, numerically reproducing the complete original 88-leg array and all four spatial temperature arrays.

Stage-by-stage at the V3 point:

| Stage | Source leg count | \(Q_h\) W | \(Q_c\) W | Sum TE leg V |
| --- | ---: | ---: | ---: | ---: |
| 0 | 58 | 0.607452 | 0.172301 | 1.087877 |
| 1 | 22 | 0.172301 | 0.041965 | 0.325838 |
| 2 | 8 | 0.041965 | 0.00349583 | 0.096174 |

**Numerical checks:** Global total electricity/TEC/die/lead/sink accounting \(5.32\times10^{-13}\) W, worst stage/interstage heat mismatch \(3.52\times10^{-15}\) W, worst separate TE leg energy residual \(7.39\times10^{-14}\) W. This does **not** validate source transport coefficients, spatial local ceramic flux fidelity, mesh accuracy or manufactured cooler temperature.

Source stage0 hot leg contact temperatures span **302.639–304.207 K**, with stage0 cold contacts **264.871–265.907 K**; stage1 hot **265.492–266.142 K**, cold **235.162–235.406 K**; stage2 hot **235.334–235.540 K**, cold approximately **209.602 K**. Genuine original-geometry contact temperature variation exists and leads to distinct individual leg heat and voltage outputs, but the change in the integrated detector result is small at this reference point. It is **not** an accuracy or sensitivity proof outside the stated operating point.

## Measured numerical deficiency: local pad flux NOT self-consistent

After the one registered solve, independently aggregate the saved individual leg heat by its exact source metal-pad tag. Compare to V2/V3's **assumed area-uniform pad flux** using

\[
D_{\mathrm{L1}} =
\frac{\sum_f |Q_f^\mathrm{leg} -
  Q^\mathrm{ceramic} A_f / \sum_{g\in\mathrm{used}} A_g|}
 {|\sum_f Q_f^\mathrm{leg}|}.
\]

This compares absolute pad-level heat-distribution shapes, **not** temperature error, a conservation residual or a FEM convergence criterion. Each plate side is evaluated separately, and available source metal-only faces exclude unmodeled Cu power lead, solder and metallization effects.

| Original ceramic pad surface | Normalized absolute distribution difference |
| --- | ---: |
| ceramic0, upper stage0 hot contacts | **9.64%** |
| ceramic1, lower stage0 cold contacts | **5.52%** |
| ceramic1, upper stage1 hot contacts | **21.25%** |
| ceramic2, lower stage1 cold contacts | **3.28%** |
| ceramic2, upper stage2 hot contacts | **44.79%** |
| ceramic3, lower stage2 cold contacts | **4.08%** |

The ceramic0 top comparison also has a **total-load difference** because the net source hot-sink heat 0.586082 W is not equal to stage0's 0.607452 W: Cu thermal lead conduction and Joule partition intervene, and not every source plate-pad tag carries a leg. Hence the first percentage is not purely an area-redistribution measure.

**This is the highest-value next numerical step**: take each leg's calculated heat, distribute it over the corresponding original source CAD metal-pad triangles, solve the original ceramic 3D conduction operator with these **nonuniform native-pad fluxes**, and iterate with the 88-leg nonlinear TE field while preserving complete-system current, heat and detector outputs. Keep non-leg Cu and detector loads separately accounted for. Do **not** treat the small +0.030 K V2→V3 die change as evidence that individual spatial effects are negligible until this local heat feedback is included.

## Preserved physics boundaries

Research P/N \(S(T),\rho(T),k(T)\) remain original unmatched Zhang 2025 material analogs, with a **declared >300 K continuation**, not source OEM-grade values. Original 3D ceramic \(k=30\) W/(m K) is a room-temperature analog held constant over 209–304 K. Original solder, composite metal and thermoelectric contact transport remain simplified; no 3D P/N electric current field, localized Joule/Peltier map or actual manufacturer measured boundary validation exists.

Historical **original P1 electrical Gate B FAIL/STOP**, **first actual 3D N/P pair raw current FAIL 8/8**, **P2 STOP**, and **full original 430-domain thermal C/D NOT RUN** remain unchanged. Preserve original STEP/Rev3/mesh and all failure evidence. No Codex or source re-meshing.

**Iteration rationale:** Keep V1, V2, V3 individually runnable; V3 adds *actual source-specific electrical series leg and spatial thermal interactions* to the same complete package simulation at one operating point. The next refinement is based on a measured deficiency in the integrated model (local flux inconsistency), not another open-ended detached mesh audit.
