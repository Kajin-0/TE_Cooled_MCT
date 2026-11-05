# V3 R3.7 — 430-volume TetGen PLC preflight

**2026-11-05 | Baseline: `8b5e2ee` | Outcome: PASS for constrained PLC input geometry and seed preflight; NO whole-device tetrahedra or PDE.**

This milestone converts the **unchanged, archived R3.3 320,522-triangle surface MSH** into an explicit TetGen piecewise-linear complex (PLC) with 430 nonoverlapping region attributes, then independently reads the PLC back against registered source geometry. It is a *preflight only*: TetGen was **not invoked for whole-device tetrahedralization**, and no thermal, electrical or detector simulation was run. The original R3.3 worker FAIL and subsequent R3.4 failures remain historically valid. The frozen 824-solid physical STEP, 378 finite contacts, canonical 38-page Rev3 and issue #2 are unchanged.

## Source and construction

The [R3.7 production script](../scripts/v3_r37_plc_preflight.py) loads the exact source R3 CAD BREP and untracked protected R3.3 surface MSH. Its source SHA-256 is recorded in the [manifest](../data/v3_r37_plc_preflight_20261105/manifest.json). For each native face, it uses the already certified shared triangulation once and attaches the native face identifier as TetGen facet marker. It uses CAD volume IDs 1–430 as TetGen region attributes, preserving the original domain-to-material mapping.

The original R3.3 MSH is **not committed as a duplicate** in this milestone. The separately versioned final PLC is [archived in GitHub](../data/v3_r37_plc_preflight_20261105/seed_refined_01/R37_430_domains_surface_seed_refined.poly), along with a [complete face-to-owner, material and contact provenance map](../data/v3_r37_plc_preflight_20261105/seed_refined_01/face_owner_contact_provenance.json).

| Verified R3.7 input quantity | Result |
| --- | ---: |
| Original surface nodes | **156,599** |
| Original TRI3 facets, each occurring exactly once | **320,522** |
| Native CAD face markers | **2,440** |
| Volume/material region records | **430** |
| Native shared interface faces | **2,397** |
| Native exterior faces | **43** |
| Triangles on two-owner internal faces | **172,414** |
| Triangles on one-owner exterior faces | **148,108** |
| Original finite-contact witness records validated | **378 / 378** |
| Duplicate triangle node triplets | **0** |
| Per-volume boundary edges of incidence other than 2 | **0** |
| Missing/ambiguous region attributes | **0** |
| Original CAD/mesh changed | **No** |

Full-face ownership and per-domain edge-incidence checks also appear in the independent [serialized PLC readback report](../data/v3_r37_plc_preflight_20261105/seed_refined_01/independent_plc_readback.json). They do not prove that all eventual TetGen interior faces will be manifold; that requires the future saved tetrahedral mesh.

## Interior point selection and clearance

CAD volume centroids work for **409** domains, one bounding-box midpoint works for another, but **20 domains** require inward normals from a shared native boundary triangle because their centroids are not inside the requested material. This includes the native cavity gas, both 15 µm polyimide jackets, thin contacts and several nonconvex solids.

Every seed is verified with Gmsh's native CAD `isInside(3,tag,point)`, followed by a uniqueness check against all other intersecting volume bounding boxes and their corresponding native CAD regions. The original PLC and its complete results are archived separately. An independent CAD `getClosestPoint` clearance audit found **six** seeds only 0.10–0.12 µm from a boundary. The [R3.7 seed-clearance derivative](../scripts/v3_r37_seed_refine.py) moved only those six seeds, without moving nodes or modifying facets; all six remained uniquely inside their intended volumes.

The revised final PLC independently revalidated all **430 seeds** and records minimum nearest-CAD-boundary clearance **0.000500000000000167 mm (0.500 µm)**, against a provisional threshold of 0.500 µm. The two polyimide shells and the cavity gas were also checked. This is a practical numerical precaution, not a proven universal bound on TetGen region classification tolerance.

The original PLC is preserved on the VPS at `data/v3_r37_plc_preflight_20261105/attempt01/R37_430_domains_surface.poly`. The checked final PLC and its revised 430 seed records are separately archived under `seed_refined_01/`. Neither file is an output volume mesh.

## Resource estimate and limitations

R3.5's small fixture produced **15,676 tetrahedra from 7,106 surface facets**. Extrapolating the same crude ratio to 320,522 facets gives approximately **707,078 tetrahedra**. Sensitivities of 2× and 4× that ratio are **1,414,157** and **2,828,315** tetrahedra. These figures are **heuristic only**; 430 material regions, curved periodic seams, thin metal finishes, complex domain nesting, and facet-recovery constraints can cause far greater counts, poor-quality elements or fatal PLC recovery. These estimates are **not a certified upper bound** or a demonstrated fit to the previous 3-million-tet / 8 GiB target. Whole-device peak RAM, runtimes, minimum tetrahedron quality and conditioning are all NOT MEASURED.

The R3.6 small-fixture optimizer improved the number of elements with quality below 0.05 but left q_min = 0.008017. No 430-domain quality or conditioning can be claimed from the present PLC.

## Reproducibility, boundaries and next gate

- The [read-only PLC builder](../scripts/v3_r37_plc_preflight.py) checks BREP face owners, MSH hashes, facets, contact tags, material mapping and unique CAD-region seeds.
- The [independent PLC auditor](../scripts/v3_r37_readback.py) re-parses TetGen's text PLC, checks triangle markers/uniqueness and 430 closed skins, computes actual CAD-boundary clearance and records sensitivity estimates.
- The [final revised-PLC auditor](../scripts/v3_r37_final_readback.py) independently checks the final changed-seed derivative.
- Machine-readable records and source hashes: [manifest](../data/v3_r37_plc_preflight_20261105/manifest.json).

**Next gate before one authorized global TetGen attempt:** qualified conservative memory/runtime and triangle-ownership safeguards; a dry-run PLC input acceptance check that demonstrably does not create volume elements or rewrite facets; validated region attribution, preserved finite contact markers, and hard limits on TetGen output. The first actual tetrahedralization must be registered as a separate experiment with a single attempt, no fallback, full saved tetrahedral Jacobian/facet/material audit and a preserved failure archive if it stops.

**Electrical Gate B remains STOP; thermal C/D remain NOT RUN.** The physical material laws and predicted TEC/detector operating temperatures are not qualified.
