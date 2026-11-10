# Source-derived TEC ceramic gas-face partition

**Result: source-rectangle partition PASS; complete gas-port mapping and physical transfer closure STOP; coupled comparison NOT RUN.** Both 824-solid synthetic assemblies include an ideal cap shell, roof and window. The original derived R3 geometry contains a connected CSG cavity (1,231.630061 mm³, with 0.077162 mm³ polymer jacket volume excluded); this is a geometry result for the nominal source, not an independently qualified gas heat-transfer field. The differently elevated 0.60 mm candidate has a separately checked STEP, but no corresponding qualified CSG gas volume or registered full gas-facing metal/ceramic port mapping. Cap/header and window seal fabrication and hermeticity are not qualified.

## Source partition and reproducibility

The single registered source pass reads the exact 824-body physical source JSONs and original R3 face ownership, checks their frozen SHA-256 identities, and divides **every one of the four rectangular ceramic bodies' six faces** into mutually exclusive direct solid contact, bare projected adjacent-plate footprint, and remaining bare source face. Both physical designs have 24 faces, identical areas under rigid translation, and source substrate gaps of 0.600 and 0.700 mm. The stage gap difference is exactly 0.100 mm. Partition categories refer to exposed *ceramic* at the face, not the top of its metal coatings. They do not establish the gas access or connection through a projected volume. Source rectangles overlapping within the same film are unioned once; overlapping unlike direct contacts are rejected.

For each original face, the saved record contains its plane, direct-contact body IDs/names and source areas and the complete matching original R3-derived CAD face tags, owners, classes and areas. Across 24 faces the maximum absolute difference between physical-source rectangular direct-contact area and derived-CAD solid-face area is 1.25e-14 mm². The analysis geometry coalesces thin metal layers, so the derived face labels need not be the original physical Ti/TiW layer identity. Candidate correspondences are **source-translated original tags**, not an independent candidate gas-BRep face-tag audit. Curved non-box solid bounding boxes are included as *candidates*, not proven contacts; cap annulus bounding boxes alone intersect all ceramic AABBs even where their real annular surfaces do not. No line-of-sight, free-molecular path or metal-side heat transfer is inferred from these boxes.

| Ceramic face | Direct contact | Bare facing projection | Remaining bare | Total |
|---|---:|---:|---:|---:|
| C0 top | 16.891750 | 11.218000 | 12.850250 | 40.960000 |
| C1 bottom | 15.660000 | 11.380000 | 0 | 27.040000 |
| C1 top | 6.855500 | 8.072000 | 12.112500 | 27.040000 |
| C2 bottom | 5.940000 | 8.500000 | 0 | 14.440000 |
| C2 top | 3.073500 | 3.215000 | 8.151500 | 14.440000 |
| C3 bottom | 2.160000 | 3.600000 | 0 | 5.760000 |
| C3 top | 4.410000 | 0 | 1.350000 | 5.760000 |

All areas are mm², for both geometries. The four bare side-face sums for C0–C3 are 12.8, 10.4, 7.6, and 4.8 mm² respectively in the source rectangle/R3 face comparison. Their assignment to a physical gas path is **not** solved. Bare projected areas on opposite faces differ because patterned metallization covers them differently; they cannot simply be paired by choosing either number as a common transfer area. The old V3.20 interstage projected areas (17.76, 10.92, 4.48 mm²) include surfaces other than bare lower ceramics. Comparing those with the bare areas does not establish a heat-flow error: gas can touch both metal and ceramic.

The R3 registry contains 1,840 gas–solid faces, including 523 gas-facing patterned-net faces. Treating only the exposed ceramic rectangle remnants as the complete cavity would silently omit metal surfaces and their thermal destinations. In particular, existing V3.20 source-face FEM loads distribute gas/radiation by a pad-area proxy and do not independently assign gas contact to all those metal faces. Projecting leg squares alone also does not remove formed foils, metallization, joints or intervening bodies along the full three-dimensional gap. Therefore no exact non-overlap of **paths** or energy-conserving per-node physical mapping is established, despite the disjoint ceramic face area ledger.

## Operator and gating

`tecooledmct/gas_partition_v322.py` implements a conservative **generic** link operator only for explicitly supplied equal-area face patches, ports and positive gaps. It rejects repeated or outside patches, self-links, unequal endpoint areas and invalid pressure, and checks zero-pressure/equal-temperature limits and signed reciprocal exchange. This is tested on analytic controls; **no inferred source-gas network is passed to the coupled package solver**. Its simple resistance law uses the existing Kr temperature-jump model; geometric partition does not validate that gas law at 100 Pa. Prior radiation remains a distinct mechanism and is not equated with gas ownership.

Run `PYTHONPATH=. python -m pytest -q tests/test_tec_gas_v322_partition.py tests/test_tec_height_coupling_v320.py tests/test_tec_height_v321_results.py` in the recovered Python 3.12 environment. The [registration and evidence](../data/tec_gas_partition_20261110/) retain source hashes, face tags, material/body counts, audit output and test results. Source scripts do not mutate or re-export either 824-solid design. No V3.22 coupled solve was run, and V3.20/V3.21 temperature comparisons and their numerical limitations remain unchanged.

**Next bounded action:** derive and independently verify a candidate-specific closed gas/solid face registry, including metallization, ceramic sides, foil, leads, die and cap/window/header boundaries. Map each gas-facing face once to an actual thermal port or explicitly unresolved reservoir and establish candidate connected-gas access; then preregister the geometry-specific conductance approximation and compare the two designs. Until then, metal-port uncertainty and the existing raw gas-flux and 3D electrical-gate failures remain separate unresolved issues.
