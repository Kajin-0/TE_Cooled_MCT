# Archived-FEM engineering report

Build the LaTeX scientific assessment without running a mesh generator or physics
solver:

```bash
python3 reports/build_engineering_report.py
```

The host entry point needs the existing `pdflatex` and `mutool` tools. Scientific
postprocessing uses the unchanged pinned `fem/run_g2b.sh` image (NumPy, SciPy,
Matplotlib, meshio and Pillow). No new host packages or Python dependencies are
installed. Output:

- `generated/HgCdTe_Engineering_Assessment.pdf`
- `generated/figures/`: revision-controlled 600 dpi mesh renderings and vector
  section/field/result figures.
- `generated/report_inputs.json`: exact archive, raw/derived field, generator and
  figure digests; field correspondence/reconstruction checks.
- `generated/report_validation.json`: LaTeX, PDF text, page-render and size checks.

`generated/render/` contains locally rendered PDF pages; the contact sheet is a
layout QA artifact. Temporary decompressed VTUs live only in a temporary directory
under ignored `outputs/report_build_cache` and are removed after reading. No raw
VTU or complete mesh is duplicated into the report deliverables. The small
section-array cache is reproducible and is not committed.

```bash
./fem/run.sh pytest -q tests/test_engineering_report.py
./fem/run.sh pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/report-quick
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/report-pellet
```

The first command tests exact tetrahedron intersections, affine P1 transfer,
coplanar-face deduplication, permuted-node/cell correspondence and preservation
of separated solid voids. Default pytest leaves optional physics reruns disabled.
The report additionally checks the entire immutable G1–G3b evidence chain,
compressed/uncompressed field hashes, actual node/cell ordering, material IDs,
independent J/q reconstruction and archived volume means/terminal voltage.

An output directory can be selected with `--out outputs/report-reproduced`.
`--skip-figures` is permitted only if recorded source/input/figure hashes still
match. It recompiles and revalidates the existing scientific figures.

The delivered 19-page PDF (7,467,457 bytes), all 12 figures, numerical tables and
input audit were reproduced byte for byte in a separate output directory:

```bash
python3 reports/build_engineering_report.py --out outputs/report-reproduced
python3 reports/check_reproduction.py
```

`generated/reproducibility_check.json` records each compared digest. The report
geometry tests passed (4 tests); the full default suite passed (80 tests, with
8 optional solver tests skipped). CLI quick and geometry-demo checks also passed.
These are report/regression checks; historical genuine Elmer executions remain
the source of the illustrated fields.
The report test imports its repository-only geometry module directly, so it also
runs in ordinary CI without the FEM wrapper's repository `PYTHONPATH`.

The report treats G3b as a **scoped checkpoint**. Fine bath-gradient errors of
1.51–1.66% still exceed the unchanged1% gate; no report or plot repairs that
physics qualification failure. The nitrogen_patch1 field is accepted on the
coarse bulk mesh with907 surface patches. Primary operating comparisons use
442-patch coarse cases, and G3a remains a separate geometry. Pre-solder is
physically present according to the user, while the current FEM mount remains
a generic50um/k2 thermal proxy, not identified metallic pre-solder.

Only actual archived FEM geometry is rendered. Approved Revision6 is a separate
mismatch table from its registry/audit; no CAD images are imported. Package phi
is a computational passive extension and is excluded from physical electrical
interpretation. Hybrid wire arcs and gas volumes are not invented in the images.
No NIST logo/branding, endorsement, manufacturer accuracy or full CFD is claimed.
Baseline evidence and LSDDTS remain untouched.
