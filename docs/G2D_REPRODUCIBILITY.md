# Reproduce G2d without changing earlier checkpoints

Run from `/home/User/TE_Cooled_MCT` in the existing `sim` session. Reuse the pinned
`tecooledmct-fem:26.2.1` image (ID
`sha256:24aa962831260903f1aeeb5209969ae012efab09d188cd8aac99f2f55f739195`).
No host installation, new tmux session, other repository or LSDDTS operation is needed.
Elmer source is `a19504ac53ec222e3355e182b08f2ff280c2203a`, Gmsh4.13.1.
The original wrappers remain unchanged: four CPUs, network-none, project-only mount,
8 GiB for ordinary checks and 12 GiB for full-stack runs. See the G2c reproduction
and source guides for protected input provenance.

## Deterministic screening and genuine PDEs

```bash
./fem/run.sh python -m tecooledmct.g2d_data
./fem/run.sh python -m tecooledmct.g2d_analysis
./fem/run.sh python scripts/audit_g2d_sources.py
./fem/run_g2b.sh python -m tecooledmct.g2d_fem
./fem/run_g2b.sh python -m tecooledmct.g2d_budget
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/check-g2d
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/pellet-g2d
```

Capture command logs under the exact names used by `fem/report_archive_g2d.py`
(see the tracked `provenance` directory); its acceptance gate requires completed
passing tests and numerical/source summaries. The full-stack command executes
four actual Elmer invocations: one strict source-profile 300 K coverage probe
and three constant-law .2 A diagnostics. The coverage probe's nonzero exit is
expected and preserved as a failed prediction; other solver failures abort.
There are three accepted new performance points, never four. Existing .1 A G2b
holdout fields are read-only evidence, not another solve. The .2 A perturbed cases
warm-start from the actual baseline state, with restart hashes, and still solve
both PDE unknowns. There is no reduced-network substitution for Elmer.

`g2d_analysis` reads calibration values only for fitting and writes
`outputs/g2d-analysis/frozen_fit.json` plus its SHA before loading held-out
numeric values for scoring. It fits rho/S/k scales only; geometry/contact/mount/load
are not freely co-fitted. Fit weights use calibration vertical reading bounds,
not full-curve slopes. The retained preliminary attempt is **unaccepted** because
its weights depended on neighboring held-out chart slopes; do not use it for
inference. Its replacement keeps the original model, hypothesis bounds and PDE
directions. The selected fit hits a bound and is only a network diagnostic.
Do not tune these choices against the reported holdout residuals. This is algorithmic
separation, not a newly blinded experimental validation: prior G2c comparisons and
the discarded preliminary attempt were already available.

`g2d_data` verifies hashes of all earlier accepted source/tests/evidence before
preparing split files. Rerunning it deterministically writes identical new G2d
registration files. Changing any registered data requires an explicit new version
and fresh calibration-only freeze. Do not overwrite prior accepted evidence.
`g2d_budget` reconstructs actual q/J.E from raw T/phi and the executed constant
coefficients; its stage control volumes include shared plates/routing, not
isolated textbook stages. `actual_material_interval_passed` in constant-law
metrics checks a mathematical interval only, not measured material coverage.

The actual mesh is the previously verified fine G2b mesh, re-audited for body
face connectivity, graph/path, geometry/contact areas, quality and ElmerGrid
mapping. No new parameter-direction refinement, alternate topology mesh or
full-stack contact transition mesh is claimed. All175 cuts and current/energy
checks must pass unchanged gates. Source code must remain unchanged during runs;
recorded hashes are checked before archival.

## Source review and archive

`data/g2d` contains immutable split manifests, a hypothesis parameter registry,
original OEM panel/rounding review and a separately qualified above300 K candidate.
The candidate is not used as a material extension. Its original HP A-axis tables
are visually audited in archived screenshots; SI conversions, signs and source
PF/ZT anchors are independently checked, including printed-digit rounding.
The primary PDF can be fetched from `primary_institutional_pdf_url` in
`material_extension_review.json`; SHA256 must match before a fresh visual review.
A transient 504 on the repository proxy was resolved with its standard blob
redirect endpoint. No unrelated-grade stitching or extrapolation is authorized.
The source paper's own constant extrapolation is explicitly not adopted here.

The source audit also re-interpolates all160 OEM readings from protected original
PDF vector paths, retaining x/y coordinates, axis origins/scales and +/-1 PDF-point
reading bounds. The literal 27 C panel is nominal300 K in preserved G2c data;
300.15 K is not silently reinterpreted as an exact300 K experiment. Dry N2 panels
and source-backed295 K predictions remain separate. No new experimental data or
new independent digitization is claimed by rechecking existing vector extraction.

After all checks, on the host record the existing image and generate the report/archive:

```bash
docker image inspect tecooledmct-fem:26.2.1 > outputs/g2d-image.json
./fem/run.sh python fem/report_archive_g2d.py
```

The gate validates source, fit freeze, SIF, raw VTU, stage budgets and prior-checkpoint
hashes before publishing. It writes `docs/PHASE1_G2D_RESULT.md` and
`fem/results/g2d_20261029`, including chart/residual/resource/cut/heat tables,
case inputs/logs, source audit, compiled callback provenance, failure records and
all three genuine raw T/phi fields. Raw fields are gzip-compressed deterministically;
the uncompressed hashes equal execution hashes. The immutable mesh is referenced
by hash in the earlier G2b archive to avoid duplication. For independent inspection:

```bash
gzip -dc fem/results/g2d_20261029/fields/baseline/fields_t0001.vtu.gz > outputs/g2d-baseline.vtu
```

The archived `checksums.json` records exact source and artifact SHA256s, code
checkpoint, three new accepted solves, one rejected source probe and one reused
G2b holdout. It does not count network BVPs, postprocessing or test smokes as
production solves. Source snapshots/hashed raw fields distinguish historical
execution from later re-verification. Normal CI runs Python checks without the
optional Elmer smokes; local `TE_FEM_SMOKE=1` evidence is retained separately.

**Verdict:** D1/D2 and bounded constant-law PDE sensitivity are verified. D3
source-backed OEM-family FEM fit/holdout qualification remains FAILED/BLOCKED.
The report specifies the missing grade/geometry/contact/boundary measurements;
conservation, network fit improvement and broad chart bounds do not establish
OEM device accuracy.
