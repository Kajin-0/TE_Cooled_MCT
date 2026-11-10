# V3.13 reader-first scientific report organization audit

**9 November 2026 | Scientific material retained, section order substantially improved.**

## Diagnosis of previous report organization

The previous 36-page cumulative assessment had adequate technical content and original numerical provenance, but retained software-milestone ordering rather than device-engineering argument order. It began with terminal wires and operating-current experiments before defining the complete TEC construction, governing thermoelectric physics or the actual ceramic field. Original V3.4 evidence, current V3.6/V3.11 experiments, V3.12 contact evidence, and V3.3 historical results were interspersed. This increased cognitive load and obscured which exact physical model produced each result. Some forced page breaks also stranded source-CAD figures on mostly unused pages.

## Implemented reader-first organization

1. Original source geometry and actual nine-pin cooler/TO package, copper and ceramic arrangement.
2. Thermoelectric transport, original ceramic FEM heat spreading, electrical routing, solder and package parasitic physics.
3. Source-matched copper/baseline comparison, then TEC operating current and imposed detector heat sweeps.
4. Later source-accepted material, mounting, gas-pressure and power/cooling sensitivity studies.
5. Corrected source-foot solder evidence, three-port copper audit and explicit 3D Gate B STOP.
6. Geometric limits, historical generations, scientific verification, materials/provenance and literature references.
7. Complete original P/N property, original leg-center, source-face heat, and technical verification appendices.

The source is `reports/current/reader_first_report.tex`; its deterministic editorial build script, `build_reader_first.py`, uses the preceding cumulative source as an immutable **input**, retaining **all 18 prior main-body sections**, all original appendix material, all original numerical tables and figures, and both existing additive study sections. One original forced page break is removed for pagination and a short reader-navigation paragraph is added. The V3.13 source-gate study is a new scientifically qualified additional section. The upstream original 30-page, previous 34-page and 36-page editions are preserved. The reader-first version is therefore a restructuring plus new evidence, **not** a replacement summary.

## Scientific corrections discovered by the audit

**Solder-material attribution:** The original V3.12 foil-foot contact sensitivity erroneously used Sn95Sb5, which belongs to P/N leg joints. Native formed foil feet `tab_joint0`...`tab_joint6` are `SnBi57_43`, i.e. Bi57Sn43. The V3.12 current source, report section and numerical fixed-face screen are corrected with an explicit erratum; 19 W/mK for nearby Bi58Sn42 at 85°C is used as an *unverified alloy-family conductivity proxy*, not a measured low-temperature property of Bi57Sn43. Archive accepted full-device solver temperatures remain unchanged.

**Three-foot electrical-current ownership:** The original 3D coupon registers net88 `tab_joint5` as a zero-current electrical dead end but a real thermal landing, whereas the reduced V3.4 copper coefficient construction includes its finite electrical contact resistance as a series current passage. A prospective error of **26.667 µW at 0.400 A** is quantified with source CAD and previous 3D evidence. This does not constitute a corrected coupled solver or updated detector temperature. The original 3D electrical Gate B (P2 worst raw cut **8.0993%** against **0.1%**, 11/16 cuts failing) remains FAIL/STOP; no 3D thermal or Joule release is claimed.

## Editorial release standard

- Original and interim scientific results should be chronologically distinguished and never silently replaced.
- Each plot must have readable axes, no hidden annotations, conditional source and boundary identification and a caption distinguishing full FEM from fixed-field screens.
- Scientific physical assumptions should precede the first result depending on them; conclusions should explicitly identify what is verified versus inferred.
- The automated checks validate section presence/order and page-bounds but **do not prove the physical model or guarantee every small interior annotation is collision-free**.
- For later new experiments, add substantive studies to the reader-first master, update reproducibility manifests and perform actual rendered-page inspection. Keep historical PDFs and source archives intact.
