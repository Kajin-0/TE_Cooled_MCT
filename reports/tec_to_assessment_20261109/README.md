# Thermal Performance of a Three-Stage Thermoelectric Cooler: A TO-Package Engineering Assessment

This is the **standalone, publication-facing engineering assessment** of the present 29/11/4 synthetic cooler and its eight independently audited gas pressure/species operating-point results. It is fully self-contained for device and thermal engineers. It does not require the reader to review an older assessment or study lineage. Detector behavior is strictly a prescribed thermal load. It is a conditional model, not validated proprietary equipment or a measured performance certificate.

- PDF: [TEC_TO_Package_Engineering_Assessment_20261109.pdf](TEC_TO_Package_Engineering_Assessment_20261109.pdf)
- Editable source: [report.tex](report.tex)
- Original saved source data and audit evidence: [eight registered source-model cases](../../data/v3_11_rev3_backfill_source_20261109/)
- Source plots, preserved by reference: [gas species](../current/figures/v311_backfill_species_pressure_cold_temperature.pdf), [krypton pressure](../current/figures/v311_krypton_pressure_sensitivity.pdf), [opaque TEC CAD](../current/figures/tec_solid_inspection.png), [TO package CAD](../current/figures/cad_package_shaded.png)

To rebuild, from this directory run `pdflatex -halt-on-error -interaction=nonstopmode report.tex` twice. Required figures are relative to `../current/figures`. No PDE / numerical simulation runs during report construction.

**QA:** A4; 9 pages; no overfull/underfull boxes or missing LaTeX references; cover and device-section opaque shaded CAD manually inspected; eight accepted runs, independent thermal and electrical audits, original 11,791 TET4 fields and SHA256 manifest referenced. PDF text scanned for unintended legacy-document wording; none present. Original cumulative 30-page report and 38-page historical report preserved byte-identically.
