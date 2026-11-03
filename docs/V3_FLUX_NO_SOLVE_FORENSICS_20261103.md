# V3 electrical numerical forensics — no new PDE or mesh

**Baseline:** Clean published ef1027e. The original failed conservative-flux producer, its saved data, the V3 R1 geometry, the 38-page Rev3, and the historical numerical gates remain protected.

## Scope and numerical status

This is source and saved-field analysis only. No new mesh, PDE solve, physical law, fitted material coefficient, thermal Gate C/D, or reconstruction of the missing mixed RT0 flux occurred. The prior P1 raw cut mismatch **81.241662%**, recovered-versus-P1 IV loss mismatch **0.769154%**, and surviving mixed-cell potential minimum **−2.652280858×10⁻⁵ V** remain FAILED.

The original control fields do not exist in the archive; archived summaries cannot support independent recomputation of their analytical L2 norms.

## New no-solve infrastructure

The independently versioned prospective writer is at tecooledmct/v3_flux_infrastructure_v2.py; the original sealed producer remains untouched. Separate namespaces p1, recovered_rt0, mixed_rt0 require seven archive entries each: mesh, potential, flux, residual, material_map, analytical_reference, metadata.

Preflight rejects a missing method/field, wrong namespace, duplicate path, invalid payload or existing directory before writing. Each file uses exclusive creation and SHA256 recording. If a failure occurs after the new directory is created, partial evidence remains with an INCOMPLETE marker; this is **fail-closed but not transactional atomicity**.

Five new tests passed, including duplicate-method-path rejection and no overwrite of existing output.

## Saved-field observations

A new script, scripts/v3_flux_no_solve_forensics.py, reads only saved L1 mesh, saved recovered flux, surviving mixed cell potentials and frozen physical coefficients. Its machine-readable output, including source SHA256 hashes, is data/v3_flux_forensics_20261103/saved_diagnostics.json.

| Observation | Result |
| --- | ---: |
| Mixed-potential minimum | −26.52280858 µV |
| Cells below old registered voltage floor | 501 |
| Minimum cell index | 203784 |
| Minimum cell domain | pin_finish |
| Minimum cell centroid (m) | (−0.0041651035, 0.0031989064, 0.002002625) |
| Nearest exterior face **centroid** distance | 2.498 µm |
| Worst cell max-edge/inradius proxy | 13.665 (93.1 percentile) |
| Recovered flux bulk dissipation at 1 V | 32.1364261101 W |
| Recovered flux finite-contact dissipation at 1 V | 2.1303697967 W |
| Recovered loss less P1 IV input | +0.2615525642 W |
| Relative discrepancy | 0.7691536318% |

The proximity metric is not the true point-to-surface distance. Cells adjacent to the minimum remain in pin_finish. This is evidence for investigating local boundary and resolution effects, **not proof** of their cause. Mixed RT0/P0 cell means need not obey a P1-like maximum principle on an arbitrary tetrahedral grid.

### Bulk loss by material region (unit-voltage numerical diagnostic, W)

| Region | Bulk loss |
| --- | ---: |
| film0 | 10.872899 |
| film2 | 9.790356 |
| tab88 | 7.351946 |
| lead9 | 3.138773 |
| Remaining regions | 0.982451 |
| Total | 32.136426 |

The largest finite-interface losses (W) were lead9/lead_land **0.385861**, lead9/lead_pin **0.371830**, joint4/film0 **0.221323**, tab88/joint4 **0.216854**, and film0/lead_land **0.200207**. All eleven are included in the machine-readable evidence.

All these values are from the recovered field, whose terminal current was constrained to P1. They are not independent mixed-solution losses, actual 1 A ratings, detector heat loads, or qualified electrical properties. The discrepancy against P1 IV does not by itself determine the independent mixed method's accuracy.

## Method-specific future protocol — proposal, not numerical authorization

- **Original CG P1:** Preserve the existing failed raw-gradient cuts and voltage floor. Do not retroactively mark PASS.
- **Equilibrated RT0 recovery:** Require conservative face continuity **and** analytic comparison, constitutive residual, correctly represented contact jump, independent spatial/loss accuracy, and refinement. Conservation enforced by construction is insufficient.
- **Direct RT0/P0 mixed:** Archive independently solved flux and cell potentials under unique immutable identifiers. Validate terminal current, mixed constitutive laws, contact voltage discontinuities, analytic benchmarks and physical loss convergence. Establish mathematically applicable cell-mean boundedness requirements prospectively; the old observed failure remains unchanged.
- **Future control archive:** Save full coordinates/elements, regional coefficients, exact reference potential/flux, residuals, numerical solution and quadrature weights for independent no-solve field-level L2 recomputation.

Before any new solver run, preregister all method-specific numerical limits, signed terminal definitions and accepted error norms, freeze full source and operator inputs, and have a separate read-only numerical reviewer inspect the no-solve infrastructure. This independent review is **NOT RUN** here.

## Verification and disposition

The new writer's five infrastructure tests passed under the existing pinned runtime. The saved-field forensic script completed without calling any numerical solver and reconstructed the previously independently reported failure values. No full regression, protected-hash audit or exact-commit CI result is claimed by this document.

**Gate status:** No-solve forensic report completed; method qualification remains STOP; mixed flux remains LOST; L2 and thermal C/D remain NOT RUN. Issue #2 remains OPEN. No update to the canonical Rev3 is warranted.

## Final local software and integrity verification

Observed 2026-11-03T02:40Z: existing pinned-runtime full pytest invocation (with the project\'s existing runtime/skips) completed **583 passed / 11 skipped** in 101.69 s; scoped new tests **6 passed**. The current-master validator returned True, archive verification returned “Verified independent geometry source/artifact ledger; prior evidence preserved”, and git diff --check passed. The frozen STEP SHA256 remains 5e46c10fb75713a9dffbc97c44a2b94ca23bee14a93df7f4c0c7c915eb761a73; Rev3 SHA256 remains 882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248. No separate independent model-assisted numerical review was available because the existing Codex session had exhausted its weekly quota. Exact-commit CI, if published, must be verified separately. The physical/numerical qualification status remains STOP.
