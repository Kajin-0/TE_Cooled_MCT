# V3 physical-model blocker closure — numerical campaign reset

**Audit date:** November 6, 2026. **Baseline Git commit:** `b4420e3cb478370340464594aad68b4c3b3c69d8` (R3.17).  
**Verdict: physical electrothermal readiness STOP.** This is a **no-solve evidence and acceptance-gate audit**, not a new FEM milestone or a material-law release. No CAD geometry, tetrahedral mesh, earlier numerical result, finite-contact witness, source measurement, material coefficient, electrical boundary condition or canonical Rev3 page was modified.

[Machine-readable audit and pinned source SHA-256 receipts](../data/v3_physical_blocker_closure_20261106/attempt01/readiness_audit.json) and [strict read-only audit implementation](../scripts/v3_physical_readiness_gate.py).

## Executive decision

We have made real engineering progress: the accepted R3 geometry is conformally meshed into 430 domains; native source contacts are carried into positive-volume tetrahedra; a difficult regional scalar solver is usable with an appropriate preconditioner; P2 basis and mathematically controlled finite interface conditions have passed. Those are **software and discretization capability milestones**, not experimental validation of the TEC-cooled MCT detector.

**Stop creating additional manufactured scalar-diffusion variants.** The next accepted activity must close an explicit *physical-model or numerical qualification blocker* using the frozen original coupon and its actual, previously registered acceptance criteria.

The original **electrical Gate B FAIL** remains the immediate stop condition. Subsequent thermal Gate C and electrothermal Gate D remain **NOT RUN**. Full-device electrical, thermal and thermoelectric operating points remain **NOT QUALIFIED**.

## 1 — Direct findings from currently accepted source files

| Physical-model gate | Verified current evidence | Decision |
| --- | --- | --- |
| Source geometry topology | 430 R3 analysis domains; 2,440 registered native faces; 378 preserved finite-contact witness records | **Geometric structure available** |
| Global 3D discretization | R3.8: 1,043,314 saved tetrahedra, 156,765 nodes, all 430 regions geometrically qualified; R3.9: 1,010,119 tetrahedra | **Geometric PASS; predictive FEM quality unqualified** |
| Element-quality burden | R3.9: 241,754 / 1,010,119 (**23.93%**) below normalized shape threshold q = 0.05; global nonadjacent overlap not audited | **Numerical accuracy risk** |
| Current 430-domain constitutive assignment | **430/430 domain entries** have `law_status=UNSET` and `solver_ready=false` | **No release-ready volume law set** |
| Current R3 boundary law assignment | **2,440/2,440 face entries** have `law_status=UNSET` | **No release-ready boundary law set** |
| Original V3 coupon electrical Gate B | Fine-mesh worst raw current-cut mismatch 85.6255%, required ≤0.1%; boundedness FAIL | **FAIL / STOP preserved** |
| Original coupon power closure | Relative error 9.9187×10⁻¹³, required ≤0.5%; resistance refinement change 0.315803%, required ≤1% | **Two subordinate checks PASS; cannot override the failed raw-cut and boundedness tests** |
| Actual thermoelectric electrical/thermal transport | Full 430-domain PDE not run; no accepted full device terminal-to-terminal V–I, heat budget or detector temperature | **NOT QUALIFIED** |
| Reduced TEC model | Previously archived conditional 200 K crossing at ~0.291139 A and 0.561973 W with assumed above-300 K continuation and an unlike 28/12/4 stage model | **Useful planning study, NOT physical validation of V3 29/11/4 stage FEM** |

Source evidence is the original [V3 local electrical Gate B report](V3_INTERCONNECT_ELECTROTHERMAL_20261102.md), [independent coupon review](V3_INTERCONNECT_INDEPENDENT_REVIEW_20261102.md), [R3.8 global tetrahedral qualification](V3_R38_GLOBAL_TETGEN_20261105.md), [R3.9 global shape-quality audit](V3_R39_GLOBAL_QUALITY_20261105.md), and [historical reduced-input evidence audit](PHYSICAL_INPUT_QUALIFICATION_20261101.md). Their earlier PASS/STOP records are preserved unchanged.

### Critical registry lineage issue

The old requirements file `data/v3_global_mesh_gate_20261103/physics_law_requirements.json` enumerates **438 domains / 2,456 faces** and explicitly records `solver_ready=false`. It belongs to an earlier geometric representation. The current accepted R3 source contains **430 domains / 2,440 faces**, with new explicit dielectric sleeve domains and updated effective axial pin-finish regions.

Therefore the old 438-domain registry cannot be silently reused as a law table for the 430-domain mesh; nor can existing bulk property hypotheses be silently treated as released effective tensor, gas, contact or thermoelectric laws. The exact 430-domain source metadata has already been enumerated without filling any of those values. **The active 430-domain physical law release remains STOP.**

This is a source-schema mismatch, **not evidence that the geometry is wrong** and not a reason to re-mesh the 430 domains.

## 2 — Gate B failure: what is known, what is not

The frozen independent V3 coupon is the net88/lead9 conductor path between **two internal cut terminals**, not the full TEC electrical circuit. The original preregistered B criterion requires both contact-law flux and **raw one-sided finite-element bulk-gradient current** to agree within **0.1% of the drive current** on all registered cuts.

| Gate B measurement | Archived fine coupon | Required |
| --- | ---: | ---: |
| Coarse/fine tetrahedra | 10,819 / **28,691** | Both under 250,000 |
| Worst raw current cut: film0 → lead_land | **85.6255%** mismatch | ≤0.1% |
| Worst accepted interface-current absolute drive for unit voltage | 34.046305 A | Diagnostic, not a device rating |
| Interface contact-integrated current | 34.046305 A | Conservation checked |
| Raw one-sided film0 current | **4.893986 A** | Must agree with contact current |
| Raw opposite-side current | **−36.328540 A** | Signed outward convention |
| Positive / reference terminal errors | **0.836320% / 3.322308%** | ≤0.1% |
| Voltage minimum at unit drive | **−7.3514×10⁻⁷ V** | Not below −1×10⁻⁸ V |
| Fine total CAD-volume representation error | **−1.64881%** | Curved geometry visibly under-resolved |
| Fine lead9 volume error | **−2.38232%** | Explicit geometry uncertainty |
| Resistance coarse/fine change | 0.315803% | ≤1%; PASS |
| Discrete `IV − losses` relative error | 9.9187×10⁻¹³ | ≤0.5%; PASS |

The [independent reviewer](V3_INTERCONNECT_INDEPENDENT_REVIEW_20261102.md) already reconstructed P1 element gradients, conductivity assumptions, signed face normals and all 11 material-interface cut integrals to near machine precision. **This rules out several simple bookkeeping explanations.** The face/contact weak form and algebraic power balance can be conservative while raw P1 bulk-gradient flux fails the *different* original acceptance requirement.

**What remains unresolved:** the relative contributions of (a) unresolved geometric curvature and thin-layer spreading, (b) non-flux-conforming P1 interpolation, (c) mesh anisotropy and local gradients, and (d) the physical suitability of the hypothetical laminate/contact-law tensors. No single mechanism is proved to account for the full 85.6255%.

Do not: silently replace raw current with contact reactions, change the denominator, relax the 0.1% limit, fit artificial material resistance to force agreement, reinterpret the original FAIL as PASS, or treat synthetic R3.17 currents as a retest of the original coupon.

### Read-only prioritization from all sixteen archived current cuts

The first bounded **P0 source-data triage was completed without a PDE solve** using
[the original fine and coarse saved Gate B field receipts](../data/v3_physical_blocker_closure_20261106/attempt01/gate_B_cut_triage.json)
and the [reproducible cut-ledger reader](../scripts/v3_gate_B_cut_triage.py).
It covers **all 11 material interfaces, both terminal cuts and three declared interior plane cuts** using the same original \`gate_error\` and 0.1% limit. This does not remeasure gradients; the original independent field-level gradient reconstruction already exists in the November 2 reviewer record.

| Comparative cut-qualification metric | Read-only result |
| --- | ---: |
| Registered cuts (11 interfaces + 2 terminals + 3 interior) | **16** |
| Fine-mesh cuts exceeding the original 0.1% gate | **13** |
| Fine-mesh cuts meeting original 0.1% gate | **3** |
| Cuts improving on the fine mesh versus coarse | **13** |
| Cuts worsening on the fine mesh versus coarse | **3** |
| Worst cut (film0 → lead_land) | **145.216% coarse → 85.6255% fine** |
| Next highest: joint6 → film2 | **81.5574% fine** |
| Next highest: joint4 → film0 | **79.8767% fine** |
| Next highest: film2 → pn87_solder | **79.7556% fine** |

The three cuts **worsening** with refinement are tab88 → joint4 (**46.523% → 46.726%**), lead9 → lead_land (**25.553% → 29.173%**), and joint5 → film1 (**0.503% → 1.097%**). Both tab88 interior plane cuts pass by large margins, and lead9_mid passes at **0.061289%**.

**Decision:** Focus any permitted subsequent physical-field attribution on the original coupon's thin laminate / solder-to-film / curved lead connection cuts, while retaining the complete 16-cut gate. The concentration of mismatch is **consistent with**, but does not conclusively prove, unresolved local P1 flux, anisotropic film spreading or curved geometry. Do not infer an identifiable material coefficient from this ledger. No numerical model, input law, acceptance threshold or physical gate status changed.

## 3 — Material and boundary-condition evidence inventory

The following classifications refer to **model-readiness**, not to whether generic published property numbers exist:

| Parameter class | Evidence currently available | Missing qualification |
| --- | --- | --- |
| P/N thermoelectric legs | Research specimen data over 40–300 K and prior conditional extrapolated reduced-network studies | Source-grade correspondence, V3 29/11/4 allocation, transport \(S(T),\rho(T),k(T)\) within demonstrated temperature range, Thomson compatibility, anisotropy and uncertainty |
| Cu, Au, Ni, Ti, barrier layers, solder | Literature or supplier ambient bulk analogues plus selected coupon scenarios | As-fabricated plating/foil transport, layered effective parallel/normal tensors, solder-specific data, T-dependent thermal/electric limits |
| Composite wedge and layer stacks | CAD source-to-effective-layer mapping, including R3 volume 410's four original sublayers | Defensible effective tensor and interface double-count prevention; no blind bulk Cu/Au replacement |
| HgCdTe photoconductor | Geometric material identity and source contact registry | Doping/composition/temperature-dependent transport, device resistance and bias, contact law, detector thermal dissipation |
| Finite contacts | 378 geometric witness records; original coupon synthetic numerical contact scenarios | Physical area-resistance and area-thermal resistance, material-pair/temperature dependence, pressure/bond quality and uncertainty |
| Native gas/radiation | Registered cavity geometry and earlier conditional gas/bath research | Actual fill composition/pressure, accommodation, temperature regime, emissivities, radiation exchange and seal assumptions |
| Electrical terminals / heater loads | Geometric pin1/pin7/pin8/pin9 face tags and named coupon cut terminals | Signed full-device drive/reference assignment, detector-bias boundary, source/current closure, applied heat load and sink condition |

For source illustration only, the current R3 metadata marks `p_HgCdTe_photoconductor` (volume 408), `det8_wedge_foot` (410), `TEC_lead9` (416), and `detector_bond8` (420) as **`law_status=UNSET`**. The wedge foot is a composite, not an assigned homogeneous material.

The four registered *external package pin* CAD faces are pin1=2414, pin7=2418, pin8=2422, pin9=2426. These are **geometric terminal candidates, not assigned electrical boundary conditions**. The original Gate B terminals are *different, internal coupon cut surfaces*. Confusing them would produce a physically invalid electrical model.

## 4 — Ordered blocker-closure gates, with stop conditions

**P0 — Original Gate B field/flux/geometry attribution (highest priority).** Freeze the original coupon CAD registry, exact two original meshes, coefficients, solver fields and previously registered numerical limits. Perform a read-only reconstruction of the fine-mesh cut-current ledger, power/resistance balances, local mesh facets and current normal orientations, with per-cut error severity; do not call a PDE solver. This may confirm the known failure and localize contributors but cannot by itself pass B. A prospective *single, separately registered* method comparison may be authorized only if it retains the original raw-current criterion, explicitly demonstrates better local resolution or mathematical flux conformity, uses independently generated comparator/negative controls, and includes all registered cuts, terminal boundedness, mesh refinement and power closure. A weaker redefined criterion must be described as a **new method-specific experimental gate** without changing original Gate B. **Stop** on missing source provenance, invalid field readback, error worsening, violated interfaces or failure to improve the actual registered worst cut.

**P1 — R3 430-domain physical law-release ledger.** Build an assignment table keyed by exact **domain ID**, source physical material/layer stack, temperature and parameter validity range, anisotropy, model family, evidence class (measured/documented/analogue/hypothesis/unknown), uncertainty and source citation. Build a face-law ledger keyed by the actual **2,440 CAD face tags**. Distinguish identity/geometry from physical values. Do not assign constants opportunistically to make a solver runnable. **Stop** for any unresolved series-connected electrical region, source-bearing detector material, TE leg, critical contact or applied boundary.

**P2 — Physical electrothermal subassembly, only after P0/P1 readiness.** Choose a real TEC P/N couple, its solders, metallizations, two ceramic heat paths and true driving electrical terminals, including the thermoelectric coupling and Joule heat. Use explicit signed conservation in current and heat and a verified hot-side/cold-side boundary. Register acceptance before running: (i) no under/overassigned source facets, (ii) source/terminal current closure independently integrated to ≤0.1% for a declared mesh-appropriate current representation, (iii) thermal energy balance ≤1%, (iv) two-level comparable mesh solution tolerance and source temperature-range adherence, (v) no hidden effective contact/heat partition. These are **proposed future acceptance thresholds**, not achievements or substitutions for the original Gate B criteria.

**P3 — Full-package physical multiphysics.** Only after subassembly physical current/heat closure, release the 430-domain material/face schema, verify global mesh accuracy and nonlocal overlaps, couple TEC leg transport, bypass heat, gas and radiation, and calculate detector stage temperature and full terminal V–I. Validate against independent measurements/OEM specifications **without fitting the same parameters to the validation target**. This gate is blocked today.

### November 6 update: one prospective P2 method comparison ran and STOPPED

The original coupon's first explicitly registered, same-geometry P2 raw-gradient
experiment has now been completed once. See the [one-shot P2 engineering report](V3_GATE_B_ORIGINAL_P2_CORRECTION_20261106.md) and
[source-hashed 16-cut receipt](../data/v3_gate_B_original_P2_20261106/attempt01/manifest.json).
It reduced worst raw-cut error **85.6255% (original P1) → 8.0993%
(prospective P2)** but still failed **11/16 cuts** and worsened
the voltage lower bound to **−9.14946×10⁻⁷ V**. The original
P1 Gate B FAIL is not changed. Independent saved-field re-integration
reproduced native contact/terminal currents; no P2 mesh convergence,
physical material release or coupled TEC physics was demonstrated.
**The P2 attempt is now STOPPED; no iterative solver/mesh follow-up
is authorized by this receipt.**

## 5 — Anti-churn execution contract

A new milestone is justified only when it produces **at least one** of:

- **Failure attribution** that measurably isolates or rules out a specific named Gate B mechanism;
- **An accepted physical property or boundary condition** with provenance, validity domain and uncertainty;
- **A verified physical conservation closure** at an explicitly declared independent cut/terminal/heat port;
- **A decisive STOP** preventing a false physical claim or a redundant re-run.

The next task is **not** R3.18 synthetic contact test. No additional P1/P2 manufactured examples, cosmetic mesh q changes, or indefinite solver benchmarking should be launched. No simultaneous campaigns. Keep a compact running ledger with old status, new measured evidence, acceptance criterion, next decision and whether the original physical blocker was actually closed.

**No additional compute hardware or Codex capacity is required** for the current no-solve, source-provenance phase.

## Archive and result

This audit intentionally **closes no physical Gate B/C/D criterion**. It replaces unsupported readiness assumptions with an explicitly versioned source-backed STOP and a bounded, reviewable route to the next qualifying experiment. The historical 438-domain registry, original failed coupon and all R3.8–R3.17 430-domain numerical demonstrations remain unchanged. Original 824-solid STEP, 38-page canonical Rev3 and issue #2 remain protected.

To reproduce without a PDE solver:

```bash
python3 scripts/v3_physical_readiness_gate.py
python3 scripts/v3_physical_readiness_gate.py --out /tmp/new_readiness_receipt.json
```

The receipt writer refuses to overwrite an existing path. Its assertions fail closed if the source counts, Gate B status, stored mesh identity or constitutive readiness change unexpectedly.
