---
name: physical-plausibility-audit
description: Independent evidence-backed physical audit of TE_Cooled_MCT geometry, electrical topology, material properties, junctions, boundary conditions and device plausibility before releasing or rebaselining any physics. Use after catastrophic model errors or whenever a builder infers an unmeasured parameter.
---

# Independent physical plausibility audit

This is a **read-only, adversarial engineering review**, not another simulation campaign. Follow the current root AGENTS.md and docs/PHYSICAL_PLAUSIBILITY_AUDIT_PROTOCOL.md. The dedicated custom Codex role is .codex/agents/physical-plausibility-auditor.toml.

1. Freeze the exact **review target**: commit, files, CAD instance, physical assumptions and claims. Read the root contract, chronology, current geometry specification and relevant code. Never assume earlier findings apply unchanged to a new design.
2. Independently consult original manufacturer diagrams and real-world assemblies, inspect the figures, then try to *disprove* the inferred construction using at least three relevant physically distinct examples when available. Record which sources are product-specific and which are analogs.
3. Map each critical parameter through documentation, code, physical geometry, mesh/material/boundary and reported results. Independently test SI units, tolerance closure, electrical return/shorts, supports and joining process, conductor R/J/Joule, parasitic G, material-data domains, conservation and manufacturing constraints.
4. Explicitly challenge unmeasured stage connectors and return wires: 89 connected mathematical Cu nets do not establish real manufacturability; the shortest-looking trace may not close the hot-side circuit. Check electrical and thermal trade-offs.
5. Distinguish physical-design approval from CAD, solver, regression and product-curve gates. A critical failure yields **STOP**, however good the plot appears. A genuine plausible synthetic alternative may be **CONDITIONAL** with bounds and an explicit closure test, without exact OEM reconstruction.
6. Produce the standard review packet and tell the builder exactly what blocks further interpretation. Never edit files, clear failed gates, silently run experiments, invoke another agent, or interrupt the VPS sim:0.0 pane.

**Prior preventable failures to screen:** 1,000x CAD length errors (and 10^9 volume implications), wrong 0.44 mm pins and TEC pin wiring, unrelated vendor specs conflated, arbitrary free-standing interstage copper structures, unmeasured 28/12/4 or 29/11/4 split, 300–390 K transport extrapolation and unqualified contact, gas or full-package field.
