# Nominal TEC: P1 subface gas coupling

**Result: source TRI3/P1 geometric and conservative-load gates PASS; one conditional partial-cavity coupled solve PASS; complete cavity gas physics NOT QUALIFIED.** Only the original 0.40 × 0.40 × 0.50 mm, 29/11/4-couple package was used. The source geometry, P/N laws, previous fields and report are unchanged. The 3D metal electrical Gate B and the historical raw gas-flux failure remain FAIL/STOP.

## Source-mesh common refinement

The original source's 752 V3.24 unobstructed bare-ceramic rectangles were intersected with **both** source-side TRI3 meshes. The resulting common refinement has 6,109 nonzero convex overlap polygons. Every polygon is assigned one triangle on each side, with its original gas face, triangle and source node IDs. A polygon's exact area and centroid give the exact integral of each linear P1 shape function; the nonlinear temperature-dependent gas flux is evaluated at that polygon centroid and is therefore **a quadrature approximation**, not an exact integral of the nonlinear law.

| Gap | Original face tags | Source triangles, hot/cold | Registered area mm² | Overlay area error mm² |
|---|---|---:|---:|---:|
| C0–C1 | 7, 43 | 1,077 / 694 | 7.428063540 | −1.78e−15 |
| C1–C2 | 73, 91 | 762 / 328 | 5.497516601 | +1.78e−15 |
| C2–C3 | 103, 113 | 409 / 154 | 1.979438000 | −4.44e−16 |

All 3,424 source triangles have a unique adjacent original ceramic tetrahedron and the expected opposed outward z normals. Worst individual rectangle area discrepancy is 1.18e−16 mm², versus the registered 1e−5 mm² gate. An independently implemented triangle-fan integration reconstructs polygon areas, barycentric weights, source-node temperatures and heat loads; its maximum single-pair conservation residual is 1.70e−21 W and maximum nodal-load difference is 3.73e−20 W. The frozen-conductance P1 matrix passes symmetry, zero-uniform-temperature and positive-semidefinite controls. Vacuum, equal-temperature and accommodation controls pass. [Operator and independent receipt](../data/nominal_gas_p1_20261111/) include all polygons, node IDs, weights, fluxes and hashes.

An initial clipping attempt failed on a small polygon centroid because of cancellation in global-coordinate shoelace arithmetic. That failure and exact source are retained. The corrected calculation translates the polygon to a local origin before area/centroid evaluation; the tolerance and physical gates were not relaxed. A subsequent vectorized equal-temperature control exposed a 7.3e−21 W rounding artifact; evaluating P1 temperature differences relative to the first node makes the uniform-temperature control exactly zero. Both records remain in the evidence directory.

## Conditional coupled original package

One registered 145.3 s original-only full-system calculation used the 88 nonlinear P/N legs, four original spatial ceramic FEM domains, reduced source copper and leads, 300 K reservoir, 2 mW imposed detector heat, and matched terminal input 0.5956680349614825 W. The selected P1 gas patches use Kr at 100 Pa and accommodation 0.8. **All other gas boundaries are adiabatic in this diagnostic; the prior external and interstage gas proxies are disabled.** The earlier gray-radiation model is retained separately. This is a deliberately incomplete partial-cavity scenario, not a validated gas boundary or a full 3D cavity solution.

| Quantity | Conditional P1 partial-cavity result |
|---|---:|
| Current | 0.399960875 A |
| Terminal voltage | 1.489315763 V |
| Electrical input | 0.595668035 W |
| Hot ceramic | 303.744877 K |
| Upper ceramic | 218.591711 K |
| Detector mount | 218.659107 K |
| Sink heat | 0.589012548 W |
| Cold-leg Qc, before parasitics | 4.238392 mW |
| Selected gas C0→C1 / C1→C2 / C2→C3 | 2.534996 / 1.197643 / 0.511544 mW |

The saved original V3.20 proxy result was 219.368939 K, so this partial-cavity case is 0.709832 K lower. **That difference combines omission and redistribution of gas paths; it is not evidence of a real cooling improvement or total gas uncertainty.** Fourteen outer iterations reached a maximum nodal update of 1.976e−7 K. Independent source-node and scalar-gas reconstruction gives maximum stage residual 1.052e−9 W, global residual 9.15e−10 W, matched-power residual 6.40e−12 W, and gas nodal sum 4.68e−20 W. A second readback reconstructs all three source copper networks and both terminal wires, including net88's thermal-only middle branch. These validate the declared discrete equations, not the physical completeness of the cavity.

## Coverage and unresolved physics

The six gas face tags are **partially** represented: both sides of the paired patches total 29.810036 mm², or 3.3004% of the 903.215050 mm² registered gas boundary. No full gas face is entirely covered and no complete-cavity gas BC is qualified. The remaining 1,834 faces have no P1 gas patch, and the 173 V3.24 temperature-proxy-unresolved faces remain unresolved: 57 formed Cu, 56 joints/fillets, 28 lead/insulation, 23 die/carrier/attach and nine mount faces. Other provisional representations overlap this classification; the nominal 98.093% proxy area must not be read as qualified physical coverage. Eight lead-joint face assignments were independently cross-checked against actual source wire/land/pin contacts and the archived lead endpoint temperatures; a finite joint temperature drop is still unmeasured and not spatially modeled.

The 0.600 mm gap/Maxwell jump column approximation does not solve connected 3D gas transport: lateral paths can cross the selected vertical columns, accommodation is assumed, other gas surfaces are omitted, and the raw full gas-flux gate remains failed. The next useful step is to couple defensible surface temperatures and non-overlapping physical gas transfer for patterned metal, leads and enclosure, then perform a bounded sensitivity/coverage study. Do not treat this partial-cavity temperature as a prediction of the manufactured detector.

Reproduction: use the pinned recovered runtime and the exact source-mesh and executable hashes in [registration and contracts](../data/nominal_gas_p1_20261111/); `tests/test_nominal_gas_p1_v325.py`, `tests/test_nominal_gas_p1_coupler_v325.py` and `tests/test_nominal_gas_p1_results_v325.py` exercise analytic, source and saved-result gates without a new package solve. No CFD or new 430-domain solve was run.
