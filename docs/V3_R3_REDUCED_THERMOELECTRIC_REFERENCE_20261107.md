# V3 29/11/4 actual source-CAD reduced electrothermal reference — nine-case conditional study

**Date:** November 7, 2026. **Baseline:** `52fc1d9c7f200d087503a099b2df7442e98b34c0`.
**Numerical verdict: PASS in nine bounded research-hypothesis cases. Physical-device prediction: NOT QUALIFIED.** This is **not** the accepted 430-domain three-dimensional electrothermal PDE and is not claimed as a simulation of a particular manufacturer assembly.

[Versioned one-run manifest and source hashes](../data/v3_reference_29114_reduced_20261107/attempt01/manifest.json), [complete case currents/temperatures/power and residuals](../data/v3_reference_29114_reduced_20261107/attempt01/cases.json), [saved numerical summary](../data/v3_reference_29114_reduced_20261107/attempt01/summary.json), [strict preregistration](../data/v3_reference_29114_reduced_20261107/attempt01/registration.json) and [source code](../scripts/v3_reference_29114_reduced_study.py).

## Purpose and provenance

Previous published reduced results, including 186.484 K under a nominal Zhang2025 analog, came from an older **28/12/4** geometry and a specific external-wire-on case. That number is NOT a result for the 430-domain original R3 geometry and must not be inherited.

This study uses the same archived nonlinear one-dimensional conservative leg BVP and five-node cascade solver, but constructs a separate `geometry()` input from the actual source CAD at `data/synthetic_v3_assembly_20261102/source_final/design.json`, independently checked against R3's accepted 430-domain metadata, all 88 leg source identities and source 29/11/4 stage allocation. It does not call the old 28/12/4 default geometry, does not interpolate a new conductivity, and does not refit OEM data.

| CAD-derived quantity | Hot stage | Middle stage | Cold stage |
| --- | ---: | ---: | ---: |
| P/N couples | **29** | **11** | **4** |
| Individual P and N leg active section | 0.4 × 0.4 mm | 0.4 × 0.4 mm | 0.4 × 0.4 mm |
| Leg length | 0.500 mm | 0.500 mm | 0.500 mm |
| Cross-sectional area per leg | 0.160 mm² | 0.160 mm² | 0.160 mm² |
| Four whole ceramic widths, hot→cold | 6.4 mm | 5.2 and 3.8 mm | 2.4 mm |
| Die-attach layer (separate die node) | **20 µm over 1.0 mm²** | Conductivity \(k=1\) W/(m·K) assumed |

The existing research P/N curves are the corrected Zhang (2025) P-HE/N-HE-1 unmatched P/N specimens, 40–300 K measurement interval, **not an identified manufacturer grade**. The three already documented engineering hypothesis scales are:
- **lower performance:** \((S,\rho,k)=(0.9,1.2,1.2)\);
- **nominal research analog:** \((1.0,1.0,1.0)\);
- **higher performance:** \((1.1,0.8,0.8)\).

These ranges are not manufacturing tolerances, confidence intervals or measured probability distributions. The existing source's assumed continuation above 300 K was **disallowed by acceptance**; all local leg temperatures of all nine accepted cases remain in the actual 40–300 K measured research-profile domain.

## Preregistered operating conditions (optimistic)

- Hot ceramic held at exactly **300 K** by an ideal sink (\(R_{\rm sink}=0\) K/W).
- Detector dissipates **2 mW**, represented at its die node. No extra absorbed optical load.
- Reduced 20-µm die-attach conduction represented using the **assumed** \(k_{\rm attach}=1\) W/(m·K), giving \(G=0.05\) W/K and an inherent **0.040 K die/ceramic drop** under 2 mW.
- **No** external copper/Au wires, gas conduction, radiation, stage-to-stage metal bypass or three-dimensional ceramic heat spreading. In reality all could be consequential; excluding them is a **declared optimistic structural assumption**, not evidence of a vacuum-sealed as-built operating condition.
- One fixed current grid **0.15, 0.25 and 0.40 A** for each of the three material hypotheses. No current optimization or fitted operating-point choice. The 0.40 A value is a **scenario point**, not a validated safe current for the synthesized reference CAD.
- Existing nonlinear solver with **32 axial finite-volume intervals per leg** and five integrated stage/die temperature nodes. No 3D mesh or FEM solution, and no thermal C/D gate qualification.

## Actual numerical outputs

All temperatures are the **calculated die-node temperature** \(T_{\mathrm{die}}\), not measured detector temperature, and were independently cross-checked against archived signed electrical and thermal results.

| Hypothetical P/N material | 0.15 A | 0.25 A | 0.40 A |
| --- | ---: | ---: | ---: |
| Lower performance | **261.503 K** | **244.294 K** | **226.495 K** |
| Nominal research analog | **250.347 K** | **229.072 K** | **207.169 K** |
| Higher performance | **235.750 K** | **210.391 K** | **185.124 K** |

At a fixed hypothetical 0.40 A, the research law choices span **41.371 K** (226.495 – 185.124 K). This is a **scenario span**, not empirical uncertainty. The nominal 0.40 A case uses a model terminal voltage **1.47879 V**, electrical power **0.591515 W**, cold-stage absorbed heat **0.002000 W** and cold ceramic temperature **207.129 K**. The higher-performance 0.40 A case uses **1.48844 V** and **0.595377 W**, cold ceramic **185.084 K**, die **185.124 K**.

**Numerical verification:** all **9/9** registered cases were accepted without retuning or additional runs. All input source hashes matched the preregistered evidence, all leg temperatures remained **185.084–300 K or warmer** in the appropriate individual case, all nine stage-interface heat-flux balances and the global electrical/thermal energy balance met their existing criteria. For the nine cases, the maximum recorded node-balance residual is **2.095×10⁻¹³ W** and the maximum global energy residual magnitude is **5.056×10⁻¹³ W**. Each case also satisfies \(P_{\rm terminal}=I\,V_{\rm terminal}\) to floating-point tolerance and has \(Q_{\rm cold}\approx 2\) mW under the declared idealized zero-parasitic assumptions.

The 32-interval 1D transport equations and global 5-node solver are the **existing** previously validated numerics, but the present runs are **single-grid** studies; no independent new-resolution convergence check for this R3 scenario set was performed. An algebraically conservative solver **does not** establish physically accurate contact losses, geometry, manufacturing feasibility or real heat-sink behavior.

## Engineering interpretation and next gate

1. This completes the previously missing **R3-specific geometry transfer into the already established reduced nonlinear TEC transport model**. It makes conditional source-defined predictions possible without pretending the old 28/12/4 results were the same design.
2. Sensitivity to actual P/N transport properties is substantial: roughly **41 K** across the three material scenarios at 0.40 A.
3. The calculated die-to-cold-ceramic offset of **0.040 K** is almost completely prescribed by the deliberately uniform 20-µm, 1-mm², \(k=1\) W/mK adhesive assumption; it does not account for spreading, imperfect bonding, contacts or additional passive heat leaks.
4. This is an **optimistic envelope**, because radiator/gas/lead transport, real hot-side contact resistance, full 430-solid device thermal bypass and detector optical/electrical loads are not included. No claim is made that actual device performance must lie within the tabulated temperature range.
5. The actual VIGO package reference and TEC Microsystems standalone module are not confirmed as one commercial assembly. The source 29/11/4 stage arrangement is a CAD hypothesis, not a published OEM internal stage wiring specification.

**Next substantive physical work:** independently constrain at least the dominant *real* hot-side thermal impedance and stage/lead/contact bypass loads from source geometry/material and evidence-backed ranges. Do not simply assert zero parasitics or choose arbitrary resistance values to reproduce an OEM temperature. A small number of **pre-registered, source-qualified sensitivity controls** may then quantify how quickly the optimistic die-temperature predictions degrade. Full 3D coupled FEM should remain gated by physical-law readiness and a technically appropriate independent electrical-current and total-energy acceptance contract, not reclassified from previous synthetic P2 results.

The original 824-solid STEP, all protected Rev3 and historical V3 failures, R3.8/R3.9 geometry and full 430-volume/2440-face law-status registry were unchanged. No source calibration, 3D PDE, CAD, mesh generation, thermal C/D promotion or Codex usage occurred.

**Current status:** bounded reduced R3 reference **CONDITIONALLY NUMERICALLY ACCEPTED**; physical as-built TEC/detector **UNQUALIFIED**; original P1 Gate B **FAIL/STOP**, P2 prospective **STOP**, thermal C/D **NOT RUN**.
