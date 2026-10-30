# Reproduce completed Cold20 and the independent bath check

Use the existing session and unchanged pinned runtime. No host install or image
rebuild is required. Existing output directories are immutable; choose new
labels for a replay. The following documents the actual run labels.

```bash
./fem/run.sh python fem/archive_cold_convergence.py --verify
./fem/run_g2b.sh python -m tecooledmct.cold20_solver \
 --mesh outputs/cold-convergence/mesh30 --case outputs/cold20/bench_direct \
 --backend big_umfpack --restart outputs/cold-convergence/cu_off30 \
 --reference outputs/cold-convergence/cu_off30
./fem/run_g2b.sh python -m tecooledmct.cold20_projection \
 --source-mesh outputs/cold-convergence/mesh30 --source-case outputs/cold-convergence/cu_off30 \
 --target-mesh outputs/cold-convergence/mesh20 --out outputs/cold20/transfer_loaded
./fem/run_g2b.sh python -m tecooledmct.cold20_solver \
 --mesh outputs/cold-convergence/mesh20 --case outputs/cold20/loaded20_direct_P1 \
 --backend big_umfpack --projection outputs/cold20/transfer_loaded --timeout 1800
./fem/run_g2b.sh python -m tecooledmct.cold20_refined_lu \
 --mesh outputs/cold-convergence/mesh30 --case outputs/cold20/bench_refined_lu \
 --restart outputs/cold-convergence/cu_off30 --reference outputs/cold-convergence/cu_off30
./fem/run_g2b.sh python -m tecooledmct.cold20_refined_lu \
 --mesh outputs/cold-convergence/mesh20 --case outputs/cold20/loaded20_refined_replay \
 --restart outputs/cold20/loaded20_direct_P1 --reference outputs/cold20/loaded20_direct_P1 \
 --timeout 1800
./fem/run_g2b.sh python -m tecooledmct.cold20_bath_mesh \
 --parent outputs/cold-convergence/mesh20 --out outputs/cold20/bath_mesh
./fem/run_g2b.sh python -m tecooledmct.cold20_projection \
 --source-mesh outputs/cold-convergence/mesh20 --source-case outputs/cold20/loaded20_direct_P1 \
 --target-mesh outputs/cold20/bath_mesh --out outputs/cold20/transfer_bath
./fem/run_g2b.sh python -m tecooledmct.cold20_refined_lu \
 --mesh outputs/cold20/bath_mesh --case outputs/cold20/bath_coupled \
 --projection outputs/cold20/transfer_bath --timeout 1800
```

The supplied plan files were registered before their numerical trials. The
same-mesh backend acceptance bounds remain2 µK,20 nV,2 µA on each cut and
identical primary-gate booleans. Native LU refinement is serial and ABI-specific
to the pinned64-bit UMFPACK wrapper. A private `LD_PRELOAD` library passes all
numeric-factorization arguments unchanged, copies the current matrix for native
residual refinement, then restores the local environment after execution. It
does not modify installed Elmer or another process, and never reuses a previous
iteration's numeric LU. Compile inputs/status, binary hashes, source snapshots
and actual solve/refinement logs are retained.

Passive and transfer qualification commands:

```bash
./fem/run.sh pytest -q tests/test_cold20.py
./fem/run_g2b.sh python -m tecooledmct.cold20_solver \
 --mesh outputs/cold-convergence/mesh30 --case outputs/cold20/passive30_gmres \
 --backend gmres_ilu1 --current 0 --load 0
./fem/run_g2b.sh python -m tecooledmct.cold20_projection \
 --source-mesh outputs/cold-convergence/mesh30 --source-case outputs/cold20/passive30_gmres \
 --target-mesh outputs/cold-convergence/mesh20 --out outputs/cold20/transfer_passive_v2
./fem/run_g2b.sh python -m tecooledmct.cold20_solver \
 --mesh outputs/cold-convergence/mesh20 --case outputs/cold20/passive20_gmres \
 --backend gmres_ilu1 --projection outputs/cold20/transfer_passive_v2 --current 0 --load 0
./fem/run_g2b.sh python -m tecooledmct.cold20_projection \
 --source-mesh outputs/cold-convergence/mesh30 --source-case outputs/cold-convergence/cu_off30 \
 --target-mesh outputs/cold-convergence/mesh30 --out outputs/cold20/transfer_replay
./fem/run_g2b.sh python -m tecooledmct.cold20_solver \
 --mesh outputs/cold-convergence/mesh30 --case outputs/cold20/bench_P1_replay \
 --backend gmres_ilu1 --projection outputs/cold20/transfer_replay \
 --reference outputs/cold-convergence/cu_off30
```

`transfer_passive` from the older protected passive source is a retained failed
absolute1 pV check; it must not be relabeled passed. `cold20_picard`,
`cold20_krylov`, `cold20_tight`, `cold20_compact` retain numerical development
trials, not recommended default backends. The completed1e-13 fine Picard field
fails independent current/energy checks and is excluded. Do not infer acceptance
from exit status/nonlinear change alone. The first timing compile failure is
explicitly a setup failure, with no Elmer PDE execution.

After actual cases complete:

```bash
./fem/run_g2b.sh python -m tecooledmct.cold20_analysis --study
./fem/run.sh python -m tecooledmct.cold20_figures --out outputs/cold20/extra_figures
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/cold20-cli
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/cold20-pellet
./fem/run.sh python fem/archive_cold20.py --verify
```

The new comparison registry names every actual mesh/case/diagnostic and records
the frozen comparison/plotting sources. Figures contain actual tetrahedron
sections, actual solved T and true owner-side triangle fluxes. Independent bath
extraction references known I·V+load, not reactions. All125 opt-in tests and
actual case/geometry audits are distinct evidence. The old PDF is never rebuilt.

For a fresh clone, first verify archives. Restore compressed inputs into a
**new outputs directory** using the reversible helper, for example:

```bash
python3 fem/restore_cold20.py \
 --source fem/results/cold_interface_convergence_20261030/device/cold30um/mesh \
 --out outputs/replay20/mesh30
python3 fem/restore_cold20.py \
 --source fem/results/cold_interface_convergence_20261030/device/cold30um/case \
 --out outputs/replay20/source30
python3 fem/restore_cold20.py \
 --source fem/results/cold_interface_convergence_20261030/device/cold20um_FAILED/mesh \
 --out outputs/replay20/mesh20
```

That last archive name reflects the earlier failed solve; its mesh was audited
and is the exact geometry used here. Restored fields/results keep original
provenance and carry `new_solver_execution:false`; restoration is not a PDE run.
Each compressed field/result is checked against its uncompressed SHA256.
Pass restored paths and **new output labels** to the projection/solver commands.
Case writers rebuild paths and callbacks, then genuinely execute Elmer.

New archives store actual raw fields for completed benchmarks, solver inputs,
statuses, source/compiled-binary evidence, all failed trials and initial files.
Derived fields are retained for primary fine/bath cases; others are reproducible
from raw T/phi with the frozen postprocessor. Parent Cold30/Cold20 mesh evidence
is referenced by protected path/hash, avoiding duplicate geometry. Never change
the archived files or earlier sources to make a later gate pass.
