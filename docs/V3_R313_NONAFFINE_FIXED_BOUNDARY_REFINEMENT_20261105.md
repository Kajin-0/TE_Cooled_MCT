# V3 R3.13 — Non-affine bond-8 manufactured solution under fixed-boundary tetrahedral refinement

**Date:** 2026-11-05. **Baseline:** `23efb16ad624a5779be77e3fc439befe3caabc24` (R3.12).  
**Verdict:** Three successive mesh levels are geometrically conformal and preserve all registered regional interfaces. **Full non-affine mesh-convergence acceptance FAIL/STOP:** the first refinement barely improves H¹ error and the second-refined solve fails its registered iterative residual target. **No physical electrical, thermal or thermoelectric PDE was run.**

## Question, geometry and prerequisites

R3.12 established that an ILU-GMRES solver can handle the saved regional scalar FEM matrices and exactly reproduce an affine harmonic field. This does **not** establish approximation accuracy for spatially varying fields.

R3.13 uses gold detector-bond 8 (native CAD **volume 420**) from the immutable **R3.9** mesh, original fixed 13,540 region-boundary triangles (including intermaterial contacts), and unchanged R3.8 node coordinates. Native CAD face **2399** is the analytical Dirichlet boundary. All other native CAD boundary faces receive the analytical natural Neumann flux.

The manufactured non-affine quadratic scalar field is

\[
u_*(\mathbf{x})=\sum_{i=1}^3\left(\frac{x_i-o_i}{s_i}\right)^2,
\qquad
-\nabla^2u_*=-2\sum_{i=1}^3s_i^{-2}=f,
\qquad
g_N=\nabla u_*\cdot\mathbf{n}.
\]

Here \(o_i\) and \(s_i\) are the original source-mesh bounding parameters, written explicitly in the [machine-readable result](../data/v3_r313_nonaffine_refinement_20261105/attempt01/convergence_result.json). Conductivity \(k=1\) and source \(f\) are **mathematical manufactured quantities**, not actual Au electrical or thermal laws. Neumann flux is integrated from the *original* true triangle areas and oriented outward normals; the same physical surface triangle geometry and Dirichlet coordinates are used across levels. No source boundary-node relocation, source geometry change, interface deletion, or full-package PDE occurs.

## Bounded refinement and independent topology certification

An exactly conforming **1→4 barycentric/centroid split** was applied to every regional tetrahedron, and repeated once on all resulting tetrahedra. Each original tetrahedron acquires precisely one interior centroid; its original four triangular faces are **not divided**. The original 13,540 region-boundary facets therefore stay bitwise-identical as vertex triplets and external/intermaterial face markers remain untouched.

The [independent topology auditor](../data/v3_r313_nonaffine_refinement_20261105/attempt01/independent_topology.py) reconstructs the three meshes independently from R3.9 source, constructs every tetrahedron's four triangular faces, counts face incidence, and compares every reconstructed boundary triangle against the native source. This is separate code from the [solver implementation](../data/v3_r313_nonaffine_refinement_20261105/attempt01/convergence.py).

| Independent geometry check | Original L0 | Refined L1 | Refined L2 |
| --- | ---: | ---: | ---: |
| Tetrahedra | **25,905** | **103,620** | **414,480** |
| Nodes | 6,884 | 32,789 | 136,409 |
| Original boundary facets exactly retained | 13,540 | 13,540 | 13,540 |
| Nonmanifold tetrahedral faces | 0 | 0 | 0 |
| Zero/negative signed tetrahedra | 0 | 0 | 0 |
| Total bond-8 volume (mm³) | 0.002455683982 | 0.002455683982 | 0.002455683982 |
| Minimum normalized tetrahedral quality q | 1.38495e-4 | 7.99442e-5 | **3.26535e-5** |
| Tetrahedra with q < 0.05 | 17,908 | 74,310 | **322,451** |
| Fraction q < 0.05 | 69.13% | 71.71% | **77.80%** |

All source file SHA-256 values and the exact original face set are saved in the [R3.13 manifest](../data/v3_r313_nonaffine_refinement_20261105/attempt01/manifest.json). All historical mesh artifacts and failed prior trials remain unchanged.

## Actual non-affine finite-element accuracy and solver behavior

P1 tetrahedral stiffness is assembled from native tetrahedron Jacobians as \(K_{ij}=V\,\nabla N_i\cdot\nabla N_j\). The manufactured right-hand side consists of constant body forcing integrated over each element plus exactly integrated analytic triangular Neumann flux on the original unprescribed boundary. Homogeneous Dirichlet values are **not** assumed: exact analytical \(u_*\) is imposed on face 2399. A fixed SciPy `spilu(drop_tol=1e-5, fill_factor=16)` preconditioner with restarted GMRES is used for all levels, with a solver tolerance of \(10^{-9}\) and an independently audited true residual acceptance threshold of \(10^{-8}\). Level 2 stops after the registered 55 restarts × 60 inner iterations.

The error norm is not based on nodal residuals. The H¹-seminorm is evaluated by **exact integration** of the squared difference between the piecewise-constant P1 gradient and the analytical affine gradient \(\nabla u_*\) over all tetrahedra. Tetrahedral second moments permit exact integration of this quadratic integrand without quadrature sampling uncertainty. A separate [125-trial independent degree-2 tetrahedral Gaussian quadrature test](../data/v3_r313_nonaffine_refinement_20261105/attempt01/H1_integration_independent_check.json) agrees with the exact-moment implementation within **6.1×10⁻¹⁶ relative error**.

| Measured numerical quantity | L0 original | L1 4× cells | L2 16× cells |
| --- | ---: | ---: | ---: |
| Free FEM DOF | 3,812 | 29,717 | **133,337** |
| ILU-GMRES iterations | 9 | 32 | **3,300 (limit)** |
| True relative algebraic residual | 3.40e-11 | 3.46e-10 | **1.84e-7 (FAIL)** |
| Relative exact H¹-seminorm error | **1.631253%** | **1.627525%** | **NOT MEASURED: solver STOP** |
| Relative interior nodal L² error | 2.53e-5 | 1.52e-4 | NOT QUALIFIED |
| ILU L+U nonzero entries | 233,354 | 2,183,211 | 13,442,642 |
| Sparse assembly and solve time (reported where qualified) | 0.142 s | 0.761 s | ILU/GMRES alone 105.627 s |

The first refinement improves relative H¹ error from 0.0163125320 to 0.0162752500, a mere **0.2285% relative reduction** despite four times the tetrahedra and more than seven times the free degrees of freedom. The finer level is explicitly recorded as a failed solver gate; it is **not** assigned a numerical H¹ error. The total bounded experiment completed in **110.945 seconds** with peak Python RSS **741.3 MiB**, within its 280-second, 4-CPU/8-GiB limits; therefore the observed stop is **not a memory or wall-time budget failure**.

### Why this is not an asymptotic mesh-convergence result

Centroid splitting subdivides tetrahedral volume but **does not reduce the diameter of any original boundary triangle**. Consequently the global mesh diameter \(h_{\max}\) does not tend to zero under this refinement family, and shape regularity *deteriorates* (q_min falls 1.38×10⁻⁴ → 3.27×10⁻⁵). Even though the nested tetrahedral meshes remain conformal, they do not furnish a shape-regular, globally refining mesh family on which to infer the usual P1 finite-element convergence order.

The small H¹ error reduction between L0 and L1 does not establish solver or discretization accuracy for the whole 430-domain package; the level-2 linear solve did not pass its algebraic gate. Nodal errors worsening between L0 and L1 further caution against treating more elements as proof of accuracy.

**Scientific outcome: this specific fixed-surface centroid-refinement method is rejected as a practical route to spatial convergence qualification.** This is a valuable controlled negative result, not an acceptance failure of the original physical CAD or the exact-interface TetGen volume mesh.

## Preservation, limitations and next method

This milestone writes only separately versioned scripts, immutable source and output hashes, geometric readback, exact-gradient integration check, three per-level results, logs and a [consolidated machine report](../data/v3_r313_nonaffine_refinement_20261105/attempt01/convergence_result.json). The original R3.8/R3.9/R3.10/R3.11 meshes, R3.12 solver recovery, historical R3.3/R3.4 failures, frozen 824-solid STEP, derived BREP, all 378 finite contact witnesses, canonical 38-page Rev3 and issue #2 remain unchanged.

**Next method should not repeat centroid-only h-refinement.** A separately registered R3.14 should first evaluate a higher-order **p-enriched (P2) finite-element basis on the same piecewise-linear conformal geometry**, which preserves the original 320,522 surface triangles as geometric entities while introducing approximation DOFs on their vertices/edges. As a separate option, a conforming boundary-refining mesh hierarchy may be constructed only under an explicitly new source-face-parent/child ownership qualification, rather than pretending original face triplets are unchanged. For either option, assess non-affine manufactured H¹ and L² errors, operator condition and runtime at fixed memory limits, before any physical electrical/thermoelectric solver.

**No full-device electrothermal simulation was run. Electrical Gate B remains STOP; thermal C/D remain NOT RUN. Physical detector temperature, TEC cooling and OEM agreement remain unqualified.**
