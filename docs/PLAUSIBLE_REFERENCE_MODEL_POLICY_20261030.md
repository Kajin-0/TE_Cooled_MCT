# Plausible reference-device modeling policy (2026-10-30)

## Authorized objective and priority

**The project goal is a physically plausible, useful multiphysics digital model of a
three-stage TEC-cooled HgCdTe detector in a TO-66 package. It is NOT an exercise in
reverse-engineering one vendor's undisclosed product, nor is OEM curve-matching a
prerequisite to useful engineering exploration.**

This policy supersedes the *priority ordering* of the 2026-10-30
`OEM_FIRST_VALIDATION_TRACK_20261030.md`, not its numerical results, provenance
or scientific caveats. We will fill incomplete construction/material data with
traceable engineering estimates and parameter ranges. Never present assumed
inputs as manufacturer measurements, and never use numerical agreement as proof
that a hypothetical internal construction matches a specific device.

The model should ultimately answer what a device engineer needs: How cold can the
detector plausibly get? What power is required? Where do heat leaks go? How
sensitive are results to the package, cooler, solder joint, leads, gas,
radiation, bias, and heat sink? What engineering change is most likely to help?

## Four input-provenance categories

1. **DOCUMENTED**: manufacturer dimensions or curves, measured property tables,
   public standards, peer-reviewed materials. Keep source, units, domain and
   specimen/product identity.
2. **ANALOG / ENGINEERING ESTIMATE**: plausible literature-grade surrogate,
   standard material behavior, typical fabrication dimension, or conventional
   interface law. Give rationale and a credible engineering range.
3. **INFERRED**: physically constructed topology or dimensions consistent with
   external constraints but not exposed by a vendor (e.g. 28/12/4 stage allocation
   or buried links). Label explicitly; offer variants when consequential.
4. **SCENARIO**: a selectable design/load/environment condition (e.g. heat-sink
   resistance, cavity gas/pressure, bias dissipation, thermal contact).
   It is not an observation.

If an input lacks evidence, do not leave the subsystem unimplemented by default:
select a plausible nominal hypothesis **with low/high alternatives**. Prefer
ranges that span a meaningful uncertainty, rather than false precision or
unjustified pseudo-confidence intervals. If an assumed quantity is responsible
for a major change in detector temperature, elevate it to a sensitivity study.

Manufacturer comparison is a **sanity check and optional constraint**, not an
optimization target that forces every unknown to fit the OEM curves. A large
mismatch is a warning about assumptions or missing physics to investigate and
report; it does not automatically halt development of a plausible synthetic
reference article.

## Physics and development priorities

**P0 — integrated plausible thermal/electrical reference device**
- Preserve the conformal 88-leg, three-stage 3D TEC, corrected nine-pin
  two-ear Kovar TO-66 header, ceramic stages, presolder, die attach and MCT.
- Choose and document a coherent nominal source-backed or analog
  temperature-dependent Bi-Te P/N grade model. Where source data end, either
  keep the scenario inside coverage or introduce an explicitly **assumed,
  bounded** continuation/new surrogate; never silently extend a measured curve.
- Specify reasonable electrical/thermal contact impedances, source-consistent
  Sn–Sb solder versus distinct unconfirmed TEC-to-header joint, and selectable
  stage geometry variants. Do not assume real internal routing is known.
- Integrate the cap/window, measured-or-inferred gas species and pressure,
  conduction, surface-to-surface radiation, electrical lead conduction/Joule
  heating, and realistic hot-side thermal resistance. Previously developed
  G3b enclosure concepts can be reused as **algorithms** only after the
  corrected geometry has new audited faces, rays and boundary conditions.
- Couple a simplified HgCdTe die heating model (bias and absorbed radiation as
  scenario inputs), giving temperature, voltage, heat budgets, currents and
  power consumption at useful operating points (e.g. 0.1–1 A, subject to
  nominal current and material-temperature validity). Do not confuse an
  imposed optical-like heat load with transmitted optical radiation.

**P1 — engineering sensitivity and plausibility**
- Sweep TEC stage split, material-grade analogs, contact thermal resistance,
  mounting/sink resistance, wire geometries, cavity backfill/pressure,
  radiation, detector dissipation and drive current.
- Report output envelopes: detector mean/max/min temperature, hot-side
  temperature, electrical input power, per-path heat flux, relative temperature
  shifts and sensitivity rankings. Distinguish variation from scenario priors
  versus true calibrated prediction uncertainty.
- Compare only matched conditions to public TEC/device specifications for
  gross plausibility; record disagreement rather than fitting away unknowns.
- Verify current/energy balance, geometry connectivity and solution convergence.
  Use goal-oriented temperature/voltage refinement for practical work. Existing
  stringent raw-gradient gates remain historically intact and mandatory for
  any **numerical-release claim** governed by the existing Rev3 release policy;
  they do not prevent explicitly qualified *exploratory/plausible-model* studies.

**P2 — optional evidence and advanced detector physics**
- Improve empirical fidelity when measurements, vendor drawings or material
  properties become available. It is advantageous, not required for the
  plausible-reference-device milestone.
- Add `R(T,V)`, calibrated MCT bandgap/absorption, spectral window transport,
  noise, responsivity and D* in separate source-backed increments as useful.
  Without device-specific inputs, label results exploratory.

## Near-term deliverable

A reproducible **nominal, low-parasitic, high-parasitic** set of integrated
operating scenarios, with assumptions table, coupled 3D field results where
computationally feasible, heat-budget Sankey/data, device temperature/current/
voltage/power plots, and a concise, candid statement of uncertain inputs.
Keep the existing simulation environment and practical resource budget.

## What must not change

Historical G1–G3b/G2d and later accepted or rejected evidence, exact archived
fields, all reported raw-flux failures, and the approved Revision 3 REVIEW DRAFT
remain preserved. Neither the old raw bath<1% nor cold-interface<5% criterion
is retroactively relaxed; an exploratory result is not a numerical release.
Do not touch unrelated repositories, LSDDTS or existing protected snapshots.

**Continuation instruction:** This policy is the newest primary user objective.
The earlier OEM-first document remains useful as an independent-validation
reference and source inventory, but its "next milestone must be OEM validation"
priority does not override this policy.
