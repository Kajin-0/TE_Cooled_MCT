# Independent normal-volume studies: reproducibility

Use only this repository, existing sim session and unchanged pinned4CPU/12GiB
`fem/run_g2b.sh` numerical wrapper. No host install is required. Preserve all
earlier source/evidence, the historical15-page PDF and the initial Rev3 edition.
This workflow adds no enclosure, gas, radiation, physical links ON or detector
carrier transport. It does not identify a manufactured OEM assembly.

The preregistered `data/gate_refinement/plan.json` fixes exact normal-edge star
bisection, original raw5%/1% gates, minimum actual SICN0.01 and1M-tet bound.
`solver_bounds.json`, `bath3_bounds.json` and `combined_bounds.json` register
bounded per-case resource settings before their dependent runs. No equations,
loads or acceptance limits change. Every generated mesh must pass actual
material/exterior/contact/circuit and Elmer-grid mapping audits before execution.

## Independent geometry operations

Run each command with a NEW output label; existing meshes/cases are immutable.

```
./fem/run_g2b.sh python -m tecooledmct.gate_refinement \
  --parent outputs/cold-convergence/mesh20 \
  --out outputs/gate-refinement/cold1_mesh --track cold
./fem/run_g2b.sh python -m tecooledmct.gate_refinement \
  --parent outputs/cold20/bath_mesh \
  --out outputs/gate-refinement/bath2_mesh --track bath
./fem/run_g2b.sh python -m tecooledmct.gate_refinement \
  --parent outputs/gate-refinement/bath2_mesh \
  --out outputs/gate-refinement/bath3_mesh --track bath
```

Target contact/bath triangles remain byte-identical. Original points and total
material volumes remain fixed. Incident owner-tetrahedral normal heights halve;
free interior nodes are added. Refining only bath surface triangles is not this
method. Geometry audit records changed body IDs and exact region locks. Shape
quality is Gmsh's actual minSICN; no synthetic proxy replaces it.

The cold track has647657-tet parent; bath track starts from the independently
completed675496-tet archived bath mesh with exactly the same original cold cells.
Parent meshes and solved fields are retained in prior immutable archives. Use
`fem/restore_cold20.py` to decompress archived inputs into a NEW outputs path;
restoration is not a solver execution. The initial fine mesh's historical
`FAILED` label concerns its then-uncompleted solver, not its geometry audit.

## Actual coupled solves

Use `tecooledmct.cold20_projection.build(source_mesh, source_case, target_mesh,
new_transfer)` for body-aware, convex P1 initial guesses, followed by
`tecooledmct.cold20_refined_lu.run(target_mesh, new_case,
projection=new_transfer, timeout=bound)`. These unchanged frozen routines
execute the real upstream Elmer ThermoElectricSolver. LU refinement uses the
exact current matrix and numeric factorization; no stale LU crosses nonlinear
updates. A transfer is an INITIAL GUESS ONLY, never a solved output.

The source cases are the archived fine refined replay for cold1, the archived
bath case for bath2, and actual completed bath2 for bath3. Bounds are3000s for
cold1 and2400s for each bath case. Native solver logs, elapsed/CPU time, peak
RSS, nonlinear iterations, exact SIF, timed upstream source, source snapshots,
compiled numeric wrapper and raw VTU are retained.

Run independent audits only after actual solver completion:

```
./fem/run_g2b.sh python -m tecooledmct.gate_refinement_analysis \
  --mesh outputs/gate-refinement/cold1_mesh \
  --case outputs/gate-refinement/cold1_case \
  --out outputs/gate-refinement/cold1_audit
```

Repeat with bath2, bath3 and combined labels as applicable. The frozen independent
auditors use actual owner gradients, SI areas, material conductivity and outward
normals, retaining face powers/heights/centroids/quality and spatial maps. The
bath reference is known0.1A times actual terminal voltage plus2mW source;
reaction/recovered flux is never substituted. Confirm all177 cuts and nonraw
conservation checks independently of the unchanged raw gates.

## Conditional combination and evidence publication

Only after the independent cold raw gate and bath raw gate pass, apply the same
cold refinement to verified bath3 geometry. The predicted994879-tet combined
mesh stays below the registered1M cap. Use actual completed bath3 P1 data as
its initial guess, and the registered3000s bound. All original field/current/
energy/raw checks apply again on that single mesh.

`python -m tecooledmct.gate_refinement_study` collects only actually completed,
independently audited samples. It also compares physical tetrahedral coordinates
and body connectivity across different node numbering: combined cold cells must
match cold1 and combined bath cells must match bath3. A combined pass is not
release without a systematically refined passing combined comparator.

Run full opt-in pytest, existing CLI/demo and earlier guards. Publish scoped
evidence using `./fem/run_g2b.sh python fem/archive_gate_refinement.py`, then
`--verify`. Failed attempts remain failed and unconverged fields stay separate.
The archive seals actual meshes, fields, initial guesses, independent audits,
libraries, sources, resource bounds, numerical status and all prior ledger hashes.

Only after verified archival publication, build a NEW Rev3 edition. The report
supplement reads the immutable study archive, checks mesh/field identities and
produces actual refined-flux figures and numerical tables. It does not read a
running solver's fields. Every new PDF needs reader/provenance checks, rendered
page inspection and its own sealed source/figure/PDF record before replacing
the public current REVIEW DRAFT copy. Earlier editions and Rev2 stay unchanged.
