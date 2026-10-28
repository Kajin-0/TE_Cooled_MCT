# Reproduce G2c material/contact numerical checks

Read PHASE1_G2C_RESULT.md and G2C_MATERIAL_PROVENANCE.md first. This milestone
qualifies numerical implementations under explicit assumptions. OEM grade matching
and full device-family validation remain open. Prior checkpoints are immutable.

Use the existing pinned `tecooledmct-fem:26.2.1` image and existing `sim` session.
`fem/run_g2b.sh` retains four CPU / 12 GiB limits, no network and the project-only
mount. No host package or shared image installation is needed for these runs.

```bash
./fem/run_g2b.sh python -m tecooledmct.fem_g2c_run
./fem/run_g2b.sh python -m tecooledmct.fem_g2c_contact \
  --out outputs/fem-g2c-contact-fine --baseline outputs/fem-g2c/summary.json
# If the initial contact study fails ONLY its zero-current cut gate:
./fem/run_g2b.sh python -m tecooledmct.fem_g2c_contact_refine
./fem/run_g2b.sh python -m tecooledmct.fem_g2c_stack
./fem/run_g2b.sh python -m tecooledmct.fem_g2c_low_temperature
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/check-g2c
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/pellet-g2c
```

The stage runner solves four actual meshes, constant and synthetic regressions,
a source-frozen comparison and a genuine 3D synthetic Thomson rod. `--stage-only`
omits the independent rod and is a narrower checkpoint. The constant regression
is independently re-postprocessed with the unchanged G2a verifier. The new
postprocessor follows the actual Elmer nodal-coefficient quadrature; J is not
assumed constant in variable-coefficient elements. Triangle cuts use degree-four
quadrature. Derived fields contain T/phi/E/J/q/Joule and actual body IDs.
Raw terminal-corner gradients and density peaks are not claimed converged.

`compile_profile` creates six real Fortran material procedures and invokes
`elmerf90` in the pinned image. Each checks the local temperature before
interpolation and calls `Fatal` outside coverage. Rho, S, k are interpolated;
sigma is reciprocal rho at nodes. ThermoElectricSolver interpolates nodal
coefficient values at its Gauss points. Its conservative `div(T S J)` term
contains Thomson conversion. There is no additional double-counted Thomson source.
Each accepted case records actual SIF/VTU/status, wall/CPU/RSS and source hashes.
Subsequent contact cases warm-start from a hashed actual solved result on the
same mesh; they still execute the full PDE and independent checks.
Tests also deliberately execute an out-of-range case and require nonzero exit.
The initial 300 K trial was rejected at an iterate; it is not a device prediction.

The contact runner creates 16 explicit transition volumes within the leg ends,
using OCC BooleanFragments, HXT tetrahedra and Netgen optimization. Both original
leg material and transition domains retain the same thermopower assumption.
Area-specific added resistances are independently tunable. At zero added values,
all material properties exactly equal the leg and recover the original continuum.
The pure Contact parameter object's standalone layer coefficients describe the
added resistance alone; actual total zone coefficients include the base BiTe
resistivity and inverse conductivity. The generated Fortran is authoritative.
The actual added I²R heat remains in those domains. Constant-property contact
checks are verification of a phenomenological transition model, not measured OEM
Sn-Sb solder. A thin metallic solder model with its own thermopower, separate
contact data and full-stack contact sensitivity is not established here.

Actual mesh audits compare box volumes, all shared face areas, the unique
conductor path and point/edge shorts. The contact/full-stack runs additionally
prove tetra-face connectivity inside every domain and across all conducting and
thermal solids. SICN below 0.01 is rejected. Early meshes that failed sliver or
zero-current-cut gates remain unaccepted development attempts. The supplemental
contact refinement reads the failed initial study, freshly re-verifies its four
completed driven field files and performs two genuine finer passive solves. It
refuses unexpected failures, retains the original summary/fields/statuses and
does not invent repeated executions. The accepted contact summary documents
this adaptive mesh policy explicitly. New ElmerGrid
output is independently checked against original nodes, tetrahedra and body IDs;
converter material renumbering cannot silently change the PDE.

The full-stack runner uses the protected G2b mesh arrays/manifests from the
tracked archive, not an untracked raw-run dependency. The fine original Gmsh mesh
is reused; the coarse Gmsh file is re-encoded from its exact recorded conformal
nodes, elements and physical boundary IDs. Both are re-audited and passed through
ElmerGrid again; the resulting tetrahedron/body mapping is checked explicitly.
The old G1/G2a/G2b source/evidence is never rewritten. The source-backed stack
uses corrected v2r1 and has a
295 K bath, +0.1 A and zero top load to stay within the ingested 200–300 K interval.
Intermediate ceramics are solved unknowns. This is not a 300 K OEM comparison.

The source registry and 160 OEM curve readings are committed JSON. To repeat
source digitization, download the original URLs in `data/g2c/retrieval.json` to
`outputs/g2c-sources` and verify the recorded PDF SHA256. Use isolated PyMuPDF
1.26.7 under `outputs/g2c-source-tools`, then:

```bash
./fem/run.sh env PYTHONPATH=/work/outputs/g2c-source-tools:/work \
  python scripts/digitize_g2c.py
```

PyMuPDF is needed only for inspecting original PDFs, not simulations. The original
copyrighted PDFs remain untracked. Axis coordinates, vector markers/polylines,
SI conversion and conservative reading bounds are retained. Source curves are
separate from FEM results. OEM current/load/environment matching is strict;
no interpolation of an unrun FEM sweep is passed off as a solved point. Split
selection predates comparisons. The family objective uses reading-bound-scaled
residuals and explicitly does not represent a statistical likelihood, unique
parameter identification or completed calibration.

After all numerical gates and full tests pass, generate plots/report and archive:

```bash
./fem/run.sh python fem/report_g2c.py
python3 fem/archive_g2c.py
```

The report helper requires the completed passing test log at
`logs/pytest-g2c-final.log`. The archive helper validates execution source hashes
and actual SIF/VTU hashes, refusing changed or failed results. It records the
current code commit as baseline. Generated Fortran sources, compilation records
and shared-library hashes are retained; machine binaries remain untracked.
Accepted selected VTUs are actual PDE fields. Case SIFs retain execution paths;
regenerate them and the libraries using the runners in a fresh checkout.

Qualification is deliberately separate: implementation checks may pass while
OEM-grade/contact/device validation remains NOT ESTABLISHED. Do not extrapolate
outside 200–300 K, merge different specimens, compare dry-N2 curves against a
vacuum-only solid stack, or tune unknown interfaces to extrema as measured data.


The additive v2 data file extends the same original HE markers to 40–300 K;
Corrected v1r1 remains the stage default; the full stack and low-temperature
check use corrected v2r1. Their shared 200–300 K subset is identical. The low-temperature runner
uses v2 with fixed 200/190 K ceramics and +0.02 A to test actual local-temperature
material functions below 200 K. That boundary-controlled 190 K is not an OEM
performance prediction. Versioned intervals remain fail-closed. The extra source
extraction script preserves the v1 subset exactly.


Prepublication N-axis extraction error: affected source-based runs were rejected
and rerun using v1r1/v2r1. See the provenance erratum and source-figure anchor tests.
`fem_g2c_contact_reverify` rechecks the unaffected G1-constant contact fields and
verifies that their actual base callback source matches regenerated constants;
it records used dependencies separately from the original broad development
manifest. It does not claim new PDE solves. No incorrect-input result is accepted.
