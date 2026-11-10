# Cumulative TEC/TO engineering assessment — 9 November 2026

**Primary reader-facing publication:** `TEC_HgCdTe_Cumulative_TEC_TO_20261109_Contact_Engineering_Rev4.pdf` (36 pages; V3.12 physical copper/joint and mounting evidence). The preceding 34-page plot-legibility Rev3 and other editions remain preserved.

This edition is the **original complete 30-page assessment plus additive sections**, not a shortened new standalone study. Original `report.tex`, `TEC_HgCdTe_Current_Architecture_20261108.pdf`, original figures, and all archived simulation evidence were preserved. The separate `reports/tec_to_assessment_20261109/` nine-page assessment is supplemental, not the master report.

## Repeatable build (no new simulation)

From `reports/current`:

```sh
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Contact_Engineering_Rev4 cumulative_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Contact_Engineering_Rev4 cumulative_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Contact_Engineering_Rev4 cumulative_report.tex
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
