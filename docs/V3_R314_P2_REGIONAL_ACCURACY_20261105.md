# V3 R3.14 — P2 quadratic finite elements on the preserved linear geometric mesh

**Date:** 2026-11-05. **Baseline:** `2d167a47c65b10b3ecf2e220ff2be3875741bf27` (R3.13).  
**Scientific verdict:** **PASS** a regional P1/P2 mathematical finite-element comparison and independent non-polynomial H¹-error validation. **NOT a qualified physical, coupled multiphysics, full-device or asymptotically mesh-converged simulation.**

R3.13 showed that interior-only barycentric tetrahedral refinement did not substantially reduce non-affine discretization error and eventually caused a numerical solver stop. R3.14 investigates a different route: enrich the **finite-element solution space** from linear P1 to quadratic P2 while retaining the *same* original straight-sided R3.9 TET4 geometry, face triangles, and region ownership. No new tetrahedra, moved CAD/interface vertices, physical interface-law changes, or full-device PDE were involved.

## Exact geometric and approximation scope

The source is the original independently verified **R3.9 gold detector-bond 8**, native CAD region 420, containing **25,905 positive TET4 cells**, 6,884 vertices and **13,540 registered exterior/intermaterial TRI3 facets**. All original geometric triangle triplets remain unchanged. Native CAD face **2399** is the Dirichlet boundary; analytical outward Neumann flux is prescribed on the remaining true native boundary facets.

The P2 solution basis has 10 local Lagrange degrees of freedom: four values at existing tetrahedral vertices and six values at midpoints of global mesh edges. Global edge tags are uniquely identified so that adjacent tetrahedra share precisely the same P2 edge degree of freedom. The **geometric interpolation is still linear**; these are approximation degrees of freedom, *not new source-mesh vertices or curved physical faces*.

| Mesh and solution-space measure | P1 | P2 |
| --- | ---: | ---: |
| Geometric tetrahedra | 25,905 | **25,905 unchanged** |
| Original geometric vertices | 6,884 | **6,884 unchanged** |
| Distinct geometric edges | — | **39,558** |
| Total solution degrees of freedom | 6,884 | **46,442** |
| Dirichlet degrees of freedom on face 2399 | 3,072 | **12,192** |
| Free degrees of freedom | **3,812** | **34,250** |
| Registered region-boundary facets | **13,540** | **13,540 identical** |

The local basis is \(N_i=\lambda_i(2\lambda_i-1)\) at vertices and \(N_{ij}=4\lambda_i\lambda_j\) on edges. The basis passed the partition-of-unity, zero total-gradient, and exact quadratic-polynomial gradient-reproduction tests on independent reference tetrahedra.

## Manufactured equations and integration

All tests solve the *mathematical* scalar unit-diffusion equation \(-\nabla^2u=f\), not physical gold conduction. The analytic solution is defined in terms of recorded region geometry parameters \(o_i,s_i\):

\[
u_Q(\mathbf x)=\sum_{i=1}^{3}\left(\frac{x_i-o_i}{s_i}\right)^2.
\]

The harder non-polynomial test adds a smooth sinusoidal contribution in one region direction:

\[
u_{NP}(\mathbf x)=u_Q(\mathbf x)+0.25\sin\big(k(y-y_{\min})\big),
\qquad
k=\frac{\pi}{\max(y_{\max}-y_{\min},\ 0.05\,{\rm mm})}.
\]

Both tests prescribe \(u_*\) exactly at the appropriate P1/P2 Dirichlet degrees of freedom on native face 2399, use analytic forcing \(f=-\nabla^2u_*\), and integrate the analytic outward Neumann flux \(\nabla u_*\cdot \mathbf n\) on every other registered planar boundary facet. Stiffness uses the original positive TET4 geometric Jacobians, not an invented curved geometry.

P1/P2 volume integration uses an 11-point degree-4 Keast tetrahedral rule; boundary loads use a 7-point degree-5 Dunavant triangle rule. An independent [simplex monomial moment audit](../data/v3_r314_p2_20261105/attempt01/quadrature_moment_audit.json) verified all **70 tetrahedral monomials through degree 4** and all **56 triangular monomials through degree 5** against exact factorial moments; maximum errors were \(6.94\times10^{-18}\) and \(9.99\times10^{-16}\), respectively.

## Quantitative results: same tetrahedra, different solution orders

| Measurement | P1 non-polynomial | P2 non-polynomial |
| --- | ---: | ---: |
| Saved geometric tetrahedra | 25,905 | 25,905 |
| Free FEM DOF | 3,812 | 34,250 |
| ILU-GMRES iterations | **9** | **11** |
| Independently computed true relative residual | **2.74×10⁻¹¹** | **1.82×10⁻¹¹** |
| Relative H¹-seminorm gradient error | **0.0170792170** | **0.0000118540704** |
| H¹ relative error, percentage | **1.707922%** | **0.001185407%** |
| Assembly + solver | 0.631 s | 2.335 s |

The P2 method reduces the non-polynomial *relative gradient error* by **approximately 1,440.79×** compared with P1, with no tetrahedral refinement. The additional DOF and 10-node elemental operations have a cost, but the observed regional P2 solve remains practical at this scale.

The separate quadratic-polynomial test is exactly representable by P2 on this *linear geometric mapping*. The measured P2 relative H¹ error was **1.6565×10⁻⁸** with true algebraic residual **2.82×10⁻¹¹** and 11 ILU-GMRES iterations, showing near-numerical-exact recovery of the quadratic field.

Across the three registered tests the comparison completed in **11.04 s**, with peak Python RSS **366.7 MiB** using the existing recovered FEM container, 4 CPUs and an 8 GiB resource limit. No additional compute resource or Codex usage was required.

## Independent H¹ validation

The primary solver evaluated H¹ error by 64-point fourth-order Duffy-product tetrahedral integration. To avoid believing the assembly's own error integration, a **separate source implementation** replayed the original finite-element solves, saved complete P1/P2 coefficient vectors, and independently reintegrated the exact analytical-gradient error with **216 points per tetrahedron** (6×6×6 Gauss–Legendre Duffy product).

| Independent integration cross-check | Relative H¹ error, 216-point | Disagreement with primary 64-point integration |
| --- | ---: | ---: |
| P2 quadratic (polynomial exactness) | **1.656521246×10⁻⁸** | 3.17×10⁻⁸ relative |
| P1 non-polynomial | **0.01707921698335** | 4.55×10⁻¹⁴ relative |
| P2 non-polynomial | **0.00001185406933** | 8.77×10⁻⁸ relative |

The independent non-polynomial accuracy ratio is **1,440.78936×**, consistent with the primary run. All three replayed H¹ values, solver residuals, iteration counts, and degrees of freedom agree exactly with the primary outputs; only execution-time and memory values naturally differ. Source hashes, original assembly and replay scripts, all three coefficient arrays, and the saved initial preflight code error are preserved in the [R3.14 manifest](../data/v3_r314_p2_20261105/attempt01/manifest.json).

The first basis-construction preflight encountered a Python/NumPy structured-array comparison exception before assembling any finite-element matrices. The exact error log is retained; the corrected implementation checks sorted unique edge pairs using `np.unique(..., axis=0)`. No source geometric data were modified.

## Interpretation and scientific limits

**What has been demonstrated:** A genuine and independently checked improvement in approximation accuracy for one non-polynomial scalar diffusion problem on the **exact same finite geometric mesh**, with effective ILU-GMRES conditioning in this regional case. Unlike centroid refinement, the field approximation gets much better without geometrically modifying contact and material-interface triangles.

**What has NOT been demonstrated:** asymptotic p-convergence across three or more polynomial orders, convergence against experimentally measured detector or TEC properties, accuracy of curved geometric interfaces, conservative multi-material interface flux transfer, or numerically sound whole-package electrothermal physics. The source TET4 geometry still has the poor element-quality population reported in R3.8–R3.13, and a higher-order solution basis does not erase geometric conditioning or curvature errors. This single-region smooth manufactured field is not a stress test of discontinuous semiconductor/metal/contact laws.

### Next gate — R3.15

The most valuable next qualification is a **two-material, continuous-flux P2 interface benchmark** across an actual registered contact or CAD internal interface, with independently specified scalar coefficients and known manufactured transmission conditions. Compare conservation/flux jumps, P1/P2 error and conditioning under exact original face ownership. Only after that should the analysis attempt multi-domain physical thermal/electrical operators or proceed toward Gate B.

All original physical 824-solid STEP bodies, source R3 derived BREP, historical R3.3/R3.4 FAIL/STOP records, R3.8–R3.13 original meshes and scientific evidence, 378 finite-contact witness records, canonical 38-page Rev3 and issue #2 remain preserved. **Electrical Gate B remains STOP; thermal C/D remain NOT RUN; no physical detector operating temperature or TEC prediction is qualified.**
