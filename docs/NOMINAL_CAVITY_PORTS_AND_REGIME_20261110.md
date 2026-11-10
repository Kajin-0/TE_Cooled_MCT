# Original 0.50 mm TEC/TO reference: cavity ports and gas regime

**Scope and result.** The authoritative working article for this phase is the original synthetic 824-solid package with 29/11/4 couples and 0.40 × 0.40 × 0.50 mm P/N pellets. Source [reference and operator receipt](../data/nominal_cavity_ports_20261110/nominal_reference.json) records hashes, assumptions, operating point and outstanding gates. This is a source-informed engineering reference, not an identified manufacturer assembly, a manufactured article or an experimentally validated temperature. The archived 0.60 mm variant was not used in this study.

## Nominal operating point and independent energy reconstruction

The V3.20 **proxy configuration** uses 300 K reservoir, 100 Pa Kr and 2 mW imposed die heating: I = 0.400297737 A, V = 1.488062461 V, IV = 0.595668035 W, hot ceramic = 303.761291 K, upper ceramic = 219.297688 K, die mount = 219.368939 K and modeled sink rejection = 0.592285058 W. V3.11 at 0.400 A gives 218.900024 K under a different proxy configuration; the two are not identical physical gas models. V3.20 adds interstage gas links and corrects the net88 electrical bookkeeping. Neither is measured performance.

| Stage, hot to cold | Qhot W | Qcold W | Voltage V | Leg count |
|---|---:|---:|---:|---:|
| 1 | 0.717058 | 0.295305 | 1.053599 | 58 |
| 2 | 0.262929 | 0.138533 | 0.310758 | 22 |
| 3 | 0.048246 | 0.006099 | 0.105289 | 8 |

These leg quantities are not the entire stage heat budget: copper tabs, joints, leads and gas paths cross the ceramic boundaries. The independent stored-result readback verifies each stage's Qhot − Qcold − IV within 8.31e-13 W, 88 individual legs within 1.48e-13 W, and the full package budget within 1.05e-9 W. The latter includes electric input, die load and Au-wire heat, external gas/radiation, signed Cu-lead conduction, the lead electrical dissipation allocated to the header, and sink rejection; the die-inclusive term already contains die gas/radiation and must not be counted twice. It is not a measurement of the underlying gas flux. Full terms are in [the readback](../data/nominal_cavity_ports_20261110/nominal_budget_audit.json).

The working model uses 88 bounded nonlinear source-research P/N legs, four source 3D ceramic temperature fields, reduced Cu multiports and wires, a finite mount, effective radiation and overlapping-possible internal/external gas proxies. The P and N specimens are not a characterized matched commercial pair; the >300 K continuation is assumed. The original 3D metal electrical Gate B and native raw gas-flux gate remain **FAIL/STOP**. Four spatial ceramic fields and conservation do not qualify the full solid/gas 3D physics.

## Complete nominal archived gas-face inventory

The [machine-readable inventory](../data/nominal_cavity_ports_20261110/nominal_gas_face_ports.json) assigns each of the 1,840 archived nominal R3 gas–solid face IDs **once** to its actual analysis-solid owner, gas and solid volume IDs and orientation signs, area, centroid, bounding box, surface type and source-physical lineage. Each entry also records an informational semantic node or distributed element and explicitly reports whether a native gas boundary condition is implemented. Independent readback against the archival face registry reproduces **903.215049791 mm²**, 429 unique solid owners, all 1,840 tags and opposite signs, with zero area difference at stored precision. This is a readback of archival CSG metadata, not a second geometry calculation.

| Semantic source class | Faces | Area mm² | Thermal-port status |
|---|---:|---:|---|
| Four ceramics | 24 | 119.799250 | Spatial solid fields exist; native gas-face interpolation not implemented |
| P/N pellets | 352 | 70.400000 | Individual axial leg states; lateral gas exchange not implemented |
| Patterned conductor nets | 523 | 26.347150 | Net, plane and face location retained; not treated as isothermal |
| Formed copper tabs | 57 | 4.646735 | Reduced multisegment model exists; gas surface-to-segment mapping missing |
| Joints/fillets | 760 | 10.032744 | Geometry identified; gas-to-joint thermal mapping missing |
| Lead/insulation | 28 | 7.140895 | Distributed wire/insulation; exterior gas mapping missing |
| Header/pins/seals | 43 | 132.950703 | Reduced bath connection; gas-face temperature not established |
| Cap/roof/window | 3 | 521.944203 | Ideal solid geometry; wall temperatures and physical seal unqualified |
| Die/carrier/attach | 33 | 6.397578 | Semantic locations identified; exact gas-face mapping missing |
| Mount interface | 9 | 3.178800 | Reduced mounting path; distributed gas port missing |
| Unresolved lead-joint destinations | 8 | 0.376991 | Source solid name and location retained; thermal destination unresolved |

A semantic name is **not an installed thermal boundary**. All 1,840 gas-face boundary conditions remain unimplemented; in particular, mapping a copper face to a net ID does not assign one temperature to the net. Thin physical film layers were combined in the archived derived CSG; source lineage records that reduction. The nominal CSG has one connected ideal cavity of 1,231.630061 mm³ with polymer jacket volume excluded, but has not been qualified as a sealed manufactured package or as a converged native gas heat-transfer model. No source-face gas links were introduced and no new coupled solve was attempted, since an allocation and distributed-temperature model for the full gas boundary are absent.

## 100 Pa krypton: flow-regime decision

For a hard-sphere **screening hypothesis** use λ = kBT/(√2 πd²p). A published Kr kinetic-diameter scale is 0.36 nm ([Kwon et al., *Krypton-Xenon Separation Properties of SAPO-34*, p. 3](https://www.osti.gov/servlets/purl/1356958)); using it as an effective Kr–Kr hard-sphere collision diameter is an assumption, not a directly measured scattering cross-section. At 250 K and 100 Pa, this gives λ ≈ 0.0599 mm. For the source nominal 0.600 mm ceramic separation, or 0.570 mm after the declared two 15 µm films, Kn is ≈0.100 or 0.105 respectively. At the nominal 0.180 mm interpellet gap, Kn ≈0.333; over 200–300 K and a deliberately illustrative 0.34–0.40 nm diameter range, the 0.570 mm and 0.180 mm Kn ranges are 0.068–0.141 and 0.216–0.448. This bracket is a sensitivity illustration, not a confidence interval.

For the 0.570 mm scale at 250 K, Kn falls to 0.0105 at 1,000 Pa, 0.000351 at 30,000 Pa and 0.000104 at 101,325 Pa. At atmospheric pressure only, a formal ideal-Kr continuum screen with 250 K, 80 K temperature difference and existing Eucken/NIST-derived transport gives Ra ≈14 for 0.570 mm and ≈2,065 for 3 mm. These are order-of-magnitude, orientation- and boundary-dependent values; the ideal horizontal-layer onset criterion is not a universal package criterion. At 100 Pa, narrow gaps are in or near the transitional regime, so continuum Rayleigh numbers are not a basis for accepting standard no-slip CFD.

A nonintrusive PATH/environment/common-directory and visible Docker-image check found no OpenFOAM executable in this runtime; this does not rule out installation elsewhere. Even if OpenFOAM is available in another environment, stock continuum buoyant CFD without an appropriate rarefied treatment is not qualified for the nominal 100 Pa narrow gaps. No CFD was run. A future continuum CFD comparison is appropriate only after a physically mapped, closed gas domain, boundary-temperature model, pressure/orientation, Kn and expected heat impact justify it; a transitional treatment needs separate validation.

## Completion gate and reproduction

[Preregistration](../data/nominal_cavity_ports_20261110/registration.json), nominal registry, independent readback, regime calculations and saved energy diagnostics are versioned. `PYTHONPATH=. python -m pytest -q tests/test_tec_nominal_v323_ports.py` exercises unique IDs, areas, orientations, negative ownership controls, source hashes, original budget and Kn scaling; no FEM or CFD runs. The next implementable step is to map original gas faces to the **actual local temperature representation** of each ceramic, patterned conductor, leg, wire and enclosure, including the eight lead joints, then establish mutually exclusive path patches and a validated rarefied transfer model. Until those gates pass, no new native-gas coupled operating temperature is claimed.
