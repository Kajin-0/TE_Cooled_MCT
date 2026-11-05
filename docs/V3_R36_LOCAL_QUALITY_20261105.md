# V3 R3.6 — Executed bounded 3→2 tetrahedral quality screening

**2026-11-05 • Baseline:** `530c5e09df1fe51a63733aba82a3011a42d7478d`  
**Status:** PASS for local three-material curved-fixture connectivity improvement. **Not qualified for FEM; full 430-domain package remains NOT RUN.**

## Scope and method

This milestone uses the exact [R3.5 refined curved copper / 15 µm polyimide / gas PLC fixture](V3_R35_TETGEN_CONSTRAINED_FIXTURE_20261105.md) from its archived `.node`, `.ele` and `.face` files. The new [standard-library-only optimizer](../scripts/v3_r36_local_quality.py) executes deterministic same-material **3-to-2 tetrahedron flips**. Each accepted flip changes three tetrahedra surrounding an internal edge to two sharing the opposite triangular face, with no new node and no coordinate movement.

Candidate checks enforce local cavity boundary identity, positive signed tetrahedral volumes, local volume conservation within 1e-9 relative tolerance, improved local quality minimum, and a reduction in the number of tets with normalized mean-ratio quality below 0.05. Three passes each compare all original exterior and intermaterial facets, including tetrahedral material owners, and every material's total signed tetrahedron volume against the baseline. No full-device tetrahedralization, Gmsh remeshing, global intersection traversal or PDE was run.

### Measured results on the VPS

The Python source compiled successfully and the complete R3.5 fixture execution completed in approximately **2.79 s**. The script stored its own results and emitted **193** accepted local operations.

| Metric | R3.5 accepted fixture input | R3.6 connectivity candidate |
| --- | ---: | ---: |
| Tetrahedra | 15,676 | **15,483** |
| Accepted 3→2 flips | 0 | **193** (113 + 53 + 27) |
| Elements with quality below 0.05 | 377 | **176** (−53.3%) |
| Elements with quality below 0.01 | 18 | **7** |
| 1st-percentile normalized quality | 0.02106 | **0.04207** |
| Median normalized quality | 0.30619 | **0.31382** |
| Minimum normalized quality | 0.008017 | **0.008017, unchanged** |
| Constrained external/material interface facets | 7,106 | **7,106, identical** |
| Nonpositive signed tetrahedra | 0 | **0** |
| Material-volume changes | None | Below numerical roundoff |

There are 3,493 nodes in the original fixture and each belongs to a constrained boundary or material interface; conventional fixed-boundary node smoothing consequently has zero free interior vertices. The original q<0.05 population is strongly concentrated in the copper core rather than the thin polyimide annulus. The current 3→2 screening reduces this tail by improving internal connectivity, **not by refining thin materials or removing interfaces**.

### Reproducible artifacts

- [Candidate mesh](../data/v3_r36_quality_20261105/attempt01/candidate.ele) and accompanying `candidate.node` / `candidate.face` tables.
- [Complete pass-by-pass numerical result](../data/v3_r36_quality_20261105/attempt01/result.json).
- [Operations log](../data/v3_r36_quality_20261105/attempt01/flips.json) and [file SHA-256 manifest](../data/v3_r36_quality_20261105/attempt01/manifest.json).
- [R3.5 input provenance](../data/v3_r35_tetgen_plc_20261105/manifest.json).

Reproduction from repository root (the output directory must not already exist):

```bash
python3 scripts/v3_r36_local_quality.py \
  --prefix data/v3_r35_tetgen_plc_20261105/refined/coaxial_15um.1 \
  --out /tmp/v3_r36_replay_unique
```

The implementation refuses to overwrite results. The preserved R3.5 parent fixture, historical R3.3/R3.4 stops, original 824-solid STEP, source mappings, 38-page canonical Rev3 and issue #2 remain unchanged.

## Strict interpretation and remaining blockers

This is a validated **fixture-scale connectivity and conserved-boundary operation**, not a proof of a globally nonintersecting tetrahedral complex, a minimum-quality threshold, linear-system conditioning or physical detector prediction.

The global minimum q remains 0.008017, and 176 tetrahedra remain below 0.05. No numerical PDE/solver-conditioning convergence or global tetrahedron-overlap audit has been executed. The project continues to require quality-tolerant refinement with the same constrained surface, followed by a registered, read-only full **430-domain PLC** input audit: inside-volume seed per domain, all 2,440 native face identities, all 378 contacts, exact shared-facet ownership and a quantified tetrahedron/memory budget. Only after those independent gates may a bounded whole-package meshing attempt be considered.

**Electrical Gate B remains STOP; thermal C/D remain NOT RUN.** No simulated detector or TEC operating temperatures are qualified by this study.
