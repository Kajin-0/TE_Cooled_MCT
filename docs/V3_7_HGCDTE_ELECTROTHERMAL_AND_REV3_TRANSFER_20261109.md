# V3.7: Self-consistent HgCdTe detector bias and Rev3 study transfer

**9 November 2026 | Five accepted whole-system electrothermal cases | Original V3.5/V3.6 TEC physics unchanged**

## Device physics added

V3.6 treated detector heat as an externally prescribed number. V3.7 computes **detector voltage-bias Joule heating from its solved temperature** and feeds that power back into the entire 88-leg, four-source-ceramic, formed-copper, TO-package nonlinear solver:

\[
R(T)=R_0\exp\!\left[\frac{E_{\mathrm{eff}}}{k_B}\left(\frac1T-\frac1{T_0}\right)\right],\qquad
I_d=V_d/R(T),\qquad Q_d=V_d^2/R(T)+Q_{\mathrm{opt,abs}}.
\]

The effective activated resistance slope \(E_{\mathrm{eff}}\) is **not the HgCdTe bandgap**, not a validated doped-carrier model, and not an assertion about a real detector. It represents a bounded engineering sensitivity assumption. Selected unmeasured reference: **500 Ω at 218.900024 K, 30 meV effective activation, 0.500 mW absorbed optical heat**. All cases: 0.400 A TEC current, 300 K sink/cap and 100 Pa krypton.

| Detector bias | Solved detector T | Detector R | Detector current | Joule heating | Total detector heating |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 V | **218.434031 K** | 501.699 Ω | 0 mA | 0 mW | 0.500 mW |
| 0.866025 V | **218.900024 K** | 500.000 Ω | 1.732 mA | 1.500 mW | 2.000 mW |
| 1.20 V | **219.331954 K** | 498.436 Ω | 2.408 mA | 2.889 mW | 3.389 mW |
| 1.50 V | **219.842855 K** | 496.601 Ω | 3.021 mA | 4.531 mW | 5.031 mW |
| 1.20 V, effective activation 60 meV | **219.334810 K** | 496.857 Ω | 2.415 mA | 2.898 mW | 3.398 mW |

At the nominal 30-meV assumption, moving from zero detector bias to 1.5 V increases detector temperature by **1.409 K** in this complete TEC–package model. The 1.2 V comparison between assumed 30 and 60 meV changes detector T by **2.856 mK** locally near the chosen common 218.9-K resistance reference. This local difference does not mean carrier transport properties can be ignored at widely different temperatures, compositions or bias.

The detector voltage source is **separate** from the TEC supply. Full-system TEC terminal voltage and power remain explicitly reported in each result.

[Bias-versus-temperature and Joule-power figure](../reports/current/figures/v37_hgcdte_bias_temperature.pdf) | [Reference resistance-law hypotheses](../reports/current/figures/v37_detector_resistance_hypotheses.pdf)

## Reference compatibility, conservation and physical boundaries

Rev3's 2-mW heater was specified as 1.5 mW bias-like and 0.5 mW optical-like heating, without computing detector current. V3.7 deliberately reproduces these amounts at 0.866025 V with 500 Ω. That case matches the frozen V3.6 **218.900024 K** detector temperature, TEC voltage, TEC input power, sink rejection and outer iteration count to numerical precision (temperature difference **2.3 × 10⁻¹³ K**).

Each of the five separately solved electrothermal states has an **independent no-PDE audit** of actual source-pin lead Joule/conduction, interstage copper nets 58/80/88 including the return's middle thermal landing, all three stage heat balances, and detector \(R(T)\), \(I_d\), \(V_dI_d\) and net heating. The independent maximum stage/global energy errors are **below 2 × 10⁻⁹ W**, final spatial pad updates below **3 × 10⁻⁷ K**. Saved original nodal temperature fields include all four ceramic FEMs with **11,791 actual tetrahedra** and 88 original nonlinear P/N legs. No old CAD, material law, model output or prior report was changed.

For constant detector-voltage bias the analytic feedback slope is

\[
\left.\frac{dP_{\rm bias}}{dT}\right|_V
=\frac{V_d^2}{R(T)}\frac{E_{\rm eff}}{k_BT^2}.
\]

Combining this with V3.6's independently determined **~311 K/W local package thermal-load sensitivity** gives *screening-only*, dimensionless gains of approximately **0.0034** at 0.866 V, **0.0065** at 1.2 V and **0.0102** at 1.5 V. With 60 meV at 1.2 V, approximately **0.0130**. Small proxy gains suggest weak positive local feedback over the selected reference cases, **not** a dynamic thermal stability eigenanalysis, exclusion of bistability, or a real hardware current-rating determination.

## Original 38-page Rev3: most useful studies for the new physical cooler

The source study is the sealed HgCdTe Engineering Assessment, Revision 3 (38 pages). That model used **a different 216-domain, 28/12/4-couple initial cooler** and separate simplified five-temperature analysis. Its absolute temperature and sensitivity magnitudes must never be imported as predictions for the current **29/11/4-couple formed-copper cooler**.

| Rev3 investigation | Original numerical finding | Use for V3.7 |
| --- | --- | --- |
| P/N transport-property screen, Section 16 | At a historical 0.15 A model point, thermal conductivity factor 0.8–1.2 shifted detector temperature **18.900 K**; Seebeck factor 0.9–1.1: **11.142 K**; resistivity factor 0.8–1.2: **2.371 K** | **Highest-value next transfer:** run small matched V3.7 source-based sweeps. The old response sizes are not portable |
| Detector heating, Sections 4 and 16 | Old imposed 1.5 mW bias + 0.5 mW optical-like; a 0.5–5 mW bias proxy span shifted temperature **2.226 K** | **Improved in V3.7:** bias power now comes from \(V_d^2/R(T)\) inside the nonlinear whole-package solve |
| Finite mounting heatsink and matched target, Section 14.8 | Historical nominal electrical input at a 200 K target rose from **0.548 to 0.622 W** for effective sink impedances 0 to 10 K/W | **High-value next transfer:** source geometry-informed TO/header finite-sink and power required to achieve specified temperature |
| Model identifiability, Section 4 | Material/geometry scaling degeneracies and a rank-8-of-9 finding in a distinct model | Preserve structural identifiability tests; do not claim unique physical material extraction from a single terminal measurement |
| Accepted/rejected states, Sections 10, 12 and 14 | Historical reduced grid 52 accepted/11 rejected; another material screen 141 admitted out of 181 | Preserve explicit physical-domain, convergence and energy STOP gates; don't interpolate missing/rejected points |
| Gas, radiation and parameter screens, Section 16 | Older pressure, emissivity and package proxies gave condition-specific spans | Repeat only if consequential for current cooler; original proxy percentage rankings are not automatically valid |
| Interface gradient and refinement checks, Sections 7–11 | Historic source raw-gradient and bath normal-refinement checks remained failed | Preserve failed full-3D release gates; an excellent global energy residual does not establish local interface accuracy |

**Material composition warning:** Rev3 used Hg₀.₇₁Cd₀.₂₉Te to prescribe a *thermal conductivity proxy*, not validated detector electronic properties. The Hansen–Schmit–Casselman bandgap relation gives approximately **0.259 eV**, equivalent to **4.79 µm nominal cutoff** at 218.9 K for x=0.29, **not LWIR**. The 30-meV *resistance slope* used for V3.7 is not that bandgap. Composition, doping, mobility, defect/contact physics, and measured spectral cutoff must be specified before claiming a useful LWIR HgCdTe device model. Bandgap context: [Seiler et al., NIST, JVST A (1990)](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=14738).

## Independent evidence and next engineering decision

- [Complete five-case registered inputs, nonlinear full-device results, original ceramic nodal fields and independent audits](../data/v3_7_hgcdte_electrothermal_20261109/)
- [Executable V3.7 whole-system solver](../scripts/v3_7_coupled_hgcdte_bias.py)
- [Explicit detector electrical/thermal law](../tecooledmct/hgcdte_bias_proxy.py)
- [Independent reconstruction of HgCdTe current, Joule power, leads, copper and all system energy balances](../scripts/v3_7_independent_electrothermal_audit.py)
- [Six detector/source/coupling regression checks](../tests/test_v3_7_hgcdte_bias_coupling.py)
- [Original cumulative V3.6 engineering report, deliberately left unchanged](../reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf)

**Priority now:** transfer a deliberately small, realistic P/N conductivity/thermopower/resistivity sensitivity test and finite TO heatsink/mounting test from Rev3 into the current 29/11/4 source model; then replace the assumed HgCdTe resistance slope with a composition/doping/mobility-constrained model and expand to power-vs-useful-detector-performance. Do not run the old Rev3 216-domain model as though it were the same physical cooler. The full original 430-domain metal/PN/void PDE and empirical detector I–V/responsivity/noise are still **not established**. The existing 30-page main PDF is **not edited** here to avoid report churn.
