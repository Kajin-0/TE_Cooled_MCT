# V3 numerical archive integrity and review-readiness — no-solve checkpoint

**Target:** The previously published [no-solve forensic checkpoint](V3_FLUX_NO_SOLVE_FORENSICS_20261103.md), commit `b51e1c575bbcad0d00459985cf4b2c08d3a06dd0`. This is a prospective source-code and synthetic-fixture data-integrity checkpoint, **not** a rerun or approval of the original coupon.

**Original results retained:** Raw P1 cut mismatch 81.241662% FAIL, recovered loss-versus-P1 input mismatch 0.769154% FAIL, surviving mixed RT0/P0 cell potential −26.5228 µV FAIL, independently solved mixed flux LOST, L2 NOT RUN, thermal C/D NOT RUN. Accepted V3 R1 CAD, the 824-solid STEP and 38-page Rev3 are unchanged. Issue #2 OPEN.

## Critical limitation discovered

The [previous method-separated writer](../tecooledmct/v3_flux_infrastructure_v2.py) only required seven named artifacts as arbitrary byte strings. It guaranteed neither typed array contents nor matching solver lineage. Its five original controls were correctly scoped to filename integrity, but were insufficient as numerical evidence.

A separately versioned [strict archive contract](../tecooledmct/v3_flux_archive_contract.py) now validates already-computed arrays **before** handing them to the previous exclusive writer. The frozen experimental producer is never imported or edited, and this validator cannot solve any PDE.

### Explicit technical checks

| Check | Prospective archived-data criterion | Qualification significance |
| --- | --- | --- |
| Three methods | Exactly `p1`, `recovered_rt0`, `mixed_rt0` with seven artifacts per method | Method isolation |
| Typed storage | NPZ numeric arrays; reject object/pickle, wrong dimensions, dtype, NaN/Inf | No arbitrary mislabeled field bytes |
| Units | Exact SI declaration for m, V, A, A/m², S/m, Ω·m, m³ and W | Unit metadata consistency |
| Mesh | Source bounding box in metres, positive element volumes, node and region validity, face-incidence uniqueness | Geometry/mesh consistency |
| Material tensors | Positive definite, symmetric conductivity and resistivity; reciprocal tensor products | Typed property map integrity |
| Method DOFs | CG trace-node versus RT0/P0 cell means, correct per-method vector and face-current dimensions | Discrete-field identity |
| Flux topology | Independently verified tetrahedral face incidence/orientation, opposite internal normal signs | Correct RT0 face-current indexing |
| Numerical consistency | Reconstruct RT0 cell residual and vector samples from signed face DOFs | Detect internally inconsistent archived flux |
| Execution lineage | Shared run/source/operator/mesh identities; appropriate per-method execution IDs, with recovery linked explicitly to P1 | Detect metadata mismatches within packet |
| Analytical controls | Numerically recompute potential and flux L2 errors from archived arrays and quadrature weights, compare with stored claims | Independent arithmetic replay *when real control fields are archived* |
| Coupons | Declare analytic references unavailable instead of fabricating analytic error norms | No invented qualification |
| Interruptions | Exclusive directory/file creation; incomplete marker and manifest-last publishing; reject bad hashes, missing/extra files, symlinks | Fail-closed retained evidence |

## Test provenance and limitations

All strict-contract tests use **synthetic fabricated arrays**, not original solver solutions. Their purpose is negative validation of the archive implementation. The tests include mismatched method and run IDs, inconsistent units and bounding boxes, incorrect material tensors and DOFs, nonfinite fields, wrong analytic norms, malformed RT0 orientation/incidence/residuals and J samples, tampering after publication, and an injected interrupted second write. An injected interruption creates an `INCOMPLETE` archive; the archive reader rejects it. The implementation retains partial evidence rather than pretending multi-file writes are atomic.

No historical missing mixed field or original control field has been recreated. The validator's independent L2 arithmetic can only be exercised on future **real archived control fields**. The source/operator SHA metadata are internal declared identities, not proof of a trusted solver execution. Likewise, reproducing an L2 norm against a stored reference does not prove the reference is analytically correct: a future release needs separate trusted reference formula/code identity and actual independent reference evaluation.

**Critical limitation:** This suite does not establish constitutive accuracy, terminal-current conservation against an independent source, solver convergence, contact-jump correctness, physical current rating or temperature accuracy. It also does not itself guarantee that a producing solver truthfully reports execution lineage; independent producer instrumentation and immutable external receipts remain necessary.

## Method-specific prospective qualification

- Original P1 raw-gradient flux: retain the historical ≤0.1% cut gate as **failed**. Neither recovery nor mixed flux can retroactively change this historical test.
- Recovered RT0: require finite interface/contact jumps, correct normal-current continuity, constitutive-residual norm based on the archived tensor/source law, analytic 3D flux accuracy and independently converged local Joule/contact losses. Do not use enforced conservation as a sufficient success criterion.
- Direct mixed RT0/P0: evaluate its own terminal input and `IV` work, its bulk/contact dissipations, normal traces, constitutive law and refinement. Its voltage-boundedness standard must be justified mathematically **before** execution, while preserving its previous measured failure.
- Future analytical controls: archive actual mesh, numerical fields, exact reference formula identity, independently evaluated reference arrays, integration weights, prescribed boundary/source conditions, and all error norms. The historical 16 controls are summary-only and remain limited in independent replay.
- Seal implementation, operator, constraints, contact/source coefficients and method-specific gates **before** any new control. A future study must specify quantitative acceptance limits prospectively and perform a separate immutable review prior to authorizing solves.

## Reviewer disposition and release decision

**Internal code/fixture checks: PASS for prospective archive *structure and self-consistency* only. Independent model-assisted numerical review: NOT RUN. Physical numerical qualification: STOP.**

The independent project auditor remains unavailable because the existing `sim:0.0` Codex session has exhausted its weekly usage allocation. No second reviewer was represented as having examined this checkpoint, and authorship/testing by the same implementation process does not count as independent sign-off. A separate reviewer must assess the full method protocol, mathematical weak forms, contact/interface orientation and analytic reference identity, and must retain authority to reject the successor numerical experiment.

**No new PDE, mesh, thermal, coupled calculation, fitting, geometry or Rev3 modification is authorized or produced by this work.** The original failures and their thresholds remain unchanged.
