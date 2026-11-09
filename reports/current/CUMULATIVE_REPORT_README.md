# Cumulative TEC/TO engineering assessment — 9 November 2026

**Primary reader-facing publication:** `TEC_HgCdTe_Cumulative_TEC_TO_20261109_Plot_QA_Rev3.pdf` (34 pages; plot-label legibility revision). The previous 34-page layout Rev2 remains preserved.

This edition is the **original complete 30-page assessment plus additive sections**, not a shortened new standalone study. Original `report.tex`, `TEC_HgCdTe_Current_Architecture_20261108.pdf`, original figures, and all archived simulation evidence were preserved. The separate `reports/tec_to_assessment_20261109/` nine-page assessment is supplemental, not the master report.

## Repeatable build (no new simulation)

From `reports/current`:

```sh
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Plot_QA_Rev3 cumulative_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Plot_QA_Rev3 cumulative_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Plot_QA_Rev3 cumulative_report.tex
```

- `cumulative_report.tex`: unabridged original report plus insertion and updated front-summary paragraph; formatting-only layout rules applied for Rev2.
- `expanded_tec_to_studies_20261109.tex`: five new technical sections and five sourced figures.
- `cumulative_20261109_manifest.json`: original and current source SHA-256 values; eight independently verified V3.11 case result and audit hashes; figure hashes; original Rev2 and current Rev3 PDF digests.

Science caveats: source synthetic 29/11/4 cooler; four actual original ceramic spatial FEM fields and 88 nonlinear axial legs, but no integrated full 430-domain volume or native cavity-gas PDE; 3 mm effective gas gap; unknown paired commercial P/N material and production interfaces. Material-factor screens are not statistical tolerances. Source-result conservation is not experimental validation.

Publication checks: original 30-page PDF SHA preserved; previous 37-page cumulative PDF remains present and unchanged; eight V3.11 accepted audits cross-checked against source result hashes and energy thresholds below 2e-9 W; 34-page Rev2 PDF confirmed; section/appendix coverage checked; no overfull-box error or page overflow in MuPDF text/image bounding-box scan.

## Plot-label legibility revision (Rev3)

Five source-data charts were re-typeset in new `*_legible` PDF/PNG files and referenced only in `cumulative_report.tex` and its additive sections. The original figure assets remain unchanged. Changes: moved the physical P/N legend outside the plotted leg centers, moved explanatory text below the two source-pad/contact plots, removed colliding temperature and power annotations (exact values remain in report tables), and clarified the discrete krypton pressure chart annotations. Also corrected two malformed LaTeX multiplication symbols. The figure source is `plot_legibility_revision.py` and `plot_legibility_manifest.json` records archived input and output SHA-256 values. No FEM or device solves were executed.
