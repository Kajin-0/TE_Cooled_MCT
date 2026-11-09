# Cumulative TEC/TO engineering assessment — 9 November 2026

**Primary reader-facing publication:** `TEC_HgCdTe_Cumulative_TEC_TO_20261109_Layout_Rev2.pdf` (34 pages; formatting-only revision of the preserved 37-page cumulative assessment).

This edition is the **original complete 30-page assessment plus additive sections**, not a shortened new standalone study. Original `report.tex`, `TEC_HgCdTe_Current_Architecture_20261108.pdf`, original figures, and all archived simulation evidence were preserved. The separate `reports/tec_to_assessment_20261109/` nine-page assessment is supplemental, not the master report.

## Repeatable build (no new simulation)

From `reports/current`:

```sh
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Layout_Rev2 cumulative_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Layout_Rev2 cumulative_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=TEC_HgCdTe_Cumulative_TEC_TO_20261109_Layout_Rev2 cumulative_report.tex
```

- `cumulative_report.tex`: unabridged original report plus insertion and updated front-summary paragraph; formatting-only layout rules applied for Rev2.
- `expanded_tec_to_studies_20261109.tex`: five new technical sections and five sourced figures.
- `cumulative_20261109_manifest.json`: original and current source SHA-256 values; eight independently verified V3.11 case result and audit hashes; figure hashes; Rev2 PDF digest.

Science caveats: source synthetic 29/11/4 cooler; four actual original ceramic spatial FEM fields and 88 nonlinear axial legs, but no integrated full 430-domain volume or native cavity-gas PDE; 3 mm effective gas gap; unknown paired commercial P/N material and production interfaces. Material-factor screens are not statistical tolerances. Source-result conservation is not experimental validation.

Publication checks: original 30-page PDF SHA preserved; previous 37-page cumulative PDF remains present and unchanged; eight V3.11 accepted audits cross-checked against source result hashes and energy thresholds below 2e-9 W; 34-page Rev2 PDF confirmed; section/appendix coverage checked; no overfull-box error or page overflow in MuPDF text/image bounding-box scan.
