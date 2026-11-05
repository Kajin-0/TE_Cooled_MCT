# V3 R3.11 — Detector-bond mesh quality versus actual scalar-FEM conditioning

**Date:** 2026-11-05. **Baseline:** `9ef3fbfe4721bdb27a2b118f5d9bb8bdec8f8824` (R3.10).  
**Scientific verdict:** targeted gold-bond **geometric mesh PASS**; representative mixed-boundary scalar-FEM iterative-solver gate **FAIL**. **No qualified electrothermal device PDE.**

R3.11 tests a critical distinction: whether local improvements to tetrahedron mean-ratio quality measurably improve the behavior of an actual assembled finite-element operator. The physical 824-solid STEP, 430-domain BREP, all 320,522 registered exterior/intermaterial facets, 2,440 source face markers, 378 contact witnesses, original R3.8/R3.9/R3.10 meshes, historical R3.3/R3.4 failure receipts, canonical 38-page Rev3 and issue #2 remain unchanged.

## Representative region and methods

The two actual gold detector-bond domains have the poorest regional normalized tetrahedron-quality distributions. R3.9 bond 8, native volume 420, contains **25,905 tetrahedra**, 6,884 unique nodes and **17,908 tetrahedra with q < 0.05**. Bond 7, volume 418, contains 22,655 tetrahedra, with 16,533 below 0.05.

Two independently assembled benchmark families use the saved linear tetrahedra. The local finite-element operator is unit-conductivity scalar Poisson/Laplace, not physical detector or TEC transport. Each element's stiffness is assembled as `K_ij = V grad(N_i)·grad(N_j)`, with signed tetrahedral volumes checked positive.

**Benchmark A: Dirichlet on all region boundaries.** The remaining systems have only 43 free interior nodes (bond 7) and 112 (bond 8). A manufactured harmonic solution `u(x,y,z) = x + 2y − 0.3z` with boundary values prescribed exactly shows maximum nodal error below 8×10⁻¹⁵. This validates the basic finite-element assembly, but fixes nearly all surface nodes, masking the conditioning difficulties associated with thin and constrained regions.

**Benchmark B: mixed conditions on bond 8.** Apply homogeneous Dirichlet to the largest registered native face, **face 2399 (6,048 surface triangles; 3,072 nodes)**, and zero natural Neumann on its remaining surfaces, with unit volumetric source `f=1`. The reduced sparse stiffness matrix has **3,812 free degrees of freedom**, with **43,206 structural nonzero entries**. Use Jacobi-preconditioned conjugate gradients (CG) with relative tolerance 10⁻⁸ and limit 2,500 iterations. A sparse direct solve serves as an independent algebraic-residual comparison; this is *not* a physical measurement or a qualified convergence study.

## Three-way numerical comparison

| Metric | R3.9 (baseline) | R3.10 (moved interior nodes) | R3.11 (targeted 3→2 flips) |
| --- | ---: | ---: | ---: |
| Whole-device tetrahedra | 1,010,119 | 1,010,119 | **1,009,877** |
| Whole-device q < 0.05 | 241,754 | 241,514 | **241,469** |
| Whole-device q < 0.01 | 53,490 | 53,420 | **53,369** |
| Global minimum q | 0.000138495 | 0.000138495 | **0.000138495** |
| Bond-8 tetrahedra | 25,905 | 25,905 | **25,663** |
| Bond-8 q < 0.05 | 17,908 | — | **17,623** |
| Bond-8 q < 0.01 | 7,369 | — | **7,248** |
| Mixed-BC CG iterations | 2,500 (limit) | 2,500 (limit) | 2,500 (limit) |
| Mixed-BC CG relative residual at limit | **6.314** | **6.400** | **6.720** |
| Mixed-BC solver gate | **FAIL** | **FAIL** | **FAIL** |

The R3.11 intervention evaluated 1,148 three-tetrahedron edge stars within *gold detector bond 8 only*, identified 247 locally admissible same-facet positive-volume flips and accepted **242 nonoverlapping conservative 3-to-2 flips** in a single bounded pass. The new derivative modifies **only tetrahedral connectivity**, never node coordinates, CAD faces or material boundaries. Mean-ratio q < 0.05 is improved by 285 tetrahedra, corresponding to only **1.59% of the bond-8 baseline poor-element count**; the global minimum q is unchanged. A first setup attempt stopped on a source element-hash alias mismatch before writing a candidate; its log is preserved.

An [independent full saved-mesh audit](../data/v3_r311_bond8_conditioning_20261105/attempt01/saved_mesh_geometric_audit.json) verifies the R3.11 candidate has **1,009,877 positive-volume tetrahedra**, **430/430 populated regions**, *exactly all 320,522 registered source triangle triplets and markers*, zero tetrahedral nonmanifold facets, zero missing/extra shared-interface facets, zero material-owner mismatches and unchanged maximum 0.4972% CAD-volume error (pin 4). All 378 finite contact witnesses remain identifiable. This is a **geometric PASS**, not a FEM PASS.

### Numerical interpretation

The restrictive all-boundary-Dirichlet benchmark found modest condition numbers that **worsened after R3.10 smoothing**:

| Reduced stiffness condition metric | R3.9 | R3.10 |
| --- | ---: | ---: |
| Bond 7 unscaled spectral condition | 6.86 | **7.62** |
| Bond 8 unscaled spectral condition | 15.44 | **24.99** |
| Bond 8 Jacobi-scaled condition | 4.28 | **5.01** |
| Bond 8 Jacobi CG iterations, relative tolerance 10⁻¹⁰ | 30 | **33** |

With the harder mixed-boundary arrangement, the reduced bond-8 operator remains extremely difficult for Jacobi CG. Sparse direct solves yield algebraic residuals around **1.3×10⁻⁹**, while Jacobi CG does not converge by 2,500 iterations and returns residuals greater than six. A read-only shift-invert eigensolve on R3.9 found an eigenvalue of approximately **5.71×10⁻⁸**, indicating a weakly constrained mode. An independent tetrahedron-edge graph check found **one geometrically connected bond-8 region**; the stiffness graph has multiple algebraic blocks due to sparse coupling, not demonstrated geometric disconnection. Plain smallest-magnitude ARPACK did not converge within 1,500 iterations; the successful shift-invert calculation and failed ARPACK run are both preserved in the record.

**Interpretation:** a lower count of low-q tetrahedra does **not** imply better linear-system conditioning, and no claim of a successful PDE qualification is justified. The current mixed-BC setup is a controlled model problem only; its artificial prescribed face and homogeneous Neumann walls are **not** actual detector-bond electrical/thermal boundary conditions. The sparse-direct solve confirms numerical solvability to a small algebraic residual under this test but does not establish usable iterative conditioning or converged physical predictions.

## Evidence and reproducibility

The [R3.11 manifest](../data/v3_r311_bond8_conditioning_20261105/attempt01/manifest.json) provides SHA-256 and byte size of all archived artifacts. The [candidate connectivity archive](../data/v3_r311_bond8_conditioning_20261105/attempt01/candidate_bond8_mesh_and_flips.tar.zst) contains the replacement `R311_430_domains.1.ele` and all 242 accepted flips. It is to be combined only with the **unchanged R3.8 original node/face records**, not R3.10 relocated coordinates. The retained source and logs cover:

- Complete read-only all-Dirichlet manufactured-solution and unit-source benchmark for bonds 7 and 8.
- Mixed-Dirichlet–Neumann Poisson benchmarks comparing R3.9, R3.10 and R3.11.
- Sparse-direct and CG residuals, graph connectivity and eigensolver diagnostics.
- Original failed source-hash setup log, corrected targeted-mesh derivation and independent geometric/audit pass.

## Next scientific decision

**Stop promoting tetrahedral q-count reduction as the primary acceptance target.** The more important next gate is a reliable regional operator with scientifically relevant boundary conditions, controlled preconditioning (e.g., algebraic multigrid or incomplete-factorization when verified), and a genuine mesh-resolution/solution-convergence experiment. Investigate whether the small eigenmode is a physical thin-direction mode, an under-anchored boundary configuration, or poor numerical scaling, using independent reference problems and material/contact laws before advancing to device PDE.

The current global mesh is geometrically preserved but **not FEM qualified**. Electrical Gate B stays STOP, thermal C/D remain NOT RUN, detector/TEC temperatures are not qualified, and canonical Rev3 remains frozen. No whole-package solver was launched in this milestone.
