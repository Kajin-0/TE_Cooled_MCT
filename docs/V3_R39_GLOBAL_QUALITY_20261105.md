# V3 R3.9 — Global tetrahedral quality optimization, one conservative pass

**Date:** 2026-11-05. **Baseline:** `f01cb53571afaa57afe0e764c11e539bda847225`.  
**Result:** independent **geometric 3D PASS** for the optimized candidate; **FEM conditioning, convergence and physical predictions remain NOT QUALIFIED**.

This milestone modifies *only the internal connectivity* of the archived [R3.8 whole-package 430-domain tetrahedral mesh](V3_R38_GLOBAL_TETGEN_20261105.md). It does not reconstruct the original CAD, rerun TetGen, alter any source node position, change the 320,522 registered external/intermaterial triangular facets, reduce thin physical layers, or execute a PDE. The frozen 824-solid STEP, R3 analysis BREP, all 378 finite contact witnesses, R3.3/R3.4 historical STOP evidence, original R3.8 mesh, canonical 38-page Rev3 and issue #2 remain unchanged.

## Method and bounded execution

The [R3.9 source](../data/v3_r39_quality_20261105/attempt01/optimizer.py) reads the protected TetGen R3.8 `.1.node` and `.1.ele` files with pinned SHA-256 evidence. A complete scan of 6,259,884 tetrahedral edge-incidence entries finds **1,274,134 unique edges**. Of those, **161,927** have exactly three incident tets, **148,610** are entirely within one material region, and **50,418** touch at least one tetrahedron with mean-ratio quality q < 0.05.

Each proposed **3-to-2 flip** replaces a three-cell ring around an interior edge with two cells across an internal triangle, after verifying the same three enclosing tetrahedral-pair faces and exactly five distinct vertices. Admission requires:

- all tetrahedra in the same native CAD material region;
- an identical local triangulated cavity boundary, so source exterior and material interfaces cannot be changed;
- strictly positive tetrahedral signed volumes and total local volume conservation to 1e-9 relative tolerance;
- an improved local minimum q and a reduction in count of q < 0.05 elements, without increasing the count below q < 0.01;
- disjoint operations within this **one** bounded pass, preventing simultaneous competing edits.

The initial optimizer screening encountered a Python set-constructor `TypeError` **before writing any candidate**; the failed log is preserved and the literal was corrected. The corrected run was separately recorded, required **17.94 seconds**, evaluated 50,418 possibly relevant edges, and found 39,362 locally admissible flips. A deterministic nonoverlapping selection accepted **33,195** operations. The optimization was constrained to 4 CPU, 8 GiB and a 240-second hard timeout, and produced an immutable separate candidate.

## Measured quality improvement

| Quantity | Protected R3.8 input | R3.9 optimized derivative |
| --- | ---: | ---: |
| Total tetrahedra | 1,043,314 | **1,010,119** |
| Accepted 3-to-2 flips | — | **33,195** |
| Poor tets, q < 0.05 | 280,430 | **241,754** |
| Relative reduction in q < 0.05 | — | **13.79%** |
| Very poor tets, q < 0.01 | 56,586 | **53,490** |
| Minimum q | 0.0000265662 | **0.0001384952** |
| 1st percentile q | 0.00157219 | **0.00157315** |
| 5th percentile q | 0.00859248 | **0.00882781** |
| Median q | 0.151659 | **0.160381** |
| Inverted or zero signed tets | 0 | **0** |
| Worst absolute CAD volume error | 0.497162% | **0.497162%** |

**All 430 material regions remain populated.** The maximum measured change in any region's mesh volume from the parent was less than **7×10⁻¹⁴ relative**. Actual independent saved-candidate re-auditing reproduced the baseline facet and material owners without missing, duplicated, spurious or nonmanifold outer/internal-interface faces.

The quality improvement is substantial at q = 0.05, but limited at the bottom percentile. **241,754 of 1,010,119 tetrahedra (23.93%) still have q < 0.05**. The new worst element lies in a gold detector bond, with q ≈ 1.38×10⁻⁴. No FE stiffness-matrix conditioning, elementwise PDE error, mesh-convergence or whole-mesh nonadjacent tetrahedron overlap search was performed.

## Region-level differences

| Region | R3.8 q < 0.05 | R3.9 q < 0.05 |
| --- | ---: | ---: |
| Cavity gas | 71,249 | **67,304** |
| TEC copper lead 9 | 35,453 | **31,108** |
| TEC copper lead 1 | 21,275 | **18,378** |
| Detector gold bond 7 | 17,152 | **16,533** |
| Detector gold bond 8 | 18,293 | **17,908** |
| Kovar pin 4 | 12,517 | **9,723** |
| Polyimide sleeve 1 | 13 | **0** |
| Polyimide sleeve 9 | 21 | **0** |

These gains indicate that internal connectivity can be improved without deleting or coarsening the 15 µm polyimide sleeves or changing contact areas. Most remaining low-quality elements are concentrated in cavity gas, lead/pin metals and Au detector bonds.

## Independent verification and archives

The [R3.9 independent saved-mesh audit](../data/v3_r39_quality_20261105/attempt01/independent_saved_mesh_audit.json) builds all four triangular faces of every saved candidate tetrahedron, then compares the resulting exterior/intermaterial facet complex to the untouched R3.7 input PLC and the registered CAD owner identities. Its measured result is:

| Gate | Candidate outcome |
| --- | --- |
| All 320,522 original facet triplets and markers | PASS — exact |
| 430/430 populated material volumes | PASS |
| All registered 378 finite contact witnesses | PASS |
| Constrained surface node coordinates unchanged | PASS |
| Missing or extra tetrahedral interface facets | 0 |
| Native CAD face/tetrahedral region owner mismatches | 0 |
| Nonmanifold tetrahedral facets | 0 |
| Nonpositive tetrahedral volumes | 0 |
| Max absolute CAD material-volume discrepancy | 0.497162%, `pin4` |

The [candidate archive](../data/v3_r39_quality_20261105/attempt01/candidate_mesh_and_flips.tar.zst) contains the replacement R3.9 `.1.ele` and all 33,195 accepted local operations; the corresponding `.node` and `.face` records must be taken from the **unchanged** [R3.8 complete saved-mesh archive](../data/v3_r38_global_tetgen_20261105/attempt01/saved_tetra_mesh.tar.zst). The [R3.9 SHA-256 manifest](../data/v3_r39_quality_20261105/attempt01/manifest.json), [preflight census](../data/v3_r39_quality_20261105/attempt01/edge_feasibility.json), [full per-region quality table](../data/v3_r39_quality_20261105/attempt01/per_region_quality.json), preregistration, and failed initial code-check log are retained. The original R3.8 archive and all earlier scientific evidence remain unchanged.

### Next gate, not yet authorized as a pass

R3.10 should determine whether **quality-constrained, local interior-node relocation** or additional validated 2-to-3/3-to-2 topology changes can improve the distribution, especially the gold detector bonds and cavity gas. Any new derivative needs an independent global saved-mesh structural and intersection audit, preserved all-source contact/face owners, a real stiffness-matrix condition and convergence assessment, and a stop gate on element quality. Do not accept a mesh for physically predictive electrothermal FEM solely because its tetrahedra have positive volumes.

**Electrical Gate B is still STOP; thermal C/D remain NOT RUN; no detector temperature, electrical load, TEC cooling or OEM accuracy is qualified.** Canonical Rev3 remains frozen and issue #2 stays open.
