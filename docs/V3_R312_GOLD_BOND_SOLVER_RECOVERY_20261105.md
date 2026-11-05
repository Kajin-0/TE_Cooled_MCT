# V3 R3.12 — Gold-bond solver recovery through incomplete-factorization preconditioning

**Date:** 2026-11-05. **Baseline commit:** `170b63ecdf4cc265c79112de4cd9116eb6b85725` (R3.11).  
**Verdict:** **PASS** for regional scalar Poisson algebraic and mixed-boundary manufactured-solution tests using ILU-GMRES. **Whole-package electrothermal PDE, mesh convergence, constitutive laws and physical predictions remain NOT QUALIFIED.**

This work resumes the R3.11 negative numerical result without regenerating any tetrahedra, changing the R3.8/R3.9/R3.10/R3.11 saved meshes, modifying source CAD or introducing electrical/thermal material models. All previous experimental failures and original results remain preserved. No Codex usage was required.

## Experimental contract and exact problem

The source of truth is [R3.11's saved mathematical finite-element benchmark](V3_R311_BOND8_CONDITIONING_20261105.md). The detector gold-bond 8 region is CAD volume **420**. The comparison holds the *same native face 2399* at homogeneous Dirichlet `u=0`, with natural homogeneous Neumann conditions on the other regional boundaries, unit scalar coefficient `k=1`, unit volumetric mathematical source `f=1`, and linear P1 tetrahedral shape functions. All coordinates are in **mm**; these coefficients are **not the actual electrical conductivity or thermal conductivity of gold**, and the boundary conditions are not qualified physical contact conditions.

For all three meshes (R3.9, R3.10 and R3.11), the resulting reduced matrix has **3,812 free degrees of freedom**, 3,072 fixed Dirichlet vertices and 43,206 nonzero stiffness entries for R3.9/R3.10 (42,930 for R3.11). The sources are pinned by the [R3.12 hash manifest](../data/v3_r312_solver_20261105/attempt01/manifest.json). Matrices are assembled from actual signed tetrahedron Jacobians and element `K_ij = V ∇N_i·∇N_j`; the maximum independently calculated affine-coordinate reproduction error is 1.46×10⁻¹¹ and relative matrix symmetry error is below 5×10⁻¹⁷.

The [bounded solver-comparison source](../data/v3_r312_solver_20261105/attempt01/solver_comparison.py) executed inside the already recovered FEM Docker runtime with **4 CPU, 8 GiB memory, no network and 180 s hard timeout**. Source mesh files were mounted **read-only**. The 3-case comparison took **2.51 s** with peak Python RSS **197.32 MiB**. It compares exactly the same assembled operator and right-hand side under four solver choices:

1. Sparse-direct `spsolve`, used only as an algebraic reference.
2. Jacobi-preconditioned CG, `rtol=1e-8`, maximum 2,500 iterations, preserving R3.11's failure.
3. SciPy `spilu(drop_tol=1e-3,fill_factor=8)` + GMRES, restart 60, `rtol=1e-8`.
4. SciPy `spilu(drop_tol=1e-5,fill_factor=16)` + GMRES, restart 60, `rtol=1e-8`.

ILU is not a symmetric preconditioner; **GMRES**, not CG, is used. No regularization, artificial anchoring or boundary-condition change was introduced.

## Measured solver results

| Same bond-8 mixed-BC operator | R3.9 | R3.10 | R3.11 |
| --- | ---: | ---: | ---: |
| Jacobi-CG iterations | 2,500 **FAIL** | 2,500 **FAIL** | 2,500 **FAIL** |
| Jacobi-CG final true relative residual | 6.314 | 6.400 | 6.720 |
| ILU (drop 1e-3, fill 8) GMRES iterations | **88** | **88** | **87** |
| ILU (drop 1e-3, fill 8) true relative residual | 4.40e-9 | 2.85e-9 | 4.88e-9 |
| Stronger ILU (drop 1e-5, fill 16) GMRES iterations | **10** | **11** | **10** |
| Stronger ILU true relative residual | **7.34e-9** | **7.99e-10** | **1.66e-9** |
| Stronger ILU relative solution difference to sparse direct | 2.13e-10 | 2.44e-10 | 9.29e-11 |
| Sparse-direct true relative residual | 1.33e-9 | 1.30e-9 | 1.29e-9 |

Residuals are independently recomputed as **`||A u − b||₂ / ||b||₂`** with the original *unpreconditioned* sparse matrix, not the solver's internal preconditioned stopping metric. Every strong-ILU run converged below `1e-8` and agreed with sparse-direct solutions to better than 3×10⁻¹⁰ in relative Euclidean norm. For the stronger ILU, the factorization is larger (roughly 230,000–237,000 combined L/U nonzeros), so 10 iterations do **not** imply the cheapest or most scalable solver at millions of degrees of freedom.

The previous R3.11 conclusion **remains correct for Jacobi-CG**: q-based local mesh optimization did not fix that particular solver failure. R3.12 demonstrates that a suitable algebraic preconditioner is sufficient to solve this *regional scalar* matrix. This is a solver improvement, not proof that R3.11's q-based mesh is better than R3.9.

## Independent mixed-boundary manufactured solution

To validate more than algebraic solver residual, a separate [manufactured-solution implementation](../data/v3_r312_solver_20261105/attempt01/manufactured_mixed_bc.py) reconstructed all **13,540 boundary triangles** of bond 8 directly from its tetrahedra and checked **exact triangle-set equality** against the original native CAD-region facets.

It prescribes the analytic harmonic field

\[
u_*(x,y,z) = x+2y-0.3z, \qquad \nabla^2u_*=0,
\]

with its actual values on native face 2399 and the **analytic nonzero Neumann flux** `∇u_* · n` on every other boundary triangle. Flux contributions are integrated over true oriented triangular faces, separately from the stiffness matrix. The integral of the flux over the closed region is approximately **1.39×10⁻¹⁷**. This experiment contains **no artificial volumetric source** and is analytically independent of the unit-source test.

| Manufactured mixed-BC test | R3.9 | R3.11 |
| --- | ---: | ---: |
| Exact affine solution discrete residual | 1.64e-14 | 1.65e-14 |
| Sparse-direct relative solution error | 3.70e-10 | 2.51e-10 |
| Strong-ILU GMRES iterations | **7** | **7** |
| Strong-ILU GMRES true relative residual | 4.90e-10 | 5.86e-10 |
| Strong-ILU GMRES relative error versus analytic affine solution | **3.10e-10** | **5.94e-10** |

This is independent evidence of correct regional P1 assembly, native-interface facet matching, outward-normal orientation, integrated Neumann boundary flux, and preconditioned solver accuracy. It is **not** a demonstration of asymptotic spatial convergence or detector-bond transport physics. Because affine harmonic functions are exactly representable by P1 elements, the very small errors do not predict accuracy on general nonlinear temperature or electric potential fields.

## Qualification limits and next gate

**R3.12 passes the narrow, explicit goal of finding a workable solver for a representative difficult regional operator under a fixed mathematical boundary-value problem.** It does not resolve the very poor tetrahedron shape distribution globally, establish finite-element spatial convergence, demonstrate electrothermal current/heat conservation across 430 domains, or determine an appropriate multilevel preconditioner for million-degree-of-freedom matrices.

The full R3.8, R3.9, R3.10 and R3.11 mesh candidates, exact 320,522 source facets, 430 source material attributes, 378 finite-contact witnesses, failed R3.11 Jacobi-CG results, historical R3.3/R3.4 failures, canonical Rev3 and issue #2 are unchanged. **Electrical Gate B remains STOP, thermal C/D NOT RUN and no physical detector or TEC operating temperature is qualified.**

**Next registered experiment (R3.13):** choose a representative *non-affine* regional diffusion manufactured solution (e.g., a polynomial or trigonometric function) and build a conservative one- or two-level **boundary-preserving** refinement hierarchy. Compare true energy or H¹-seminorm error and operator conditioning versus mesh size, with explicit runtime/RAM controls. Only then consider richer interface physics and a full-device discretization solver.
