# V3.8 Engineering Study: Material Transport and Thermal-Mounting Penalties

**9 November 2026 | Refined 29/11/4 three-stage TEC + HgCdTe photoconductor + TO package**

## Engineering summary

Two valuable Revision 3 studies were repeated using the **present physical source geometry**, not its historical 28/12/4-couple cooler. The present integrated system contains 88 individually solved nonlinear P/N legs, the original four spatial ceramic FEMs totaling 11,791 tetrahedra, actual source-face copper interstage tabs and the three-landing return, two separately connected source TEC leads, a finite TO mounting path, and the krypton/radiation enclosure approximation. V3.7's self-consistent HgCdTe bias Joule heating remains active.

**Practical finding 1:** With an imposed common ±20% range on P/N thermal conductivity, predicted detector temperature spans **19.815 K**. The corresponding ±10% common Seebeck screen spans **13.318 K**, and ±20% electrical resistivity spans **4.750 K**. These are *selected one-factor physical-hypothesis spans*, not empirical material tolerances or probability bounds.

**Practical finding 2:** Holding detector temperature within **0.032 K** of the nominal 218.900 K reference requires approximately **8.85% more TEC electrical power** when external mounting thermal resistance increases by 5 K/W, or **19.61% more** when it increases by 10 K/W. The original 4.833387 K/W package resistance is **retained**; the increments represent added thermal impedance outside the modeled package.

**Practical implication:** Material characterization and a defined thermal mounting interface are prerequisites to trustworthy absolute detector-temperature predictions and power budgets. Further optimization of minor lead-alloy details is unlikely to be the best use of compute compared with narrowing these uncertainties.

## 1. Matched physical reference and transport assumptions

Conditions for the one-factor transport screen:

- TEC current: **0.400 A**. Mount reservoir and enclosure: **300 K**. Krypton pressure: **100 Pa**.
- HgCdTe bias: **0.8660254 V**, separately supplied from the TEC power source.
- The currently *unmeasured* detector proxy: **R(218.900024 K) = 500 Ω**, effective activated logarithmic resistance slope **30 meV**, absorbed optical heat **0.500 mW**. Actual detector bias power is recalculated as **V²/R(T)** in each full-system solution, rather than held fixed.
- Original TEC material properties: P/N measured-research-specimen analog values from the previous V3.7 solver. Common factors are applied to both P and N source curves: Seebeck S by 0.9/1.1, electrical resistivity by 0.8/1.2, thermal conductivity k by 0.8/1.2. The temperature derivatives of each scaled source law are consistently scaled, too.
- Original metal, solder, Cu foil, header, ceramic geometry and all detector parameters are **identical across the one-factor experiments**. No new global mesh, CAD, fit or source-material substitution.
- Nominal effective external sink resistance **R_ext = 4.833386961 K/W**, taken from the frozen V2-derived package boundary. This value is treated as a model assumption, not a measured hardware specification.

The exact new V3.8 all-factors-unity reference reproduces the frozen V3.7 voltage, detector temperature, electrical input and heat rejection **bit-for-bit in the saved scalar outputs**, with **T_die = 218.900024028684 K**, **V_TEC = 1.489170087404 V** and **P_TEC = 0.595668034961 W**.

## 2. Result: Transport-property changes have meaningful thermal effects

One-factor operating-point results at 0.400 A:

| Hypothesis | Calculated HgCdTe T (K) | ΔT versus nominal (K) | TEC electrical input (W) |
| --- | ---: | ---: | ---: |
| All source transport factors 1.00 | 218.900 | 0 | 0.5957 |
| Seebeck ×0.90 | 225.833 | +6.933 | 0.5627 |
| Seebeck ×1.10 | 212.515 | −6.385 | 0.6318 |
| Electrical resistivity ×0.80 | 216.563 | −2.337 | 0.5237 |
| Electrical resistivity ×1.20 | 221.313 | +2.413 | 0.6689 |
| Thermal conductivity ×0.80 | 207.812 | −11.088 | 0.6167 |
| Thermal conductivity ×1.20 | 227.627 | +8.727 | 0.5794 |

The corresponding two-endpoint temperature differences are **19.815 K**, **13.318 K**, and **4.750 K** for k, S, and resistivity, respectively, *under the deliberately different percentage intervals stated above*. This ranking is consistent with Rev3's warning that P/N heat conduction and thermopower can dominate cooling predictions. Their numerical magnitudes are **not cross-model validations** because the old cooler's geometry, parasitic links, drive current, sink and package physical model differ.

**Device interpretation:** Lowering thermoelectric leg conductivity reduces passive Fourier return of heat to the cold side. Higher thermopower increases useful Peltier cooling but also changes TEC terminal voltage/power. Lower electrical resistivity reduces resistive heating and voltage demand. Real thermoelectric material properties are not freely independent; improving one at fixed others is a screening hypothesis, not a demonstrated available device material.

The HgCdTe temperature-dependent electrical load also changes slightly with these temperatures. For example, at k ×0.80 and T_die 207.812 K, the assumed detector resistance increases to **544.28 Ω**, reducing detector Joule heating to **1.378 mW**; at k ×1.20 and 227.627 K it decreases to **470.42 Ω**, increasing bias heating to **1.594 mW**. These adjustments are part of the nonlinear full-system solution.

[Material-response figure: source-geometry accepted points](../reports/current/figures/v38_source_material_response.pdf)

## 3. Result: Additional mounting resistance at fixed drive

At fixed TEC current **0.400 A**, 300 K external reservoir and unchanged detector bias, worsening external mounting thermal resistance gives:

| Additional R_sink (K/W) | Total effective R_ext (K/W) | HgCdTe T (K) | TEC electrical power (W) |
| ---: | ---: | ---: | ---: |
| +0 | 4.833387 | 218.900 | 0.5957 |
| +5 | 9.833387 | 220.393 | 0.6049 |
| +10 | 14.833387 | 221.856 | 0.6137 |

Thus the fixed-current detector penalty is **+1.493 K** for +5 K/W and **+2.956 K** for +10 K/W. The model's hot-side TEC ceramic rises from **303.762 K** at nominal to **309.494 K** at +10 K/W, consistent with heat rejection through a worse mounting thermal boundary. These are full-system results, not a simple assumed ΔT = Q × ΔR imposed on the detector node.

[Additional mounting resistance: solved detector-temperature response](../reports/current/figures/v38_package_sink_temperature.pdf)

## 4. Practical matched-target power experiment

Rev3 correctly distinguished fixed-current comparisons from the question an engineer often cares about: **How much electricity must the cooler consume to hold the same detector temperature?**

We repeated that *method* on the current hardware geometry, with a nominal target **218.900024 K**. We first solved fixed-current brackets at **0.40 and 0.55 A**, interpolated a current estimate, saved those intermediate trial results, then performed one further secant correction and **re-solved the complete 88-leg, four-spatial-ceramic system** at each corrected current. The table below contains *actual final nonlinear states*, not interpolated power values.

| Extra mounting R (K/W) | Total R_ext (K/W) | Actual TEC current (A) | Actual HgCdTe T (K) | TEC terminal input (W) | Extra power |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 4.833387 | 0.400000 | 218.900024 | 0.595668 | reference |
| 5 | 9.833387 | 0.415286 | 218.892717 | 0.648375 | **+8.848%** |
| 10 | 14.833387 | 0.433174 | 218.868845 | 0.712481 | **+19.610%** |

Maximum deviation from the reference target is **0.03118 K**. The R+5 result requires another **52.71 mW** and the R+10 another **116.81 mW**, relative to the accepted nominal module input. These are **module electrical terminal powers**, not external driver wall-socket consumption.

The current adjustments are **not a demonstrated global current or power optimum**, an OEM current rating, or a transient mounting qualification. They quantify conditional *matched-temperature energy penalties* in this reference model.

[Matched-temperature current and electrical power figure](../reports/current/figures/v38_matched_detector_temperature_power.pdf) | [Machine-readable final matched target acceptance](../data/v3_8_rev3_transport_and_sink_20261109/accepted_matched_temperature_power.json)

## 5. Original Rev3 transfer and scientific limits

The sealed original **38-page Rev3 assessment** included one-factor material-property effects and matched-200-K finite-sink electrical demand studies using an **obsolete 28/12/4 source hardware hypothesis**, distinct from today's 29/11/4 source design. At its original 0.15 A reduced-model material control it reported conditional endpoint spans of **18.900 K (k ×0.8–1.2)**, **11.142 K (S ×0.9–1.1)** and **2.371 K (resistivity ×0.8–1.2)**. Here the method is successfully transferred, not those old predicted response curves or material/geometry selections.

Important physical limitations, in descending practical priority:

1. **Unidentified thermoelectric material grade.** The source P/N transport laws are research analogs, not an actual qualified matched TE module. Their correlations, thermal contact coefficients, low-temperature validity and unmeasured manufacturing scatter remain unidentified. The large sensitivity spans are not statistical error bars.
2. **Warm-end extrapolation.** Original TE research curves cover up to **300 K**; the chosen method extends the source derivatives above 300 K by an explicitly assumed quarter-slope continuation. The stage-0 hot ceramic reaches approximately **303.8–311.0 K** in these accepted cases, so inferred absolute power and mounting penalties depend partly on this provisional extrapolation.
3. **Mounting R is lumped.** The additional 5/10 K/W represents external interface/heatsink uncertainty; no new mounting block geometry, interface pressure, thermal cycling, heat spreader 3D field, or real hardware test was performed. A realistic next geometry validation should identify the actual header contact footprint and mounting boundary before claiming as-built resistance.
4. **HgCdTe detector resistance is a placeholder.** The assumed activated 500-Ω resistor and 30-meV slope are not bandgap, doping, dark-current measurements, optical absorption, photoconductive gain, noise or spectral response. The 0.866-V detector bias and 0.5-mW absorbed optical heat are conditional illustrative loading.
5. **Conservation ≠ hardware accuracy.** The source 88 P/N nonlinear axial transport equations are solved alongside four actual 3D ceramic FEM fields, with formed-copper and lead multiports, but not a full 430-domain metal/leg/cavity electrothermal PDE. Independent no-PDE audits rederive global/stage energy, detector Joule/current, original copper/lead conductive power and external sink thermal-drop closure. They do **not** independently re-solve all 88 leg source constitutive equations or validate local measured heat flux at every physical metal/ceramic interface.
6. **No intrinsic optimal bias/current demonstrated.** A matched-temperature electrical comparison cannot establish best power, signal-to-noise ratio, detectivity or life expectancy without realistic detector I–V/optical and TEC ratings.

## 6. Numerical verification and reproduce-it-yourself record

**All 15 saved scenarios** are distinct source-registered full nonlinear solves: seven material/nominal cases, four fixed-drive sink/current conditions, two intermediate temperature-target estimates, and two refined matched-temperature confirmations.

The independent verifier reconstructs detector \(V^2/R(T)\), lead and Cu branch thermal/electrical behavior, stage/global energy, and the external sink boundary independently of the solver's internal residual. For every accepted scenario, independent global energy error is below **2 × 10⁻⁹ W**, maximum independent stage mismatch below **2 × 10⁻⁹ W**, absolute hot-side effective sink thermal boundary mismatch below **4 × 10⁻⁷ K**, and the final spatial ceramic-pad convergence tolerance remains **3 × 10⁻⁷ K**. No physical PDE or constitutive gate was relaxed for the new study.

- [Input registrations, nonlinear result JSON, original 3D nodal temperature archives, original logs and audit receipts](../data/v3_8_rev3_transport_and_sink_20261109/)
- [15-case machine-readable SHA-256 acceptance and source-provenance manifest](../data/v3_8_rev3_transport_and_sink_20261109/accepted_study_manifest.json)
- [Conservative full-system V3.8 source](../scripts/v3_8_transport_sink_sensitivity.py)
- [Independent no-PDE original source-pad energy and sink audit](../scripts/v3_8_independent_transport_sink_audit.py)
- [One-factor and fixed-current mounting figures](../scripts/v3_8_material_and_sink_figures.py)
- [Matched detector temperature versus mounting-power figure](../scripts/v3_8_matched_sink_figures.py)
- [All-scenario source and scientific regressions](../tests/test_v3_8_transport_sink_transfer.py)
- [Original V3.7 HgCdTe reference kept unchanged](../data/v3_7_hgcdte_electrothermal_20261109/reference_match/)
- [Original 30-page cumulative current assessment, deliberately unchanged](../reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf)

**Prepublication audit-record integrity correction.** The first independent verifier serialized its external sink base resistance under a variable that was later reused for the full archived V3.4 result. The independently calculated sink temperature drop and all energy checks were made before that reuse and were already correct, but the resulting audit field was incorrectly a large object instead of 4.833386961 K/W. The verifier was corrected, and **all 15 independent audit receipts were reconstructed from the unchanged frozen nonlinear outputs**. The original defective audit record is retained as one prepublication witness with its SHA-256 and explicit explanation. Tests now reject a nonscalar or inconsistent external sink audit value. No nonlinear solver, source geometry, constitutive law or accepted T/V/P value was rerun or changed.

The per-run registration contains a literal SHA-256 of the source solver, the original CAD/mesh/source inputs, and all selected hypothesis values. To reproduce, launch the solver with that exact registration, matching source revision, a newly empty output directory, and the fixed original mesh/source paths. Independently rerun the read-only V3.8 audit on the resulting archived fields. The plots and summary are regenerated only from independently accepted results, never from modeled lines interpolated across failed or missing points.

**Immediate next high-value engineering step:** narrow the actual TEC P/N \(S(T),k(T),\rho(T)\) property evidence and the TO mounting interface geometry / thermal resistance, before larger sweeps. In parallel, advance the HgCdTe bandgap/composition/doping/resistance/noise link so that cooling can be optimized against useful infrared detector signal rather than temperature alone. More CAD variants, speculative global meshes, and repeated cosmetic report rewriting would contribute less at this stage.
