# Standalone archived-FEM assessment — Revision 2

Build the LaTeX scientific assessment from immutable archived mesh and actual
Elmer fields, without a mesh generator or physics rerun:

```bash
python3 reports/build_engineering_report.py
```

The host uses existing `pdflatex` and `mutool`. Scientific postprocessing uses
the unchanged pinned `fem/run_g2b.sh` image (NumPy, SciPy, Matplotlib, meshio and
Pillow). No new host dependencies are required.

The reader-facing PDF is `generated/HgCdTe_Engineering_Assessment.pdf`. It has a
neutral title and attribution, scientific operating conditions, public source
citations, actual FEM figures and a formal verification matrix. Repository
paths, source filenames, usernames, source hashes and internal milestone/case
labels are excluded from its pages and identifying metadata. Personal author
attribution is omitted; scientific references retain publication/vendor details.

Verified delivery: 15 pages, 6,724,033 bytes; all 14 generated scientific figures,
the PDF, numerical tables, verification matrix and input audit reproduce byte for
byte in an independent build. The full default suite passes 85 tests with 8
optional solver tests skipped; CLI quick and geometry-demo regressions pass.

Machine provenance remains separate and complete:

- `generated/report_inputs.json`: immutable evidence-chain checks, compressed and
  uncompressed field hashes, node/cell correspondence, reconstructed J/q errors,
  numerical means, generator/input/figure digests and material limitations.
- `generated/verification_matrix.json`: verdicts and their exact archival sources.
- `generated/report_validation.json`: PDF digest/size/page count, forbidden-text
  and metadata checks, LaTeX errors and rendered-page checks.
- `generated/reproducibility_check.json`: independent byte-reproduction evidence.
- `generated/figures/`: revision-controlled 600 dpi mesh renderings and vector
  scientific section/result figures.

The enlarged package and TEC views use actual boundary triangles, closed with
exact tetrahedral intersections. The annotated 3D temperature and detector/attach
panels use the accepted nitrogen_patch1 raw and derived solution. Body means are
volume-weighted from those fields; the line joining means is explicitly a visual
guide, not a continuous axial profile. No conceptual CAD image, gas volume or
hybrid wire arc is invented. The registered field panel masks passive package
potential from physical electrical interpretation.

```bash
./fem/run.sh pytest -q reports/test_reader_validation.py reports/test_verification.py tests/test_engineering_report.py
./fem/run.sh pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/report-quick
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/report-pellet
python3 reports/build_engineering_report.py --out outputs/report-reproduced
python3 reports/check_reproduction.py
```

Geometry tests check exact P1 intersections, coplanar deduplication, field
correspondence and void preservation. Reader-policy tests cover every forbidden
identifier, line wrapping, Unicode hyphens and visible hashes. Matrix tests
preserve the distinction between coarse passes and fine failures. Default pytest
skips optional physics reruns. Report tests load their repository-only tools
explicitly and work without the FEM wrapper's repository PYTHONPATH.
Metadata tests decode Unicode PDF strings before checking identity text.

`--skip-figures` recompiles only if source, input, figure and derived-record hashes
still match. Temporary decompressed VTUs are removed after reading; rendered
pages, LaTeX intermediates and section arrays are ignored. The contact sheet is
a layout QA artifact. No large mesh/VTU is duplicated into the report directory.

The scoped coarse checkpoint remains unchanged. All three converged fine cases
still fail the independent bath-gradient 1% gate (1.51–1.66%); full G3b and OEM
accuracy remain unqualified. The illustrated case has 907 patches; operating
comparisons use 442 patches on the coarse bulk mesh. G3a is a separate geometry.
Pre-solder is physically present at the header/alumina interface per the supplied
hardware information; the current 50 µm/k2 mount remains a generic thermal proxy,
not an identified metallic joint or metallurgical model. Hybrid-wire, opaque-grey
window, material-grade, carrier-transport and gas-CFD limitations remain explicit.

All physics implementation, baseline evidence and LSDDTS remain untouched.
Revision 1 is retained in version-control history.
