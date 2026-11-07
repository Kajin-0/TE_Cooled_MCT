# V3 original Gate B — native lead9 contact-law versus raw P2 flux, radial attribution

**Audit date:** November 6, 2026. **Parent:** `7e5fbede2bb5a33257880c6cd1f7b03736f79467`. **Status:** A source-hashed, **no-solve numerical attribution PASS**; both the historical original P1 Gate B and the distinct prospective P2 Gate B remain **STOP**. No PDE solve, remesh, material change, coefficient fitting, boundary reassignment or old acceptance-gate modification was performed.

[Full data and source SHA-256 record](../data/v3_physical_blocker_closure_20261106/attempt01/lead9_contact_operator_audit.json) and [replayable read-only diagnostic](../scripts/v3_gate_B_lead9_contact_operator_audit.py), based on the original saved [28,691-TET4 V3 coupon P1 failure](V3_INTERCONNECT_ELECTROTHERMAL_20261102.md), the [preregistered failed same-mesh P2 candidate](V3_GATE_B_ORIGINAL_P2_CORRECTION_20261106.md), and the [source-quality audit](V3_GATE_B_LEAD9_GEOMETRY_ATTRIBUTION_20261106.md).

## 1. Actual source faces and field definitions

The original electrically connected source coupon has two circular source-metal contact interfaces:

| Interface | Source CAD face tag | Native TRI3 | Saved TRI3 area (m²) |
| --- | ---: | ---: | ---: |
| lead9 → lead_land | **43** | **158** | **3.13836382911×10⁻⁸** |
| lead9 → lead_pin | **47** | **160** | **3.13836382911×10⁻⁸** |

The original circular CAD registered area is \(3.14159265359\times10^{-8}\,\mathrm{m}^2\) on each interface, giving a **−0.102777%** geometric surface-area difference. The saved original mesh, original NOM anisotropic conductivity tensors and original finite electrical contact area resistance \(R''=10^{-11}\,\Omega\cdot\mathrm{m}^2\) are unchanged and not independently measured physical values.

For every source triangle \(f\), this diagnostic reconstructs three distinct integrated currents using the **same saved preregistered P2 potential vector**:

\[
\begin{aligned}
I_f^{\rm law}&=\int_{A_f}\frac{V_{\rm lead9}-V_{\rm other}}{R''}\,dA,\\
I_f^{\rm lead9}&=\int_{A_f}[-\boldsymbol\sigma_{\rm lead9}\nabla V_{\rm lead9}]\cdot\mathbf n\,dA,\\
I_f^{\rm other}&=\int_{A_f}[-\boldsymbol\sigma_{\rm other}\nabla V_{\rm other}]\cdot\mathbf n\,dA.
\end{aligned}
\]

The common normal \(\mathbf n\) points from the lead9 region to the adjacent material. On the original planar TRI3, the *P2 potential-jump surface integral* equals the triangle area times the average of the three globally unique P2 edge-midpoint trace differences. Because P2 potential gradient is linear within the original linear geometric TET4, the *raw P2 gradient surface integral* is exactly the triangle centroid evaluation times area. This is a raw-gradient/contact-law comparison, **not** a replacement for the preregistered original current-cut test.

The \(I_f^{\rm other}\) values are sign-reversed from the original archive's outward-from-other convention to make all three currents comparable along the same lead9→other normal. All per-face results re-sum to independently established original P1 currents, P2 currents and the original weak/contact-law integrated current for each source contact, within the existing \(10^{-11}\) drive-normalized acceptance for a read-only diagnostic.

## 2. Integrated side-specific bias

All currents are for the **original coupon's artificial unit-voltage excitation**, **not rated TEC/detector operating currents**.

| Source current / local operator diagnostic | Face 43: lead_land | Face 47: lead_pin |
| --- | ---: | ---: |
| Finite-contact-law current, oriented lead9→other | **−33.842252 A** | **+33.842252 A** |
| Raw P2 lead9-side current | −34.983383 A | +34.487773 A |
| Raw P2 adjacent material-side current, same normal | −31.101265 A | +31.523073 A |
| Lead9-side signed bias \(I^{\rm lead9}-I^{\rm law}\) | **−1.141131 A** | **+0.645521 A** |
| Lead9-side absolute error / unit drive | **3.37191%** | **1.90744%** |
| Other-side signed bias \(I^{\rm other}-I^{\rm law}\) | **+2.740987 A** | **−2.319179 A** |
| Other-side absolute error / unit drive | **8.09930%** | **6.85291%** |
| Gross absolute other-side face-current mismatch | 3.035341 A | 2.479281 A |
| Gross absolute lead9-side face-current mismatch | 1.295677 A | 0.732691 A |
| Other-side signed-bias-aligned share of gross error | **95.15%** | **96.77%** |
| Lead9-side signed-bias-aligned share of gross error | 94.04% | 94.05% |

The **limiting 8.10% and 6.85% errors originate in the raw P2 gradients on the adjoining lead_land / lead_pin side**. Both lead9-side raw gradients are appreciably closer to the native contact-law current. This is a direct observable of the saved scalar field and contact integration, not an assumption about how the numerical method should behave.

The strong sign agreement of face-level errors indicates systematic *directional* bias, but a single uniform multiplicative bias is insufficient to explain their spatial pattern. Diagnostic least-squares raw-to-contact density scaling accounts for only **33.31% of squared density mismatch** on lead_land and **30.85%** on lead_pin (and 53.17% / 57.29% on the respective lead9 sides). These scaling factors are **descriptive only**—they were **not** applied to the FEM solution or used to fit contact resistance.

## 3. Radial contact-rim concentration

Using the actual original circular CAD face area to define \(r_{\rm CAD}=\sqrt{A_{\rm CAD}/\pi}=100\,\mu\mathrm{m}\), every saved interface-triangle centroid is placed into the radial intervals \(0\le r/r_{\rm CAD}<0.5\), 0.5–0.75, 0.75–0.9, and **0.9–1.05**. These are **centroid-based diagnostic bins**, not exact clipped annular-triangle integrations; the outermost bin contains source triangle centroids of 0.9–0.982 times the original circular radius, and no centroids beyond the CAD circle.

| Radial diagnostic | Face 43: lead_land | Face 47: lead_pin |
| --- | ---: | ---: |
| Number of TRI3 with centroid \(r/r_{\rm CAD}\ge 0.9\) | **112/158** | **111/160** |
| Fraction of saved TRI3 surface area in this centroid bin | **20.42%** | **19.23%** |
| Fraction of gross absolute **other-material-side** contact-law mismatch in this bin | **78.01%** | **72.47%** |
| Fraction of gross absolute **lead9-side** mismatch in same bin | 17.93% | 13.30% |
| Signed other-material side contact-law bias in rim bin | **+2.367746 A** | **−1.796856 A** |
| Total signed other-material bias across contact | +2.740987 A | −2.319179 A |

This **refines rather than contradicts** the preceding [shape-quality investigation](V3_GATE_B_LEAD9_GEOMETRY_ATTRIBUTION_20261106.md): that report found the **gross two-sided raw-vs-raw mismatch** was not overwhelmingly concentrated in the largest 10% of individual triangles. The current report instead compares each separate material's raw gradient against the **actual finite-contact-law current** and groups them by **distance from the CAD circle perimeter**. Those are different diagnostic questions and explain why the new rim-side concentration can coexist with the earlier broadly distributed total discrepancy.

The roughly 20%-area perimeter-centroid bands account for nearly three-quarters of the *other-side* gross error, while the lead9-side discrepancies are considerably more evenly distributed. This makes the **contact perimeter / adjacent material gradient representation** a substantially better next hypothesis than global element mean-ratio quality optimization.

## 4. What is and is not established

**Established:**
- All 318 saved original source triangles, both sides' material ownership, contact-law and raw-gradient surface integrals, source-hashed field identity, and strict old sign convention were reproduced.
- The dominant residual **integrated** P2 Gate B cut errors come from the adjoining materials, not lead9 itself.
- The 0.9–1.05 CAD-radius centroid bands have a disproportionate share of other-side contact-law discrepancy, which is a new testable spatial finding.
- No severely poor-quality tetrahedra (\(q<0.1\)) were found directly incident to either source interface in the preceding fixed-mesh shape audit.
- The original surface area differs from CAD by only −0.102777%, not enough under uniform current density to account independently for the observed 6.85–8.10% errors.

**Not established:** whether this rim effect arises from a real physical current-crowding/singularity near a circular material interface, local finite-element convergence order, anisotropic conductivity assignment, geometry approximation at the contact circumference, contact-law weak-form discretization, or an interaction of these. The finite-contact current is not a measurement of the physically correct interface current density. The source NOM contact area resistance is a hypothesis, not a measured physical qualification. Neither the P2 minimum-voltage violation nor any of the 11 other still-failed current gates has been corrected.

### Decision

**Do not start another general remesh, unconstrained P2 solve, alternative scalar manufactured benchmark or bulk-material fitting pass.** The next potential numerical experiment, if approved separately, should isolate **native contact perimeter-field consistency** in the original lead9 metal/joint subassembly, preserving the original raw-current test, both-sided face gradients, the exact contact law, source area and voltage bound. A credible method change would need a preregistered local perimeter-resolution or interface-consistent gradient comparison, source-preserving negative controls, all 16 cut outcomes and a fixed stop condition. Any improvement to the weak/recovered flux must **not** be misrepresented as a raw-gradient qualification.

The immediate alternative is the existing **physical-input law inventory**: before any general TEC performance analysis, source all domain conductivities, thermoelectric coupling and contact resistance under realistic temperature/measurement uncertainty and stop where evidence is absent.

**Qualification unchanged:** Original P1 Gate B **FAIL/STOP**. Prospective P2 Gate B **STOP**. Thermal Gates C/D **NOT RUN**. Source CAD/STEP, all prior mesh/P1/P2 solutions, 430-domain derived geometry, canonical Rev3 and issue #2 remain preserved. Codex quota untouched.
