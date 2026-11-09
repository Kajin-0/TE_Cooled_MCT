# Active project scope — Three-stage TEC and TO-package electrothermal engineering

**Scope correction: 2026-11-09. This document is the active research priority, overriding any older “NEXT” directive inside historical V3.7–V3.10 milestones.** Historical results are retained; no source code or report is retroactively invalidated merely by this change of focus.

## Primary physical system

Develop a scientifically reproducible, inspectable model of the *three-stage thermoelectric cooler*, its interstage connections, local metal/ceramic and electrical contacts, trimmed terminal leads, die attach, 9-pin TO-66 package, cavity thermal pathways and the external mounting/heatsinking boundary. The engineering objective is to predict and understand **detector-mounting temperature**, **cold-side and hot-side stage temperatures**, **TEC voltage/current/input power**, **heat lifted and rejected**, **stage-by-stage heat and Joule budget**, **effective COP**, **thermal parasitics**, **practical drive point**, **construction/material sensitivity**, and **operating margins** as physical knobs are changed. Every conclusion must distinguish mathematical/numerical verification from validated hardware accuracy.

## HgCdTe scope boundary

The detector is a **passive thermal node / die / attach with a user-prescribed dissipated load**. Keep its geometry and realistic bulk thermal conductivity/heat capacity assumptions where applicable; bias power may be supplied as a user-defined external thermal load. Detector-specific bandgap, intrinsic carrier density, doping, mobility, contacts, current gain, absorption, quantum efficiency, responsivity, noise, and D* optimization **are NOT research priorities in this repository**. Existing V3.7 and V3.10 detector physics studies remain optional historic capability and are **not the default physics or the immediate next milestone**. Do not expand them without explicit user authorization.

**LSDDTS is the separately developed detailed MCT detector simulator.** Future coupling may pass a small, rigorously defined interface (detector/die mounting temperature, effective heat-transfer resistance or thermal impedance, allowable steady-state/transient load, perhaps external bias heat) to LSDDTS. **Do not inspect, modify, call, or integrate LSDDTS now**; no integration has been requested. No duplicate detector research.

## Next high-value numerical physics, prioritized

1. **TEC interstage thermal and electrical loss fidelity**: revisit physical copper formed-foil tabs 58/80 and three-foot return 88, local contact/landing resistance, solder geometry, ceramic current and thermal transfer, bias Joule power, and potential localized 3D metal/copper-field discrepancies. The present source CAD-derived multiport model is useful but not a fully solved 430-domain bulk-metal multiphysics PDE. The historical 3D coupon failures and source-contact gates must stay visible; improving physical fidelity is not the same as merely adding mesh complexity.
2. **Realistic, evidence-constrained TO thermal interfaces**: die attach and carrier, lead material and *trimmed* installed length, package pins/header, mounting/header contact area, interface pressure and mounting thermal resistance, internal gas conduction and enclosure radiation. Explicitly distinguish CAD facts, manufacturer's geometry/material ranges, and assumptions.
3. **Matched P/N thermoelectric stage constitutive laws and joints**: realistic paired stage material properties S(T), rho(T), k(T), and thermoelectric heat sources including Peltier, Thomson and Joule; sensitivity should respect correlated physical feasible grades, not only independent percentage scales. Existing P/N specimen analogs are not a qualified matched commercial material pair.
4. **Useful operating maps and cross-effects**: finite-source 3D ceramic and correctly coupled 88-leg steady states over a *limited registered* current, mounting temperature/resistance, detector heat load, internal gas-pressure, lead and joint-condition space. Report T_die, T_cold for stages, T_hot, TEC V/P, net heat lift, Q_hot, COP=Q_cold/P_TEC (define cold lift and parasitic inclusion), partial derivative sensitivities, and any stability/validity boundaries. Use matched-temperature or matched-heat comparisons where appropriate. Do not use apparent global-optimum labels without admissible rated current/voltage/temperature evidence.
5. **After credible steady state:** thermal capacitances, a time-dependent package/control response with sourced thermal properties and identifiable time constants. No fictional manufacturer dynamics.

## Defensible numerical and engineering release gates

- Show an explicit component heat-flow budget and electrical conservation for source stage, internal joints, cap/gas, die and external sink; audit energy independently from the forward solver.
- Provide sensitivity of detector temperature or TEC power to *each* physical knob, the precise operating condition, and chosen hypothesis interval. Do not call engineering scenario ranges confidence intervals.
- Distinguish four actual spatial ceramic FEMs + resolved nonlinear legs from a true full-volume metal/cavity coupled PDE; preserve geometrical and contact-fidelity limitations.
- Retain existing canonical report, all source data, numerically accepted/failed states and historic studies. Publish additive, stand-alone engineering results; only modify the cumulative report after a substantive, clearly traceable revision is warranted and after full-page figure QA.
- No broad or speculative runs, geometry churn or detector-paper reanalysis without a specific unresolved TEC/TO physical question and measurable engineering deliverable. Prioritize source material/boundary evidence and one-factor controls before larger expensive sweeps.

## Immediate next technical decision

**Study the physical plausibility and sensitivity of the formed-copper interstage thermal path and its solder/plating contacts, alongside the hot-side TO mounting interface.** Build on V3.4–V3.5 copper, lead and source geometry audits and V3.8 matched-temperature sink results. Narrow the physically admissible joint/contact parameter ranges before any further numerical series, and produce a component-level *thermal-resistance/heat-flow diagram and ranked sensitivity table*. This is a TEC/TO engineering deliverable, not a new detector model.

## References

- [V3.4 source-copper electrical and thermal multiport](V3_4_SOURCE_COPPER_MULTIPORT_20261108.md)
- [V3.5 terminal leads and interstage contact](V3_5_POWER_LEAD_AND_INTERSTAGE_CONTACT_20261108.md)
- [V3.6 TEC current and imposed detector heat-load envelope](V3_6_CURRENT_AND_DETECTOR_LOAD_OPERATING_ENVELOPE_20261109.md)
- [V3.8 P/N material and matched mounting power analysis](V3_8_REV3_MATERIAL_AND_FINITE_SINK_STUDY_20261109.md)
- [Original contact and geometry gate](V3_INTERCONNECT_ELECTROTHERMAL_20261102.md)
