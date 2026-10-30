# Plausible reference-device modeling policy (2026-10-30)

Internal implementation/source notes. The single current scientific document is the
[Revision 3 master](../reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf).
The authoritative [current project contract](../AGENTS.md) defines read-first order,
execution ownership and next milestones. The live master is continuously updated;
sealed historical PDF bytes, numerical archives and original gates remain immutable.

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

## Current next milestones

First implement bounded native-surface visibility/exchange from corrected source
faces, retaining the filled-core proxy as a comparator. Then run paired
mechanisms and contact/bypass/grade/reservoir hypotheses in the existing nonlinear
five-node package. The contract gives the required audits and the conditional
later 3D qualification path. OEM calibration and a large remesh are not prerequisites.

## Longer-term physics scope

**Integrated plausible thermal/electrical reference device**
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

**Engineering sensitivity and plausibility**
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

**Optional evidence and advanced detector physics**
- Improve empirical fidelity when measurements, vendor drawings or material
  properties become available. It is advantageous, not required for the
  plausible-reference-device milestone.
- Add `R(T,V)`, calibrated MCT bandgap/absorption, spectral window transport,
  noise, responsivity and D* in separate source-backed increments as useful.
  Without device-specific inputs, label results exploratory.

## Continuing deliverable

Improve the existing nominal/low-parasitic/high-parasitic scenarios, mechanism
comparisons and assumptions in the same Rev3 master, with heat budgets and
temperature/current/voltage/power plots. Keep genuine archived solid-only 3D
fields distinct from reduced transport and preliminary enclosure exchange.
Maintain the internal methods guides coherently within the existing resource budget.

## What must not change

Historical G1–G3b/G2d and later accepted or rejected evidence, exact archived
fields, all reported raw-flux failures, Rev2 and the sealed original 15-page Rev3
snapshot remain preserved. The live Rev3 is expressly authorized to evolve in place;
its historical PDF identity is recorded separately. Neither the raw bath<1% nor
the cold-interface<5% criterion
is retroactively relaxed; an exploratory result is not a numerical release.
Do not touch unrelated repositories, LSDDTS or existing protected snapshots.

**Continuation instruction:** Apply the authoritative current contract with this policy.
The earlier OEM-first document remains useful as an independent-validation
reference and source inventory, but its "next milestone must be OEM validation"
priority does not override this policy.
