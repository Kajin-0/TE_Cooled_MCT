# V3 R3.3–R3.4: verified surface and failed global 3D handoff

**Date:** 2026-11-05. **Baseline:** 3d7eb2a9bfd77d7e10d52034b77df402a4e0acad. **Scientific state:** STOP — no qualified whole-device tetrahedral mesh. This document supersedes provisional statements but does not alter historical results, protected R3/R2 meshes, the physical 824-solid STEP, the original 378 finite-contact witnesses, issue #2, or the canonical 38-page Rev3. No PDE/TEC/detector predictions were run.

## Source and R3.3 surface evidence

The saved R3.3 full surface mesh contains **320,522 linear triangles, 156,599 nodes, 2,440 source CAD faces and 430 closed computational-volume skins**. Native generation took 4.109 s; the original worker took 32.991 s / 662.824 MiB and recorded **FAIL GLOBAL SURFACE GATE; NO RETRY**. Preserve that FAIL: its normal-sampling and unmeasured intersection/readback gates were not validly passed by the original worker.

Separate post-hoc independent inspection of the same, unchanged MSH (SHA-256 3ee984051366990cb912c71e88332021a4c7b3f2cc1484f35ca546fd265d859b) established:
- Strict <1% CAD-area checks pass for 2,440/2,440 native faces (worst **0.2853343%**) and 2,422/2,422 R2 ancestors.
- Gmsh getClosestPoint() returned zero, non-positional UV in the original normal-check usage. Computing UV with getParametrization() removes the 82 apparent mixed-sign faces: **0/2,440 mixed**. All **251,176 triangles** on 100 curved faces maintain consistent local normal sign; smallest absolute normal cosine **0.99578727**. This does not waive CAD orientation, convexity or mesh quality.
- All 430 volume boundaries are closed and oriented (fresh-file incidence verification); zero originally duplicated triangle node triplets.
- A complete linear-facet BVH visited **930,338** BVH-node pairs, considered **19,032,493** broad candidate pairs and tested **2,228,647** filtered candidate pairs in **143.643 s**. Its floating-point predicate flagged 98 same-vertex contacts. Independent exact-rational tests of those flagged pairs rejected all 98 as strictly interior intersections. **Zero confirmed intersections** under the recorded BVH/coplanar tolerances; this is not an exact CAD Hausdorff guarantee.
- Minimum normalized triangle quality **0.0057734**; max edge aspect **300.002**. The 12 worst faces are thin sidewalls of cold-side Au, underside Au and header Ni; *3D element quality remains unqualified*.

Source: [post-hoc machine summary](../data/v3_r34_handoff_review_20261105/surface_posthoc.json). Original R3.3 MSH, logs and worker result remain preserved under data/v3_r33_surface_20261105/attempt_01 (not recopied into this evidence bundle).

## Two full-package 3D attempts: both STOP, no tets qualified

Both used **Gmsh 4.13.1**, Delaunay algorithm 1, recovered runtime image sha256:97526dcefe0324c06197ce2a2dc632840ddd27a06493c6220002a85fb7a9ef14, 4 CPUs / 8 GiB and hard timeouts, no PDE and no automatic retry. The rebuilt image is *not* bit-identical to the historical a0b22cf runtime.

| Distinct attempt | Measured outcome | Cause |
| --- | --- | --- |
| Original saved R3.3 MSH | STOP at **0.751 s**, **147.629 MiB**, no whole-device tet MSH | Curve-edge recovery failed because the imported boundary lacked CAD parameters |
| Separate reconstructed-parametric MSH | STOP at **2.746 s**, **238.680 MiB**, no whole-device tet MSH | Invalid boundary: overlapping/duplicated facets on surface **2360**, Cu/15 µm polyimide boundary |

In the original MSH merge, CAD parameters were missing on **14,747/14,747** classified 1D nodes and **139,111/139,111** classified 2D nodes. An isolated reconstruction re-added existing nodes and elements with Gmsh getParametrization() and Mesh.SaveParametric=1. Its output exactly retained existing classified-node positions, connectivity, element IDs and CAD owners, with **6.75e-14 mm** maximum parameter-to-CAD displacement and a successful independent saved-MSH readback in **25.36 s**. This solves missing parametric metadata, not 3D feasibility.

Critically, the full-model Gmsh generate(2) stage **changes the imported surface mesh despite Mesh.MeshOnlyEmpty=1**. Example: face **2360** changes from **7,018** unique input triangles to **310** output entries, only **264** unique (46 duplicates). Face 1 changes 90→92; face 2230 changes 260→164. The duplicated face2360 facets explain the second global3D STOP. The qualified R3.3 boundary itself has none of these duplicate triplets.

Evidence: [attempt 1](../data/v3_r34_handoff_review_20261105/original_volume_failure.json), [parametric reconstruction](../data/v3_r34_handoff_review_20261105/parametric_preflight.json), [attempt 2](../data/v3_r34_handoff_review_20261105/parametric_volume_failure.json), [handoff forensics](../data/v3_r34_handoff_review_20261105/parametric_handoff_forensics.json).

## Small boundary-preserving workflow fixtures: NOT YET QUALIFIED

A separate Gmsh discrete-surface createGeometry() route was tested on two actual Cu/15µm dielectric/gas fixtures, without changing the product geometry:

| Fixture | TRI3 before/after 3D stage | Tets | Strict preservation gate |
| --- | --- | --- | --- |
| Planar, three material regions | **632→634** | 1,114 | **FAIL** — triangles changed |
| Curved concentric Cu core / 15 µm annulus / gas | **2,960→0** in failed-state readback | 0 | **STOP** — discrete 1D boundary loop not closed |

Earlier simple-box tests produced tetrahedra but did not independently establish preserved surface identity. *Generating some tetrahedra is not a pass.* Tests of createTopology/classifySurfaces were inconclusive. [Recorded fixture results](../data/v3_r34_handoff_review_20261105/boundary_preserving_fixture_results.json).

## Next scientific gate

Do **not** launch another full-package 3D attempt until a representative curved, thin-wall Cu/polyimide/gas fixture demonstrates simultaneously: (1) exactly unchanged input boundary facets through tetrahedralization, including shared copper/dielectric/gas face ownership and periodic seams; (2) all intended volumes filled by positive-Jacobian tets; (3) no overlapping/duplicated facets; (4) per-material volumes within 1% of CAD; and (5) acceptable quality, memory and runtime. A meshing backend that treats input facets as truly immutable constraints is preferable to repeating Gmsh CAD remeshing. A subsequent global attempt requires a fresh bounded registration and independent saved-volume mesh audit. No electrical, thermal, constitutive or OEM validation follows from a mesh alone. Electrical Gate B remains STOP; thermal C/D remain NOT RUN. The canonical Rev3 stays frozen.

[Machine-readable evidence/checksum manifest](../data/v3_r34_handoff_review_20261105/summary.json) records all six copied post-hoc evidence files. All original failures and complete VPS execution logs remain separately archived.
