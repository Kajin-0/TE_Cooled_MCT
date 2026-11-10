# Original TEC: source-mapped gas subset and lead joints

**Result: executable one-way nominal gas subset PASS; full native gas coupling STOP; no new coupled temperature.** This study uses only the original 0.40 × 0.40 × 0.50 mm, 29/11/4-couple source geometry and its saved V3.20 nominal operating state. The original 824 solids, source fields and historical results are unchanged. No alternative geometry is evaluated.

## Thermal representations at source gas faces

The [1,840-face map](../data/nominal_gas_coupler_20261110/nominal_face_temperature_map.json) retains each source face tag, location, area and source-registry SHA. Of these, 1,667 faces (885.990098 of 903.215050 mm², **98.093% of area**) receive a **provisional** temperature representation; 173 faces (17.224952 mm², 1.907%) remain unresolved. Area coverage is dominated by 300 K housing/header proxy assumptions and is **not** qualified-physics coverage. **Zero native gas boundary conditions are physically qualified or installed.**

The previously unresolved eight lead-joint faces now have exact original CAD contact witnesses: land joints connect TEC lead1/9 to net0/net88 Au pads, and pin joints connect those leads to pin1/9 Au. Their assigned temperature is the V3.20 lead's corresponding pad or header endpoint, with a declared zero-joint-drop assumption. It is not a measured solder temperature. All source contact names, weights and temperatures are recorded; net88's middle Cu foot remains thermal-only and no model is changed.

Four ceramic fields and conductor-adjacent ceramic temperatures are sampled by nearest archived source node at the face centroid; the latter assumes no local metal–ceramic temperature difference and no resolved film spreading. Individual P/N side faces use linear endpoint temperature interpolation, **not** a reconstructed nonlinear BVP profile. Individual solder bodies use their adjacent leg endpoint; die/carrier use their existing lumped nodes; cap/header/pins use the existing 300 K reservoir hypothesis. Formed tabs, wire/insulation exteriors and other inadequately represented surfaces remain explicitly unresolved rather than being forced to an isothermal net. Node weights, distances, locations, assumptions and unresolved reasons are in the map.

## Geometry-derived, non-overlapping bare-face subset

`scripts/tec_nominal_v324_subset.py` derives vertical source-coordinate columns between each pair of ceramics. Every source solid whose z-range intersects an interstage slab is projected and excluded: exact source rectangles for box bodies, conservative AABBs for curved bodies. The annular cap is omitted only after checking the whole working rectangle lies inside its 7.1 mm inner radius. This yields mutually exclusive bare-face patch cells with actual archived original R3 gas-face pairs (7,43), (73,91), (103,113). The sample rectangles are checked against all source solid bounding geometries and are disjoint by construction. Gaps are the actual 0.600 mm bare ceramic planes; no arbitrary metal-film subtraction is made where these selected cells are bare.

| Gap, hot to cold | Unblocked source-column subset area mm² | Cells | Original face tags |
|---|---:|---:|---|
| C0–C1 | 7.428064 | 431 | 7, 43 |
| C1–C2 | 5.497517 | 244 | 73, 91 |
| C2–C3 | 1.979438 | 77 | 103, 113 |

This is a **geometric subset of vertical, solid-free columns**, not the whole connected gas volume and not a rigorous bound on actual heat flow. A gas molecule or continuum diffusion path can cross column boundaries; the bounding boxes can over-exclude free space. No metallized face is silently included as bare ceramic. Exterior and all other cavity surfaces are adiabatic **only in the subset diagnostic**; existing V3.20 results and their separate overlapping-possible proxies are unchanged.

The executable gas law uses the existing Kr Eucken/NIST-derived conductivity and Maxwell-type temperature-jump approximation: `G = k A/(L + 2 b)` and `Q = G(Th − Tc)`. It is positive and pairwise reciprocal, rejects invalid geometry/pressure/accommodation, gives zero at zero pressure and equal temperature, and approaches the bulk-conduction limit at high pressure. The jump/accommodation model is a conditional engineering approximation in the transitional regime, not a validated molecular gas transport solution.

## Actual saved-field, one-way calculation

The 752 source-derived cells are evaluated against **actual saved V3.20 nominal ceramic fields**, selecting the nearest ceramic surface node to each cell center; the largest nearest-node lateral distance is 0.1784 mm. This is an approximate quadrature on saved fields, not a new FEM solve. For 100 Pa Kr, the computed subset hot-to-cold link heat is:

| Accommodation hypothesis | C0→C1 mW | C1→C2 mW | C2→C3 mW |
|---|---:|---:|---:|
| 0.5 | 1.900574 | 0.918993 | 0.401021 |
| 0.8 | 2.519773 | 1.188742 | 0.506549 |
| 1.0 | 2.826754 | 1.317665 | 0.555253 |

At 0.8, corresponding heat **into** C0/C1/C2/C3 is −2.519773/+1.331031/+0.682193/+0.506549 mW, summing to zero to numerical precision. Accommodation is a sensitivity hypothesis, not measured uncertainty; these three links are not a prediction or bound on complete cavity gas heat. The baseline fixed-field `V3.20` original stage-wise interstage and external proxies do not describe these same surfaces and cannot be added to this subset.

The [source-residual adapter](../data/nominal_gas_coupler_20261110/source_residual_adapter.json) replaces the original interstage terms by the subset links and disables all original exterior gas terms in the **archived original solver's balance equations only**, leaving radiation unchanged. At the old temperatures the four changed stage/die residuals are +3.4440, +1.9078, +1.6733 and +0.2046 mW; bath rejection algebra changes by +3.8280 mW. These nonzero residuals demonstrate that the archived solution is not an equilibrium for this partial boundary model. This is not a coupled solve or a new detector temperature. The conditional subset law and residual adapter are executable without modifying the frozen solver.

**Why no coupled solve:** source-derived selected patches do not yet have conservative TRI3 subface quadrature and localized loads in the four ceramic FEM matrices; the remaining gas-facing metal, leads, housing and connected-gas transport also lack qualified boundary allocation. Replacing all original gas terms and interpreting a new package temperature would falsely present omitted surfaces as physically adiabatic. The exact next integration is source-face triangle/rectangle clipping with area and P1 load checks for these six face tags, then explicit non-overlapping ownership and temperature interpolation for the remaining gas interfaces. Preserve original native 3D metal electrical Gate B and raw gas flux FAIL/STOP.

[Registration, source mappings, source-field samples, code hashes and tests](../data/nominal_gas_coupler_20261110/) preserve this checkpoint. No OpenFOAM or full-system solve was run. The updated report's geometry diagram uses all 58/22/8 original P/N centers; its two-glyph section is explicitly labeled representative.
