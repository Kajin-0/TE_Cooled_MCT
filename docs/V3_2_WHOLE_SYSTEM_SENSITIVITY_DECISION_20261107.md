# 2026-11-07 — Fast whole-device material and boundary sensitivity decision after V3.2

**Working physical-device baseline preserved:** [V3.2 original-CAD 88 individual legs + four 3D ceramics with electrical solder/contact loss](../data/v3_2_joint_loss_feedback_20261107/attempt01/result.json), commit \`15d5746\`. **Purpose:** choose the next highest-value physics refinement using a bounded *whole-device* result rather than more local interface microaudits or expensive indiscriminate full-source solves.

**Scientific scope:** Eight preregistered, end-to-end **V1 REDUCED-MODEL** nonlinear 29/11/4 TEC/detector cases, all at **0.40 A, 300 K ambient and source Cu/Au pins**, with original CAD leg counts, source wire paths, the archived original header/TIM/solder/ceramic coarse hot-path \(5.281295\) K/W at baseline, 2 mW detector load, zero cavity gas and radiation, original 32-interval measured research-material transport with *assumed extension above 300 K*. The canonical **V3.2's spatially varying four-ceramic FEM and the 176 solder/352 contact electrical loss are NOT present in the screening solver**. Therefore results are **first-pass conditional sensitivity derivatives only**, not full V3.2 sensitivity results, experimental confidence intervals or manufacturing predictions.

## Reproducible evidence

- [Fast screening solver and source-CAD whole-device one-parameter cases](../scripts/v3_2_fast_system_sensitivity.py)
- [Prospectively fixed eight-case registration and original source hashes](../data/v3_2_bounded_sensitivity_20261107/attempt01/fast_registration.json)
- [All eight accepted numerical source 29/11/4 results and reduced-model ranking](../data/v3_2_bounded_sensitivity_20261107/attempt01/fast_results.json)
- [Independent no-solve source-hash, \(IV\), thermal conservation and baseline replay verification](../data/v3_2_bounded_sensitivity_20261107/attempt01/read_only_acceptance.json)
- [Read-only audit implementation](../scripts/v3_2_bounded_sensitivity_audit.py)
- [Forensic STOP receipt for abandoned high-cost full V3.2 sensitivity campaign](../data/v3_2_bounded_sensitivity_20261107/attempt01/stopped_timebox.json)
- [Archive/source hash manifest](../data/v3_2_bounded_sensitivity_20261107/attempt01/manifest.json)

## Eight fixed inputs and results

All cases are computed in the **same reduced nonlinear whole-device model**. Changes are relative to its actual rerun baseline **\(T_{\rm die}=209.059878\) K**, not to the higher-fidelity **V3.2 \(T_{\rm die}=209.987981\) K**. Those two absolute temperatures have different unresolved physical representations, and must **not** be combined as an uncertainty interval.

| Assumption changed from the same reduced baseline | Calculated die T (K) | \(\Delta T_{\rm die}\) (K) |
| --- | ---: | ---: |
| 0.4 A source-CAD baseline | 209.059878 | 0 |
| **P/N \(S(T)\) × 1.10**, unchanged \(\rho,k\) | 202.460269 | **−6.599609** |
| **P/N \(\rho(T)\) × 1.20**, unchanged \(S,k\) | 211.488372 | **+2.428494** |
| **P/N \(k(T)\) × 1.20**, unchanged \(S,\rho\) | 219.276507 | **+10.216629** |
| Radiator \(R\) from **2 to 3 K/W** (total hot path from 5.2813 to 6.2813 K/W) | 209.323938 | **+0.264060** |
| Detector bias power **2 to 4 mW** | 209.686716 | **+0.626837** |
| Coherent *lower-performance* research-material hypothesis \(S\)×0.9, \(\rho\)×1.2, \(k\)×1.2 | 228.640740 | **+19.580861** |
| Coherent *higher-performance* research-material hypothesis \(S\)×1.1, \(\rho\)×0.8, \(k\)×0.8 | 186.871275 | **−22.188604** |

**Numerical acceptance:** 8/8 cases accepted. Each 0.4 A run enforces terminal \(P=IV\), max whole-system node heat residual \(<10^{-8}\) W, full energy balance \(|\varepsilon|<10^{-8}\) W and independent nonlinear stage energy residual \(<10^{-9}\) W. The nominal case reproduces the archived V1 detector temperature and terminal voltage to \(10^{-8}\) precision. **All eight cases ran in 14.2 seconds.**

**Comparison caution:** Magnitudes rank the *specific, unequal perturbation sizes registered above*, NOT parameter confidence, achievable property tolerance or a global Sobol index. For the three transport single-property scalings, a basic local finite-step slope relative to a fraction of nominal parameter is:

\[
\frac{\Delta T}{\Delta S/S}\simeq -65.996~\mathrm K,\quad
\frac{\Delta T}{\Delta \rho/\rho}\simeq +12.142~\mathrm K,\quad
\frac{\Delta T}{\Delta k/k}\simeq +51.083~\mathrm K.
\]

These are **one-sided finite differences** over 10–20% changes, not infinitesimal derivatives, statistical error bars or validated response surfaces. \(S\) and \(k\) show the largest sensitivities per percentage input change, but the ranking depends on the active operating point and unvalidated material analog.

## Relationship to existing 3D V3.2 and contact coefficient hypotheses

The present *higher-fidelity* V3.2 (one conditional 0.4 A case, NOT rerun for these eight perturbations) calculates \(T_{\rm die}=209.987981\) K, terminal \(1.524071\) V and input power \(0.609628\) W. Its separately established difference from V3.1 is **+0.184688 K** of die temperature after adding **4.5672 mW** from unmeasured 176 source SnSb joints/352 electrical contacts. This is **not directly comparable as an equal-fidelity sensitivity derivative** to the above reduced cases. The source's prior conditional contact areal resistivity envelopes of \(10^{-12},10^{-11},10^{-10}\ \Omega\mathrm m^2\) span an enormous factor 100 but have no matching actual measured distribution. No new contact-specific full V3.2 sensitivity result has been accepted or inferred here.

## Deliberately stopped nonproductive compute attempt

One preregistered six-case study initially attempted to run the **FULL V3.2 original 3D spatial hybrid** once per perturbation. The very first \(S\)×1.10 case used approximately **six minutes of CPU-heavy runtime without producing an accepted result**. To obey the user's *working prototype first, refine only proven material bottlenecks* instruction, the study was explicitly **stopped**. The original six-case registration, source SHA and STOP receipt are retained. **Zero full V3.2 sensitivity cases completed**, and there are **no inferred full V3.2 results**, no hidden replacement of the original numerical gate, and no resume promise.

The fast complete reduced-device screening was then preregistered and executed separately, with its different model fidelity explicit. It needed only 14.2 seconds for 8 cases. Do **not** resume the expensive six-case original 3D campaign as an open-ended parameter grid.

## Actionable next physics work: evidence before detailed FEM

**Primary uncertainty to constrain: actual 3-stage P/N material transport.** The model currently uses unrelated published Zhang P-HE/N-HE-1 research specimens, not identified actual thermoelectric leg grades. Real \(S_P(T),S_N(T),\rho_P(T),\rho_N(T),k_P(T),k_N(T)\), including their **current-carrying direction** and approximate 200–305 K range, are the highest-value source data. Manufacturer material grade/part number and specific transport measurements are more valuable now than refining leg mesh density.

**Second-tier:** obtain actual TEC current/voltage at representative ambient and cooler load, installed radiator temperature or thermal resistance, junction/contact electrical resistance if available, actual die power, and whether cavity gas/radiation is negligible. Once real inputs arrive, update the SAME working V3.2 model and compare its complete I/V/P/Tdie/energy outputs, without retroactively modifying exploratory results.

Historical original P1 Gate B **FAIL/STOP**, original first-couple P1 raw face current **FAIL 8/8**, prospective P2 **STOP**, full 430-domain coupled thermal C/D **NOT RUN**, source physical material release UNSET, and as-built detector-temperature validation **NOT QUALIFIED**, preserved. No Codex was used.

**Development conclusion:** broad inference from slow, unmeasured 3D parameter sweeps is churn. The fast reduced integrated-model screen shows that P/N transport assumptions likely matter by **multiple kelvin to tens of kelvin**, while the tested radiator resistance and die-power changes have substantially smaller effects. Prioritize real P/N evidence and preserve reproducible, increasingly detailed V1–V3.2 working baselines.
