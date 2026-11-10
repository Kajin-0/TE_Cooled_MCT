# Cumulative TEC/TO engineering assessment — 9 November 2026

**Primary reader-facing publication:** `TEC_TO_Reader_First_Assessment_20261110_V315.pdf` (40 pages; complete reader-first cumulative report and a new saved-field contact-perimeter attribution study). The earlier 39-page V3.14 edition and all previous reports are preserved. The V3.12 foil-foot bulk-property screen was corrected in the new edition after recognizing Bi57Sn43 joint identity; previous published PDF is unchanged but superseded on that specific contact study.

This edition is the **original complete 30-page assessment plus additive sections**, not a shortened new standalone study. Original `report.tex`, `TEC_HgCdTe_Current_Architecture_20261108.pdf`, original figures, and all archived simulation evidence were preserved. The separate `reports/tec_to_assessment_20261109/` nine-page assessment is supplemental, not the master report.

## Repeatable build (no new simulation)

From `reports/current`:

```sh
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_TO_Reader_First_Assessment_20261110_V315 reader_first_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_TO_Reader_First_Assessment_20261110_V315 reader_first_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_TO_Reader_First_Assessment_20261110_V315 reader_first_report.tex
```

- `cumulative_report.tex`: unabridged original report plus insertion and updated front-summary paragraph; formatting-only layout rules applied for Rev2.
- `expanded_tec_to_studies_20261109.tex`: five new technical sections and five sourced figures.
- `cumulative_20261109_manifest.json`: original and current source SHA-256 values; eight independently verified V3.11 case result and audit hashes; figure hashes; original Rev2 and current Rev3 PDF digests.

Science caveats: source synthetic 29/11/4 cooler; four actual original ceramic spatial FEM fields and 88 nonlinear axial legs, but no integrated full 430-domain volume or native cavity-gas PDE; 3 mm effective gas gap; unknown paired commercial P/N material and production interfaces. Material-factor screens are not statistical tolerances. Source-result conservation is not experimental validation.

Publication checks: original 30-page PDF SHA preserved; previous 37-page cumulative PDF remains present and unchanged; eight V3.11 accepted audits cross-checked against source result hashes and energy thresholds below 2e-9 W; 34-page Rev2 PDF confirmed; section/appendix coverage checked; no overfull-box error or page overflow in MuPDF text/image bounding-box scan.

## Plot-label legibility revision (Rev3)

Five source-data charts were re-typeset in new `*_legible` PDF/PNG files and referenced only in `cumulative_report.tex` and its additive sections. The original figure assets remain unchanged. Changes: moved the physical P/N legend outside the plotted leg centers, moved explanatory text below the two source-pad/contact plots, removed colliding temperature and power annotations (exact values remain in report tables), and clarified the discrete krypton pressure chart annotations. Also corrected two malformed LaTeX multiplication symbols. The figure source is `plot_legibility_revision.py` and `plot_legibility_manifest.json` records archived input and output SHA-256 values. No FEM or device solves were executed.

## V3.12 new engineering evidence (Rev4)

A new two-page source-audited scientific section, `v312_contact_mounting_section.tex`, was inserted additively after the V3.11 gas study. It retains the complete original and previous cumulative source sections and appends two figures with visible axis and legend text. Associated full study: `docs/V3_12_COPPER_JOINT_MOUNTING_EVIDENCE_20261109.md`, source script: `scripts/v3_12_contact_mounting_assessment.py`, registered result: `data/v3_12_contact_mounting_assessment_20261109/assessment.json`. The new calculation reuses the accepted V3.5/3.8/3.11 operating points, reconstructs original Cu-foil heat transfer from frozen temperatures and evaluates six static, bulk-solder contact hypotheses (not six new full-device solves). Property sources are recorded and experimental validation is not asserted. Reproducibility and figure digests appear in the V3.12 record and the cumulative manifest.

## Current reader-first cumulative edition (V3.13)

`reader_first_report.tex` is deterministically generated from all 18 previous major scientific sections, the unabridged legacy appendices and all additive V3.8-V3.12 sections, followed by V3.13 local foil-port evidence. Run `python3 build_reader_first.py` before LaTeX. `reader_first_organization_manifest.json` lists section preservation hashes and order. The new reader sequence starts with construction, governing physics and thermal package, then operating points, design sensitivities, historical models and appendices. Full editorial rationale is in `docs/V3_13_REPORT_ORGANIZATION_REVIEW_20261109.md`.

Important erratum: the V3.12 bulk bondline screen must use Bi57Sn43 formed-foil joining feet, not Sn95Sb5 P/N leg solder. The corrected screen uses 19 W/(m K) for near-eutectic Bi58Sn42 at 85 C as an explicitly unverified family analog. The other correction is the prospective electrical dead-end middle foot on net88. The older V3.13 archived electrical Gate B still fails raw-gradient criteria; NO new spatial FEM result is asserted. See `docs/V3_13_NATIVE_FOIL_PORT_AND_3D_GATE_20261109.md`.

## V3.14 registered contact-perimeter source-CAD FEM experiment

`v314_p2_resolution_section.tex` extends the reader-first report with one full 12-region source-BREP P2 electrical refinement from h=45um to 35um (28,691 to 47,277 tetrahedra); the original 0.1% raw-gradient electrical gate still **FAIL/STOP** with new 7.019% worst cut and 11/16 failures. Independent no-solve review of 2,178 physical triangles and both terminal cuts agrees to 4.511e-13 relative. No thermal Gate C, Joule Gate D or complete TEC rerun followed. Exact source, figure, field, mesh and result hashes are in `cumulative_20261109_manifest.json` and `data/v3_14_native_net88_perimeter_resolution_20261109/`. Source physics, original archival reports, the prior V3.13 and historical failed current gates are unchanged.

## V3.15 source-native saved-field contact perimeter audit

The V3.15 reader-first section is additive, not a shortened standalone replacement. It compares the original and V3.14 native 3D P2 fields at lead9 metal-to-solder interfaces by reconstructing the raw one-sided face current and the distinct finite electrical contact-law current. The contact rim accounts for roughly 72–79% of solder-side gross mismatch in only ~20% of contact area. A *frozen-field counterfactual* removing its signed bias still fails the original 0.1% limit. This is a read-only no-PDE negative control. Original physical 3D electrical Gate B remains FAIL/STOP; thermal C and Joule D remain NOT RUN. Full documentation: `docs/V3_15_LEAD9_CONTACT_PERIMETER_FIELD_DIAGNOSIS_20261110.md`, receipts and plots in `data/v3_15_lead9_perimeter_20261110/`, release hashes in `cumulative_20261109_manifest.json`.
