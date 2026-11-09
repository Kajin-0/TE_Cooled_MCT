# V3.11 — Backfill gas and pressure: Rev3 experiment repeated on the refined TEC

**9 November 2026 | Eight independently accepted source-geometry electrothermal solutions | Separate engineering study**

## Executive result

The redesigned three-stage **29/11/4-couple thermoelectric cooler**, its four original spatial ceramic FEMs, formed copper interstage foils, electrical leads, TO mounting path, radiation and a fixed 2 mW detector heat load were kept unchanged. The only varied physical inputs in the principal comparison were cavity gas species and pressure. These are newly calculated operating states, **not numerical results copied from the older Rev3 28/12/4 architecture**.

All cases below use **TEC current 0.400 A**, 300 K external reservoir, source-defined sink resistance and a fixed **2.000 mW detector heat load**. The detector-specific semiconductor model is not used.

| Backfill | TEC cold ceramic (K) | Detector-mounting proxy (K) | Gas load (mW) | TEC electrical input (W) |
| --- | ---: | ---: | ---: | ---: |
| Vacuum: gas conduction turned OFF | 218.35275 | **218.43662** | 0.000 | 0.596111 |
| Kr, 100 Pa: frozen original reference | 218.80673 | **218.90002** | 3.420 | 0.595668 |
| Kr, 30 kPa | 218.84525 | **218.93933** | 3.724 | 0.595630 |
| Kr, 101.325 kPa | 218.84535 | **218.93943** | 3.725 | 0.595630 |
| Ar, 30 kPa | 219.27678 | **219.37982** | 6.966 | 0.595209 |
| N2, 30 kPa | 219.70279 | **219.81465** | 10.170 | 0.594792 |
| N2, 101.325 kPa | 219.70307 | **219.81495** | 10.172 | 0.594792 |

Compared at the same 30 kPa, **nitrogen increases the modeled detector temperature by 0.87533 K relative to krypton** and adds **6.446 mW** of heat through the effective cavity gas branches. Argon at 30 kPa increases the detector temperature by **0.44049 K relative to krypton**. Vacuum is **0.50281 K colder than 101.325 kPa Kr**, and **1.37833 K colder than 101.325 kPa nitrogen**, at this fixed operating condition.

The model also predicts **strong pressure saturation** in the nominal 3 mm effective gap. Raising krypton from 100 Pa to 30 kPa changes the detector by only **+0.03930 K**; raising 30 kPa to 101.325 kPa changes it only **+0.00010 K**. This is a *result of the specified effective gap, area and gas accommodation law*, NOT a measured full-cavity pressure response. Real narrow inter-pellet gaps and gas-exposed contacts could invalidate that apparent early saturation.

A separately solved **0.55 A, Kr 30 kPa** case yields **205.93098 K top TEC ceramic**, **206.03180 K detector-mounting proxy**, **1.06462 W TEC input** and **4.214 mW** cavity gas heating. Relative to the unchanged prior 0.55 A, 100 Pa Kr baseline, its detector temperature increases **0.03935 K**. The higher current substantially lowers temperature but raises input power; this pair does not establish a globally optimal current without current-rating evidence and an explicit admissible objective.

[Gas species and pressure thermal results](../reports/current/figures/v311_backfill_species_pressure_cold_temperature.pdf) | [Krypton pressure response](../reports/current/figures/v311_krypton_pressure_sensitivity.pdf)

## Historical Rev3 science transferred to the new physical architecture

Original Rev3 Sections 13, 14, and 16 analyzed pressure-dependent gas conduction, gray enclosure radiation, N2/Ar/Kr tabulated thermal properties, sensitivity to gas-accommodation and package parameters, and compound low/nominal/high parasitic regimes. At one historical **0.15 A** reduced-model scenario, the original **28/12/4** candidate produced a conditional **0.721 K** difference between vacuum and 101.325 kPa Kr. Its mixed vacuum/Kr/N2 scenario families also varied mounting, emissivity and Au-wire properties simultaneously: those families are useful engineering alternatives, but they do **not** isolate a single factor.

V3.11 uses genuine **new source 29/11/4** TEC assembly with **88 separately solved nonlinear P/N legs**, the **four original source-coordinate 3D ceramic FEMs totaling 11,791 tetrahedra**, source-metal interstage foils 58/80 and three-foot 88, proper power leads and original mounting thermal feedback. All gas comparisons at 0.400 A hold the other physical parameters fixed. The **100 Pa Kr reference exactly reproduces frozen V3.6 temperature, TEC voltage/input and sink rejection**. These facts support internal source-model consistency, not agreement with an OEM unit.

## Physics of the assumed cavity gas model

The active four-branch gas-conductance proxy uses:

\[
G_{g,i}=\frac{k_g(T_{\rm mean})A_i}{g+2\ell_{\rm jump}(p,T_{\rm mean},a)},\qquad
Q_{g,i}=G_{g,i}(T_{\rm reservoir}-T_i).
\]

Here the effective gap is **g = 3 mm**, thermal accommodation coefficient **a = 0.8**, and the source-defined exposed areas for three successive cold ceramic patches and the die are **[12.60, 8.68, 4.76, 1.00] mm²** (27.04 mm² total). Gas temperature-dependent conductivity is interpolated from existing 200/300/400 K NIST-type data with an Eucken viscosity/mean-free-path engineering closure. Representative 300 K conductivities: **Kr 0.0095, Ar 0.0177, N2 0.0259 W/(m K)**. The vacuum limit sets gas conductance exactly zero but retains radiation and solid conduction.

The original source ceramic effective-node temperatures entering the four gas branches are **stage-1 hot surface, stage-2 hot surface, carrier and die**, according to the V3.6 model. This is not a full internal gas-domain finite-element model or a geometrically comprehensive gas-conduction network. Importantly, these simplified exposed areas are mapped to source ceramic pad heat, not the true full surface of the sidewalls and pellets. The cap and window are assumed warm reservoirs; nonisothermal cap fields, interleg occlusion, actual package free volume, leakage and convective effects remain unresolved. A more physical gas model should extract available narrow gaps and exposed patches from the **current** source CAD rather than infer their conductance from an arbitrary fitted scale.

At the 0.400 A 30 kPa points, gray-radiation heat remains nearly unchanged (**~0.56 mW**) while net cavity gas heat varies **3.72 / 6.97 / 10.17 mW** for Kr/Ar/N2. Thus the observed difference is traceable to the intentionally varied gas transport physics, not changes in material or assumed detector heating.

## What controls minimum top-stage temperature?

Rev3's useful goal was not to produce a single attractive cold-temperature value; it was to identify *which construction and operating variables materially affect cooling*. Previous accepted new-architecture experiments provide a guide, but their ranges are engineering hypotheses **not empirical tolerances or confidence intervals**:

| Existing source-architecture experiment | Conditional effect on detector temperature or power | Confidence limitation |
| --- | --- | --- |
| V3.8 P/N thermal conductivity ×0.8–1.2 | **19.815 K** detector-temperature span | Independent hypothetical material scaling; no certified paired P/N grade |
| V3.8 P/N Seebeck ×0.9–1.1 | **13.318 K** span | Tradeoff with other P/N properties not constrained |
| V3.8 P/N resistivity ×0.8–1.2 | **4.750 K** span | Unmeasured grade, joints and contact resistance |
| V3.8 external mounting resistance +10 K/W | **+2.956 K** at 0.400 A, or **+19.61% TEC input** at approximately matched detector T | Assumed external sink model, no measured interface |
| V3.11 vacuum vs 101.325 kPa N2 | **1.378 K** span at 0.400 A | Effective 3 mm gas cavity proxy; actual source-native leakage unknown |
| V3.11 30 kPa N2 vs Kr | **+0.875 K** at 0.400 A | Same effective-gap geometry and accommodation hypothesis |
| V3.6 fixed detector load 1–6 mW | Roughly 1.56 K in original operating-point screen | Fixed imposed load; not optical/electronic detector performance |

Do not compare these raw spans as a statistically ranked uncertainty budget: their factor ranges are different and selected arbitrarily. A narrower physically feasible range can produce a smaller real variation even if its raw mathematical sensitivity is large.

The optimization target is the **TEC's final cold-stage ceramic / detector mounting temperature**, with constraints on maximum TEC input power, realistic P/N material pairing, source-interstage thermal bypass, terminal and joint heating, sensible external mounting resistance and a specified die thermal load. A cooler-temperature operating point alone does not define maximum COP or minimum electrical-energy expenditure.

## Pellet dimensions: physically consistent next Rev3-derived experiment

The new source TEC uses **0.40 × 0.40 × 0.50 mm P/N pellets on 0.58 mm pitch**, with identical leg cross section **0.16 mm²** in each of the 29/11/4 series stages. The 1D nonlinear transport physics explicitly uses cross section **A** and leg length **L**; elementary limiting scalings are:

\[
j=I/A,\quad K_{\rm pellet}\sim \kappa A/L,\quad
R_{\rm pellet}\sim \rho L/A.
\]

These competing effects are the reason pellet dimensions are attractive for optimizing minimum cold-stage temperature. However, changing **L** alters stage height, foil bridge geometry and clearance; changing pellet width changes pad coverage, thermal/electrical solder contact and interleg void area. A physically meaningful new-architecture pellet study needs **two distinct labels**:

1. **Axial transport-only diagnostic:** vary pellet A or L in the existing 88-leg solver, explicitly keeping all ceramic spatial fields/contact/source placement fixed. This isolates an underlying mechanism but is **NOT a physically rebuilt cooler**.
2. **Source-geometry consistent synthetic variant:** update actual pellet dimensions, pad/plate landing and contact sizes, gap volumes, formed Cu tab bends/clearances and thermal interfaces, then validate and regenerate the necessary geometry/thermal mapping. This is what can ultimately support comparative construction-design claims.

Do not imply the older Rev3 provided as-built pellet geometry evidence or a source-qualified new-geometry sweep. The next planned controlled geometry study should use realistic width/height options at fixed couple count and pitch, with an explicit feasibility gate before expensive full-system solving.

Other Rev3 families worth reproducing on the refined architecture include cap/window emissivity, source terminal lead length and composition, interstage and solder-interface contact resistance, die attach thickness and thermal conductivity, external mounting temperature, and an admissible current/heat-load operating map.

## Verification, reproducibility and release limits

All **eight** V3.11 cases are separately registered, converged and independently audited, each retaining the **88 source-leg solutions** and **11,791 original ceramic TET4** spatial nodal field values. The no-PDE verifier reconstructs source lead Joule/heat flows, source Cu 58/80/88 thermal/electric multiport, all three TEC stage heat balances, bath energy, and **gas-species/pressure-specific Eucken/Knudsen conductances and four heat inputs** without calling the forward solver. Source V3.6 physics, Rev3 source, source CAD and existing cumulative report are unchanged.

An excellent global energy residual is necessary but does not validate each exposed gas patch's actual area or the three-dimensional spatial interface gradients. The present system is a physically useful **hybrid source-leg plus actual ceramic FEM**, not a complete full-volume 430-domain metal/TEC/gas PDE. The source's previously failed raw contact-gradient and global-mesh release gates remain unresolved.

Numerical evidence:
- [Eight complete registered operating points, original ceramic 3D nodal fields and source output](../data/v3_11_rev3_backfill_source_20261109/)
- [Rev3-inspired gas operating-point solver](../scripts/v3_11_package_gas_pressure.py)
- [Independent gas/TEC energy verifier](../scripts/v3_11_independent_backfill_audit.py)
- [Scientific source-vs-Rev3 regression checks](../tests/test_v3_11_backfill_source.py)
- [Original historical 38-page Rev3](../reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf)
- [Preserved cumulative 30-page current architecture assessment](../reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf)

**Near-term research plan:** First source-validate actual exposed gas paths and narrow-gap geometry, then conduct a bounded pellet cross-section/height sensitivity, followed by its **physically consistent** geometry/thermal-contact rebuild if it yields substantial meaningful design leverage. Each release must report cold ceramic T, die mounting T, electrical input, sink rejection, component-level heat flow, and physically interpretable limitations. The independent specialist LSDDTS detector simulator is not used and remains out of scope.
