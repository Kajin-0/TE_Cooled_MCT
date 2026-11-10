# Source-based 0.60 mm pellet geometry feasibility

**Status: coordinate and source-path controls PASS; assembled CAD, contact, collision, thermal-map and gas gates NOT RUN; coupled comparison STOP.** This is a geometric feasibility investigation, not a new detector-temperature solution. The source 824-body R1 assembly, 0.50 mm 29/11/4 TEC and all historical failure gates remain intact. See `data/tec_height_geometry_20261110/registration.json` for pre-registered hashes, constraints and stop conditions.

## Construction and source dependencies

The native generator `tecooledmct/tec_assembly_v3.py` imports 88 legs, four ceramic boxes and 176 SnSb solder boxes from `data/tec_candidate_29114_v2_20261102/source_final/design.json`. Four source ceramic plates are 0.50 mm thick; their lower z datums above the header are 1.58425, 2.68425, 3.78425 and 4.88425 mm. Leg hot/cold surfaces are separated by 0.50 mm and each meets a nominal 0.035 mm solder layer, a 0.015 mm metallization stack and a ceramic face. Each nominal leg-to-solder interface is 0.16 mm². The five-layer Ti/TiW/Cu/Ni/Au films, 89 series net identities, seven foil feet, nets 58/80/88, hot-side lead landings, detector attach/carrier and wire endpoints are separately generated. The complete source has 824 bodies and 176 registered leg/solder plus 176 solder/metallization contacts; those contact statements are source-coordinate assertions, not the result of a new candidate STEP intersection.

The V3.11 `OriginalPlates` model assembles each source plate from its original 3D tetrahedra and original tagged surface triangles, with 95 native pad/load responses. Its gas calculation is a separate 3 mm effective-gap four-branch proxy. Formed copper is an independently specified reduced multiport, not a solved source-wide 3D Cu field. A plate may in principle be translated rigidly without changing its internal local conduction matrix; that observation does not establish that translated mesh face ownership, metal foot contacts, paths to the header, radiation visibility, or the full package mapping are correct.

## Registered coordinate hypotheses

Only a common 0.10 mm height increase is proposed. The bottom mounting datum stays fixed; plate j is translated upward by `j × 0.10 mm` and each leg in stage j lengthens between its unchanged lower and translated upper solder. Width, material identity, leg position and series ordering are unchanged. Exact source box coordinate arithmetic checks all 88 proposed axial alignments and their 176 nominal solder faces; the separate machine-readable outputs enumerate every leg, P/N identity and nodes.

| Quantity | Source 0.50 mm | Coordinate proposal 0.60 mm |
|---|---:|---:|
| Ceramic lower z (mm, C0/C1/C2/C3) | 1.58425 / 2.68425 / 3.78425 / 4.88425 | 1.58425 / 2.78425 / 3.98425 / 5.18425 |
| Nominal TEC stack height (mm) | 3.80 | 4.10 |
| Interleg pitch / edge gap (mm) | 0.58 / 0.18 | 0.58 / 0.18 |
| Die top / axial window separation (mm) | 5.77625 / 3.87375 | 6.07625 / 3.57375 |
| Sum P/N volume (mm³) | 7.040 | 8.448 |
| Sum P/N lateral area (mm²) | 70.40 | 84.48 |

The die-window figure is only an axial dimension, **not** a whole-assembly collision or optical-clearance test. The candidate 4.10 mm stack is outside the cited 3.80 ± 0.15 mm product envelope, so retaining that particular nominal source family tolerance would require a different package-stack design; no exact commercial-assembly claim follows. The +1.408 mm³ and +14.08 mm² are P/N-solid changes, not a computed native gas-volume change or gas conductance.

| Formed return | Source neutral path (mm) | Source-fillet proposal (mm) | Required |
|---|---:|---:|---|
| net58 | 1.960619 | 2.060619 | Re-form and revalidate both feet and collisions |
| net80 | 1.970619 | 2.070619 | Re-form and revalidate both feet and collisions |
| net88 | 3.706239 | 3.906239 | Re-form all three feet; new Cu multiport required |

An unchanged detector-bond apex is demonstrably invalid: moving the die end up 0.30 mm leaves 0.0651 mm rise to the original apex, less than the source 0.15 mm bend radius. Moving the apex from 6.15 to 6.45 mm permits the source analytic fillet construction, with the pin ends fixed, but that proposed wire has **not** passed 3D interference, assembly and contact tests. The first path draft used a wrong absolute net80 stage datum; it is preserved as `formed_paths_initial_incorrect_stage_datum.json` and is rejected, not used as the final proposal. The corrected datum is covered by a negative/source-position control.

## Stop and exact next action

The proposed coordinates have **not** been written as a new 824-body STEP, independently SI-imported, union/intersection audited, or checked for unlike-net shorts, support, actual pin/wire/cap clearance, closed gas voids, or contact-face ownership. The plate mesh and the multiport, gas and radiation mappings have not been regenerated and audited for the changed geometry. Therefore the registered prerequisite for coupled cases is not satisfied: **zero new full-system solves, zero new temperature predictions, zero new global energy balances**. The V3.17 +8.532 mW frozen-pad number is not a predicted temperature improvement. The old 3D net88 current FAIL/STOP remains untouched.

A minimum next implementation is a new versioned generator that applies the registered layer translations to all solids and contacts, rebuilds the three formed foil paths and both detector bonds, then exports an independent SI-checked STEP. Run exact 176-face contacts and graph/short/interference checks, cap and wire clearance, and regenerate plate-tag mappings, Cu multiport and consistent exposed-gas proxy. Only after those gates pass, attempt a single bounded matched-power comparison under 300 K, Kr100 Pa and 2 mW, with the original separate P/N source law (40–300 K measured research specimens; quarter-tangent continuation above 300 K assumed). The 0.595668 W comparison must report actual I,V,P, die and ceramic temperatures, and independently audited stage/Cu/lead/die/gas/sink balances.

## Reproduction and evidence

The calculation uses `scripts/tec_height_geometry_audit_20261110.py`, `scripts/tec_height_path_controls_20261110.py`, `scripts/tec_height_series_audit_20261110.py`, the source and registration hashes, and `tests/test_tec_height_geometry_20261110.py`. The independently checked source registry retains the ordered 89-node series path and 352 declared interfaces; this is not an intersection test for a new CAD. The prior attempt file is forensic evidence and must not be interpreted as the corrected proposal. Tests include a deliberately shifted solder face, absolute net80 datum, bond bend failure, area and volume controls; 36 focused/source-regression tests passed in the qualified recovered container. No mesh, PDE, full-system or detector-physics calculation was performed.

The archive verifier's initial invocation ended with SIGTERM (exit 143) without a result; the separately logged, bounded retry completed successfully. Prior numerical archives and the 44-page master hash remained unchanged. To repeat the focused checks without modifying the saved evidence:

```sh
docker run --rm --network none --cpus=2 --memory=4g \
  -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory \
  -e GIT_CONFIG_VALUE_0=/workspace -v "$PWD:/workspace" -w /workspace \
  tecooledmct-fem:26.2.1-recovered-20261105 python -m pytest -q \
  tests/test_tec_height_geometry_20261110.py tests/test_synthetic_v3_assembly.py \
  tests/test_tec_pellet_screen_20261110.py
/home/User/venvs/plotting/bin/python -B fem/archive_bath_spatial_device.py --verify
/home/User/venvs/plotting/bin/python scripts/tec_height_report_build_20261110.py --out <new-empty-staging-directory>
```

The geometry and path writers refuse to overwrite the archived output; reproduce those in an isolated copy with the sealed inputs. The runtime image is the previously qualified recovered image, not the missing original image digest.
