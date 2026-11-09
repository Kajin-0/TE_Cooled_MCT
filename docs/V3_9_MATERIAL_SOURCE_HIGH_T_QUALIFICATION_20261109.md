# V3.9 | TEC source-material coverage and high-temperature continuation

**9 November 2026 | Six accepted complete 88-leg + 3D-ceramic coupled simulations**

## Engineering finding

The current physical TEC–HgCdTe–TO assembly uses digitized P/N thermoelectric research-specimen properties measured to **300 K**, while the hot ceramic reaches approximately 303.8 K at nominal mounting and 309.5 K with 10 K/W additional external mounting resistance. The original model extends all three research-source properties, Seebeck S(T), electrical resistivity rho(T), and thermal conductivity k(T), above 300 K using **25% of the final published property-curve segment's slope**. This is explicitly an unverified modeling assumption, not OEM evidence.

We have quantified how much this particular extrapolation matters while **holding every source property at and below 300 K unchanged**, leaving the real 29/11/4-couple CAD and source 88 nonlinear P/N legs, four original 3D ceramic FEM meshes (11,791 tetrahedra), physically placed Cu formed-foil connectors and terminal wires, gas/radiation proxies and V3.7 self-heating HgCdTe detector law intact.

The tested above-300-K tangent factors are **0% (flat), 25% (current reference), 100% (full final source slope)**. These three explicitly different **hypotheses are not calibrated confidence bounds**.

| Extra mounting R (K/W) | Unverified >300 K slope | Tdie (K) | TEC terminal input (W) | Hot TEC node (K) |
|---:|---:|---:|---:|---:|
| 0 | 0% | 218.904303 | 0.595531 | 303.761 |
| 0 | **25% reference** | **218.900024** | **0.595668** | 303.762 |
| 0 | 100% | 218.887271 | 0.596076 | 303.765 |
| +10 | 0% | 221.875686 | 0.612869 | 309.481 |
| +10 | **25% reference** | **221.856050** | **0.613656** | 309.494 |
| +10 | 100% | 221.797477 | 0.615984 | 309.530 |

At nominal mounting, the 0-to-100% engineering-hypothesis span is **0.017032 K in detector temperature** and **0.545 mW in TEC electrical input**. At +10 K/W external mounting resistance, the corresponding spans increase to **0.078210 K** and **3.115 mW**.

These effects are much smaller than the previously accepted new-design V3.8 source-material scale experiments: **19.815 K** temperature span when P/N thermal conductivity is varied ±20%, **13.318 K** for Seebeck ±10%, and **4.750 K** for resistivity ±20%. Those larger spans likewise represent selected hypothetical factors, **not statistical uncertainty or manufacturable material variability**.

**Practical decision:** Retain the 25% continuation as a clearly marked provisional law at the investigated conditions, rather than invest further in fitting a nonexistent measured >300 K property curve. **The larger priority remains obtaining actual paired P/N material-grade S(T), rho(T), k(T) and thermal mounting-interface evidence.**

## Original thermoelectric material evidence

The repository already carried an independent material-readiness audit, preserved at docs/V3_2_PHYSICAL_MATERIAL_READINESS_20261107.md. Its source is the digitized Zhang et al. (2025) thermoelectric specimen paper, Chinese Physics Letters 42, DOI **10.1088/0256-307X/42/5/056304**. The material registry data/g2c/zhang2025_he_40_300_v2.json documents two independent hot-extruded research specimens:

- P-HE: (Bi,Sb)2Te3; published S, rho, k plotted and digitized from the same P sample.
- N-HE-1: Bi2(Te,Se)3; published S, rho, k plotted and digitized from the same N sample.

Six properties with 14 original figure marker values each yield **84 digitized markers across 40–300 K**. They are neither original raw instrument files nor a measured/qualified commercial P/N matched TEC pair. Manufacturer batch identification, grade matching and correlations are **not established**. Digitization reading uncertainty does not determine module-to-module material scatter.

The numerical 32-interval axial transport domain runs from 180 to 390 K, but this does **not** extend published measurements. For T>300 K the separate V3.9 hypothesis uses:

\[
f(T)=f(300\mathrm{K})+
s_{\rm ext}(T-300\mathrm{K}) f'_{\rm final\ published\ segment},
\quad f\in\{S,\rho,\kappa\},\quad s_{\rm ext}\in\{0,0.25,1\}.
\]

All P/N values **and temperature derivatives** below 300 K match the frozen nominal law; the 25% V3.9 solver reproduces V3.8 TEC input, temperature, voltage and sink output to saved floating-point precision at both mounting conditions.

## Scope and physical interpretation

Every saved case remains a fully coupled original-geometry calculation at **TEC drive current 0.400 A**, 300 K environment, 100 Pa krypton, and with a **separate 0.8660 V assumed detector bias** and 0.5 mW assumed absorbed optical heat. The HgCdTe resistance is still a placeholder **500 ohms at 218.900 K with 30-meV effective logarithmic activation slope**, not a real material-specific carrier population, photoconductive gain, spectral absorption or detector noise model.

**Actual source exposure is finite and nonzero.** All 58 lower-stage P/N legs have hot-side source temperatures >300 K in these six cases. At nominal sink, **265–266 of the total individual leg axial temperature grid nodes** lie above 300 K across the 88 legs; at +10 K/W, **578–586** axial nodes do so. This is a finite-grid node count, not a solved continuous volume fraction. The local hot ceramic state is ~303.8 K versus ~309.5 K.

The 0-to-100% study bracket is deliberately limited. It does not establish material behavior beyond 300 K, a safe module operating condition, a temperature-independent full-system bound, or an OEM qualification. A different real grade or non-linear source extrapolation could lead to different performance. The source constitutive functions above 300 K, current-dependent interconnect contact resistance and optical detector response remain unvalidated.

## Evidence, controls and reproducibility

All six cases retain registered input settings, actual nonlinear per-leg outputs, original four source 3D ceramic nodal temperature archives, physical-balance convergence records and a separate **no-PDE** source-contact/lead/copper/detector energy and external sink-boundary audit. The independent auditor reconstructs electronic Joule heat and entire stage/global energy without re-running the full nonlinear PDE or transport solver. It explicitly tracks the registered source slope factor and checks the exact number of >300 K leg hot boundaries and axial temperature nodes.

An additional opt-in axial transport module exists only for this experiment and **does not overwrite the active baseline nonlinear_tec or graded_tec laws**. Five new tests check identical properties and derivatives at/below 300 K, passivity and conservative leg energy at extrapolated temperatures, rejection of unsupported multipliers, original frozen current-model identity and both exact 25% reference recoveries.

Sources and deliverables:

- Six full solved cases and independent energy audits: data/v3_9_highT_source_qualification_20261109/
- Registered source-transport variant: tecooledmct/nonlinear_tec_v39.py
- Source-based 88-leg/3D-ceramic whole-device model: scripts/v3_9_highT_source_qualification.py
- Independent energy audit: scripts/v3_9_independent_highT_energy_audit.py
- Reproducible figure: reports/current/figures/v39_high_temperature_source_extrapolation.pdf
- Focused model/historical preservation checks: tests/test_v3_9_highT_source_qualification.py
- Actual source material evidence gate: docs/V3_2_PHYSICAL_MATERIAL_READINESS_20261107.md
- Preceding material/sink physics: docs/V3_8_REV3_MATERIAL_AND_FINITE_SINK_STUDY_20261109.md
- Frozen 30-page cumulative hardware engineering report: reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf

## Research direction

**Next practical physics work:** preserve the paired-grade input gate rather than fabricate real-looking P/N curves. Material feasibility/grade evidence for the actual 29/11/4 P/N stage and corresponding TO-header mounting contact should be narrowed using existing datasheet/source evidence. The pre-existing source candidate validator is already in scripts/v3_2_material_candidate_validator.py. After physically credible P/N evidence is available, independently assess the semiconductor/detector composition, doping/mobility, contacts, infrared absorption and noise, and compare integrated model predictions to hardware observables.

The original Rev3 PDF and all earlier sources, tests, reported 3D meshing failures and engineering documents remain unchanged. This standalone study intentionally does **not** revise the stable cumulative report or start a new global 430-domain mesh.
