# V3 original Gate B — fine-mesh face-resolved raw current diagnostic (no solve)

**Date:** November 6, 2026. **Baseline:** `e85832d0752eb0c8a96ba00fcc80511f9d85ebd6`. **Scientific verdict:** Original electrical **Gate B remains FAIL/STOP**; a strictly read-only reconstruction narrows the spatial and numerical patterns behind its 16-cut current ledger. **No original PDE, geometry, material/contact coefficient, terminal condition, threshold, Rev3 or historical failure was changed.**

## Why this is a new diagnosis rather than another synthetic benchmark

The prior [physical blocker-closure audit](V3_PHYSICAL_BLOCKER_CLOSURE_20261106.md) classified all 430 current source domain laws and 2,440 face laws as UNSET, and the [original Gate B cut triage](../data/v3_physical_blocker_closure_20261106/attempt01/gate_B_cut_triage.json) confirmed **13 of 16 original fine-mesh cuts fail** the preserved relative tolerance of **0.1%**. That tells us where the errors are but not how they arise on the geometric interface.

This diagnostic reuses the actual **28,691 original fine tetrahedra**, original `J_unitV_A_m2` cell-gradient field, exact original registered CAD boundary faces, face owner material IDs and the original immutable natural integrated contact-current ledger. It builds a face-incidence map of the saved tetrahedral mesh, orients every native interface triangle outward from the lower-numbered material region, and recomputes **both** adjacent cell-gradient currents independently. Across **1,574 registered triangular faces at 11 original material interfaces**, the sum of every independently reconstructed one-sided raw current reproduces the original stored cut-current values to within **4×10⁻¹³ of the 34.046304527 A unit-voltage drive current**. This verifies the analysis uses the actual saved field, not a replacement interpolation or an alternative contact-reaction current.

[Full source-backed face ledger](../data/v3_physical_blocker_closure_20261106/attempt01/gate_B_face_flux_diagnostic.json) and [read-only analysis script](../scripts/v3_gate_B_face_flux_diagnostic.py).

## Quantitative findings

| Original interface | Source face triangles | Original fine-mesh worst current-cut failure | Raw side-A current (A) | Raw side-B outward current (A) | Opposite-flow area on side A | Top 10% of triangles: share of absolute side-A flux |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **film0 → lead_land** | 204 | **85.6255%** | +4.8940 | −36.3285 | **35.19%** | **45.89%** |
| **joint6 → film2** | 94 | **81.5574%** | −35.2388 | +6.2790 | 0% | 15.95% |
| **joint4 → film0** | 94 | **79.8767%** | +36.2635 | −6.8513 | 0% | 20.89% |
| **film2 → pn87_solder** | 194 | **79.7556%** | −6.8925 | +36.6569 | 24.36% | 56.38% |
| **tab88 → joint6** | 104 | 52.2059% | −16.2721 | +33.0158 | 0% | 24.20% |
| **tab88 → joint4** | 104 | 46.7264% | +18.1379 | −31.9577 | 3.13% | 31.98% |
| **lead9 → lead_pin** | 160 | 30.015% | +35.6823 | −23.8272 | 0% | 46.63% |
| **lead9 → lead_land** | 158 | 29.173% | −36.9943 | +24.1141 | 0% | 45.34% |

The opposite material side uses its own outward normal. Thus the currents in the two columns should *sum* toward zero for local flux balance; they are not expected to have the same sign. The respective **weak/contact-integrated current** remains independently conservative in the original discretization and must not be substituted for either raw gradient-side current to satisfy Gate B.

### Distinct error mechanisms are suggested, not proved

**A. Concentration and local reversal, lead-land region.** At the worst cut film0→lead_land, **35.19% of registered interface area** has raw P1 normal current opposite the signed net side-A current. The absolute triangle-by-triangle current totals **1.74 times** its signed net, and the 10% most active triangles account for **45.89%** of absolute flow. Across all 204 faces, the raw outward side-to-side mismatch is **−31.4346 A**, despite the original weak contact term carrying **+34.0463 A**. Such reversal/concentration is compatible with true 3D crowding *or* poor mesh/gradient fidelity. It cannot be attributed solely to a sign convention.

**B. Large two-sided gradient disagreement even without current reversal.** On joint6→film2, side-A raw current is **−35.2388 A**, while the opposite outward raw current is **+6.2790 A**: the signed combined mismatch is **−28.9597 A** across 94 faces. On joint4→film0, the analogous mismatch is **+29.4122 A**. Both pairs have **0% side-A area carrying reverse-oriented current**. These cases demonstrate that explaining the Gate B failure *only* by reverse flow or a small population of extreme face fluxes would be incorrect. A nonconforming P1 cell-gradient normal current, local thin-film anisotropic spreading and unresolved geometry remain plausible contributors. The data do not distinguish them causally.

**C. Source-free/dead-end branches demand correct normalization.** Original joint5→film1 and tab88→joint5 are registered as zero-drive-current branches. Their signed raw currents are small, and the absolute sums can be much larger due to cancellation: **125.17×** and **10.81×** ratios, respectively. The division by a small *raw net* in these ratios is **not evidence of 125× a physical supply current**. Their original gate errors are still preserved as fractions of the **global unit-voltage drive current**, with the original zero-branch denominator handling.

**D. Cross-method interpretation.** The original R3.12–R3.17 manufactured P2 scalar benchmarks did not use this original 28,691-element coupon or its measured current-density field. P2's ability to represent analytical manufactured solutions does not imply that P2 automatically removes these physical/coupon current defects. Previous RT0 recovered-current work showed mathematical flux balance, but a recovered/current-reaction surrogate does not qualify the original required **raw one-sided bulk-gradient current**. The original FAIL stands.

## What is now testable

The existing saved-field evidence identifies two distinct implementation questions for a future one-attempt controlled numerical comparator:

1. Can the original coupon's actual thin-film/contact-side current be represented by a **flux-conforming approximation or validated reconstruction**, without replacing the original raw P1 Gate B test or relaxing its registered 0.1% criterion?
2. Can selected curved lead-land and film/solder interface regions resolve enough local geometry and gradients to make the unchanged raw cut test pass, while also preserving bounded voltage, intermaterial face ownership, and source-volume agreement?

The next work order should **not** blindly increase global tetrahedron count or use more synthetic FEM benchmarks. It should pre-register the actual original 16 cut observables, both signed side currents, the weak contact current, exact geometric interface faces and material tensors, local error/conditioning diagnostics, and independent accepted checks. The historical raw P1 Gate B outcome must remain FAIL regardless of a newer method's success; a corrected method may receive a distinctly named prospective gate only after a fair comparison and unchanged physical assumptions.

## Status and preservation

This diagnostic closes **one attribution subtask**: it independently verifies and localizes actual original cut-current failure patterns at the face level. It does **not** identify a unique numerical or material root cause, fix Gate B, assign a physical conductivity, or qualify any thermal result. Electrical Gate B remains FAIL/STOP. Thermal C/D remain NOT RUN. Issue #2 remains open, original source geometry/Rev3 is frozen, and all R3.3–R3.17 evidence remains unchanged.

The read-only implementation can be reproduced with the existing recovered FEM runtime and without launching a solver:

```bash
docker run --rm --network=none --cpus=3 --memory=3g \
  -v "$PWD":/work:ro -w /work tecooledmct-fem:26.2.1-recovered-20261105 \
  python -B scripts/v3_gate_B_face_flux_diagnostic.py --verify-only
```

The \`--verify-only\` option compares every reconstructed source field against the
published JSON receipt without writing. The default archival run exclusively creates
a new receipt and refuses to overwrite prior evidence. It never modifies historical PDE results.
