# Original cavity: source-connected copper thermal reconstruction

**PASS:** conditional local 1D formed-copper reconstruction and an independently checked distributed-bath mathematical operator. **STOP:** no supplemental physical gas path or new coupled package solve. The original 0.40 × 0.40 × 0.50 mm assembly and the V3.25 P1 operator, fields and 52-page report remain unchanged. No native 3D metal electrical or full-cavity gas qualification is asserted.

## Source-to-temperature mapping

The source has formed foil conductors 58, 80 and 88, with actual line/arc centerlines, 0.30 mm width and 0.030 mm thickness. The original reduced Cu operator resolves 58 and 80 between two foil contact nodes and 88 between **three** nodes. The middle node of net 88 carries thermal exchange but has zero electrical contact resistance in the series circuit. The saved V3.25 case has I = 0.399960875 A. Each endpoint node is coupled to its source ceramic joint through the existing **assumed**, not measured, contact area resistance 1e−6 m² K/W.

We project each original gas-face centroid onto the source line/arc centerline, identify its source-contact-centered segment and retain that segment's endpoint node IDs and weights. The 0.15 mm free ends outside the joint centers are not silently clamped to a node. Some broad side faces have centroids outside the local strip because a centroid of an extended bent surface need not lie on that surface; such faces are unresolved. The 0.025 mm projection acceptance includes the analytic centroid offset of a 90-degree annular sector for source center radius 0.075 mm and 0.030 mm thickness (maximum approximately 0.021 mm); it rejects the broad side centroids (at least 0.0379 mm from the centerline). This test locates a **centroid sample**, not a temperature distribution or area-integral over the face. An independent 1001-point-per-part source-centerline readback checks all 39 mapped samples; the maximum arclength difference is 0.000250 mm, and an independent temperature reconstruction agrees to recorded precision.

For a segment with conductance G, electrical resistance R, current I, fractional distance u and endpoint temperatures T0,T1, the explicitly conditional reconstruction is

`T(u) = (1−u)T0 + u T1 + I²R u(1−u)/(2G)`.

It assumes constant kA, uniform Joule generation and **no gas heat on that segment**, matching the saved source multiport's equal Joule allocation to adjacent nodes. The exact local source heat balance gives `q0+q1+I²R=0`, with q positive from node into segment. T lies between the lower endpoint and the upper endpoint plus `I²R/(8G)`. Unknown contact drops, lateral spreading, temperature-dependent properties within the segment, real interfacial and gas loads are not constrained by this calculation. These are thermal-model conditional bounds, not measured surface-temperature intervals.

| Source net | Endpoint foil node temperatures, K | Centerline faces / area mm² | Mapped centroid temperature range, K | Maximum midpoint Joule rise, K |
|---|---|---:|---:|---:|
| 58 | 299.0784 → 272.4343 | 10 / 1.02637 | 273.8441–299.0784 | 0.02960 |
| 80 | 268.0796 → 248.3403 | 10 / 1.03237 | 249.4388–268.0796 | 0.02665 |
| 88 | 298.3799 → 271.7186 → 248.5493 | 19 / 2.01374 | 249.7829–298.3799 | 0.02957 |

The two segments of net 88 individually carry approximately 55.38 mW and 45.76 mW from their warmer nodes into the foil under the saved no-surface-gas model; Joule heating contributes separately. These are **existing-model heat paths**, not native 3D copper fields or newly solved gas leakage.

The [face graph](../data/nominal_cavity_metal_v326_20261111/face_temperature_graph.json) has 1,840 unique source faces / 903.21505 mm². Status counts and areas are mutually exclusive: 39 faces / 4.07249 mm² have the above **conditional** distributed-Cu centroid mapping; 1,667 faces / 885.99010 mm² retain prior approximate node, leg, contact or reservoir proxies; 134 faces / 13.15247 mm² remain unresolved. The latter includes 18 of the 57 original formed-tab faces. The 523 patterned-metal faces remain nearest-ceramic proxies, not validated isothermal nets. The previous eight lead-joint endpoint assignments remain proxies with unmeasured joint drops. No whole-cavity gas boundary condition is physically qualified. The previous P1 gas patches cover parts of six source faces totaling 29.81004 mm² on both sides; those areas overlap the temperature-status categories and must not be added to their totals.

## Film and hypothetical distributed-gas operator

For the source 15 µm Cu film, an explicitly selected illustrative `k = 200–400 W/(m K)` and normal heat flux of 1,000 W/m² give a bulk through-film drop `q''t/k = 0.0000375–0.000075 K`. This is an algebraic engineering sensitivity, **not** a measured flux, temperature field, source material uncertainty distribution, or bound on the metal/ceramic interface: contact resistance and in-plane spreading are excluded. The existing assumed interstage contact resistance alone would give 0.001 K at the same illustrative flux.

A reusable exact constant-property **1D conductor with a uniformly distributed thermal bath** is implemented in `segment_with_uniform_bath`. It retains actual endpoint reactions and `qgas = q0 + q1 + I²R`; its conductance is an explicit caller input, **not a calculated native-cavity coefficient**. Vacuum/zero-coupling, equal-temperature and Joule controls are tested. A separate centered-difference solve at 41, 81 and 161 nodes approaches the analytic profile by approximately 4× per refinement; at 161 nodes its maximum temperature error is 1.14e−8 K and the independently integrated gas/endpoint energy residual is 9.48e−10 W. The numerical bath is an analytic benchmark and is not a device gas path.

## Gas geometry gate and next action

The face registry supplies source identities, centroids, areas, bounding boxes and boundary-curve identities; those alone do **not** prove opposing trimmed face overlap, unobstructed intervening gas, mutual ownership, or disjointness with the 752 existing ceramic columns. In particular, broad foil-face centroids cannot stand in for actual face patches. Therefore zero supplemental metal–gas paths and zero new package solves were run. No new detector temperature is claimed. The exact next implementation is an original-CAD trimmed-face intersection and segment-obstruction check that returns disjoint, area-conservative foil/other-surface patches and contact-centered thermal weights, followed by a source-compatible gas coefficient model. Only then can the distributed-bath operator be assigned a physically defensible local conductance. The existing transitional-gas and native electrical flux gates remain FAIL/STOP.

## Reproduction and checks

The preregistered source SHA identities and scope are in [registration.json](../data/nominal_cavity_metal_v326_20261111/registration.json); the output graph, numerical controls and logs are in the same folder. Run `PYTHONPATH=. python scripts/tec_nominal_v326_metal_mapping.py`, `PYTHONPATH=. python scripts/tec_nominal_v326_quantify.py` and `PYTHONPATH=. python scripts/tec_nominal_v326_independent.py` in a disposable checkout with the recorded frozen inputs and only the registration retained in a fresh V3.26 output directory; the scripts deliberately refuse to overwrite published results. Focused tests cover analytic path projection, source face ownership, P1 preservation, thermal end reactions, zero and invalid conditions, and the distributed-bath ODE. The 1D construction is not an enclosed 3D gas solve or manufacturing validation.
