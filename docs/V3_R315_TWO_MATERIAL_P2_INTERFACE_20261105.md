# V3 R3.15 — Native two-material CAD interface: P1/P2 transmission and flux-conservation benchmark

**Date:** 2026-11-05 (America/Chicago). **Baseline:** `28a62ca26ac6181d4cb8907a3a56920c589604f9` (R3.14).  
**Scientific verdict: PASS** for a *synthetic two-material scalar diffusion transmission benchmark* on real conformal CAD-region geometry. **NOT QUALIFIED** for physical gold/composite conductivities, interfacial contact physics, coupled thermoelectric transport, mesh convergence or detector/TEC performance.

## Geometric source and material ownership

The actual registered CAD interface is **face 2349**, between:

| CAD volume ID | Source object | Source material |
| ---: | --- | --- |
| 410 | `det8_wedge_foot` | `COMPOSITE_MULTILAYER` |
| 420 | `detector_bond8` | `Au` |

The two source bodies were selected by actual source CAD identity, not a standalone fabricated interface fixture. Their saved source is the original **R3.9 conforming 430-region volume mesh**, with unchanged R3.8 node/face records and the same R3.7 registered PLC. Both source material-law fields remain **UNSET**; in particular the effective composite is not a validated homogeneous conductor.

The independently reviewed [native two-domain preflight](../data/v3_r315_interface_20261105/attempt01/native_interface_preflight.json) confirms:

| Property | Actual saved source |
| --- | ---: |
| Two-region tetrahedra | **26,053** (148 in region 410; 25,905 in region 420) |
| Union vertex count | 6,908 |
| Source interface CAD face | **2349** |
| Native conformal shared interface triangles | **48/48** |
| Distinct interface vertices | 49 |
| Native outer union triangles | 13,586 |
| Interface plane | \(z=5.7849\,{\rm mm}\) |
| Maximum interface-node deviation from plane | **0 mm** at saved precision |
| Saved planar triangulation interface area | 0.0002537429177 mm² |
| Source CAD interface area | 0.0002544690049 mm² |
| Area discrepancy | **−0.285334%** |

Every interface triangle matches *both* tetrahedral regions by the exact same three original node IDs; both sides are represented once each, with zero missing or extra source-interface facets. All source coordinates and registered material/face tags remain unchanged. The area discrepancy is the inherited prior sub-1% CAD-surface tolerance, not a new interface error.

The first preflight had two *audit implementation* errors: it initially categorized all two-sided tetrahedron faces as material interfaces, then failed to sort each tetrahedral face triplet **in-place** before grouping. Both initial STOP/diagnostic logs are retained. The corrected preflight distinguishes same-volume internal faces from genuine region-410/420 faces and verifies all 48 exact matches. No source mesh was modified or regenerated.

## Artificial two-material manufactured transmission test

For an explicitly synthetic conductivity ratio, set

\[
k_{410}=1,\qquad k_{420}=10
\]

in arbitrary consistent mathematical units. **These are not physical values for the gold bond or the composite multilayer.**

Define a piecewise quadratic field on the real two-volume union:

\[
u_r(x,y,z)=
A\big[(x-x_0)^2+(y-y_0)^2\big]+B(z-z_0)^2
+\frac{Q}{k_r}(z-z_0),
\]

where \(x_0=-0.35\,{\rm mm}\), \(y_0=0\), \(z_0=5.7849\,{\rm mm}\), \(A=0.025\), \(B=0.05\) and \(Q=1\) are registered mathematical parameters.

This field is continuous along the common plane, and the oriented normal-flux transmission condition holds exactly:

\[
[u]_{2349}=0,\qquad
k_{410}\frac{\partial u_{410}}{\partial z}
=k_{420}\frac{\partial u_{420}}{\partial z}=Q
\quad\text{at }z=z_0.
\]

Each source region uses independently specified exact forcing \(f_r=-\nabla\cdot(k_r\nabla u_r)=-k_r(4A+2B)\). Native source CAD face **2399** is assigned exact Dirichlet values. All other exterior facets receive the exact analytic Neumann flux, integrated with a degree-5 face quadrature. No explicit source term is placed on the internal face 2349; its flux is transmitted through shared continuous nodal/edge degrees of freedom.

P1 and P2 are assembled with the *same unchanged linear geometric tetrahedra*. P2 adds globally unique edge-based field degrees of freedom, including the shared interface edges; source TRI3 geometry remains straight and identical on both sides.

## Results from the same real two-region geometric mesh

| Measurement | P1 continuous linear | P2 continuous quadratic |
| --- | ---: | ---: |
| Geometric TET4 cells | 26,053 | 26,053 |
| Original geometric vertices | 6,908 | 6,908 |
| Total scalar field DOF | 6,908 | **46,661** |
| Free field DOF | 3,836 | **34,469** |
| Synthetic conductivity contrast | 10:1 | 10:1 |
| ILU-GMRES iterations | 8 | **11** |
| True original-operator relative algebraic residual | 9.35×10⁻¹¹ | **4.04×10⁻¹²** |
| **Relative H¹ gradient error** | 0.0066321860 | **1.2619081×10⁻⁸** |
| Relative RMS *one-sided normal-flux jump* at internal face 2349 | 0.0358152060 | **1.0868271×10⁻⁸** |
| Maximum relative normal-flux jump over interface triangles | 0.0364128 | **1.8294971×10⁻⁸** |
| Signed net interfacial mismatch integral | −9.09×10⁻⁶ | **2.58×10⁻¹²** |
| Interface field-trace continuity, maximum absolute side-to-side difference | ≈1.75×10⁻¹⁸ | **≈1.69×10⁻¹⁸** |

The independent H¹ error ratio is **525,568× lower with P2** for this specific polynomial manufactured solution. The RMS flux-discontinuity ratio is **3.295 million× lower**. These impressive factors primarily measure P2's ability to represent a **piecewise quadratic field exactly** on the unchanged straight-sided tetrahedra. They should **not** be generalized into the expected accuracy ratios of real semiconductor or TEC fields with unknown constitutive laws, nonlinearities, non-smooth contact sources or geometric curvature.

Both tests passed the original-matrix residual criterion of \(10^{-8}\), using the same ILU-GMRES settings as R3.14. The first full comparison completed in **4.864 s** with peak Python RSS **374.6 MiB** in the existing 4-CPU/8-GiB recovered FEM runtime. No Codex usage or extra compute was needed.

## Independent solution and interface audit

The entire benchmark was replayed in a separately preserved run, changing only the code required to save solved P1/P2 coefficient arrays. All numerical solution outputs, residuals, iteration counts, field errors, and interface jumps reproduced exactly; only run-duration/resource readings varied.

A **separate** [independent interface and H¹ auditor](../data/v3_r315_interface_20261105/attempt01/independent_interface_audit.py) reads those saved coefficients but does not call the original solver/assembly. It:

1. Rebuilds the exact native two-side tetrahedron adjacency for all 48 shared CAD-face triangles.
2. Recomputes both one-sided element gradients, outward face normals, and signed normal fluxes, and evaluates side-to-side trace differences.
3. Reintegrates the piecewise gradient error with a **216-point independent tetrahedral Duffy quadrature**, rather than the original positive four-point degree-2 rule.
4. Checks the saved P1/P2 source hashes and agreement of H¹ error and flux mismatch with the original benchmark.

Its [signed results](../data/v3_r315_interface_20261105/attempt01/independent_interface_audit.json) independently reproduced:

| Audit metric | P1 | P2 |
| --- | ---: | ---: |
| Relative H¹ error, separate 216-point integration | 0.00663218603182963 | **1.26190806456200×10⁻⁸** |
| RMS relative normal flux mismatch | 0.0358152060009104 | **1.08682712294675×10⁻⁸** |
| Maximum absolute trace discontinuity | 1.75×10⁻¹⁸ | **1.69×10⁻¹⁸** |

The close agreement rules out the original integration procedure as the sole source of the observed P1/P2 improvement.

## Strict scientific limitations and next gate

**Qualified in R3.15:** a conformal two-region native-interface mesh with a single shared continuous P1/P2 field, internally conservative analytic transmission conditions under artificial coefficient discontinuity, independently audited gradient/normal-flux errors, and accurate regional algebraic solver convergence.

**Not qualified:** measured conductivity of either source material, anisotropic or thermoelectric interface constitutive behavior, finite electrical or thermal contact resistance, global energy conservation for physical 430-domain junctions, accurate curved CAD geometry, mesh-resolution convergence, or electrical/thermal/thermoelectric device performance. Real heterogeneous materials may have potential jumps, finite interfacial conductance, Seebeck coupling and local contact heating; *none* was included in this idealized transmission test.

The original 824-solid STEP, R3 derived 430-domain BREP, all historical R3.3/R3.4 failure/STOP evidence, original R3.8–R3.14 mesh/scientific records, 378 finite-contact witness records, frozen 38-page canonical Rev3, and issue #2 remain unchanged. **Electrical Gate B remains STOP; thermal C/D remain NOT RUN.**

**Recommended R3.16:** establish a controlled finite-contact-resistance interface model on this same source CAD face (e.g., a mixed trace/jump law), and test independent integrated current/heat-flux balance before extending the assembly to the full package. Separately validate actual material/contact coefficients and register a non-polynomial transmission benchmark to avoid treating P2 polynomial exactness as proof of general convergence.

[Evidence manifest](../data/v3_r315_interface_20261105/attempt01/manifest.json) includes the original/source hashes, scripts, logs, two solved coefficient arrays, preregistration, the preserved initial preflight failures, and the independent audit.
