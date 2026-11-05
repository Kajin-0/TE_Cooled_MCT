# V3 R3.8 — First complete 430-region constrained TetGen volume mesh

**Date:** 2026-11-05. **Baseline:** `141bc7775e4b0e048e497b5318dd6c1b3c6cb50a`. **Scientific verdict: PASS recorded geometric 3D gates; FAIL to qualify for FEM on tetrahedral quality. No PDE.**

This is the first saved global tetrahedral representation of the complete **430-domain** derived analysis BREP. The physical 824-solid STEP, 2,440 native faces, 378 finite-contact witnesses, original R3.3 surface (including its historically failed producer result), R3.4 failed handoffs, R3.5/R3.6 fixtures, master 38-page Rev3, and issue #2 remain preserved. The original R3.7 PLC was read-only throughout. Only one actual global TetGen tetrahedralization was launched, with no fallback or repeated meshing attempt.

## Preregistered computational conditions

The immutable input is the [R3.7 corrected-seed PLC](../data/v3_r37_plc_preflight_20261105/seed_refined_01/R37_430_domains_surface_seed_refined.poly), SHA-256 `f36eb5efc49318058f176d4661caa9e1029f5238fe3f43806d6cc911ca1deeb3`. The independent input readback certified 156,599 original nodes, 320,522 TRI3 facets, 2,440 CAD face identifiers, 430 valid uniquely located region seeds, and all 378 contact witnesses.

TetGen 1.6 was compiled from pinned `libigl/tetgen` commit `e05aca7df74e3f531bc35733ed87d36d437266c5`; executable SHA-256 `361f99ea481c3bf2ce630a181fdc883a564f0e6698bb8654bdf60ee07712d08f`. Its recovered FEM runtime Docker image has ID `sha256:97526dcefe0324c06197ce2a2dc632840ddd27a06493c6220002a85fb7a9ef14`, **not** the original historical image digest.

The exactly registered invocation was `tetgen -pYYAC -V R38_430_domains.poly` inside Docker with **4 CPUs, 8 GiB hard RAM and swap limits, 7.5 GiB early-memory guard, 900 s wall limit, 6 GiB output cutoff, no network, and one attempt**. The actual recorded TetGen run completed in **25.7496 s**. Docker sampled roughly **985 MiB** during execution; TetGen separately estimated about **558 MB** of internally used memory. The 'maximum number of tetrahedra' line in the TetGen log (**1,580,488**) describes a peak memory allocation/capacity, **not the saved mesh count**.

## Saved mesh and independent qualification

| Measure | Actual saved result | Registered gate |
| --- | ---: | --- |
| Saved linear tetrahedra | **1,043,314** | Under 3,000,000: PASS |
| Saved mesh nodes | **156,765** | Input 156,599 exactly retained: PASS |
| Newly added interior nodes | 166 | None on original constrained facets: PASS |
| Nonempty CAD material regions | **430/430** | PASS |
| Preserved input facet triplets and native face markers | **320,522/320,522** | Exact equality: PASS |
| Incorrect native facet/tetrahedron material owners | **0** | PASS |
| Missing or extra outer/intermaterial tetrahedron facets | **0** | PASS |
| Nonmanifold tetrahedron face incidence (>2) | **0** | PASS |
| Inverted or zero signed tetrahedral volumes | **0** | PASS |
| Material regions with CAD-volume error ≥1% | **0** | PASS |
| Largest absolute material-volume error | **0.4971617%**, `pin4` | PASS |
| Finite-contact witness records preserved | **378/378** | PASS |
| Global post-tet nonadjacent tetrahedron overlap audit | NOT RUN | UNQUALIFIED |
| PDE / electrical / thermal solver | NOT RUN | UNQUALIFIED |

TetGen's `-C` consistency check independently reported connected mesh boundaries, segment/tetrahedron connectivity and a consistent mesh. Our [separate saved-file audit](../data/v3_r38_global_tetgen_20261105/attempt01/saved_mesh_audit.json) reads the `.1.node`, `.1.ele`, and `.1.face` outputs, independently matches every face triplet/marker to the original PLC, constructs **all four faces of every tetrahedron**, verifies manifold incidence and actual tetrahedron-side material IDs, checks all 430 CAD-volume integrals and evaluates every tetrahedron's signed volume and normalized shape metric.

The **first audit implementation had a software defect**: it called `np.sort(face_triplets,axis=1)` without assigning the returned array, thereby creating a false appearance of millions of unmatched faces. Its failed log and script remain archived. The corrected auditor sorts each face *in place*, and an independently cleaned final version reproduced the same measured PASS. Neither correction changes the original TetGen files or constitutes another meshing attempt.

## Element quality — FEM readiness remains blocked

Mean-ratio tetrahedral quality was computed using

\[
q = \frac{12(3|V|)^{2/3}}{\sum_{e=1}^{6}\ell_e^2},
\]

with a regular tetrahedron giving q = 1. Signed volumes were checked separately.

| Distribution metric | Observed |
| --- | ---: |
| **Minimum q** | **0.0000265662** |
| 1st percentile q | **0.00157219** |
| 5th percentile q | **0.00859248** |
| Median q | **0.151659** |
| Tetrahedra with q < 0.01 | **56,586** |
| Tetrahedra with q < 0.05 | **280,430 (26.9%)** |
| Tetrahedra with q < 0.10 | **409,723** |
| Largest TetGen aspect ratio | 29,718 |
| Smallest TetGen dihedral angle | 0.0023255° |

The low-quality population is concentrated in several critical components, not principally the insulated sleeves:

| Material/region category | Tetrahedra with q < 0.05 |
| --- | ---: |
| Cavity gas | **71,249** |
| Kovar-pin domains | **63,840** |
| Copper domains | **57,371** |
| Effective axial Kovar/Ni/Au pin domains | **50,726** |
| Gold detector-bond domains | **35,461** |
| Polyimide candidate sleeve domains | 34 |

Within the two separate gold detector-bond domains, **70–74%** of tetrahedra are below 0.05; their local minimum qualities are around `1.38e-4` and `2.51e-4`. The worst tetrahedron overall is in the cavity gas, with q ≈ `2.66e-5`. See the [430-region breakdown and worst 30 elements](../data/v3_r38_global_tetgen_20261105/attempt01/region_quality.json).

Positive Jacobians and exact facet ownership do **not** imply acceptable finite-element conditioning or mesh-converged predictions. The present output is therefore a **qualified geometric volume-mesh candidate**, **not an accepted FEM analysis mesh**. No electrical Gate B retest, thermal gates C/D, material/interface law fitting, TEC temperature, detector temperature, or OEM-comparison claim is authorized.

## Archives and reproducibility

The full set of saved TetGen `.1.node`, `.1.ele`, `.1.face` and `.1.edge` output files is archived as a **22 MB compressed, checksummed artifact**, [`saved_tetra_mesh.tar.zst`](../data/v3_r38_global_tetgen_20261105/attempt01/saved_tetra_mesh.tar.zst). The archive's SHA-256 is `8843feda378680b7adf32857d305b2b4206f707d3ce2cb4c0c016b40ee71fe1e`. The input PLC is separately retained under R3.7; it is not duplicated in the archive.

The [manifest](../data/v3_r38_global_tetgen_20261105/attempt01/manifest.json) covers the archived results, single-attempt preregistration, runner, exact output hashes, resource samples, TetGen log, final independent geometric auditor, quality diagnostic and the preserved initial audit failure. Original full raw output remains in the **untracked** VPS attempt folder `/var/tmp/v3_r38_global_tetgen_20261105/attempt01/work/`.

## Next scientific gate

R3.9 should be **a separate, bounded, read-only quality investigation of this exact saved 1,043,314-tet volume mesh**, prioritizing the gas cavity, leads, pins and detector bonds. Candidate local interior connectivity operations must preserve every one of the 320,522 source facets and 2,440 markers, all 430 material IDs and volumes, and all 378 contact witness interfaces. Unlike the R3.6 three-material fixture, the full mesh contains 166 additional interior nodes, so quality improvement can investigate strictly constrained internal relocation in addition to local flips. Require robust intersection checks, positive volumes, and independent quality improvement evidence, rather than arbitrarily smoothing or deleting thin physical layers. Run actual PDE solvers only after an explicit mesh-quality/conditioning and conservation-convergence gate.

The exact historical original producer R3.3 FAIL and prior R3.4 STOP receipts remain unchanged; the canonical Rev3 stays frozen and issue #2 OPEN. Electrical Gate B remains STOP; thermal C/D remain NOT RUN.
