# V3 R3.10 — Fixed-interface interior-node relocation on the 430-domain mesh

**Date:** 2026-11-05. **Baseline:** `1520e1a637ec7de271684dddf54b09ab514ee8d9` (R3.9).  
**Verdict:** PASS independent geometric 3D checks on a limited interior-coordinate derivative. **Optimization impact is small; FEM quality remains NOT QUALIFIED.**

This milestone tests whether relocating the only freely movable interior nodes can materially improve the quality of the validated R3.9 430-domain tetrahedral mesh. The source CAD/STEP, 320,522 original external and material-interface facets, 2,440 native CAD face identities, 378 source finite-contact witnesses, all existing node tags/connectivity, original R3.8 volume mesh, original R3.9 optimized mesh, Rev3 master and issue #2 remain untouched. No new tetrahedralization or PDE was run. A new `.node` derivative is archived separately and is paired with the unchanged R3.9 `.ele` mesh and R3.8 registered `.face` table.

## Read-only free-node census: an important practical limit

The [independent R3.10 census](../data/v3_r310_interior_relocation_20261105/attempt01/free_node_census.json) constructed a node-to-element incidence map for all **1,010,119** R3.9 tetrahedra and compared the volume nodes against every saved constrained triangular facet.

| Quantity | Verified result |
| --- | ---: |
| Mesh vertices | 156,765 |
| Vertices on registered material/exterior facets (locked) | **156,599** |
| Free interior vertices | **166** |
| CAD regions containing these interior vertices | 5 |
| Incident tetrahedra per free node (min / median / max) | 12 / 188 / 2,396 |
| R3.9 tetrahedra with mean-ratio q < 0.05 | 241,754 |
| Poor-quality tets incident to at least one free node | **13,378 (5.53%)** |
| Poor-quality tets with no free node | **228,376 (94.47%)** |
| Very poor tets q < 0.01 with a free node | 3,753 of 53,490 |

Thus **interior-node smoothing alone cannot resolve most bad tetrahedra**. Nearly all quality defects are geometrically constrained by exterior and intermaterial face nodes or internal connectivity involving only locked nodes. Modifying these nodes directly would violate the source-facet acceptance contract.

## Registered, bounded relocation experiment

The [saved relocation optimizer](../data/v3_r310_interior_relocation_20261105/attempt01/interior_relocation.py) operated on the exact saved R3.9 mesh and used a deterministic one-pass ranking of all 166 free vertices by their incident poor-element counts. For each free vertex, it considered discrete trust fractions toward its immediate neighbor-vertex mean and median. A move was accepted **only** if:

- every affected tetrahedron retained strictly positive signed volume and finite mean-ratio quality;
- the complete local star's signed volume changed by less than the configured conservative tolerance;
- no local increase occurred in q < 0.01 or q < 0.05 counts and no deterioration of the local minimum q occurred;
- the move actually reduced the local number of q < 0.05 tetrahedra;
- all 156,599 fixed exterior/intermaterial vertices retained their original binary64 coordinates exactly.

The optimizer ran for **3.12 seconds**, within its hard 140-second execution limit, 4-CPU allocation and 8-GiB memory limit; peak Python RSS was **434.6 MiB**. It accepted **66/166** interior-node relocations and generated a separately stored `.node` table without changing tetrahedral connectivity.

## Measured outcome

| Quantity | R3.9 baseline | R3.10 derivative |
| --- | ---: | ---: |
| Linear tetrahedra | 1,010,119 | **1,010,119 unchanged** |
| Node coordinates modified | — | **66 interior nodes only** |
| Source exterior/material interface facets | 320,522 | **320,522 unchanged** |
| Poor tetrahedra (q < 0.05) | 241,754 | **241,514 (−240, −0.0993%)** |
| Very poor tetrahedra (q < 0.01) | 53,490 | **53,420 (−70)** |
| Minimum mean-ratio quality | 0.000138495 | **0.000138495 (unchanged)** |
| Material-volume drift from R3.9 | — | <9.8×10⁻¹⁵ relative |
| Populated CAD regions | 430 | **430** |
| Nonpositive signed tetrahedra | 0 | **0** |
| Worst absolute CAD-volume error | 0.4972% | **0.4972%** |

An **independent saved-mesh audit**, rather than the optimizer's self-check, again reconstructed all tetrahedral face incidences and matched them against the original R3.7 PLC and registered material identities. Its [complete result](../data/v3_r310_interior_relocation_20261105/attempt01/independent_saved_mesh_audit.json) reports: zero missing/extra constrained or interface facets, zero material-owner mismatches, zero nonmanifold faces, and zero nonpositive tetrahedra. The 378 finite contact witnesses remain registered through the exact original native-face markers.

The optimized mesh **remains unfit for qualified multiphysics predictions**: 241,514 tetrahedra still have q < 0.05, and the worst q remains (1.38495\times10^{-4}). No nonlocal tetrahedron-intersection check, stiffness-matrix conditioning, FE error estimate or convergence study has been conducted. The geometry pass must not be confused with a physics pass.

## Provenance and next decision

The [R3.10 manifest](../data/v3_r310_interior_relocation_20261105/attempt01/manifest.json) retains the original-source SHA-256, a compressed `.node` derivative and accepted-move audit, scripts, CPU logs, complete node census and independent geometric audit. The [R3.10 derivative archive](../data/v3_r310_interior_relocation_20261105/attempt01/candidate_nodes_and_moves.tar.zst) contains the new node-coordinate table and all 66 applied moves. Use the **unchanged R3.9 `.ele`** plus **unchanged R3.8 `.face`** for reconstructing the derivative; do not substitute the earlier R3.8 element connectivity.

**Next gate:** stop further generic interior-node smoothing. The dominant remaining quality issues require a carefully gated alternative such as same-facet local tetrahedral topology optimization, quality-constrained internal point insertion, or documented local thin-feature numerical reductions that retain actual material/contact identity. A representative difficult region should first demonstrate improved q-distribution *and* a real discretized PDE conditioning/convergence benchmark before propagating methods to 430 domains. Any proposed boundary-node change must be disallowed unless a separately registered process requalifies the exact original facet geometry and ownership.

**No PDE solve, electrothermal device performance estimate, revision to canonical Rev3, or electrical Gate B/thermal C-D qualification occurred.** Historical R3.3/R3.4 failures remain preserved.
