# V3 Gate B — one-shot P2 correction on the original electrical coupon (STOP)

**Date:** November 6, 2026. **Baseline:** `7312b55cfe4608d1887700529b2b14d41367bb78`.  
**Scientific verdict:** **FAIL/STOP for the prospective P2 same-mesh electrical current-cut and voltage-boundedness gate.** P2 markedly improves the original P1 raw one-sided gradient currents but **11 of the original 16 registered cuts still fail** the 0.1% gate; voltage undershoot also becomes larger. The historical original **P1 Gate B FAIL/STOP is unchanged**. No thermal Gate C/D simulation was performed.

[Complete preregistration, original source hashes, saved P2 coefficient array, results, stdout, and independent readback](../data/v3_gate_B_original_P2_20261106/attempt01/manifest.json). Implementation: [one-shot original-coupon P2 assembly and raw current evaluation](../scripts/v3_gate_B_p2_coupon_attempt.py), [independent saved-field face-current auditor](../scripts/v3_gate_B_p2_saved_field_audit.py).

## 1. Scope: the actual historical coupon, not a synthetic fixture

The original V3 net88/lead9 electrical coupon remains the **same** fine geometric mesh and 105 native CAD face tags:

| Registered source parameter | Actual unchanged candidate |
| --- | ---: |
| Original source tetrahedra | **28,691 TET4** |
| Original geometric source vertices | **9,272** |
| Original region-separated P1 scalar DOF | **10,329** |
| New region-separated P2 scalar DOF | **58,993** |
| Free P2 DOF | **57,227** |
| Real CAD contact source triangles | **1,574** across 11 material interfaces |
| Real external CAD triangles | **16,164** |
| Original coupon physical regions | **12** |
| Applied coupon potentials | **1 V** at original PN87/SnSb internal cut, **0 V** at original pin9 Ni/finished end |
| Bulk tensors | **Unchanged original NOM**, including anisotropic 15-µm laminate and 3.5-µm pin finish |
| Electrical interface contact resistance | **1×10⁻¹¹ Ω·m²** (original NOM assumption, not measured) |
| Source original STEP and registered BREP | **Unchanged** |

This candidate does **not** use the complete 430-domain physical R3 source and does not purport to model the full TEC. It uses the original, previously failed, independently audited 28,691-TET4 coupon with the **same** assumed material/contact laws and electrode definitions. No geometry modification, mesh refinement, conductivity fitting, adjusted terminal assignment or relaxation of registered limits occurred.

### Pre-registered P2 method

Each tetrahedron retains its original linear geometric mapping, but its potential field uses a **10-node quadratic Lagrange basis**: four source vertices and six globally unique, **region-separated** edge DOFs. Interface field traces remain distinct across different materials; they are coupled with the **same original finite-contact area resistance**, integrated using a degree-5 seven-point triangular rule. P2 bulk stiffness uses 11-point degree-4 tetrahedral quadrature and original anisotropic conductivity tensors.

Raw P2 electrical current is **\(\mathbf J=-\boldsymbol\sigma\nabla V\)**, with the one-sided gradient evaluated at each original interface triangle centroid. Because the P2 gradient is linear within each original TET4, the centroid gives the **exact planar-triangle integral of that element's raw normal flux**. No equilibration, recovery, weak-reaction substitution or artificially shared interface gradient was used to score the 16 original cuts. Three original interior-plane cuts are re-evaluated from polygon intersections with tetrahedra and linear P2 gradients, retaining the signed 0.1% criterion.

**Prospective acceptance** was registered *before* this candidate's first numerical solve, with exact hashes of the source, original mesh, original field, native face registry and historical Gate B receipt. PASS required **all 16 raw cuts ≤0.1%**, **voltage in [−10⁻⁸, 1+10⁻⁸] V** and **relative independently integrated \(IV\)–bulk/contact losses ≤0.5%**. No retries, new meshes, parameter changes or second solver method were authorized. The historical original P1 electrical gate remains separately failed regardless of prospective success.

## 2. Quantitative comparison

| Independent engineering observable | Original P1 fine | Prospective P2 same fine mesh | Criterion |
| --- | ---: | ---: | --- |
| Worst current cut | **85.62550%** | **8.099302%** | ≤0.1% — P2 **FAIL** |
| Original registered cuts passing | **3 of 16** | **5 of 16** | 16/16 |
| Cuts failing | **13** | **11** | 0 |
| Minimum unit potential | −7.35136×10⁻⁷ V | **−9.14946×10⁻⁷ V** | ≥−1×10⁻⁸ V — P2 **FAIL** |
| Unit-potential source current | 34.0463045 A | **33.8422517 A** | Physics diagnostic; *not* rated current |
| Original fine discrete coupon resistance | 0.0293717634 Ω | **0.0295489 Ω** (approximately) | P2 mesh refinement **NOT RUN** |
| Relative \(IV\)–loss discrepancy | 9.919×10⁻¹³ | **6.339×10⁻⁹** | ≤0.5% — P2 PASS |
| Solver algebraic relative residual | Historical direct solver | **1.09324×10⁻¹¹** | ≤1×10⁻⁸ |
| ILU-GMRES solve | Not applicable (original P1) | **6 iterations** | Solver PASS |

The worst raw-gradient cut is reduced by a factor of **approximately 10.57×**, but still fails its historical limit by **80.99×**. Fifteen of the 16 registered cut errors improve in the P2 candidate. The sole deterioration is the lead9 interior cut, **0.06129% → 0.131997%**, which crosses from pass to fail.

The original high-severity film0 → lead_land discrepancy improves **85.6255% → 1.805219%**, which is approximately **47.43× lower**. This supports field approximation order as a substantial **numerical contributor** to the historical P1 interface-gradient failure, while demonstrating that field order alone is insufficient.

### Selected cut-by-cut results (both from the exact original geometry)

| Current-cut witness | Original P1 failure | P2 failure |
| --- | ---: | ---: |
| **lead9 → lead_land** | 29.17271% | **8.09930%** |
| lead9 → lead_pin | 30.01540% | **6.85291%** |
| tab88 → joint4 | 46.72565% | **6.84322%** |
| tab88 → joint6 | 52.20607% | **6.71292%** |
| joint6 → film2 | 81.55735% | **6.64945%** |
| joint4 → film0 | 79.87666% | **4.81229%** |
| film2 → pn87_solder | 79.75557% | **3.89230%** |
| film0 → lead_land | 85.62550% | **1.80522%** |
| lead_pin → pin_finish | 5.61015% | **1.70870%** |
| **lead9_mid** | **0.06129% PASS** | **0.131997% FAIL** |

The complete source-identified results for all 16 original registered cuts, including the zero-current branches, both terminals and all three interior-plane cuts, are saved in the manifest and [P2 result](../data/v3_gate_B_original_P2_20261106/attempt01/P2_coupon_result.json). The original acceptance denominator and sign conventions were preserved.

## 3. Independent verification and source identity

The [independent P2 readback](../data/v3_gate_B_original_P2_20261106/attempt01/independent_readback.json) uses the **saved P2 scalar solution vector**. It independently rebuilds the original 28,691-cell face incidence, 12-region nodal/edge field ownership, P2 element gradients, raw one-sided currents, and exact finite-contact face integrals for each of the 1,574 native registered contact triangles. Its per-material-interface and both external terminal current integrals reproduce the original P2 producer to within **3.5861×10⁻¹³ relative to the unit-voltage drive current**.

This independent audit does not run a PDE, does not reconstruct physical properties and does not validate a second P2 mesh. The three original interior-plane cut integrals are recorded from the preregistered P2 producer (which performs explicit intersected polygon integration), not separately reproduced by this auditor. Therefore the independent verification fully supports the **11 intermaterial and two electrical terminal integrals**, while the original source code/result is the evidence for the three interior cuts.

The source script SHA-256, input source-hash roster and preregistration were sealed before the solve; no input coefficient/source modification was made afterward. A single original-coupon P2 solve produced one saved 58,993-component field array and the complete failed-gate diagnostic. The sealed run was capped at **4 CPU / 8 GiB / 180 seconds** and completed in **8.51 seconds** with **451.2 MiB** peak Python RSS. The P2 reduced matrix has **1,341,565 nonzero entries**. The source is unchanged by the audit and the prior historical failure results remain fully preserved. **No Codex capacity was consumed.**

## 4. What this DOES and DOES NOT establish

**Narrow positive finding:** Raising the potential approximation from P1 to P2 on the *same unchanged original coupon*, using unchanged selected NOM tensor/contact assumptions and exact native finite-contact geometry, reduces the worst original raw-gradient current mismatch by a factor of approximately **10.57×** and improves **15 of 16** registered cut errors. This directly supports approximation order/gradient fidelity as a material contributor to historical Gate B numerical failure.

**Negative finding:** The new P2 field still has **11 failed raw current cuts**, new worst errors in the lead9 interface branch around **8.1%**, and a stronger negative-voltage undershoot. It also lacks any comparable two-mesh P2 resistance/flux refinement or certified converged local curvature geometry. A consistent algebraic residual and near-exact discrete power closure do **not** certify local current-conservation accuracy. P2 on fixed first-order geometric surfaces cannot repair geometric curvature or omitted physical property evidence.

No proof exists that the entire remaining error is caused by P2 order, thin-film mesh density, numerical conditioning, source tensor assumptions or a physical contact geometry artifact. No physical current rating, detector temperature, TEC operating point or global 430-domain physical law is now qualified.

### Stop decision and focused next activity

**STOP this one-shot P2 candidate**—do not tune the preconditioner, generate additional meshes or continue iterative solver experiments without a new physical engineering acceptance design. The most informative next action is **read-only geometric and field-conditioning attribution** at the *remaining* lead9/lead_land and lead9/lead_pin source faces, comparing original facet geometry, element aspect/shape and local conductivity jumps before authorizing any further prospective electrical solve. Any later new method requires a separate registered gate and a resolution/independent comparator, while the original P1 Gate B FAIL/STOP remains immutable.

**Electrical Gate B remains FAIL/STOP; thermal C/D remain NOT RUN; physical constitutive-law release remains STOP.** The original 824-solid STEP, protected Rev3, 430-domain derived geometry, prior R3.3–R3.17 benchmark evidence, all original coupon meshes and all historical failures remain unaltered.
