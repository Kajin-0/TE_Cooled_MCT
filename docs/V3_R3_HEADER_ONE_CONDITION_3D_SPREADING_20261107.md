# V3 R3.9 original-source 3D Kovar header spreading: one registered condition

**Date:** November 7, 2026. **Baseline:** 72e5104c5bcdde24e3bdaf0992698633d6d6f554.
**Status:** Single-domain numerical PASS; **as-built thermal sink boundary and coupled TEC prediction STOP**.

[Source-hashed calculation](../data/v3_r3_header_spreading_20261107/attempt01/result.json), [registration](../data/v3_r3_header_spreading_20261107/attempt01/registration.json), [manifest](../data/v3_r3_header_spreading_20261107/attempt01/manifest.json), [replayable FEM source](../scripts/v3_r3_header_one_condition.py), [setup-only initial failure](../data/v3_r3_header_spreading_20261107/attempt01/run.log), [single completed solve log](../data/v3_r3_header_spreading_20261107/attempt01/run_02.log), and [prior hot-mount source audit](V3_R3_HOT_MOUNT_THERMAL_READINESS_20261107.md).

## Original R3 geometry and boundary

The frozen R3.9 global tetrahedral mesh has 1,010,119 TET4. The actual source Kovar header **volume386** is a 47,702-tetrahedron, 16,277-node submesh extracted without remeshing. On the unchanged registered original source surface, **face2228** is the header/Ni finish contact (1,000 TRI3, 37.21 mm²), and **face2225** is the external header underside (9,617 TRI3, source CAD 333.96070 mm², source mesh 334.00611 mm², +0.0136% area difference).

Solve steady \(\nabla\cdot(k\nabla T)=0\), using constant **17.3 W/(m·K)** generic room-temperature Kovar conductivity (bulk proxy, NOT independently identified as-built alloy). Apply exactly **0.5870297615 W** uniform inward heat over face2228, taken unchanged from the **previous conditional R3 nominal 0.4 A / 5 K/W / CAD wires-ON** reduced scenario (not a measurement). Fix the **entire header underside face2225 to 300 K** as an intentionally hypothetical isothermal fixture. All remaining header surfaces are insulated. The Ni/Au composite finishes, solder, alumina, actual sink contact and all other package domains are **excluded**.

The P1 weak system uses original TET4 gradients, exact tetra volumes, integrated Neumann surface TRI3 loads, Dirichlet reduction and conjugate gradient / Jacobi with relative convergence 1e-10. There is no material fitting, variable BC adjustment, new mesh or global multiphysics PDE.

## Quantitative numerical result

| Observable | Value |
| --- | ---: |
| Original source header tetrahedra / used nodes | 47,702 / 16,277 |
| Underside fixed / free P1 nodes | 5,195 / 11,082 |
| Triangulated header volume | 501.03855 mm³ |
| Original CAD-model header volume | 500.94105 mm³ |
| Input heat and sink reaction | +0.5870297615 W / −0.58702976149 W |
| TEC-facing face area-weighted mean temperature | **300.92576665 K** |
| TEC-facing source-face min/max nodal temperature | **300.38415 / 301.20624 K** |
| Header maximum temperature | 301.20624 K |
| **Header-only effective spreading resistance, mean contact temperature rise divided by heat input** | **1.57703529 K/W** |
| Relative source/sink reaction power closure | **4.8872×10⁻¹²** |
| Discrete energy quadratic/work relative consistency | **6.1287×10⁻¹⁶** |
| Max free-node residual | 4.726×10⁻¹³ W |
| Negative-orientation TET4 | 0 |

The solution demonstrates a nonuniform **real source-CAD 3D conduction field** under the declared scenario. The prior uniform-column reference values (0.260 K/W assuming a full-area column; 2.408 K/W assuming a 36 mm² column) are not rigorous upper/lower bounds on a true spreading calculation. The actual 3D result of 1.577 K/W is **model-dependent**, not a replacement for a measured header-to-sink thermal resistance.

## Numerical and physical limitations

A single original R3.9 mesh was used. The existing global mesh has shape-quality deficits, so energy closure and iterative convergence establish internal discrete conservation, **not mesh independence or spatial approximation accuracy**. No 3D h-convergence, measured temperature calibration or actual fixture-contact data are available. The entire underside isothermal condition may be physically optimistic or incorrect depending on real clamp/sink footprint and contact resistance.

The previously used **5 K/W effective sink** parameter in the reduced TEC model encompasses the whole assumed hot-ceramic-to-ambient pathway. **Do not simply add 1.577 K/W to 5 K/W**; that would double count a component. The prior 208.985 K conditional die temperature has **not** been updated by this uncoupled header calculation.

The as-built mounting still requires: validated exterior contact pattern and sink boundary, header material grade and k(T), source solder thermal properties and void fraction, Ni/Au effective multilayer tensors, original four solid-solid interface thermal contact laws, actual TEC pad heat distribution, and verified calorimetry/temperature response.

## Source identity, reproduction, and final qualification

The saved registration pins SHA-256 digests for the extracted unchanged R38 source nodes/surface facets, R39 source 3D tets, six independently archived input sources and the exact solver script. For read-only replay, extract those three original mesh inputs from their existing source tar.zst archives into '/var/tmp/mct_r3_header_3d_20261107', mount that directory unchanged, and run the solver source with its archived registration and result path in --verify-only mode.

The first container invocation failed **before** calculating any matrix because the host mesh path was not mounted inside the container; original failure is preserved. The sole subsequent solve after fixing the mount produced the archived result. No additional solve conditions were attempted.

**Geometric and one-condition 3D header heat conduction: numerical PASS. Real mounted hot-side BC: STOP. Full 430-domain coupled thermal C/D: NOT RUN. Original electrical P1 Gate B: FAIL/STOP; P2 candidate: STOP. Physical detector operating temperature: UNQUALIFIED. No new source CAD, re-meshing, contact-law release or Codex use.**
