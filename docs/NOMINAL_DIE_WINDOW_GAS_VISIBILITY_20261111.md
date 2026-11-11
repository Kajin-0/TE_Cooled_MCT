# Original TEC/TO: die-to-window gas visibility

**Scope:** source-native, original 0.40 × 0.40 × 0.50 mm reference only. A conservative die-to-window surface subset is connected to the existing V3.25 ceramic-P1 gas model; it is not a complete cavity, a 3D gas-field solution or manufacturer validation. The original 3D metal electrical Gate B and native-gas raw-flux gate remain FAIL/STOP.

## Source surfaces and occlusion

A prioritized outer-cavity path was selected because the window is warm in the existing reservoir model and the detector mount is cold; this is a source-based opportunity, **not a demonstrated ranking** against unmodeled foil, side-wall or carrier paths. Original native gas face 2335 is the detector top (solid 408) and face 2410 is the window underside (solid 423). Their actual R38 surface triangles have unique R39 owner tetrahedra and outward normals +z and −z, respectively. Source z values are 5.77625 and 9.65000 mm: the normal gap is 3.87375 mm. The 76 die triangles cover 0.9958 mm² (CAD agreement to roundoff); 722 window triangles cover 27.292937 mm², −0.1711% relative to the 27.339710 mm² CAD face. The selected detector footprint lies strictly inside the source window circle and 7.1 mm cap-shell inner radius.

All 824 original source-solid bounding boxes were screened against the full die-to-window z interval. Ten intervening contact, wedge and wire bodies have their **complete** conservative x-y bounding projections excluded with a 0.1 µm margin; the cap shell is excluded by its exact annular hole. Thus, subject to correctness of source body bounding boxes, no accepted vertical prism intersects a source solid. Bounding boxes intentionally over-exclude possible open space. Each surviving rectangle is intersected with both actual TRI3 meshes; 301 common polygons cover **0.694599734 mm² on each facing surface**. The independently accumulated die-side area matches to 3.34e−16 mm²; an independent triangle-fan and source-node readback reproduces the geometry and P1 weights. The die/window face identities are unique and distinct from the six V3.25 P1 ceramic gas faces. Their vertical extent starts at 5.77625 mm; the highest existing ceramic gap ends at 4.88425 mm, so the new prisms do not overlap the old ceramic columns in three-dimensional space.

The polygons use source mesh triangles and P1 integrals for ownership/area; because the prior package treats the die and window as lumped thermal nodes, no invented 3D die or window temperature field is implied. The window is assumed fixed at 300 K, not solved or experimentally measured. The geometric subset is a conservative **area subset**, not a bound on real cavity heat: molecules can move laterally, reflect and collide outside vertical prisms. Remaining cavity surfaces are not made adiabatic in reality; they are omitted only in the conditional model.

## Conditional gas law and fixed-field check

For krypton the existing Eucken/NIST-derived conductivity and Maxwell-style jump approximation are applied independently to the die/window pair, with assumed accommodation α and `Q = k A (Twindow − Tdie) / (L + 2b)`. Equal and opposite node loads sum exactly to zero. On the saved V3.25 state (die 218.659107 K, window assumed 300 K, 100 Pa), α = 0.5 / 0.8 / 1.0 gives **0.106412 / 0.112874 / 0.115206 mW** into the die. The pressure-zero and equal-temperature controls give zero; reverse temperature reverses heat flow. This is a model sensitivity to chosen accommodation, not a statistical uncertainty interval or total gas-leak bound. Radiation remains a separate pre-existing gray proxy and can act on the same physical surface as a distinct mechanism.

## Coupled original-only result

One original-only 88-leg/four-spatial-ceramic matched-power solve included the original V3.25 ceramic-P1 columns plus the new die/window subset, with 300 K bath, 100 Pa Kr, α=0.8, 2 mW die load and 0.595668035 W input. It converged in 14 outer iterations with maximum spatial update 1.984e−7 K. The independently reconstructed heat budget gives:

| Quantity | V3.27 conditional result |
|---|---:|
| Die temperature | 218.693303 K |
| Stage-2 cold-interface node | 218.605250 K |
| Carrier node | 218.623662 K |
| Hot ceramic node | 303.745534 K |
| Current / voltage / input | 0.399969325 A / 1.489284298 V / 0.595668035 W |
| Die/window gas into die | 0.112833 mW |
| Existing three ceramic gas links | 2.534821 / 1.197341 / 0.511163 mW |
| Sink rejection | 0.589121821 W |
| Max stage / global energy residual | 1.06e-09 / 9.18e-10 W |

Compared with the V3.25 partial-cavity die result, this added conditional path changes die temperature by **+0.034196 K**. This is the response to one declared supplemental model path, not a physical error bound or experimental result. The window supplies the equal-and-opposite pair heat. Independent audits also reconstruct the three Cu networks and two leads; the old gas proxies remain off.

**Node-label correction:** the `top_K` key in the earlier V3.25 and inherited V3.27 independent audits refers to the *carrier* source node, not the stage-2 cold-interface node. V3.25's 218.591711 K carrier and 218.573820 K stage-2 cold node are distinct. Historical data and reports are preserved; the [node identity audit](../data/nominal_gas_visibility_v327_20261111/node_label_audit.json) records both explicitly.

**Saved-result metadata clarification:** inherited `internal_gas_geometry_proxy` and `source_3D_ceramic_gas_radiation_heat_spread` descriptions still name the unused earlier gas proxy. The executed gas operator uses the 0.600 mm source P1 patches and this die/window subset; the saved effective-area array describes the separate gray-radiation proxy. The [metadata receipt](../data/nominal_gas_visibility_v327_20261111/result_metadata_clarification.json) preserves the original output while identifying the applied operators and saved P1 nodal loads.


## Limitations and next source gate

Only 31.199236 mm², or **3.45424%** of the 903.21505 mm² source gas-facing area, is represented by the existing two-sided 752 ceramic patches plus these die/window patches. Other gas surfaces are adiabatic **in this diagnostic only**. The copper surface temperature mapping remains conditional, the window boundary is assumed, and no lateral gas transport, molecular scattering distribution, natural-convection field or validated full-cavity exchange is solved. Existing external 3 mm/interstage gas proxies are disabled to avoid double counting. No conclusion is drawn about a measured detector temperature or physical operating optimum. The next useful step is a source-CAD obstruction-screened **carrier or top-ceramic to window/roof** path with its actual local temperature representation, preserving disjoint surface areas and the same energy audit; wall-to-side and foil-to-ceramic routes also need verified opposing patches and temperatures.

The frozen source SHA identities, 301 polygons, blocker boxes, results, tests, failure logs, and independent receipts are in [versioned evidence](../data/nominal_gas_visibility_v327_20261111/). No source CAD, prior fields or historical PDFs were modified. Geometry, P1 and solver code are versioned separately; no new mesh or 430-domain PDE was run.
