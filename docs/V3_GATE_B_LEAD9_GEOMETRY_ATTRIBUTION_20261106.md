# V3 Gate B — read-only original lead9 P1/P2 interface shape and flux attribution

**Date:** November 6, 2026. **Baseline:** `e4f661108bba8805f19a8f7425a97ea4623da92e`.  
**Scientific outcome: diagnostic PASS; Gate B remains STOP.** No new PDE, material-law variation, mesh generation/optimization, numerical solver tuning, or change to the original acceptance thresholds was performed. This work examines the **original net88/lead9 Gate B 28,691-TET4 coupon** and the **one previously stopped 58,993-DOF P2 same-geometry candidate**.

[Source-hashed diagnostic JSON](../data/v3_physical_blocker_closure_20261106/attempt01/lead9_shape_attribution.json) and [strict no-solve source](../scripts/v3_gate_B_lead9_shape_attribution.py). The immutable original P1 and P2 sources/results are preserved at their historical paths and [the first registered P2 STOP](V3_GATE_B_ORIGINAL_P2_CORRECTION_20261106.md).

## Question investigated

After the single prospective P2 correction, the two most serious remaining raw current-cut mismatches were

- **lead9 → lead_land:** **8.09930%** relative error on native CAD face tag **43**;
- **lead9 → lead_pin:** **6.85291%** relative error on native CAD face tag **47**.

Both exceed the preserved original **0.1%** current-cut tolerance by an order of magnitude or more. The objective was to determine whether these failures are concentrated in severely low-quality tetrahedra or a few isolated interface triangles, rather than assuming a new mesh campaign is warranted.

The original saved P1 cell-current density, saved P2 field coefficient vector, all original anisotropic material tensors, and the registered two-sided CAD face/owner mapping are used without modification. The diagnostic independently reconstructs the exact original adjacent tetrahedron identities, outward normals, **P1 raw one-sided flux** and **P2 raw quadratic-gradient flux** at each original triangle centroid. It also reintegrates the original finite-contact P2 face current from native globally indexed per-material edge fields.

All 318 signed P1/P2 face currents sum to precisely the original archived 158- and 160-triangle interface integrated currents within the source-level check tolerance \(10^{-11}\) relative to the one-volt drive current.

## Normalized tetrahedron mean-ratio criterion

For one actual linear tetrahedron, the normalized mean-ratio shape score is

\[
q = \frac{12(3V)^{2/3}}{\sum_{i<j}\lVert\mathbf x_i-\mathbf x_j\rVert^2}.
\]

This score gives \(q=1\) for an equilateral regular tetrahedron and tends to zero as the element collapses. For each original source interface triangle, the diagnostic records the smaller \(q\) of its **two immediately incident geometric tetrahedra**, the greater of their longest-edge/minimum-altitude ratios, and both independently reconstructed signed fluxes. These quality measurements characterize the exact cells used in the original one-sided gradient calculation, not an unrelated regional mesh average.

## Quantitative findings

| Original physical face | lead9 → lead_land | lead9 → lead_pin |
| --- | ---: | ---: |
| Source CAD face tag | **43** | **47** |
| Registered native interface triangles | **158** | **160** |
| Original P1 relative raw-current cut error | **29.17271%** | **30.01540%** |
| Existing P2 relative raw-current cut error | **8.09930%** | **6.85291%** |
| Minimum adjacent tetrahedron mean-ratio \(q\) | **0.175304** | **0.214508** |
| Median smaller-side mean-ratio \(q\) | **0.463442** | **0.499300** |
| Adjacent contact area with \(q<0.05\) | **0%** | **0%** |
| Adjacent contact area with \(q<0.1\) | **0%** | **0%** |
| Adjacent contact area with \(q<0.2\) | **1.3%** | **0%** |
| Highest local tetrahedral longest-edge/altitude | **16.11** | **13.10** |
| Median local longest-edge/altitude | **5.04** | **4.88** |
| P1 gross absolute two-sided raw mismatch | **12.88025 A** | **11.85514 A** |
| P2 gross absolute two-sided raw mismatch | **3.95207 A** | **2.96619 A** |
| P2 *signed* integrated two-sided raw mismatch | **−3.88212 A** | **+2.96470 A** |
| Fraction of gross P2 mismatch in 10% most discrepant interface triangles | **22.98%** | **20.89%** |
| Signed P2 finite-contact integral | **−33.842252 A** | **+33.842252 A** |

**Important:** The source-current unit-voltage values are numerical coupon diagnostics, not rated detector or TEC drive currents. The one-sided gradient mismatch is a nonconforming flux diagnostic, not actual charge creation at a contact. The original contact-integrated weak formulation still conserves its own interface and terminal reactions.

### Independent source CAD area check

The original registry lists a **circular physical contact face area** of \(3.14159265358979\times10^{-8}\,{\rm m}^2\) at **both** face tags 43 and 47. The actual polygonal TRI3 surfaces in the archived fine mesh have area \(3.13836382911380\times10^{-8}\,{\rm m}^2\) (face 43), and essentially the same value at face 47. This is a **−0.102777%** saved-mesh surface-area discrepancy relative to original CAD.

This discrepancy is slightly larger than the **0.1% raw-current gate tolerance** *when expressed as an area percentage*, so geometric-area fidelity will matter for final strict qualification. However, a 0.103% area difference by itself cannot explain the currently observed **6.85–8.10%** raw current errors under an assumed uniform current-density model; local fields and numerical approximation may amplify geometric effects, but that amplification has **not** been demonstrated. The current mismatch remains a separate unresolved numerical problem.

### Distribution of the residual mismatch

Neither interface has a single original incident tetrahedron with \(q<0.1\), so the original *extremely poor-shape-element* hypothesis is **not supported for the source face-adjacent cells**. The top 10% most discrepant triangles contribute only 20–23% of the gross absolute two-sided flux disagreement. There is some spatial concentration, but **the remaining error is distributed broadly rather than being almost entirely driven by a few extreme triangles**.

The two-sided P2 gradient traces are still non-flux-conforming under the original finite-resistance weak interface law. Although the P2 voltage field produces a more accurate approximation than P1, pointwise or integrated raw gradients are not constrained to equal the interface-law reaction on every discrete triangle. That mathematical distinction is a plausible *structural* source of the diagnostic discrepancies, but is not yet a measured causal partition between polynomial order, physical geometry and constitutive assumptions.

A positive measured association between \(\log_{10}q\) and \(\log_{10}\) face mismatch is present in this dataset (about 0.56 for lead_land, 0.52 for lead_pin). This is **not evidence** that improving \(q\) will improve the cut current: face area, orientation, interface localization and higher flux can confound the correlation. We do not use that statistic to justify quality-driven remeshing.

## Decision, qualification limits and the next engineering gate

**P0 attribution subtask achieved:** reproduced actual native P1/P2 lead9 interface currents, established local incident element quality, quantified mismatch concentration, and ruled out *extremely low mean-ratio shape quality in the immediately adjoining tetrahedra* as an adequate standalone explanation for the observed 6.85–8.10% residual error.

**No original gate closed:** Existing P1 Gate B remains **FAIL/STOP**, and the distinct one-shot P2 candidate remains **STOP**. The original P2 voltage boundedness also failed, and this audit did **not** investigate or resolve that. No P2 spatial mesh refinement comparison, anisotropic-tensor validation, physically measured contact resistivity, or new electrical solve was performed.

**Specific next decision:** Prefer a bounded, independently checkable **current-operator/interface consistency and geometry-curvature feasibility analysis** before any new FEM correction. That would compare the actual original weak-contact flux density with raw one-sided P2 flux on each saved face, identify how much of the mismatch is systematic rather than spatially concentrated, and qualify whether boundary geometry can meet a fixed 0.1% criterion. Such a read-only comparator must not substitute weak reactions for raw current or relabel an original failure as PASS.

Do not launch a general mesh-quality campaign or another P2 solve solely on the basis of mean-ratio quality. A new physical solve, material-law update or remesh requires a separate, prospective gate with a demonstrably new causal hypothesis, source provenance and an explicit stop criterion.

Original 824-solid physical STEP, frozen 38-page canonical Rev3, 430-domain source BREP, original coupon fields, all R3.3–R3.17 records and historical failures, and issue #2 remain unchanged. **Electrical Gate B FAIL/STOP; prospective P2 STOP; thermal C/D NOT RUN. Codex usage unchanged.**
