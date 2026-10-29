# Reproduce the scoped G3b checkpoint

**Full G3b gate D is NOT QUALIFIED.** Ten selected coarse integrated cases pass;
all three converged fine cases fail the independent direct-bath1% gate.
The checkpoint publishes accepted cases and quarantines failures separately.
Temperature/voltage convergence and conservative reaction balance do not
override that failed criterion. No numerical tolerance was lowered.

Read [the result](PHASE1_G3B_RESULT.md), `data/g3b/enclosure_registry.json` and
`data/g3b/source_review.json`. This is genuine coupled 3D solid thermoelectric
FEM with reduced conservative gray radiation, rarefied gas films and 1D Au/Cu
leads. It is not gas CFD or an OEM-qualified detector prediction. The gray
window is opaque internally and externally adiabatic; ambient spectral
transmission is absent. The thermistor and additional carrier parts are omitted.

Use `/home/User/TE_Cooled_MCT` and the existing `sim` session. Reuse the pinned
`tecooledmct-fem:26.2.1` image, Elmer source
`a19504ac53ec222e3355e182b08f2ff280c2203a`, Gmsh 4.13.1. The unchanged
`fem/run_g2b.sh` has four CPUs, 12 GiB, network-none and a project-only mount.
No host package installation, other repo, OpenFOAM or LSDDTS is required.

## Fresh geometry and solid controls

On a fresh checkout, create new raw directories. Never overwrite a completed
accepted case or published evidence. Geometry generation itself does not solve
thermal/electrical fields. `fem_g3b_data.preserve()` checks all protected G1–G3a
source/data/evidence before mesh/solve/archival operations.

```bash
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_geometry --level 0 --out outputs/fem-g3b/mesh_h0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_geometry --level 1 --out outputs/fem-g3b/mesh_h1
```

The two solid controls use the new geometry, old gold bonds, header bath and
MCT source, with gas/radiation/Cu leads off. They deliberately call the separate
reference constructor/postprocessor; they are not exchange-enabled cases with
ambiguous toggles. Execute the following inside the pinned container:

```bash
./fem/run_g2b.sh python - <<'PY'
from pathlib import Path
from tecooledmct.g2d_data import ROOT,sha,dump
from tecooledmct.fem_g3b_data import preserve
from tecooledmct.fem_g3b_reference import write_case
from tecooledmct.fem_g3b_reference_post import postprocess
from tecooledmct.fem_g2b_physics import execute_solver
preserve();mesh=ROOT/'outputs/fem-g3b/mesh_h0'
for label,current,load in [('passive_h0',0.,0.),('solid_reference_h0',.1,.002)]:
    case=ROOT/'outputs/fem-g3b'/label
    if case.exists():raise ValueError('Retain completed case; use a fresh raw tree')
    sources=[ROOT/'tecooledmct'/f'fem_g3b_{n}.py' for n in ('data','geometry','reference','reference_post')]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    write_case(mesh,case,current,pbias=.75*load,poptical=.25*load)
    status=execute_solver(case)
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Source changed during execution')
    result=postprocess(mesh,case)
    dump(case/'execution.json',{'source_sha256':hashes,'solver_status':status,'mesh_sha256':sha(mesh/'mesh.npz'),'sif_sha256':sha(case/'case.sif'),'vtu_sha256':sha(case/result['field_source']),'scope':'nine-pin/cap/window solid control; gas/radiation/supply leads off, gold bonds retained'})
    if not result['passed']:raise ValueError('Control acceptance failed')
PY
```

Only the external header underside is fixed at 300 K. No internal cap/window,
pin or ceramic is a bath. Detector heat is one 1.5 mW prescribed bias-power
representation plus .5 mW thermally absorbed optical heat in the actual MCT
volume. Do not add another detector Joule term. Tiny package sigma is a passive
potential extension; it is not physical metal electrical transport. TEC
coefficients are the preserved constant verification law, not calibrated BiTe.

## Surface operators and actual coupled campaign

```bash
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_rays --mesh outputs/fem-g3b/mesh_h0 --out outputs/fem-g3b/operator_h0 --level 0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_rays --mesh outputs/fem-g3b/mesh_h0 --out outputs/fem-g3b/operator_h0p1 --level 1
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_rays --mesh outputs/fem-g3b/mesh_h1 --out outputs/fem-g3b/operator_h1 --level 1
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --case outputs/fem-g3b/vacuum_a0 --initial outputs/fem-g3b/solid_reference_h0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --case outputs/fem-g3b/nitrogen_0 --gas N2 --pressure 100 --restart outputs/fem-g3b/vacuum_a0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --case outputs/fem-g3b/lead_only_0 --radiation-off --restart outputs/fem-g3b/vacuum_a0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --case outputs/fem-g3b/argon_0 --gas Ar --pressure 100 --restart outputs/fem-g3b/nitrogen_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --case outputs/fem-g3b/krypton_0 --gas Kr --pressure 100 --restart outputs/fem-g3b/nitrogen_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --case outputs/fem-g3b/window_high_0 --window-eps .8 --restart outputs/fem-g3b/vacuum_a0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --operator outputs/fem-g3b/operator_h0p1 --case outputs/fem-g3b/nitrogen_patch1 --gas N2 --pressure 100 --initial outputs/fem-g3b/nitrogen_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_refine
# Inspect its expected direct-bath-only rejection, then run the separate local refinement:
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_bath_refine --build
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_bath_refine
# Bath-only refinement also fails the unchanged1% gate; retain it and continue:
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_feedthrough_refine --build
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_feedthrough_refine
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --case outputs/fem-g3b/package_sigma_100 --sigma 1e-14 --gas N2 --pressure 100 --restart outputs/fem-g3b/nitrogen_0
./fem/run.sh python -m tecooledmct.fem_g3b_plate_check
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q > logs/pytest-g3b-final.log 2>&1
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/check-g3b > logs/cli-g3b.log 2>&1
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/pellet-g3b > logs/geometry-g3b.log 2>&1
```

The coupled runner uses default .1 A/2 mW, radiation on and Cu leads on.
Pressure defaults to zero, which eliminates gas exchange exactly; a gas species
name alone does not turn on continuum conduction. `--lead-off` also removes
lead Joule. The preserved publication's first vacuum/nitrogen executions used
the archived earlier iteration-startup implementation; all physical equations
are unchanged. Fresh runs use the corrected startup and may differ at roundoff
or stopping-tolerance scale. Do not claim that fresh executions reproduce their
original source hashes. Exact snapshots and generated Fortran identify what ran.

Each case compiles actual Fortran callbacks, invokes ThermoElectricSolver and
checks actual T/phi fields independently. Surface temperatures update in the
nonlinear iteration. Anderson mixing stabilizes boundary powers, not a reduced
prescribed final temperature. Independent postchecks reconstruct unmixed
radiosity and gas/link heat and reject a stale or one-way source. Two-plate
benchmarks use HeatSolver only as independently soluble 1D exchange references;
they do not replace any 3D thermoelectric package solve.

`--restart` requires exact same actual bulk node/element files. `--initial`
interpolates a hashed accepted field only between the identical bulk discretization
with changed surface patches. For a different bulk mesh use `fem_g3b_refine`: it
transfers only temperature and initializes potential to zero. The rejected
cross-mesh T/phi interpolation produced about 81 W of artificial initial Joule
heat by blending dielectric potentials into copper routes and was stopped by
the MCT coverage check. It is retained as `nitrogen_fine`, never accepted. The
new `nitrogen_fine_verified` identifies the genuinely converged temperature-only
execution that remains **unaccepted** because direct-bath flux error is1.65587%.
The final attempted case is `nitrogen_feedthrough`, using
`mesh_feedthrough/operator_feedthrough`; it remains unaccepted at1.58383%
direct-bath error. `nitrogen_bath` remains unaccepted at1.51412%.
The accepted907-patch representative is `nitrogen_patch1` on the coarse bulk mesh.
The earlier `nitrogen_fine_tonly` attempt reached its900s cap at9.88e-9 and
remains unaccepted; the final fine runner allows at most1800s with unchanged1e-9
nonlinear tolerance. These are
only initial conditions. Both still execute the coupled PDE. `--resume`
rechecks source/SIF/VTU/mesh/configuration and independently postprocesses a
completed actual execution; it does not execute or count another solve. For
example:

```bash
./fem/run_g2b.sh python -m tecooledmct.fem_g3b_run --case outputs/fem-g3b/nitrogen_0 --gas N2 --pressure 100 --resume
```

Source-version checking accepts an old `fem_g3b_physics.py` only with its exact
used snapshot and an exact byte comparison allowing only the three known startup-patch
edits. All other Python/Fortran, mapping, I/O or physical changes fail.
It does not silently attribute old results to new source. The general runner has a900s bound and the fine runner a maximum1800s
per-solver bound; compile/initialization/postprocessing time is additional.
Do not change runtime sources while an execution is active.

## Qualification and archival

Actual meshes prove volume/contact/face topology and the original 181/180
conductor path. The cavity skin is closed; analytic first-hit rays map to actual
same-owner/orientation facets. Symmetric balancing preserves visibility zeros.
Raw reciprocity/closure errors, correction scales and hit-mapping distances are
retained, because balanced closure alone does not establish view-factor accuracy.
The same-bulk442-to-907-patch case separates surface resolution sensitivity.
The final bulk comparison uses429,100 versus1,194,385 tetrahedra, the latter
including local bath refinement of the821,874-tetrahedron intermediate mesh.
The intermediate converged point fails only the direct-bath1% gate and must
return nonzero from `fem_g3b_refine`; do not suppress unrelated failures or call
it qualified. All215 solid domains and its raw field/status remain preserved.

`fem_g3b_bath_refine --build` applies two complete-edge-star bisection rounds to
bath-adjacent cells within1.3mm of each of the nine pin centers. It preserves
material volumes/contact areas, face conformity, the entire TEC discretization
and every cavity triangle. `operator_bath` inherits exactly the original fine
F/gaps/patches and extends the surface weights with zero columns for new nodes;
no additional rays are claimed. ElmerGrid and actual boundary mapping are audited
again. The new test independently checks interface/volume conservation and exact
affine P1 field transfer. A300000-node build cap and1800s solver cap bound this step.
The bath-only refinement still fails the unchanged gate; its field is retained
as unaccepted. `fem_g3b_feedthrough_refine --build` instead refines all material
cells in a0.7mm-radius,0.15mm-half-height neighborhood of each feedthrough at the
header underside, including the glass and pin roots. One complete-edge-star
round produces275377 nodes and1194385 tetrahedra. The original broader0.9mm/
0.25mm selection was rejected before a PDE because it exceeded the node cap.
The final construction preserves the same TEC/cavity and exact inherited
operator_h1 exchange matrices. Its actual coupled solve uses the original
converged-but-bath-unaccepted fine field only as the P1 initial guess.

The converged but bath-unaccepted actual field supplies only the P1-prolongated
initial guess. The source must have zero solver exit,1e-9 nonlinear convergence
and every other physical gate passing; its exact VTU/SIF hashes are verified.
Existing conductor values remain unchanged and new midpoint values are exact
linear averages. The new full coupled solve, not this interpolation, determines
final T/phi. These two attempted fine runs still fail the original direct-bath
gate and remain unaccepted. The bath-unaccepted source field
is archived explicitly as unaccepted for this initialization provenance.

All 175 driven cuts must pass .5%, zero current 1 uA; current/free current
1 uA; global/free thermal residual 1 uW; direct bath gradient 1%; attach cut
5%; package Joule and each internal mechanism balance 1 nW; die mean/max and
cold ceramic changes 1% of lift and voltage 1%. Generated source matrices,
actual boundary mappings, nonnegative gas conductances and final independent
physical residuals are checked. Whole-package horizontal budgets include cap,
pins and each nonlocal source; they are not isolated textbook stage budgets.
Cap transfer inferred from net cap/window exchange is separately labeled and
is not an independent cap-gradient measurement.

The scoped publisher validates all ten accepted cases and two independent plate
checks, plus the exact expected failure of the three converged fine cases, full
regression/CLI outputs, field/SIF/source/operator hashes and
refinement/isolation gates. Capture campaign command logs as `logs/g3b-*.log`.
Published evidence contains actual T/phi VTUs for all accepted cases, a derived
accepted907-patch T/phi/J/q/Joule VTU, mesh/operator arrays, original logs/statuses,
compiler/source snapshots, tables and figures. Generated binary hashes are
retained; local binaries are rebuilt from archived Fortran. Failed development
attempts are explicitly unaccepted and never counted as qualified executions.

```bash
./fem/run_g2b.sh python fem/report_archive_g3b.py --coarse-checkpoint --out outputs/g3b-reproduced
```

The explicit --coarse-checkpoint one-time publication writes `docs/PHASE1_G3B_RESULT.md` and
`fem/results/g3b_checkpoint_20261029`; it refuses to overwrite a tracked published archive.
A custom `--out` writes its own report inside that new project directory.
Decompress actual fields, for example:

```bash
gzip -dc fem/results/g3b_checkpoint_20261029/fields/nitrogen_patch1/fields_t0001.vtu.gz > outputs/g3b-nitrogen-accepted.vtu
```

`checksums.json` records both artifact and current source digests; each execution
retains the exact source version that ran. Per-field uncompressed digests allow
verification after decompression. Postprocessing and report regeneration are
not additional PDE executions. CI runs Python tests/CLI; the archived local
Elmer evidence is scoped numerical verification with failed full-qualification
records kept separately.

Verify the published files and decompressed raw fields without rerunning a PDE:

```bash
./fem/run.sh python - <<'PY'
import gzip,hashlib,json
from pathlib import Path
from tecooledmct.g2d_data import ROOT,sha
from tecooledmct.fem_g3b_data import preserve
preserve();archive=ROOT/'fem/results/g3b_checkpoint_20261029'
ledger=json.loads((archive/'checksums.json').read_text())
for section,base in [('source_sha256',ROOT),('document_sha256',ROOT),('artifact_sha256',archive)]:
    for name,digest in ledger[section].items():assert sha(base/name)==digest,name
for record in archive.rglob('uncompressed_sha256.json'):
    for name,digest in json.loads(record.read_text()).items():
        h=hashlib.sha256()
        with gzip.open(record.parent/(name+'.gz'),'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        assert h.hexdigest()==digest,(record,name)
print('All G3b source, document, artifact and decompressed actual-field hashes pass; G1–G3a intact')
PY
```

The publisher refuses publication without `--coarse-checkpoint`: full G3b is
unqualified. Its summary and checksum ledger explicitly set
`full_g3b_qualified=false`. Both accepted fields and the three rejected
converged fields are archived with separate provenance. Further work must
resolve independent bath-gradient flux before claiming full G3b qualification.
