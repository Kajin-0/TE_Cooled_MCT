# Reproduce the cold-interface investigation

Use the existing `sim` session and pinned image through the existing wrappers.
No installation, host change, enclosure operator, historical source change or
report rebuild is required. Choose new output labels for a replay; runners reject
existing directories. The commands below record the actual checkpoint locations.

```bash
./fem/run.sh python fem/archive_corrected_thermal.py --verify
./fem/run_g2b.sh python -m tecooledmct.cold_interface_audit \
 --mesh outputs/geometry-complete-v4 --case outputs/corrected-thermal/cu_off \
 --out outputs/cold-convergence/coarse_diagnosis
./fem/run_g2b.sh python -m tecooledmct.cold_layer_benchmark \
 --out outputs/cold-convergence/benchmark
./fem/run_g2b.sh python -m tecooledmct.cold_roi_mesh \
 --out outputs/cold-convergence/mesh30 --level 0
./fem/run_g2b.sh python -m tecooledmct.cold_roi_mesh \
 --out outputs/cold-convergence/mesh20 --level 1
./fem/run_g2b.sh python -m tecooledmct.cold_roi_run \
 --mesh outputs/cold-convergence/mesh30 --case outputs/cold-convergence/cu_off30
./fem/run_g2b.sh python -m tecooledmct.cold_roi_run \
 --mesh outputs/cold-convergence/mesh20 --case outputs/cold-convergence/cu_off20
```

The last command is the retained **failed 32-bit factorization attempt**. It
produced no temperature/potential solution and must not be included as a solved
convergence level. A setup attempt under `cu_off20_big` was rejected before
execution because the input comparison also compared output paths. That check
was corrected to normalize only each case directory. Its log and SIF are retained.
The separate retry changes only direct-solver index width and case paths, with
the original mesh, fresh300 K/phi0, PDE, material coefficients and tolerances:

```bash
./fem/run_g2b.sh python -m tecooledmct.cold_roi_big_run \
 --mesh outputs/cold-convergence/mesh20 --case outputs/cold-convergence/cu_off20_big_retry \
 --failed outputs/cold-convergence/cu_off20
```

This fresh-start retry remains bounded at1200 s. Its actual status and any
failure are retained: it timed out after three completed nonlinear steps,
last change0.005277926. A separate numerical initialization plan was registered
before the next attempts. First, a same-mesh actual rerun checks an ASCII3
identity-permutation initial file made from the genuine middle-mesh field.
It completed in two iterations, reproducing die mean within0.34 µK and voltage
within4.8 nV. The fine retry then uses nearest solved middle-field node values
only as its starting guess. This is an explicit cross-mesh initialization,
not interpolation of a final accepted field. There are no cross-void interpolated
triangles or prescribed final temperatures; the final evidence must be the
fine mesh's own actual converged coupled solve, with all original checks.
This projected fine retry also timed out after three steps (last change
0.001588001); it supplies no final VTU, accepted temperature or flux. The
fine-interface audit command below applies only after a successful future
fine execution. It was **not** run on either incomplete field in this checkpoint.

```bash
./fem/run_g2b.sh python -m tecooledmct.cold_roi_projected_run \
 --mesh outputs/cold-convergence/mesh30 --case outputs/cold-convergence/same_mesh_restart_check \
 --seed outputs/cold-convergence/cu_off30
./fem/run_g2b.sh python -m tecooledmct.cold_roi_projected_run \
 --mesh outputs/cold-convergence/mesh20 --case outputs/cold-convergence/cu_off20_projected \
 --seed outputs/cold-convergence/cu_off30 \
 --same-mesh-check outputs/cold-convergence/same_mesh_restart_check
./fem/run_g2b.sh python -m tecooledmct.cold_interface_audit \
 --mesh outputs/cold-convergence/mesh30 --case outputs/cold-convergence/cu_off30 \
 --out outputs/cold-convergence/diagnosis30
```

Do not run `cold_interface_audit` on Cold20 until an actual converged field
exists. `cold_convergence_summary` detects the failed solver status and excludes
that mesh from QoI/GCI fitting. It retains the geometry and failed-run metadata.

The original mesh metrics were computed on a new copy of the protected
`mesh.npz` and `manifest.json` under `outputs/cold-convergence/coarse_mesh`:

```bash
./fem/run.sh python -m tecooledmct.cold_roi_mesh \
 --out outputs/cold-convergence/coarse_mesh --metrics-only
./fem/run.sh python -m tecooledmct.cold_convergence_summary \
 --out outputs/cold-convergence/study.json
./fem/run.sh python -m tecooledmct.cold_convergence_figures \
 --out outputs/cold-convergence/figures
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/cold-convergence-cli
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/cold-convergence-pellet
./fem/run.sh python fem/archive_corrected_thermal.py --verify
./fem/run.sh python fem/archive_cold_convergence.py --verify
```

Summary/figure modules intentionally reference the checkpoint labels in their
`CONFIG` registry. For a completely separate replay, pass the corresponding
paths through their Python functions or use an additive, versioned comparison
registry; do not overwrite protected outputs to make labels match.

`data/cold_convergence/plan.json` was written before new mesh/solver executions.
Its hash is in the independent benchmark, mesh and summary evidence. The
benchmark uses Elmer's actual `HeatSolver`; the device uses the actual coupled
`ThermoElectricSolver`, never a prescribed field or HeatSolver replacement.
Device runs have a1200 s child timeout, four-CPU/12 GiB container bound and
nonlinear relative tolerance1e-9. Status files retain elapsed/CPU/peakRSS,
iterations, exit code and timeout. Sources/SIF/actual-field hashes and new
execution source snapshots are archived. The projected starting file is
explicitly labeled `projected_initial_guess.result`, with a separate hash and
initialization metadata; it is never a solved VTU or a final QoI. Median nearest
distance is zero,95th percentile34.57 µm, maximum771.64 µm in the sparsely meshed
package. Approximate starting values have no acceptance status. The old field used for the original
level remains protected in its earlier archive; it was independently re-extracted,
not rerun or rewritten in this checkpoint.

The new archive contains both new meshes, actual Elmer mesh files, inputs,
logs, endpoint weights, callbacks, raw and derived fields, all benchmark meshes
and fields, per-triangle diagnostics, numerical comparisons and figures. Large
text/field files use deterministic gzip with uncompressed hashes. To inspect a
field, decompress it into a **new outputs directory**, then use meshio/ParaView.
Do not edit the published archive. Rebuild case paths/callbacks using the runner
when rerunning; archived SIF paths identify the original execution environment.

Archive verification checks current source and artifact hashes, source snapshots,
real solver completion, mesh/field correspondence, retained failed gates and all
earlier guards. GitHub's existing Python CI runs the portable suite/CLI/demo;
the explicitly enabled local120+ test run additionally exercises real Elmer
smokes. A process exit of zero or a passing weak energy balance does not waive
the raw bath1% or interface5% criteria.
