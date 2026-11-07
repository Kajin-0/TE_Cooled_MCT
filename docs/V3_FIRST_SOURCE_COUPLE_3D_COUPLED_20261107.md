# V3 first original-source 3D coupled N/P thermoelectric subassembly

**Date:** 2026-11-07. **Baseline:** 8dd6253812d3fb273eb27ebfe1d4da9ee112c8da.

**Verdict: Coupled 3D conditional weak charge/energy PASS; all eight raw P1 contact-gradient current cuts FAIL 0.1%. No as-built validation, no full 430-domain Gate C/D.**

The [saved-field independent audit](../data/v3_first_couple_coupled_20261107/attempt04/saved_field_independent_audit.json) confirms the independent electrical-work identity, native contact weak currents, prescribed current and thermal balance without running the PDE again. The [complete saved fields](../data/v3_first_couple_coupled_20261107/attempt04/result.json), [preregistration](../data/v3_first_couple_coupled_20261107/attempt04/registration.json), [source-hashed attempt history](../data/v3_first_couple_coupled_20261107/manifest.json), [coupled solver](../scripts/v3_first_couple_coupled_3d.py) and [read-only auditor](../scripts/v3_first_couple_saved_field_audit.py) preserve evidence.

## Scope: exact original CAD, no remeshing

From archived R3.9 1,010,119 global TET4, select 1,000 existing tetrahedra for nine native conducting volumes: N leg 5, P leg 8, hot/cold SnSb solids 6, 7, 9, 10, and source composite-metal nets 269, 270, 271. Preserve the **112 original triangular facets** belonging to solder contact tags **124, 125, 130, 135, 140, 141, 146, 151**. Two true original CAD cut interfaces are tagged **1531** (mathematical current source) and **162** (return). Hot pad/ceramic source interfaces **8 and 9** and cold pad/ceramic interface **44** have prescribed-temperature boundary values. The surrounding 86 legs, full ceramic plates, hot sink, detector, gas and radiation remain excluded, not treated as physically modeled insulation.

Each field uses **454 source-region-separated nodal degrees of freedom**, allowing finite potential and temperature jumps across interfaces. This is one real source-CAD nine-conductor subassembly, not a full actual TEC or an artificial independent package-terminal pair.

## Signed transport and energy equations

The chosen potential and Seebeck sign convention is:

\[
\mathbf J=-\sigma(T)[\nabla V+S(T)\nabla T],\qquad
\mathbf q=S(T)T\mathbf J-k(T)\nabla T,
\]

\[
\nabla\cdot \mathbf J=0,\qquad
\nabla\cdot\mathbf F=0,\qquad
\mathbf F=\mathbf q+V\mathbf J.
\]

Full **total-energy conservation**, not Fourier heat flux alone, is the coupling equation. Material P and N use unmatched 40–300 K Zhang (2025) research-specimen transport interpolated at each tetrahedral centroid. SnSb uses the **historical hypothetical** electrical resistivity 1.7e-7 ohm m and thermal conductivity 45 W/(m K). Laminated metal nets use historical conditional anisotropic tensors. SnSb and metal are assigned zero Seebeck coefficient. None of these constitutes actual manufacturer-specific properties.

Each original solder contact uses deliberately hypothetical specific electrical resistivity **1e-11 ohm m2** and area-specific thermal resistance **1e-7 m2 K/W**. With native face-side orientation a to b, the interface model uses:

\[
j_{ab}=(V_a-V_b)/r_e,\qquad
F_{ab}=(T_a-T_b)/r_t+\tfrac12(V_a+V_b)j_{ab}.
\]

This imposes equal and opposite interface total-energy fluxes, with contact voltage drop dissipating \(j_{ab}(V_a-V_b)=r_ej_{ab}^2\). Electrical contact Joule heating is split symmetrically between sides in this conditional model. The discontinuous bulk thermopower enters through the adjacent Seebeck heat flux. This contact model is not a measured junction thermopower, and centroid property quadrature remains a low-order approximation.

## One prospective conditional test case

The actual CAD cut interfaces receive **0.050 A** current, not a prescribed physical package-terminal voltage. Source hot pad faces 8/9 are **298 K**, and source cold pad face 44 is **296 K**. These temperatures are **inputs**, not predicted cooling outcomes. Every other selected exterior boundary is electrically and thermally insulated except electrical-current ports, where total-energy flux includes electrical work. A region-disjoint P1 tetrahedral current/temperature solve used 20 temperature fixed-point steps.

| Metric | Calculated and independently checked |
| --- | ---: |
| Original selected TET4 cells | **1,000** |
| Separate V and T source-region trace DOFs | **454 per field** |
| Original internal solder TRI3 facets | **112** |
| Applied current through mathematical pair | **0.050 A** |
| Calculated cut-terminal voltage | **4.210119 mV** |
| Calculated electrical input | **0.210506 mW** |
| Bulk positive Joule dissipation | **0.168449 mW** |
| Signed bulk Seebeck conversion work | **+0.040584 mW** |
| Eight-interface electrical Joule heat | **0.001473 mW** |
| Independent electric-work relative error | **1.39e-12** |
| Computed source selected temperature extrema | **295.98293 to 298.01744 K** |
| Hot pad total-energy reaction | **+4.419430 mW** |
| Cold pad total-energy reaction | **-4.208924 mW** |
| Hot + cold minus electrical input (relative) | **4.40e-10** |
| Free electric weak residual | **2.27e-13 A** |
| Free thermal weak residual | **6.09e-14 W** |
| Eight weak contact-current errors | **at most 2.21e-12 relative** |
| **Raw original one-sided P1 current-gradient gate** | **FAIL: 8 of 8 cuts; worst 368.62%** |

The signed thermal boundary reactions are quoted as produced by the defined weak-form convention; the prescribed cold-pad temperature is not solved. Their sum equals the electrical input. Positive bulk Joule, signed Seebeck work and finite interface Joule contributions independently reconstruct the calculated electrical input. Exact weak and algebraic conservation does **not** certify the original raw gradient current.

## Critical current fidelity failure

For every one of the eight actual solder contacts, integrate **both separate one-sided constitutive currents** directly from the original tetrahedral P1 bulk gradients, without replacing them with a contact-law reaction. All **eight fail the 0.1% raw-current tolerance** even though finite-contact weak fluxes conserve 0.050 A across every series interface. Worst is original **face 146**, where the metal-side raw current differs by **3.68616 times the imposed current**.

This is a **prospective subassembly raw-contact failure**, separate from the original historical Gate B P1 coupon failure, which remains FAIL/STOP without reclassification. The correct conclusion is *coupled equations and weak conservation infrastructure work, but the raw interface current field is numerically unacceptable*. No physical or fully coupled 430-domain solve is authorized by these results.

## Preserved attempt history and read-only verification

The [evidence manifest](../data/v3_first_couple_coupled_20261107/manifest.json) preserves all four attempts and all available logs and results. Attempt01 had triangle-dependent owner orientation in signed contact diagnostics. Attempt02 fixed orientation according to the registered source CAD face ownership, revealing correct weak series currents and the 8/8 raw failure. Attempt03 added the independent electrical-work identity but failed **after numerical evaluation** on NumPy-int JSON serialization; its partial output is intentionally retained under a .partial.json.gz filename. Attempt04 changed only scalar serialization, preserving the same mesh, currents, temperatures and material/contact hypotheses, and produced complete saved V/T trace fields.

The saved-field [auditor](../scripts/v3_first_couple_saved_field_audit.py) never solves a PDE. It reconstructs the 0.050 A signed weak contact integrals, the independent voltage/work breakdown, both thermal reactions, and the raw one-sided currents directly from the archived V/T fields and exact source CAD. It reproduces the weak passes and **8 raw failures**.

## Next prospective numerical and physical gates

The next mathematical contribution should be a **single prospective, independently preregistered conservative flux recovery or mixed H(div) discretization** with independent native-contact current and mesh-resolution acceptance. Do not retroactively call a changed flux observable a pass of the original P1 raw-gradient Gate B. Further arbitrary material/contact sweeps on this same under-resolved P1 interface field would be churn.

Independently, a product-grade calculation still requires matched P/N transport, actual contact coefficients, external TEC drive and heat-sink conditions, cavity/radiative loads and verified source assembly identity.

**Unchanged:** frozen 824-solid source STEP, original 430-domain/2,440-face geometry and Rev3, prior failures, issue #2. Original P1 Gate B **FAIL/STOP**; P2 prospective **STOP**; full thermal C/D **NOT RUN**; physical material/face laws **UNSET**; actual detector temperature **UNQUALIFIED**. No Codex use.
