# Constructed 0.60 mm custom TEC/TO assembly

The previously proposed height change is now a **separately constructed, source-derived 824-body candidate**, not merely a transport or coordinate overlay. Its [design.json](../data/tec_height_060_cad_20261110/source_candidate/design.json) and [SI-checked STEP](../data/tec_height_060_cad_20261110/cad_attempt01/synthetic_v3_mm.step) are distinct from the frozen 0.50 mm source assembly. The 4.10 mm custom stack is a disclosed difference from the separate manufacturer's 3.80 ± 0.15 mm nominal product; it is not by itself a failure of the TO design or evidence of OEM internals.

## Construction

`tecooledmct/tec_height_060_candidate.py` reads the immutable 824-body source design and changes actual solid parameters, not just bounding boxes. It lengthens all 88 P/N boxes to 0.60 mm; shifts the four 0.50 mm ceramic bodies by 0/0.10/0.20/0.30 mm; moves 176 corresponding solder bodies, face metallization, seven foil feet and joints; reforms Cu tabs 58/80/88 from their actual lines and arcs; translates cold finish, die/carrier/attach and detector pads; and reforms both detector bond wires to a 6.45 mm apex while retaining their pin endpoints. It recomputes body bounds, volumes, source-plane metadata and contact coordinates. Body/material IDs and leg series identities are preserved. **Plane numbers embedded in body names remain stable source identifiers, not the new coordinates**; the numeric `plane` and solid coordinates are authoritative.

The source topology contains 29/11/4 couples on 0.58 mm pitch, 0.40 mm square P/N legs, 89 conductor nets, and a pin1→net0→88 alternating P/N legs→net88→pin9 circuit. Detector pins 7/8 retain their separate wires; pins 5/6 remain unpopulated. Source pin diameter is 0.76 mm; TEC lead diameter is 0.20 mm, detector bond diameter 0.018 mm. The source model's chosen materials and layer thicknesses are retained. The hot-side mounting datum, pin shafts, shell and window remain fixed.

## Checked geometry and limits

| Check | Result and scope |
|---|---|
| Source-derived construction | 824 body identities; 556 modified body geometries; candidate SHA-256 `cf580248c44f4f06ce82f046aa797ee3c2826d52f4225698eb2af1c88d95eec7` |
| Analytic source graph | 89 nets, 98 metal components; pin1/9 series endpoints and detector pin7/8 connections; no unlike-net short detected by the original source-face graph |
| Independent rectangular contacts | 176 P/N–solder and 176 solder–Au face intersections, each nominally 0.160 mm²; net58/net80/net88 retain 2/2/3 foil feet |
| Source solid boxes | No positive box–box overlap under original source audit's tolerance |
| STEP writer | 824 solids, 151.19 s, <=4 CPUs/8 GiB; [STEP SHA-256](../data/tec_height_060_cad_20261110/cad_attempt01/writer.json) `7f24bbb192cc7531a71fb35c75763dbbb0c38cac7722bbc6f8ff6b05616760a8` |
| Independent SI reader | 824 identities; 1 mm cube = 1e-9 m³; max relative volume error 1.289e-11, max bbox error 1.000e-7 m |
| Independent imported BRep | All 923 source contact witness points found on both corresponding imported boundaries; 58 candidate curved/interacting body Boolean intersections all zero volume; 1,250 further pairs have conservative separation certificates |
| Conservative nominal envelopes | Shell clearance >=0.78544 mm; roof clearance >=3.186 mm; minimum unrelated pin/wire clearance >=1.78317 mm across 48 pairs; minimum same-stage P/N gap 0.180 mm |

Imported contact witness membership verifies the declared interfaces at points; it is **not** an independent measurement of all imported contact areas. The 0.160 mm² contacts above come from independent rectangle/union calculations on source solids. The 58 Boolean results and 1,250 separation certificates cover the registered curved/header/wedge candidate pairs under the inherited source audit. No fitted temperature or detector outcome is implied. Bounds are nominal source-geometry checks, not demonstrated manufacturing capability, process tolerance or current rating. In particular, the inherited `contact_audit.json` embeds a **hard-coded baseline 3.80 mm tolerance table**: that portion is not a tolerance audit of this 4.10 mm candidate and must not be interpreted as one.

The original source 3D electrical-contact numerical gate remains **FAIL/STOP**. The imported geometry result does not qualify that physics, nor does it complete the altered ceramic 3D face mapping, Cu electrical/thermal multiport, gas/radiation and package heat balance. **No new thermal, electrical or coupled FEM solve was run**, and no matched-power detector-temperature comparison is claimed. The next engineering step is to construct source-consistent ceramic-face ownership/translations and Cu/gas mapping for this saved geometry, audit the translated domains and then run the preregistered bounded 0.595668 W comparison with independent global energy checks.

## Reproduction and verification

Registration and original/candidate identities, writer, independent SI reader, all boundary witnesses/Boolean results, clearance and tests are retained in [the evidence directory](../data/tec_height_060_cad_20261110/). The source construction is intentionally output-only and refuses to overwrite its existing candidate directory. The original-source CAD export and fresh reader use the previously qualified **recovered** runtime image, not a bit-identical original image; their maximum allowed wall time was 180 s per role, 4 CPU and 8 GiB.

The focused test suite passed 44 tests. The old `verify_synthetic_v3_checkpoint.py` did **not** pass: it compares `docs/MASTER_REPORT_REPRODUCIBILITY.md` with an older historical baseline and that file was changed by commit `ea27334` on 2026-11-08, before this task. Its recorded failure is retained; the same file and all other non-documentation tracked inputs match this task's starting HEAD. This is an existing historical verifier incompatibility, not a passing original check. Independent current-source SHA checks and archive verification are reported separately in the evidence directory.
