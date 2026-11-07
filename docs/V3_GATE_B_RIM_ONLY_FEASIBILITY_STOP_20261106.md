# V3 Gate B — Stop a rim-only correction campaign before another mesh/PDE run

**Decision date:** November 6, 2026. **Parent:** `218362914670479a91d75ddc9ce2a755366c5735`.  
**Verdict: NO GO for isolated contact-rim correction of existing saved flux.** Both the original P1 electrical Gate B and the separate P2 candidate remain **FAIL/STOP**. This is a source-hashed, exact-replay, **no-solve counterfactual feasibility calculation** using [the existing contact-law-vs-gradient radial ledger](../data/v3_physical_blocker_closure_20261106/attempt01/lead9_contact_operator_audit.json). Its [machine-readable decision receipt](../data/v3_physical_blocker_closure_20261106/attempt01/rim_only_feasibility_stop.json) and [reproducer](../scripts/v3_gate_B_rim_only_feasibility.py) are retained with the original archive.

## Question

The preceding [contact-operator analysis](V3_GATE_B_LEAD9_CONTACT_OPERATOR_20261106.md) found that **78.01%** and **72.47%** of gross absolute other-material-side face mismatch occurred at triangles whose centroids have \(r\ge0.9R_\mathrm{CAD}\). This seemed to support a targeted contact-perimeter mesh correction. However, it does not establish that correcting **only** the perimeter is sufficient to satisfy the original **0.1% integrated raw-current cut gate**.

A necessary screening test for that **limited fixed-field premise** is: *if all existing raw-minus-contact-law current discrepancy assigned to the outer centroid bin were magically zero, but all inner-bin discrepancies remained exactly as saved, would the original registered current cut pass?*

Define signed error for source-material side \(s\in\{\mathrm{lead9},\mathrm{other}\}\):

\[
\Delta I_s = \sum_{f\in A_{\rm inner}}(I_{s,f}^{\rm raw}-I_f^{\rm law})+
\sum_{f\in A_{\rm rim}}(I_{s,f}^{\rm raw}-I_f^{\rm law}).
\]

The **rim-only zero-error counterfactual** sets only the second sum to zero. All source P2 coefficients, CAD geometry, original raw-gradient currents, contact-law currents, interior terms and \(|I_\mathrm{drive}|\) denominator remain fixed. For each side the residual is exactly the original **signed inner-bin sum**.

## Measured fixed-field counterfactual

| Diagnostic | lead9 → lead_land, face 43 | lead9 → lead_pin, face 47 |
| --- | ---: | ---: |
| Original source TRI3 | 158 | 160 |
| Contact-law current magnitude at unit drive | 33.842252 A | 33.842252 A |
| Original P2 full-interface worst cut error | 8.0993% | 6.8529% |
| Outer-band fraction of source contact area | 20.42% | 19.23% |
| Outer-band signed **other-side** current mismatch | +2.367746 A | −1.796856 A |
| Remaining **inner other-side** signed mismatch | **+0.373241 A** | **−0.522323 A** |
| Other-side error if entire rim mismatch eliminated | **1.10288%** | **1.54340%** |
| Remaining inner **lead9-side** signed mismatch | −1.061272 A | +0.630035 A |
| Lead9-side error if entire rim mismatch eliminated | **3.13594%** | **1.86168%** |
| Worst either-side error after perfect rim correction | **3.13594%** | **1.86168%** |
| Original all-cut threshold | 0.1% | 0.1% |
| Worst-side exceedance of limit | **31.36×** | **18.62×** |
| Rim-only fixed-field correction verdict | **FAIL / NO GO** | **FAIL / NO GO** |

The earlier absolute-mismatch radial shares are **different observables** from these signed integrals. The exact fixed-field counterfactual retains both material-side original gradient currents and all input conductivities.

## Engineering significance

**This eliminates a narrowly specified proposition:** simply removing or correcting all of the *existing* rim-bin raw-current mismatch, with the inner saved field unchanged, is incapable of satisfying the 0.1% gate on either contact. The inner contact region already has residual error exceeding the gate by 11–31× depending on which side is considered.

**This is not a mathematical impossibility theorem for contact-perimeter refinement in a NEW FEM solve.** Changing mesh or polynomial spaces at the rim changes the global elliptic solution and may improve interior gradients too. The current experiment does **not** predict that global redistribution, does not bound a newly recomputed field, and does not estimate the convergence rate of any new mesh. In addition, the prospective P2 candidate has 11 of 16 failing cuts and fails the voltage bound; passing just these two contacts would not by itself pass Gate B.

**Decision:** No new isolated rim-only meshing/solver campaign is justified by current evidence. A future full-interface prospective method would need to demonstrate a causal reason why both rim **and** interior errors should improve; preserve all 16 cuts, their 0.1% criterion, original contact and material assumptions, voltage boundedness and the historical original P1 failure; and preregister the method and independent field verification. At present, further synthetic or localized numerical experimentation has declining value compared with releasing evidence-backed, real thermoelectric and contact laws.

## Anti-churn next work

1. **Freeze** the original 28,691-TET4 P1 Gate B failure and the original-geometry 58,993-DOF P2 failed candidate. Do not touch the 824-solid STEP, 430-domain source CAD, canonical Rev3 or prior results.
2. **Prioritize the exact 430-domain material/2,440-face physical input ledger**, making unknown temperature-dependent thermoelectric, metal, interface and external boundary conditions visible. Existing source metadata are all `UNSET`; never fill silently using bulk analogues or synthetic contact resistance.
3. Before any new electrical solve, require a **separately registered full-interface field and flux-consistency hypothesis** that addresses *both* interior and perimeter lead9 gradients, all other 14 original cuts, voltage undershoot and mesh independence. Do not count easier algebraic/weak-contact current conservation as equivalent to the registered raw-current gate.

**Qualification status:** Original P1 Gate B **FAIL/STOP**; prospective P2 Gate B **STOP**; thermal C/D **NOT RUN**; physical material-law release **STOP**. No solver, remesh, contact-law fit, PDE or Codex usage in this milestone.
