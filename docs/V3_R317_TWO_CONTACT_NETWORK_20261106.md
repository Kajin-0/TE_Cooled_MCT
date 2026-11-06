# V3 R3.17 — Actual three-material, two-contact scalar FEM network with spatially varying normal flux

**Date:** November 6, 2026. **Baseline commit:** `5fa9e9a6dc4717e501f7ae311c8119122de56b95` (R3.16).  
**Verdict: PASS** for the *registered mathematical, manufactured, three-region/two-contact scalar diffusion* test including two distinct finite-resistance laws, independently reconstructed interface flux, and non-polynomial H¹ gradient error. **No true device electrical, thermal or thermoelectric model; no global physical network-current closure or asymptotic mesh convergence is claimed.**

## Actual source CAD and provenance

This is not a fabricated mesh fixture. R3.17 extracts **three physically connected regions** from the existing immutable R3.9 whole-package TetGen conformal volume mesh:

| Native volume | Source CAD region | Source material label |
| ---: | --- | --- |
| **408** | `p_HgCdTe_photoconductor` | `pHgCdTe_PC` |
| **410** | `det8_wedge_foot` | `COMPOSITE_MULTILAYER` |
| **420** | `detector_bond8` | `Au` |

The network has **two real CAD solid/solid interfaces**, each separately qualified by exact native face/node IDs:

| Contact | Adjacent CAD regions | Original conformal TRI3 count | Saved interface area (mm²) |
| --- | --- | ---: | ---: |
| **2336** | HgCdTe 408 / composite 410 | **6** | **0.002100000** |
| **2349** | Composite 410 / Au 420 | **48** | **0.0002537429177** |

The 3-region union has **26,290 original TET4 elements** and **6,998 unique geometric nodes**. Field traces are separated by native material identity, so the three regions have **7,055 P1 field vertices**, or **47,334 P2 scalar DOFs** with globally shared same-material edges and intentionally separate contact-side edge/vertex degrees of freedom. The entire physical mesh, source coordinates, registered CAD surface markers and all other 427 source volumes remain unchanged.

The independent face-complex preflight reconstructs every tetrahedron incidence and compares exactly the two sets of CAD registered interface triangles: zero missing, extra, misowned or duplicate two-material interface facets. It also confirms the original **13,766 native exterior triangles** for the three-region union. This remains a geometrically restricted subassembly, not a remeshed or reinterpreted global CAD source.

## Manufactured finite-contact network

The test uses **artificial mathematical material coefficients**, *not* measured HgCdTe, composite wedge or Au conductivities:

\[
k_{408}=2,\quad k_{410}=1,\quad k_{420}=10,
\qquad
G_{2336}=4,\quad G_{2349}=5.
\]

The manufactured normal-gradient flux varies over each interface:

\[
q(x,y)=1+1.8(x+0.35)+2.5y.
\]

The measured analytic ranges sampled at the native interface centroids are:

| Native contact | \(q_{\min}\) | \(q_{\max}\) |
| --- | ---: | ---: |
| 2336 | 0.9348333 | 1.0651667 |
| 2349 | 0.9815673 | 1.0184327 |

Define a shared tangential field \(F(x,y)=A[(x+0.35)^2+y^2]+\beta\sin(\omega(y-y_{\min}))\), with \(A=0.025\), \(\beta=0\) (piecewise quadratic case) or 0.15 (non-polynomial case), and \(\omega=\pi/\max(\Delta y,0.05\,{\rm mm})\). In each region the manufactured solution is

\[
u_r(x,y,z)=F(x,y)+q(x,y)s_r(z),
\]

with

\[
\begin{aligned}
s_{408}(z)&=(z-z_1)/k_{408}-1/G_{2336},\\
s_{410}(z)&=(z-z_1)/k_{410},\\
s_{420}(z)&=(z-z_2)/k_{420}+(z_2-z_1)/k_{410}+1/G_{2349},
\end{aligned}
\]

where \(z_1=5.77625\,{\rm mm}\) and \(z_2=5.7849\,{\rm mm}\). By construction, the gradient-normal flux is continuous through both contacts while the potential exhibits **two different, spatially varying contact jumps**:

\[
\begin{aligned}
u_{408}-u_{410}&=-q(x,y)/G_{2336},&&z=z_1,\\
u_{410}-u_{420}&=-q(x,y)/G_{2349},&&z=z_2.
\end{aligned}
\]

These satisfy the correct diffusive outward-flux sign convention \(\mathbf q_r=-k_r\nabla u_r\). The weak form includes \(G_c\int_{\Gamma_c}(u_a-u_b)(v_a-v_b)\,dA\) independently at **both** native interfaces. Exact region-specific manufactured forcing and analytic natural Neumann flux are applied on the original exterior faces; native CAD face 2399 is the prescribed Dirichlet boundary. Interface faces **2336 and 2349 are never treated as external Neumann faces**.

The local field spaces are P1 continuous within each material, and P2 quadratic within each material with globally consistent per-material shared-edge field DOFs. Neither contact is artificially welded, and no physical contact resistivity or thermal junction law is inferred.

## All four registered solver results

All runs passed a true, unpreconditioned operator relative residual gate \(\|Au-b\|_2/\|b\|_2<10^{-8}\), under the bounded 4-CPU/8-GiB original FEM runtime and the same SciPy ILU-GMRES preconditioning strategy as R3.14–R3.16.

| Metric | P1 quadratic | P2 quadratic | P1 non-polynomial | P2 non-polynomial |
| --- | ---: | ---: | ---: | ---: |
| Free scalar DOFs | 3,983 | **35,142** | 3,983 | **35,142** |
| ILU-GMRES iterations | 8 | **12** | 8 | **12** |
| True algebraic residual | 9.40×10⁻¹² | 5.37×10⁻¹² | 9.56×10⁻¹² | 5.12×10⁻¹² |
| H¹ gradient error, independent 216-point quadrature | 0.107087524 | **1.057752×10⁻⁹** | 0.110789151 | **2.509963×10⁻⁵** |

The genuine non-polynomial manufactured result shows **4,413.98× lower relative H¹ gradient error with P2** than with P1. It is a measured result for this single smooth mathematical field; the extremely small quadratic-case P2 error is largely expected because P2 exactly represents the piecewise quadratic component.

### Both contact laws qualified separately

For the hardest (non-polynomial P2) experiment, the **independent saved-coefficient auditor** finds:

| Native CAD contact | Relative RMS Robin-condition mismatch | Relative RMS outward-normal flux imbalance |
| --- | ---: | ---: |
| **2336 (HgCdTe/composite)** | **8.823445×10⁻⁶** | **8.818163×10⁻⁶** |
| **2349 (composite/Au)** | **1.339013×10⁻⁷** | **2.121760×10⁻⁷** |
| Preregistered threshold | **1×10⁻⁵** | **1×10⁻⁵** |

The less-resolved **six-triangle** HgCdTe/composite contact is the limiting interface and passes narrowly. P1 on the same non-polynomial problem has substantial flux-condition error: relative Robin mismatches **0.135467 (2336)** and **0.0173509 (2349)**. Therefore R3.17 does not support an assertion that simple P1 interpolation is adequate for this interface network.

These are **separate contact face-local flux mismatch checks**. The cross-sectional integral of \(q\) may vary across the network because the contact areas differ and the artificial body and exterior forcing are nonzero. **This is not a demonstration of a measured, globally closed detector current**; actual global current closure is still unqualified.

## Independent geometric and error audit

A separate read-only program [`independent_network_audit.py`](../data/v3_r317_two_contact_network_20261106/attempt01/independent_network_audit.py) reads each solved field coefficient vector and reconstructs all tetrahedron geometries, source-face ownership, interface outward normals, contact jumps, per-material gradients and two-sided fluxes from scratch. It does not call the finite-element assembly, solver or the primary error integrator.

It evaluates H¹ gradient-error integrals using **216 Duffy/Gauss–Legendre tetrahedral points per element**, instead of the primary four-point rule. Primary and independent contact mismatches agree at each face. The saved measurements are in [`independent_network_audit.json`](../data/v3_r317_two_contact_network_20261106/attempt01/independent_network_audit.json).

**Quadrature caution:** The original four-point quadrature produced non-polynomial P2 H¹ error \(1.737827×10^{-5}\), whereas independent 216-point integration produced \(2.509963×10^{-5}\), an **increase of 44.43% relative to the primary estimate**. Because the non-polynomial gradient-squared integrand exceeds the original rule's exactness, the independently integrated high-order value is authoritative. This discrepancy is explicitly preserved, not replaced by a new solver run or tuned away.

The total registered primary benchmark took **15.702 s**, peak Python RSS **392.6 MiB**, with no Codex use, no newly needed compute resource, no altered source mesh and no launched full-package physics PDE. The separately bounded independent audit passed in **24.44 s**.

## Qualification limits and next engineering decision

**R3.17 PASS means:** the native HgCdTe/composite/Au material path supports **two different finite-contact Robin laws, two separate voltage jumps, spatially varying prescribed normal flux, conservative shared interface weak-form coupling**, and independently verified P2 accuracy on a non-polynomial scalar manufactured solution.

**R3.17 does not mean:** validated HgCdTe transport, current flow from an actual detector bias supply, meaningful interface contact resistivity, multi-layer composite effective physics, Seebeck/Peltier transport, Joule heat, correct physical boundary ports, global 430-domain current conservation, mesh convergence or an accepted detector/TEC operating point.

The next gate should use measured/qualified electrical and thermal coefficients (and contact-law alternatives) to establish a **physical subassembly** test with explicitly accounted electrical terminals and integrated source/flux closure. A standalone global weak-form conservation and reaction-balance audit should be required before advancing to the full package. A separately preregistered sensitivity/convergence experiment should evaluate the six-triangle contact 2336 before interpreting interface losses physically.

The original 824-solid STEP, 430-domain source BREP, all 320,522 registered surface facets, 378 finite contact witnesses, original R3.8–R3.16 mesh variants, historical R3.3/R3.4 failure receipts, canonical 38-page Rev3 and issue #2 remain unchanged. **Electrical Gate B remains STOP. Thermal gates C/D remain NOT RUN. No physical detector temperature or TEC performance prediction is qualified.**

**Evidence:** [R3.17 manifest](../data/v3_r317_two_contact_network_20261106/attempt01/manifest.json) with exact SHA-256 of primary/independent code, saved P1/P2 fields, original residuals and all audit outputs.
